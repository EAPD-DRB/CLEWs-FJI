# Fiji v2.9 schema-ledger update

This documentation-only change copies the validated Fiji v2.7 six-ledger
package forward and adds the complete v2.8 crop and v2.9 Fisheries demand/trade
lineage. It does not change any live model source parameter or solver result.

The six canonical tables are SOURCES.csv, CALCULATIONS.csv, ASSUMPTIONS.csv,
MODEL_MAP.csv, GAPS.csv and CHANGES.csv. Old production-based crop-demand maps
and fixed Fisheries service-demand maps are explicitly superseded. The
retained input snapshots and final validation reports make every annual value,
HS observation, conversion, diagnostic and limitation inspectable.
