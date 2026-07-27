# Fiji `DEMINDOHC` branch review

Date reviewed: 26 July 2026

## Question

Does Fiji v2 need the generated `OHC` → `DEMINDOHC` → `INDOHC`
other-hydrocarbons demand branch?

## Findings

- In the generated model, nothing produces or imports `OHC`.
- `INDOHC` has no specified demand.
- `DEMINDOHC` has no capacity, cost, availability, or emissions parameters.
  Its only active parameter rows are unit input and output ratios.
- The United Nations Statistics Division annual energy-data query for Fiji
  (area code 242), 2020–2024, contains no observations for SIEC 4500
  `Other hydrocarbons`.
- The query does contain minor `Other oil products`, including lubricants,
  recorded as non-energy use. Those products are not evidence for an
  industrial combustible-fuel demand branch.
- Fiji's 2023 national greenhouse-gas inventory reports industrial combustion
  using fuel oil, diesel, LPG, fuelwood, and bagasse. It treats lubricant use
  outside energy combustion.

## Decision

Remove `OHC`, `DEMINDOHC`, and `INDOHC` from active Fiji v2. This is a
country-applicability decision, not a historical dispatch calibration.
Reintroduce an appropriately defined service and supply chain only if national
energy-balance or industry evidence establishes material combustible use.

## Source entry points

- UNSD Energy Statistics API query:
  https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/.242../?startPeriod=2020&endPeriod=2024&format=csv
- UNSD International Recommendations for Energy Statistics / SIEC:
  https://unstats.un.org/unsd/energystats/methodology/documents/ires-web.pdf
- Fiji National Inventory Report 2023:
  https://unfccc.int/sites/default/files/resource/Fiji_GHG%20NIR%202023_Final.pdf

The API result is mutable upstream. Re-run the exact query and record its
download date if this structural decision is reviewed later.
