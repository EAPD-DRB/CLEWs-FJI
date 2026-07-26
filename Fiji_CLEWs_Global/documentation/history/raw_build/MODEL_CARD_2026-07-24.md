# Model card: Fiji CLEWs Global raw model

## Purpose and status

This model is a reproducible starting point for developing a Fiji climate,
land, energy, and water model. It is technically solved but deliberately
uncalibrated. It is suitable for software, structural, and data-gap work—not
for policy conclusions, investment estimates, or historical performance claims.

## Scope

- **Geography:** Fiji as one electricity node (`FJIXX`) and four national
  agro-climatic land clusters.
- **Period:** 2021–2050.
- **Time resolution:** wet season (November–April) and dry season
  (May–October), each split into daytime and nighttime.
- **Climate:** GAEZ RCP4.5 crop and water layers.
- **Energy:** unmodified overlapping OSeMOSYS Global Fiji parameter values.
- **Land and crops:** sugar cane, coconut, a taro/yam/root proxy, cassava, and
  an aggregate other-crops group using unity crop-yield factors.
- **Water:** precipitation, evapotranspiration, crop-water deficit, groundwater
  return, and runoff relationships inherited from GeoCLEWs/CLEWs Global.

## Country adaptations retained

- Fiji identifiers, time zone, seasons, node, and 2021–2050 horizon.
- GADM 4.1 Fiji boundaries with explicit antimeridian handling.
- Equal-area spatial processing and four agro-climatic clusters.
- Structural normalization to the documented 18,273 km² model domain.
- Crop taxonomy proxies required to connect Fiji crop names to available GAEZ
  layers.
- Evidence-based energy topology and technology applicability settings.

These define the modelled system. None was chosen by minimizing historical
output error.

## Raw historical diagnostic

The upstream 2021 electricity capacity values are 209 MW hydro, 74 MW oil,
10 MW wind, and 69.7 MW biomass. The unforced model generates approximately
625.3 GWh hydro and 305.3 GWh biomass in 2021, with no material oil or wind
generation. This differs substantially from the historical observations.

Raw 2021 harvested areas also differ materially, especially sugar cane and
cassava. Those discrepancies are expected and are recorded in
`diagnostics/raw_vs_history.csv`.

The mismatch is evidence that calibration is still required. It must not be
removed by silently forcing one historical year.

## Interpretation

The results describe how the pinned global defaults behave after being
structurally adapted to Fiji. They do not describe Fiji's actual 2021 system
and should not be treated as a forecast.

The negative objective value arises from inherited CLEWs land-activity cost
conventions. It is not a national welfare or conventional total-system-cost
estimate.

## Important limitations

- A single node does not represent Fiji's separate island grids.
- Four time slices cannot represent hourly renewable variability, evening
  peaks, storage operation, or cyclone outages.
- The MUIO import represents CLEWs Global technology capacity credits with a
  derived annual user-defined constraint. It is a planning-capacity proxy, not
  an operational reliability model, and its mandatory stale check must be run
  after relevant demand or scenario edits.
- Upstream capacities and retirement profiles differ from Fiji records.
- Generic costs, efficiencies, availability factors, and fuel limits have not
  been calibrated.
- Crop proxies and GAEZ potential yields are not observed Fiji farm yields.
- Water parameters have not been compared with basin withdrawals, irrigation
  infrastructure, or environmental flows.
- No held-out historical validation or uncertainty analysis has been performed.
- Fiji's renewable-energy, NDC, and net-zero targets are not applied.

## Fitness for use

Suitable for:

- verifying the CLEWs Global workflow for Fiji;
- inspecting raw global-data behavior;
- identifying data and structural gaps;
- preparing a transparent calibration plan.

Not suitable for:

- estimating Fiji investment requirements;
- assessing historical emissions or generation;
- reliability or operational analysis;
- ranking Fiji policy pathways;
- decision-grade land or water trade-offs.
