#!/usr/bin/env python3
"""
bake_sd_profiles.py — Offline black-box color-profile distiller for M-Film.

Runs `spektrafilm` strictly as an external black-box spectral film simulator
(with halation, physical grain, glare, and auto-exposure disabled) on a
synthetic test target composed of:
  - Standard 24-patch ColorChecker (linear sRGB)
  - 6x6x6 (216-point) linear RGB color cube
  - 256-step logarithmic greyscale ramp (-7.0 to +3.5 stops around 0.18)

Then fits each film stock's input-to-output color mapping using
scipy.optimize.least_squares into a compact, purely parametric model
(3x3 linear input matrix + per-channel generalized logistic tone curves +
3x3 display output matrix & bias) compatible with M-Film's clean-room
GPL-2.0 external profile loader (`ML/MFILM/profiles/*.cfg`).

License isolation note:
  This script is an independent host-side tool. The generated `.cfg` files
  are derived measurement data subject to CC BY-SA 4.0 (as declared in
  `PROFILES_ATTRIBUTION.txt`) and are kept strictly isolated on the SD card
  from the GPL-2.0 camera firmware binaries (`autoexec.bin`, `filmos.mo`).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Tuple

import colour
import numpy as np
from scipy.optimize import least_squares


# ---------------------------------------------------------------------------
# Standard 24-patch ColorChecker (D65 sRGB -> linear sRGB)
# Reference: BabelColor / X-Rite Classic 24-patch sRGB values (0..255)
# ---------------------------------------------------------------------------
COLORCHECKER_24_SRGB = np.array([
    [115,  82,  68],  # 1. Dark Skin
    [194, 150, 130],  # 2. Light Skin
    [ 98, 122, 157],  # 3. Blue Sky
    [ 87, 108,  67],  # 4. Foliage
    [133, 128, 177],  # 5. Blue Flower
    [103, 189, 170],  # 6. Bluish Green
    [214, 126,  44],  # 7. Orange
    [ 80,  91, 166],  # 8. Purplish Blue
    [193,  90,  99],  # 9. Moderate Red
    [ 94,  60, 108],  # 10. Purple
    [157, 188,  64],  # 11. Yellow Green
    [224, 163,  46],  # 12. Orange Yellow
    [ 56,  61, 150],  # 13. Blue
    [ 70, 148,  73],  # 14. Green
    [175,  54,  60],  # 15. Red
    [231, 199,  31],  # 16. Yellow
    [187,  86, 149],  # 17. Magenta
    [  8, 133, 161],  # 18. Cyan
    [243, 243, 242],  # 19. White 9.5
    [200, 200, 200],  # 20. Neutral 8
    [160, 160, 160],  # 21. Neutral 6.5
    [122, 122, 121],  # 22. Neutral 5
    [ 85,  85,  85],  # 23. Neutral 3.5
    [ 52,  52,  52],  # 24. Black 2
], dtype=np.float64) / 255.0


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb_to_lab(srgb: np.ndarray) -> np.ndarray:
    lin = srgb_to_linear(np.clip(srgb, 0.0, 1.0))
    xyz = colour.RGB_to_XYZ(
        lin,
        colour.RGB_COLOURSPACES["sRGB"],
        apply_cctf_decoding=False,
    )
    return colour.XYZ_to_Lab(xyz)


# ---------------------------------------------------------------------------
# Film stock catalog to sample from SpektraFilm (black-box identifiers only)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StockSpec:
    sf_name: str
    print_paper: str
    key: str
    brand: str
    name: str
    shortname: str
    process: str
    group: int          # 0=COLOUR, 1=SLIDE, 2=B&W, 3=CINE
    box_iso: int
    iso: int
    kelvin: int
    slide: int
    desc: str
    label_style: int
    label_top: str
    label_word: str
    label_num: str
    label_bg: Tuple[int, int]
    label_band: Tuple[int, int]
    label_accent: Tuple[int, int]
    label_text: Tuple[int, int]
    label_num_ink: Tuple[int, int]


STOCKS: List[StockSpec] = [
    StockSpec("kodak_ektar_100", "kodak_portra_endura", "sf_ektar100", "KODAK", "Ektar 100 (SF)", "SF_Ektar100",
              "C-41", 0, 100, 100, 5500, 0, "Vivid fine-grain color negative",
              2, "KODAK", "EKTAR", "100", (0, 28), (3, 160), (3, 180), (0, 235), (3, 200)),
    StockSpec("kodak_portra_160", "kodak_portra_endura", "sf_portra160", "KODAK", "Portra 160 (SF)", "SF_Portra160",
              "C-41", 0, 160, 160, 5500, 0, "Delicate skin tones, soft contrast",
              1, "KODAK", "PORTRA", "160", (0, 226), (1, 185), (2, 160), (0, 24), (3, 150)),
    StockSpec("kodak_portra_400", "kodak_portra_endura", "sf_portra400", "KODAK", "Portra 400 (SF)", "SF_Portra400",
              "C-41", 0, 400, 400, 5500, 0, "Warm portrait negative, wide latitude",
              1, "KODAK", "PORTRA", "400", (0, 226), (1, 195), (2, 165), (0, 24), (3, 155)),
    StockSpec("kodak_portra_800", "kodak_portra_endura", "sf_portra800", "KODAK", "Portra 800 (SF)", "SF_Portra800",
              "C-41", 0, 800, 800, 5500, 0, "High-speed warm portrait negative",
              1, "KODAK", "PORTRA", "800", (0, 220), (2, 175), (3, 155), (0, 24), (3, 165)),
    StockSpec("kodak_portra_800_push1", "kodak_portra_endura", "sf_portra800p1", "KODAK", "Portra 800+1 (SF)", "SF_Portra800P1",
              "C-41", 0, 1600, 1600, 5500, 0, "Portra 800 pushed +1 stop",
              1, "KODAK", "PORTRA", "800+", (0, 215), (2, 165), (3, 165), (0, 24), (3, 175)),
    StockSpec("kodak_portra_800_push2", "kodak_portra_endura", "sf_portra800p2", "KODAK", "Portra 800+2 (SF)", "SF_Portra800P2",
              "C-41", 0, 3200, 3200, 5500, 0, "Portra 800 pushed +2 stops",
              1, "KODAK", "PORTRA", "800++", (0, 210), (3, 155), (2, 175), (0, 24), (3, 185)),
    StockSpec("kodak_gold_200", "kodak_endura_premier", "sf_gold200", "KODAK", "Gold 200 (SF)", "SF_Gold200",
              "C-41", 0, 200, 200, 5500, 0, "Classic warm consumer negative",
              0, "KODAK", "GOLD", "200", (1, 195), (3, 150), (0, 22), (0, 235), (0, 22)),
    StockSpec("kodak_ultramax_400", "kodak_endura_premier", "sf_ultramax400", "KODAK", "UltraMax 400 (SF)", "SF_UltraMax400",
              "C-41", 0, 400, 400, 5500, 0, "Punchy everyday consumer 400",
              0, "KODAK", "ULTRAMAX", "400", (1, 205), (5, 130), (3, 160), (0, 235), (0, 22)),
    StockSpec("kodak_vision3_50d", "kodak_2383", "sf_v3_50d", "KODAK", "Vision3 50D (SF)", "SF_V3_50D",
              "ECN-2", 3, 50, 100, 5500, 0, "Daylight cine negative + 2383 print",
              2, "VISION3", "50D", "5203", (0, 32), (1, 185), (1, 200), (0, 235), (1, 210)),
    StockSpec("kodak_vision3_250d", "kodak_2383", "sf_v3_250d", "KODAK", "Vision3 250D (SF)", "SF_V3_250D",
              "ECN-2", 3, 250, 250, 5500, 0, "Versatile daylight cine + 2383 print",
              2, "VISION3", "250D", "5207", (0, 32), (2, 175), (2, 195), (0, 235), (2, 205)),
    StockSpec("kodak_verita_200d", "kodak_2383", "sf_verita200d", "KODAK", "Verita 200D (SF)", "SF_Verita200D",
              "ECN-2", 3, 200, 200, 5500, 0, "Daylight motion picture stock + 2383",
              2, "KODAK", "VERITA", "200D", (0, 36), (1, 170), (2, 180), (0, 235), (1, 195)),
    StockSpec("kodak_vision3_200t", "kodak_2383", "sf_v3_200t", "KODAK", "Vision3 200T (SF)", "SF_V3_200T",
              "ECN-2", 3, 200, 200, 3200, 0, "Tungsten cine negative + 2383 print",
              2, "VISION3", "200T", "5213", (0, 28), (5, 145), (5, 185), (0, 235), (5, 200)),
    StockSpec("kodak_vision3_500t", "kodak_2383", "sf_v3_500t", "KODAK", "Vision3 500T (SF)", "SF_V3_500T",
              "ECN-2", 3, 500, 500, 3200, 0, "High-speed tungsten cine + 2383 print",
              2, "VISION3", "500T", "5219", (0, 24), (5, 130), (5, 175), (0, 235), (5, 195)),
    StockSpec("fujifilm_pro_400h", "fujifilm_crystal_archive_typeii", "sf_pro400h", "FUJIFILM", "Pro 400H (SF)", "SF_Pro400H",
              "C-41", 0, 400, 400, 5500, 0, "Airy pastel greens & soft highlights",
              1, "FUJIFILM", "PRO 400H", "400H", (0, 230), (4, 155), (4, 130), (0, 26), (4, 120)),
    StockSpec("fujifilm_c200", "fujifilm_crystal_archive_typeii", "sf_c200", "FUJIFILM", "Fujicolor C200 (SF)", "SF_C200",
              "C-41", 0, 200, 200, 5500, 0, "Crisp greens & balanced consumer look",
              0, "FUJIFILM", "C200", "200", (4, 145), (0, 232), (3, 155), (0, 24), (0, 232)),
    StockSpec("fujifilm_xtra_400", "fujifilm_crystal_archive_typeii", "sf_xtra400", "FUJIFILM", "Superia X-TRA (SF)", "SF_Xtra400",
              "C-41", 0, 400, 400, 5500, 0, "Cool shadows, lively street color",
              0, "FUJIFILM", "X-TRA", "400", (4, 135), (3, 150), (0, 232), (0, 235), (0, 232)),
    StockSpec("kodak_ektachrome_100", "kodak_portra_endura", "sf_e100", "KODAK", "Ektachrome 100 (SF)", "SF_E100",
              "E-6", 1, 100, 100, 5500, 1, "Clean neutral reversal slide film",
              1, "KODAK", "EKTACHROME", "E100", (0, 232), (5, 140), (1, 190), (0, 24), (5, 140)),
    StockSpec("kodak_kodachrome_64", "kodak_portra_endura", "sf_k64", "KODAK", "Kodachrome 64 (SF)", "SF_K64",
              "K-14", 1, 64, 100, 5500, 1, "Iconic rich reds & deep slide contrast",
              0, "KODAK", "KODACHROME", "64", (1, 200), (3, 155), (0, 22), (0, 235), (0, 22)),
    StockSpec("fujifilm_velvia_100", "fujifilm_crystal_archive_typeii", "sf_velvia100", "FUJIFILM", "Velvia 100 (SF)", "SF_Velvia100",
              "E-6", 1, 100, 100, 5500, 1, "Ultra-saturated landscape slide film",
              1, "FUJIFILM", "VELVIA", "100", (0, 30), (4, 145), (3, 165), (0, 235), (4, 175)),
    StockSpec("fujifilm_provia_100f", "fujifilm_crystal_archive_typeii", "sf_provia100f", "FUJIFILM", "Provia 100F (SF)", "SF_Provia100F",
              "E-6", 1, 100, 100, 5500, 1, "Faithful fine-grain daylight slide",
              1, "FUJIFILM", "PROVIA", "100F", (0, 232), (5, 150), (4, 140), (0, 24), (5, 145)),
]


# ---------------------------------------------------------------------------
# Synthetic target generation (24 ColorChecker + 6x6x6 RGB cube + 256 grey)
# ---------------------------------------------------------------------------
def build_synthetic_samples() -> Tuple[np.ndarray, int, int, int]:
    """Return (samples [N, 3] in linear sRGB, n_cc, n_cube, n_grey)."""
    # 1. 24-patch ColorChecker in scene-linear sRGB
    cc_lin = srgb_to_linear(COLORCHECKER_24_SRGB)

    # 2. 6x6x6 RGB color cube spanning shadows to highlights (linear sRGB)
    # Using perceptually spaced levels from 0.004 to 1.6 (covers -5.5 to +3.15 EV)
    levels = np.array([0.004, 0.025, 0.08, 0.20, 0.50, 1.40], dtype=np.float64)
    rr, gg, bb = np.meshgrid(levels, levels, levels, indexing="ij")
    cube_lin = np.stack([rr.ravel(), gg.ravel(), bb.ravel()], axis=-1)

    # 3. 256-step logarithmic greyscale ramp (-7.0 to +3.5 stops around 0.18)
    stops = np.linspace(-7.0, 3.5, 256)
    g_val = 0.18 * (2.0 ** stops)
    grey_lin = np.stack([g_val, g_val, g_val], axis=-1)

    samples = np.vstack([cc_lin, cube_lin, grey_lin])
    return samples, len(cc_lin), len(cube_lin), len(grey_lin)


def pack_patches_to_image(samples: np.ndarray, tile: int = 4) -> Tuple[np.ndarray, int]:
    """Pack N RGB samples into an (H, W, 3) float32 image with tile x tile blocks."""
    n = len(samples)
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    img = np.full((rows * tile, cols * tile, 3), 0.18, dtype=np.float32)
    for idx, rgb in enumerate(samples):
        r, c = divmod(idx, cols)
        img[r * tile : (r + 1) * tile, c * tile : (c + 1) * tile] = rgb
    return img, cols


def unpack_patches_from_image(out: np.ndarray, n: int, cols: int, tile: int = 4) -> np.ndarray:
    """Sample the center pixel of each tile x tile block."""
    cy = tile // 2
    cx = tile // 2
    res = np.zeros((n, 3), dtype=np.float64)
    for idx in range(n):
        r, c = divmod(idx, cols)
        res[idx] = out[r * tile + cy, c * tile + cx]
    return np.clip(res, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Parametric color model (identical to fos_extprof.c in M-Film)
# ---------------------------------------------------------------------------
def eval_parametric_model(theta: np.ndarray, lin_rgb: np.ndarray) -> np.ndarray:
    """Evaluate 36-parameter model: M_in (9) + curves (15) + M_out (9) + bias (3)."""
    m_in = theta[0:9].reshape(3, 3)
    contrast = theta[9:12]
    pivot = theta[12:15]
    black = theta[15:18]
    white = theta[18:21]
    gamma = theta[21:24]
    m_out = theta[24:33].reshape(3, 3)
    bias = theta[33:36]

    u = lin_rgb @ m_in.T
    u = np.maximum(u, 1e-6)
    t = np.log2(u / 0.18) - pivot[None, :]

    span = np.maximum(white - black, 0.05)
    k = 4.0 * contrast / span
    z = np.clip(-k[None, :] * t, -40.0, 40.0)
    s = 1.0 / (1.0 + np.exp(z))
    s = np.power(np.maximum(s, 1e-7), gamma[None, :])
    v = black[None, :] + (white - black)[None, :] * s

    y = v @ m_out.T + bias[None, :]
    return np.clip(y, 0.0, 1.0)


def fit_parametric_model(
    lin_in: np.ndarray,
    srgb_target: np.ndarray,
    n_cc: int,
    n_cube: int,
) -> Tuple[np.ndarray, float, float, float]:
    """Fit 36-parameter model via scipy.optimize.least_squares and return (theta, de_cc_mean, de_cc_max, de_all_mean)."""
    # Weights: emphasize 24-patch ColorChecker and neutral greyscale
    n_total = len(lin_in)
    weights = np.ones(n_total, dtype=np.float64)
    weights[:n_cc] = 3.5
    weights[n_cc + n_cube :] = 1.5
    w_sqrt = np.sqrt(weights)[:, None]

    # Initial guess: identity matrices + neutral sRGB-like logistic curve
    x0 = np.zeros(36, dtype=np.float64)
    x0[0:9] = np.eye(3).ravel()
    x0[9:12] = [0.22, 0.22, 0.22]       # contrast
    x0[12:15] = [0.0, 0.0, 0.0]         # pivot
    x0[15:18] = [0.01, 0.01, 0.01]      # black
    x0[18:21] = [0.99, 0.99, 0.99]      # white
    x0[21:24] = [1.0, 1.0, 1.0]         # gamma
    x0[24:33] = np.eye(3).ravel()
    x0[33:36] = [0.0, 0.0, 0.0]

    lb = np.full(36, -3.0)
    ub = np.full(36, 3.0)
    # Bounds for curve parameters
    lb[9:12], ub[9:12] = 0.04, 1.50     # contrast
    lb[12:15], ub[12:15] = -4.0, 4.0    # pivot
    lb[15:18], ub[15:18] = -0.10, 0.35  # black
    lb[18:21], ub[18:21] = 0.65, 1.25   # white
    lb[21:24], ub[21:24] = 0.15, 4.00   # gamma
    lb[33:36], ub[33:36] = -0.25, 0.25  # bias

    def residual(theta: np.ndarray) -> np.ndarray:
        pred = eval_parametric_model(theta, lin_in)
        diff = (pred - srgb_target) * w_sqrt
        # Gentle regularization on matrix drift for numerical stability
        reg_in = 0.005 * (theta[0:9] - np.eye(3).ravel())
        reg_out = 0.005 * (theta[24:33] - np.eye(3).ravel())
        return np.concatenate([diff.ravel(), reg_in, reg_out])

    res = least_squares(
        residual,
        x0,
        bounds=(lb, ub),
        method="trf",
        loss="soft_l1",
        f_scale=0.02,
        max_nfev=600,
    )
    theta = res.x
    pred = eval_parametric_model(theta, lin_in)

    # Evaluate perceptual CIEDE2000 color difference
    lab_ref = srgb_to_lab(srgb_target)
    lab_fit = srgb_to_lab(pred)
    de_all = colour.delta_E(lab_ref, lab_fit, method="CIE 2000")
    de_cc = de_all[:n_cc]
    return theta, float(np.mean(de_cc)), float(np.max(de_cc)), float(np.mean(de_all))


# ---------------------------------------------------------------------------
# .cfg writer & CC BY-SA 4.0 attribution generator
# ---------------------------------------------------------------------------
def fmt_floats(vals: np.ndarray) -> str:
    return ", ".join(f"{float(v):.6f}" for v in vals)


def write_cfg(path: str, spec: StockSpec, theta: np.ndarray, de_cc_mean: float, de_all_mean: float) -> None:
    content = (
        f"# Parametric film color profile for M-Film external loader\n"
        f"# Measurement-derived data: see PROFILES_ATTRIBUTION.txt (CC BY-SA 4.0)\n"
        f"# Fit quality: ColorChecker dE2000={de_cc_mean:.2f}, Full-Chart dE2000={de_all_mean:.2f}\n"
        f"format = 1\n"
        f"key = {spec.key}\n"
        f"brand = {spec.brand}\n"
        f"name = {spec.name}\n"
        f"shortname = {spec.shortname}\n"
        f"process = {spec.process}\n"
        f"group = {spec.group}\n"
        f"desc = {spec.desc}\n"
        f"box_iso = {spec.box_iso}\n"
        f"iso = {spec.iso}\n"
        f"kelvin = {spec.kelvin}\n"
        f"slide = {spec.slide}\n"
        f"mono = 0\n"
        f"ev = 0.0\n"
        f"sat = 1.0\n"
        f"grain = 2\n"
        f"punch = 3\n"
        f"colour = 4\n"
        f"warmth = 3\n"
        f"matrix = {fmt_floats(theta[0:9])}\n"
        f"contrast = {fmt_floats(theta[9:12])}\n"
        f"pivot = {fmt_floats(theta[12:15])}\n"
        f"black = {fmt_floats(theta[15:18])}\n"
        f"white = {fmt_floats(theta[18:21])}\n"
        f"gamma = {fmt_floats(theta[21:24])}\n"
        f"out_matrix = {fmt_floats(theta[24:33])}\n"
        f"out_bias = {fmt_floats(theta[33:36])}\n"
        f"label_style = {spec.label_style}\n"
        f"label_top = {spec.label_top}\n"
        f"label_word = {spec.label_word}\n"
        f"label_num = {spec.label_num}\n"
        f"label_sub = CC BY-SA 4.0\n"
        f"label_bg = {spec.label_bg[0]}, {spec.label_bg[1]}\n"
        f"label_band = {spec.label_band[0]}, {spec.label_band[1]}\n"
        f"label_accent = {spec.label_accent[0]}, {spec.label_accent[1]}\n"
        f"label_text = {spec.label_text[0]}, {spec.label_text[1]}\n"
        f"label_num_ink = {spec.label_num_ink[0]}, {spec.label_num_ink[1]}\n"
    )
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def write_attribution(out_dir: str, baked_names: List[str]) -> None:
    text = (
        "================================================================================\n"
        "  EXTERNAL FILM PROFILES ATTRIBUTION & LICENSE NOTICE (CC BY-SA 4.0)\n"
        "================================================================================\n\n"
        "The parametric film color profile files (*.cfg) in this directory\n"
        "(ML/MFILM/profiles/) contain numerical color-mapping parameters derived via\n"
        "black-box colorimetric sampling from:\n\n"
        "  Project : SpektraFilm (Spectral simulation of analog film photography)\n"
        "  Author  : Andrea Volpato\n"
        "  Source  : https://github.com/andreavolpato/spektrafilm\n"
        "  License : Creative Commons Attribution-ShareAlike 4.0 International\n"
        "            (CC BY-SA 4.0) — see SPEKTRAFILM_LICENSE.txt upstream:\n"
        "            https://github.com/andreavolpato/spektrafilm/blob/main/SPEKTRAFILM_LICENSE.txt\n\n"
        "LICENSE ISOLATION (AGGREGATION):\n"
        "  - The camera firmware binaries (autoexec.bin, ML/modules/filmos.mo) are\n"
        "    independent GPL-2.0 software with zero GPL-3.0 code or hardcoded\n"
        "    SpektraFilm data.\n"
        "  - These *.cfg files are standalone data files read dynamically from the\n"
        "    SD card at runtime, forming a compliant Aggregation alongside the\n"
        "    GPL-2.0 firmware binaries.\n"
        "  - Any redistribution or derivative of these *.cfg files must preserve\n"
        "    this attribution notice and remain under CC BY-SA 4.0.\n\n"
        f"Included Profiles ({len(baked_names)}):\n"
        + "".join(f"  - {name}\n" for name in baked_names)
    )
    with open(os.path.join(out_dir, "PROFILES_ATTRIBUTION.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# ---------------------------------------------------------------------------
# Main black-box sampling & fitting driver
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Bake external M-Film .cfg profiles via SpektraFilm black-box sampling.")
    ap.add_argument("--spektrafilm-src", required=True, help="Path to standalone spektrafilm/src directory")
    ap.add_argument("--out-dir", required=True, help="Output directory for ML/MFILM/profiles")
    ap.add_argument("--report", required=True, help="Output Markdown report path (docs/SPEKTRAFILM_BAKE_REPORT.md)")
    args = ap.parse_args()

    sys.path.insert(0, os.path.abspath(args.spektrafilm_src))
    from spektrafilm.runtime.api import init_params, simulate

    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)

    samples, n_cc, n_cube, n_grey = build_synthetic_samples()
    target_img, cols = pack_patches_to_image(samples, tile=4)
    print(f"[bake] Synthetic test chart: {n_cc} ColorChecker + {n_cube} RGB cube + {n_grey} grey = {len(samples)} patches ({target_img.shape[1]}x{target_img.shape[0]})")

    results = []
    baked_files = []
    t_start = time.time()

    for idx, spec in enumerate(STOCKS, 1):
        t0 = time.time()
        p = init_params(film_profile=spec.sf_name, print_profile=spec.print_paper)
        # Disable all spatial/stochastic effects for pure point-wise colorimetric sampling
        p.film_render.halation.active = False
        p.film_render.grain.active = False
        p.film_render.glare.active = False
        p.print_render.glare.active = False
        p.film_render.dir_couplers.diffusion_size_um = 0.0
        p.film_render.dir_couplers.diffusion_tail_um = 0.0
        p.film_render.dir_couplers.diffusion_tail_weight = 0.0
        p.camera.auto_exposure = False
        p.camera.lens_blur_um = 0.0
        p.io.input_color_space = "sRGB"
        p.io.input_cctf_decoding = False
        p.io.output_color_space = "sRGB"
        p.io.output_cctf_encoding = True
        p.io.scan_film = bool(spec.slide)

        out_img = simulate(target_img, p)
        srgb_ref = unpack_patches_from_image(out_img, len(samples), cols, tile=4)

        theta, de_cc_mean, de_cc_max, de_all_mean = fit_parametric_model(samples, srgb_ref, n_cc, n_cube)
        cfg_name = f"{spec.sf_name}.cfg"
        cfg_path = os.path.join(args.out_dir, cfg_name)
        write_cfg(cfg_path, spec, theta, de_cc_mean, de_all_mean)
        baked_files.append(cfg_name)

        dt = time.time() - t0
        print(f"  [{idx:02d}/{len(STOCKS)}] {spec.sf_name:<26s} -> {cfg_name:<30s} CC dE00={de_cc_mean:.2f} (max {de_cc_max:.2f}) All dE00={de_all_mean:.2f} ({dt:.1f}s)")
        results.append((spec, cfg_name, de_cc_mean, de_cc_max, de_all_mean, dt))

    write_attribution(args.out_dir, baked_files)

    avg_cc = float(np.mean([r[2] for r in results]))
    max_cc_overall = float(np.max([r[3] for r in results]))
    avg_all = float(np.mean([r[4] for r in results]))
    total_s = time.time() - t_start

    # Write Chinese evaluation report per GEMINI.md bilingual policy
    lines = [
        "# SpektraFilm 离线黑盒烘焙与色差（ΔE2000）评估报告",
        "",
        "## 一、 协议隔离与烘焙方法概述",
        "",
        "- **协议防火墙架构**：",
        "  - 宿主机离线脚本 `workspace/tools/bake_sd_profiles.py` 将 `andreavolpato/spektrafilm`（克隆于独立临时目录 `workspace/04_spektrafilm/`）严格作为外部黑盒模拟器运行，**零源码/头文件/数据数组拷贝至 GPL-2.0 固件树**。",
        "  - 输出的纯文本数值配置文件（`ML/MFILM/profiles/*.cfg`）随附 `PROFILES_ATTRIBUTION.txt`，规范遵循 **CC BY-SA 4.0** 署名共享协议，在 SD 卡上与 GPL-2.0 固件二进制（`autoexec.bin` / `ML/modules/filmos.mo`）构成合规的 **Aggregation（聚合）** 隔离。",
        "- **黑盒采样配置**：",
        "  - 关闭光晕（`halation.active = False`）、物理颗粒（`grain.active = False`）、镜头/印相眩光（`glare.active = False`）、DIR 空间扩散与自动曝光（`auto_exposure = False`），输入标准线性 sRGB（`0.18 = 18%` 中灰），输出显示 sRGB。",
        f"  - 合成采样测试图包含：**24 色标准 ColorChecker** + **6×6×6（216 点）RGB 色彩立方体** + **256 级对数灰阶斜坡**（`-7.0` 至 `+3.5` EV），共 `{len(samples)}` 个采样点。",
        "- **参数化拟合模型（36 自由度，与 `fos_extprof.c` 逐比特一致）**：",
        "  - 线性场景 `3×3` 色彩矩阵 + RGB 分通道广义 Logistic 色调曲线（反差 `contrast`、中灰支点 `pivot`、黑场 `black`、白场 `white`、非对称指数 `gamma`）+ 显示空间 `3×3` 输出矩阵与偏置，经 `scipy.optimize.least_squares`（TRF + Soft-L1 鲁棒损失）拟合。",
        "",
        "## 二、 汇总指标",
        "",
        f"- **烘焙胶片总数**：`{len(results)}` 款（覆盖 Kodak Pro/Consumer/Cine、Fujifilm C-41 及 E-6/K-14 反转片）",
        f"- **24 色 ColorChecker 平均色差（ΔE2000）**：**`{avg_cc:.2f}`**",
        f"- **24 色 ColorChecker 单色块最大色差（ΔE2000）**：`{max_cc_overall:.2f}`",
        f"- **全图 496 采样点（含 6×6×6 色彩立方体与 256 级灰阶）平均色差（ΔE2000）**：**`{avg_all:.2f}`**",
        f"- **离线烘焙总耗时**：`{total_s:.1f} s`",
        "",
        "## 三、 逐胶片拟合精度明细表",
        "",
        "| # | 胶片名称 | 配置文件 | 工艺 / ISO | 印相纸配对 | ColorChecker 平均 ΔE00 | ColorChecker 最大 ΔE00 | 全图 496 点平均 ΔE00 |",
        "| :-: | :--- | :--- | :--- | :--- | :-: | :-: | :-: |",
    ]
    for idx, (spec, cfg_name, de_cc_mean, de_cc_max, de_all_mean, _dt) in enumerate(results, 1):
        paper = "反转正片 (直出)" if spec.slide else spec.print_paper
        lines.append(
            f"| {idx:02d} | {spec.name} | `{cfg_name}` | {spec.process} / ISO {spec.box_iso} | `{paper}` | **{de_cc_mean:.2f}** | {de_cc_max:.2f} | {de_all_mean:.2f} |"
        )
    lines.append("")

    with open(args.report, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(f"[bake] DONE: {len(results)} profiles baked. Mean CC dE2000 = {avg_cc:.2f}, Mean All dE2000 = {avg_all:.2f} ({total_s:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
