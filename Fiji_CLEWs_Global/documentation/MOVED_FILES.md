# Folder reorganization record

On 25 July 2026, Fiji documentation and evidence were reorganized to follow
the Philippines v12 tracking structure. Current guidance, source records,
assumptions, calculations, model mappings, dated evidence, and diagnostics are
now separated. No numerical model parameter or active MUIO JSON value was
changed.

## Build package

| Previous location | Current location |
|---|---|
| `MODEL_CARD.md` | `documentation/history/raw_build/MODEL_CARD_2026-07-24.md` |
| `CALIBRATION_HANDOFF.md` | `documentation/history/calibration/CALIBRATION_HANDOFF_2026-07-24.md` |
| `REPRODUCE.md` | `documentation/history/raw_build/REPRODUCE_RAW_BUILD_2026-07-24.md` |
| `MUIO_IMPORT.md` | `documentation/history/raw_build/MUIO_IMPORT_2026-07-24.md` |
| `UPSTREAM.lock` | `documentation/history/raw_build/UPSTREAM_LOCK_2026-07-24.txt` |
| `sources/SOURCE_MANIFEST.csv` | `documentation/history/raw_build/SOURCE_MANIFEST_ORIGINAL_2026-07-24.csv` |
| `sources/CALIBRATION_CANDIDATES.csv` | `data_sources/evidence/raw_baseline/CALIBRATION_CANDIDATES_2026-07-24.csv` |
| `sources/CROP_PROXY_MAPPING.csv` | `data_sources/evidence/raw_baseline/CROP_PROXY_MAPPING_2026-07-24.csv` |
| `overrides/PATCH_NOTES.md` | `documentation/history/raw_build/PATCH_NOTES_2026-07-24.md` |
| `assessment/*` | `diagnostics/calibration_assessment/2026-07-24_raw/*` |
| `geospatial/FJI_LandCover_byCluster_summary.csv` | `geospatial/summary_stats/FJI_LandCover_byCluster_summary.csv` |
| `geospatial/FJI_Parameter_byCluster_summary.csv` | `geospatial/summary_stats/FJI_Parameter_byCluster_summary.csv` |
| `geospatial/clustering_results_*.csv` | `geospatial/summary_stats/clustering_results_*.csv` |

## New current records

- `documentation/CURRENT_MODEL.md`
- `documentation/MODEL_STRUCTURE.md`
- `documentation/KNOWN_LIMITATIONS.md`
- `documentation/CALIBRATION_PROTOCOL.md`
- `documentation/HISTORY.md`
- `data_sources/DATA_SOURCES.md`
- `data_sources/ASSUMPTIONS.csv`
- `data_sources/CALCULATIONS.csv`
- `data_sources/MODEL_DATA_MAP.csv`
- `config/upstream_versions.json`
- `WebAPP/DataStorage/Fiji_CLEWs_Global/README.md`
- `WebAPP/DataStorage/Fiji_CLEWs_Global/documentation/README.md`

Historical contents were preserved. References inside dated records may use
their original locations and should be interpreted using this migration table.
