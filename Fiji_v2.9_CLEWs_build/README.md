# Fiji v2.9.0 CLEWs build

This is the current source, provenance and validation package for the MUIO
case `Fiji_v2.9`, derived through solved Fiji v2.7 and v2.8.

Start with `data_sources/DATA_SOURCES.md`. The ledgers now document the source
chain from the pinned raw CLEWs/GAEZ country build through Fiji v2, public
water, sectoral electricity demand, cane/bagasse, v2.4 and v2.5, as well as the
complete population-driven crop and fish layers through v2.9. Exact retained
archives, raw tables and reconstructed source selections are under
`data_sources/evidence/`. Full annual and HS-level values are retained in the
calculation ledger and `data_sources/snapshots/`.

The simple Fisheries constraint uses `RYT.json/TAU` and the active
`AAC2_TotalAnnualTechnologyActivityUpperLimit` equation. Capture is limited to
0.023661 Mt/year in 2020–2050. Aquaculture is limited to 0.000216925 Mt/year
through 2023, then 0.000350, 0.000530, 0.000800, 0.001180 and 0.001450 Mt/year
in 2024–2028, holding the last value through 2050. `TAL` remains zero for both
routes and the fish import backstop remains open.

The final live run `Fisheries_Bounds_Table18_v2.9` solved optimally at CBC
objective 4182.52681513. In 2025 it supplies 0.023661 Mt capture,
0.000530 Mt aquaculture and 0.0075338982 Mt imports against
0.0317248982 Mt final fish demand. Validation reports are under `validation/`.

The result is suitable for national screening of a plausible aggregate
capture/aquaculture mix. It is not a stock assessment, legal quota, feed
balance, site/facility expansion model, wastewater assessment, nutrition model
or behavioral trade forecast.
