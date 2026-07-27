# Phase 1C electricity accounting and bottom-up demand

**Date:** 27 July 2026
**Status:** Implemented, validated and promoted to the live MUIOGO case
**Scope:** Commercial, industrial and central-grid residential electricity,
plus direct distribution-loss and boundary overhead

## Outcome

Phase 1C connects the existing commercial, industrial and residential
electricity adapters without double counting the model's grid requirement.
Observed 2020–2024 electricity use is assigned to
`COMELCFJIXX02`, `INDELCFJIXX02` and `RESELCFJIXX02`. Direct
`ELCFJIXX02` demand is reduced to distribution loss plus station-use/boundary
reconciliation.

From 2025, the inherited aggregate trajectory is replaced by independent
sector paths. This is the bottom-up-projections version selected after the
Phase 1C.0 design gate. It is an electricity final-demand layer, not yet a
useful-service or fuel-switching model.

## Historical accounting

The Fiji Bureau of Statistics energy account supplies commercial, industrial,
domestic, household own-generation and distribution-loss quantities. Central
grid residential use is:

```text
domestic electricity use - household own-generation output
```

For every year from 2020 through 2024:

```text
gross grid requirement
  = commercial grid use
  + industrial grid use
  + central-grid residential use
  + distribution loss
  + station-use/boundary residual
```

The retained extract is
`data_sources/evidence/energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv`.
The largest numerical reconciliation difference in the implemented JSON is
zero at the retained precision.

The complete publication/checksum/locator record is
`data_sources/evidence/energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md`.
The detailed executable calculation note is
`data_sources/calculation_notes/PHASE_1C_BOTTOM_UP_ELECTRICITY.md`.

The three inherited adapters remain 1:1:

```text
ELCFJIXX02 -> DEMCOMELCFJIXX02 -> COMELCFJIXX02
ELCFJIXX02 -> DEMINDELCFJIXX02 -> INDELCFJIXX02
ELCFJIXX02 -> DEMRESELCFJIXX02 -> RESELCFJIXX02
```

Their mode-1 variable cost is set to zero. The inherited `0.0001` value was a
generic numerical placeholder; retaining it would make a pure accounting
split change the objective.

## Projection method

The base scenario follows the Government of Fiji's BAU-unconditional LEDS
assumptions, rebased to observed 2024 sector electricity instead of the LEDS
2013 quantities.

### Commercial

```text
commercial(y) = observed commercial(2024) * 1.026^(y-2024)
```

The 2.6% annual rate is the LEDS BAU-unconditional commercial electricity
assumption.

### Industrial

```text
industrial(y) = observed industrial(2024) * 1.020^(y-2024)
```

The 2.0% annual rate is used by the LEDS for industrial grid electricity in
all scenarios.

### Central-grid residential

Residential electricity is the observed 2024 central-grid quantity multiplied
by a normalized household/appliance stock index:

```text
residential(y)
  = observed central-grid residential(2024)
  * composite household-appliance electricity(y)
  / composite household-appliance electricity(2024)
```

The index uses:

- 182,282 households in 2013 and 0.38% annual household growth;
- the LEDS urban-household milestones from 52.98% in 2013 to 64.93% in
  2050, linearly interpolated;
- Fiji MICS 2021 central-grid access rates of 93.9% for urban and 74.2% for
  rural households, held by area while urbanization changes;
- LEDS refrigerator adoption, rising from 75%/66% in urban/rural
  grid-connected households in 2014 to 90%/80% in 2050;
- urban air-conditioning adoption rising from 5% in 2020 to 20% in 2050;
- 90% television adoption in grid-connected households;
- LEDS appliance intensities and MEPS turnover for refrigerators, lighting,
  air conditioning and televisions; and
- 500 kWh per grid-connected household for other electrical appliances.

Cooking is excluded from this projection index. The newer MICS identifies
stove shares but not an annual electricity or useful-energy quantity, and the
LEDS cooking transition does not resolve that current-data gap. Existing
cooking electricity remains inside the observed 2024 residential anchor; no
new cooking service is activated.

### Distribution loss and boundary overhead

Historical direct `ELCFJIXX02` demand is observed loss plus the calculated
boundary residual. From 2025, the combined overhead is scaled with total
sector end use:

```text
direct overhead(y)
  = [commercial(y) + industrial(y) + residential(y)]
  * 0.119232103417779
```

