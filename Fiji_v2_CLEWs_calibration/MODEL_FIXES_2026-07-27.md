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

## Phase 1C sector electricity and bottom-up demand

### Reason

The Phase 1C.0 gate found that the inherited commercial, industrial and
residential electricity adapters were structurally valid but inactive. The
model instead placed the full grid requirement directly on `ELCFJIXX02`.
Adding sector demand on top of that quantity would double count electricity.

Fiji Bureau of Statistics evidence supports an exact 2020–2024 split into
commercial, industrial, central-grid residential, distribution-loss and
station-use/boundary-residual components. The user selected independently
projected future sector demand rather than frozen 2024 shares.

### Source files and parameters changed

Permanent changes originate in:

- `scripts/apply_fiji_phase1c_bottom_up_demand.py`;
- `scripts/validate_fiji_phase1c_bottom_up_demand.py`;
- `scripts/manage_reserve_margin_proxy.py`;
- `muio/reserve_margin_proxy_config.json`;
- `model/inputs/SpecifiedAnnualDemand.csv`;
- `model/inputs/SpecifiedDemandProfile.csv`; and
- `model/inputs/VariableCost.csv`.

The live MUIOGO source changes are in:

- `RYC.json` (`SAD`);
- `RYCTs.json` (`SDP`);
- `RYTM.json` (`VC`, mode 1 for the three adapters);
- `RYCn.json` (regenerated reserve-proxy constants);
- `reserve_margin_proxy.json`; and
- `genData.json` description metadata.

No structural entity was added, so `UpdateCase` was not required. No permanent
edit was made to `data.txt`, `data_processed.txt`, an LP file or solver
results.

### Before and after

Before:

```text
ELCFJIXX02 -> direct gross demand

ELCFJIXX02 -> DEMCOMELCFJIXX02 -> COMELCFJIXX02 -> no demand
ELCFJIXX02 -> DEMINDELCFJIXX02 -> INDELCFJIXX02 -> no demand
ELCFJIXX02 -> DEMRESELCFJIXX02 -> RESELCFJIXX02 -> no demand
```

After:

```text
ELCFJIXX02 -> direct loss and station/boundary overhead demand
ELCFJIXX02 -> DEMCOMELCFJIXX02 -> commercial grid demand
ELCFJIXX02 -> DEMINDELCFJIXX02 -> industrial grid demand
ELCFJIXX02 -> DEMRESELCFJIXX02 -> central-grid residential demand
```

The three adapters retain 1:1 input/output ratios. Their inherited `0.0001`
mode-1 variable cost is set to zero because it was a generic numerical
placeholder; an accounting-only split must not add cost.

Historical demand closes exactly. For 2024, in PJ:

```text
4.3880616000
  = 1.8214069392 commercial
  + 0.8443905300 industrial
  + 1.2548027232 central-grid residential
  + 0.4674614076 loss plus boundary overhead
```

From 2025:

- commercial electricity grows 2.6% annually from the observed 2024 anchor;
- industrial electricity grows 2.0% annually;
- residential electricity uses a 2024-normalized household/appliance stock
  index with LEDS household growth, urbanization, appliance adoption,
  appliance intensity and MEPS turnover, plus MICS urban/rural central-grid
  access;
- direct overhead is 11.9232103418% of those three end-use quantities; and
- all four demand components use the inherited normalized four-slice
  electricity profile.

Gross demand is 4.4584995 PJ in 2025 and 7.2373759 PJ in 2050. The 2050 value
is 3.1444347 PJ (30.2879%) below the inherited Phase 1B trajectory.

The reserve-margin proxy now sums direct, commercial, industrial and
residential demand rates. Otherwise, moving demand out of `ELCFJIXX02` would
have understated the adequacy requirement.

### Evidence

Historical quantities come from Fiji Bureau of Statistics, *Fiji's
Experimental Environmental Account for Energy 2024*, with the retained extract
`data_sources/evidence/energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv`.

Projection assumptions come from the Government of Fiji, *Fiji Low Emission
Development Strategy 2018–2050* (PDF SHA-256
`eb424c7f05c4e038dcf12cf28814f80c300b7127dfc4850f088bc1c25db191eb`)
and Fiji MICS 2021. The formulas and evidence boundaries are recorded in
`documentation/history/structural/PHASE_1C_BOTTOM_UP_ELECTRICITY_DEMAND_2026-07-27.md`.

