#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/path/to/CLEWs_Global" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="$(cd "$1" && pwd)"
EXPECTED_COMMIT="8df78c66be104e446f84a7dbb0df1c0a4fda4080"
CURRENT_COMMIT="$(git -C "${TARGET_DIR}" rev-parse HEAD)"

if [[ "${CURRENT_COMMIT}" != "${EXPECTED_COMMIT}" ]]; then
  echo "Expected CLEWs Global ${EXPECTED_COMMIT}, found ${CURRENT_COMMIT}." >&2
  exit 1
fi

cp "${BUNDLE_DIR}/overrides/config.yaml" \
  "${TARGET_DIR}/config/config.yaml"
cp "${BUNDLE_DIR}/overrides/workflow/envs/clews_global.yaml" \
  "${TARGET_DIR}/workflow/envs/clews_global.yaml"
cp "${BUNDLE_DIR}/overrides/workflow/scripts/clewsy.py" \
  "${TARGET_DIR}/workflow/scripts/clewsy.py"

GEO_ROOT="${TARGET_DIR}/workflow/submodules/CLEWs_GAEZ/GAEZ_Processing"
cp "${BUNDLE_DIR}/overrides/workflow/submodules/CLEWs_GAEZ/config/config.yaml" \
  "${GEO_ROOT}/user_input/config.yaml"
cp "${BUNDLE_DIR}/overrides/workflow/submodules/CLEWs_GAEZ/workflow/scripts/collect.py" \
  "${GEO_ROOT}/libs/collect.py"
cp "${BUNDLE_DIR}/overrides/workflow/submodules/CLEWs_GAEZ/workflow/scripts/process_land_cells.py" \
  "${GEO_ROOT}/libs/process_land_cells.py"
cp "${BUNDLE_DIR}/overrides/workflow/submodules/CLEWs_GAEZ/workflow/scripts/spatial_clustering.py" \
  "${GEO_ROOT}/libs/spatial_clustering.py"
cp "${BUNDLE_DIR}/overrides/workflow/submodules/CLEWs_GAEZ/resources/data/Crop_code.csv" \
  "${GEO_ROOT}/Data/Crop_code.csv"

cp "${BUNDLE_DIR}/overrides/workflow/submodules/clewsy/clewsy/src/build/clewsy.py" \
  "${TARGET_DIR}/workflow/submodules/clewsy/src/build/clewsy.py"

echo "Fiji CLEWs overrides applied to ${TARGET_DIR}."
