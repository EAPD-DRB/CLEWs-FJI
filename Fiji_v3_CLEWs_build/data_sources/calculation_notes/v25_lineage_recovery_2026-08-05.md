# Fiji v2.5 lineage recovery for the v2.9 schema ledger

## Recovery result

The earlier `SRC_FIJI_V25_CASE` gap was recoverable from this repository. The
raw Fiji CLEWs build, Fiji v2 calibration package, v2.4 case and v2.5 handoff
were retained with source extracts, scripts, calculation notes, model maps and
validation records. This recovery freezes those records within the v2.9
package and connects the active inherited parameter families to their
original sources.

No live `WebAPP/DataStorage/Fiji_v2.9` parameter file, packaged model input,
solver result or MUIO archive was changed. The pre-recovery six-table ledger
is preserved under
`documentation/history/schema_ledger_pre_v25_recovery_2026-08-05/`.

## Frozen authoritative packages

`evidence/v25_lineage/archives/Fiji_CLEWs_Global_source_raw_pre_tracking_2026-07-25.zip`
is the immutable raw source package: 190 files, SHA-256
`6f53a3788a374ad86ebbc7ae2a41df5a8bc47d002aacc6a64d3b3b88d112c51d`.

`evidence/v25_lineage/archives/Fiji_v2_v2.5.0_HANDOFF_2026-07-29.zip` is the
complete result-free v2.5 handoff: 321 files, SHA-256
`3dfe81379dc249cde99886be52923787064a7caefc4bde915f6b1eb4546ca729`.
It contains the v2 and v2.4 source cases, all v2.5 source JSONs, the complete
calibration evidence directory, three legacy ledgers, calculation notes,
implementation and validation scripts, and Phase 1K validation records.

## Raw workflow lineage

The raw build pins:

- `DeltaE/CLEWs_Global` at
  `8df78c66be104e446f84a7dbb0df1c0a4fda4080`;
- `OSeMOSYS/CLEWs_GAEZ` at
  `30ec12e6524dc9c8ce474ffe1a467508f992007f`;
- `OSeMOSYS/clewsy` at
  `6eefaf2abc6d91917c0fddfeea373db37443a8dd`; and
- `OSeMOSYS/osemosys_global` at
  `036fdd07cc0dc31df1649cdc1689a8aa35a83a36`.

The GADM 4.1 Fiji boundary URL, national land-area normalization to 18,273
km², four-cluster configuration, wet/dry and day/night mapping, raw MUIO
import assumptions and reserve proxy are retained in the raw package.

## Exact GAEZ, FAOSTAT and SSP2 recovery

Six pinned GAEZ catalogue tables are retained under
`evidence/raw_clews_lineage/gaez_input_tables/`. Replaying the exact Fiji
`collect.py` ordering gives 72 surviving crop-cache filenames and URLs:
36 high-input and 36 low-input rasters across `SGC`, `CON`, `YAM`, `CAS`,
`RCP` and `PTS`, three metrics and two water modes. `VEG` and `FRU` occur in
the crop-code mapping but have no matching generic GAEZ catalogue rows.
The workflow aggregates the additional available proxy layers into `OTH`.
Together with `precipitation prc.tif` and `LCType_ncb.tif`, the reconstructed
raw cache contains 74 files, matching the retained historical cache count.

The exact `FAOSTAT_2020.csv` and `FAOSTAT_production_2020.csv` inputs are
retained. `FAOSTAT_FJI_2020_SELECTION.csv` records the ten selected Fiji
crops, harvested area, production, flags, crop proxies, final model group and
physical source lines.

The exact population workbook is retained as
`iamc_db_POP_Countries.xlsx`. The selected record is `data!A553:Y553`:
Model `IIASA-WiC POP`, Scenario `SSP2`, Region `FJI`, Variable `Population`,
Unit `million`. `SSP2_FJI_ANNUAL_INDEX_2021_2050.csv` reproduces the raw
workflow's annual interpolation and normalization to its 2021 start year.

## Recovered calibrated lineage

The v2.5 handoff establishes the following active source chains inherited by
v2.9:

- Fiji v2 electricity: EFL 2024 total generation and the Fiji Renewable
  Energy Integration Investment Plan for the 2021 fleet, with documented
  MWh-to-PJ, residual-capacity and wind-availability calculations;
- Phase 1B public water: Fiji Bureau of Statistics Water Account 2024,
  including annual delivery, surface abstraction and loss ratios;
- Phase 1C electricity demand: EFL, the Fiji energy physical supply-and-use
  account, Fiji LEDS and Fiji MICS, with exact historical reconciliation and
  commercial, industrial, residential and overhead projection formulas;
- Phase 1D cane/bagasse/wood electricity: FSC annual operating data, the
  IRENA exportable-bagasse coefficient, the REI fleet split and EFL IPP
  purchases; and
- Phases 1F–1K: the source rows already present in the v2.9 ledger, now backed
  by the frozen v2.5 handoff rather than absent legacy extracts.

Phase 1E hydro conditioning was experimental and was not promoted; it remains
inside the archive for historical transparency but is not mapped as an active
v2.9 source.

## Verification

`scripts/verify_fiji_v25_lineage_recovery.py` is a read-only verifier. It
checks 20 retained evidence hashes, both archive file counts and required
contents, all 72 GAEZ request rows, the ten FAOSTAT selections, the selected
SSP2 workbook row and annual index, and the seven authoritative live v2.9
source JSONs. It passes on the recovered package. The canonical six-ledger
validator also passes and verifies 19 ledger-linked evidence digests.

The general `validation/ledger_live_consistency.json` report was created
before the final Fisheries activity ceilings and therefore records the earlier
`RYT.json` hash. The authoritative post-ceiling hash is
`ff8e8c9598c062767cc0bd76c4b0c1c7ff9d72eafff587f7d630d14ade5957cd`,
which is independently recorded as both candidate and live in the later
passing `validation/fisheries_bounds_v29_final.json`. The recovery verifier
uses that final hash; the other six authoritative source hashes are unchanged.

## Remaining limitations

The recovery closes the earlier blanket “original external lineage for
unchanged Fiji_v2.5 parameters” and “legacy local evidence extracts” gaps.
Remaining `GAPS.csv` rows describe genuine model/calibration limitations or
unavailable higher-resolution observations. The original downloaded bytes of
the 72 temporary GAEZ crop rasters and their per-file checksums are not
retained; their exact filenames, URLs and source-table rows are retained.
