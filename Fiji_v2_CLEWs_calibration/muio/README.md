# Fiji v2 MUIO package

- Current portable case: `Fiji_v2_v2.0.1_MUIO.zip`
- SHA-256:
  `6186c3ee14559fc4f8c07242859b91717242e8662353d8adb90cf80256fde6d1`
- Exported: 26 July 2026
- Source case: `WebAPP/DataStorage/Fiji_v2`
- Active-input status: post-OHC correction
- Solver results: excluded

The v2.0.1 archive contains the editable MUIO parameter JSON and view
metadata after removal of `OHC`, `DEMINDOHC`, and `INDOHC`. It excludes the
`res/` folder and generated `lp.lp`; both are regenerated when the case is
solved. The most recent stored `Historical_Backcast` and calibration
diagnostics predate the OHC-only prune and are not represented as recertified
v2.0.1 results.

The immutable repository archive `Fiji_v2_v2.0.0_MUIO.zip` remains the tagged
v2.0.0 package.

Recreate it with:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
  WebAPP/DataStorage/Fiji_v2 \
  Fiji_v2_CLEWs_calibration/muio/Fiji_v2_v2.0.1_MUIO.zip \
  --exclude-results
```
