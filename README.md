# M-Film for Canon EOS M2 (Firmware 1.0.3)

[中文文档 (README_CN.md)](./README_CN.md)

A **Magic Lantern** port (based on [`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)) with **M-Film v0.2.3** ([`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)) film simulation and in-camera RAW darkroom integrated for the **Canon EOS M2** (DIGIC 5 / ARM946E-S, Official Firmware **1.0.3**).

---

## ⚠️ Safety Warning — Read Before Use

> [!CAUTION]
> - **Firmware 1.0.3 ONLY**: This port is strictly locked to **Canon EOS M2 official firmware `1.0.3`** (`EOSM2.103`). Check your camera's `Firmware Ver. 1.0.3` in Canon's menu before trying anything. Do **not** run this on any other camera model or firmware version.
> - **Non-Persistent Loading Strongly Recommended**: Always test via Canon's built-in **Menu → Wrench → Firmware Ver. 1.0.3 → Firmware Update** flow. Do **not** enable or write the NVRAM Bootflag during early testing.
> - **Zero Automatic Bootflag Writes**: All builds in this repository are statically audited (`scripts/verify_m2_safety.py`) to contain zero automatic `EnableBootDisk` / `SetBootFlag` calls and 100% preserved `EOSM2.103` hardware addresses.
> - **Use at Your Own Risk**: Third-party camera firmware carries inherent risk. If the camera ever freezes or shows a black screen during non-persistent loading, **remove the battery for 5 seconds and reinsert it** to cleanly return to stock Canon firmware.

---

## Key Features

- **Modern Magic Lantern Base (`EOSM2.103`)**: Migrated from the legacy EOS M2 1.0.3 DryOS port onto `magiclantern_simplified` with all 144 active `NSTUB` addresses, VRAM pointers, and `BGMT_*` keycodes preserved intact.
- **M-Film v0.2.3 External Module (`--module`)**: Runs the Film OS and in-camera CR2→JPEG darkroom as an external module (`ML/modules/filmos.mo`) to stay safely within DIGIC 5's 592 KB (`605,952 B`) fixed boot memory reservation (`537,344 B` used, `67.0 KB` headroom).
- **Mirrorless HUD & Canon Graphics Hiding**: Inherits EOS M mirrorless optimizations — direct LiveView HUD rendering (skipping DSLR top-plate code) and **`Settings → Advanced → Hide Canon's graphics`** to prevent Canon's exposure scale/icons from drawing over the M-Film HUD.
- **Three-Stage Release Bundles**:
  - `01_EOSM2_Clean_ML_Base.zip`: Pure Magic Lantern base for verifying boot, menus, and buttons first.
  - `02_EOSM2_MFilm_023_TestBuild.zip`: Standard M-Film v0.2.3 bundle with built-in darkroom LUTs and film stocks.
  - `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`: M-Film v0.2.3 with the dynamic external profile loader (`fos_extprof`) and 20 baked SpektraFilm `(SF)` profiles pre-populated under `ML/MFILM/profiles/`.

---

## Quick Start (4 Steps)

