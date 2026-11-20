#!/usr/bin/env bash
# Reproducible end-to-end build script for Canon EOS M2 (Firmware 1.0.3)
# Magic Lantern (magiclantern_simplified) + M-Film v0.2.3 (--module mode).
#
# Requirements:
#   - arm-none-eabi-gcc (tested with xPack GNU Arm Embedded GCC 12.3.1)
#   - gcc (host compiler for fontblob), make, git, python3, zip, unzip
#   - Python packages: docutils, setuptools, numpy, segno (for ML/M-Film asset generation)
#
# Usage:
#   ./scripts/build_all.sh [BUILD_DIR]
#   Default BUILD_DIR is ./build

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${1:-${REPO_ROOT}/build}"
DIST_DIR="${REPO_ROOT}/dist"

ML_REPO_URL="https://github.com/reticulatedpines/magiclantern_simplified.git"
ML_COMMIT="142472e95054d73640f50789ac0fd66325499d82"

MFILM_REPO_URL="https://github.com/HNGSeries/mfilm-canon-film-simulation.git"
MFILM_COMMIT="3c3986dddb45b8b9acd2f7bc84e7c89c1b194f84"

ML_DIR="${BUILD_DIR}/magiclantern_simplified"
MFILM_DIR="${BUILD_DIR}/mfilm-canon-film-simulation"

# Verify required host tools
for tool in git make gcc arm-none-eabi-gcc arm-none-eabi-objcopy arm-none-eabi-readelf arm-none-eabi-nm python3 zip; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "ERROR: Required tool '${tool}' not found in PATH." >&2
        exit 1
    fi
done

export ARM_BINPATH="$(dirname "$(command -v arm-none-eabi-gcc)")"

mkdir -p "${BUILD_DIR}" "${DIST_DIR}" "${HOME}/ml"

echo "==> [1/5] Fetching pinned upstream repositories..."
if [ ! -d "${ML_DIR}/.git" ]; then
    git clone "${ML_REPO_URL}" "${ML_DIR}"
fi
git -C "${ML_DIR}" fetch --all --tags
git -C "${ML_DIR}" reset --hard "${ML_COMMIT}"
git -C "${ML_DIR}" clean -fdx

if [ ! -d "${MFILM_DIR}/.git" ]; then
    git clone "${MFILM_REPO_URL}" "${MFILM_DIR}"
fi
git -C "${MFILM_DIR}" fetch --all --tags
git -C "${MFILM_DIR}" reset --hard "${MFILM_COMMIT}"
git -C "${MFILM_DIR}" clean -fdx

echo "==> [2/5] Applying EOSM2.103 platform port to magiclantern_simplified..."
cp -a "${REPO_ROOT}/platform/EOSM2.103" "${ML_DIR}/platform/EOSM2.103"
git -C "${ML_DIR}" apply --whitespace=nowarn "${REPO_ROOT}/patches/01-ml-simplified-eosm2.patch"

echo "==> [3/5] Building clean Magic Lantern base for EOSM2.103..."
make -C "${ML_DIR}/platform/EOSM2.103" -j"$(nproc)"
BASE_ZIP="${DIST_DIR}/01_EOSM2_Clean_ML_Base.zip"
rm -f "${BASE_ZIP}"
(
    cd "${ML_DIR}/platform/EOSM2.103/build/zip"
    if [ -d "ML/modules" ]; then
        mkdir -p "ML/MODULES"
        mv ML/modules/* ML/MODULES/ 2>/dev/null || true
        rmdir "ML/modules"
    fi
    if [ ! -s "ML/MODULES/EOSM2103.SYM" ]; then
        echo "ERROR: Missing or empty ML/MODULES/EOSM2103.SYM in Stage 01 zip dir." >&2
        exit 1
    fi
    cp -f "${ML_DIR}/platform/EOSM2.103/ML-SETUP.FIR" ./ML-SETUP.FIR
    zip -r -9 "${BASE_ZIP}" . >/dev/null
)
echo "    Clean base package: ${BASE_ZIP}"

echo "==> [4/5] Applying EOSM2.103 & external profile loader patches to M-Film v0.2.3..."
git -C "${MFILM_DIR}" apply --whitespace=nowarn "${REPO_ROOT}/patches/02-mfilm-eosm2.patch"
git -C "${MFILM_DIR}" apply --whitespace=nowarn "${REPO_ROOT}/patches/03-mfilm-extprof-loader.patch"
# Clean platform build directory before M-Film fork overlay
make -C "${ML_DIR}/platform/EOSM2.103" clean
ML_SRC="${ML_DIR}" bash "${MFILM_DIR}/ml-dev/build_fork.sh" EOSM2.103 --module

echo "==> [5/5] Packaging M-Film v0.2.3 SD card bundle..."
MFILM_OUT="${MFILM_DIR}/ml-dev/out/fork-EOSM2.103"
MFILM_ZIP="${DIST_DIR}/02_EOSM2_MFilm_023_TestBuild.zip"
rm -f "${MFILM_ZIP}"
(
    cd "${MFILM_OUT}"
    if [ -d "ML/modules" ]; then
        mkdir -p "ML/MODULES"
        mv ML/modules/* ML/MODULES/ 2>/dev/null || true
        rmdir "ML/modules"
    fi
    if [ ! -s "ML/MODULES/EOSM2103.SYM" ]; then
        echo "ERROR: Missing or empty ML/MODULES/EOSM2103.SYM in Stage 02 output." >&2
        exit 1
    fi
    cp -f "${ML_DIR}/platform/EOSM2.103/ML-SETUP.FIR" ./ML-SETUP.FIR
    zip -r -9 "${MFILM_ZIP}" . >/dev/null
)
echo "    M-Film package: ${MFILM_ZIP}"

echo "==> Generating SHA256 checksums..."
(
    cd "${DIST_DIR}"
    sha256sum "01_EOSM2_Clean_ML_Base.zip" > "01_EOSM2_Clean_ML_Base.zip.sha256"
    sha256sum "02_EOSM2_MFilm_023_TestBuild.zip" > "02_EOSM2_MFilm_023_TestBuild.zip.sha256"
)

echo "==> Done! Run scripts/verify_m2_safety.py to audit the build before testing on camera."
