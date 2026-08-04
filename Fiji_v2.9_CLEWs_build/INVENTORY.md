# Fiji v2.9 schema-ledger package inventory

## Canonical ledgers

- `data_sources/SOURCES.csv`: observations, solved-case lineage and validation evidence.
- `data_sources/CALCULATIONS.csv`: full-precision formulas, inputs and outputs.
- `data_sources/ASSUMPTIONS.csv`: scenario, boundary and conversion choices.
- `data_sources/MODEL_MAP.csv`: source-file and parameter mappings.
- `data_sources/GAPS.csv`: absent evidence and model limitations.
- `data_sources/CHANGES.csv`: v2.7, v2.8 and v2.9 change history.

## Retained evidence

- `data_sources/snapshots/`: immutable v2.8 crop and v2.9 Fisheries input snapshots.
- `model/inputs/`: v2.8/v2.9 manifests and an inventory of every live Fiji v2.9 JSON source/support file.
- `validation/`: crop, Fisheries, solver-chain, schema and live-consistency reports.
- `data_sources/calculation_notes/`: readable equation-first classification and design notes.

## Reproduction and integrity

- `documentation/REPRODUCE.md`: build, solve and validation commands.
- `scripts/validate_provenance.py`: canonical six-ledger schema validator.
- `scripts/validate_fiji_v29_schema_ledger.py`: ledger-to-live semantic validator.
- `config/config.yaml`: identifies Fiji_v2.9 / SC_0 / 2020-2050.

This is a working-tree documentation package, not a frozen delivery archive.
Source SHA cells and a portable archive checksum are intentionally omitted;
the retained local evidence copies and seven authoritative live source files
are checked byte-for-byte by the semantic validator.
