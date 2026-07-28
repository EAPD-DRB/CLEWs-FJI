# Phase 1D cane–bagasse–electricity closure

**Date:** 28 July 2026

**Status:** Implemented in the live source case; dedicated validation passed;
general Fiji validation incomplete at 14/15

**Live case/run:** `Fiji_v2` / `Phase1D_Cane_Bagasse`

## Reason

The inherited model connected land to sugar-cane output but demanded raw
`CRPSGC` directly. Grid-supplying biomass was a separate aggregate chain:

```text
land -> CRPSGC -> direct accumulated demand

RNWBIOFJIXX -> BIOFJIXX -> PWRBIOFJIXX01 -> ELCFJIXX01
```

The electricity generated from bagasse therefore had no dependence on cane
production or mill throughput. The 34 MW aggregate biomass technology also
combined documented FSC bagasse and Tropik Wood residue plants and allowed
future expansion without a separate resource boundary.

## Sources and traceability

Every external source, page locator, URL and checksum is recorded in
`data_sources/evidence/energy/PHASE_1D_SOURCE_EXTRACTS_2026-07-28.md`.
The frozen source/derivation table is
`data_sources/evidence/energy/fiji_phase1d_cane_bagasse_power_balance_2020_2024.csv`,
SHA-256
`f3bc9cf7d1c0ddbbe15e2a3d08b84d3995732dfae49b118eb1970c2a0b2e9717`.

The active sources are:

- FSC annual reports for 2020–2024 cane crushed, sugar and molasses;
- IRENA 2019, PDF p. 37, Table 3.1, for the 25.4 kWh/t-cane
  export-electricity proxy;
- the Government of Fiji REI Investment Plan for the 25 MW FSC and 9 MW
  Tropik stock split; and
- EFL's 2024 Annual Report for aggregate 2020–2024 IPP purchases.

All equations and units are in
`data_sources/calculation_notes/PHASE_1D_CANE_BAGASSE_ELECTRICITY.md`.
The source-to-parameter path is registered under `M-1D-01`–`M-1D-03` in
`data_sources/MODEL_DATA_MAP.csv`.

## Implemented structure

After:

```text
land -> CRPSGC [Mt]
     -> SGCMILLFJI
          -> SGCPROCFJI [Mt processed-cane demand]
          -> BAGEXPFJI [PJ exportable energy]
     -> PWRBAGFJIXX01
     -> ELCFJIXX01

RNWBIOFJIXX -> BIOFJIXX -> PWRWODFJIXX01 -> ELCFJIXX01
```

Added technologies:

- `SGCMILLFJI`;
- `PWRBAGFJIXX01`; and
- `PWRWODFJIXX01`.

Added commodities:

- `SGCPROCFJI`; and
- `BAGEXPFJI`.

`PWRBIOFJIXX01` remains as a disabled shell with zero residual capacity,
maximum capacity investment and activity upper limit.

## Source files and parameters changed

Permanent changes originate in:

- `scripts/apply_fiji_phase1d_cane_bagasse.py`;
- `scripts/validate_fiji_phase1d_cane_bagasse.py`;
- `scripts/score_historical_fit.py`;
- `scripts/audit_fiji_topology.py`;
- `scripts/validate_fiji_v2.py`;
- `muio/reserve_margin_proxy_config.json`; and
- the relevant portable CSV files under `model/inputs/`.

The structural edit was passed through MUIOGO `UpdateCase`. The active MUIO
source changes are in:

- `genData.json`: new entities, relations and corrected cane metadata;
- `RYC.json`: raw-cane accumulated demand moved to processed cane;
- `RYT.json`: capacities, availabilities and activity bounds;
- `RYTCM.json`: mill and generator input/output ratios;
- `RT.json`, `RYTM.json` and `RYTTs.json`: mill and split-generator technical
  parameters;
- `RYCn.json` and `reserve_margin_proxy.json`: refreshed derived reserve
  proxy; and
- regenerated view JSON.

No permanent change was made to `data.txt`, `data_processed.txt`, an LP file
or solver results.

## Numerical formulation

Historical processed-cane demand in Mt is:

```text
2020  1.729171
2021  1.417185
2022  1.639004
2023  1.565586
2024  1.331922
```

Post-2024 demand is the inherited cane path rebased to the FSC 2024 actual.
It is 1.337652981 Mt in 2025 and 1.372601601 Mt in 2050.