The complete source identities, official URLs, retrieval checksums and
page/table locators are in
`data_sources/evidence/energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md`.
The frozen 2020–2050 calculation table is
`data_sources/evidence/energy/fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv`,
SHA-256
`f58c1ec3df4b6017966a2ad542256dd2f3e1f847837bd8bdc722ab9175ac181a`.
The formula-level audit is
`data_sources/calculation_notes/PHASE_1C_BOTTOM_UP_ELECTRICITY.md`.

### Generated artifacts and baseline

- Phase 1B baseline: `Fiji_v2_Phase1B_Test/res/Phase1B_Public_Water`.
- Accounting control:
  `Fiji_v2_Phase1C_Accounting_Test/res/Phase1C_Accounting`.
- Bottom-up disposable case:
  `Fiji_v2_Phase1C_BottomUp_Test/res/Phase1C_BottomUp`.
- Promoted live case: `Fiji_v2/res/Phase1C_BottomUp`.
- Phase 1B objective: `-1387.57010517`.
- Accounting-control objective: `-1387.57010517`.
- Live bottom-up objective: `-1573.67149091`.
- Bottom-up objective change: `-186.10138574` (`-13.4120%`).

The objective change is reported for regression control only. Because the
future demand path changes and the wider model retains unresolved negative
forest activity credit, it is not a welfare or savings estimate.

Live artifact hashes and timestamps are recorded in
`diagnostics/calibration_runs/phase1c/live_validation_summary.json` and
`live_general_validation_summary.json`. Generated solver artifacts are
excluded from the portable MUIOGO archive.

### Validation results

- Accounting-control MUIO generation and preprocessing: passed.
- Accounting-control GLPK matrix construction and CBC solve: Optimal.
- Bottom-up disposable generation and preprocessing: passed.
- Bottom-up disposable GLPK matrix construction and CBC solve: Optimal.
- Live generation and preprocessing: passed.
- Live GLPK matrix construction and CBC solve: Optimal.
- Accounting objective parity: exact.
- Accounting non-adapter activity comparison: 7,409 rows, zero changed.
- Bottom-up versus accounting historical activity: 1,210 rows, zero changed.
- Historical capacity comparison: 655 rows, zero changed.
- Historical emissions comparison: 655 rows, zero changed.
- Annual sector adapter activity and gross-transmission closure: passed for
  all 31 years.
- Relevant annual balance duals: zero.
- Aggregate reserve-margin proxy: `CURRENT`, zero mismatches.
- Dedicated live Phase 1C validation: 15/15 passed.
- General live Fiji technical validation: 15/15 passed.
- Source/assumption/calculation/model-map lineage validation: 8/8 passed.
- Result freshness and case/version identity: passed.
- Topology audit: 76 connected; 28 produced/unconsumed/undemanded; 23
  inactive end-use output stubs; default audit passes with 32 classified
  warnings.
- Held-out 2023–2024 energy fit: unchanged at 9.9388% material-generation
  MAPE and 5.1328 percentage-point renewable-share MAE.

The reusable lineage report is
`diagnostics/calibration_runs/phase1c/data_lineage_validation_summary.json`.
It confirms unique ledger IDs, complete cross-reference resolution, evidence
and archive checksums, exact projection-to-input correspondence and complete
active-source locator coverage.

### Incomplete checks and limitations

No sector-specific load profiles, current commercial/industrial activity
drivers, separate future loss/station-use projections, transport
electrification, agriculture electricity or useful-service demand was added.
The LEDS ±10% uncertainty and conditional/high-ambition demand assumptions
have not yet been parameterized. Residential cooking remains inactive because
the MICS supplies technology shares rather than an annual useful-energy or
electricity magnitude. The next gate should add scenario sensitivities around
the documented Phase 1C drivers before activating a useful-service branch.

## Phase 1D cane–bagasse–electricity closure

### Reason

Sugar cane was produced by the land system but demanded directly, while
grid-supplying biomass used an independent aggregate resource and generator.
The model therefore did not require cane or mill throughput for bagasse
electricity and combined documented FSC bagasse and Tropik Wood capacity in
one expandable technology.

### Source files and parameters changed

Permanent changes originate in:

- `scripts/apply_fiji_phase1d_cane_bagasse.py`;
- `scripts/validate_fiji_phase1d_cane_bagasse.py`;
- `model/inputs/TECHNOLOGY.csv` and `FUEL.csv`;
- `model/inputs/AccumulatedAnnualDemand.csv`;
- `model/inputs/InputActivityRatio.csv` and `OutputActivityRatio.csv`;
- `model/inputs/ResidualCapacity.csv` and `AvailabilityFactor.csv`;
- `model/inputs/TotalTechnologyAnnualActivityUpperLimit.csv`;
- related cost, lifetime, capacity-factor and capacity-limit CSV files; and
- `muio/reserve_margin_proxy_config.json`.

