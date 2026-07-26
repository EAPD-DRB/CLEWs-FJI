# Fiji CLEWs Global model

This package is the tracked build record for the Fiji CLEWs Global model. The
current model is the technically solved, **uncalibrated** raw case covering
2021–2050. It couples an OSeMOSYS Global energy system to Fiji-specific
GeoCLEWs land, crop, water, and climate processing.

The folder follows the Philippines v12 documentation and provenance
conventions. Current guidance is separated from dated evidence, and active
model objects are linked to explicit source, assumption, and calculation
records. No numerical model parameter was changed during this reorganization.

## Start here

- Current model description: `documentation/CURRENT_MODEL.md`
- Model structure: `documentation/MODEL_STRUCTURE.md`
- Calibration protocol: `documentation/CALIBRATION_PROTOCOL.md`
- Data sources: `data_sources/DATA_SOURCES.md`
- Assumptions: `data_sources/ASSUMPTIONS.csv`
- Calculations used by the model: `data_sources/CALCULATIONS.csv`
- Model-to-source map: `data_sources/MODEL_DATA_MAP.csv`
- Known limitations: `documentation/KNOWN_LIMITATIONS.md`
- Chronological history: `documentation/HISTORY.md`
- File-migration record: `documentation/MOVED_FILES.md`

Dated build, import, assessment, and calibration-handoff records remain under
`documentation/history/` and `diagnostics/calibration_assessment/`. They are
evidence of how the model evolved, not a description of a later calibrated
case.

## Delivered model

- Portable MUIO case:
  `muio/Fiji_CLEWs_Global_raw-v1.0.0_MUIO.zip`
- Active-case navigation:
  `WebAPP/DataStorage/Fiji_CLEWs_Global/README.md`
- Raw OSeMOSYS/CLEWs inputs and results: `model/`
- Reproducible importer workbook:
  `muio/Fiji_CLEWs_Global_MUIO_import.xlsx`
- Raw build instructions:
  `documentation/history/raw_build/REPRODUCE_RAW_BUILD_2026-07-24.md`
- MUIO import record:
  `documentation/history/raw_build/MUIO_IMPORT_2026-07-24.md`
- Pinned upstream versions: `config/upstream_versions.json`
- Country adaptations: `overrides/`
- Immutable pre-tracking backups: `backups/`

## Representation

The active raw case contains 132 technologies and 107 commodities over
2021–2050. It uses one national electricity node, four agro-climatic land
clusters, and four time slices: wet/dry season crossed with day/night.

The model intentionally preserves the generated upstream country values. It
does not force historical generation, crop area, water use, or emissions.
Observed values in the evidence and diagnostic folders are comparison data
only.

## Provenance rules

Every future edit must be recorded before it is treated as part of the
calibrated model:

1. Add or update the publication or dataset in
   `data_sources/DATA_SOURCES.md`.
2. Record modeller choices in `data_sources/ASSUMPTIONS.csv`.
3. Record formulas and transformations in
   `data_sources/CALCULATIONS.csv`.
4. Link the affected model entity and parameter through
   `data_sources/MODEL_DATA_MAP.csv`.
5. Add a dated entry to `documentation/HISTORY.md`.
6. Retain calculation evidence under `data_sources/evidence/` and
   machine-readable checks under `diagnostics/`.

An empty source field never means “common knowledge.” Unknown lineage is
labelled as a documentation gap. Observed outcomes used only for testing must
remain distinguishable from exogenous historical conditions supplied to the
model.

## Raw-model verification

- Upstream CBC solve: **Optimal**, objective `-240.33220528`.
- MUIO `Raw` solve: **Optimal**, objective `-2267.3628049`.
- MUIO `Raw_ReserveProxy` solve: **Optimal**, objective
  `-2261.49703717`.
- Input integrity: zero duplicate indices across 33,179 input rows.
- Historical-forcing audit: **Pass**, with no added calibration locks.

Run the raw validator from the repository root:

```bash
python3 Fiji_CLEWs_Global/scripts/validate_model.py
```

The reserve-capacity proxy must also be checked after any relevant MUIO input
or scenario edit:

```bash
python3 Fiji_CLEWs_Global/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_CLEWs_Global --check
```

## Interpretation

The raw results show how the pinned global defaults behave after structural
adaptation to Fiji. They do not reproduce Fiji's historical electricity
system and must not be presented as a forecast or used to rank policies.

The next permitted stage is a separately versioned calibration build following
`documentation/CALIBRATION_PROTOCOL.md`. The raw inputs, results, diagnostics,
and backups remain the immutable reference against which every later change is
audited.
