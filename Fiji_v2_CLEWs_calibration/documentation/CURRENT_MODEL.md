# Fiji v2: current model

## Status

The active case is `WebAPP/DataStorage/Fiji_v2`. It contains 130
technologies, 103 commodities, four time slices, and a continuous 2020–2050
horizon. The most recent stored solve is the 27 July post-OHC
`Historical_Backcast`. It is Optimal and uses the current v2.0.1 inputs.
The objective and calibration metrics are unchanged from the pre-OHC result.

The source/input package on `EAPD-DRB/CLEWs-FJI` `main` is v2.0.1. Its
portable `Fiji_v2_v2.0.1_MUIO.zip` contains the corrected editable inputs and
excludes solver results. The latest tagged release remains v2.0.0, while the
main-branch v2.0.1 inputs and diagnostics are recertified in
`history/calibration/PHASE_0_RECERTIFICATION_2026-07-27.md`.

| Component | Current v2 status |
|---|---|
| Annual electricity grid supply | Calibrated on 2020–2022 and held-out tested on 2023–2024 |
| Hydro/thermal/IPP/wind fleet | Corrected to documented Fiji aggregate capacities |
| Land and crops | Structurally active; historically uncalibrated |
| Water and climate | Structurally active; historically unvalidated |
| Cross-nexus links | Present but not covered by the v2 calibration claim |
| Commodity topology | Phase 1A audited; classified warnings remain for Phases 1B–1D |
| Investment economics | Executable but not decision-grade calibrated |

The assessment grade is **Good, 76.4/100, medium confidence** for annual
national grid-supply energy only.

Phase 1A's read-only topology audit is complete. It classifies all 103
commodities and changes no input. Seventy-one are connected; 32 are produced,
unconsumed and undemanded. The audit found no consumed-but-unproduced
commodity and no positive demand without supply. Its strict mode fails
intentionally until the classified structural warnings are resolved. See
`history/structural/PHASE_1A_TOPOLOGY_AUDIT_2026-07-27.md`.

## Historical experiment

- Calibration: 2020–2022.
- Held-out validation: 2023–2024.
- Total reported generation is the exogenous annual supply requirement (`J`).
- Historical fleet stocks and the prohibition on unobserved 2020–2024 power
  investments are `J`.
- Hydro, thermal dispatch, IPP/biomass output, wind, and renewable share are
  model results.
- Calibration-period biomass and wind comparisons are `H` because their
  availability factors were estimated from 2020–2022 outcomes.
- Those factors are frozen before the 2023–2024 `E` validation.

The historical generation rows are not equality-constrained. The validator
finds zero positive lower-equals-upper activity or capacity locks.

## Main numerical changes from the raw reference

| Item | Raw reference | Fiji v2 |
|---|---:|---:|
| First model year | 2021 | 2020 |
| Existing hydro | 209 MW | 133.4 MW |
| Existing thermal/oil | 74 MW | 182 MW |
| Existing wind | 10 MW | 9.8 MW |
| Existing biomass/IPP | 69.7 MW | 34 MW |
| Biomass availability | 0.50 | 0.225644641 |
| Wind availability, 2020–2024 | 0.90 | 0.005909670 |
| 2024 electricity requirement | 3.58 PJ | 4.3880616 PJ |
| Malformed duplicate transmission branch | Present but inactive | Removed |
| Unsupported other-hydrocarbons branch | Present but inactive | Removed |

The `OHC` → `DEMINDOHC` → `INDOHC` branch was also removed. It had no
Fiji supply, specified demand, cost, availability, capacity, or emissions
data. The documented UNSD evidence does not establish material Fiji combustion
of the corresponding fuel category.

The hydro capacity factors and wet/dry shape are inherited without tuning.
Future demand preserves the raw growth path and is rebased to the observed
2024 grid-supply boundary. Corrected future residual-capacity paths preserve
the raw retirement ratios. Both are scenario assumptions, not observations.

## Most recent stored results

The MUIO solve is Optimal with objective `-1387.57013590`.

For material held-out generation categories (hydro, thermal, and IPP/biomass),
2023–2024 MAPE is 9.94%. Renewable-share MAE is 5.13 percentage points.
The largest material miss is 2024 thermal generation at 19.37%; the model
also underproduces 2024 hydro by 16.52%. This reflects the absence of
year-specific inflow, reservoir, and outage conditions.

## Permitted interpretation

Fiji v2 is conditionally suitable for exploratory annual renewable-pathway
screening after adding explicit scenario cost, fuel, demand, target, and
weather sensitivities. It is unsuitable for official investment decisions,
hourly dispatch, operational adequacy, reliability, or a claim that the full
CLEWs nexus has been calibrated.
