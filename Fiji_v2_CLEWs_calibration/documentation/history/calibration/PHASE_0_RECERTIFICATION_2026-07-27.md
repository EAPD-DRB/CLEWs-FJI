# Fiji v2.0.1 Phase 0 recertification — 27 July 2026

## Scope

This record closes Phase 0 from `HANDOFF-2026-07-26.md`. It recertifies the
existing annual `Historical_Backcast` against the already published v2.0.1
inputs after removal of the dormant `OHC -> DEMINDOHC -> INDOHC` branch. It
does not change a model parameter or extend the calibration claim.

The active inputs came from CLEWs-FJI commit
`195c8fb40022565adb024dcec55a71f48b6e5b3e`. The MUIO case contains 130
technologies, 103 commodities, 31 years and four time slices. Its
`genData.json` SHA-256 is
`6a585ab82bc8064f4df87ad37a96deeec2f53c024673d62da0a717497d4a09be`.

## Generation and solve

MUIOGO regenerated `data.txt`, preprocessed it, created `lp.lp` through the
normal `glpsol --check` matrix path, solved the LP with CBC, and regenerated
the result CSV and Pivot files. The saved run is newer than every active
top-level parameter JSON.

| Artifact | SHA-256 |
|---|---|
| `data.txt` | `14b40ab8eed9f3e2b7c54946b6b9c55ae6845bab7bb1a8a6b5a0fd7be71e9dd9` |
| `data_processed.txt` | `21bc0d40dad7a32d00b9277917743149d0c8ea1ab46968c24fa2ad2dc9cec94f` |
| `lp.lp` | `97c3873d7845b631c73510854bda4b20d080408c463aba46c6d66e168d874dd7` |
| `results.txt` | `f403f1d4a95a4080ce6578559b8ffb30373b003ac5b33e727464212265a711f4` |
| `ObjectiveValue.csv` | `92b5a143658b2723700568292ac7a550ff5993a2f8acad1a4aba71240b17d5a9` |

CBC status is `Optimal` and the objective is `-1387.57013590`.

## Validation and comparison

The refreshed validator passes 15 of 15 checks:

- the post-OHC dimensions are 130 technologies and 103 commodities;
- no active CSV, parameter JSON or regenerated solver file contains `OHC`,
  `DEMINDOHC` or `INDOHC`;
- the valid `FJIXX` generation-transmission-demand chain remains connected;
- the reserve-margin proxy is `CURRENT` with zero mismatches;
- input indices are unique;
- there are no positive lower-equals-upper historical outcome locks;
- registered evidence hashes and the calibration/validation split are
  preserved; and
- the regenerated solve and held-out fit pass their declared thresholds.

The recalculated score is unchanged:

| Metric | Before OHC prune | Post-OHC rerun | Change |
|---|---:|---:|---:|
| Weighted score | 76.4 | 76.4 | 0 |
| Held-out material generation MAPE | 9.9388% | 9.9388% | 0 |
| Held-out renewable-share MAE | 5.1328 percentage points | 5.1328 percentage points | 0 |
| Worst material held-out miss | 19.374% | 19.374% | 0 |

The refreshed structural inventory still flags generic commodity descriptions
and zero-valued exact bound pairs. These are pre-existing metadata and
screening findings. The dedicated forcing audit confirms that no positive
historical outcome is fixed by equal lower and upper bounds.

## Artifact note

The MUIOGO batch action also regenerated `Raw` and `Raw_ReserveProxy` using
the current active Fiji v2 inputs. Their solver inputs and results are
byte-identical to `Historical_Backcast`; they are labels of the current solve,
not recoverable raw-reference baselines. Historical raw comparison evidence
in the dated raw-build records is retained, but these two regenerated folders
must not be used as raw controls.

The active inputs did not change during recertification. The result-free
`Fiji_v2_v2.0.1_MUIO.zip` therefore remains valid with SHA-256
`6186c3ee14559fc4f8c07242859b91717242e8662353d8adb90cf80256fde6d1`.

## Outcome

Phase 0 is complete for the stated annual national grid-supply calibration
scope. Phase 1 may begin with the non-mutating topology audit in Phase 1A.