The mill coefficients are:

```text
1 Mt CRPSGC
  -> 1 Mt SGCPROCFJI
  -> 0.3493008 PJ BAGEXPFJI

3.82 PJ BAGEXPFJI
  -> 1 PJ ELCFJIXX01
```

This reproduces 25.4 kWh exported per tonne cane.

The inherited residual-capacity path is split 25/34 and 9/34. Wood
availability is `0.338533130391`, and annual wood activity is capped at
`0.0960838272 PJ`, equivalent to the mean 2020–2022 residual
26,689.952 MWh.

## Disposable controls

Two disposable cases were generated from the Phase 1C source:

1. `Fiji_v2_Phase1D_Accounting_Test` / `Phase1D_Accounting`; and
2. `Fiji_v2_Phase1D_Physical_Test` / `Phase1D_Physical_Capped`.

The accounting case uses inherited cane demand and aggregate availability. An
artificial 10 PJ bagasse output per Mt cane keeps its resource nonbinding over
the whole horizon. This number is diagnostic only.

Accounting results:

- CBC: Optimal;
- objective: `-1573.67381668`;
- Phase 1C baseline: `-1573.67149091`;
- difference: `-0.00232577` (`-0.000147793%`);
- aggregate biomass activity difference: at most
  `1.11 × 10^-16 PJ`; and
- unrelated annual technology-activity rows: 3,999 compared, zero changed.

The tiny objective drift is caused by equivalent investment timing after the
technology split, not by dispatch or resource differences. Solve time is
about one second, so the initial diagnostic solve-time regression was removed
before promotion.

## Live validation chain

The physical case and the promoted live case completed:

1. structural update through `UpdateCase`;
2. MUIO `generateDatafile`;
3. MUIO preprocessing;
4. GLPK `--check` and LP matrix creation;
5. CBC optimization through the normal MUIO path;
6. source/mapping inspection;
7. baseline, activity, capacity, balance and dual comparisons;
8. frozen historical-fit scoring; and
9. result timestamp and case/run identity checks.

The live matrix contains 161,160 rows, 127,358 columns and 944,969 nonzeros.
CBC solved Optimal in about one second at objective `-1548.8662358`.
Relative to Phase 1C, the objective is 24.80525511 higher, or 1.576266%.

All 15 dedicated Phase 1D checks pass. Exportable-bagasse annual balance
residuals are below `7 × 10^-17 PJ`; the largest reported selected dual is
`5.911028 × 10^-6` in 2050. Reserve-proxy status is `CURRENT` with zero
mismatches. All 12 source-lineage checks also pass, including external
checksum, calculation, portable-input and result-free archive tests.

Aggregate IPP generation MAPE is 4.97575% in the 2020–2022 calibration period
and 8.91430% in held-out 2023–2024.

The live hashes and full findings are in
`diagnostics/calibration_runs/phase1d/live_validation_summary.json`; lineage
findings are in
`diagnostics/calibration_runs/phase1d/data_lineage_validation_summary.json`.

## Incomplete check and limitation

The general Fiji technical validator passes 14 of 15 checks. Its failed check
is 2024 thermal generation at 20.6466% above observation against the existing
20% single-outcome threshold. Aggregate held-out material-generation MAPE is
10.3014%, and renewable-share MAE is 5.4391 percentage points.

The miss is principally the existing 2024 hydro underproduction combined with
the fixed total grid-supply boundary. Phase 1D improves the absolute 2024 IPP
error slightly, but the lower biomass quantity shifts the balance to thermal.
The bagasse or wood parameters were not retuned to the held-out year.
Accordingly, Phase 1D is implemented and dedicated-validated but must not be
described as fully validated.

## Topology result

The live read-only topology audit reports:

- 134 technologies and 106 commodities;
- 78 connected commodities;
- 28 produced, unconsumed and undemanded commodities;
- 23 inactive end-use output stubs; and
- 32 classified warnings.

The two new physical commodities are connected and introduce no
consumed/unproduced or demanded/unsupplied error.

## Next gate

Run a declared sensitivity envelope for the IRENA bagasse-export coefficient
and the inferred wood-residue bound. Separately address the 2024 hydro/thermal
dispatch miss with observed hydro conditions rather than tuning the
cane–bagasse closure to held-out electricity output.
