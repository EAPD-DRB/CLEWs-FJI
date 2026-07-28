# Phase 1D source extracts: cane, bagasse and IPP electricity

**Date reviewed:** 28 July 2026

**Active evidence table:** `fiji_phase1d_cane_bagasse_power_balance_2020_2024.csv`

**Evidence-table SHA-256:** `f3bc9cf7d1c0ddbbe15e2a3d08b84d3995732dfae49b118eb1970c2a0b2e9717`

This record pins every external quantity used by the Phase 1D
cane–bagasse–electricity closure. The calculations are documented separately
in `../../calculation_notes/PHASE_1D_CANE_BAGASSE_ELECTRICITY.md`.

## Fiji Sugar Corporation operating data

The [FSC annual-report index](https://fsc.com.fj/annualreports/) is the entry
point. Phase 1D uses the operating table for each crushing season, not a
financial proxy.

| Season | Cane crushed t | Sugar made t | Molasses t | Source and locator |
|---|---:|---:|---:|---|
| 2020 | 1,729,171 | 151,589 | 82,767 | FSC 2021 Annual Report, PDF p. 15, “2020 Season Key Operating Data” |
| 2021 | 1,417,185 | 133,209 | 71,710 | FSC 2022 Annual Report, PDF pp. 14–15, “2021 Key Operating Data” |
| 2022 | 1,639,004 | 155,812 | 74,178 | FSC 2023 Annual Report, PDF pp. 16–17, “2022 Season Key Operating Data” |
| 2023 | 1,565,586 | 139,628 | 71,939 | FSC 2024 Annual Report, PDF pp. 20–21 |
| 2024 | 1,331,922 | 126,522 | 64,191 | FSC 2025 Annual Report, PDF p. 21, “Targets vs Achievements for 2024 Season” |

The downloaded source checksums were:

| Report | URL | SHA-256 |
|---|---|---|
| FSC 2021 | `https://fsc.com.fj/wp-content/uploads/2025/11/2021.pdf` | `87a7d6751eb27122834c6cd3b1cf7db9ba534663cbea08ec93346a49d91b63eb` |
| FSC 2022 | `https://fsc.com.fj/wp-content/uploads/2025/11/2022.pdf` | `6c26fdcf616bc36809c46c0865622a3c0a2e816334bb4baf6afaf2ae3f0ab002` |
| FSC 2023 | `https://fsc.com.fj/wp-content/uploads/2025/11/2023.pdf` | `25456526f1fbd12f4a714166a4c0bdd61d4f4cc8e0e9456e471f0cbacda40c24` |
| FSC 2024 | `https://fsc.com.fj/wp-content/uploads/2025/11/2024_Annual-Report-1.pdf` | `c0fa0e21b53a8c14c5ba0d3fc7b9e88f2f4b8dab01293e1eadc6294240d76269` |
| FSC 2025 | `https://fsc.com.fj/wp-content/uploads/2025/11/FSC-Annual-Inserts-2025_compressed.pdf` | `c861fc8abe28673301cbd7a3c57c8c44b30e475bbbfb38258e3ab76231004940` |

Cane crushed is active model input. Sugar and molasses are retained as
cross-check quantities but are not yet separate model commodities.

## Exportable bagasse-electricity coefficient

The active engineering source is IRENA, *Sugarcane bioenergy in Southern
Africa: Economic potential for sustainable scale-up* (2019):

- URL:
  `https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2019/Apr/IRENA_Sugarcane_bioenergy_2019.pdf`
- SHA-256:
  `2b7c25413dabdff10d0b549c29aa53482dfa60b50d590ef483693619cf294a44`
- locator: PDF p. 37, Table 3.1;
- selected case: 42 bar, 400°C, 500 kg process steam per tonne cane, no
  recovered straw; and
- surplus electricity: 25.4 kWh per tonne cane.

This is a central engineering proxy, not a claim that all FSC mills have the
same boiler and steam cycle. The table also supplies lower and higher
configurations that should be used in sensitivity analysis.

The same IRENA publication gives a gross bagasse proxy of 280 kg at 50%
moisture per tonne cane. Phase 1D retains that value only in the evidence
table. The active model uses exportable energy after process-steam needs,
avoiding double counting gross bagasse energy and mill process heat.

## Grid-supplying biomass stock

The Government of Fiji, *Renewable Energy Integration Investment Plan*,
identifies:

- FSC Lautoka: 5 MW bagasse;
- FSC Labasa: 20 MW bagasse; and
- Tropik Wood: 9 MW wood residue.

The active split is therefore 25 MW bagasse plus 9 MW wood residue. Source
URL:
`https://fijiclimatechangeportal.gov.fj/wp-content/uploads/2023/09/Fiji_CIF_REI_IP.pdf`;
retained checksum:
`3d291fad4853905d40486f253d974483a9b788881c6ea9e02e6ba725989790e1`.

## Aggregate IPP generation

Energy Fiji Limited's 2024 Annual Report, printed p. 88, “Generation
Statistics for the Past Ten (10) Years,” reports aggregate IPP purchases:

| Year | IPP MWh |
|---|---:|
| 2020 | 67,094 |
| 2021 | 61,053 |
| 2022 | 73,471 |
| 2023 | 76,115 |
| 2024 | 63,799 |

Source URL:
`https://efl.com.fj/wp-content/uploads/2025/05/EFL-2024-Annual-Report.pdf`;
retained checksum:
`b3427b8e597399f31aabc2ab315b1a72a24138e20cd8faa5c3fec2894f0fe956`.

EFL does not separate FSC bagasse and Tropik Wood in this table. Phase 1D
therefore calculates bagasse export from cane and treats the remaining
2020–2022 IPP output as the wood-residue calibration quantity. The 2023–2024
rows remain held out.

## Boundary cross-check

The Fiji Bureau of Statistics physical energy-supply-and-use workbook was
checked for a separate bagasse or wood series:

- URL:
  `https://www.statsfiji.gov.fj/download/245/tables/3487/energy-supply-and-use.xlsx`
- SHA-256:
  `8850294afaaa4e70b6f276ae052da24e74e3743cca317d2a3b5ab007bf199ed4`.

It supports the aggregate renewable/electricity boundary but does not identify
bagasse and Tropik Wood separately. It is therefore a cross-check, not the
source of either Phase 1D coefficient.

## Calibration split and use restrictions

- 2020–2022: permitted calibration years.
- 2023–2024: held-out validation years.
- The IRENA coefficient is an engineering assumption and must be
  sensitivity-tested.
- The calculated wood residual is not direct plant-level measurement.
- The 2023–2024 IPP observations were not used to tune the active wood bound.
