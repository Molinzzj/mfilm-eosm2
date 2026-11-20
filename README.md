# M-Film for Canon EOS M2 (Firmware 1.0.3)

[![Build & Safety Audit](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml/badge.svg)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml)
![Hardware Verification](https://img.shields.io/badge/EOS%20M2%20(1.0.3)-Hardware%20Verified%20(PASS)-brightgreen)

[中文文档 (README_CN.md)](./README_CN.md)

A **Magic Lantern** port (based on [`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)) with **M-Film v0.2.3** ([`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)) film simulation and in-camera RAW darkroom integrated for the **Canon EOS M2** (DIGIC 5 / ARM946E-S, Official Firmware **1.0.3**).

> **Hardware Status**: **Hardware Verified (PASS)** on a physical **Canon EOS M2 (Firmware 1.0.3)** across all three stages — Stage 1 (Clean Magic Lantern Base), Stage 2 (M-Film v0.2.3 Core & In-Camera Darkroom), and Stage 3 (20 External SpektraFilm `.cfg` Profiles Loading & Developing).

---

## ⚠️ Safety Warning — Read Before Use

> [!CAUTION]
> - **🔴 STRICT FIRMWARE WARNING — OFFICIAL FIRMWARE `1.0.3` ONLY — DO NOT UPGRADE TO `1.0.4`!**
>   - This port strictly supports **Canon EOS M2 official firmware `1.0.3`** (`EOSM2.103`) **ONLY**.
>   - Users currently on **`1.0.1`** or **`1.0.2`** may safely upgrade to official **`1.0.3`** using Canon's official 1.0.3 updater.
>   - **DO NOT upgrade to Canon's latest `1.0.4` security-patch firmware — firmware `1.0.4` CANNOT be downgraded and is NOT supported!**
> - **Non-Persistent Loading Strongly Recommended**: Always load via Canon's built-in **Menu → Wrench → Firmware Ver. 1.0.3 → Firmware Update** flow. Do **not** enable or write the NVRAM Bootflag unless you understand the risks.
> - **Zero Automatic Bootflag Writes**: All builds in this repository are statically audited (`scripts/verify_m2_safety.py`) to contain zero automatic `EnableBootDisk` / `SetBootFlag` calls and 100% preserved `EOSM2.103` hardware addresses.
> - **Use at Your Own Risk**: Third-party camera firmware carries inherent risk. If the camera ever freezes or shows a black screen during non-persistent loading, **remove the battery for 5 seconds and reinsert it** to cleanly return to stock Canon firmware.

---

## Key Features

- **Modern Magic Lantern Base (`EOSM2.103`) — Hardware Verified (PASS)**: Migrated from the legacy EOS M2 1.0.3 DryOS port onto `magiclantern_simplified` with all 144 active `NSTUB` addresses, VRAM pointers, and `BGMT_*` keycodes preserved intact. Uses the DryOS FAT32 8.3-compliant symbol table **`ML/MODULES/EOSM2103.SYM`** so module loading works reliably on EOS M2's single-slot FAT32 filesystem.
- **M-Film v0.2.3 External Module (`--module`) — Hardware Verified (PASS)**: Runs the Film OS and in-camera CR2→JPEG darkroom as an external module (`ML/MODULES/filmos.mo`) to stay safely within DIGIC 5's 592 KB (`605,952 B`) fixed boot memory reservation (`537,344 B` used, `67.0 KB` headroom).
- **Mirrorless HUD & Canon Graphics Hiding**: Inherits EOS M mirrorless optimizations — direct LiveView HUD rendering (skipping DSLR top-plate code) and **`Settings → Advanced → Hide Canon's graphics`** to prevent Canon's exposure scale/icons from drawing over the M-Film HUD.
- **Cross-Model External Profile Loader (`fos_extprof`) — Hardware Verified (PASS)**: Clean-room GPL-2.0 loader with zero `EOSM2`-specific macros, hardcoded screen coordinates, or camera-specific memory assumptions — uses `fos_port_*` file/memory pool abstractions so it builds cleanly across M-Film models (`EOSM2.103`, `EOSM.202`, `6D.116`, etc.), verified on physical EOS M2 (1.0.3) with 20 external `(SF)` `.cfg` profiles, an `EOSM.202` `filmos.mo` (`FATAL_WARNINGS=y`) smoke build, and a host-side zero-leak unit test (`Allocs == Frees`).
- **Three-Stage Release Bundles**:
  - `01_EOSM2_Clean_ML_Base.zip`: Pure Magic Lantern base (`ML/MODULES/EOSM2103.SYM`) for verifying boot, menus, and buttons first.
  - `02_EOSM2_MFilm_023_TestBuild.zip`: Standard M-Film v0.2.3 bundle (`ML/MODULES/filmos.mo` + `ML/MODULES/EOSM2103.SYM`) with built-in darkroom LUTs and film stocks.
  - `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`: M-Film v0.2.3 with the dynamic external profile loader (`fos_extprof`) and 20 baked SpektraFilm `(SF)` profiles pre-populated under `ML/MFILM/profiles/`.

---

## Quick Start (4 Steps)

1. **Verify Firmware (`1.0.3` ONLY) & Prepare SD Card**: Confirm your EOS M2 is on official **Firmware `1.0.3`** (`1.0.1` / `1.0.2` users may update to `1.0.3`; **never upgrade to `1.0.4`**). Format a **≤ 32 GB FAT32** SD card inside the camera and make sure the battery is fully charged.
2. **Download Release Bundle**: Download `01_EOSM2_Clean_ML_Base.zip`, `02_EOSM2_MFilm_023_TestBuild.zip`, or `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` (recommended — includes the 20 pre-baked `(SF)` external film profiles) from [GitHub Releases](https://github.com/Molinzzj/mfilm-eosm2/releases) or the latest green [GitHub Actions (`Build & Safety Audit`)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml) Artifacts (`eos-m2-mfilm-bundles-and-reports`, retained for 30 days), and verify the `.sha256` checksum.
3. **Extract to SD Card Root**: Unzip the archive directly into the **root directory** of the SD card so `autoexec.bin`, `ML-SETUP.FIR`, `ML/MODULES/EOSM2103.SYM`, and the `ML/` folder sit directly at the top level (do not nest inside an extra folder). When using `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`, this also populates `ML/MFILM/profiles/*.cfg` (20 `(SF)` profiles) and `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt`, making all external stocks immediately selectable in the M-Film shelf upon boot.
4. **Load via Firmware Update**: Insert the card, switch the mode dial to a still-photo mode (`M` / `Av` / `Tv`), set image quality to **RAW** (required for M-Film's in-camera darkroom), open Canon's menu → **Firmware Ver. 1.0.3 → Firmware Update**, and run a non-persistent boot. In LiveView, **long-press the Delete / Trash button** to open Magic Lantern / M-Film.

For the full three-stage real-camera test report (**Hardware Verified (PASS)**), see [`docs/REAL_CAMERA_SMOKE_TEST.md`](./docs/REAL_CAMERA_SMOKE_TEST.md).

---

## Repository Layout

```text
.
├── .github/workflows/
│   └── build-and-audit.yml              # CI: 3-bundle build, EOSM.202 smoke, 6-gate audit & artifacts
├── platform/EOSM2.103/                  # Audited EOS M2 (1.0.3) platform port files
├── patches/
│   ├── 01-ml-simplified-eosm2.patch     # Minimal EOS M2 patch for magiclantern_simplified
│   ├── 02-mfilm-eosm2.patch             # Minimal EOS M2 patch for M-Film v0.2.3
│   └── 03-mfilm-extprof-loader.patch    # Cross-model clean-room GPL-2.0 .cfg profile loader (fos_extprof)
├── scripts/
│   ├── bake_sd_profiles.py              # Offline black-box SpektraFilm baker -> ML/MFILM/profiles/*.cfg
│   ├── build_all.sh                     # Reproducible upstream clone + patch + Stage 01 & 02 build script
│   ├── build_03_bundle.sh               # Non-interactive Stage 03 bundle builder (isolated temp clone)
│   └── verify_m2_safety.py              # 6-gate static/binary safety & license auditor
├── docs/
│   ├── REAL_CAMERA_SMOKE_TEST.md        # Three-stage real-camera smoke test guide
│   ├── SAFETY_AUDIT_REPORT.md           # Static, binary, cross-model & zero-leak audit report (PASS)
│   └── SPEKTRAFILM_BAKE_REPORT.md       # Offline SpektraFilm baking & ΔE2000 accuracy report
├── LICENSE                              # GNU General Public License v2.0
├── README.md                            # English documentation
└── README_CN.md                         # Chinese documentation
```

---

## How to Build from Source

### Prerequisites

- **ARM Toolchain**: `arm-none-eabi-gcc`, `binutils-arm-none-eabi`, `libnewlib-arm-none-eabi` (tested on Ubuntu `gcc-arm-none-eabi` and xPack GNU Arm Embedded GCC `12.3.1-1.2`)
- **Host Tools**: `gcc`, `make`, `git`, `python3`, `zip`, `unzip`
- **Python 3 Packages**: `docutils`, `setuptools`, `numpy`, `segno` (plus `scipy`, `colour-science`, `scikit-image`, `matplotlib`, `opt-einsum`, `numba`, `OpenImageIO`, `pyfftw`, `rawpy`, `exiv2`, `lensfunpy` for running `scripts/build_03_bundle.sh`)

### One-Command Reproducible Build (`01`, `02` & `03` Bundles)

```bash
git clone https://github.com/Molinzzj/mfilm-eosm2.git
cd mfilm-eosm2

# Build Stage 01 (Clean ML Base) and Stage 02 (M-Film v0.2.3)
./scripts/build_all.sh

# Optional: Bake 20 external SpektraFilm (SF) profiles in an isolated temp dir -> Stage 03 bundle
./scripts/build_03_bundle.sh
```

- `scripts/build_all.sh` automatically clones pinned `reticulatedpines/magiclantern_simplified` (`142472e9`) and `HNGSeries/mfilm-canon-film-simulation` (`3c3986dd`, v0.2.3), applies `platform/EOSM2.103/` and all three patches, and produces `dist/01_EOSM2_Clean_ML_Base.zip` and `dist/02_EOSM2_MFilm_023_TestBuild.zip` with `.sha256` checksums.
- `scripts/build_03_bundle.sh` clones `andreavolpato/spektrafilm` into a temporary directory outside the repository (`mktemp -d`, auto-cleaned on exit), runs `scripts/bake_sd_profiles.py` to generate 20 `.cfg` profiles + `PROFILES_ATTRIBUTION.txt`, and packages `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` and its `.sha256` without writing any `.cfg` data files into the Git source tree.

### Run the 6-Gate Safety & License Audit

```bash
python3 scripts/verify_m2_safety.py dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
```

See [`docs/SAFETY_AUDIT_REPORT.md`](./docs/SAFETY_AUDIT_REPORT.md) for the full 6-gate audit output, `EOSM.202` cross-model smoke build result, and host-side `Allocs == Frees` zero-leak verification.

---

## External Film Profile Loader & License Isolation Architecture (GPL-2.0 / CC BY-SA 4.0)

To support third-party spectral film profiles without introducing any GPL-3.0 code into the GPL-2.0 Magic Lantern / M-Film firmware tree, this repository implements a strict **License Firewall + SD-Card Aggregation** architecture:

1. **Cross-Model Clean-Room GPL-2.0 Firmware Loader ([`patches/03-mfilm-extprof-loader.patch`](./patches/03-mfilm-extprof-loader.patch))**:
   - Adds `fos_extprof.c` / `fos_extprof.h` inside `ML/modules/filmos.mo`.
   - Fully camera-agnostic: contains zero `EOSM2`-specific macros, screen coordinates, or memory-map assumptions, relying strictly on `fos_port_card()`, `fos_port_list()`, `fos_port_open()`/`read()`/`close()`, and `fos_port_alloc()`/`free()` so it works across all M-Film platforms (`EOSM2.103`, `EOSM.202`, `6D.116`, etc.).
   - At boot or when opening the film shelf / darkroom, automatically scans `ML/MFILM/profiles/*.cfg` on the SD card and dynamically appends discovered parametric film stocks to the M-Film shelf.
   - Synthesizes the 33×33×33 Cineon-log 3D LUT on demand in the darkroom from each `.cfg`'s pure numerical parameters (`3×3` linear color matrix + RGB per-channel generalized logistic tone curves + `3×3` display output matrix).
   - **Zero boot-RAM overhead & zero leaks**: All parsing and profile arrays reside in `filmos.mo` runtime memory (`fos_port_alloc` / `tmp_malloc`), keeping `autoexec.bin` boot usage unchanged at `537,344 / 605,952 bytes` (`67.0 KB` headroom), verified by a host-side unit test with reload and OOM injection (`Allocs=39, Frees=39, LiveBytes=0`).
2. **Standalone Host-Side Black-Box Baker ([`scripts/bake_sd_profiles.py`](./scripts/bake_sd_profiles.py) & [`scripts/build_03_bundle.sh`](./scripts/build_03_bundle.sh))**:
   - Runs an external spectral simulator (`andreavolpato/spektrafilm` cloned in an isolated temp directory) as a pure black box with halation, grain, glare, and auto-exposure disabled, sampling a 496-patch synthetic target (24-patch ColorChecker + 6×6×6 RGB cube + 256-step greyscale ramp).
   - Fits each stock via `scipy.optimize.least_squares` into plain-text `ML/MFILM/profiles/*.cfg` files and emits `PROFILES_ATTRIBUTION.txt` (CC BY-SA 4.0) plus [`docs/SPEKTRAFILM_BAKE_REPORT.md`](./docs/SPEKTRAFILM_BAKE_REPORT.md) (mean 24-patch ColorChecker ΔE2000 = `2.42`, full 496-patch mean ΔE2000 = `1.93` across 20 stocks).
   - **No CC BY-SA 4.0 `.cfg` data files are mixed into this GPL-2.0 Git repository**; users can download the CI-built `03` bundle from GitHub Actions Artifacts or generate it locally with `./scripts/build_03_bundle.sh`.

---

## Development Methodology & Safety Verification

This port was engineered using an **AI-assisted, rule-governed workflow (Google Antigravity)** combining a 3-way architectural diff migration with deterministic static verification and automated GitHub Actions CI:

- **Zero-Hallucination Address Preservation**: No firmware addresses were guessed or generated by AI. Every hardware offset in `platform/EOSM2.103/`—including all **135 `0xFF...` firmware stubs** in `stubs.S`, `ROMBASEADDR = 0xFF0C0000`, `RESTARTSTART = 0x44C100`, VRAM addresses, and `BGMT_*` key event codes—was preserved verbatim from the hardware-verified EOS M2 (1.0.3) port (`ccritix/magic-lantern`) and locked by golden SHA256 digests in [`scripts/verify_m2_safety.py`](./scripts/verify_m2_safety.py).
- **Automated CI & 6-Gate Audit**: Every push to `main` and pull request triggers [`.github/workflows/build-and-audit.yml`](./.github/workflows/build-and-audit.yml), which builds all three bundles, performs an upstream `EOSM.202` `filmos.mo` cross-model smoke build (`FATAL_WARNINGS=y`), enforces all 6 deterministic safety/compliance gates (startup memory `< 592 KB`, zero automatic NVRAM Bootflag writes, zero GPL-3.0 contamination), and uploads verified bundles and reports as 30-day Artifacts.
- **Verification Status — Hardware Verified (PASS)**: Cross-compilation, `EOSM.202` cross-model smoke compilation, host memory-pool zero-leak testing, all 6 static safety/compliance checks, and **all three stages on a physical Canon EOS M2 (Firmware `1.0.3`)** — Stage 1 (Clean ML Base + `ML/MODULES/EOSM2103.SYM`), Stage 2 (M-Film v0.2.3 Core & Darkroom), and Stage 3 (20 External SpektraFilm `.cfg` Profiles Loading & Developing) — have **PASSED**. Non-persistent loading via Canon's **Firmware Update** menu remains strongly recommended.

---

## Credits & Upstream Projects

This project stands on the shoulders of the Magic Lantern and M-Film communities:

- **[`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)** — M-Film (v0.2.3) film simulation OS, blind-shooting workflow, low-memory HUD, Canon graphics hiding, and in-camera CR2 darkroom.
- **[`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)** — Modernized Magic Lantern codebase and build system.
- **Bilal / [`ccritix/magic-lantern`](https://github.com/ccritix/magic-lantern)** — Original Canon EOS M2 (Firmware 1.0.3) DryOS port, `stubs.S` address table, `consts.h` VRAM constants, and `gui.h` button mappings.
- **[`andreavolpato/spektrafilm`](https://github.com/andreavolpato/spektrafilm)** — Spectral film simulation reference model and measured film/paper datasets (CC BY-SA 4.0) used to bake external `.cfg` profiles via `scripts/bake_sd_profiles.py`.

---

## License

All firmware patches, platform code, and tooling in this repository are licensed under the **GNU General Public License v2.0 (GPL-2.0)** — see [`LICENSE`](./LICENSE) for the full text, consistent with Magic Lantern and M-Film. External `.cfg` film profiles generated by `scripts/bake_sd_profiles.py` from SpektraFilm remain separate CC BY-SA 4.0 data assets on the SD card (never committed into this GPL-2.0 source tree).
