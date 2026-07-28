#!/usr/bin/env python3
"""Validate Fiji Phase 1D cane-bagasse-electricity closure."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
DEFAULT_MUIOGO = Path(__file__).resolve().parents[3] / "MUIOGO"
DEFAULT_OUTPUT = (
    PACKAGE
    / "diagnostics"
    / "calibration_runs"
    / "phase1d"
    / "validation_summary.json"
)
HISTORICAL_YEARS = tuple(range(2020, 2025))
CALIBRATION_YEARS = tuple(range(2020, 2023))
VALIDATION_YEARS = tuple(range(2023, 2025))

sys.path.insert(0, str(PACKAGE / "scripts"))
from apply_fiji_phase1d_cane_bagasse import (  # noqa: E402
    BAGASSE_CAPACITY_GW,
    BAGASSE_POWER,
    EXPORT_ELECTRICITY_PJ_PER_MT_CANE,
    EXPORTABLE_BAGASSE,
    EXPORTABLE_BAGASSE_PJ_PER_MT_CANE,
    FSC_OPERATIONS,
    GRID_OUTPUT,
    IPP_MWH,
    MILL,
    NEW_COMM_IDS,
    NEW_TECH_IDS,
    OLD_POWER,
    POWER_HEAT_RATE,
    PROCESSED_CANE,
    RAW_CANE,
    WOOD_ACTIVITY_UPPER_PJ,
    WOOD_AVAILABILITY,
    WOOD_CAPACITY_GW,
    WOOD_POWER,
    cane_throughput,
)
from manage_reserve_margin_proxy import (  # noqa: E402
    check_proxy,
    expected_proxy,
    load_case,
    validate_config,
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parameter_row(
    data: dict[str, Any], parameter: str, **identifiers: Any
) -> dict[str, Any]:
    matches = [
        row
        for row in data[parameter]["SC_0"]
        if all(row.get(key) == value for key, value in identifiers.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {identifiers}; "
            f"found {len(matches)}"
        )
    return matches[0]


def objective(run: Path) -> float:
    return float(rows(run / "csv" / "ObjectiveValue.csv")[0]["ObjectiveValue"])


def result_value(
    path: Path, symbol: str, indices: tuple[Any, ...]
) -> tuple[float, float]:
    label = f"{symbol}({','.join(str(value) for value in indices)})"
    match = re.search(
        rf"^\s*\d+\s+{re.escape(label)}\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$",
        path.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Missing result row: {label}")
    return float(match.group(1)), float(match.group(2))


def table_map(
    path: Path, keys: tuple[str, ...], value: str
) -> dict[tuple[str, ...], float]:
    result: dict[tuple[str, ...], float] = defaultdict(float)
    for row in rows(path):
        result[tuple(row[key] for key in keys)] += float(row[value])
    return dict(result)


def compare_maps(
    left: dict[tuple[str, ...], float],
    right: dict[tuple[str, ...], float],
    *,
    exclude_technologies: set[str],
    tolerance: float = 1e-7,
) -> dict[str, Any]:
    keys = {
        key
        for key in left.keys() | right.keys()
        if key[0] not in exclude_technologies
    }
    differences = [
        (key, left.get(key, 0.0), right.get(key, 0.0))
        for key in keys
        if not math.isclose(
            left.get(key, 0.0),
            right.get(key, 0.0),
            rel_tol=0,
            abs_tol=tolerance,
        )
    ]
    return {
        "compared_rows": len(keys),
        "changed_rows": len(differences),
        "maximum_absolute_difference": max(
            (abs(a - b) for _, a, b in differences), default=0.0
        ),
        "examples": [
            {"key": key, "baseline": a, "checkpoint": b}
            for key, a, b in sorted(differences)[:10]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--muiogo-root", type=Path, default=DEFAULT_MUIOGO)
    parser.add_argument("--baseline-case", default="Fiji_v2")
    parser.add_argument("--baseline-run", default="Phase1C_BottomUp")
    parser.add_argument(
        "--accounting-case", default="Fiji_v2_Phase1D_Accounting_Test"
    )
    parser.add_argument("--accounting-run", default="Phase1D_Accounting")
    parser.add_argument(
        "--physical-case",
        default="Fiji_v2_Phase1D_Legacy_Removal_Test",
    )
    parser.add_argument(
        "--physical-run", default="Phase1D_Legacy_Removal"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    storage = args.muiogo_root.resolve() / "WebAPP" / "DataStorage"
    baseline_case = storage / args.baseline_case
    accounting_case = storage / args.accounting_case
    physical_case = storage / args.physical_case
    baseline_run = baseline_case / "res" / args.baseline_run
    accounting_run = accounting_case / "res" / args.accounting_run
    physical_run = physical_case / "res" / args.physical_run
    output = args.output.resolve()

    required: list[Path] = []
    for case, run in (
        (baseline_case, baseline_run),
        (accounting_case, accounting_run),
        (physical_case, physical_run),
    ):
        required.extend(
            [
                case / "genData.json",
                case / "RYC.json",
                case / "RYT.json",
                case / "RYTCM.json",
                run / "data.txt",
                run / "data_processed.txt",
                run / "lp.lp",
                run / "results.txt",
                run / "csv" / "ObjectiveValue.csv",
                run / "csv" / "TotalAnnualTechnologyActivityByMode.csv",
                run / "csv" / "TotalCapacityAnnual.csv",
                run / "csv" / "AnnualTechnologyEmission.csv",
            ]
        )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing artifacts: " + "; ".join(missing))

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, finding: Any, evidence: str) -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "finding": finding,
                "evidence": evidence,
            }
        )

    gen_data = read_json(physical_case / "genData.json")
    years = [int(year) for year in gen_data["osy-years"]]
    tech = {row["Tech"]: row for row in gen_data["osy-tech"]}
    comm = {row["Comm"]: row for row in gen_data["osy-comm"]}
    expected_entities = set(NEW_TECH_IDS) <= tech.keys() and set(
        NEW_COMM_IDS
    ) <= comm.keys()
    check(
        "Phase 1D structural entities and dimensions are present",
        expected_entities
        and OLD_POWER not in tech
        and len(tech) == 133
        and len(comm) == 106,
        {
            "technologies": len(tech),
            "commodities": len(comm),
            "legacy_technology_present": OLD_POWER in tech,
            "new_technologies": sorted(set(NEW_TECH_IDS) & tech.keys()),
            "new_commodities": sorted(set(NEW_COMM_IDS) & comm.keys()),
        },
        "genData.json",
    )
    units = {
        name: comm[name]["UnitId"]
        for name in (RAW_CANE, PROCESSED_CANE, EXPORTABLE_BAGASSE)
    }
    check(
        "Cane and bagasse metadata use the implemented physical units",
        units
        == {
            RAW_CANE: "Mt",
            PROCESSED_CANE: "Mt",
            EXPORTABLE_BAGASSE: "PJ",
        },
        units,
        "genData.json; upstream clewsy.py FAOSTAT / 1,000,000 conversion",
    )

    tech_ids = {name: row["TechId"] for name, row in tech.items()}
    comm_ids = {name: row["CommId"] for name, row in comm.items()}
    ryc = read_json(physical_case / "RYC.json")
    inherited_ryc = read_json(baseline_case / "RYC.json")
    inherited = {
        year: float(
            parameter_row(
                inherited_ryc, "AAD", CommId=comm_ids[RAW_CANE]
            )[str(year)]
        )
        for year in years
    }
    if all(value == 0.0 for value in inherited.values()):
        accounting_ryc = read_json(accounting_case / "RYC.json")
        accounting_gen = read_json(accounting_case / "genData.json")
        accounting_comm_ids = {
            row["Comm"]: row["CommId"]
            for row in accounting_gen["osy-comm"]
        }
        inherited = {
            year: float(
                parameter_row(
                    accounting_ryc,
                    "AAD",
                    CommId=accounting_comm_ids[PROCESSED_CANE],
                )[str(year)]
            )
            for year in years
        }
    expected_throughput = cane_throughput(years, inherited)
    raw_demand = parameter_row(ryc, "AAD", CommId=comm_ids[RAW_CANE])
    processed_demand = parameter_row(
        ryc, "AAD", CommId=comm_ids[PROCESSED_CANE]
    )
    throughput_differences = {
        year: float(processed_demand[str(year)]) - expected_throughput[year]
        for year in years
    }
    check(
        "FSC historical cane throughput and rebased future path are exact",
        all(
            math.isclose(value, 0.0, rel_tol=0, abs_tol=1e-10)
            for value in throughput_differences.values()
        )
        and all(float(raw_demand[str(year)]) == 0.0 for year in years),
        {
            "maximum_absolute_difference_mt": max(
                abs(value) for value in throughput_differences.values()
            ),
            "historical_mt": {
                year: float(processed_demand[str(year)])
                for year in HISTORICAL_YEARS
            },
            "future_mt": {
                year: float(processed_demand[str(year)])
                for year in (2025, 2030, 2040, 2050)
            },
        },
        "RYC.json; FSC annual reports; inherited Phase 1C path",
    )

    rytcm = read_json(physical_case / "RYTCM.json")

    def relation(parameter: str, technology: str, commodity: str) -> float:
        row = parameter_row(
            rytcm,
            parameter,
            TechId=tech_ids[technology],
            CommId=comm_ids[commodity],
            MoId=1,
        )
        values = {float(row[str(year)]) for year in years}
        if len(values) != 1:
            raise ValueError(
                f"Nonconstant {parameter} for {technology}/{commodity}"
            )
        return values.pop()

    relations = {
        "mill_raw_cane_input": relation("IAR", MILL, RAW_CANE),
        "mill_processed_cane_output": relation(
            "OAR", MILL, PROCESSED_CANE
        ),
        "mill_bagasse_output": relation(
            "OAR", MILL, EXPORTABLE_BAGASSE
        ),
        "bagasse_power_input": relation(
            "IAR", BAGASSE_POWER, EXPORTABLE_BAGASSE
        ),
        "bagasse_power_output": relation(
            "OAR", BAGASSE_POWER, GRID_OUTPUT
        ),
        "wood_power_output": relation(
            "OAR", WOOD_POWER, GRID_OUTPUT
        ),
    }
    expected_relations = {
        "mill_raw_cane_input": 1.0,
        "mill_processed_cane_output": 1.0,
        "mill_bagasse_output": EXPORTABLE_BAGASSE_PJ_PER_MT_CANE,
        "bagasse_power_input": POWER_HEAT_RATE,
        "bagasse_power_output": 1.0,
        "wood_power_output": 1.0,
    }
    check(
        "Cane-mill-bagasse-electricity coefficients are exact",
        all(
            math.isclose(
                relations[key], value, rel_tol=0, abs_tol=1e-12
            )
            for key, value in expected_relations.items()
        ),
        relations,
        "RYTCM.json; IRENA 2019 Table 3.1; inherited heat rate",
    )

    ryt = read_json(physical_case / "RYT.json")

    def year_parameter(parameter: str, technology: str) -> dict[int, float]:
        row = parameter_row(
            ryt, parameter, TechId=tech_ids[technology]
        )
        return {year: float(row[str(year)]) for year in years}

    bag_rc = year_parameter("RC", BAGASSE_POWER)
    wood_rc = year_parameter("RC", WOOD_POWER)
    baseline_ryt = read_json(baseline_case / "RYT.json")
    baseline_gen = read_json(baseline_case / "genData.json")
    baseline_tech_ids = {
        row["Tech"]: row["TechId"]
        for row in baseline_gen["osy-tech"]
    }
    baseline_rc_row = parameter_row(
        baseline_ryt, "RC", TechId=baseline_tech_ids[OLD_POWER]
    )
    accounting_ryt = read_json(accounting_case / "RYT.json")
    accounting_gen = read_json(accounting_case / "genData.json")
    accounting_tech_ids = {
        row["Tech"]: row["TechId"]
        for row in accounting_gen["osy-tech"]
    }
    accounting_bag_rc = parameter_row(
        accounting_ryt,
        "RC",
        TechId=accounting_tech_ids[BAGASSE_POWER],
    )
    accounting_wood_rc = parameter_row(
        accounting_ryt,
        "RC",
        TechId=accounting_tech_ids[WOOD_POWER],
    )
    split_errors = {
        year: (
            bag_rc[year] + wood_rc[year]
            - (
                float(baseline_rc_row[str(year)])
                if any(
                    float(baseline_rc_row[str(candidate)]) != 0.0
                    for candidate in years
                )
                else float(accounting_bag_rc[str(year)])
                + float(accounting_wood_rc[str(year)])
            )
        )
        for year in years
    }
    check(
        "The retired aggregate technology is absent and stock remains split 25/9 MW",
        OLD_POWER not in tech
        and all(
            math.isclose(value, 0.0, rel_tol=0, abs_tol=1e-12)
            for value in split_errors.values()
        )
        and math.isclose(bag_rc[2021], BAGASSE_CAPACITY_GW)
        and math.isclose(wood_rc[2021], WOOD_CAPACITY_GW),
        {
            "legacy_technology_present": OLD_POWER in tech,
            "bagasse_2021_gw": bag_rc[2021],
            "wood_2021_gw": wood_rc[2021],
            "maximum_split_error_gw": max(
                abs(value) for value in split_errors.values()
            ),
        },
        "genData.json; RYT.json; Government of Fiji REI Investment Plan",
    )
    wood_af = year_parameter("AF", WOOD_POWER)
    wood_tau = year_parameter("TAU", WOOD_POWER)
    bag_af = year_parameter("AF", BAGASSE_POWER)
    check(
        "Bagasse is cane-limited and wood residue has a separate resource cap",
        all(value == 1.0 for value in bag_af.values())
        and all(
            math.isclose(
                value, WOOD_AVAILABILITY, rel_tol=0, abs_tol=1e-12
            )
            for value in wood_af.values()
        )
        and all(
            math.isclose(
                value,
                WOOD_ACTIVITY_UPPER_PJ,
                rel_tol=0,
                abs_tol=1e-12,
            )
            for value in wood_tau.values()
        ),
        {
            "bagasse_availability": bag_af[2020],
            "wood_availability": wood_af[2020],
            "wood_activity_upper_pj": wood_tau[2020],
        },
        "RYT.json; 2020-2022 EFL/FSC residual calculation",
    )

    generated = (physical_run / "data_processed.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    mappings = (
        "(1, SGCMILLFJI)" in generated
        and "(1, PWRBAGFJIXX01)" in generated
        and "(1, PWRWODFJIXX01)" in generated
        and OLD_POWER not in generated
        and "MODExTECHNOLOGYperFUELout[BAGEXPFJI]" in generated
        and "MODExTECHNOLOGYperFUELin[BAGEXPFJI]" in generated
    )
    check(
        "Generated solver sets contain every Phase 1D mode and fuel mapping",
        mappings,
        "Phase 1D technologies and BAGEXPFJI present in derived mappings"
        if mappings
        else "One or more generated mappings are missing",
        "data_processed.txt",
    )

    solver_status = (
        physical_run / "results.txt"
    ).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    check(
        "Physical checkpoint passed preprocessing, GLPK matrix creation and CBC",
        solver_status.startswith("Optimal")
        and (physical_run / "data_processed.txt").stat().st_size > 0
        and (physical_run / "lp.lp").stat().st_size > 0,
        {
            "solver_status": solver_status,
            "lp_bytes": (physical_run / "lp.lp").stat().st_size,
        },
        "data_processed.txt; lp.lp; results.txt",
    )

    baseline_obj = objective(baseline_run)
    accounting_obj = objective(accounting_run)
    physical_obj = objective(physical_run)
    accounting_pct = 100 * (accounting_obj - baseline_obj) / abs(
        baseline_obj
    )
    physical_pct = 100 * (physical_obj - baseline_obj) / abs(baseline_obj)
    check(
        "Accounting-control objective remains within the declared parity tolerance",
        abs(accounting_pct) <= 0.2,
        {
            "baseline": baseline_obj,
            "accounting": accounting_obj,
            "difference": accounting_obj - baseline_obj,
            "difference_percent": accounting_pct,
            "tolerance_percent": 0.2,
        },
        "ObjectiveValue.csv; aggregate-equivalent stock split",
    )

    activity_file = "TotalAnnualTechnologyActivityByMode.csv"
    baseline_activity = table_map(
        baseline_run / "csv" / activity_file,
        ("t", "y"),
        "TotalAnnualTechnologyActivityByMode",
    )
    accounting_activity = table_map(
        accounting_run / "csv" / activity_file,
        ("t", "y"),
        "TotalAnnualTechnologyActivityByMode",
    )
    power_aggregate_errors: dict[int, float] = {}
    for year in years:
        old = baseline_activity.get((OLD_POWER, str(year)), 0.0)
        split = sum(
            accounting_activity.get((technology, str(year)), 0.0)
            for technology in (BAGASSE_POWER, WOOD_POWER)
        )
        power_aggregate_errors[year] = split - old
    unaffected = compare_maps(
        baseline_activity,
        accounting_activity,
        exclude_technologies={
            OLD_POWER,
            MILL,
            BAGASSE_POWER,
            WOOD_POWER,
            "RNWBIOFJIXX",
        },
    )
    check(
        "Accounting control preserves aggregate biomass and unrelated activity",
        max(abs(value) for value in power_aggregate_errors.values())
        <= 1e-7
        and unaffected["changed_rows"] == 0,
        {
            "maximum_biomass_activity_error_pj": max(
                abs(value) for value in power_aggregate_errors.values()
            ),
            "unaffected": unaffected,
        },
        "TotalAnnualTechnologyActivityByMode.csv",
    )

    physical_results = physical_run / "results.txt"
    flow: dict[int, Any] = {}
    flow_pass = True
    for year in years:
        mill, _ = result_value(
            physical_results,
            "TotalAnnualTechnologyActivityByMode",
            ("RE1", MILL, 1, year),
        )
        bagasse, _ = result_value(
            physical_results,
            "TotalAnnualTechnologyActivityByMode",
            ("RE1", BAGASSE_POWER, 1, year),
        )
        wood, _ = result_value(
            physical_results,
            "TotalAnnualTechnologyActivityByMode",
            ("RE1", WOOD_POWER, 1, year),
        )
        expected_bagasse = (
            expected_throughput[year]
            * EXPORT_ELECTRICITY_PJ_PER_MT_CANE
        )
        flow_pass &= math.isclose(
            mill, expected_throughput[year], rel_tol=0, abs_tol=1e-6
        )
        flow_pass &= math.isclose(
            bagasse, expected_bagasse, rel_tol=0, abs_tol=1e-6
        )
        flow_pass &= wood <= WOOD_ACTIVITY_UPPER_PJ + 1e-8
        if year in HISTORICAL_YEARS or year in (2030, 2050):
            flow[year] = {
                "mill_mt": mill,
                "bagasse_power_pj": bagasse,
                "expected_bagasse_power_pj": expected_bagasse,
                "wood_power_pj": wood,
            }
    check(
        "Solved cane and bagasse flows close in every model year",
        flow_pass,
        flow,
        "results.txt; FSC throughput; IRENA export coefficient",
    )

    bagasse_residuals: dict[int, Any] = {}
    residual_pass = True
    for year in years:
        residual, dual = result_value(
            physical_results,
            "EBb4_EnergyBalanceEachYear4",
            ("RE1", EXPORTABLE_BAGASSE, year),
        )
        residual_pass &= abs(residual) <= 1e-8
        if year in HISTORICAL_YEARS or year in (2030, 2050):
            bagasse_residuals[year] = {
                "residual_pj": residual,
                "dual": dual,
            }
    check(
        "Exportable-bagasse annual balance residuals are numerically zero",
        residual_pass,
        bagasse_residuals,
        "results.txt EBb4_EnergyBalanceEachYear4",
    )

    fit: dict[str, Any] = {}
    for label, selected_years in (
        ("calibration", CALIBRATION_YEARS),
        ("validation", VALIDATION_YEARS),
    ):
        errors = []
        year_rows = {}
        for year in selected_years:
            bagasse, _ = result_value(
                physical_results,
                "TotalAnnualTechnologyActivityByMode",
                ("RE1", BAGASSE_POWER, 1, year),
            )
            wood, _ = result_value(
                physical_results,
                "TotalAnnualTechnologyActivityByMode",
                ("RE1", WOOD_POWER, 1, year),
            )
            modeled_mwh = (bagasse + wood) / 0.0000036
            error = 100 * (modeled_mwh - IPP_MWH[year]) / IPP_MWH[year]
            errors.append(abs(error))
            year_rows[year] = {
                "observed_mwh": IPP_MWH[year],
                "modeled_mwh": modeled_mwh,
                "percent_error": error,
            }
        fit[label] = {
            "mape_percent": sum(errors) / len(errors),
            "years": year_rows,
        }
    check(
        "Held-out 2023-2024 aggregate IPP generation stays within 15% MAPE",
        fit["validation"]["mape_percent"] <= 15.0,
        fit,
        "results.txt; EFL 2024 Annual Report",
    )

    proxy_config = read_json(
        PACKAGE / "muio" / "reserve_margin_proxy_config.json"
    )
    validate_config(proxy_config)
    case_data = load_case(physical_case)
    expected_proxy_data = expected_proxy(case_data, proxy_config)
    proxy = check_proxy(
        physical_case,
        case_data,
        proxy_config,
        expected_proxy_data,
        tolerance=1e-10,
    )
    check(
        "Reserve-margin proxy is current after the biomass split",
        proxy["status"] == "CURRENT" and proxy["mismatch_count"] == 0,
        {
            "status": proxy["status"],
            "mismatch_count": proxy["mismatch_count"],
        },
        "reserve_margin_proxy.json; reserve_margin_proxy_config.json",
    )

    source_mtime = max(
        path.stat().st_mtime
        for path in physical_case.glob("*.json")
        if path.is_file()
    )
    result_paths = [
        physical_run / "data.txt",
        physical_run / "data_processed.txt",
        physical_run / "lp.lp",
        physical_run / "results.txt",
        physical_run / "csv" / "ObjectiveValue.csv",
    ]
    freshness = min(path.stat().st_mtime for path in result_paths)
    check(
        "Physical results postdate the disposable source and identify the selected run",
        freshness >= source_mtime
        and args.physical_run in str(physical_run)
        and args.physical_case in str(physical_case),
        {
            "case": args.physical_case,
            "run": args.physical_run,
            "result_timestamp": datetime.fromtimestamp(
                freshness, timezone.utc
            ).isoformat(),
            "source_timestamp": datetime.fromtimestamp(
                source_mtime, timezone.utc
            ).isoformat(),
        },
        "MUIO source and run artifact timestamps",
    )

    failed = [item for item in checks if item["status"] == "FAIL"]
    summary = {
        "schema_version": 1,
        "phase": "1D cane-bagasse-electricity",
        "status": "PASS" if not failed else "FAIL",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "cases": {
            "baseline": {
                "case": args.baseline_case,
                "run": args.baseline_run,
            },
            "accounting": {
                "case": args.accounting_case,
                "run": args.accounting_run,
            },
            "physical": {
                "case": args.physical_case,
                "run": args.physical_run,
            },
        },
        "objectives": {
            "baseline": baseline_obj,
            "accounting": accounting_obj,
            "physical": physical_obj,
            "accounting_difference_percent": accounting_pct,
            "physical_difference_percent": physical_pct,
        },
        "checks": checks,
        "failed_checks": len(failed),
        "artifacts": {
            str(path.relative_to(physical_case)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in result_paths
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
