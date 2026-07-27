# Calibration assessment — Fiji v2 CLEWs annual electricity calibration

- **Country:** Fiji
- **Calibration grade:** Good
- **Weighted score:** 76.4/100 (preliminary band: Good)
- **Confidence:** Medium
- **Intended use:** exploratory annual renewable-pathway and policy-scenario comparison

## Critical gates

| Gate | Status | Evidence |
|---|---|---|
| Executable Case | pass | Historical_Backcast solved Optimal with CBC; validation_summary.json. |
| Referential Integrity | pass | The refreshed post-OHC muiogo_inventory.json resolves 130 technologies, 103 commodities, one emission, and one scenario. Commodity descriptions remain generic metadata, but identifiers and parameter references resolve. |
| Physical Accounting | pass | Annual grid-supply balance closes within MUIO CSV output precision; 0 duplicate input indices; reserve-margin proxy check reports zero mismatches. |
| Scope Integrity | pass | README, CURRENT_MODEL.md, genData.json, and validation_summary.json restrict the claim to annual national grid-supply energy. Land, water, agriculture, reliability, and network calibration are expressly excluded. |
| Historical Evidence | pass | EFL 2024 Annual Report and Fiji Renewable Energy Integration Investment Plan are retained with SHA-256 hashes, page/table locators, boundary notes, and a machine-readable 2020-2024 table. |
| Forcing Disclosure | pass | parameter_register.csv and assessment_comparisons.csv classify every comparison E, J, or H. Positive lower-equals-upper lock audit found zero positive exact locks. |
| Reproducibility | pass | build_fiji_v2.py, solve_muiogo_case.py, score_historical_fit.py, validate_fiji_v2.py, source hashes, build_manifest.json, and the retained solved case reproduce the experiment. |

## Forcing profile

- Endogenous: 84.1%
- Justified constraint: 5.1%
- History-fixed: 10.8%

## Domain results

| Domain | Score | Rationale |
|---|---:|---|
| Energy | 76 | Annual national grid-supply mix is credibly initialized and meaningfully validated, but the model lacks weather-responsive hydro, island grids, losses, plant detail, and robust cost/fuel calibration. |

## Strong points

- Optimal, fully reproducible MUIO case with a frozen 2023-2024 holdout.
- Official evidence is retained with hashes, locators, boundaries, and forcing classifications.
- Held-out material generation MAPE is below 10% and renewable-share MAE is about 5.1 percentage points.
- No positive lower-equals-upper generation or capacity outcome locks were introduced.

## Weak points

- The fixed wet/dry hydro profile cannot explain the high-hydro 2024 weather year.
- Wind output is sub-GWh and is not reproduced reliably.
- The one-node lossless annual representation omits island grids, losses, station use, chronology, and reliability.
- Costs, fuel prices, heat rates, project constraints, land, water, and the cane-bagasse balance remain uncalibrated.
- MUIO commodity descriptions are generic placeholders even though identifier references resolve.

## Required improvements

- Add observed rainfall/inflow, reservoir, outage, and plant-level hydro evidence and test a weather-responsive hydro formulation.
- Calibrate delivered fuel prices, thermal heat rates, fixed and variable costs, and technology investment costs with uncertainty ranges.
- Represent the principal island systems, network losses, existing units, commissioning, retirement, and documented project pipelines.
- Build a traceable cane-bagasse-mill balance for biomass instead of relying on aggregate effective availability.
- Run fuel-price, demand, cost, weather, target, and structural sensitivities before using v2 to rank renewable pathways.
- Calibrate and validate the land, water, climate, and cross-nexus modules separately before making a full CLEWs claim.

## Fitness for purpose

- **Conditionally Suitable — exploratory annual renewable-pathway comparison:** Use it to screen broad annual generation and capacity pathways only after adding scenario-specific cost, fuel, target, and weather sensitivities; do not read the optimizer's single path as a forecast.
- **Unsuitable — official investment plan or least-cost procurement decision:** Fuel prices, technology costs, financing, island networks, project constraints, and uncertainty have not been validated to decision-grade standards.
- **Unsuitable — operational adequacy, reliability, or dispatch:** Four time slices and one national node cannot represent chronology, unit commitment, reserves, island-grid limits, storage operation, or loss-of-load risk.

> The scorecard makes reviewer judgments explicit but cannot verify source quality, constraint classification, tolerances, or the truth of supplied evidence.
