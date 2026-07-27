# Phase 1C bottom-up electricity calculation

**Active version:** Fiji v2.0.3
**Calculation IDs:** `C-1C-HIST-ELECTRICITY`, `C-1C-COM`, `C-1C-IND`,
`C-1C-RES`, `C-1C-OVERHEAD`, `C-MUIO-04`

## Inputs and boundaries

Publication identities, page/table locators, retrieved-file hashes and
extract hashes are in
`../evidence/energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md`.
The historical input extract is
`../evidence/energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv`.

The model boundary is annual EFL gross grid supply. Household own generation
is subtracted from reported domestic use because it does not pass through the
central grid. Cooking is not a separate service because MICS supplies shares,
not an annual energy quantity.

## Historical transformation

For year `y` in 2020–2024:

```text
RES(y) = domestic_total(y) - household_own_generation(y)

ELC_direct(y)
  = EFL_gross(y) - COM(y) - IND(y) - RES(y)
  = distribution_loss(y) + reconciliation_residual(y)
```

The four components sum exactly to the pre-Phase-1C gross requirement.

## Future transformation

The commercial and industrial projections are rebased to the observed 2024
FBoS quantities:

```text
COM(y) = COM(2024) * 1.026^(y - 2024)
IND(y) = IND(2024) * 1.020^(y - 2024)
```

Residential demand uses a household/appliance-stock index:

```text
households(y) = 182282 * 1.0038^(y - 2013)

urban_grid_households(y)
  = households(y) * urban_fraction(y) * 0.939

rural_grid_households(y)
  = households(y) * [1 - urban_fraction(y)] * 0.742

stock_kWh(y)
  = urban_grid_households(y) * urban_kWh_per_grid_household(y)
  + rural_grid_households(y) * rural_kWh_per_grid_household(y)

RES(y) = RES(2024) * stock_kWh(y) / stock_kWh(2024)
```

`urban_fraction(y)` and all appliance adoption and efficiency shares are
linearly interpolated between the LEDS milestones. The per-household baskets
sum refrigerator, lighting, air-conditioning where applicable, television
and other-appliance electricity:

```text
urban kWh/household
  = refrigerator_adoption * refrigerator_intensity
  + lighting_intensity
  + air_conditioning_adoption * air_conditioning_intensity
  + 0.90 * television_intensity
  + 500

rural kWh/household
  = refrigerator_adoption * refrigerator_intensity
  + lighting_intensity
  + 0.90 * television_intensity
  + 500
```

Conventional and efficient appliance intensities are blended by the LEDS
MEPS turnover shares. The executable milestone dictionaries are in
`household_driver()` in
`../../scripts/apply_fiji_phase1c_bottom_up_demand.py`.

Direct grid overhead uses the 2024 observed/calculated accounting ratio:

```text
overhead_ratio
  = [distribution_loss(2024) + reconciliation_residual(2024)]
  / [COM(2024) + IND(2024) + RES(2024)]
  = 0.119232103417779

ELC_direct(y) = overhead_ratio * [COM(y) + IND(y) + RES(y)]
```

Each positive component receives the inherited normalized four-slice profile.
The reserve proxy then sums all four demand commodities before calculating
the maximum annual demand rate.

## Outputs

The executable writes:

- `model/inputs/SpecifiedAnnualDemand.csv`;
- `model/inputs/SpecifiedDemandProfile.csv`;
- zero mode-1 adapter costs in `model/inputs/VariableCost.csv`;
- MUIO source parameters `RYC.json`, `RYCTs.json` and `RYTM.json`; and
- the derived reserve proxy in `RYCn.json` and
  `reserve_margin_proxy.json`.

The frozen annual audit table is
`../evidence/energy/fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv`,
SHA-256
`f58c1ec3df4b6017966a2ad542256dd2f3e1f847837bd8bdc722ab9175ac181a`.

## Controls and tolerances

- Historical four-component reconciliation tolerance: `1e-10 PJ`.
- Demand-profile normalization tolerance: `1e-10`.
- Accounting-control objective difference from Phase 1B: exactly zero at
  reported solver precision.
- Reserve-proxy status: `CURRENT`, zero mismatches.
- Dedicated Phase 1C validation: 15/15 passed.
- General Fiji technical validation: 15/15 passed.

Machine-readable reports are under
`../../diagnostics/calibration_runs/phase1c/`. The accounting control is a
regression control, not an independent forecast. The bottom-up path is a
documented base scenario and remains subject to the LEDS ±10% sensitivity.
