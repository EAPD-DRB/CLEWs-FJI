# Fiji v3 canonical migration

Fiji v3.0.0 was created on 5 August 2026 from the preserved Fiji v2.9.0
package and portable case at Git tag `v2.9.0`.

The migration changes only:

- package and portable-archive identity;
- `osy-casename` from `Fiji_v2.9` to `Fiji_v3`;
- the case description;
- `view/resData.json`, reset to an empty result registry; and
- documentation for the ZIP/push and pull/unzip workflow.

All editable model parameter JSON files are byte-identical to the v2.9.0
portable case. Solver results are excluded. The inherited ledgers and retained
evidence are complete inside this package and do not require the earlier
package to be interpreted.
