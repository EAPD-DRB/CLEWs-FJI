# Fiji v2.0.1 Phase 1A topology audit — 27 July 2026

## Scope

Phase 1A implements the handoff's non-mutating commodity-topology audit. It
reads the authoritative CSV inputs in `model/inputs`, confirms their
technology and commodity sets against the active MUIO `genData.json`, and
adds 2020–2024 activity from the recertified `Historical_Backcast`.

The implementation is:

- `scripts/audit_fiji_topology.py`
- `diagnostics/topology/2026-07-27_phase1a/commodity_ledger.csv`
- `diagnostics/topology/2026-07-27_phase1a/warnings.csv`
- `diagnostics/topology/2026-07-27_phase1a/audit.json`
- `diagnostics/topology/2026-07-27_phase1a/REPORT.md`

The script never deletes, rewires, or edits a model entity. It hashes every
active root/view MUIO JSON and every input CSV before and after the audit and
stops if any hash changes. Default mode succeeds with classified warnings;
`--strict` returns exit code 2 when warnings exist.

## Results

The audit reconciled all 103 commodities and 130 technologies between the
source CSVs and the active MUIO case.

| Result | Count |
|---|---:|
| Connected commodities | 71 |
| Produced, unconsumed and undemanded commodities | 32 |
| Consumed but unproduced | 0 |
| Positive demand without supply | 0 |
| Disconnected | 0 |
| Warning records | 37 |
| Commodities with warnings | 33 |

The four renewable resource carriers each receive both the generic
produced/unconsumed warning and the more specific output-only-resource
warning. This accounts for the difference between 37 warning records and 33
warned commodities.

The 32 produced/unconsumed commodities reproduce the handoff inventory:

- 25 sector/fuel end-use carrier outputs;
- `GEO`, `HYD`, `SOL`, and `WND`;
- `PUBWATFJI`;
- `WTREVTFJI` and `WTRGRCFJI`.

All 25 end-use carrier output stubs had zero production and zero linked
technology activity in 2020–2024. This confirms that the saved solve does not
use them, but it does not make their missing service layer acceptable for
future policy analysis.

The physical water outputs are different. In the saved 2020–2024 result,
`WTRGRCFJI` has 5.3834 units of production and `WTREVTFJI` has 160.7431
units of production. `WTRSURFJI` has 66.9383 units and is topologically
connected. These totals use the commodities' declared model units and are
reported only as topology/activity evidence; Phase 1A does not validate the
physical calibration or interpretation of those values.

## Structural findings

1. `COMELCFJIXX02 -> DEMPUBGWTFJI -> PUBWATFJI` is the one detected
   cross-sector consumer. The public groundwater technology consumes
   commercial-service electricity at 0.0173 and consumes no groundwater
   commodity.
2. `AGRELCFJIXX02 -> DEMAGRGWTFJI -> AGRWATFJI` has the same
   electricity-only groundwater pattern. It does not trigger the
   cross-sector rule because both names are agricultural, but it must be
   handled when agricultural water is reviewed.
3. `PUBWATFJI` has two producers but no demand, so both public-water paths
   remain inactive.
4. `WTRGRCFJI` is produced by active land technologies but has no consumer.
   It must first be classified as recharge, extractable groundwater, or an
   intermediate. Adding final demand to it would erase a warning without
   repairing the physical model.
5. `GEO`, `HYD`, `SOL`, and `WND` are resource carriers. Their output-only
   state should be addressed through availability or potential constraints,
   not final demand.

## Validation and audit trail

- Default audit: passed with classified warnings.
- Strict audit: expected failure, exit code 2, because warnings remain.
- Input mutation guard: passed; all source hashes were identical before and
  after the audit.
- Existing Fiji technical validator: passed all 15 checks after the audit.
- Active `genData.json` SHA-256:
  `6a585ab82bc8064f4df87ad37a96deeec2f53c024673d62da0a717497d4a09be`.
- Saved `results.txt` SHA-256:
  `f403f1d4a95a4080ce6578559b8ffb30373b003ac5b33e727464212265a711f4`.
- Baseline: the Phase 0 recertified post-OHC `Historical_Backcast`, Optimal,
  objective `-1387.57013590`.

Generation, preprocessing, `glpsol --check`, CBC optimization and a new
baseline comparison were not rerun because Phase 1A changes no model source
or generated solver artifact. The technical validator rechecked the existing
generated artifacts, solve identity, objective, reserve proxy, input indices,
locks, dimensions, held-out metrics and timestamps. The prior Phase 0
certificate remains the solve baseline; this record does not claim a new
optimization or full nexus validation.

## Phase 1B gate

Phase 1B must begin with an evidence/design record, not a parameter edit. The
record must settle:

1. the physical meaning, boundary and unit of `WTRGRCFJI`;
2. whether a separate groundwater stock, availability or abstraction
   commodity is needed;
3. the raw-water and electricity inputs of public surface-water and
   groundwater supply;
4. the 2020–2024 `PUBWATFJI` observation boundary and conversion into model
   units.

Only after those four items are documented should the public-water topology
or demand be changed.
