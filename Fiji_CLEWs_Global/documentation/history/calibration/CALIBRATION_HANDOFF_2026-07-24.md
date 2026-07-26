# Fiji calibration handoff

The raw model intentionally preserves upstream behavior. None of the
observations below is applied as a parameter, multiplier, or constraint.

## Principal raw-model gaps

| Domain | Raw behavior | Historical evidence | Interpretation |
|---|---|---|---|
| Power capacity | 209 MW hydro, 74 MW oil, 10 MW wind, 69.7 MW biomass | 133.4, 182, 9.8, and 34 MW respectively | Upstream capacity composition differs substantially |
| 2021 generation | 625.3 GWh hydro and 305.3 GWh biomass; negligible oil/wind | 544, 61, 327, and 0.2 GWh for hydro, biomass, oil, and wind | Generic dispatch and resource limits do not reproduce Fiji |
| 2021 energy CO₂ | Approximately zero in the raw solution | Oil generation implies positive emissions historically | Historical fuel use is not represented |
| Sugar-cane area | About 1,569 km² | About 380 km² | GAEZ potential-yield and commodity definitions require investigation |
| Cassava area | About 73 km² | About 36 km² | Raw yield/production relationship differs from reported data |
| Other crops | About 68 km² | About 117 km² | Aggregation and proxy definitions require review |

Exact comparisons are in `diagnostics/raw_vs_history.csv`.

## Data required for later calibration

1. Plant-level capacity, commissioning, retirement, and outage histories.
2. Annual and monthly generation by plant and technology for multiple years.
3. Electricity demand, losses, hourly/seasonal profiles, and separate island
   systems.
4. Fuel prices, efficiencies, fuel consumption, and biomass supply constraints.
5. Hydropower inflows, reservoir operation, spill, and monthly availability.
6. Crop production, harvested area, fresh/dry-matter conversions, irrigation,
   and farm yields for several years.
7. Basin-level withdrawals, irrigation infrastructure, return flows, and
   environmental constraints.

## Later-stage calibration principle

Calibrate underlying drivers over several years, then remove outcome locks and
test a held-out period. Historical capacity may be supplied as an observed
stock, but generation, crop area, water use, and emissions should be evaluated
endogenously wherever possible.

If constraints are introduced later, version them in a separate calibrated
scenario. Do not overwrite this raw reference case.
