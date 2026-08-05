# Fiji v2.9 schema-ledger update

This documentation-only change copies the validated Fiji v2.7 six-ledger
package forward and adds the complete v2.8 crop and v2.9 Fisheries demand/trade
lineage. It does not change any live model source parameter or solver result.

The six canonical tables are SOURCES.csv, CALCULATIONS.csv, ASSUMPTIONS.csv,
MODEL_MAP.csv, GAPS.csv and CHANGES.csv. Old production-based crop-demand maps
and fixed Fisheries service-demand maps are explicitly superseded. The
retained input snapshots and final validation reports make every annual value,
HS observation, conversion, diagnostic and limitation inspectable.

On 2026-08-05 the inherited raw-build-to-v2.5 lineage was recovered from the
repository's exact raw source archive and complete v2.5 handoff. The recovery
adds local hashed evidence and ledger mappings only; it does not alter the live
model. Archive identities, pinned upstream revisions, GAEZ raster selections,
FAOSTAT rows, the exact SSP2 workbook row and remaining evidence limits are in
`v25_lineage_recovery_2026-08-05.md`.
