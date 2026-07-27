# Fiji v2 CLEWs model structure

Fiji v2 retains the integrated raw-model structure while calibrating only its
annual national grid-supply energy subset. It combines an energy lineage with
a spatial land–agriculture–water lineage.

| System | Main model objects | Connection to the rest of the model |
|---|---|---|
| Energy supply | Imported fuels; hydro, biomass, oil, wind, solar, and other generation options; transmission; final energy demands | Supplies electricity and fuels to residential, commercial, industrial, transport, agriculture, and water services |
| Land and crops | Crop-production options and four cluster allocation technologies | Uses land, precipitation, evapotranspiration, and irrigation; produces crop commodities |
| Water | Surface-water and groundwater resources, agricultural water, and public-water supply | Phase 1B closes observed public delivery through surface abstraction; public groundwater has an explicit but quarantined abstraction chain |
| Climate representation | GAEZ RCP4.5 precipitation, evapotranspiration, runoff, and potential-yield coefficients | Determines spatial crop and water coefficients; does not reproduce observed 2020–2024 weather |
| MUIO reserve proxy | Annual capacity-credit user-defined constraints | Replaces native reserve tags unsupported by the installed MUIO formulation; does not calibrate historical output |

## Electricity representation

All electricity is represented through one national node, `FJIXX`. The
commodity chain contains an upstream electricity carrier, `ELCFJIXX01`, and a
final-demand carrier, `ELCFJIXX02`, connected by the generated transmission
technology. Final electricity demands are split among agriculture,
commercial, industry, residential, and transport services.

The inactive duplicate `ELCFJI01` → `PWRTRNA01` → `ELCFJI02` branch has been
removed from Fiji v2. It was generated with the land code `FJI` while the
actual electricity technologies and demand use the mapped grid-node code
`FJIXX`; it had no producer at its input, no demand at its output, and zero
activity in the pre-correction solve.

The separate `OHC` → `DEMINDOHC` → `INDOHC` branch has also been removed
from active Fiji v2. It was a dormant generic end-use branch: `OHC` had no
producer or importer, `INDOHC` had no specified demand, and the conversion
technology carried no Fiji cost, capacity, availability, or emissions data.
The structural review is retained at
`../data_sources/evidence/energy/OHC_BRANCH_REVIEW_2026-07-26.md`.

The current structure pools Viti Levu, Vanua Levu, Taveuni, Ovalau,
and other systems. It cannot represent island-specific capacity adequacy,
dispatch, outages, or network constraints. Those are required structural
changes for a later higher-resolution calibration.

## Temporal representation

The four slices are:

| Timeslice | Season | Daypart |
|---|---|---|
| `S1D1` | Wet, November–April | Day |
| `S1D2` | Wet, November–April | Night |
| `S2D1` | Dry, May–October | Day |
| `S2D2` | Dry, May–October | Night |

This structure can support annual and coarse wet/dry-season energy balances.
It cannot support hourly reliability, ramping, short-duration storage, or
chronological cyclone and outage analysis.

## Land and crop representation

Four cluster technologies, `LNDAGRFJIC01`–`LNDAGRFJIC04`, allocate land and
apply spatial crop and water coefficients. The explicit crop outputs are:

- sugar cane, `CRPSGC`;
- coconut, `CRPCON`;
- taro/yam/root proxy, `CRPYAM`;
- cassava, `CRPCAS`;
- aggregated other crops, `CRPOTH`.

The mapping is documented in
`../data_sources/evidence/raw_baseline/CROP_PROXY_MAPPING_2026-07-24.csv`.
Potential yields are not observations of Fiji farm yields.

## Water representation

`DEMAGRGWTFJI` and `DEMAGRSURFJI` supply agricultural water from modeled
groundwater and surface-water pathways. Phase 1B represents public water as:

```text
WTRSURFJI -> DEMPUBSURFJI -> PUBWATFJI -> annual demand
WTRGRCFJI -> WTRABSFJI -> WTRGWRFJI -> DEMPUBGWTFJI -> PUBWATFJI
             inactive                    quarantined
```

`WTRGRCFJI` is modeled annual recharge. `WTRGWRFJI` is raw abstracted
groundwater, separated by `WTRABSFJI`; both the abstraction and public
groundwater delivery routes are inactive pending Fiji evidence. The surface
route supplies observed 2020–2024 public delivery and uses annual Water
Authority of Fiji abstraction/delivery ratios to represent purification and
distribution losses. Annual-only evidence is allocated with `YearSplit`.
All water flow and service commodities use `km3`.

Precipitation, evapotranspiration, runoff, and groundwater relationships are
generated from the GAEZ-derived spatial coefficients.

The model does not currently contain calibrated reservoir operations, basin
withdrawal constraints, environmental flows, groundwater source shares, or
measured pumping/treatment electricity. No explicit public-water electricity
input is added because no Fiji intensity was found and the gross grid-supply
boundary already includes water-sector use. Hydropower is part of the energy
system and is not yet linked to a plant-specific historical reservoir
balance.

## Important accounting boundaries

- GAEZ climate layers describe scenario climatology, not a particular
  historical weather year.
- Fiji v2 uses reported total grid generation as the annual supply
  requirement. This aligns the generation categories but does not explicitly
  model customer demand, station use, or network losses.
- National fuel imports are not equivalent to power-sector fuel consumption.
- EFL generation and Fiji-wide generation can differ because of IPPs,
  household systems, and off-grid supply.
- Crop potential, crop production, harvested area, and land allocation are
  different quantities and must not be interchanged.
- The reserve proxy is a formulation-porting mechanism, not an observed
  reserve margin or a calibration lock.

The definitive parameter-to-source mapping is
`../data_sources/MODEL_DATA_MAP.csv`.
