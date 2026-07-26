#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/path/to/CLEWs_Global" >&2
  exit 2
fi

TARGET_DIR="$(cd "$1" && pwd)"
SHAPE_DIR="${TARGET_DIR}/workflow/submodules/CLEWs_GAEZ/GAEZ_Processing/user_input/shapefile"
DOWNLOAD_URL="https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_FJI_shp.zip"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

mkdir -p "${SHAPE_DIR}"
curl -L "${DOWNLOAD_URL}" -o "${TEMP_DIR}/gadm41_FJI_shp.zip"
unzip -o "${TEMP_DIR}/gadm41_FJI_shp.zip" -d "${SHAPE_DIR}"

echo "GADM 4.1 Fiji boundaries installed in ${SHAPE_DIR}."
