# Calibration assessment — Fiji CLEWs Global raw model

- **Country:** Fiji
- **Calibration grade:** Not assessable
- **Weighted score:** 39.0/100 (preliminary band: Unacceptable)
- **Confidence:** Low
- **Intended use:** workflow demonstration, raw-data inspection, and preparation for later calibration

## Critical gates

| Gate | Status | Evidence |
|---|---|---|
| Executable Case | pass | CBC solution is optimal with objective -240.33220528; diagnostics/technical_qa.csv. |
| Referential Integrity | pass | The full case generates and solves; 68 input CSVs contain 33,179 data rows with zero duplicate parameter indices; required result tables are present. |
| Physical Accounting | partial | The case solves and its main structures are coherent, but independent energy, land, water, emissions, and cross-nexus balance tests are absent. The CBC objective (-240.332) also does not reconcile with the sum of exported TotalDiscountedCost (-89.080), and forest activity carries an inherited -10 variable-cost credit. |
| Scope Integrity | pass | Energy, land, crop, water, climate-raster, and cross-sector commodity links are structurally present. Their country fidelity is evaluated separately and is weak or untested. |
| Historical Evidence | partial | Traceable 2021 electricity capacity/generation and 2020 harvested-area observations exist. No aligned historical tests are available for water balances, climate behavior, seasonal patterns, emissions, or cross-nexus transfers. |
| Forcing Disclosure | pass | diagnostics/no_forcing_audit.json reports no added historical locks or fitted hooks. Outcome tracing classifies inherited 2021 residual capacities as H and generation/crop areas as E. |
| Reproducibility | pass | Pinned source and submodule revisions, override files, rebuild instructions, solver metadata, generated inputs, solution, results, and technical validation are packaged. The MUIOGO JSON inventory script is inapplicable because this is a CLEWs Global CSV bundle. |

## Forcing profile

- Endogenous: 69.2%
- Justified constraint: 0.0%
- History-fixed: 30.8%

## Domain results

| Domain | Score | Rationale |
|---|---:|---|
| Energy | 25 | Four endogenous generation comparisons all miss tolerance; three of four inherited capacity stocks are materially wrong, and the model has one national node and four time slices. |
| Land | 30 | Only coconut area is within the declared 20% tolerance; sugar cane, cassava, roots, and other crops miss, with proxy and year-alignment limitations. |
| Water | 25 | Water commodities and hydrological relationships exist, but no Fiji withdrawals, runoff, irrigation, reservoir, or environmental-flow observations are compared. |
| Climate | 35 | GAEZ RCP4.5 layers are included, but historical precipitation, evapotranspiration, runoff timing, hazards, and climate sensitivity have not been validated. |
| Nexus | 25 | Cross-sector links are structurally present but no electricity-for-water, water-for-crops, biomass-to-energy, or associated-emissions flow is historically tested. |

## Strong points

- The raw model solves optimally and is reproducible from pinned upstream versions and packaged overrides.
- Added Fiji-specific history forcing has been removed and the remaining forcing is disclosed outcome by outcome.
- Fiji geography, seasons, four land clusters, and full nexus commodity structure are present.
- Historical mismatches are retained transparently instead of being hidden through calibration locks.

## Weak points

- Only one of nine endogenous historical comparisons is within the declared tolerance.
- Inherited 2021 capacity stocks are fixed but mostly inconsistent with the cited national evidence.
- Historical water, climate, seasonal, emissions, and cross-nexus flow evidence is missing.
- The negative forest credit and inconsistent cost-reporting equations prevent economic interpretation of the objective.
- No held-out validation, uncertainty analysis, or structural sensitivity testing has been performed.

## Required improvements

- Assemble aligned multi-year Fiji observations for energy stocks and flows, crop production and area, water balances, climate variables, emissions, and material nexus transfers.
- Correct the technical cost-accounting inconsistency and replace or justify the inherited -10 forest credit before using costs or objectives.
- Reconcile inherited power assets, island-grid topology, retirements, demand, fuel use, efficiencies, and operating constraints to traceable Fiji evidence.
- Calibrate underlying crop yields, conversions, hydrology, infrastructure, and resource constraints across several years without fixing the outcomes being tested.
- Freeze the calibrated parameters and evaluate a held-out period, then test uncertainty and temporal/spatial structural alternatives.

## Fitness for purpose

- **Suitable — teaching and workflow demonstration:** The model solves reproducibly, contains all nexus structures, discloses its limitations, and clearly labels historical comparisons as diagnostic.
- **Unsuitable — exploratory Fiji national scenario analysis:** Energy and land historical behavior is poor, water and nexus behavior is untested, and the objective is not economically interpretable.
- **Unsuitable — policy, investment, or official planning support:** The model lacks acceptable calibration, held-out validation, robustness testing, reconciled cost accounting, and decision-relevant spatial and temporal detail.
- **Unsuitable — operational adequacy or reliability analysis:** One national energy node and four annual time slices cannot represent island grids, chronological operations, reserves, outages, or reliability.

## Grade rules applied

- Historical evidence or forcing disclosure is unresolved.
- At least one critical technical gate is not evidenced.

> The scorecard makes reviewer judgments explicit but cannot verify source quality, constraint classification, tolerances, or the truth of supplied evidence.