The structural edit passed through MUIOGO `UpdateCase`. The live MUIO source
changes are in `genData.json`, `RT.json`, `RYC.json`, `RYCTs.json`,
`RYT.json`, `RYTCM.json`, `RYCn.json`, `RYTM.json`, `RYTTs.json` and
`reserve_margin_proxy.json`. No generated solver file was edited.

### Before and after

Before:

```text
land -> CRPSGC -> direct demand
RNWBIOFJIXX -> BIOFJIXX -> PWRBIOFJIXX01 -> ELCFJIXX01
```

After:

```text
land -> CRPSGC -> SGCMILLFJI -> SGCPROCFJI demand
                              -> BAGEXPFJI
                              -> PWRBAGFJIXX01 -> ELCFJIXX01
RNWBIOFJIXX -> BIOFJIXX -> PWRWODFJIXX01 -> ELCFJIXX01
```

Added entities are `SGCMILLFJI`, `PWRBAGFJIXX01`,
`PWRWODFJIXX01`, `SGCPROCFJI` and `BAGEXPFJI`. `CRPSGC` and
`SGCPROCFJI` use `Mt`; `BAGEXPFJI` uses `PJ`.

FSC 2020–2024 cane crushed is active processed-cane demand. Post-2024 demand
is the inherited path rebased to the FSC 2024 actual. The mill produces
0.3493008 PJ exportable bagasse per Mt cane; the generator consumes 3.82 PJ
per PJ electricity, reproducing the IRENA 25.4 kWh/t-cane central case.

The documented 34 MW aggregate stock is split into 25 MW bagasse and 9 MW
wood residue. Wood availability is `0.338533130391`, and activity is capped
at `0.0960838272 PJ/year`, derived only from the 2020–2022 EFL/FSC residual.
The old aggregate shell has zero residual capacity, investment and activity.

### Evidence

The complete source locators, URLs and checksums are in
`data_sources/evidence/energy/PHASE_1D_SOURCE_EXTRACTS_2026-07-28.md`.
The retained calculation table is
`data_sources/evidence/energy/fiji_phase1d_cane_bagasse_power_balance_2020_2024.csv`,
SHA-256
`f3bc9cf7d1c0ddbbe15e2a3d08b84d3995732dfae49b118eb1970c2a0b2e9717`.
Equations are in
`data_sources/calculation_notes/PHASE_1D_CANE_BAGASSE_ELECTRICITY.md`.

### Generated artifacts and baseline

- Baseline: `Fiji_v2/res/Phase1C_BottomUp`.
- Baseline objective: `-1573.67149091`.
- Accounting control:
  `Fiji_v2_Phase1D_Accounting_Test/res/Phase1D_Accounting`.
- Accounting objective: `-1573.67381668`.
- Physical disposable:
  `Fiji_v2_Phase1D_Physical_Test/res/Phase1D_Physical_Capped`.
- Live: `Fiji_v2/res/Phase1D_Cane_Bagasse`.
- Live objective: `-1548.8662358`.
- Live objective change: `+24.80525511` (`+1.576266%`).

Live generated-artifact hashes are recorded in
`diagnostics/calibration_runs/phase1d/live_validation_summary.json`. They are
not included in the portable archive.

### Validation results

- Disposable and live MUIO generation: passed.
- Preprocessing: passed.
- GLPK matrix creation: passed; 161,160 rows, 127,358 columns and 944,969
  nonzeros.
- CBC optimization: Optimal; about one second.
- Accounting aggregate biomass activity difference: at most
  `1.11 × 10^-16 PJ`.
- Accounting unrelated activity: 3,999 annual rows compared, zero changed.
- Dedicated Phase 1D validation: 15/15 passed.
- Source-lineage validation: 12/12 passed.
- Cane and bagasse flow closure: passed for all 31 years.
- Exportable-bagasse annual residual: below `7 × 10^-17 PJ`.
- Selected balance duals: zero through 2049; 2050 bagasse dual
  `5.911028 × 10^-6`.
- Reserve proxy: `CURRENT`, zero mismatches.
- Live/disposable source and objective identity: passed.
- Held-out aggregate IPP generation MAPE: 8.9143%.
- Topology: 78 connected; 28 produced/unconsumed/undemanded; no new topology
  error.

### Incomplete check and limitations

