#!/usr/bin/env bash
# Non-interactive builder for the Stage 03 SD card bundle:
#   dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
#
# Clones andreavolpato/spektrafilm into an isolated temporary directory,
# invokes scripts/bake_sd_profiles.py to distill 20 parametric .cfg profiles
# plus PROFILES_ATTRIBUTION.txt (CC BY-SA 4.0), and merges them with the
# Stage 02 M-Film v0.2.3 binaries. Zero .cfg data files are written into the
# Git source tree.
#
# Usage:
#   ./scripts/build_03_bundle.sh [REPORT_PATH]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
BASE_02_ZIP="${DIST_DIR}/02_EOSM2_MFilm_023_TestBuild.zip"
OUT_03_ZIP="${DIST_DIR}/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip"
REPORT_PATH="${1:-${REPO_ROOT}/docs/SPEKTRAFILM_BAKE_REPORT.md}"
SPEKTRAFILM_URL="https://github.com/andreavolpato/spektrafilm.git"

for tool in git python3 unzip zip sha256sum; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "ERROR: Required tool '${tool}' not found in PATH." >&2
        exit 1
    fi
done

if [ ! -f "${BASE_02_ZIP}" ]; then
    echo "ERROR: Missing Stage 02 bundle: ${BASE_02_ZIP}" >&2
    echo "       Run ./scripts/build_all.sh first." >&2
    exit 1
fi

TMP_BASE="$(mktemp -d "${TMPDIR:-/tmp}/mfilm-bundle03.XXXXXX")"
trap 'rm -rf "${TMP_BASE}"' EXIT

SF_DIR="${TMP_BASE}/spektrafilm"
STAGE_DIR="${TMP_BASE}/bundle_03"
PROFILES_DIR="${STAGE_DIR}/ML/MFILM/profiles"

echo "==> [1/4] Cloning andreavolpato/spektrafilm into isolated temp dir..."
git clone --depth 1 "${SPEKTRAFILM_URL}" "${SF_DIR}"

echo "==> [2/4] Unpacking Stage 02 M-Film bundle..."
mkdir -p "${STAGE_DIR}"
unzip -q "${BASE_02_ZIP}" -d "${STAGE_DIR}"

echo "==> [3/4] Baking 20 SpektraFilm profiles into ML/MFILM/profiles/..."
mkdir -p "${PROFILES_DIR}"
python3 "${REPO_ROOT}/scripts/bake_sd_profiles.py" \
    --spektrafilm-src "${SF_DIR}/src" \
    --out-dir "${PROFILES_DIR}" \
    --report "${REPORT_PATH}"

CFG_COUNT="$(find "${PROFILES_DIR}" -maxdepth 1 -type f -name '*.cfg' | wc -l | tr -d ' ')"
if [ "${CFG_COUNT}" -ne 20 ]; then
    echo "ERROR: Expected 20 .cfg files in ${PROFILES_DIR}, found ${CFG_COUNT}." >&2
    exit 1
fi
if [ ! -f "${PROFILES_DIR}/PROFILES_ATTRIBUTION.txt" ]; then
    echo "ERROR: Missing PROFILES_ATTRIBUTION.txt in ${PROFILES_DIR}." >&2
    exit 1
fi
if [ ! -s "${STAGE_DIR}/ML/MODULES/EOSM2103.SYM" ]; then
    echo "ERROR: Missing or empty ML/MODULES/EOSM2103.SYM in Stage 03 bundle." >&2
    exit 1
fi

echo "==> [4/4] Packaging ${OUT_03_ZIP} and generating SHA256..."
rm -f "${OUT_03_ZIP}" "${OUT_03_ZIP}.sha256"
(
    cd "${STAGE_DIR}"
    zip -r -9 "${OUT_03_ZIP}" . >/dev/null
)
(
    cd "${DIST_DIR}"
    sha256sum "$(basename "${OUT_03_ZIP}")" > "$(basename "${OUT_03_ZIP}").sha256"
)

echo "==> Done: ${OUT_03_ZIP}"
cat "${OUT_03_ZIP}.sha256"
