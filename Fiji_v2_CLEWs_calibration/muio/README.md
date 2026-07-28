# Fiji v2 MUIO package

- Current portable case: `Fiji_v2_v2.0.4_MUIO.zip`
- SHA-256:
  `cb835f3a70269b072d7dfbd8810f9f3dcdd605f301ca8c21589153351a739ddb`
- Exported: 28 July 2026
- Source case: `WebAPP/DataStorage/Fiji_v2`
- Active-input status: Phase 1D cane–bagasse–electricity closure
- Solver results: excluded

The v2.0.4 archive retains the post-OHC correction, Phase 1B public-water
closure and Phase 1C sector electricity demand. It contains the editable
Phase 1D MUIO parameter JSON and view metadata, including FSC cane throughput,
the explicit mill and exportable-bagasse chain, separate bagasse and
wood-residue generation, and the refreshed reserve proxy. It excludes the
`res/` folder and generated solver inputs, LP and results. The 28 July 2026
`Phase1D_Cane_Bagasse` run uses these inputs and solves Optimal.

The earlier v2.0.0 through v2.0.3 archives remain available for comparison.

Recreate it with:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
  WebAPP/DataStorage/Fiji_v2 \
  Fiji_v2_CLEWs_calibration/muio/Fiji_v2_v2.0.4_MUIO.zip \
  --exclude-results
```