The general Fiji validator passes 14/15. It fails the existing single-outcome
threshold because 2024 thermal generation is 20.6466% above observation
against a 20% limit. Aggregate held-out material-generation MAPE is 10.3014%
and renewable-share MAE is 5.4391 percentage points. Phase 1D slightly
improves the 2024 absolute IPP error; the thermal miss reflects the existing
hydro deficit and fixed total-supply boundary. The held-out year was not used
to retune bagasse or wood parameters.

The IRENA coefficient is not Fiji mill measurement. Individual mills,
process steam, sugar/molasses co-products, bagasse storage, moisture,
crushing-season timing and outages are not represented. Tropik Wood output is
an inferred residual, and the future cane path is a scenario rather than an
FSC forecast. Phase 1D is therefore implemented and dedicated-validated but
not fully validated.

## 28 July 2026 — remove the superseded aggregate biomass shell

### Reason and prior/new formulation

`PWRBIOFJIXX01` (`TEC_w665d`) was retained as an inactive migration shell
when Phase 1D split the inherited aggregate biomass stock. It no longer
represented a physical stock, conversion, pass-through, accounting device,
backstop or demand.

Before removal, every year had zero `RC`, `TAMaxC`, `TAMaxCI`, `TAMinC`,
`TAMinCI`, `TAL` and `TAU`; the `Phase1D_Cane_Bagasse` result had zero
capacity, new capacity and activity. After removal, the technology and its
indexed source rows are absent. The active 25 MW bagasse and 9 MW
wood-residue technologies, mill, processed-cane demand and resource
constraints are unchanged.

The exact equation mapping and removal condition are recorded under
`C-1D-LEGACY-REMOVAL` in `data_sources/CALCULATIONS.csv`. No new external
data source or empirical value was introduced. The original aggregate stock
evidence remains `DS-FIJI-REI-IP`, and historical archives v2.0.0–v2.0.4
preserve the retired identifier.

### Source and portable-input changes

The change was made in `genData.json` and regenerated through MUIOGO
`UpdateCase`. Live source files changed:

- `genData.json`;
- `RT.json`;
- `RYC.json`;
- `RYT.json`;
- `RYTCM.json`;
- `RYTM.json`; and
- `RYTTs.json`.

After filtering only `TEC_w665d`, every nonlegacy source parameter matched
the control. Portable inputs removed 313 rows from 13
technology-indexed CSV files. The scripts are
`scripts/remove_fiji_phase1d_legacy_biomass.py` and
`scripts/validate_fiji_phase1d_legacy_removal.py`.

### Generated artifacts, baseline and validation

- Unchanged control: `Fiji_v2/Phase1D_Cane_Bagasse`.
- Disposable candidate:
  `Fiji_v2_Phase1D_Legacy_Removal_Test/Phase1D_Legacy_Removal`.
- Preserved source/result baseline:
  `Fiji_v2_Phase1C_BottomUp_Test/Phase1C_BottomUp`.
- Live candidate: `Fiji_v2/Phase1D_Legacy_Removal`.
- Cleanup validation: 11/11 passed.
- Original Phase 1D validation: 15/15 passed on disposable and live.
- Generation and preprocessing: passed through MUIOGO `DataFile`.
- GLPK matrix validation: passed; 160,383 rows, 126,737 columns and 937,818
  nonzeros.
- CBC: Optimal at `-1548.8662358`; live wall time about 1.05 seconds.
- Objective change from removal control: exactly zero.
- Capacity, new capacity, emissions, demands and Phase 1D flows: unchanged.
- Reserve proxy: `CURRENT`, zero mismatches.
- Historical calibration and held-out metrics: unchanged.
- Result timestamps and case/run identity: passed.

Machine-readable evidence is in
`diagnostics/calibration_runs/phase1d/legacy_removal_*`. The portable
v2.0.5 archive is result-free, contains no legacy ID and has SHA-256
`d818202c10c9dc3eb7b1d827b2afb827b2e87abdca40abc86e43978e1476724c`.

### Issues and limitations

The cleanup exposed an existing alternate optimum. Forty-four mode-level
activity rows shift only within declared land and renewable substitute
groups, while aggregate services remain unchanged. Six nonbinding water
surplus rows change in 2044/2050, and 371 discounted annual-balance shadow
prices change. All primal balances remain feasible and the maximum Phase 1D
balance difference is `3.12e-12`.

The broader validator still passes 14/15 because the inherited 2024 thermal
generation error is `20.647%`, just above the `20%` threshold. This was not
caused or repaired by the cleanup.

The reusable lessons and adopted guardrails are in
`documentation/LESSONS_LEARNED.md`. In particular, exact dual or
technology-level dispatch identity must not substitute for physical
invariant checks on a degenerate model, and each structural baseline must
retain both source and results.
