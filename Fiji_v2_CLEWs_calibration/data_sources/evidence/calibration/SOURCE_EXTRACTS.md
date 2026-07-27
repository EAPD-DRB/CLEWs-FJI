# Fiji v2 historical electricity evidence

## Source records

| File | Publication | SHA-256 | Extraction |
|---|---|---|---|
| `../external/EFL_2024_Annual_Report.pdf` | Energy Fiji Limited, *2024 Annual Report* | `b3427b8e597399f31aabc2ab315b1a72a24138e20cd8faa5c3fec2894f0fe956` | 25 July 2026 |
| `../external/Fiji_REI_Investment_Plan_2023.pdf` | Government of Fiji, *Renewable Energy Integration Investment Plan* | `3d291fad4853905d40486f253d974483a9b788881c6ea9e02e6ba725989790e1` | 25 July 2026 |

The source PDFs are retained in the original working package when local
redistribution is permitted. They are not committed to the public
`CLEWs-FJI` repository. The official URLs, file checksums, extraction notes,
and model-relevant facts are retained here so another authorized copy can be
verified.

The official entry points are:

- https://efl.com.fj/wp-content/uploads/2025/05/EFL-2024-Annual-Report.pdf
- https://fijiclimatechangeportal.gov.fj/wp-content/uploads/2023/09/Fiji_CIF_REI_IP.pdf

## Generation extraction

The machine-readable values in `historical_electricity_2020_2024.csv` were
transcribed from the EFL report's table “Generation Statistics for the Past
Ten (10) Years,” printed page 88. The table reports EFL hydro, EFL thermal,
EFL wind, EFL solar, IPP purchases, total EFL generation, total generation,
station auxiliary consumption, and shares for 2015–2024.

For 2024 the table combines wind and solar in one 849 MWh row and separately
reports 131 MWh of solar. Fiji v2 therefore records 718 MWh of wind and
131 MWh of solar. The earlier years report zero solar.

The electricity balance used as the historical model supply requirement is
the table's **Total Generation**, not customer sales or billed consumption.
It is supplied to the model as a justified exogenous condition (`J`) because
the current one-node model has no explicit network-loss or station-use
representation. It is not scored as an independently reproduced outcome.

## Capacity extraction

The investment plan states 329 MW of installed capacity in 2021: 182 MW
thermal and 147 MW renewable. Table 3.1 identifies:

- 133.4 MW hydro: Wailoa 80 MW, Nadarivatu 44 MW, Wainikasou 6.6 MW,
  and Nagado 2.8 MW;
- 9.8 MW wind at Butoni;
- 34 MW of grid-supplying biomass/IPP capacity: Tropik Wood 9 MW,
  FSC Lautoka 5 MW, and FSC Labasa 20 MW.

The same table reports about 61 GWh of biomass generation, consistent with
the EFL 2021 IPP total of 61.053 GWh at the precision needed here.

The 2021 fleet is held constant over 2020–2024 as an explicit modelling
assumption because a complete public annual commissioning/retirement register
was not found. These capacity values are class `J`; their close reproduction
is not counted as endogenous calibration success.

## Boundary and conflict notes

- EFL generation plus IPP purchases is a grid-supply boundary. It excludes
  behind-the-meter and off-grid generation.
- The investment plan lists small self-consumption solar installations.
  They are not added to the grid-generation fleet.
- EFL's 2024 component rows differ from their displayed subtotal by 1 MWh
  because of reporting precision. The published total is retained.
- The model represents Fiji as one national copper plate and cannot validate
  island-grid congestion, hourly reliability, unit commitment, reservoir
  operations, or customer-level losses.
- The Bureau of Statistics electricity release is retained as a boundary
  cross-check, but the internally consistent EFL time series is the numerical
  source for this experiment.
