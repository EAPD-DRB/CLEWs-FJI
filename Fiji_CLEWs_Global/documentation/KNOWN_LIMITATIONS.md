# Fiji CLEWs Global known limitations

These limitations are part of the model record and must be checked before
using results in advice or presentations.

## Source traceability

- The generated energy system inherits many values from OSeMOSYS Global, but a
  complete row-level record of the original databases and transformations has
  not yet been reconstructed.
- The exact bundled SSP2 population file and transformation locator remains
  to be recorded.
- The Fiji raw build retains complete override files rather than
  revision-specific patches. The pinned revisions and original change notes
  are available, but the patch reconstruction is still outstanding.
- Observations identified for 2020–2024 have not yet been extracted into one
  reconciled, machine-readable evidence table with page and boundary notes.

## Energy representation

- One national electricity node does not represent Fiji's separate island
  grids.
- Four time slices cannot reproduce hourly renewable variability, evening
  peaks, storage operation, unit commitment, or cyclone outages.
- Upstream capacities and retirement profiles differ from Fiji records.
- Generic costs, efficiencies, availability factors, fuel prices, and fuel
  limits have not been calibrated.
- The raw transmission link is not a calibrated representation of network
  losses or constraints.
- The active demand path is below the 2024 EFL customer-demand figure and its
  statistical boundary has not been reconciled.
- Some EFL 2024 headline and detailed generation totals appear to use
  different boundaries. They must be reconciled rather than averaged.

## Hydro, climate, and reliability

- Hydropower is not represented by plant-specific reservoirs, inflows,
  storage, releases, spill, or operating rules.
- GAEZ RCP4.5 layers are scenario climate data, not observed 2020–2024
  rainfall.
- Public rainfall evidence is available, but complete reservoir and inflow
  time series have not been retained.
- The MUIO reserve-capacity proxy is annual and non-chronological. It is not a
  loss-of-load or operational reliability model.
- The default proxy reserve margin is 1.0 because the generated native table
  is empty; this is not a sourced Fiji planning criterion.

## Land, agriculture, and water

- Crop proxies and GAEZ potential yields are not observed Fiji farm yields.
- Crop production, harvested area, irrigation, and yield have not been
  aligned across several years.
- Water parameters have not been compared with basin withdrawals,
  infrastructure, environmental flows, or measured pumping energy.
- The national annual water account does not supply the spatial, monthly, or
  infrastructure detail required for basin operations.
- Biomass generation is not yet constrained by a reconciled cane–bagasse–mill
  balance.

## Economic interpretation

- A 5% discount rate is inserted during MUIO import because the upstream Fiji
  table is empty; it is not yet justified for a particular policy question.
- The upstream and MUIO objectives differ because MUIO subtracts discounted
  salvage value while the active upstream formulation does not.
- The inherited negative forest activity credit and the raw objective require
  reconciliation before welfare or total-system-cost interpretation.
- No uncertainty ranges or structural sensitivity tests have been performed.

## Calibration and fitness

- No held-out historical validation has been performed.
- The raw model is not suitable for ranking Fiji policy pathways, estimating
  investment requirements, or making official planning recommendations.
- Public data are sufficient for a planned annual and probably wet/dry-season
  electricity–hydro–bagasse calibration, but not for hourly operational or
  reliability validation.
- Investment behavior cannot be validated credibly from 2020–2024 alone; a
  longer historical series and project/finance evidence are required.

See `CALIBRATION_PROTOCOL.md` for the conditions under which these limitations
may be retired or narrowed.
