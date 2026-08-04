# CLEWs Fiji

This repository contains the Fiji CLEWs country models for MUIO/MUIOGO,
including model documentation, change history, source registers, assumptions,
calculations, diagnostics, and portable MUIO cases.

## Current recommended model

The current `main`-branch package is **Fiji v2.9.0**:

- model package: `Fiji_v2.9_CLEWs_build/`;
- MUIO case: `Fiji_v2.9`;
- portable archive:
  `Fiji_v2.9_CLEWs_build/muio/Fiji_v2.9_v2.9.0_MUIO.zip`;
- validated live run: `Fisheries_Bounds_Table18_v2.9`;
- scope: the earlier energy, water, land and crop improvements plus explicit
  Fisheries services, population-driven crop/fish demand and trade, and
  aggregate capture/aquaculture production ceilings.

The Fisheries ceilings are deliberately simple. Capture is limited to the
documented 23,661 tonne/year 2020 boundary; aquaculture follows the detailed
2024–2028 national programme envelope and is held at 1,450 tonne/year
thereafter. Neither route has a production floor, and fish imports remain open.
The limits therefore prevent an unlimited least-cost switch to one domestic
subsector without pretending to be biological stock, quota, feed, site or
wastewater models.

The earlier Fiji v2.0.5 package remains under
`Fiji_v2_CLEWs_calibration/`, and the tagged
[v2.0.0](https://github.com/EAPD-DRB/CLEWs-FJI/releases/tag/v2.0.0)
release remains immutable.

Read `Fiji_v2.9_CLEWs_build/documentation/CURRENT_MODEL.md` and
`Fiji_v2.9_CLEWs_build/documentation/KNOWN_LIMITATIONS.md` before using the
model.

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

The model folders preserve the working-package structure:

- `Fiji_CLEWs_Global/`: immutable raw reference;
- `Fiji_v2_CLEWs_calibration/`: earlier Fiji v2.0.5 package;
- `Fiji_v2.9_CLEWs_build/`: current recommended Fiji v2.9.0 package.

Within each package, `config/`, `data_sources/`, `documentation/`,
`diagnostics/`, `geospatial/`, `licenses/`, `model/`, `muio/`, `overrides/`,
`patches/`, and `scripts/` retain their existing roles.

Original external publications and generated MUIO runtime outputs are not
distributed in this repository. Compact raw-reference solve evidence used by
the documented validation record is retained under `model/`.
