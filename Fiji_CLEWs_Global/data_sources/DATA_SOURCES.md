# Fiji CLEWs Global data sources

This is the current consolidated source register. It distinguishes external
observations from modeller assumptions and calculations so that a publication
is never confused with a modelling choice.

## How to use this register

1. Find the model object in `MODEL_DATA_MAP.csv`.
2. Follow its `source_ids`, `assumption_ids`, and `calculation_ids`.
3. Use this file for source identity, `ASSUMPTIONS.csv` for choices, and
   `CALCULATIONS.csv` or `calculation_notes/` for transformations.
4. Check the `Role` column before claiming that an observation affects the
   active model.
5. If an entry says “documentation gap,” do not claim a more precise origin
   until supporting evidence is recovered.

## Active raw-model lineage

| Source ID | Provider and dataset | Model use | Role | Location or entry point |
|---|---|---|---|---|
| `DS-CLEWS-GLOBAL` | CLEWs Global workflow, pinned revision | Country workflow, integration, parameter generation, and raw model structure | Active input | `config/upstream_versions.json`; https://github.com/DeltaE/CLEWs_Global |
| `DS-OSEMOSYS-GLOBAL` | OSeMOSYS Global, pinned submodule revision | Energy technologies, fuels, demand paths, costs, efficiencies, capacities, and other global defaults | Active input; country-specific row lineage is incomplete | `config/upstream_versions.json`; https://github.com/ClimateCompatibleGrowth/osemosys_global |
| `DS-CLEWS-GAEZ` | CLEWs GAEZ, pinned submodule revision | Land-cell processing, crop potential, water coefficients, and spatial clusters | Active input | `config/upstream_versions.json`; https://github.com/ClimateCompatibleGrowth/CLEWs_GAEZ |
| `DS-CLEWSY` | clewsy, pinned submodule revision | Builds OSeMOSYS/CLEWs parameter tables | Active input | `config/upstream_versions.json`; https://github.com/ClimateCompatibleGrowth/clewsy |
| `DS-GADM-4.1` | GADM version 4.1 Fiji national boundary | National boundary and land-cell clipping | Active input | `geospatial/`; https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_FJI_shp.zip |
| `DS-GAEZ-V4-YIELD` | FAO Global Agro-Ecological Zones v4 | Irrigated/rain-fed and high/low-input crop potential yields | Active input | https://gaez.fao.org/ |
| `DS-GAEZ-V4-WATER` | FAO Global Agro-Ecological Zones v4 | Precipitation, evapotranspiration, runoff, and crop-water coefficients | Active input | https://gaez.fao.org/ |
| `DS-GAEZ-V4-LANDCOVER` | FAO Global Agro-Ecological Zones v4 land-cover raster | Cluster land-cover shares | Active input | `geospatial/summary_stats/`; https://gaez.fao.org/ |
| `DS-FAOSTAT-2020-CROPS` | FAOSTAT Crops and livestock products | Crop selection and 2020 output-demand anchors bundled by the upstream workflow | Active input and diagnostic evidence | https://www.fao.org/faostat/en/#data/QCL |
| `DS-SSP2-POP` | IIASA-WiC SSP2 population series bundled by OSeMOSYS Global | Population-only growth of crop-output demand | Active input | Upstream model resources; exact bundled-file locator remains to be recorded |
| `DS-FJI-LAND-AREA` | Government of Fiji project documentation | Normalization of the modeled land domain to 18,273 km² | Active structural input | https://fiji.gov.fj/getattachment/2e544cd4-06c7-45c8-b773-8dcf3e06249c/Fiji-Northern-Connectivity-ESMP.aspx |
| `DS-MUIO-5.4` | MUIO v5.4 formulation and importer | Active JSON formulation, import interpretation, and solved MUIO case | Active implementation evidence | `WebAPP/DataStorage/Fiji_CLEWs_Global`; repository solver and importer files |
| `DS-RAW-SOLUTION` | Generated raw CBC and MUIO solutions | Baseline behavior, technical validation, and later before/after comparison | Active model evidence | `model/results/`, `model/data.sol`, `muio/`, and `diagnostics/` |

The generated energy inputs contain many country and technology values inherited
from the upstream global databases. Their complete original row-level source
and transformation lineage has not yet been reconstructed. Those values must
not be described as fully Fiji-sourced merely because they are present in the
country model.

## Electricity observations reserved for calibration and validation