The factor is the 2024 loss-plus-residual quantity divided by 2024 sector end
use. This holds a technical accounting factor, not 2024 sector demand shares.
Loss and station-use/boundary residual should be separated in future when
independent projections are available.

### Time-slice profile

Each positive demand component uses the existing normalized aggregate
electricity profile: 28%, 25%, 22% and 25% across the four model slices.
This exactly preserves the historical peak shape and allows the reserve proxy
to aggregate the four demand commodities. It is a declared limitation:
sector-specific Fiji profiles were not available.

## Projection result

| Year | Commercial PJ | Industrial PJ | Residential PJ | Direct overhead PJ | Gross PJ |
|---|---:|---:|---:|---:|---:|
| 2025 | 1.868764 | 0.861278 | 1.253492 | 0.474965 | 4.458500 |
| 2030 | 2.124668 | 0.950921 | 1.245331 | 0.515192 | 4.836113 |
| 2040 | 2.746406 | 1.159167 | 1.371053 | 0.629143 | 5.905770 |
| 2050 | 3.550082 | 1.413018 | 1.503276 | 0.771000 | 7.237376 |

The residential index falls slightly through 2030 because documented MEPS
efficiency turnover initially outweighs household and appliance-stock growth.
It rises thereafter as household numbers, urbanization, refrigeration and air
conditioning increase.

The 2050 gross requirement is 3.144435 PJ (30.288%) below the inherited
10.381811 PJ trajectory. This is a transparent scenario divergence, not a
calibration improvement claim.

The annual source, driver and result fields are frozen in
`data_sources/evidence/energy/fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv`,
SHA-256
`f58c1ec3df4b6017966a2ad542256dd2f3e1f847837bd8bdc722ab9175ac181a`.
Its 2020–2024 difference from the accounting control is zero in every year.

## Reserve-margin proxy

The MUIO proxy previously read only direct `ELCFJIXX02` demand. That would
understate peak demand after the sector split. Its configuration and generator
now aggregate:

```text
ELCFJIXX02
+ COMELCFJIXX02
+ INDELCFJIXX02
+ RESELCFJIXX02
```

The proxy remains backward-compatible with a legacy singular configuration.
Both disposable Phase 1C cases report `CURRENT` with zero mismatches.

## Validation chain

Two disposable cases were generated from the live Phase 1B source:

1. `Fiji_v2_Phase1C_Accounting_Test`, with the 2020–2024 split but the
   unchanged inherited aggregate path from 2025; and
2. `Fiji_v2_Phase1C_BottomUp_Test`, with the full 2020–2050 sector paths.

Both were generated and preprocessed through `DataFile`, translated and
matrix-checked by GLPK, and solved with CBC.

Results:

- accounting checkpoint: Optimal, objective `-1387.57010517`;
- Phase 1B baseline objective: `-1387.57010517`;
- accounting objective difference: exactly zero;
- 7,409 non-adapter activity rows compared with Phase 1B: zero changed;
- bottom-up case: Optimal, objective `-1573.67149091`;
- complete 2020–2024 activity comparison between checkpoints: 1,210 rows,
  zero changed;
- 2020–2024 capacity comparison: 655 rows, zero changed;
- 2020–2024 emissions comparison: 655 rows, zero changed;
- sector adapter activities and gross transmission close to demand in all
  31 years, with zero reported annual balance duals;
- dedicated validation: 15/15 passed; and
- general Fiji technical validation: 15/15 passed.

Machine-readable results are in
`diagnostics/calibration_runs/phase1c/validation_summary.json` and
`general_validation_summary.json`. Generated solver files remain only in the
disposable MUIOGO cases and are not part of the portable model package.

## Limitations and next gate

The LEDS applies a sector-wide uncertainty range of ±10%; Phase 1C records but
does not yet parameterize that sensitivity. The commercial and industrial
paths are sector-specific annual growth assumptions because the LEDS states
that reliable GDP elasticities were unavailable. The residential path is the
more disaggregated household/appliance stock calculation.

This phase does not add:

- transport electrification;
- agriculture electricity;
- explicit water-pumping electricity;
- separate sector load shapes;
- distinct loss and station-use projections; or
- useful cooking, heating, cooling, motive-power or mobility services.

The next implementation gate should therefore be a sensitivity/scenario
wrapper around these documented drivers before activating a useful-service
branch. Residential cooking remains blocked until its magnitude, efficiencies,
fuel stacking, biomass boundary and biogas convention are resolved.
