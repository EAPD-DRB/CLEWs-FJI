# Fiji calibration protocol

This protocol governs the next stage. It prevents the raw reference from being
silently overwritten and distinguishes endogenous historical reproduction
from history imposed by constraints.

## Version boundary

`Fiji_CLEWs_Global` is the immutable raw reference. Calibration work must use
a separately named working case and dated build record. A calibrated release
must not replace the raw inputs, results, MUIO archive, diagnostics, or
pre-tracking backups.

Every change package must state:

- the affected model entities and parameters;
- the prior and new values;
- source, assumption, and calculation IDs;
- whether it is structural, observed exogenous history, calibrated, or a
  scenario assumption;
- which calibration outcomes it was permitted to use;
- the diagnostic and solver results before and after the change.

## Historical-variable classes

Every historical quantity must be assigned one class before use:

| Class | Meaning | Fiji examples |
|---|---|---|
| `E` — endogenous test output | The solver must reproduce it without an outcome lock | generation by plant/category, fuel use, renewable share, emissions, hydro use |
| `J` — justified exogenous condition | Information genuinely known to the historical decision maker/model | demand, installed fleet, commissioning and retirement, observed rainfall/inflow, documented outages, delivered fuel prices |
| `H` — history fixed | The result is imposed or reconstructed by equality/near-equality constraints | forced generation or crop area; allowed only in an explicitly labelled accounting diagnostic |
| `S` — scenario assumption | A future choice or uncertainty, not historical evidence | renewable target, fuel-price path, technology costs, climate pathway |

The main historical score is calculated from class `E` outcomes. Class `H`
results must never be described as independent historical reproduction.

## Evidence workflow

1. Register the source in `../data_sources/DATA_SOURCES.md`.
2. Retain a page/table locator, boundary, units, extraction date, and conflict
   note under `../data_sources/evidence/`.
3. Reconcile units and statistical boundaries before calculating model inputs
   or targets.
4. Register modeller choices in `../data_sources/ASSUMPTIONS.csv`.
5. Register formulas in `../data_sources/CALCULATIONS.csv`.
6. Link the affected parameter through
   `../data_sources/MODEL_DATA_MAP.csv`.
7. Add the dated action to `HISTORY.md`.

Conflicting sources remain separate until reconciled. Do not average them or
select one silently. In particular, the 2024 EFL headline, detailed
generation table, customer demand, IPP, and Fiji-wide energy-account
boundaries must be resolved explicitly.

## Proposed historical split

- **2020:** initialization and, after extending the model, calibration
  evidence.
- **2020–2022:** permitted calibration period.
- **2023–2024:** held-out validation period.

Parameters are frozen before the held-out run. Observed 2023–2024 exogenous
conditions may be supplied, but their class `E` outcomes may not be used for
tuning. Any exception changes the validation design and must be documented
before results are reported.

## Required structural work before tuning

1. Represent the principal separate electricity systems rather than one
   national copper plate.
2. Create a traceable unit or plant fleet with commissioning, retirement,
   fuel, capacity, and availability.
3. Represent hydro resources and operating constraints at a resolution
   supported by retained rainfall, inflow, or reservoir evidence.
4. Reconcile customer demand, station use, network losses, IPPs, household
   generation, and off-grid supply.
5. Constrain biomass through a documented cane–bagasse–mill balance.
6. Represent thermal fuels, heat rates, prices, and availability explicitly.
7. Increase temporal resolution only as far as the evidence and intended use
   justify.

Structural changes are not “calibration parameters” and must be completed and
verified before numerical tuning begins.

## Calibration and validation records

Before the first tuning run, create:

- a machine-readable evidence table for 2020–2024;
- a parameter register containing bounds and reasons for every tunable value;
- declared error metrics and tolerances by outcome;
- an automated run-and-score script;
- a raw-versus-structural-rebuild comparison;
- a dated calibration build record under `history/calibration/`.

Recommended reported metrics include absolute error, percentage error where
the denominator is stable, energy-balance closure, fuel-to-generation
consistency, and renewable-share error. Results must be shown for every year,
not only as a five-year average.

## Claim boundary

With public evidence alone, the intended first release is an annual or
wet/dry-season electricity–hydro–bagasse backcast. It must not claim hourly
dispatch, reliability, or precise reconstruction of historical investment
choice. Wider land and water calibration should be released only after its own
evidence and held-out tests are complete.
