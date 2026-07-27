#!/usr/bin/env python3
"""Validate Fiji Phase 1C accounting parity and bottom-up projections."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
DEFAULT_MUIOGO = Path(__file__).resolve().parents[3] / "MUIOGO"
DEFAULT_OUTPUT = (
    PACKAGE
    / "diagnostics"
    / "calibration_runs"
    / "phase1c"
    / "validation_summary.json"
)
HISTORICAL_YEARS = tuple(range(2020, 2025))
DEMAND_COMMODITIES = (
    "ELCFJIXX02",
    "COMELCFJIXX02",
    "INDELCFJIXX02",
    "RESELCFJIXX02",
)
ADAPTER_BY_COMMODITY = {
    "COMELCFJIXX02": "DEMCOMELCFJIXX02",
    "INDELCFJIXX02": "DEMINDELCFJIXX02",
    "RESELCFJIXX02": "DEMRESELCFJIXX02",
}

sys.path.insert(0, str(PACKAGE / "scripts"))
from apply_fiji_phase1c_bottom_up_demand import (  # noqa: E402
    bottom_up_projection,
    historical_rows,
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
    data: dict[str, Any],
    parameter: str,
    **identifiers: Any,
) -> dict[str, Any]:
    matches = [
        row
        for row in data[parameter]["SC_0"]
        if all(row.get(key) == value for key, value in identifiers.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {identifiers}, "
            f"found {len(matches)}"
        )
    return matches[0]


def objective(run: Path) -> float:
    return float(rows(run / "csv" / "ObjectiveValue.csv")[0]["ObjectiveValue"])


def result_row(path: Path, symbol: str, indices: list[Any]) -> tuple[float, float]:
    label = f"{symbol}({','.join(str(item) for item in indices)})"
    match = re.search(
        rf"^\s*\d+\s+{re.escape(label)}\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$",
        path.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Result row not found: {label}")
    return float(match.group(1)), float(match.group(2))


def table_map(
    path: Path,
    keys: tuple[str, ...],
    value_field: str | None = None,
) -> dict[tuple[str, ...], float]:
    data = rows(path)
    if not data:
        return {}
    value_field = value_field or list(data[0])[-1]
    return {
        tuple(row[key] for key in keys): float(row[value_field])
        for row in data
    }


def compare_maps(
    left: dict[tuple[str, ...], float],
    right: dict[tuple[str, ...], float],
    *,
    include: Any = lambda key: True,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    keys = {key for key in left.keys() | right.keys() if include(key)}
    differences = {
        key: (left.get(key, 0.0), right.get(key, 0.0))
        for key in keys
        if not math.isclose(
            left.get(key, 0.0),
            right.get(key, 0.0),
            rel_tol=0,
            abs_tol=tolerance,
        )
    }
    maximum = max(
        (
            abs(left.get(key, 0.0) - right.get(key, 0.0))
            for key in keys
        ),
        default=0.0,
    )
    return {
        "compared_rows": len(keys),
        "changed_rows": len(differences),
        "maximum_absolute_difference": maximum,
        "examples": [
            {"key": key, "left": values[0], "right": values[1]}
            for key, values in sorted(differences.items())[:10]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muiogo-root", type=Path, default=DEFAULT_MUIOGO
    )
    parser.add_argument(
        "--baseline-case", default="Fiji_v2_Phase1B_Test"
    )
    parser.add_argument(
        "--baseline-run", default="Phase1B_Public_Water"
    )
    parser.add_argument(
        "--accounting-case", default="Fiji_v2_Phase1C_Accounting_Test"
    )
    parser.add_argument(
        "--accounting-run", default="Phase1C_Accounting"
    )
    parser.add_argument(
        "--bottom-up-case", default="Fiji_v2"
    )
    parser.add_argument(
        "--bottom-up-run", default="Phase1C_BottomUp"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    muiogo = args.muiogo_root.resolve()
    storage = muiogo / "WebAPP" / "DataStorage"
    baseline_case = storage / args.baseline_case
    baseline_run = baseline_case / "res" / args.baseline_run
    accounting_case = storage / args.accounting_case
    accounting_run = accounting_case / "res" / args.accounting_run
    bottom_up_case = storage / args.bottom_up_case
    bottom_up_run = bottom_up_case / "res" / args.bottom_up_run
    output = args.output.resolve()

    required = []
    for case, run in (
        (baseline_case, baseline_run),
        (accounting_case, accounting_run),
        (bottom_up_case, bottom_up_run),
    ):
        required.extend(
            [
                case / "genData.json",
                case / "RYC.json",
                case / "RYCTs.json",
                case / "RYTM.json",
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
        raise FileNotFoundError(
            "Missing required artifacts: " + "; ".join(missing)
        )

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

    gen_data = read_json(bottom_up_case / "genData.json")
    years = [int(year) for year in gen_data["osy-years"]]
    comm_ids = {
        str(item["Comm"]): str(item["CommId"])
        for item in gen_data["osy-comm"]
    }
    tech_ids = {
        str(item["Tech"]): str(item["TechId"])
        for item in gen_data["osy-tech"]
    }
    expected = bottom_up_projection(years)
    history = historical_rows()

    accounting_ryc = read_json(accounting_case / "RYC.json")
    bottom_up_ryc = read_json(bottom_up_case / "RYC.json")
    historical_reconciliation: dict[int, Any] = {}
    history_pass = True
    for year in HISTORICAL_YEARS:
        actual = {
            commodity: float(
                parameter_row(
                    bottom_up_ryc,
                    "SAD",
                    CommId=comm_ids[commodity],
                )[str(year)]
            )
            for commodity in DEMAND_COMMODITIES
        }
        accounting_actual = {
            commodity: float(
                parameter_row(
                    accounting_ryc,
                    "SAD",
                    CommId=comm_ids[commodity],
                )[str(year)]
            )
            for commodity in DEMAND_COMMODITIES
        }
        gross = sum(actual.values())
        expected_gross = history[year][
            "model_gross_grid_supply_requirement_pj"
        ]
        history_pass &= all(
            math.isclose(
                actual[commodity],
                expected[year][commodity],
                rel_tol=0,
                abs_tol=1e-10,
            )
            for commodity in DEMAND_COMMODITIES
        )
        history_pass &= actual == accounting_actual
        history_pass &= math.isclose(
            gross, expected_gross, rel_tol=0, abs_tol=1e-10
        )
        historical_reconciliation[year] = {
            "components_pj": actual,
            "gross_pj": gross,
            "evidence_gross_pj": expected_gross,
            "difference_pj": gross - expected_gross,
        }
    check(
        "Observed 2020-2024 sector split reconciles exactly in both checkpoints",
        history_pass,
        historical_reconciliation,
        "RYC.json; FBoS Energy Account extract",
    )

    projection_values: dict[int, Any] = {}
    projection_pass = True
    for year in years:
        actual = {
            commodity: float(
                parameter_row(
                    bottom_up_ryc,
                    "SAD",
                    CommId=comm_ids[commodity],
                )[str(year)]
            )
            for commodity in DEMAND_COMMODITIES
        }
        projection_pass &= all(
            math.isclose(
                actual[commodity],
                expected[year][commodity],
                rel_tol=0,
                abs_tol=1e-10,
            )
            for commodity in DEMAND_COMMODITIES
        )
        if year in {2025, 2030, 2040, 2050}:
            projection_values[year] = {
                "components_pj": actual,
                "gross_pj": sum(actual.values()),
                "residential_driver_index": expected[year][
                    "residential_driver_index_2024_1"
                ],
            }
    check(
        "2025-2050 bottom-up demand matches the documented generator",
        projection_pass,
        projection_values,
        "RYC.json; apply_fiji_phase1c_bottom_up_demand.py",
    )

    accounting_future_pass = True
    accounting_future: dict[int, Any] = {}
    baseline_ryc = read_json(baseline_case / "RYC.json")
    for year in range(2025, 2051):
        inherited = float(
            parameter_row(
                baseline_ryc,
                "SAD",
                CommId=comm_ids["ELCFJIXX02"],
            )[str(year)]
        )
        actual = {
            commodity: float(
                parameter_row(
                    accounting_ryc,
                    "SAD",
                    CommId=comm_ids[commodity],
                )[str(year)]
            )
            for commodity in DEMAND_COMMODITIES
        }
        accounting_future_pass &= math.isclose(
            actual["ELCFJIXX02"], inherited, rel_tol=0, abs_tol=1e-12
        )
        accounting_future_pass &= all(
            actual[commodity] == 0.0
            for commodity in DEMAND_COMMODITIES[1:]
        )
        if year in {2025, 2050}:
            accounting_future[year] = actual
    check(
        "Accounting checkpoint leaves the inherited future path unchanged",
        accounting_future_pass,
        accounting_future,
        "Phase 1B and accounting RYC.json",
    )

    profile_pass = True
    profile_summary: dict[str, Any] = {}
    bottom_up_profiles = read_json(bottom_up_case / "RYCTs.json")
    for commodity in DEMAND_COMMODITIES:
        sums: dict[int, float] = {}
        for year in years:
            total = 0.0
            for timeslice in gen_data["osy-ts"]:
                row = parameter_row(
                    bottom_up_profiles,
                    "SDP",
                    CommId=comm_ids[commodity],
                    TsId=str(timeslice["TsId"]),
                )
                total += float(row[str(year)])
            sums[year] = total
            profile_pass &= math.isclose(
                total, 1.0, rel_tol=0, abs_tol=1e-12
            )
        profile_summary[commodity] = {
            "minimum_sum": min(sums.values()),
            "maximum_sum": max(sums.values()),
        }
    check(
        "Every positive component has a normalized demand profile",
        profile_pass,
        profile_summary,
        "RYCTs.json",
    )

    rytm = read_json(bottom_up_case / "RYTM.json")
    zero_cost_pass = True
    zero_cost: dict[str, Any] = {}
    for technology in ADAPTER_BY_COMMODITY.values():
        row = parameter_row(
            rytm,
            "VC",
            TechId=tech_ids[technology],
            MoId=1,
        )
        values = [float(row[str(year)]) for year in years]
        zero_cost[technology] = {
            "minimum": min(values),
            "maximum": max(values),
        }
        zero_cost_pass &= all(value == 0.0 for value in values)
    check(
        "Sector electricity adapters are zero-cost accounting routes",
        zero_cost_pass,
        zero_cost,
        "RYTM.json VariableCost mode 1",
    )

    generated = (bottom_up_run / "data_processed.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    mapping_checks = {
        technology: (
            f"set MODEperTECHNOLOGY[{technology}]:= 1;" in generated
        )
        for technology in ADAPTER_BY_COMMODITY.values()
    }
    elc_consumers = re.search(
        r"set MODExTECHNOLOGYperFUELin\[ELCFJIXX02\]:=(.*);",
        generated,
    )
    mapping_checks["ELCFJIXX02 consumers"] = (
        elc_consumers is not None
        and all(
            technology in elc_consumers.group(1)
            for technology in ADAPTER_BY_COMMODITY.values()
        )
    )
    check(
        "Generated derived sets include all three sector adapters",
        all(mapping_checks.values()),
        mapping_checks,
        "data_processed.txt",
    )

    solve_summary: dict[str, Any] = {}
    solve_pass = True
    for label, case, run in (
        ("accounting", accounting_case, accounting_run),
        ("bottom_up", bottom_up_case, bottom_up_run),
    ):
        first_line = (run / "results.txt").read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()[0]
        sizes = {
            name: (run / name).stat().st_size
            for name in ("data.txt", "data_processed.txt", "lp.lp", "results.txt")
        }
        source_time = max(
            path.stat().st_mtime
            for path in (
                case / "genData.json",
                case / "RYC.json",
                case / "RYCTs.json",
                case / "RYTM.json",
            )
        )
        result_time = (run / "results.txt").stat().st_mtime
        case_name = read_json(case / "genData.json")["osy-casename"]
        current = (
            first_line.startswith("Optimal")
            and all(size > 0 for size in sizes.values())
            and result_time >= source_time
            and case_name == case.name
        )
        solve_pass &= current
        solve_summary[label] = {
            "solver": first_line,
            "artifact_bytes": sizes,
            "case_name": case_name,
            "source_latest_utc": datetime.fromtimestamp(
                source_time, tz=timezone.utc
            ).isoformat(),
            "result_utc": datetime.fromtimestamp(
                result_time, tz=timezone.utc
            ).isoformat(),
        }
    check(
        "Both disposable cases passed generation, preprocessing, GLPK and CBC",
        solve_pass,
        solve_summary,
        "MUIO DataFile generation/run chain",
    )

    proxy_config = read_json(
        PACKAGE / "muio" / "reserve_margin_proxy_config.json"
    )
    validate_config(proxy_config)
    proxy_summary: dict[str, Any] = {}
    proxy_pass = True
    for label, case in (
        ("accounting", accounting_case),
        ("bottom_up", bottom_up_case),
    ):
        data = load_case(case)
        proxy_expected = expected_proxy(data, proxy_config)
        report = check_proxy(
            case, data, proxy_config, proxy_expected, tolerance=1e-10
        )
        proxy_summary[label] = {
            "status": report["status"],
            "mismatches": report["mismatch_count"],
            "fingerprint": proxy_expected[
                "input_fingerprint_sha256"
            ],
        }
        proxy_pass &= report["status"] == "CURRENT"
    check(
        "Aggregate four-commodity reserve proxy is current",
        proxy_pass,
        proxy_summary,
        "reserve_margin_proxy.json and demand/profile inputs",
    )

    activity_file = "TotalAnnualTechnologyActivityByMode.csv"
    baseline_activity = table_map(
        baseline_run / "csv" / activity_file, ("t", "m", "y")
    )
    accounting_activity = table_map(
        accounting_run / "csv" / activity_file, ("t", "m", "y")
    )
    nonadapter_parity = compare_maps(
        baseline_activity,
        accounting_activity,
        include=lambda key: key[0] not in ADAPTER_BY_COMMODITY.values(),
        tolerance=1e-8,
    )
    check(
        "Accounting split leaves all non-adapter activity unchanged",
        nonadapter_parity["changed_rows"] == 0,
        nonadapter_parity,
        "Phase 1B and Phase 1C accounting activity CSVs",
    )

    bottom_up_activity = table_map(
        bottom_up_run / "csv" / activity_file, ("t", "m", "y")
    )
    historical_activity = compare_maps(
        accounting_activity,
        bottom_up_activity,
        include=lambda key: int(key[2]) in HISTORICAL_YEARS,
        tolerance=1e-8,
    )
    check(
        "Bottom-up case preserves the complete historical activity solution",
        historical_activity["changed_rows"] == 0,
        historical_activity,
        "Accounting and bottom-up activity CSVs, 2020-2024",
    )

    historical_capacity = compare_maps(
        table_map(
            accounting_run / "csv" / "TotalCapacityAnnual.csv",
            ("t", "y"),
        ),
        table_map(
            bottom_up_run / "csv" / "TotalCapacityAnnual.csv",
            ("t", "y"),
        ),
        include=lambda key: int(key[1]) in HISTORICAL_YEARS,
        tolerance=1e-8,
    )
    historical_emissions = compare_maps(
        table_map(
            accounting_run / "csv" / "AnnualTechnologyEmission.csv",
            ("t", "e", "y"),
        ),
        table_map(
            bottom_up_run / "csv" / "AnnualTechnologyEmission.csv",
            ("t", "e", "y"),
        ),
        include=lambda key: int(key[2]) in HISTORICAL_YEARS,
        tolerance=1e-8,
    )
    check(
        "Historical capacities and emissions remain unchanged",
        historical_capacity["changed_rows"] == 0
        and historical_emissions["changed_rows"] == 0,
        {
            "capacity": historical_capacity,
            "emissions": historical_emissions,
        },
        "Accounting and bottom-up capacity/emission CSVs, 2020-2024",
    )

    result_path = bottom_up_run / "results.txt"
    solved_closure: dict[int, Any] = {}
    closure_pass = True
    for year in years:
        components: dict[str, Any] = {}
        for commodity, technology in ADAPTER_BY_COMMODITY.items():
            activity, activity_dual = result_row(
                result_path,
                "TotalAnnualTechnologyActivityByMode",
                ["RE1", technology, 1, year],
            )
            balance, balance_dual = result_row(
                result_path,
                "EBb4_EnergyBalanceEachYear4",
                ["RE1", commodity, year],
            )
            target = expected[year][commodity]
            closure_pass &= (
                math.isclose(activity, target, rel_tol=0, abs_tol=1e-6)
                and math.isclose(balance, target, rel_tol=0, abs_tol=1e-6)
                and activity_dual == 0.0
                and balance_dual == 0.0
            )
            components[commodity] = {
                "activity_pj": activity,
                "balance_pj": balance,
                "dual": balance_dual,
            }
        transmission, transmission_dual = result_row(
            result_path,
            "TotalAnnualTechnologyActivityByMode",
            ["RE1", "PWRTRNFJIXX", 1, year],
        )
        gross = expected[year]["gross_grid_requirement_pj"]
        closure_pass &= (
            math.isclose(transmission, gross, rel_tol=0, abs_tol=1e-6)
            and transmission_dual == 0.0
        )
        if year in {2020, 2024, 2025, 2050}:
            solved_closure[year] = {
                "components": components,
                "transmission_activity_pj": transmission,
                "target_gross_pj": gross,
            }
    check(
        "Solved sector activities and gross grid transmission close annually",
        closure_pass,
        solved_closure,
        "results.txt; sector demands and EBb4 balances",
    )

    baseline_objective = objective(baseline_run)
    accounting_objective = objective(accounting_run)
    bottom_up_objective = objective(bottom_up_run)
    accounting_difference = accounting_objective - baseline_objective
    bottom_up_difference = bottom_up_objective - baseline_objective
    check(
        "Accounting-only objective is identical to Phase 1B",
        math.isclose(
            accounting_objective,
            baseline_objective,
            rel_tol=0,
            abs_tol=1e-7,
        ),
        {
            "phase1b": baseline_objective,
            "accounting": accounting_objective,
            "difference": accounting_difference,
        },
        "ObjectiveValue.csv",
    )
    check(
        "Bottom-up objective difference is reported against Phase 1B",
        math.isfinite(bottom_up_objective),
        {
            "phase1b": baseline_objective,
            "bottom_up": bottom_up_objective,
            "difference": bottom_up_difference,
            "percent_change": (
                100.0 * bottom_up_difference / abs(baseline_objective)
            ),
        },
        "ObjectiveValue.csv",
    )

    inherited_2050 = float(
        parameter_row(
            baseline_ryc,
            "SAD",
            CommId=comm_ids["ELCFJIXX02"],
        )["2050"]
    )
    bottom_up_2050 = expected[2050]["gross_grid_requirement_pj"]
    check(
        "Projection divergence is explicit rather than a frozen sector share",
        bottom_up_2050 < inherited_2050
        and all(expected[2050][commodity] > 0 for commodity in DEMAND_COMMODITIES),
        {
            "bottom_up_2050_pj": bottom_up_2050,
            "inherited_2050_pj": inherited_2050,
            "difference_pj": bottom_up_2050 - inherited_2050,
            "percent_difference": (
                100.0 * (bottom_up_2050 - inherited_2050) / inherited_2050
            ),
            "sector_components_pj": {
                commodity: expected[2050][commodity]
                for commodity in DEMAND_COMMODITIES
            },
        },
        "Bottom-up generator and Phase 1B RYC.json",
    )

    failed = [item for item in checks if item["status"] == "FAIL"]
    report = {
        "phase": "1C sector electricity accounting and bottom-up demand",
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "cases": {
            "baseline": {
                "case": baseline_case.name,
                "run": baseline_run.name,
            },
            "accounting": {
                "case": accounting_case.name,
                "run": accounting_run.name,
            },
            "bottom_up": {
                "case": bottom_up_case.name,
                "run": bottom_up_run.name,
            },
        },
        "status": "PASS" if not failed else "FAIL",
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "checks": checks,
        "artifact_sha256": {
            f"{label}/{name}": sha256(run / name)
            for label, run in (
                ("accounting", accounting_run),
                ("bottom_up", bottom_up_run),
            )
            for name in ("data.txt", "data_processed.txt", "lp.lp", "results.txt")
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
