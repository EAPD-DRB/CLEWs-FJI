# CLEWs Fiji

This repository contains the Fiji CLEWs country models for MUIO/MUIOGO,
including model documentation, change history, source registers, assumptions,
calculations, diagnostics, and portable MUIO cases.

## Current recommended model

The current recommended release is **Fiji v2.0.0**:

- model package: `Fiji_v2_CLEWs_calibration/`;
- MUIO case: `Fiji_v2`;
- calibration scope: annual national grid-supply energy.

Download the release from
[v2.0.0](https://github.com/EAPD-DRB/CLEWs-FJI/releases/tag/v2.0.0).
The same portable archive is tracked under
`Fiji_v2_CLEWs_calibration/muio/`.

Fiji v2 is not a calibration of the full land-water-agriculture nexus,
investment economics, island networks, or operational reliability. Read
`Fiji_v2_CLEWs_calibration/documentation/CURRENT_MODEL.md` and
`Fiji_v2_CLEWs_calibration/documentation/KNOWN_LIMITATIONS.md` before using
the model.

## Raw reference model

`Fiji_CLEWs_Global/` is the immutable, technically solved, uncalibrated raw
reference from which Fiji v2 was developed. It is retained under the
[raw-v1.0.0](https://github.com/EAPD-DRB/CLEWs-FJI/releases/tag/raw-v1.0.0)
release and is not the recommended policy model.

## Use with MUIOGO

1. Install or clone [MUIOGO](https://github.com/EAPD-DRB/MUIOGO).
2. Extract the required archive from the appropriate package's `muio/`
   folder.
3. Place the extracted case folder under `MUIOGO/WebAPP/DataStorage/`.
4. Start MUIOGO and open the case.

The archives contain the editable MUIO parameter JSON and view files. Solver
outputs are intentionally excluded and are regenerated when the model is
solved.

## Repository structure

The two model folders preserve the existing working-package structure:

- `Fiji_CLEWs_Global/`: immutable raw reference;
- `Fiji_v2_CLEWs_calibration/`: current calibrated model.

Within each package, `config/`, `data_sources/`, `documentation/`,
`diagnostics/`, `geospatial/`, `licenses/`, `model/`, `muio/`, `overrides/`,
`patches/`, and `scripts/` retain their existing roles.

Original external publications and generated MUIO runtime outputs are not
distributed in this repository. Compact raw-reference solve evidence used by
the documented validation record is retained under `model/`.
