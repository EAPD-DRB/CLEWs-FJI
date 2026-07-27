# Phase 1B public-water evidence, design and implementation record

**Date:** 27 July 2026
**Status:** complete and validated in the active Fiji v2 case

## Decision

Phase 1B closes the public-water service while keeping unsupported details
out of the model:

```text
WTRSURFJI --DEMPUBSURFJI--> PUBWATFJI --> observed annual demand

WTRGRCFJI --WTRABSFJI--> WTRGWRFJI --DEMPUBGWTFJI--> PUBWATFJI
                                      (quarantined)
```

`WTRGRCFJI` is an annual groundwater-recharge flow, not delivered water and
not a measured abstraction limit. `WTRABSFJI` and `WTRGWRFJI` therefore make
the groundwater boundary explicit. The public-groundwater route is assigned
zero annual activity through 2050 until Fiji-specific public-groundwater
abstraction and pumping evidence is available.

## Evidence and boundary

The primary source is the Fiji Bureau of Statistics, *Fiji's Experimental
Environmental Account for Water 2024*, Appendix, Physical Supply and Use
Tables for Water:

<https://www.statsfiji.gov.fj/download/240/releases/4667/2024-fijis-experimental-environmental-account-for-water.pdf>

The extracted evidence is retained in
`data_sources/evidence/water/fiji_water_account_2024_public_supply_2020_2024.csv`.
The tables report megalitres (ML). For 2020–2024, Water Authority of Fiji
abstraction is reported as surface water. The model's public-water service is
the sum of billed household, government, commercial and carted-water use:

| Year | Public delivery (ML) | Model demand (km3) | WAF surface abstraction (ML) |
|---:|---:|---:|---:|
| 2020 | 70,079 | 0.070079 | 143,660 |
| 2021 | 71,071 | 0.071071 | 140,979 |
| 2022 | 69,294 | 0.069294 | 141,298 |
| 2023 | 68,332 | 0.068332 | 138,941 |
| 2024 | 67,091 | 0.067091 | 151,467 |

The conversion is:

```text
1 ML = 10^-6 km3
public demand [km3] = public delivery [ML] / 1,000,000
```

The model water unit is physically `km3`: land activity is in thousand km2
and its precipitation/evapotranspiration/runoff coefficients are water depths
in metres, so:

```text
1,000 km2 * 1 m = 1 km3
```

The prior `PJ` labels on water commodities and water-delivery activities were
metadata errors. Phase 1B corrects them without changing the underlying
land-water coefficients.

## Loss representation

The water account closes each WAF surface-supply year as:

```text
surface abstraction
  = purification loss + billed/carted delivery + distribution loss
```

The historical input ratio on `DEMPUBSURFJI` is therefore:

```text
InputActivityRatio
  = WAF surface abstraction / public delivery
```

This yields 2.049972, 1.983636, 2.039109, 2.033323 and 2.257635 for
2020–2024. Output remains one unit of `PUBWATFJI` per unit of technology
activity. The annual demand profile equals `YearSplit`, a declared flat-rate
allocation necessitated by annual-only evidence.

## Electricity boundary

The inherited public-groundwater input `COMELCFJIXX02 * 0.0173` is removed.
Upstream `clewsy.py` identifies that coefficient as copied from Bolivia and
also comments that its magnitude may be wrong. It is not Fiji evidence.
`COMELCFJIXX02` is commercial electricity and must not be consumed by public
water.

No replacement pumping or treatment electricity coefficient is introduced
in Phase 1B because:

1. no Fiji-specific pumping/treatment intensity was found in the retained
   evidence; and
2. `ELCFJIXX02` is calibrated to gross national grid supply, which already
   includes water-sector electricity, so adding an explicit input without
   adjusting residual electricity demand would double count it.

This is an explicit data gap, not an assumption of zero physical energy use.
Source mix and pumping emissions cannot yet be claimed as endogenous.

## Source changes

The reproducible generator is
`scripts/apply_fiji_phase1b_public_water.py`. It:

- adds `WTRABSFJI` and `WTRGWRFJI` with collision-checked MUIO IDs;
- passes the structural edit through MUIO `UpdateCase`;
- changes `DEMPUBGWTFJI` from commercial electricity to raw groundwater;
- sets `DEMPUBGWTFJI` annual activity and capacity investment upper bounds to
  zero for 2020–2050;
