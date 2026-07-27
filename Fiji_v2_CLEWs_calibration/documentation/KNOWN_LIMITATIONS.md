# Fiji v2 known limitations

These limitations are part of the result, not optional caveats.

## Calibration boundary

- Only annual national grid-supply energy is calibrated and validated.
- Total grid generation is an exogenous requirement and cannot be claimed as
  reproduced demand.
- The 2021 fleet is held constant over 2020–2024 because a complete annual
  public commissioning and retirement register was not found.
- Calibration-period biomass and wind output receive no independent
  reproduction credit; their frozen 2023–2024 results do.
- The full land, climate, agriculture, hydrology, and nexus modules remain
  uncalibrated. Phase 1B validates only the stated annual public-water
  delivery and aggregate surface-abstraction boundary.

## Public water

- Public delivery is observed only for 2020–2024; no future demand path is
  supplied after 2024.
- Annual evidence is spread across the four time slices with a flat-rate
  `YearSplit` profile; no seasonal demand data are represented.
- Public groundwater is structurally represented but quarantined because no
  Fiji-specific public-groundwater abstraction/source-share evidence was
  retained.
- No Fiji-specific pumping or treatment electricity intensity was found.
  Omitting an explicit input avoids double-counting against the current gross
  grid-supply boundary, but water-sector energy and emissions are not
  endogenous.
- Aggregate purification and distribution losses are embedded in the
  historical surface input ratio. The model does not distinguish treatment
  stages, assets, leakage locations, storage or pressure zones.

## Energy structure

- One national copper plate does not represent Viti Levu, Vanua Levu, Ovalau,
  or isolated systems separately.
- The grid conduit is lossless. Network losses and station auxiliary use are
  reconciled only through the selected gross-generation boundary.
- Four wet/dry day/night slices cannot reproduce hourly renewable
  variability, evening peaks, unit commitment, storage chronology, outages,
  or cyclone recovery.
- Wind generation is below 1 GWh in the observed period and the model does
  not reproduce its year-to-year behavior reliably.
- Small grid solar appears only in 2024 and is not separately represented in
  the historical fit.
- Fiji v2 does not represent a generic industrial `Other hydrocarbons`
  service. Reintroducing one requires evidence for its physical fuel,
  material demand, supply chain, and accounting boundary; reported non-energy
  lubricant or bitumen use must not be treated as combustion demand.
- The post-OHC `Historical_Backcast` recertification preserved the objective,
  score and reported calibration metrics. The removed OHC branch was dormant.
- MUIO commodity descriptions remain generic placeholders, although
  identifier references resolve.

## Hydro and biomass

- Hydro uses one aggregate technology and a constant inherited wet/dry
  profile. There are no plant reservoirs, inflows, releases, spill,
  operating rules, rainfall response, or annual outage conditions.
- The 2024 high-hydro year is therefore underpredicted by 16.52%.
- Biomass/IPP output is represented through aggregate capacity and an
  effective availability factor. It is not backed by a calibrated
  cane-bagasse-mill balance.

## Costs and future pathways

- Delivered fuel prices, thermal heat rates, fixed and variable operating
  costs, technology capital costs, financing, and project-specific
  constraints have not been validated for Fiji v2.
- The 5% discount rate remains an importer assumption rather than a
  question-specific social or financial rate.
- Future demand is a rebased raw trajectory, not a forecast.
- Future residual-capacity paths preserve raw retirement ratios rather than a
  verified unit retirement schedule.
- No formal demand, fuel-price, cost, weather, technology, target, or
  structural sensitivity ensemble has yet been run.
- The objective and inherited negative forest activity credit require
  reconciliation before total-system-cost or welfare interpretation.

## Fitness limits

Fiji v2 may support exploratory annual scenario screening once the relevant
future assumptions are added and stress-tested. It is not yet suitable for:

- official procurement or investment plans;
- a definitive “best” renewable pathway;
- tariff or financing analysis;
- operational dispatch, adequacy, reserves, or reliability;
- climate-resilient hydro operations; or
- a calibrated full-CLEWs policy claim.

The ordered improvement list is in
`../diagnostics/calibration_runs/historical_fit/scorecard.md`.
