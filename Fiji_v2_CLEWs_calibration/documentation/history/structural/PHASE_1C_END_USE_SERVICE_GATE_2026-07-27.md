# Phase 1C.0 end-use service evidence and design gate

**Date:** 27 July 2026  
**Outcome:** Gate complete; no model input or active MUIOGO case changed  
**Scope:** The 26 energy end-use carriers still reported as produced,
unconsumed and undemanded after Phase 1B

**Completion note:** The electricity-accounting recommendation was implemented
with independently projected 2025–2050 sector paths in
`PHASE_1C_BOTTOM_UP_ELECTRICITY_DEMAND_2026-07-27.md`. The cooking-service gate
remains closed.

## Decision

Proceed next with an **electricity-accounting implementation**, not yet with a
residential useful-cooking demand.

FBoS evidence is sufficient to partition the existing 2020-2024 gross
electricity requirement into commercial, industrial, grid-served domestic,
distribution-loss, and residual components without changing total grid
supply. The Fiji MICS provides a credible residential cooking technology mix,
but it does not provide a useful-energy magnitude or technology efficiencies.
Activating cooking now would therefore manufacture the quantity that drives
the model.

Phase 1C.0 makes no structural or numerical model change. It records the
architecture and activation tests so the next implementation is reproducible.

## What the audit found

The remaining service warnings comprise 26 carriers:

- agriculture: 1;
- commercial: 6;
- industry: 8;
- residential: 5;
- transport: 6.

Every producing `DEM*` technology has zero activity in 2020-2024. The detailed
disposition is in
`data_sources/evidence/energy/phase1c_end_use_carrier_register_2026-07-27.csv`.

There is also a twenty-seventh inherited sector-energy carrier,
`AGRELCFJIXX02`. It is not in the warning list because
`DEMAGRGWTFJI` consumes it, but both its electricity adapter and groundwater
route are inactive in the current solve. It must still be included in any
future gross-grid reconciliation if agricultural pumping becomes active.

## Why the branches are disconnected

This is an integration seam rather than 26 independent modelling errors.
OSeMOSYS Global supplied generic final-energy adapters such as
`DEMRESLPG: LPG -> RESLPG`, while the CLEWs land-water system supplied
physical crop and water chains. The imported Fiji model retained both
subsystems but did not create the country-specific useful-service demands and
conversion layers that would join most final-energy outputs to economic
services. The energy calibration then placed one gross requirement directly
on `ELCFJIXX02` to reproduce the documented grid-supply boundary.

Consequently, connecting a sector electricity branch by simply adding demand
would make the model require the same electricity twice.

## Target architecture

```text
supply carrier
  -> inherited sector final-energy adapter
  -> sector final-energy carrier
  -> explicit appliance/process/vehicle technology
  -> useful-service commodity
  -> specified service demand
```

The inherited `COM*`, `IND*`, `RES*`, `TRA*` and `AGR*` outputs are therefore
treated as **sector final-energy carriers**, not useful services. They are
retained as an interface layer. New service commodities should be added only
when their magnitude and conversion parameters can be documented.

Examples of later useful-service boundaries are residential cooking,
commercial low-temperature heat, industrial process heat, agricultural
mechanical work, road passenger/freight mobility, domestic aviation, and
domestic marine mobility. These are design categories, not active model
entities.

## Electricity anti-double-counting rule

Historical grid electricity must satisfy:

```text
gross grid requirement
  = sector grid use + distribution loss + station/boundary residual
```

Domestic total electricity use must first be reduced by household
own-generation output before it is assigned to the central grid. The exact
2020-2024 reconciliation is retained in
`data_sources/evidence/energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv`.

The 2024 example is:

| Component | PJ |
|---|---:|
| Commercial grid use | 1.8214069392 |
| Industrial grid use | 0.8443905300 |
| Grid-served domestic use | 1.2548027232 |
| Distribution loss | 0.2377850076 |
| Station-use/boundary residual | 0.2296764000 |
| Existing gross grid requirement | 4.3880616000 |

In the next implementation, the commercial, industrial and grid-served
domestic quantities may become demand on `COMELCFJIXX02`,
`INDELCFJIXX02` and `RESELCFJIXX02`. Direct `ELCFJIXX02` demand must be
reduced by exactly those same quantities, leaving losses plus the residual.
The sum must remain equal to the current gross requirement in every year.

The post-2024 allocation needs a declared scenario rule. A frozen 2024 sector
share is a possible neutral starting assumption, but Phase 1C.0 does not
approve or apply it.

## Residential cooking pilot verdict

**No-go for active demand; go for architecture and share validation.**

The 2021 Fiji MICS supports LPG, kerosene, biomass/open-fire, electricity and
biogas pathways. It does not support using `RESNGS` for biogas: the inherited
`NGS` carrier denotes a fossil natural-gas chain, while the survey reports
biogas. A later active model must introduce a distinct biogas pathway or
document an explicit aggregation convention.

The pilot remains blocked by:

1. an annual residential cooking-service magnitude;
2. Fiji-appropriate appliance efficiencies;
3. treatment of fuel stacking;
4. allocation of domestic electricity between cooking and other uses;
5. a physical biomass supply boundary;
6. a biogas representation decision.

Survey percentages cannot be multiplied directly by a national PJ total: a
share of people using a stove is not a share of fuel energy or useful cooking
energy.

## Approved next implementation: Phase 1C.1

Phase 1C.1 should be limited to the existing electricity adapters:

1. Work on a disposable copy of `Fiji_v2`.
2. For 2020-2024, place observed demand on `COMELCFJIXX02`,
   `INDELCFJIXX02` and grid-served `RESELCFJIXX02`.
3. Replace direct `ELCFJIXX02` gross demand with the exactly reconciled
   distribution-loss plus station/boundary residual.
4. Select and document the 2025-2050 sector-allocation assumption before
   extending the change beyond history.
5. Keep the adapters at 1:1 and zero added cost so the historical gross grid
   requirement and dispatch should remain unchanged.
6. Generate and preprocess through the MUIOGO application, validate the
   matrix with GLPK, solve with CBC, and compare against
   `Phase1B_Public_Water`.
7. Require exact annual grid-balance reconciliation, nonzero activity in the
   three sector adapters, unchanged gross grid supply, and no unexpected
   changes outside those accounting routes.

This is an accounting closure, not yet a useful-service or fuel-switching
model. The cooking pilot follows only after its activation gates pass.

## Files added by this gate

- `data_sources/evidence/energy/PHASE_1C_SOURCE_REVIEW_2026-07-27.md`
- `data_sources/evidence/energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv`
- `data_sources/evidence/energy/fiji_mics_2021_cooking_mix.csv`
- `data_sources/evidence/energy/phase1c_end_use_carrier_register_2026-07-27.csv`

No file under `model/inputs`, no active-case JSON, and no generated solver
artifact was changed. No solve was required because this gate contains no
model change.
