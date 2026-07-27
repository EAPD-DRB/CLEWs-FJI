# Fiji v2 Phase 1B topology audit

## Scope and status

- Case: `/Users/sato/Documents/GitHub/MUIOGO/WebAPP/DataStorage/Fiji_v2`
- Saved run: `Phase1B_Public_Water`
- Historical activity window: 2020–2024
- Commodities audited: 104
- Technologies referenced: 131
- Model inputs changed: **No**
- Default audit status: **PASS with classified warnings**
- Strict mode would: **FAIL**
- Warning records: 35 across 31 commodities

This is a non-mutating topology audit. A warning is an investigation flag, not
an instruction to delete, suppress, demand, or rewire a commodity.

## Balance summary

| balance_status | count |
|---|---|
| connected | 73 |
| produced_unconsumed_undemanded | 31 |


- No commodity is consumed without a producer.
- No commodity with positive specified or accumulated demand lacks a producer.
- 26 end-use carrier outputs have no consumer or demand;
  all 26 were inactive in the 2020–2024 solve.
- The four renewable carriers each receive a generic balance warning and a
  more specific resource-classification warning, so warning-record and
  commodity counts intentionally differ.

## Warning counts

| code | count |
|---|---|
| output_only_resource_carrier | 4 |
| produced_unconsumed_undemanded | 31 |


## Priority findings

| commodity | code | finding |
|---|---|---|
| GEO | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| HYD | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| SOL | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |
| WND | output_only_resource_carrier | Renewable resource carrier is output-only; model availability, not demand. |


## Role counts

| role | count |
|---|---|
| intermediate | 5 |
| resource | 36 |
| service | 35 |
| sink | 1 |
| stock | 27 |


## Interpretation

The complete commodity-by-commodity evidence is in `commodity_ledger.csv`.
`warnings.csv` contains every machine-detected topology warning.

Phase 1B now treats `WTRGRCFJI` as annual recharge,
adds an explicit raw-groundwater abstraction layer, closes observed public
water through the surface route, and quarantines public groundwater. The
next structural step is Phase 1C: define useful-service boundaries and
evidence gates for the inactive end-use carrier outputs. The agricultural
groundwater chain remains deferred to Phase 1D.
