# Fiji v2 MUIO package

- Current portable case: `Fiji_v2_v2.0.2_MUIO.zip`
- SHA-256:
  `62ef6b2b3ec683a0f0ae7d50eca9435c7214892186f75d87acb8358123262053`
- Exported: 27 July 2026
- Source case: `WebAPP/DataStorage/Fiji_v2`
- Active-input status: Phase 1B public-water closure
- Solver results: excluded

The v2.0.2 archive retains the post-OHC correction and contains the editable
Phase 1B MUIO parameter JSON and view metadata. It adds the public-water
demand and surface abstraction/loss accounting, the explicit groundwater
abstraction layer, and the quarantined public-groundwater route. It excludes
the `res/` folder and generated `lp.lp`; both are regenerated when the case is
solved. The 27 July 2026 `Phase1B_Public_Water` run uses these inputs, solves
Optimal and preserves the held-out annual energy fit.

The earlier `Fiji_v2_v2.0.0_MUIO.zip` and
`Fiji_v2_v2.0.1_MUIO.zip` archives remain available for comparison.

Recreate it with:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
  WebAPP/DataStorage/Fiji_v2 \
  Fiji_v2_CLEWs_calibration/muio/Fiji_v2_v2.0.2_MUIO.zip \
  --exclude-results
```
