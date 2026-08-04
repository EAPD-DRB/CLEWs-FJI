# Fiji v2.7 model fixes

## 2026-08-03 — Source-traceable non-forcing Fisheries sector

Reason: Fiji v2.6 represented fishing energy only inside aggregate
agriculture/forestry/fishing and industry boundaries. It had no explicit fleet,
aquaculture, cold-chain or fish-processing technology choices and no traceable
Fisheries water/emissions account.

Physical design and observation classification: official 2020 catch,
aquaculture harvest, vessel/processor, ice and solar-freezer observations are
initial-condition evidence or validation benchmarks. The three modeled useful
services are final demands. Asset life, uniform-age retirement, technical
availability and input/output conversion are continuing full-horizon physical
dynamics. The Ministry's 2029 aquaculture goals and official ice output are
benchmark-only and do not constrain production, activity or investment.

Technology classification: `FSHCAPDSL`, `FSHCAPELE`, `FSHAQDSL`, `FSHAQELE`,
`FSHPOSTDSL`, `FSHPOSTELE` and `FSHPOSTSOL` are physical conversions. They are
not pass-throughs, accounting devices, backstops or demands. The service
commodities `FSHCAPSERV`, `FSHAQSERV` and `FSHPOSTSERV` are demands. No new
accounting terminal or user-defined constraint was added.

Source files changed:

- `genData.json`: one Fisheries group, three PJ useful-service commodities,
  seven technologies and Fiji_v2.7 identity/description.
- `RYC.json`: the three service demands and same-unit corrections to `SRVAGR`,
  `SRVINDHEAT`, `INDELCFJIXX02`, `ELCFJIXX02` and `PUBWATFJI`.
- `RYT.json`: availability, capital/fixed cost, residual capacity and open
  activity/capacity/investment bounds; only the inherited observed 2020-2023
  `MOTAGRDSL` and `HTINDDSL` exact boundaries are reduced by the reallocated
  Fisheries diesel amounts.
- `RT.json`: `CAU=1` and 10/12/15-year operating lives.
- `RYTCM.json`: mode-1 diesel/electricity/water inputs and unit service outputs.
- `RYTEM.json`: direct diesel CO2 coefficients; grid emissions remain upstream.
- `RYTM.json`: zero variable O&M, zero mode minima and host-open mode maxima.
- `RYTTs.json`: technical capacity factors of one in all four timeslices.
- `RYCTs.json`: equal 0.25 service profiles over the four timeslices.

Boundary before/after formulation: capture removes 0.11169422 PJ final diesel
(0.027923555 PJ at the inherited 0.25 agriculture efficiency) from the
agriculture/forestry/fishing boundary. Processing removes 0.00506389356 PJ
diesel (0.004051114848 PJ industry-heat service) and 0.02025557424 PJ
electricity from industry. Aquaculture removes its 0.000007789284 PJ 2020 grid
input, growing 5% annually, from national direct grid demand. Processing removes
0.00006026636 km3 public water in 2020-2024; the inherited public-water demand is
zero thereafter, so later Fisheries water is an explicit addition rather than
a subtraction. The machine-readable manifest records every year.

Equations and generated representation: the final services enter
`EBb4_EnergyBalanceEachYear4_ICR`; timeslice and annual stock/service envelopes
are `CAa4_Constraint_Capacity` and `CAb1_PlannedMaintenance`; annual activity
limits are `AAC2/AAC3`; capacity and investment limits are `TCC1/TCC2` and
`TAC2/TAC3`; mode limits are `LU1/LU2`. All seven generated
`MODEperTECHNOLOGY` sets contain only mode 1, and the expected diesel, grid,
water, service and CO2 mappings survived preprocessing.

Sources and calculations: the detailed registers are in
`docs/Fiji_v2.7_Fisheries/data_sources/fisheries/`. They contain 8 sources, 15
explicit assumptions, 20 linked calculations, 31 parameter mappings, 13
boundary decisions and 19 completeness checks. Central observations are Fiji
Ministry of Fisheries 2020-2021 data: 12,661 t offshore longline catch, 11,000
t coastal commercial catch, 4,327.38 kg aquaculture harvest, 1,429.22084 t ice
and four solar freezers. FAO fuel/processing engineering values are graded C
proxies with required sensitivity; all analyst priors and upgrade sources are
disclosed.