| Source ID | Provider and publication | Intended use | Role | Location or entry point |
|---|---|---|---|---|
| `DS-FJI-REI-IP` | Government of Fiji, *Renewable Energy Integration Investment Plan* | 2021 capacity, generation, and policy context | Diagnostic only in the raw case; calibration candidate | https://mecc.gov.fj/wp-content/uploads/2025/12/Fiji_CIF_REI_IP_12234.pdf |
| `DS-FBS-ELECTRICITY-2024` | Fiji Bureau of Statistics, *Fiji Electricity 2024* | Independent electricity accounting cross-check | Calibration and validation candidate | https://www.statsfiji.gov.fj/electricity-2024/ |
| `DS-EFL-AR-2020` | Energy Fiji Limited, *2020 Annual Report* | Plant/category generation, demand, losses, fuel, costs, and operating events | Calibration candidate | https://efl.com.fj/wp-content/uploads/2021/07/2020-EFL-Annual-Report.pdf |
| `DS-EFL-AR-2021` | Energy Fiji Limited, *2021 Annual Report* | Plant/category generation, demand, losses, fuel, costs, and operating events | Calibration candidate | https://efl.com.fj/wp-content/uploads/2022/08/EFL-2021-Annual-Report-website_cmpress.pdf |
| `DS-EFL-AR-2022` | Energy Fiji Limited, *2022 Annual Report* | Plant/category generation, demand, losses, fuel, costs, and operating events | Calibration candidate | https://efl.com.fj/wp-content/uploads/2022/08/EFL-2022-Annual-Report.pdf |
| `DS-EFL-AR-2023` | Energy Fiji Limited, *2023 Annual Report* | Plant/category generation, demand, losses, fuel, costs, rainfall, outages, and Aggreko hire | Calibration candidate | https://efl.com.fj/wp-content/uploads/2024/07/EFL-2023-Annual-Report.pdf |
| `DS-EFL-AR-2024` | Energy Fiji Limited, *2024 Annual Report* | Plant/category generation, demand, losses, fuel, costs, rainfall, outages, and new solar/BESS | Calibration and held-out validation candidate | https://efl.com.fj/wp-content/uploads/2025/05/EFL-2024-Annual-Report.pdf |
| `DS-FBS-ENERGY-ACCOUNT-2024` | Fiji Bureau of Statistics, *Experimental Environmental Account for Energy 2024* | Reconcile EFL, household, and off-grid generation boundaries | Calibration-accounting candidate | https://www.statsfiji.gov.fj/fijis-experimental-environmental-account-for-energy-2024/ |
| `DS-FIJI-NEP-2023` | Government of Fiji, *National Energy Policy 2023–2030* | Policy definitions and later scenario design | Scenario context only; not active in raw model | https://www.mims.gov.fj/wp-content/uploads/2025/05/National-Energy-Policy-2023-2030.pdf |
| `DS-FIJI-NDC` | Government of Fiji revised/updated NDC, indexed by IEA | Renewable and emissions target context | Scenario context only; not active in raw model | https://www.iea.org/policies/11838-revisedupdated-ndc-of-fiji |

The EFL reports provide overlapping ten-year tables, which permit
cross-vintage checks instead of relying on one report. Some 2024 headline and
detailed totals appear to use different accounting boundaries. That conflict
must be reconciled with the Fiji Bureau of Statistics energy account before
any target value is entered in the calibration evidence table.

## Climate, water, agriculture, and biomass candidates

| Source ID | Provider and dataset | Intended use | Role | Location or entry point |
|---|---|---|---|---|
| `DS-FMS-ANNUAL-CLIMATE` | Fiji Meteorological and Hydrological Service annual climate summaries | Annual and station rainfall, climate-event interpretation, and hydro-driver checks | Calibration candidate | https://www.met.gov.fj/climate-services/annual-climate-summary/ |
| `DS-FMS-MONASAVU` | Fiji Meteorological and Hydrological Service Monasavu outlook archive | Monthly Monasavu rainfall reconstruction | Calibration candidate; not a substitute for reservoir inflows | https://adila.met.gov.fj/climate-services/monasavu-outlooks/ |
| `DS-FBS-WATER-2024` | Fiji Bureau of Statistics, *Experimental Environmental Account for Water 2024* | Annual 2020–2024 surface water, groundwater, and rainwater extraction | Calibration candidate for aggregate water accounts | https://www.statsfiji.gov.fj/fijis-experimental-environmental-account-for-water-2024/ |
| `DS-FSC-ANNUAL-REPORTS` | Fiji Sugar Corporation annual reports | Cane crushed, sugar output, mill operations, and bagasse-resource checks | Calibration candidate | https://fsc.com.fj/annualreports/ |
| `DS-MOA-AR-2021-22` | Fiji Ministry of Agriculture, *Annual Report 2021–2022* | Aggregate and commodity crop-production checks | Calibration candidate | https://www.agriculture.gov.fj/documents/annualreport/AR%202021-2022%20for%20Web.pdf |
| `DS-FBS-TRADE-2023` | Fiji Bureau of Statistics, *2023 International Merchandise Trade Statistics* | Diesel and residual-fuel import-value cross-check | Diagnostic candidate; national imports are not power-sector consumption | https://www.statsfiji.gov.fj/download/157/imts-annual-report/5696/2023-international-merchandise-trade-statistics-report.pdf |
| `DS-FBS-TRADE-2024` | Fiji Bureau of Statistics, *2024 International Merchandise Trade Statistics* | Diesel and residual-fuel import-value cross-check | Diagnostic candidate; national imports are not power-sector consumption | https://www.statsfiji.gov.fj/download/394/2024/4646/imts_annual_2024.pdf |

## Evidence not yet public or not yet retained

The following high-value records have not been found as complete public
datasets:

- hourly or half-hourly load by island grid;
- plant-level hourly dispatch;
- complete unit register with commissioning and retirement dates;
- unit outage and maintenance logs;
- reservoir storage, inflow, release, spill, and operating-rule series;
- station heat rates and delivered fuel prices;
- line ratings and operational transmission constraints;
- IPP contract, availability, and curtailment records;
- detailed water-pumping electricity consumption.

These gaps limit hourly reliability and operational validation. They do not
prevent an annual or wet/dry-season historical dispatch calibration, provided
the claim is kept at that resolution.

## Historical records

The original compact source manifest is retained unchanged at
`../documentation/history/raw_build/SOURCE_MANIFEST_ORIGINAL_2026-07-24.csv`.
The observations used in the initial raw comparison are retained at
`evidence/raw_baseline/CALIBRATION_CANDIDATES_2026-07-24.csv`. Neither file
should be mistaken for the complete current source register.
