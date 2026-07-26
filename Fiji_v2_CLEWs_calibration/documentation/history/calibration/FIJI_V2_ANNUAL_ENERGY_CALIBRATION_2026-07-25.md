# Fiji v2 annual energy calibration — 25 July 2026

## Decision

Fiji v2 is released as a **Good (76.4/100), medium-confidence** calibration
for annual national grid-supply energy only. It is not a calibrated full
CLEWs nexus or an operational electricity model.

## Immutable starting point

- Raw build package: `Fiji_CLEWs_Global`
- Raw MUIO case: `WebAPP/DataStorage/Fiji_CLEWs_Global`
- V2 package: `Fiji_v2_CLEWs_calibration`
- V2 MUIO case: `WebAPP/DataStorage/Fiji_v2`

The v2 build script recopies raw parameter inputs before applying documented
transformations. Raw results and sources are not overwritten.

## Evidence

Generation comes from Energy Fiji Limited's 2024 Annual Report, printed page
88. Fleet capacities come from the Government of Fiji Renewable Energy
Integration Investment Plan, printed pages 23–24 and Table 3.1. Both PDFs are
retained and SHA-256 hashed in
`data_sources/evidence/calibration/SOURCE_EXTRACTS.md`.

## Protocol frozen before validation

- 2020–2022: calibration.
- 2023–2024: held-out validation.
- EFL total generation: supplied annual grid requirement (`J`).
- Documented aggregate fleet: supplied historical stock (`J`).
- Hydro shape and availability: inherited without outcome tuning.
- Biomass/IPP availability: estimated from mean 2020–2022 IPP output, then
  frozen.
- Wind availability ceiling: estimated from mean 2020–2022 wind output, then
  frozen through 2024.
- Historical power-generation investment: blocked from 2020–2024.
- Annual generation outcomes: not equality-constrained.

The structural grid conduit `PWRTRNFJIXX` is excluded from the investment
block. An initial diagnostic solve incorrectly blocked this conduit and became
infeasible because the importer represents its lossless capacity with a
999,999 GW dummy investment. That run is retained under
`diagnostics/calibration_runs/failed_01_pwrtrn_blocked/`; the exception is
explicit in the parameter register and build script.

## Solve

`Historical_Backcast` solved Optimal with CBC:

`Optimal - objective value -1387.57013590`

The automated validator confirms:

- continuous and identical CSV/MUIO 2020–2050 horizons;
- 0 duplicate indices across 34,253 input rows;
- 0 positive lower-equals-upper history locks;
- matching retained-source hashes;
- current reserve-margin proxy;
- held-out material generation MAPE below 15%; and
- no held-out material generation error above 20%.

## Historical results

| Metric | Calibration 2020–2022 | Validation 2023–2024 |
|---|---:|---:|
| Material generation MAPE | 9.12% | 9.94% |
| Material generation MAE | 41.89 GWh | 42.10 GWh |
| Renewable-share MAE | 4.07 percentage points | 5.13 percentage points |

The largest held-out material miss is 2024 thermal generation at 19.37%.
Hydro is 16.52% low in 2024. The EFL report documents unusually strong 2024
hydro production and rainfall/inflow conditions; Fiji v2 has no year-specific
inflow or reservoir state, so that miss is retained rather than tuned away.

Wind percentages are unstable because observed annual output is below 1 GWh.
Wind remains in the full comparison with very low materiality weight and is
excluded from aggregate material-generation MAPE.

## Forcing profile

Weighted comparison evidence is:

- 84.1% endogenous (`E`);
- 5.1% justified exogenous condition (`J`);
- 10.8% history-fixed/calibration-dependent (`H`).

Calibration-period biomass and wind are `H`. The frozen 2023–2024 outcomes
are `E`, providing an independent replacement test. Total electricity supply
and installed fleet receive no endogenous-reproduction claim.

## Use boundary

Conditionally suitable:

- exploratory annual renewable generation and capacity pathway screening,
  after explicit demand, cost, fuel, target, weather, and project
  sensitivities are added.

Unsuitable:

- official procurement or investment decisions;
- a definitive least-cost “best path”;
- hourly dispatch, adequacy, reliability, or reserve studies; and
- any claim that land, water, agriculture, climate, or cross-nexus history has
  been calibrated.

## Reproduction

The exact commands are in the top-level `README.md`. The machine-readable
transformation record is
`diagnostics/calibration_runs/build_manifest.json`, and the final assessment
is `diagnostics/calibration_runs/historical_fit/scorecard.md`.
