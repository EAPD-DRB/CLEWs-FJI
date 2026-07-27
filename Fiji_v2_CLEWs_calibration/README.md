# Fiji v2 CLEWs calibration

Fiji v2 is a traceable annual electricity backcast built from the immutable
raw `Fiji_CLEWs_Global` case. It covers 2020–2050, uses 2020–2022 for
calibration, freezes the selected parameters, and tests 2023–2024 as held-out
history.

The result is **Good (76.4/100), medium confidence** for the claimed annual
national grid-supply energy scope. In the held-out years, material generation
has 9.94% mean absolute percentage error and renewable share has 5.13
percentage-point mean absolute error. Phase 1B additionally closes observed
2020–2024 public-water delivery and aggregate surface abstraction/loss
accounting. This is not a calibration of the full land-water-agriculture
nexus, investment economics, island networks, or operational reliability.
Phase 1C additionally decomposes 2020–2024 grid electricity into commercial,
industrial, central-grid residential and direct overhead demand and supplies
independent 2025–2050 sector projections.

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
- Chronological record: `documentation/HISTORY.md`
- Current cross-laptop handoff: `HANDOFF-2026-07-27.md`

## Version boundary

- Immutable raw reference: `Fiji_CLEWs_Global`
- Fiji v2 build package: `Fiji_v2_CLEWs_calibration`
- Active MUIO case: `WebAPP/DataStorage/Fiji_v2`
- Most recent solved run: `Phase1C_BottomUp`
- Current result-free MUIO archive: `muio/Fiji_v2_v2.0.3_MUIO.zip`

The raw package, raw MUIO case, retained sources, and v2 evidence are never
silently overwritten. `scripts/build_fiji_v2.py` starts from the raw inputs
and records every v2 transformation in a machine-readable manifest.

The v2.0.3 source/input patch retains the Phase 1B public-water closure and
adds the Phase 1C sector-electricity accounting and bottom-up demand path. Its
portable archive contains editable inputs and excludes saved solver results.
The 27 July live solve preserves the historical energy fit metrics and grade.

## What is supplied and what is tested

Observed total grid generation is supplied as the annual electricity
requirement, and the documented 2021 fleet is supplied as the historical
installed stock. These are justified exogenous conditions (`J`), not
independent reproduction.

Hydro, thermal residual dispatch, IPP/biomass generation, wind generation,
and renewable share remain model results. The biomass and wind availability
factors use 2020–2022 generation evidence, so those calibration-period
comparisons are conservatively classed `H`. The same frozen parameters are
tested endogenously (`E`) in 2023–2024. No positive
lower-equals-upper generation or capacity outcome locks were introduced.

## Reproduce

From the repository root:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/build_fiji_v2.py

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1b_public_water.py \
  --source-case Fiji_v2 --target-case Fiji_v2 \
  --sync-csv-inputs

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/apply_fiji_phase1c_bottom_up_demand.py \
  --source-case Fiji_v2 --target-case Fiji_v2 \
  --checkpoint bottom-up --sync-csv-inputs

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_v2 --check

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/solve_muiogo_case.py \
  Phase1C_BottomUp \
  --case Fiji_v2 \
  --muiogo-root /path/to/MUIOGO

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/score_historical_fit.py \
  --case-folder /path/to/MUIOGO/WebAPP/DataStorage/Fiji_v2 \
  --run Phase1C_BottomUp

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/validate_fiji_v2.py \
  --case-folder /path/to/MUIOGO/WebAPP/DataStorage/Fiji_v2 \
  --run Phase1C_BottomUp

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/validate_fiji_phase1c_bottom_up_demand.py \
  --baseline-case Fiji_v2_Phase1B_Test \
  --bottom-up-case Fiji_v2 --bottom-up-run Phase1C_BottomUp

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/validate_fiji_data_lineage.py

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/audit_fiji_topology.py \
  --case-folder /path/to/MUIOGO/WebAPP/DataStorage/Fiji_v2 \
  --run Phase1C_BottomUp --phase 1C \
  --output-dir \
  Fiji_v2_CLEWs_calibration/diagnostics/topology/2026-07-27_phase1c_live
```

If the named run already exists, solve it with `--reuse-existing`. The reserve
proxy check must report zero mismatches before a solve.

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

Fiji v2 shows that this model structure can reproduce the broad annual
hydro/thermal/IPP balance outside the calibration years without fixing those
yearly outcomes. It does not show that the optimizer knows Fiji's future.
Use it as a starting point for transparent scenario stress-testing, not as a
single best-path oracle.
