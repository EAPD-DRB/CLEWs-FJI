# Fiji v2 CLEWs calibration

Fiji v2 is a traceable annual electricity backcast built from the immutable
raw `Fiji_CLEWs_Global` case. It covers 2020–2050, uses 2020–2022 for
calibration, freezes the selected parameters, and tests 2023–2024 as held-out
history.

The result is **Good (76.4/100), medium confidence** for the claimed annual
national grid-supply energy scope. In the held-out years, material generation
has 9.94% mean absolute percentage error and renewable share has 5.13
percentage-point mean absolute error. This is not a calibration of the full
land-water-agriculture nexus, investment economics, island networks, or
operational reliability.

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
- Most recent technical validation, before the OHC-only prune:
  `diagnostics/calibration_runs/validation_summary.json`
- Chronological record: `documentation/HISTORY.md`

## Version boundary

- Immutable raw reference: `Fiji_CLEWs_Global`
- Fiji v2 build package: `Fiji_v2_CLEWs_calibration`
- Active MUIO case: `WebAPP/DataStorage/Fiji_v2`
- Most recent solved run: `Historical_Backcast` (pre-OHC-only prune)
- Current result-free MUIO archive: `muio/Fiji_v2_v2.0.1_MUIO.zip`

The raw package, raw MUIO case, retained sources, and v2 evidence are never
silently overwritten. `scripts/build_fiji_v2.py` starts from the raw inputs
and records every v2 transformation in a machine-readable manifest.

The v2.0.1 source/input patch removes the dormant unsupported
`OHC -> DEMINDOHC -> INDOHC` branch. Its portable archive contains the
corrected editable inputs and excludes saved solver results. The most recent
stored solve and calibration score predate that dormant-branch correction;
exact solve/input parity has not yet been recertified.

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
  Fiji_v2_CLEWs_calibration/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_v2 --update

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/solve_muiogo_case.py \
  Historical_Backcast

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/score_historical_fit.py

/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/validate_fiji_v2.py
```

If the named run already exists, solve it with `--reuse-existing`. The reserve
proxy check must report zero mismatches before a solve.

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