Generated artifacts inspected: application-generated `data.txt` and
`data_processed.txt`, derived mode/input/output/emission sets, GLPK LP export,
CBC results, full-precision result rows, CSV exports and pivots for the
disposable candidate and the independently regenerated live case.

Validation status: **PASSED**.

- Provenance validator: pass on cycle 2; zero errors or warnings.
- Residual-capacity estimator: pass; 155 annual technology rows.
- Deterministic design: 171 boundary reconciliations and 372 annual-timeslice
  stock/vintage/service envelopes passed, including survival and replacement
  of endogenous vintages; zero unexpected inherited source changes.
- Non-forcing audit: pass with zero errors. The one expected warning identifies
  zero pre-base residual capacity for diesel aquaculture and electric capture,
  for which no pre-2020 stock was evidenced.
- GLPK 5.0 `--check`: pass; 169,810 rows, 130,447 columns, 719,047 matrix
  nonzeros. This is +7,268 rows, +5,618 columns and +41,376 nonzeros relative
  to the unchanged Fiji v2.6 control.
- 60-second bounded CBC 2.10.13: optimal in 25.94 seconds, objective
  4130.82371520.
- Normal disposable application chain: optimal in 32.04 seconds end to end,
  objective 4130.82371520.
- Normal live application chain: optimal in 33.25 seconds end to end (CBC
  wallclock 28.03 seconds), objective 4130.82371520.
- Fresh unchanged Fiji v2.6 control: optimal in 31.73 seconds, objective
  4147.08805706. The candidate change is -16.26434186 (-0.392187%). Runtime
  change for the disposable full chain is +0.97%.
- Constraint checks: maximum raw Fisheries service residual is 9.5e-10 PJ;
  inherited `ENV_LAND_CLOSURE` residual is at most 7.11e-15.
- Case identity/timestamps: passed; live source, generated data, LP and result
  timestamps are ordered and the live objective exactly matches the disposable
  candidate. The nine authoritative Fisheries source files are byte-identical
  between disposable and live cases.

Solved Fisheries pathway: 2020 capture service is all diesel; post-harvest is
0.0029633168 PJ diesel plus 0.016279479 PJ integrated solar, while aquaculture
uses 0.000005841963 PJ electric service. By 2050 capture is 0.033508266 PJ
electric, aquaculture is 0.000025248627 PJ electric and post-harvest is
0.019242796 PJ electric. These shares are optimizer outcomes, not constraints.

Changes elsewhere: all unrelated source parameters are unchanged. Result
differences outside the direct boundary are indirect energy-system responses,
principally fuel-import costs, grid/bio supply and bagasse-linked sugarcane
timing. CBC also changes some zero-cost/open-capacity and dual rows because the
inherited model is degenerate; host-open 999999 auxiliary values are excluded
from physical comparisons. Full lists, residuals, duals and adjacent-year
changes are retained in
`docs/Fiji_v2.7_Fisheries/validation/control_candidate_comparison.json`.

Known limitations: this is a technically valid, source-traceable extension, not
a policy-grade Fisheries calibration. Fiji-specific fuel intensity, facility
energy/water, cost, asset-age/utilization, processor throughput/product mix,
feed/FCR, aquaculture land/water/wastewater, refrigerant leakage, bycatch and
stock-assessment-linked catch dynamics remain gaps. No artificial catch cap is
added in their place. The flat capture/post-harvest services, 5% aquaculture
service growth, 50% longline processing share and screening costs require
sensitivity analysis before policy use.

## 2026-07-31 — National one-mode land allocation and exact environmental closure

Reason: the inherited four-zone, 26-mode land layer consumed every land-class commodity before the environmental terminal, so `ENV_LAND` reported zero and the national allocation was not explicitly closed.

Source changes: `genData.json`, `RYTCM.json`, `RYTM.json`, `RYT.json`, `RYTTs.json`, `RYTCn.json`, `RYCn.json`, `view/resData.json`; source data are copied into `land_allocation_2020.json` and the complete formulation is in `national_land_manifest.json`.