- applies observed public demand and surface abstraction/delivery ratios for
  2020–2024;
- applies a `YearSplit` demand profile;
- corrects water metadata units and descriptions;
- can synchronize the portable otoole CSV source inputs; and
- supports a no-write dry run and disposable target case.

It never copies or edits `data.txt`, `data_processed.txt`, LP files, results,
or saved result archives.

## Validation status

Phase 1B was first applied to the disposable
`Fiji_v2_Phase1B_Test` case. After that chain passed, the same generator was
applied to the active `Fiji_v2` case. The active source JSON was regenerated
through MUIO `UpdateCase`; the reserve-margin proxy was refreshed and reports
`CURRENT` with zero mismatches.

The live `Phase1B_Public_Water` run completed the required chain:

1. `DataFile(case).generateDatafile(run)`;
2. `preprocessData()`;
3. `glpsol --check` and LP creation;
4. CBC optimization through the normal MUIO solve path; and
5. result export, fit scoring, dedicated water validation and general
   technical validation.

CBC solved Optimal with objective `-1387.57010517`. The unchanged
post-OHC `Historical_Backcast` is the baseline at `-1387.57013590`. The
increase is `0.00003073`, or `0.000002215%`, and agrees with the discounted
operating cost of the added public-water activity to within
`4.66 × 10^-9`.

All 15 dedicated Phase 1B checks pass:

- 131 technologies and 104 commodities are present;
- all seven water commodities use `km3` metadata;
- the commercial-electricity/public-groundwater bug is absent;
- all intended MUIO and generated activity mappings are present;
- 2020–2024 public demand and surface abstraction/delivery ratios match the
  retained FBoS extract;
- the flat annual demand profile is normalized;
- public groundwater activity, abstraction and investment are zero;
- public surface-water activity equals annual delivery demand exactly;
- no existing non-water activity changed across 7,409 compared result rows;
- no existing technology emission changed across 4,030 compared rows; and
- the live case identity and result timestamps match.

The general Fiji validator also passes 15 of 15 checks. Held-out energy fit is
unchanged: 2023–2024 material generation MAPE is `9.9388%` and renewable-share
MAE is `5.1328` percentage points. The post-change topology audit finds 73
connected commodities and 31 produced/unconsumed/undemanded commodities,
compared with 71 and 32 at Phase 1A.

The authoritative reports are:

- `diagnostics/calibration_runs/phase1b/live_validation_summary.json`;
- `diagnostics/calibration_runs/phase1b/live_technical_validation_summary.json`;
- `diagnostics/calibration_runs/phase1b/live_historical_fit/summary.json`;
- `diagnostics/calibration_runs/phase1b/live_reserve_margin_proxy_check.json`;
- `diagnostics/topology/2026-07-27_phase1b_live/`; and
- `MODEL_FIXES_2026-07-27.md`.

The generated live artifacts have the following SHA-256 hashes:

| Artifact | SHA-256 |
|---|---|
| `data.txt` | `281fe0dcdf6e9e619aefa0e6e3dd9414cf59da4f67bd496ec78c54874d12c2f0` |
| `data_processed.txt` | `6c77e2dfd0e32a8fa221c70992e46282b83bd0db27091b7eb340e80b6fd5968a` |
| `lp.lp` | `b38e54d1f6306bed51de24f017edfef0f3e4d44536fbb9415531f2439bd4a7d4` |
| `results.txt` | `4fcad8c3f90931295dc4dcbb32f8f4d35a6d37a9d44a157d6f3bbcfc39e78da2` |
| `ObjectiveValue.csv` | `500fc835ab6db8f61e4bbf4281b5fac1f230fa5b9a2b7c73dd568c961a87fc80` |

The result-free import package is
`muio/Fiji_v2_v2.0.2_MUIO.zip`, SHA-256
`62ef6b2b3ec683a0f0ae7d50eca9435c7214892186f75d87acb8358123262053`.

## Remaining limitations and next gate

Phase 1B does not calibrate the full water system. It does not estimate
pumping/treatment electricity, groundwater source share, seasonal water
demand, basin constraints, storage, environmental flows or demand after 2024.
The next step is Phase 1C's evidence/design gate for useful end-use services;
it should not create service demand or efficiencies until their statistical
boundaries and sources are documented.
