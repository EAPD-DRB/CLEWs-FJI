# Phase 1C source review: end-use energy and residential cooking

**Review date:** 27 July 2026  
**Purpose:** Decide which disconnected end-use branches can be activated
without inventing demand or double counting the existing gross electricity
requirement.

## Sources inspected

### `DS-FBS-ENERGY-ACCOUNT-2024`

- Provider: Fiji Bureau of Statistics (FBoS).
- Publication: *Fiji's Experimental Environmental Account for Energy 2024*,
  Release No. 50, 2025.
- PDF:
  https://www.statsfiji.gov.fj/download/241/releases/5048/2024-fijis-experimental-environmental-account-for-energy.pdf
- Physical supply-and-use workbook linked from Appendix 1:
  https://www.statsfiji.gov.fj/download/245/tables/3487/energy-supply-and-use.xlsx
- Retrieved: 27 July 2026.
- PDF SHA-256:
  `24f869da57d75eb32523fd1c21f075ecfa48add56f103a41762d3fb663f974fa`.
- Workbook SHA-256:
  `8850294afaaa4e70b6f276ae052da24e74e3743cca317d2a3b5ab007bf199ed4`.
- Relevant locators: PDF Appendix 1, page 3; workbook sheet `Energy SUT`,
  rows for 2020-2024.

The source gives annual electricity use by commercial, industrial and
domestic customers, household own-generation output, and distribution losses.
Those quantities are sufficient to decompose the model's existing gross EFL
grid-supply requirement without changing its total. They do not allocate
electricity among cooking, lighting, appliances, motors or thermal services.

The reviewed 2020-2024 extraction and reconciliation is retained in
`fiji_energy_account_2024_electricity_boundary_2020_2024.csv`.

### `DS-FJI-MICS-2021`

- Providers: Fiji Bureau of Statistics, Ministry of Health and Medical
  Services, and UNICEF.
- Publication: *Fiji Multiple Indicator Cluster Survey 2021 - Survey Finding
  Report*.
- Official FBoS entry:
  https://www.statsfiji.gov.fj/mics-2021/
- Report:
  https://www.statsfiji.gov.fj/download/56/mics/66/Fiji_MICS_2021_Survey_Finding_Report.pdf
- Retrieved: 27 July 2026.
- Report SHA-256:
  `bd07375a3851447fa907ffbe15b4c9c708deb451e521f24074e269d17ffcfba7`.
- Relevant locators: Table SR.2.1, printed page 29; Table TC.4.1,
  printed page 157; Table TC.4.2, printed page 158.

The weighted national results show that 52.1% of households used clean
cooking fuels and technologies. On a household-member basis, the main
cookstove shares were 46.0% LPG, 27.2% non-alcohol liquid-fuel stove,
19.3% open fire, 2.7% biogas, 1.3% traditional solid-fuel stove and 1.0%
electric stove. Table TC.4.2 separately reports 28.0% primary reliance on
kerosene/paraffin and 21.4% on wood.

These are population or household shares, not energy quantities. They support
the candidate residential technology set and provide later share-validation
targets. They do not establish annual fuel input, useful cooking demand, fuel
stacking, appliance utilization or conversion efficiency.

The extracted values and model-mapping cautions are retained in
`fiji_mics_2021_cooking_mix.csv`.

## Electricity boundary that the evidence supports

For each historical year, the existing model quantity can be decomposed as:

```text
gross EFL grid-supply requirement
  = commercial grid use
  + industrial grid use
  + (domestic total use - household own-generation output)
  + distribution loss
  + station-use and boundary-reconciliation residual
```

The last term is calculated rather than directly observed. It must remain
labelled as a residual until EFL station-use and FBoS/EFL boundary differences
are reconciled.

For 2024, in PJ:

```text
4.3880616
  = 1.8214069392
  + 0.8443905300
  + (1.5792538397 - 0.3244511165)
  + 0.2377850076
  + 0.2296764000
```

This permits a future accounting-only implementation that routes the
commercial, industrial and grid-served domestic components through the
existing sector electricity adapters while reducing direct
`ELCFJIXX02` demand by exactly the same amount. Adding sector demand on top
of the current gross requirement would double count electricity.

## Evidence decisions

| Proposed use | Decision | Reason |
|---|---|---|
| Historical commercial electricity quantity | Ready for accounting implementation | Annual 2020-2024 PJ values are available and reconcile to the existing gross boundary with explicit residuals |
| Historical industrial electricity quantity | Ready for accounting implementation | Same |
| Historical grid-served domestic electricity quantity | Ready for accounting implementation | Domestic total can be separated from household own generation |
| Future sector electricity shares | Assumption required | No post-2024 observation is used by this gate |
| Residential cooking technology mix | Ready as share evidence | Weighted national survey results identify the main stove/fuel pathways |
| Residential cooking useful-energy demand | Not ready | No annual useful-energy or fuel-quantity magnitude is established |
| Cooking conversion efficiencies | Not ready | No Fiji-specific efficiency set is retained |
| Existing `RESNGS` as biogas | Rejected | Surveyed biogas is not fossil natural gas; it needs a distinct documented pathway |

## Evidence still required for an active cooking service

At least one defensible annual magnitude is needed: residential cooking fuel
quantities, expenditure-plus-price quantities, measured stove consumption, or
a transparent household useful-energy estimate. The implementation also needs
technology efficiencies, treatment of fuel stacking, a biomass boundary, and
a documented decision on whether biogas is explicit or aggregated. Until then,
the MICS percentages remain validation and technology-choice evidence only.
