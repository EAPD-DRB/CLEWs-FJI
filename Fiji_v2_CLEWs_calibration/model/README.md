# Fiji v2 model tables

`inputs/` contains the active Fiji v2 OSeMOSYS-compatible parameter CSVs.
They are rebuilt from the immutable raw package by
`../scripts/build_fiji_v2.py`.

The authoritative solved v2 implementation is the MUIO
`Historical_Backcast` run under `WebAPP/DataStorage/Fiji_v2` and in the
portable archive `../muio/Fiji_v2_v2.0.0_MUIO.zip`.

The raw package's pre-calibration `data.txt`, solution, solver record, and
result CSVs were moved to `../diagnostics/raw_reference/`. They are comparison
evidence and must not be read as results from the v2 inputs.
