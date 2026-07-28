# Fiji v2 CLEWs calibration

Fiji v2 is a traceable annual electricity backcast built from the immutable
raw `Fiji_CLEWs_Global` case. It covers 2020–2050, uses 2020–2022 for
calibration, freezes the selected parameters, and tests 2023–2024 as held-out
history.

The last formal scorecard is **Good (76.4/100), medium confidence** for the
pre-Phase-1D annual national grid-supply scope. Phase 1D is implemented and
its dedicated validator passes 15/15 checks, but it is not described as fully
validated: the broader Fiji validator passes 14/15 because 2024 thermal
generation is 20.65% above observation against a 20% threshold. Across the
held-out years, material generation has 10.30% mean absolute percentage error
and renewable share has 5.44 percentage-point mean absolute error.

Phase 1B closes observed 2020–2024 public-water delivery and aggregate surface
abstraction/loss accounting. Phase 1C decomposes 2020–2024 grid electricity
into commercial, industrial, central-grid residential and direct overhead
demand and supplies independent 2025–2050 sector projections. Phase 1D routes
reported FSC cane through an explicit mill, co-produces exportable bagasse,
and separates the documented 25 MW bagasse and 9 MW wood-residue power stocks.
This is not a calibration of the full land-water-agriculture nexus, mill
engineering, investment economics, island networks, or operational
reliability.

## Start here

- Current model: `documentation/CURRENT_MODEL.md`
- Calibration protocol and forcing rules:
  `documentation/CALIBRATION_PROTOCOL.md`
- Retained evidence and extraction notes:
  `data_sources/evidence/calibration/`
- Parameter register:
  `data_sources/evidence/calibration/parameter_register.csv`
- Sources, assumptions, calculations, and model map:
  `data_sources/`
- Known limitations: `documentation/KNOWN_LIMITATIONS.md`
- Calibration assessment:
  `diagnostics/calibration_runs/historical_fit/scorecard.md`
- Most recent post-OHC technical validation:
  `diagnostics/calibration_runs/validation_summary.json`
- Phase 1A commodity topology audit:
  `diagnostics/topology/2026-07-27_phase1a/REPORT.md`
- Phase 1B public-water record:
  `documentation/history/structural/PHASE_1B_PUBLIC_WATER_2026-07-27.md`
- Phase 1B live validation:
  `diagnostics/calibration_runs/phase1b/live_validation_summary.json`
- Phase 1C electricity-demand method:
  `documentation/history/structural/PHASE_1C_BOTTOM_UP_ELECTRICITY_DEMAND_2026-07-27.md`
- Phase 1C source locators and checksums:
  `data_sources/evidence/energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md`
- Phase 1C detailed calculation:
  `data_sources/calculation_notes/PHASE_1C_BOTTOM_UP_ELECTRICITY.md`
- Phase 1C live validation:
  `diagnostics/calibration_runs/phase1c/live_validation_summary.json`
- Phase 1C lineage validation:
  `diagnostics/calibration_runs/phase1c/data_lineage_validation_summary.json`
- Phase 1D implementation and validation record:
  `documentation/history/structural/PHASE_1D_CANE_BAGASSE_ELECTRICITY_2026-07-28.md`
- Phase 1D source locators and checksums:
  `data_sources/evidence/energy/PHASE_1D_SOURCE_EXTRACTS_2026-07-28.md`
- Phase 1D detailed calculation:
  `data_sources/calculation_notes/PHASE_1D_CANE_BAGASSE_ELECTRICITY.md`
- Phase 1D live validation:
  `diagnostics/calibration_runs/phase1d/live_validation_summary.json`
- Phase 1D broader technical validation:
  `diagnostics/calibration_runs/phase1d/live_technical_validation_summary.json`
- Phase 1D topology audit:
  `diagnostics/topology/2026-07-28_phase1d_live/REPORT.md`
- Chronological record: `documentation/HISTORY.md`
- Current cross-laptop handoff: `HANDOFF-2026-07-28.md`

## Version boundary

- Immutable raw reference: `Fiji_CLEWs_Global`
- Fiji v2 build package: `Fiji_v2_CLEWs_calibration`
- Active MUIO case: `WebAPP/DataStorage/Fiji_v2`
- Most recent solved run: `Phase1D_Legacy_Removal`
- Current result-free MUIO archive: `muio/Fiji_v2_v2.0.5_MUIO.zip`

The raw package, raw MUIO case, retained sources, and v2 evidence are never
silently overwritten. `scripts/build_fiji_v2.py` starts from the raw inputs
and records every v2 transformation in a machine-readable manifest.

