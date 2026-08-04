# Fiji v2.9 data sources and ledger routing

`SOURCES.csv` catalogs observations and immediate solved-case lineage.
`CALCULATIONS.csv` records full-precision inputs, formulas, dependencies and
all 2020-2050 outputs. `ASSUMPTIONS.csv` separates scenario and boundary
choices from observations. `MODEL_MAP.csv` connects each active source-file
parameter family to evidence. `GAPS.csv` states what cannot yet be supported.
`CHANGES.csv` records the model and documentation history.

Source hierarchy for the new layers:

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
explicitly excluded. Source SHA cells remain blank under the inherited
intentional-omission policy; the retained input snapshots preserve their own
recorded download/input hashes where available.
