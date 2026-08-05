# Fiji SSP2-4.5 precipitation pathway

The model retains its full-precision 2020 precipitation Input Activity Ratio (IAR) of 2.5499318663156916 km3 per 1000 km2. The World Bank Climate Change Knowledge Portal (CCKP) CMIP6 Fiji ensemble provides a 1995-2014 historical annual precipitation climatology median of 2274.78 mm/year and SSP2-4.5 median anomalies of -39.88 mm/year for 2020-2039 and -37.53 mm/year for 2040-2059. SSP2-4.5 is used as the RCP4.5-equivalent forcing pathway.

The period midpoints are mapped to 2030 and 2050. The implemented anchors are `1 + anomaly / 2274.78`: 0.9824686343294736 in 2030 and 0.9835017012634188 in 2050. Annual multipliers are linearly interpolated from 2020=1.0 to 2030 and then to 2050. On 18.2729 thousand km2 of land, modeled precipitation is therefore 46.59465 km3 in 2020, 45.77778215255981 km3 in 2030 and 45.82591754477356 km3 in 2050.

For every one-mode national land technology, `RYTCM.json` multiplies the WTRPRCFJI IAR and the WTREVTFJI, WTRGRCFJI and WTRSURFJI Output Activity Ratios (OARs) by the same annual factor. This preserves the inherited evapotranspiration/recharge/runoff partition. `RYTCn.json` then rebuilds the ENV_WATER_CLOSURE User-Defined Constraint (UDC) activity multipliers from the effective annual net water OAR-minus-IAR values.

The annual interpolation and proportional hydrology response are explicit assumptions. CCKP p10 and p90 anomalies are retained in `scripts/data/fiji_v26_precipitation_ssp245.json` for later sensitivity cases; they are not used in the central SC_0 run. The exact transformation, source fingerprints and equation mapping are in `precipitation_ssp245_manifest.json`; validation is in `validation_ssp245_disposable.json` and `validation_ssp245_live.json`.