Before: 26 national land pass-through technologies -> four `LNDAGRFJIC01`-`04` technologies with 26 modes -> crop/hydrology outputs; 26-mode `ENV_LAND`; unforced/postprocessed `ENV_WATER`.

After: the same 26 named `LND...TOT` technologies each have one active mode and directly produce their crop/hydrology outputs. The four zonal technologies and 22 redundant intermediate stock commodities are removed; the four natural stock commodities retained for `ENV_LAND` follow Namibia's pattern. Five continuing constraints enforce national land closure, the cropland and irrigation ceilings, environmental-land closure and water closure. `ENV_LAND` has four modes; `ENV_WATER` has three.

Allocation: total land 18.2729 thousand km²; forest 11.1344; grass/pasture 1.73; built-up 0.4313919726492575; inland water 0.16680430818632933; bare 0.0026639171888409225. Crop land is endogenous up to 1.386 and irrigated crop land up to 0.04; `LNDOTHTOT` closes the residual.

Validation status: **PASSED**. `validation_national_land.json` records both the disposable pre-promotion test and the post-promotion source validation. The live case was then regenerated, preprocessed and solved through `DataFile`; its current `results.txt` is optimal with objective 4147.08896485.

Checks completed: exact source-value and constraint-coefficient checks; MUIO generation and preprocessing; explicit `glpsol --check`; 30-second bounded CBC; normal CBC; fresh unchanged Fiji v2.5 control; result timestamp/case identity; annual national-land, environmental-land and environmental-water closures; stock, cropland and irrigation bounds; matrix, capacity, activity, emissions, residual/dual and adjacent-year comparisons.

Control comparison: Fiji v2.5 objective 3111.46795841; Fiji v2.6 objective 4147.08896485, a 33.2840% increase. The material accounting effect is the reduction of forest activity from the inherited all-residual-land allocation to the sourced 11.1344 thousand km² stock; this reduces the inherited mode-23 negative land operating-cost credit. The credit is carried forward to preserve source economics, but it is constant under the fixed forest stock and does not affect technology choices. Total annual technology-emission output is unchanged within exported CSV precision (31.6726 control; 31.6727 candidate summed across all years/emissions).

Matrix comparison: 162,542 rows, 124,829 columns and 677,671 matrix nonzeros; respectively 19,441, 21,268 and 327,827 fewer than the unchanged control. Reconstructed closure residuals from four-decimal result CSVs are at most 0.0002 thousand km² for national land, effectively zero for `ENV_LAND`, and 0.00056 km³ for `ENV_WATER`; the underlying solver equalities are exact.

Solved allocation: cropland activity ranges from 0.6588 to 0.8626 thousand km² against the 1.386 ceiling; irrigated crop activity is zero against the 0.04 ceiling. `ENV_LAND` ranges from 16.8122 to 17.0159 thousand km² and `ENV_WATER` from 46.4627 to 46.6144 km³. In 2020, `ENV_LAND` is 16.9870 thousand km²: 11.1344 forest + 1.7300 grass/pasture + 4.1199 other/fallow + 0.0027 bare (display-rounded).

Known limitation: forest, grass/pasture, built-up, inland-water and bare stocks are held constant through 2050 because the case has no land-conversion technologies. Crop activity is endogenous and `LNDOTHTOT` absorbs unused/fallow land; the model does not force observed harvested area or crop shares.

## 2026-07-31 — Canonical six-ledger provenance migration

Reason: source records, formulas, assumptions and change history were dispersed
across Phase 1F-1K JSON files and the land/water manifests, so there was no
single validated route from an active parameter family back to its evidence.

Change: created the canonical package `docs/Fiji_v2.6_CLEWs_build` with the six
`build-clews-model` ledgers. It contains 23 source records, 99 calculation
records, 61 assumptions, 169 model mappings, 15 disclosed gaps and 9 historical
change records. `model/inputs/active_source_files.csv` inventories all 32 live
case JSON files. The live case README points to this package; existing phase and
land/water JSONs remain detailed supporting records rather than competing
canonical ledgers.

