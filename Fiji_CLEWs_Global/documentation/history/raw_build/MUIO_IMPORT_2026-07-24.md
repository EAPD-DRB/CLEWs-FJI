# MUIO import handoff

## Outcome

The raw, uncalibrated CLEWs Global Fiji model has been imported into MUIO as
`WebAPP/DataStorage/Fiji_CLEWs_Global`. The original `Raw` run and the
subsequent `Raw_ReserveProxy` run both solve to optimal CBC solutions.

No historical calibration constraints were added. `ImportTemplate.py` was not
edited; its SHA-256 during the import was
`d46c2e00b449f13763d5a093f4501789a6957597952f5e8b730e2d3f2f9b6ad0`.

## One-off workflow

1. Convert the upstream CLEWs CSV directory to Excel using otoole and
   `config/clewsy_otoole_config.yaml`.
2. Run `scripts/prepare_muiogo_workbook.py`. It:
   - adds the required `TECHGROUP` sheet and assigns all 132 technologies;
   - adds wet/dry and day/night descriptions;
   - omits empty optional parameter sheets that MUIO otherwise interprets as
     populated;
   - explicitly sets `DiscountRate` to 0.05 because CLEWs Global supplies no
     Fiji-specific value.
3. Run MUIO's existing importer with `scripts/import_into_muiogo.py`.
4. Run `scripts/repair_muiogo_timeslices.py` against only the generated Fiji
   case. It reconstructs the imported `genData.json` references and
   `RYDtb.json` values from `Conversionls.csv`, `Conversionld.csv`,
   `Conversionlh.csv`, and `DaySplit.csv`.
5. Create the `Raw` case run, generate `data.txt`, and solve with CBC.
6. Run the input and result parity checks.
7. Install the reserve-margin proxy described below, run its mandatory stale
   check, and solve the separate `Raw_ReserveProxy` case run.

The repaired mapping is:

| Timeslice | Season | Day type | Daily bracket |
|---|---|---|---|
| `S1D1` | Wet | Representative day | Day |
| `S1D2` | Wet | Representative day | Night |
| `S2D1` | Dry | Representative day | Day |
| `S2D2` | Dry | Representative day | Night |

Both daily brackets have `DaySplit = 0.0014` in every model year, as supplied
by CLEWs Global.

## Validation

The imported MUIO case contains 132 technologies, 107 commodities, 30 years,
four timeslices, two seasons, one day type, and two daily time brackets.

The preserved pre-proxy `Raw` solve is optimal with objective
`-2267.3628049`. The `Raw_ReserveProxy` solve is optimal with objective
`-2261.49703717`; all 30 annual UDC inequalities are present in its generated
data and solution output. The upstream CLEWs Global solution is also optimal,
with objective `-240.33220528`.

The most recent proxy check reports `CURRENT` with zero mismatches. An
intentional test that increased only 2022 annual demand correctly returned
`STALE`, exit status 2, and identified both the changed input fingerprint and
the outdated 2022 UDC constant.

Input round-trip:

- 66 of 68 otoole files are semantically exact.
- 32,609 of 33,179 source rows match, including implicit default-zero rows
  (98.282%).
- The only non-default losses are 30 `ReserveMarginTagFuel` rows and 540
  `ReserveMarginTagTechnology` rows.

Those reserve-margin values cannot be imported into their native parameters in
this MUIO version: they are absent from `Parameters.json`, and the declarations
and constraint are commented in `SOLVERs/model.v.5.4.txt`. A Fiji-specific
proxy now reproduces the intended capacity-credit test using MUIO's existing
annual user-defined constraints, without changing MUIO code. The proxy uses the
peak demand for `ELCFJIXX02`, since CLEWs Global tags the immediately upstream
`ELCFJIXX01` electricity node while final demand is placed on `ELCFJIXX02` and
the intervening transmission technology is 1:1.

The proxy is a derived constraint, not a calibration constraint. Its visible
MUIO name is
`RESERVE_PROXY_RUN_CHECK_IF_DEMAND_OR_MARGIN_CHANGES`. Its left-hand side uses
the 18 CLEWs Global technology capacity credits and
`CapacityToActivityUnit`; its right-hand side is the maximum, over timeslices,
of:

```text
SpecifiedAnnualDemand * SpecifiedDemandProfile / YearSplit * reserve margin
```

The default reserve margin is 1.0 because CLEWs Global's generated Fiji
`ReserveMargin.csv` is empty. Change that assumption in
`muio/reserve_margin_proxy_config.json`, not by manually editing the UDC.

### Mandatory stale check

The UDC constants cannot update themselves when their source data changes.
Before every solve after editing demand, its profile, `YearSplit`,
`CapacityToActivityUnit`, capacity credits, reserve margin, model years,
timeslices, or scenarios, run:

```bash
python3 Fiji_CLEWs_Global/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_CLEWs_Global --check
```

`CURRENT` means the stored UDC still matches the live MUIO case. `STALE`
returns exit status 2 and identifies the differences. Regenerate and recheck
with:

```bash
python3 Fiji_CLEWs_Global/scripts/manage_reserve_margin_proxy.py \
  WebAPP/DataStorage/Fiji_CLEWs_Global --update
```

The check covers every MUIO scenario. A new demand scenario therefore becomes
stale automatically until its UDC values are regenerated. A conspicuous
constraint name and description provide the warning inside MUIO, while
`reserve_margin_proxy.json` carries the warning and last-synchronized input
fingerprint inside the portable case backup.

The active objectives still differ: MUIO subtracts discounted salvage value,
while the active CLEWs Global objective used for Fiji does not. This remains a
formulation difference, not a calibration choice.

Consequently, this is a successful, usable MUIO import with a transparent
reserve-capacity proxy, but it is **not a result-equivalent execution of the
upstream CLEWs Global formulation**. The proxy addresses the unsupported
reserve tags; the objective difference remains. The original pre-proxy parity
evidence is retained in `muio/input_parity.json` and
`muio/result_parity.json`.

## Portable artifacts

- `muio/Fiji_CLEWs_Global_MUIO_import.xlsx`: reproducible importer workbook.
- `muio/Fiji_CLEWs_Global_MUIO_case.zip`: MUIO backup of the imported and
  solved case; `lp.lp` is omitted, matching MUIO's own backup behavior.
- `muio/reserve_margin_proxy_config.json`: reserve-margin assumption and the
  CLEWs Global technology capacity credits used by the proxy.
- `muio/reserve_margin_proxy_check.json`: most recent machine-readable stale
  check.
- `muio/genData.before_timeslice_repair.json` and
  `muio/RYDtb.before_timeslice_repair.json`: pre-repair audit copies.
- `muio/data_for_otoole_parity.txt`: analysis-only, otoole-readable copy of the
  generated MUIO data file.

On another laptop with the same MUIOGO version, upload the case ZIP through
MUIO or regenerate it from the workbook and scripts above.
