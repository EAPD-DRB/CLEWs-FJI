# Fiji v2: current model

## Status

The active case is `WebAPP/DataStorage/Fiji_v2`. It contains 131
technologies, 104 commodities, four time slices, and a continuous 2020–2050
horizon. The most recent stored solve is the 27 July
`Phase1C_BottomUp` run. It is Optimal and uses the current Phase 1C inputs.
The held-out annual energy metrics are unchanged from Phase 0.

The next prepared source/input package is v2.0.3. Its portable MUIOGO archive
contains the editable Phase 1C inputs and excludes solver results. Earlier
archives remain available for comparison.

| Component | Current v2 status |
|---|---|
| Annual electricity grid supply | Observed 2020–2024 commercial, industrial, central-grid residential and overhead accounting; sector projections from 2025 |
| Hydro/thermal/IPP/wind fleet | Corrected to documented Fiji aggregate capacities |
| Land and crops | Structurally active; historically uncalibrated |
| Public water | 2020–2024 delivery and aggregate surface abstraction/loss accounting validated |
| Other water and climate | Structurally active; historically unvalidated |
| Cross-nexus links | Present but not covered by the v2 calibration claim |
| Commodity topology | 76 connected; 28 produced/unconsumed/undemanded; 23 inactive end-use output stubs |
| Investment economics | Executable but not decision-grade calibrated |

The assessment grade is **Good, 76.4/100, medium confidence** for annual
national grid-supply energy only.

Phase 1B closes public water without claiming a full water calibration.
Observed billed/carted public delivery is demanded in 2020–2024, the
surface-water route accounts for reported abstraction and losses, and the
groundwater route is structurally explicit but inactive pending evidence.
The Phase 1C audit classifies all 104 commodities: 76 are connected and 28
are produced, unconsumed and undemanded. Its strict mode still fails
intentionally until later classified warnings are resolved. See
`history/structural/PHASE_1C_BOTTOM_UP_ELECTRICITY_DEMAND_2026-07-27.md`.

Phase 1C now applies that split. Commercial and industrial projections use the
Government of Fiji LEDS BAU-unconditional rates, while residential demand uses
a 2024-normalized household/appliance stock index. Direct grid demand carries
loss and station-use/boundary overhead. An accounting-only control proves that
the historical split changes neither objective nor non-adapter dispatch.
Cooking remains inactive because the MICS shares do not supply a useful-energy
quantity or efficiency set.

The source-to-parameter audit trail for this active demand path is in
`../data_sources/evidence/energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md`;
the executable formulas are in
`../data_sources/calculation_notes/PHASE_1C_BOTTOM_UP_ELECTRICITY.md`.

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
| 2050 electricity requirement | 8.47 PJ raw; 10.38 PJ Phase 1B rebased | 7.2373759 PJ Phase 1C bottom-up |
| Sector electricity demand | Inactive | Commercial, industrial and central-grid residential active |
| Malformed duplicate transmission branch | Present but inactive | Removed |
| Unsupported other-hydrocarbons branch | Present but inactive | Removed |
| Public-water demand | Absent | Observed billed/carted delivery, 2020–2024 |
| Public groundwater input | Commercial-service electricity | Raw-groundwater chain; quarantined |
| Water metadata | `PJ` | `km3` |

The `OHC` → `DEMINDOHC` → `INDOHC` branch was also removed. It had no
Fiji supply, specified demand, cost, availability, capacity, or emissions
data. The documented UNSD evidence does not establish material Fiji combustion
of the corresponding fuel category.

The hydro capacity factors and wet/dry shape are inherited without tuning.
Future electricity demand now follows documented sector assumptions rebased
to observed 2024 sector use. Corrected future residual-capacity paths still
preserve the raw retirement ratios. Both are scenario assumptions, not
observations.

## Most recent stored results

The live Phase 1C MUIO solve is Optimal with objective `-1573.67149091`.
The accounting-only checkpoint is exactly equal to the Phase 1B objective
`-1387.57010517` and changes none of 7,409 non-adapter activity rows. The
bottom-up objective difference reflects the changed future electricity path
and must not be interpreted as a welfare improvement.

For material held-out generation categories (hydro, thermal, and IPP/biomass),
2023–2024 MAPE is 9.94%. Renewable-share MAE is 5.13 percentage points.
The largest material miss is 2024 thermal generation at 19.37%; the model
also underproduces 2024 hydro by 16.52%. This reflects the absence of
year-specific inflow, reservoir, and outage conditions.

## Permitted interpretation

Fiji v2 is conditionally suitable for exploratory annual renewable-pathway
screening after adding explicit scenario cost, fuel, demand, target, and
weather sensitivities. Phase 1C supplies an auditable base electricity-demand
path, not a forecast. The model remains unsuitable for official investment
decisions, hourly dispatch, operational adequacy, reliability, basin
hydrology, or a claim that the full CLEWs nexus has been calibrated.