Traceability boundary: every active source JSON has an immediate lineage map.
Changed families have parameter-specific evidence/calculation mappings.
Unchanged cells point to Fiji v2.5; the absence of complete original CLEWs
Global evidence for those inherited values is explicitly recorded in
`GAPS.csv`. No source is invented to fill that gap.

SHA policy: all `SOURCES.csv.sha256` cells are intentionally blank at the
user's direction. Public provider URLs and exact dataset/query/table locators
are recorded instead. The package's cryptographic baseline freeze is therefore
marked `not_frozen`.

Validation: scaffold, package-build, provenance-build and provenance-delivery
checks passed. Delivery coverage is 1/1 for the JSON-native active-file
inventory. The eight warnings are blank commit IDs for working-tree changes;
there are no missing ledger files, broken evidence references, orphaned
calculations or uncovered inventory inputs. No model parameter or solver result
was changed, so the previously passed CBC solve remains the applicable model
validation.

## 2026-07-31 — CMIP6 SSP2-4.5 precipitation pathway

Reason: precipitation was constant from 2020 through 2050. This change retains the 2020 model value and applies the World Bank CCKP CMIP6 SSP2-4.5 ensemble-median anomaly through 2050.

Source changes: `RYTCM.json` scales WTRPRCFJI inputs and the linked WTREVTFJI, WTRGRCFJI and WTRSURFJI outputs for all 26 national land technologies. `RYTCn.json` is rebuilt from those effective ratios so `ENV_WATER_CLOSURE` remains exact. Descriptions and manifests are updated; no model object or equation family is added.

Before: precipitation and hydrological coefficients were constant. After: the multiplier is 1.0 in 2020, follows the 2020-2039 median anomaly at its 2030 midpoint, and follows the 2040-2059 median anomaly at its 2050 midpoint, with annual linear interpolation.

Disposable validation status: PASSED. A fresh unchanged Fiji_v2.6 control and the candidate both passed application generation, preprocessing, `glpsol --check`, the 60-second bounded CBC run and the normal CBC chain. The matrix remained 162,542 rows, 124,829 columns and 677,671 nonzeros. Objective changed from 4147.08896485 to 4147.08805706 (-0.00002189 percent); all but 8.5e-8 of the difference is analytically attributable to lower MINPRCFJI variable cost. Precipitation is 46.59465 km3 in 2020, 45.77778 in 2030 and 45.82592 in 2050. The display-rounded precipitation balance residual is at most 0.0003 km3 and the raw ENV_WATER UDC residual is at most 2.2e-14 km3. Final demand and emissions are unchanged within validation tolerance; individual activity and zero-cost slack-capacity rows are not row-for-row identical because CBC selected an alternate optimal basis. The live application-chain result is recorded separately in `validation_ssp245_live.json` after promotion.

<!-- SSP245_LIVE_VALIDATION_START -->

Live validation status: **PASSED**. `validation_ssp245_live.json` records the
post-promotion in-place MUIO generation, preprocessing, explicit GLPK matrix
check and LP export, 60-second bounded CBC solve, normal CBC solve, source/result
timestamps and comparison with the timestamped pre-change Fiji v2.6 backup.

The live objective is 4147.08805706000 versus
4147.08896485000 in the unchanged control, a
-0.00002189% change. The expected discounted reduction
from lower `MINPRCFJI` activity is
-0.000907705395; the remaining
unattributed difference is only -8.46e-08. The
matrix is unchanged at 162,542 rows, 124,829 columns
and 677,671 nonzeros. Candidate bounded and normal CBC timings
were 24.50 and 28.87
seconds respectively.

Source checks covered 104 climate-linked
ratio rows (3,224 annual
values) and 930 annual water
closure coefficients, with no source changes outside the allowlist. Mode,
stock, capacity-factor and every-timeslice service envelopes were unchanged.

Solved precipitation is 46.5946 km3 in 2020,
45.7778 km3 in 2030 and 45.8259 km3 in 2050.
`ENV_WATER` is 46.4687, 45.7969 and
45.8451 km3 in those years. The maximum display-rounded
precipitation commodity-balance residual is
0.0003
km3; the maximum raw `ENV_WATER_CLOSURE` residual is
2.13e-14 km3.

