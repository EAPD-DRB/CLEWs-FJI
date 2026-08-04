# Reproduce Fiji v2.8 and v2.9

From the repository root, using MUIOGO's existing virtual environment:

```sh
.venv/bin/python scripts/create_fiji_v28_population_crop_trade.py --target-name .Fiji_v2.8-reproduction
.venv/bin/python scripts/validate_fiji_v28_population_crop_trade.py --candidate WebAPP/DataStorage/.Fiji_v2.8-reproduction
.venv/bin/python scripts/run_fiji_v28_population_crop_trade.py solve --case .Fiji_v2.8-reproduction

.venv/bin/python scripts/create_fiji_v29_population_fisheries_trade.py --target-name .Fiji_v2.9-reproduction
.venv/bin/python scripts/validate_fiji_v29_population_fisheries_trade.py --candidate WebAPP/DataStorage/.Fiji_v2.9-reproduction
.venv/bin/python scripts/run_fiji_v29_population_fisheries_trade.py solve --case .Fiji_v2.9-reproduction
```

Both generators use `UpdateCase` for structural additions and then write only
source parameter JSON. Solver inputs are produced through
`DataFile.generateDatafile()` and `.preprocessData()`.

Validate this schema-ledger package with:

```sh
.venv/bin/python docs/Fiji_v2.9_Population_Crop_Fisheries_Trade/scripts/validate_provenance.py \
  docs/Fiji_v2.9_Population_Crop_Fisheries_Trade --stage build
.venv/bin/python docs/Fiji_v2.9_Population_Crop_Fisheries_Trade/scripts/validate_fiji_v29_schema_ledger.py
```

The documented GLPK check for v2.9 is:

```sh
/opt/homebrew/bin/glpsol --check \
  -m WebAPP/SOLVERs/model.v.5.4.txt \
  -d WebAPP/DataStorage/Fiji_v2.9/res/Population_Fisheries_Trade_v2.9/data_processed.txt \
  --wlp /tmp/fiji_v29_check.lp
```

The validated installation used GLPK 5.0 and CBC 2.10.13.