The v2.0.5 source/input package retains the Phase 1B public-water closure and
Phase 1C sector-electricity path and adds the Phase 1D physical
cane–bagasse–electricity connection. The superseded aggregate biomass shell
is removed. Its portable archive contains editable inputs and excludes saved
solver results and regenerated view caches. The 28 July live solve is
Optimal; the retained pre-Phase-1D grade is not silently extended to the new
model.

## What is supplied and what is tested

Observed total grid generation is supplied as the annual electricity
requirement, and the documented 2021 fleet is supplied as the historical
installed stock. These are justified exogenous conditions (`J`), not
independent reproduction.

Hydro, thermal residual dispatch, bagasse and wood-residue generation, wind
generation, and renewable share remain model results. Bagasse generation is
bounded by reported cane throughput and an IRENA engineering export
coefficient. The wood-residue availability and annual resource cap, and the
wind availability factor, use 2020–2022 generation evidence, so those
calibration-period comparisons are conservatively classed `H`. The same
frozen parameters are tested endogenously (`E`) in 2023–2024. No positive
lower-equals-upper generation or capacity outcome locks were introduced.

## Reproduce

From the MUIOGO repository root, using its existing virtual environment:

```bash
.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/build_fiji_v2.py

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1b_public_water.py \
  --source-case Fiji_v2 --target-case Fiji_v2 \
  --sync-csv-inputs

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1c_bottom_up_demand.py \
  --source-case Fiji_v2 --target-case Fiji_v2 \
  --checkpoint bottom-up --sync-csv-inputs

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1d_cane_bagasse.py \
  --source-case Fiji_v2 --target-case Fiji_v2 \
  --checkpoint physical --sync-csv-inputs --write-evidence

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_v2 --check

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/solve_muiogo_case.py \
  Phase1D_Cane_Bagasse \
  --case Fiji_v2 \
  --muiogo-root .

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/score_historical_fit.py \
  --case-folder WebAPP/DataStorage/Fiji_v2 \
  --run Phase1D_Cane_Bagasse \
  --output-dir \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/diagnostics/calibration_runs/phase1d/live_historical_fit

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/validate_fiji_v2.py \
  --case-folder WebAPP/DataStorage/Fiji_v2 \
  --run Phase1D_Cane_Bagasse \
  --fit-folder \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/diagnostics/calibration_runs/phase1d/live_historical_fit \
  --output \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/diagnostics/calibration_runs/phase1d/live_technical_validation_summary.json

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/validate_fiji_phase1d_cane_bagasse.py \
  --muiogo-root . \
  --baseline-case Fiji_v2 --baseline-run Phase1C_BottomUp \
  --accounting-case Fiji_v2_Phase1D_Accounting_Test \
  --accounting-run Phase1D_Accounting \
  --physical-case Fiji_v2 --physical-run Phase1D_Cane_Bagasse

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/validate_fiji_data_lineage.py

.venv/bin/python \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/audit_fiji_topology.py \
  --case-folder WebAPP/DataStorage/Fiji_v2 \
  --run Phase1D_Cane_Bagasse --phase 1D \
  --output-dir \
  /path/to/CLEWs-FJI/Fiji_v2_CLEWs_calibration/diagnostics/topology/2026-07-28_phase1d_live
```

If the named run already exists, solve it with `--reuse-existing`. The reserve
proxy check must report zero mismatches before a solve. The general validator
currently exits nonzero on the documented 2024 thermal-generation check; this
is a retained finding, not a reproduction failure.

To regenerate the frozen annual Phase 1C calculation evidence after producing
the accounting checkpoint:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1c_bottom_up_demand.py \
  --evidence-only \
  --source-case Fiji_v2 \
  --comparison-case Fiji_v2_Phase1C_Accounting_Test
```

The topology audit is read-only. It exits successfully with classified
warnings by default; add `--strict` when unresolved warnings should return
exit code 2.

To reapply only the documented Fiji structural exclusions without cloning the
raw reference, recalibrating, or solving:

```bash
python3 Fiji_v2_CLEWs_calibration/scripts/build_fiji_v2.py \
  --prune-excluded-branches-only
```

## Plain interpretation

Fiji v2 now makes the annual sugar-cane-to-grid-electricity connection
explicit: cane availability limits bagasse generation, while wood residue has
a separate resource bound. The model broadly reproduces the annual
hydro/thermal/IPP balance outside the calibration years without fixing those
yearly outcomes, but the 2024 thermal result narrowly misses the declared
tolerance. It does not show that the optimizer knows Fiji's future. Use it as
a starting point for transparent scenario stress-testing, not as a single
best-path oracle.
