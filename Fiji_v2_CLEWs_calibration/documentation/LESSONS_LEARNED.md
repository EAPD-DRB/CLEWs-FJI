# Fiji v2 lessons learned

This is the short reusable-process ledger. Case-specific facts remain in
`../MODEL_FIXES_2026-07-27.md` and dated history records. A lesson belongs
here only when it changes a future check or workflow. Once it proves useful
across models, promote the rule to `CALIBRATION_PROTOCOL.md` or a shared
Model-tools skill.

Each entry records: signal, cause, evidence, adopted guardrail and reuse
scope.

## LL-2026-07-28-01 — zero-variable removal can select another optimum

- Signal: deleting the zero-capacity `PWRBIOFJIXX01` shell changed 44
  mode-level activity rows and 371 discounted annual-balance shadow prices.
- Cause: the old and cleaned matrices have the same relevant feasible
  projection but multiple cost-equivalent allocations. MUIO also emits
  derived mode/fuel sets from unordered collections, so harmless ordering
  changes can alter which optimum CBC returns.
- Evidence: objective, capacities, new capacity, emissions, demands, Phase
  1D flows and aggregate power service are unchanged. Six nonbinding
  water-surplus primal rows change; all balances remain feasible. The
  maximum Phase 1D balance difference is `3.12e-12`.
- Guardrail: compare physical invariants and aggregate services before
  requiring rowwise solution identity. Record mode and dual changes
  explicitly. Never interpret a shadow price without an alternate-optimum
  stability check.
- Reuse: all structural deletions, reindexing and solver/export-order changes.

## LL-2026-07-28-02 — preserve the source side of a baseline

- Signal: after live promotion, the Phase 1D validator could still read the
  old Phase 1C result but could no longer resolve its deleted technology in
  the now-current source.
- Cause: a result directory alone is not a complete baseline identity.
- Guardrail: before structural promotion, retain or name an immutable
  baseline case containing both source parameters and result artifacts.
  Live recertification now uses
  `Fiji_v2_Phase1C_BottomUp_Test/Phase1C_BottomUp`.
- Reuse: every structural phase and every validator that maps result IDs
  through source metadata.

## LL-2026-07-28-03 — view caches are results, not portable source

- Signal: live `view/*.json` caches retained historical references to the
  deleted technology although active root JSON and the new solve did not.
- Cause: MUIO view files aggregate display data from stored runs and are
  regenerated from results.
- Guardrail: result-free exports exclude `res/` and regenerated `view/`
  caches, preserving only `view/viewDefinitions.json`.
- Reuse: push/handoff packages and release archives.
