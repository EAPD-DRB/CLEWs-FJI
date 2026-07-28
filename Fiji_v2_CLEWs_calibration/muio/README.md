# Fiji v2 MUIO package

- Current portable case: `Fiji_v2_v2.0.5_MUIO.zip`
- SHA-256:
  `d818202c10c9dc3eb7b1d827b2afb827b2e87abdca40abc86e43978e1476724c`
- Exported: 28 July 2026
- Source case: `WebAPP/DataStorage/Fiji_v2`
- Active-input status: Phase 1D cane–bagasse–electricity closure
- Solver results: excluded

The v2.0.5 archive retains the post-OHC correction, Phase 1B public-water
closure and Phase 1C sector electricity demand. It contains the editable
Phase 1D MUIO parameter JSON and view metadata, including FSC cane throughput,
the explicit mill and exportable-bagasse chain, separate bagasse and
wood-residue generation, and the refreshed reserve proxy. The superseded
aggregate biomass shell is absent. It excludes `res/` and regenerated view
caches, retaining only `viewDefinitions.json`; generated solver inputs, LP
and results are not packaged. The 28 July 2026
`Phase1D_Legacy_Removal` run uses these inputs and solves Optimal.

The earlier v2.0.0 through v2.0.4 archives remain available for comparison
and preserve the retired aggregate identifier's history.

Recreate it with:

```bash
/opt/anaconda3/bin/python \
  Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
  WebAPP/DataStorage/Fiji_v2 \
  Fiji_v2_CLEWs_calibration/muio/Fiji_v2_v2.0.5_MUIO.zip \
  --exclude-results
```
