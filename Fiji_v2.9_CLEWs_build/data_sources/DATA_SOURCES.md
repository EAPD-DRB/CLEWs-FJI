# Fiji v2.9 data sources and ledger routing

`SOURCES.csv` catalogs observations and immediate solved-case lineage.
`CALCULATIONS.csv` records full-precision inputs, formulas, dependencies and
all 2020-2050 outputs. `ASSUMPTIONS.csv` separates scenario and boundary
choices from observations. `MODEL_MAP.csv` connects each active source-file
parameter family to evidence. `GAPS.csv` states what cannot yet be supported.
`CHANGES.csv` records the model and documentation history.

Recovered inherited lineage:

1. The exact raw-build archive and the complete Fiji v2.5 handoff are retained
   under `evidence/v25_lineage/archives/`, with verified SHA-256 values and an
   archive manifest.
2. The raw GAEZ request set is reconstructed from the six pinned catalogue
   tables: 72 crop rasters (36 high-input and 36 low-input) plus the two
   retained base rasters. Exact filenames and URLs are recorded in
   `GAEZ_FJI_RASTER_CACHE_MANIFEST.csv`.
3. The exact `FAOSTAT_2020.csv`, `FAOSTAT_production_2020.csv`, ten selected
   Fiji rows, SSP2 workbook, selected `data!A553:Y553` row and reconstructed
   2021-2050 annual index are retained under `evidence/raw_clews_lineage/`.
4. The full Fiji v2, public-water Phase 1B, electricity-demand Phase 1C and
   cane/bagasse Phase 1D evidence, scripts and original three-ledger records
   are preserved inside the v2.5 handoff. Phase 1E was experimental and was
   not promoted into the inherited case.

See `calculation_notes/v25_lineage_recovery_2026-08-05.md` for archive hashes,
pinned upstream revisions, row selections and the remaining evidence limits.

Source hierarchy for the v2.8-v2.9 layers:

1. UN WPP 2024 medium annual population for Fiji.
2. FAOSTAT 2021-2023 Food Balance Sheets and Supply Utilization Accounts for
   resident food availability and crop-equivalent conversions.
3. UN Comtrade 2025 physical net weights for crop and fish imports/exports,
   with Fiji Bureau of Statistics annual trade as a national cross-check.
4. Solved Fiji v2.7 for crop-control duals and Fisheries service calibration;
   solved Fiji v2.8 as the unchanged v2.9 control.
5. Explicit assumptions for constant per-capita pathways, conversions,
   retained imports, screening costs and absent biological/site constraints.

Cross-checks are not silently averaged into selected values. Tourism is
explicitly excluded. Historical remote-only source rows can remain unhashed,
but recovered archives and exact retained input files now carry verified
SHA-256 values and local-file pointers in `SOURCES.csv`.
