# Fiji v2 calibration protocol

This protocol governs Fiji v2. It prevents the raw reference from being
silently overwritten and distinguishes endogenous historical reproduction
from history imposed by constraints.

## Implemented v2 scope

The first v2 release implements the public-data-feasible subset: an annual
national grid-supply electricity–hydro–IPP backcast. The more ambitious
structural items below remain requirements for a later
plant/grid/seasonal release; they are not silently treated as completed.

The implemented split is 2020–2022 calibration and 2023–2024 held-out
validation. Selected parameters were frozen before the held-out results were
scored. The assessment is in
`../diagnostics/calibration_runs/historical_fit/scorecard.md`.

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

## Historical split

- **2020:** initialization and, after extending the model, calibration
  evidence.
- **2020–2022:** permitted calibration period.
- **2023–2024:** held-out validation period.

Parameters are frozen before the held-out run. Observed 2023–2024 exogenous
conditions may be supplied, but their class `E` outcomes may not be used for
tuning. Any exception changes the validation design and must be documented
before results are reported.

## Required structural work for a higher-resolution release

1. Represent the principal separate electricity systems rather than one
   national copper plate.
2. Create a traceable unit or plant fleet with commissioning, retirement,
   fuel, capacity, and availability.
3. Represent hydro resources and operating constraints at a resolution
   supported by retained rainfall, inflow, or reservoir evidence.
4. Reconcile customer demand, station use, network losses, IPPs, household
   generation, and off-grid supply.
5. Replace the Phase 1D annual cane–bagasse proxy with Fiji mill-level steam,
   electricity, co-product, storage and outage evidence when the intended use
   requires that resolution.
6. Represent thermal fuels, heat rates, prices, and availability explicitly.
7. Increase temporal resolution only as far as the evidence and intended use
   justify.

Structural changes are not “calibration parameters” and must be completed and
verified before numerical tuning begins.

## Calibration and validation records

Fiji v2 provides:

- a machine-readable evidence table for 2020–2024;
- a parameter register containing bounds and reasons for every tunable value;
- declared error metrics and tolerances by outcome;
- an automated run-and-score script;
- the retained raw assessment and a raw-versus-v2 result comparison;
- a dated calibration build record under `history/calibration/`.

Recommended reported metrics include absolute error, percentage error where
the denominator is stable, energy-balance closure, fuel-to-generation
consistency, and renewable-share error. Results must be shown for every year,
not only as a five-year average.

## Lessons loop and alternate optima

Record case-specific incidents and model changes in `MODEL_FIXES*.md`. Record
a reusable process lesson in `LESSONS_LEARNED.md` only when it creates a new
guardrail. Promote a lesson into this protocol or a shared skill after it has
a clear cross-case application.

For structural deletion, reindexing or exporter-order changes:

1. preserve an immutable baseline containing both source and result
   artifacts;
2. prove the removed entity is inactive from source equations and
   full-precision control results;
3. compare objective, primal feasibility, capacity/vintage envelopes,
   demands, emissions, affected physical flows and aggregate services;
4. classify any row-level activity substitution explicitly; and
5. report dual/shadow-price instability rather than treating dual identity
   as a physical parity requirement.

MUIO derived set order and a degenerate feasible face can select a different
cost-equivalent CBC solution. A shadow price is not decision-grade until it
is stable across relevant alternate optima or the ambiguity is otherwise
resolved.

## Claim boundary

With the retained public evidence, this release is an annual
electricity–hydro–IPP backcast with a cane-linked bagasse balance. It does not
claim hourly dispatch, mill engineering fidelity, reliability, precise
reconstruction of historical investment choice, or a calibrated full nexus.
Wider land, water, agriculture, and cross-nexus calibration must be released
only after their own evidence and held-out tests are complete.
