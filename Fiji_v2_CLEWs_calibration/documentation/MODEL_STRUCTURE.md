# Fiji v2 CLEWs model structure

Fiji v2 retains the integrated raw-model structure while calibrating only its
annual national grid-supply energy subset. It combines an energy lineage with
a spatial land–agriculture–water lineage.

| System | Main model objects | Connection to the rest of the model |
|---|---|---|
| Energy supply | Imported fuels; hydro, biomass, oil, wind, solar, and other generation options; transmission; final energy demands | Supplies electricity and fuels to residential, commercial, industrial, transport, agriculture, and water services |
| Land and crops | Crop-production options and four cluster allocation technologies | Uses land, precipitation, evapotranspiration, and irrigation; produces crop commodities |
| Water | Surface-water and groundwater resources, agricultural water, and public-water supply | Irrigation and public supply share modeled raw-water pathways; groundwater pumping uses electricity |
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
groundwater and surface-water pathways. `DEMPUBGWTFJI` and `DEMPUBSURFJI`
serve public-water demand. Precipitation, evapotranspiration, runoff, and
groundwater relationships are generated from the GAEZ-derived spatial
coefficients.

The model does not currently contain calibrated reservoir operations, basin
withdrawal constraints, environmental flows, or measured pumping electricity.
Hydropower is part of the energy system and is not yet linked to a
plant-specific historical reservoir balance.

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
