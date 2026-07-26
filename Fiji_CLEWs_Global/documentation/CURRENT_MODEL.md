# Fiji CLEWs Global: current model

This is the plain-language description of the model that is active now. Dated
build notes and superseded formulations are retained under `history/`; they
are evidence of how the model evolved, not instructions for a future
calibrated case.

## What the current model contains

| Component | Origin | Current status |
|---|---|---|
| Energy system | OSeMOSYS Global Fiji country build | Structurally active; historically uncalibrated |
| Land and crops | CLEWs Global and GAEZ country workflow | Structurally active; historically uncalibrated |
| Water and climate links | CLEWs GAEZ | Structurally active; historically unvalidated |
| MUIO implementation | Imported raw CLEWs case plus reserve-capacity proxy | Technically solved; not result-equivalent to every upstream formulation detail |

The active case is `WebAPP/DataStorage/Fiji_CLEWs_Global`. It contains 132
technologies and 107 commodities, covers 2021–2050, and uses four time slices.
Its current runs are `Raw` and `Raw_ReserveProxy`.

## Current boundaries

- Electricity is represented at one national node, `FJIXX`.
- Land, crops, and water use four agro-climatic clusters.
- Wet season is November–April and dry season is May–October.
- Each season has one daytime and one nighttime slice.
- Crop and water coefficients use GAEZ RCP4.5 layers.
- The model includes sugar cane, coconut, a taro/yam/root proxy, cassava, and
  an aggregated other-crops group.
- No Fiji renewable target, NDC, or net-zero constraint is active.
- No historical generation, crop area, water use, or emissions outcome is
  locked to an observation.

## Raw behavior

The generated 2021 residual power capacities are 209 MW hydro, 74 MW oil,
10 MW wind, and 69.7 MW biomass. The raw solution produces approximately
625.3 GWh hydro and 305.3 GWh biomass in 2021, with no material oil or wind
generation. This behavior differs substantially from Fiji observations and is
retained as the unforced calibration baseline.

The raw crop areas also differ materially from 2020 observations, especially
for sugar cane and cassava. Exact initial comparisons remain in
`../diagnostics/raw_vs_history.csv`.

## Where to answer questions

- Start with `../data_sources/DATA_SOURCES.md` for the source register.
- Use `../data_sources/ASSUMPTIONS.csv` for analyst choices.
- Use `../data_sources/CALCULATIONS.csv` for formulas and transformations.
- Use `../data_sources/MODEL_DATA_MAP.csv` to connect a model object to its
  sources, assumptions, and calculations.
- Use `MODEL_STRUCTURE.md` for the commodity and system boundaries.
- Use `KNOWN_LIMITATIONS.md` before interpreting results.
- Use `CALIBRATION_PROTOCOL.md` before making historical changes.
- Use `HISTORY.md` to understand when the formulation changed.

## Interpretation boundary

The raw model is suitable for workflow verification, structural inspection,
and calibration planning. It is not a Fiji historical model or forecast. It
is not suitable for ranking renewable pathways, estimating investments, or
making policy recommendations until a separate calibrated version passes
held-out validation and robustness tests appropriate to the intended use.
