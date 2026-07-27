# Fiji v2 model fixes — 27 July 2026

## Phase 1B public-water closure

### Reason

The Phase 1A audit found that `PUBWATFJI` had two supply technologies but no
demand. It also found the invalid inherited chain
`COMELCFJIXX02 -> DEMPUBGWTFJI -> PUBWATFJI`: public groundwater consumed a
commercial-service electricity commodity and no groundwater. Meanwhile,
`WTRGRCFJI` was active annual recharge with no downstream abstraction layer.

### Source files and parameters changed

Permanent changes originate in:

- `scripts/apply_fiji_phase1b_public_water.py`;
- `model/inputs/TECHNOLOGY.csv` and `FUEL.csv`;
- `model/inputs/InputActivityRatio.csv`;
- `model/inputs/OutputActivityRatio.csv`;
- `model/inputs/SpecifiedAnnualDemand.csv`;
- `model/inputs/SpecifiedDemandProfile.csv`; and
- `model/inputs/TotalTechnologyAnnualActivityUpperLimit.csv` and
  `TotalAnnualMaxCapacityInvestment.csv`.

The active MUIO structural edit was passed through `UpdateCase`. Values were
then written to `genData.json`, `RYTCM.json`, `RYC.json`, `RYCTs.json` and
`RYT.json` through the reproducible generator. No permanent edit was made to
`data.txt`, `data_processed.txt`, an LP file or solver results.

### Before and after

Before:

```text
COMELCFJIXX02 -> DEMPUBGWTFJI -> PUBWATFJI
WTRSURFJI     -> DEMPUBSURFJI -> PUBWATFJI
PUBWATFJI demand = absent
```

After:

```text
WTRGRCFJI -> WTRABSFJI -> WTRGWRFJI -> DEMPUBGWTFJI -> PUBWATFJI
             inactive                    quarantined

WTRSURFJI -> DEMPUBSURFJI -> PUBWATFJI -> observed demand
```

`WTRABSFJI` and `WTRGWRFJI` were added. Public groundwater annual activity
and capacity investment are capped at zero for 2020–2050 pending Fiji
groundwater and pumping evidence. Public surface-water input ratios are the
observed Water Authority of Fiji surface abstraction divided by billed/carted
public delivery. Public demand is `0.070079`, `0.071071`, `0.069294`,
`0.068332` and `0.067091 km3` in 2020–2024. Its profile equals `YearSplit`.
Water commodity metadata was corrected from `PJ` to `km3`.

No explicit pumping/treatment electricity coefficient was added because no
Fiji-specific coefficient was found and the existing gross-grid-supply
boundary already includes water-sector electricity. This is a declared data
gap, not a physical-zero claim.

### Evidence

The primary evidence is Fiji Bureau of Statistics, *Fiji's Experimental
Environmental Account for Water 2024*, Appendix Physical Supply and Use
Tables. The retained extract is
`data_sources/evidence/water/fiji_water_account_2024_public_supply_2020_2024.csv`,
SHA-256
`700629cd41272588bf5cceb04fce6d0ac2405afc5ffd4ee27e005d4788da622e`.
The design and unit decisions are recorded in
`documentation/history/structural/PHASE_1B_PUBLIC_WATER_2026-07-27.md`.

### Generated artifacts and baseline

- Disposable case: `Fiji_v2_Phase1B_Test`.
- Promoted active case: `Fiji_v2`.
- Live run: `Phase1B_Public_Water`.
- Baseline: unchanged post-OHC `Fiji_v2/res/Historical_Backcast`.
- Baseline objective: `-1387.57013590`.
- Phase 1B objective: `-1387.57010517`.
- Objective change: `0.00003073` (`0.000002215%`).

The live generated artifact hashes are recorded in
`diagnostics/calibration_runs/phase1b/live_validation_summary.json`. They are
not included in the portable MUIO archive.

### Validation results

- MUIO generation: passed.
- MUIO preprocessing: passed.
- `glpsol --check` and LP construction: passed.
- CBC optimization: Optimal.
- Reserve-margin proxy: `CURRENT`, zero mismatches.
- Dedicated Phase 1B validation: 15/15 passed.
- General Fiji technical validation: 15/15 passed.
- Existing non-water activity comparison: 7,409 rows, zero changed.
- Existing emissions comparison: 4,030 rows, zero changed.
- Held-out energy fit: unchanged at 9.9388% generation MAPE and 5.1328
  percentage-point renewable-share MAE.
- Result freshness and case identity: passed.
- Topology audit: 73 connected; 31 produced/unconsumed/undemanded; default
  passes with 35 classified warnings.

### Incomplete checks and limitations

No Fiji-specific public-water electricity intensity, groundwater abstraction
share, seasonal demand profile, basin constraint, storage, environmental
flow or post-2024 demand path was available. Public groundwater therefore
remains quarantined and public-water validation is limited to annual
2020–2024 delivery and aggregate surface abstraction accounting.