The result is not row-for-row identical. CBC selected an alternate optimal
basis with 167
technology-year activity changes (maximum
0.1886) and
53 zero-cost slack-capacity changes, some reaching the inherited
999999 upper bound. Final demands are exactly unchanged; annual emissions are
unchanged within 0.0001 display precision; capital investment, annualized
investment cost and fixed operating cost are unchanged. The full production,
use, activity and capacity difference lists are retained in the live report.
These basis changes are disclosed as inherited model degeneracy, not attributed
to a new physical climate response.

Known limitations: the CCKP values are 20-year climatologies represented at
period midpoints; only the median is implemented; the p10/p90 range remains for
future sensitivity cases; proportional hydrology scaling is not a calibrated
rainfall-runoff model; and interannual, cyclone and subnational variability are
not represented.

<!-- SSP245_LIVE_VALIDATION_END -->

## 2026-08-03 — Population-driven crop demand and 2025 trade backstops

Reason: crop final demand in v2.7 reproduced observed crop production, so a
production shock could incorrectly reduce the amount of food the model had to
supply. Fiji v2.8 instead represents resident food needs, crop exports and a
minimum level of crop imports explicitly, without adding crop commodities.

Physical classification: `CRPCAS`, `CRPYAM`, `CRPCON`, `CRPOTH` and
`SGCPROCFJI` are existing final-demand commodities. Domestic crop/land
technologies are physical production; `SGCMILLFJI` is a conversion; the five
new `IMP...` technologies are accounting backstops. Observed 2020-2024
production is benchmark-only. Resident food use, the 2025 import floor and the
2025 export commitment are continuing demand/trade assumptions.

Source formulation: `RYC.json/AAD` equals resident food plus exports, both
scaled with UN WPP 2024 medium population. Tourism is excluded. `RYT.json/TAL`
sets the population-scaled 2025 import floor; open upper bounds and a screening
`RYTM.json/VC` of 10 allows imports to rise during drought, land or water
shortfalls while preferring domestic supply. `RYTCM.json/OAR` maps each import
backstop directly to its existing commodity. Sugar is expressed in the model's
cane-throughput equivalent. No export technology or new commodity is added.

Source files changed: `genData.json`, `RYC.json`, `RYT.json`, `RT.json`,
`RYTCM.json`, `RYTM.json`, and `RYTTs.json`. The source snapshot and all annual
series are in `population_crop_trade_v28_manifest.json`; the reproducible
generator is `scripts/create_fiji_v28_population_crop_trade.py`.

Validation status: **PASSED** for the disposable candidate. The deterministic
audit passed 25,930 source checks and 25,935 source-plus-generated checks. MUIO
generation and preprocessing passed; all five generated mode sets contain only
mode 1. GLPK 5.0 `--check` passed with 174,098 rows, 133,862 columns and
732,134 matrix nonzeros. CBC reached an optimal solution in 39.04 seconds end
to end (33.30 seconds reported solver wallclock), objective 4158.92072593.

The unchanged solved v2.7 control objective is 4130.82371520, so v2.8 changes
the objective by +28.09701073 (+0.680179%). Matrix size increases by 4,288
rows, 3,415 columns and 13,087 nonzeros. Result timestamps postdate source and
generated inputs. In normal operation, 2025 cassava and taro imports are zero;
coconut is 0.0002 Mt, `CRPOTH` 0.0702 Mt and sugar 0.1119 Mt cane-equivalent,
at their population-scaled floors within result-display precision.

A separate disposable 95% crop-yield-loss test solved optimally in 33.13
seconds. In 2025 imports rose above the normal case by 0.0589 Mt cassava,
0.0656 Mt taro/yam proxy, 0.0238 Mt coconut, 0.0668 Mt other crops and 0.1691
Mt sugar cane-equivalent. This verifies that imports respond to a severe local
production crash rather than replacing domestic supply in the normal case.

Known limitations: the screening import cost is a policy-ordering penalty, not
a calibrated border price; UN Comtrade physical export flows cannot fully
separate re-exports; coconut product weights are mapped one-for-one; rice and
sugar use disclosed crop-equivalent conversion factors; resident intake is a
2021-2023 food-availability average rather than a dietary recommendation; and
exports/import floors remain exogenous per-capita assumptions rather than a
trade model.

