# Phase 1D cane–bagasse–electricity calculations

**Date:** 28 July 2026

**Builder:** `scripts/apply_fiji_phase1d_cane_bagasse.py`

**Frozen evidence:** `../evidence/energy/fiji_phase1d_cane_bagasse_power_balance_2020_2024.csv`

## Implemented chain

```text
land/crop options
  -> CRPSGC [Mt raw cane]
  -> SGCMILLFJI
       -> SGCPROCFJI [Mt processed cane demand]
       -> BAGEXPFJI [PJ exportable bagasse energy]
  -> PWRBAGFJIXX01
  -> ELCFJIXX01

RNWBIOFJIXX
  -> BIOFJIXX
  -> PWRWODFJIXX01
  -> ELCFJIXX01
```

`PWRBIOFJIXX01` remains in the case only as a disabled shell so existing MUIO
identifiers and historical packages stay traceable.

## Units

The upstream crop generator calculates FAOSTAT production as:

```text
crop production [tonnes] / 1,000,000
```

The numerical unit of `CRPSGC` is therefore million tonnes (`Mt`), despite
the inherited generic `PJ` label. Phase 1D corrects the metadata and uses:

- `CRPSGC`: Mt raw cane;
- `SGCPROCFJI`: Mt processed cane;
- `BAGEXPFJI`: PJ exportable bagasse energy; and
- power-technology activity: PJ electricity.

## Cane throughput

For 2020–2024:

```text
SGCPROCFJI(y) [Mt] = FSC cane crushed(y) [t] / 1,000,000
```

This replaces direct accumulated demand on `CRPSGC`. The mill has 1:1 raw
cane input and processed-cane output, so the crop system must supply the
reported physical throughput.

For 2025–2050:

```text
SGCPROCFJI(y)
  = FSC cane crushed(2024)
  × inherited CRPSGC(y)
  / inherited CRPSGC(2024)
```

Selected values are:

| Year | Processed cane Mt |
|---|---:|
| 2024 | 1.331922000 |
| 2025 | 1.337652981 |
| 2030 | 1.359240771 |
| 2040 | 1.380624641 |
| 2050 | 1.372601601 |

This is a rebased scenario path, not an FSC forecast.

## Bagasse export

IRENA's selected central case exports 25.4 kWh per tonne cane:

```text
electricity export [PJ/Mt cane]
  = 25.4 kWh/t
  × 1,000,000 t/Mt
  × 3.6 MJ/kWh
  / 1,000,000,000 MJ/PJ
  = 0.09144 PJ/Mt cane
```

The inherited biomass generator consumes 3.82 PJ fuel per PJ electricity.
The mill therefore produces:

```text
exportable bagasse [PJ/Mt cane]
  = 0.09144 × 3.82
  = 0.3493008
```

and the generator uses:

```text
3.82 PJ BAGEXPFJI -> 1 PJ ELCFJIXX01
```

The two-stage chain exactly reproduces 25.4 kWh exported per tonne cane.

## Wood-residue residual

For each evidence year:

```text
bagasse export MWh(y)
  = FSC cane crushed t(y) × 25.4 kWh/t / 1,000

wood residual MWh(y)
  = EFL aggregate IPP MWh(y) - bagasse export MWh(y)
```

| Year | Bagasse export MWh | Wood residual MWh | Split |
|---|---:|---:|---|
| 2020 | 43,920.9434 | 23,173.0566 | Calibration |
| 2021 | 35,996.4990 | 25,056.5010 | Calibration |
| 2022 | 41,630.7016 | 31,840.2984 | Calibration |
| 2023 | 39,765.8844 | 36,349.1156 | Validation |
| 2024 | 33,830.8188 | 29,968.1812 | Validation |

Only 2020–2022 enter the active parameter:

```text
mean wood generation
  = mean(23,173.0566; 25,056.5010; 31,840.2984)
  = 26,689.952 MWh/year

wood activity upper
  = 26,689.952 × 0.0000036
  = 0.0960838272 PJ/year

wood availability
  = 26,689.952 MWh
  / (9 MW × 8,760 h)
  = 0.338533130391
```

Both the annual activity upper bound and availability are retained. The
activity cap prevents the inherited investment option from turning a
calibrated 9 MW residue plant into an unlimited future biomass resource.

## Capacity split

The inherited aggregate residual-capacity path is split without changing its
sum:

```text
PWRBAGFJIXX01 RC(y) = inherited PWRBIOFJIXX01 RC(y) × 25 / 34
PWRWODFJIXX01 RC(y) = inherited PWRBIOFJIXX01 RC(y) × 9 / 34
```

The active 2021 capacities are 0.025 GW and 0.009 GW. The old aggregate
technology has zero residual capacity, maximum investment and activity upper
limit.

## Accounting control

The structural control retains inherited cane demand and aggregate biomass
availability. It uses an artificial mill output of 10 PJ `BAGEXPFJI` per Mt
cane so bagasse cannot bind anywhere in 2020–2050. That number is diagnostic
only.

The control reproduces aggregate biomass activity to numerical precision and
changes no unrelated annual technology-activity row. Its objective differs
from Phase 1C by `-0.00232577` (`-0.000147793%`) because the split creates
equivalent investment timing alternatives in the discounted objective.

## Physical validation result

The live `Phase1D_Cane_Bagasse` run is Optimal at objective
`-1548.8662358`, 1.576266% above the Phase 1C objective. Exportable-bagasse
annual balance residuals are below `7 × 10^-17 PJ`.

Aggregate IPP generation MAPE is:

- 2020–2022 calibration: 4.97575%; and
- 2023–2024 held out: 8.91430%.

The broader generation validator reports 2024 thermal generation 20.6466%
above observation, just outside its 20% single-outcome threshold. This is
recorded as an incomplete general validation check; Phase 1D was not retuned
to the held-out years.
