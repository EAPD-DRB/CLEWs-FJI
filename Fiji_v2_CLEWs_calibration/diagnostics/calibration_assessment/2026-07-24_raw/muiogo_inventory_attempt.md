# MUIOGO inventory attempt

The skill's `audit_muiogo_model.py` command was run against
`Fiji_CLEWs_Global` on 2026-07-24. It returned:

> ERROR: genData.json not found in Fiji_CLEWs_Global

This is a format limitation, not a failed model-integrity finding. The Fiji
package is a CLEWs Global/OSeMOSYS CSV bundle rather than a MUIOGO
`WebAPP/DataStorage` JSON model. Native structural evidence is therefore taken
from `diagnostics/technical_qa.csv`, `diagnostics/no_forcing_audit.json`, the
input/result CSVs, and the pinned-source reconstruction files.