## 2026-08-04 — Population-driven Fisheries food demand and trade

Reason: Fiji v2.8 fixes Fisheries useful-service demands independently of the
amount of fish residents need. Fiji v2.9 adds an explicit annual fish mass
balance so population, domestic exports and imports determine how much capture,
aquaculture and post-harvest service is required.

Physical classification: `FSHRAW` and `FSHFOOD` are mass commodities.
`FSHCAPHARV`, `FSHAQHARV` and `FSHPOSTPRC` are one-year mass-link conversions;
their capacity is an accounting envelope rather than additional physical fleet,
farm or cold-chain stock. The seven v2.7 Fisheries service technologies remain
physical stocks/conversions. `IMPFSHFOOD` is an accounting backstop. `FSHFOOD`
is the final demand. Observed 2020 harvest and service values are calibration
benchmarks, not activity pins.

Source formulation: `RYC.json/AAD` for `FSHFOOD` equals resident food
availability plus domestic exports, both population-scaled. `RYT.json/TAL`
sets the population-scaled 2025 retained-import floor, with no upper import
limit. Retained imports are the sum of positive same-HS differences between
imports and reported re-exports, preventing processing/re-export throughput
from displacing domestic production. The
former `SAD` values for `FSHCAPSERV`, `FSHAQSERV` and `FSHPOSTSERV` are zero;
the mass-link technologies pull those services through `RYTCM.json/IAR`.
Tourism is not added. No catch quota, aquaculture expansion target or trade
price response is imposed.

Source files changed: `genData.json`, `RYC.json`, `RYT.json`, `RT.json`,
`RYTCM.json`, `RYTM.json`, and `RYTTs.json`. A disclosed `CC=1e-6` numerical
tie-breaker keeps the four accounting capacities at their minimum feasible
values instead of arbitrary open upper bounds. The evidence snapshot and all
annual series are in `population_fisheries_trade_v29_manifest.json` and
`scripts/data/fiji_v29_population_fisheries_trade.json`.

Validation status: **PASSED**.

- Deterministic source audit: 24,373 checks passed. Generated source/mapping
  audit: 24,382 checks passed; all four new technologies have only mode 1.
- GLPK 5.0 `--check`: passed at 178,353 rows,
  137,090 columns and 743,918 matrix nonzeros.
- The 75-second bounded CBC candidate solved optimally in 35.96 seconds;
  objective 4170.87205658000. The normal disposable chain
  solved in 40.88 seconds and the fresh
  live chain in 45.58 seconds, with the same
  objective.
- Relative to unchanged Fiji v2.8, the objective changes by
  +11.95133065
  (+0.287366%). The matrix adds
  4,255 rows,
  3,228 columns and
  11,784 nonzeros.
- Normal 2025 supply is 0.027689166 Mt domestic
  plus 0.004035732 Mt retained imports, meeting
  0.031724898 Mt final demand. The solver
  selects aquaculture for all normal domestic raw fish and zero capture harvest;
  this is an economic outcome of the current unconstrained screen, not a
  calibration target.
- In the disposable 95% domestic-production-loss test, 2025 imports rise to
  0.030340440 Mt, an increase of
  0.026304708 Mt, while final fish demand
  remains met. This verifies that extra imports respond to a domestic crash.
- Annual raw-fish, food-fish and useful-service balances close within
  1.05e-09 in their respective Mt/PJ
  units. Import floors bind within exported-result precision; their largest
  reported dual is 134.111480.
- The seven authoritative source files and generated `data.txt` are
  byte-identical between disposable and live cases; derived-set ordering in
  `data_processed.txt` is nondeterministic but both generated audits, matrix
  checks and objectives match. Source/data/LP/result timestamps are ordered.

Known limitations: fish is one aggregate market-weight commodity; species,
preservation state, edible yield, processing losses, feed, biological stocks,
catch quotas and aquaculture land/water limits are not represented. The import
variable cost is a screening penalty, not a border price.

