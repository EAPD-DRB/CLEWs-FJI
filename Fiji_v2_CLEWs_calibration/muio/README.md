# Fiji v2 MUIO package

- Current portable case: `Fiji_v2_v2.0.3_MUIO.zip`
- SHA-256:
  `da1b1e078bb223636a33c50ba55b5cf63ec28d2b34705e4c67c4b252e1588c9d`
- Exported: 27 July 2026
- Source case: `WebAPP/DataStorage/Fiji_v2`
- Active-input status: Phase 1C sector electricity and bottom-up demand
- Solver results: excluded

The v2.0.3 archive retains the post-OHC correction and Phase 1B public-water
closure. It contains the editable Phase 1C MUIO parameter JSON and view
metadata, including observed 2020–2024 sector electricity accounting,
independent 2025–2050 commercial, industrial and central-grid residential
demand, and the aggregate reserve proxy. It excludes the `res/` folder and
generated solver inputs, LP and results. The 27 July 2026
`Phase1C_BottomUp` run uses these inputs, solves Optimal and preserves the
held-out annual energy fit.

The earlier v2.0.0, v2.0.1 and v2.0.2 archives remain available for
comparison.

Recreate it with:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
  WebAPP/DataStorage/Fiji_v2 \
  Fiji_v2_CLEWs_calibration/muio/Fiji_v2_v2.0.3_MUIO.zip \
  --exclude-results
```
