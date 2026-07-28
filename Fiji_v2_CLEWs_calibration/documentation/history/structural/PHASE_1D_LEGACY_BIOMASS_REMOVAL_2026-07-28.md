# Phase 1D legacy biomass removal

## Decision

`PWRBIOFJIXX01` (`TEC_w665d`) was a migration shell retained when the
inherited aggregate 34 MW biomass stock was separated into 25 MW bagasse
(`PWRBAGFJIXX01`) and 9 MW wood residue (`PWRWODFJIXX01`). It is absent from
the active v2.0.5 model.

This is a structural cleanup, not a new calibration or physical assumption.
No empirical value was replaced. Historical archives v2.0.0–v2.0.4, the
Phase 1D implementation record and the cleanup diagnostics preserve the
identifier and its lineage.

## Equation-first gate

The control source set, for every model year:

```text
RC = TAMaxC = TAMaxCI = TAMinC = TAMinCI = TAL = TAU = 0
```

The `Phase1D_Cane_Bagasse` control result also has exactly zero
`TotalCapacityAnnual`, `NewCapacity` and
`TotalAnnualTechnologyActivityByMode` for the legacy technology.

Under the active OSeMOSYS formulation:

- `NCC1` prevents new investment through `TAMaxCI = 0`;
- `CAa2` gives zero total capacity from zero residual and new capacity;
- `CAa4` therefore permits no capacity-backed activity; and
- `AAC2` independently caps annual activity at `TAU = 0`.

Removing the variable and its indexed rows therefore removes a zero-only
shell. The surviving physical behavior remains the 25/9 MW split, processed
cane demand, the cane-limited bagasse branch and the separately capped wood
branch.

## Source changes

The structural deletion was made in `genData.json` and passed through
MUIOGO `UpdateCase`. The regenerated live source files changed were:

- `genData.json`;
- `RT.json`;
- `RYC.json`;
- `RYT.json`;
- `RYTCM.json`;
- `RYTM.json`; and
- `RYTTs.json`.

All nonlegacy source parameter rows were structurally compared after
filtering `TEC_w665d`; zero mismatches were found. The portable CSV inputs
remove 313 legacy-indexed rows from 13 files. The reproducible implementation
is `scripts/remove_fiji_phase1d_legacy_biomass.py`.

## Validation

Disposable control:
`Fiji_v2/Phase1D_Cane_Bagasse`.

Disposable candidate:
`Fiji_v2_Phase1D_Legacy_Removal_Test/Phase1D_Legacy_Removal`.

Live candidate:
`Fiji_v2/Phase1D_Legacy_Removal`.

- Cleanup validator: 11/11 passed.
- Original Phase 1D validator: 15/15 passed on disposable and live cases.
- GLPK matrix: 160,383 rows, 126,737 columns, 937,818 nonzeros.
- Matrix reduction from the control: 777 rows, 621 columns and 7,151
  nonzeros.
- CBC: Optimal at `-1548.8662358`; live wall time about 1.05 seconds.
- Objective difference from the removal control: exactly zero.
- Capacity, new capacity, emissions, demands and Phase 1D chain activity:
  unchanged.
- Reserve proxy: `CURRENT`, zero mismatches.
- Historical-fit metrics: unchanged.
- General Fiji validator: 14/15; the pre-existing 2024 thermal-generation
  error remains `20.647%` against the `20%` single-outcome threshold.

## Alternate optimum and limitations

The smaller/reordered matrix selects another point on an existing
cost-equivalent feasible face:

- 44 mode-level rows move only within three land technologies, the
  hydro/solar/wind group and their renewable-accounting mirrors;
- land technology-year activity and aggregate renewable power service remain
  unchanged within `1e-6`;
- six nonbinding 2044/2050 water-surplus balance activities change;
- 371 discounted annual-balance shadow prices change; and
- all annual commodity balances remain feasible, with Phase 1D balance
  differences below `3.12e-12`.

The cleanup validator records these differences rather than claiming
row-for-row solver identity. Shadow prices from this degenerate solution
should not be used for policy interpretation without a stability analysis.

## Portable package

`muio/Fiji_v2_v2.0.5_MUIO.zip` is result-free and contains 133 technologies
and 106 commodities. It excludes `res/` and regenerated view caches,
preserves only `view/viewDefinitions.json`, and contains no legacy name or
ID.

SHA-256:
`d818202c10c9dc3eb7b1d827b2afb827b2e87abdca40abc86e43978e1476724c`.