1. **Verify Firmware & Prepare SD Card**: Confirm your EOS M2 is on official **Firmware 1.0.3**. Format a **≤ 32 GB FAT32** SD card inside the camera and make sure the battery is fully charged.
2. **Download Release Bundle**: Go to [GitHub Releases](https://github.com/Molinzzj/mfilm-eosm2/releases) and download `01_EOSM2_Clean_ML_Base.zip` (recommended for first-time sanity check), `02_EOSM2_MFilm_023_TestBuild.zip`, or `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` (includes the 20 pre-baked `(SF)` external film profiles), and verify the `.sha256` checksum.
3. **Extract to SD Card Root**: Unzip the archive directly into the **root directory** of the SD card so `autoexec.bin`, `ML-SETUP.FIR`, and the `ML/` folder sit directly at the top level (do not nest inside an extra folder). When using `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`, this also populates `ML/MFILM/profiles/*.cfg` (20 `(SF)` profiles) and `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt`, making all external stocks immediately selectable in the M-Film shelf upon boot.
4. **Load via Firmware Update**: Insert the card, switch the mode dial to a still-photo mode (`M` / `Av` / `Tv`), set image quality to **RAW** (required for M-Film's in-camera darkroom), open Canon's menu → **Firmware Ver. 1.0.3 → Firmware Update**, and run a non-persistent boot. Press **Trash / Delete** (or long-press **Down**) in LiveView to open Magic Lantern / M-Film.

For a detailed checklist covering the test builds, see [`docs/REAL_CAMERA_SMOKE_TEST.md`](./docs/REAL_CAMERA_SMOKE_TEST.md).

---

## Repository Layout

```text
.
├── platform/EOSM2.103/                  # Audited EOS M2 (1.0.3) platform port files
├── patches/
│   ├── 01-ml-simplified-eosm2.patch     # Minimal EOS M2 patch for magiclantern_simplified
│   ├── 02-mfilm-eosm2.patch             # Minimal EOS M2 patch for M-Film v0.2.3
│   └── 03-mfilm-extprof-loader.patch    # Clean-room GPL-2.0 external .cfg profile loader (fos_extprof)
├── scripts/
│   ├── bake_sd_profiles.py              # Offline black-box SpektraFilm baker -> ML/MFILM/profiles/*.cfg
│   ├── build_all.sh                     # Reproducible upstream clone + patch + build script
│   └── verify_m2_safety.py              # 6-gate static/binary safety & license auditor
├── docs/
│   ├── REAL_CAMERA_SMOKE_TEST.md        # Real-camera smoke test guide
│   ├── SAFETY_AUDIT_REPORT.md           # Static & binary audit report (PASS)
│   └── SPEKTRAFILM_BAKE_REPORT.md       # Offline SpektraFilm baking & ΔE2000 accuracy report
├── LICENSE                              # GNU General Public License v2.0
├── README.md                            # English documentation
└── README_CN.md                         # Chinese documentation
```

---

## How to Build from Source

### Prerequisites

- **ARM Toolchain**: `arm-none-eabi-gcc` (tested with xPack GNU Arm Embedded GCC `12.3.1-1.2`)
- **Host Tools**: `gcc`, `make`, `git`, `python3`, `zip`, `unzip`
- **Python 3 Packages**: `docutils`, `setuptools`, `numpy`, `segno` (plus `scipy` and `colour-science` if running `scripts/bake_sd_profiles.py` offline)

### One-Command Reproducible Build (`01` & `02` Bundles)

```bash
git clone https://github.com/Molinzzj/mfilm-eosm2.git
cd mfilm-eosm2
./scripts/build_all.sh
```

`scripts/build_all.sh` automatically:
1. Clones `reticulatedpines/magiclantern_simplified` (pinned commit `142472e9`) and `HNGSeries/mfilm-canon-film-simulation` (pinned commit `3c3986dd`, v0.2.3).
2. Copies `platform/EOSM2.103/` and applies `patches/01-ml-simplified-eosm2.patch`.
3. Builds `dist/01_EOSM2_Clean_ML_Base.zip`.
4. Applies `patches/02-mfilm-eosm2.patch` and `patches/03-mfilm-extprof-loader.patch` (compiling `fos_extprof` into `ML/modules/filmos.mo`), cleans `platform/EOSM2.103/`, and runs M-Film's `build_fork.sh EOSM2.103 --module`.
5. Packages `dist/02_EOSM2_MFilm_023_TestBuild.zip` and generates `.sha256` files.

### Optional: Bake External SpektraFilm Profiles (`03` Bundle)

Because SpektraFilm data assets are licensed under **CC BY-SA 4.0**, `.cfg` files are not committed to this GPL-2.0 repository. To generate the `03` bundle locally:

```bash
# 1. Clone SpektraFilm into an isolated directory outside this repo
git clone https://github.com/andreavolpato/spektrafilm.git /tmp/spektrafilm

# 2. Unpack the 02 bundle into a staging directory and bake 20 (SF) profiles into ML/MFILM/profiles/
mkdir -p /tmp/bundle_03 && unzip -q dist/02_EOSM2_MFilm_023_TestBuild.zip -d /tmp/bundle_03
python3 scripts/bake_sd_profiles.py \
  --spektrafilm-src /tmp/spektrafilm/src \
  --out-dir /tmp/bundle_03/ML/MFILM/profiles \
  --report docs/SPEKTRAFILM_BAKE_REPORT.md

# 3. Package 03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
(cd /tmp/bundle_03 && zip -r -9 "${OLDPWD}/dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip" .)
sha256sum dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip > dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip.sha256
```

### Run the Safety Audit

```bash
python3 scripts/verify_m2_safety.py dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
```

See [`docs/SAFETY_AUDIT_REPORT.md`](./docs/SAFETY_AUDIT_REPORT.md) for the full 6-gate audit output.

---

## External Film Profile Loader & License Isolation Architecture (GPL-2.0 / CC BY-SA 4.0)

To support third-party spectral film profiles without introducing any GPL-3.0 code into the GPL-2.0 Magic Lantern / M-Film firmware tree, this repository implements a strict **License Firewall + SD-Card Aggregation** architecture:

1. **Clean-Room GPL-2.0 Firmware Loader ([`patches/03-mfilm-extprof-loader.patch`](./patches/03-mfilm-extprof-loader.patch))**:
   - Adds `fos_extprof.c` / `fos_extprof.h` inside `ML/modules/filmos.mo`.
   - At boot or when opening the film shelf / darkroom, automatically scans `ML/MFILM/profiles/*.cfg` on the SD card and dynamically appends discovered parametric film stocks to the M-Film shelf.
   - Synthesizes the 33×33×33 Cineon-log 3D LUT on demand in the darkroom from each `.cfg`'s pure numerical parameters (`3×3` linear color matrix + RGB per-channel generalized logistic tone curves + `3×3` display output matrix).
   - **Zero boot-RAM overhead**: All parsing and profile arrays reside in `filmos.mo` runtime memory (`fos_port_alloc` / `tmp_malloc`), keeping `autoexec.bin` boot usage unchanged at `537,344 / 605,952 bytes` (`67.0 KB` headroom).
2. **Standalone Host-Side Black-Box Baker ([`scripts/bake_sd_profiles.py`](./scripts/bake_sd_profiles.py))**:
   - Runs an external spectral simulator (e.g. `andreavolpato/spektrafilm` cloned in a separate directory) as a pure black box with halation, grain, glare, and auto-exposure disabled, sampling a 496-patch synthetic target (24-patch ColorChecker + 6×6×6 RGB cube + 256-step greyscale ramp).
   - Fits each stock via `scipy.optimize.least_squares` into plain-text `ML/MFILM/profiles/*.cfg` files and emits `PROFILES_ATTRIBUTION.txt` (CC BY-SA 4.0) plus [`docs/SPEKTRAFILM_BAKE_REPORT.md`](./docs/SPEKTRAFILM_BAKE_REPORT.md) (mean 24-patch ColorChecker ΔE2000 = `2.42`, full 496-patch mean ΔE2000 = `1.93` across 20 stocks).
   - **No CC BY-SA 4.0 `.cfg` data files are mixed into this GPL-2.0 Git repository**; users can generate them locally with `scripts/bake_sd_profiles.py` and place them in `ML/MFILM/profiles/` on their SD card as a compliant Aggregation.

---

## Development Methodology & Safety Verification

This port was engineered using an **AI-assisted, rule-governed workflow (Google Antigravity)** combining a 3-way architectural diff migration with deterministic static verification:

- **Zero-Hallucination Address Preservation**: No firmware addresses were guessed or generated by AI. Every hardware offset in `platform/EOSM2.103/`—including all **135 `0xFF...` firmware stubs** in `stubs.S`, `ROMBASEADDR = 0xFF0C0000`, `RESTARTSTART = 0x44C100`, VRAM addresses, and `BGMT_*` key event codes—was preserved verbatim from the hardware-verified EOS M2 (1.0.3) port (`ccritix/magic-lantern`).
- **Deterministic 6-Gate Static Audit**: Prior to packaging, every build is validated by [`scripts/verify_m2_safety.py`](scripts/verify_m2_safety.py) to guarantee 100% symbol/address parity, DIGIC 5 startup memory headroom (`< 592 KB`), **zero automatic NVRAM Bootflag writes**, and **zero GPL-3.0 / third-party source contamination**.
- **Verification Status**: Cross-compilation and all 6 static safety/compliance checks have passed (`Pre-release`). Non-persistent loading via Canon's **Firmware Update** menu is strictly recommended while physical smoke testing on an EOS M2 (1.0.3) is completed.

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