Canonical documentation: `docs/Fiji_v2.9_Population_Crop_Fisheries_Trade/`
contains the six schema ledgers, retained evidence, calculation notes and
validation reports for the v2.8 crop and v2.9 Fisheries changes.

## 2026-08-04 — Aggregate capture and aquaculture activity ceilings

Reason: the population-driven Fisheries formulation allowed capture or
aquaculture to supply the whole domestic market without representing biological,
feed, land, water, farm-expansion or environmental limits. This made its
least-cost subsector split unsuitable even for a simple policy screen.

Physical and observation classification: `FSHCAPHARV` and `FSHAQHARV` remain
physical annual mass-balance conversions with one-year accounting capacities.
The 2020 included capture boundary (12,661 tonnes offshore longline plus 11,000
tonnes coastal commercial) is used as a continuing aggregate screening ceiling,
not a legal quota or biological stock estimate. The 2021-2022 aquaculture output
(212.83 tonnes tilapia plus 4.095 tonnes freshwater prawn) and the Fiji
Aquaculture Development Plan 2024-2028 commodity programmes define an aggregate
maximum expansion envelope, not demand or a production target. `FSHFOOD` remains
final demand and `IMPFSHFOOD` remains the open feasibility backstop.

Source formulation: only `RYT.json/TAU` changes. `FSHCAPHARV` changes from
999999 to 0.023661 Mt/year in every year 2020-2050. `FSHAQHARV` changes from
999999 to 0.000216925 Mt/year in 2020-2023, then 0.000350, 0.000530,
0.000800, 0.001180 and 0.001450 Mt/year in 2024-2028, with 0.001450
Mt/year held from 2029 through 2050. The active `AAC2` equation enforces these
annual upper limits. `TAL` remains zero for both technologies, so neither
subsector is forced to produce. No object, user-defined constraint, demand,
cost or import rule changes.

Evidence: Fiji Ministry of Fisheries Annual Reports 2020-2021 and 2021-2022,
and the Fiji Aquaculture Development Plan 2024-2028. Full source locators,
component arithmetic, interpolation and annual values are retained in
`scripts/data/fiji_v29_population_fisheries_trade.json` and
`population_fisheries_trade_v29_manifest.json`.

Validation status: **PASSED**.

- Deterministic source/generated audit: 24,635
  checks passed. Exactly 62 intended year-values changed; the other six
  authoritative files are semantically unchanged.
- GLPK 5.0 `--check`: passed at 178,353 rows,
  137,090 columns and 743,918 matrix nonzeros,
  identical to the unchanged v2.9 control.
- The 90-second bounded candidate solved optimally in 44.82 seconds at
  objective 4182.52681514000. The normal control and live CBC chains
  also solved optimally; the bounded candidate and live objectives match within
  exported precision.
- Relative to the unchanged v2.9 control, objective increases by
  +11.65475855 (+0.279432%). Normal-chain elapsed
  live-chain elapsed time is 51.29 seconds,
  versus 48.51 seconds for the control.
- In 2025, capture is 0.023661000 Mt, aquaculture is
  0.000530000 Mt, and imports are 0.007533898 Mt.
  Both domestic ceilings bind, final demand remains met, and imports exceed the
  retained-import floor by 0.003498166 Mt.
- All 31 annual capture and aquaculture activities respect and bind their
  aggregate ceilings within solver precision. Maximum absolute raw-fish,
  food-fish and Fisheries service balance residual is
  4.31e-10 Mt/PJ.
- Candidate and live `data.txt`, objective and selected Fisheries activities
  match. Source/data/LP/result timestamps are ordered; the previous live run is
  preserved as the baseline and the validated new run is
  `res/Fisheries_Bounds_Table18_v2.9`.

Known limitations: the capture ceiling is a conservative observed-boundary
proxy, not a stock assessment or quota trajectory. The aquaculture ceiling
aggregates feed, land, water, facility and wastewater restrictions rather than
modeling them separately. The plan also contains broader headline goals that
differ from its detailed Table 18 deliverables; this implementation deliberately
uses the more conservative detailed annual table. Fish remains one aggregate
market-weight commodity. The result is suitable for national screening of a plausible
capture/aquaculture mix, not species-, fleet-, farm- or site-level planning.

