# Fiji v2 Phase 1A topology audit

## Scope and status

- Case: `/Users/sato/Documents/GitHub/MUIOGO/WebAPP/DataStorage/Fiji_v2`
- Saved run: `Historical_Backcast`
- Historical activity window: 2020–2024
- Commodities audited: 103
- Technologies referenced: 130
- Model inputs changed: **No**
- Default audit status: **PASS with classified warnings**
- Strict mode would: **FAIL**
- Warning records: 37 across 33 commodities

This is a non-mutating topology audit. A warning is an investigation flag, not
an instruction to delete, suppress, demand, or rewire a commodity.

## Balance summary

| balance_status | count |
|---|---|
| connected | 71 |
| produced_unconsumed_undemanded | 32 |


- No commodity is consumed without a producer.
- No commodity with positive specified or accumulated demand lacks a producer.
- 25 end-use carrier outputs have no consumer or demand;
  all 25 were inactive in the 2020–2024 solve.
- The four renewable carriers each receive a generic balance warning and a
  more specific resource-classification warning, so warning-record and
  commodity counts intentionally differ.

## Warning counts

| code | count |
|---|---|
| likely_cross_sector_consumer | 1 |
| output_only_resource_carrier | 4 |
| produced_unconsumed_undemanded | 32 |


## Priority findings

| commodity | code | finding |
|---|---|---|
| COMELCFJIXX02 | likely_cross_sector_consumer | DEMPUBGWTFJI (public_water) consumes a commercial commodity. |
| GEO | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| HYD | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| SOL | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| WND | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |


## Role counts

| role | count |
|---|---|
| intermediate | 4 |
| resource | 36 |
| service | 35 |
| sink | 1 |
| stock | 27 |


## Interpretation

The complete commodity-by-commodity evidence is in `commodity_ledger.csv`.
`warnings.csv` contains every machine-detected topology warning. The next
structural step is Phase 1B, but it must begin with a documented decision on
whether `WTRGRCFJI` is recharge, extractable groundwater, or an intermediate.
No public-water link should be changed until that decision and its units are
reviewed. `AGRELCFJIXX02 -> DEMAGRGWTFJI -> AGRWATFJI` has the same
electricity-only groundwater pattern but is not a cross-sector link; retain it
for the Phase 1D agricultural-water review.
