#!/usr/bin/env python3
"""Compare solved Fiji_v2.7 Fisheries candidate with the fresh Fiji_v2.6 control."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
CONTROL_REPORT = REPO / "tmp" / "fiji-v27-fisheries" / "control_report.json"
CANDIDATE_REPORT = REPO / "docs" / "Fiji_v2.7_Fisheries" / "validation" / "candidate_solve.json"
CONTROL_RESULTS = (
    REPO
    / "WebAPP"
    / "DataStorage"
    / ".Fiji_v2.6-fisheries-control-20260803T163026Z"
    / "res"
    / "Environmental_Accounting_v2.6"
    / "results.txt"
)
CANDIDATE_RESULTS = (
    REPO
    / "WebAPP"
    / "DataStorage"
    / ".Fiji_v2.7-fisheries-candidate"
    / "res"
    / "Fisheries_v2.7"
    / "results.txt"
)
ROW_PATTERN = re.compile(
    r"^\s*\d+\s+(\S+\([^)]*\))\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$"
)
FSH_TECHS = (
    "FSHCAPDSL",
    "FSHCAPELE",
    "FSHAQDSL",
    "FSHAQELE",
    "FSHPOSTDSL",
    "FSHPOSTELE",
    "FSHPOSTSOL",
)
FSH_SERVICES = ("FSHCAPSERV", "FSHAQSERV", "FSHPOSTSERV")
YEARS = [str(year) for year in range(2020, 2051)]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_results(path: Path) -> dict[str, tuple[float, float]]:
    rows: dict[str, tuple[float, float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_PATTERN.match(line)
        if match:
            rows[match.group(1)] = (float(match.group(2)), float(match.group(3)))
    return rows


def function_name(key: str) -> str:
    return key.split("(", 1)[0]


def args(key: str) -> list[str]:
    return key.split("(", 1)[1].rstrip(")").split(",")


def value(rows: dict[str, tuple[float, float]], key: str) -> float:
    if key not in rows:
        raise KeyError(key)
    return rows[key][0]


def fisheries_outputs(rows: dict[str, tuple[float, float]]) -> dict[str, Any]:
    activity: dict[str, dict[str, float]] = {tech: {} for tech in FSH_TECHS}
    new_capacity: dict[str, dict[str, float]] = {tech: {} for tech in FSH_TECHS}
    total_capacity: dict[str, dict[str, float]] = {tech: {} for tech in FSH_TECHS}
    emissions: dict[str, dict[str, float]] = {tech: {} for tech in FSH_TECHS}
    for tech in FSH_TECHS:
        for year in YEARS:
            activity[tech][year] = value(
                rows, f"TotalAnnualTechnologyActivityByMode(RE1,{tech},1,{year})"
            )
            new_capacity[tech][year] = value(rows, f"NewCapacity(RE1,{tech},{year})")
            total_capacity[tech][year] = value(rows, f"TotalCapacityAnnual(RE1,{tech},{year})")
            emission_key = f"AnnualTechnologyEmission(RE1,{tech},CO2FJI,{year})"
            emissions[tech][year] = rows.get(emission_key, (0.0, 0.0))[0]

    service_balance: dict[str, dict[str, dict[str, float]]] = {}
    for service in FSH_SERVICES:
        service_balance[service] = {}
        for year in YEARS:
            key = f"EBb4_EnergyBalanceEachYear4_ICR(RE1,{service},{year})"
            activity_value, dual = rows[key]
            production = sum(
                activity[tech][year]
                for tech in FSH_TECHS
                if (service == "FSHCAPSERV" and tech.startswith("FSHCAP"))
                or (service == "FSHAQSERV" and tech.startswith("FSHAQ"))
                or (service == "FSHPOSTSERV" and tech.startswith("FSHPOST"))
            )
            service_balance[service][year] = {
                "constraint_activity": activity_value,
                "technology_output": production,
                "residual": production - activity_value,
                "dual": dual,
            }
    adjacent = {}
    for tech in FSH_TECHS:
        adjacent[tech] = {
            year: activity[tech][year] - activity[tech][str(int(year) - 1)]
            for year in YEARS[1:]
            if abs(activity[tech][year] - activity[tech][str(int(year) - 1)]) > 1e-10
        }
    return {
        "activity": activity,
        "new_capacity": new_capacity,
        "total_capacity": total_capacity,
        "direct_co2": emissions,
        "service_balance_constraints": service_balance,
        "adjacent_year_activity_changes": adjacent,
    }


def common_changes(
    control: dict[str, tuple[float, float]], candidate: dict[str, tuple[float, float]]
) -> dict[str, Any]:
    by_function: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"count": 0, "max_abs_primal_delta": 0.0, "max_abs_dual_delta": 0.0}
    )
    changed: list[dict[str, Any]] = []
    dual_only_changes = 0
    for key in sorted(set(control) & set(candidate)):
        control_primal, control_dual = control[key]
        candidate_primal, candidate_dual = candidate[key]
        primal_delta = candidate_primal - control_primal
        dual_delta = candidate_dual - control_dual
        tolerance = 1e-7 + 1e-7 * max(abs(control_primal), abs(candidate_primal))
        primal_changed = abs(primal_delta) > tolerance
        dual_changed = abs(dual_delta) > tolerance
        if not primal_changed and not dual_changed:
            continue
        function = function_name(key)
        summary = by_function[function]
        summary["count"] = int(summary["count"]) + 1
        summary["max_abs_primal_delta"] = max(float(summary["max_abs_primal_delta"]), abs(primal_delta))
        summary["max_abs_dual_delta"] = max(float(summary["max_abs_dual_delta"]), abs(dual_delta))
        if primal_changed:
            changed.append(
                {
                    "key": key,
                    "control_primal": control_primal,
                    "candidate_primal": candidate_primal,
                    "primal_delta": primal_delta,
                    "control_dual_or_reduced_cost": control_dual,
                    "candidate_dual_or_reduced_cost": candidate_dual,
                    "dual_delta": dual_delta,
                }
            )
        elif dual_changed:
            dual_only_changes += 1
    meaningful_functions = {
        "AnnualFixedOperatingCost",
        "AnnualTechnologyEmission",
        "AnnualVariableOperatingCost",
        "CapitalInvestment",
        "Demand",
        "EBb4_EnergyBalanceEachYear4_ICR",
        "NewCapacity",
        "TotalAnnualTechnologyActivityByMode",
        "TotalCapacityAnnual",
        "UDC1_UserDefinedConstraintInequality",
        "UDC2_UserDefinedConstraintEquality",
    }
    meaningful = [
        item
        for item in changed
        if function_name(item["key"]) in meaningful_functions
        and max(abs(item["control_primal"]), abs(item["candidate_primal"])) < 900000
    ]
    top_primal = sorted(meaningful, key=lambda item: abs(item["primal_delta"]), reverse=True)[:30]
    affected_tokens = (
        "FSH",
        "AGRDSL",
        "SRVAGR",
        "INDDSL",
        "INDELC",
        "SRVINDHEAT",
        "PUBWAT",
        "DSL",
        "ELCFJIXX",
        "PWR",
        "CO2FJI",
    )
    outside = [
        item for item in meaningful if not any(token in item["key"] for token in affected_tokens)
    ]
    top_outside = sorted(outside, key=lambda item: abs(item["primal_delta"]), reverse=True)[:30]
    return {
        "common_rows_compared": len(set(control) & set(candidate)),
        "primal_changed_rows_above_tolerance": len(changed),
        "dual_only_changed_rows_above_tolerance": dual_only_changes,
        "changed_by_function": dict(sorted(by_function.items())),
        "top_meaningful_primal_changes": top_primal,
        "top_meaningful_changes_outside_declared_energy_water_boundary": top_outside,
        "interpretation": (
            "Primal comparisons exclude 999999 host-open auxiliary capacity/slack values. "
            "Dual-only changes are counted because alternate optimal bases can change duals "
            "without changing physical outcomes."
        ),
    }


def exact_accounts(rows: dict[str, tuple[float, float]]) -> dict[str, Any]:
    land = []
    for year in YEARS:
        key = f"UDC2_UserDefinedConstraintEquality(RE1,ENV_LAND_CLOSURE,{year})"
        primal, dual = rows[key]
        land.append({"year": year, "residual": primal, "dual": dual})
    return {
        "land_closure_max_abs_residual": max(abs(item["residual"]) for item in land),
        "land_closure": land,
    }


def bounded_objective(path: Path) -> float:
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.search(r"objective value\s+([-+0-9.eE]+)", first_line, re.IGNORECASE)
    if not match:
        raise ValueError(f"cannot parse objective from {path}")
    return float(match.group(1))


def compare() -> dict[str, Any]:
    control_report = read_json(CONTROL_REPORT)
    candidate_report = read_json(CANDIDATE_REPORT)
    control = parse_results(CONTROL_RESULTS)
    candidate = parse_results(CANDIDATE_RESULTS)
    objective_delta = candidate_report["objective"] - control_report["objective"]
    fisheries = fisheries_outputs(candidate)
    candidate_path = CANDIDATE_RESULTS.parents[2]
    bounded_path = CANDIDATE_RESULTS.parent / "bounded_results.txt"
    bounded = bounded_objective(bounded_path)
    timestamps = {
        path.name: path.stat().st_mtime
        for path in (
            candidate_path / "genData.json",
            CANDIDATE_RESULTS.parent / "data.txt",
            CANDIDATE_RESULTS.parent / "data_processed.txt",
            CANDIDATE_RESULTS.parent / "lp.lp",
            CANDIDATE_RESULTS,
        )
    }
    matrix_control = {"rows": 162542, "columns": 124829, "nonzeros": 677671}
    matrix_candidate = {"rows": 169810, "columns": 130447, "nonzeros": 719047}
    report = {
        "status": "pass",
        "identity": {
            "control_case": control_report["case"],
            "control_identity": control_report["source_case_identity"],
            "candidate_case": candidate_report["case"],
            "candidate_identity": candidate_report["case_identity"],
            "control_result": str(CONTROL_RESULTS.resolve()),
            "candidate_result": str(CANDIDATE_RESULTS.resolve()),
            "timestamps_epoch": timestamps,
            "timestamps_ordered": timestamps["genData.json"] <= timestamps["data.txt"] <= timestamps["results.txt"],
        },
        "solver": {
            "control_status": control_report["status"],
            "candidate_status": candidate_report["status"],
            "control_objective": control_report["objective"],
            "candidate_objective": candidate_report["objective"],
            "bounded_candidate_objective": bounded,
            "bounded_matches_normal": math.isclose(bounded, candidate_report["objective"], abs_tol=1e-8),
            "objective_delta": objective_delta,
            "objective_percent_change": 100 * objective_delta / control_report["objective"],
            "control_elapsed_seconds": control_report["elapsed_seconds"],
            "candidate_elapsed_seconds": candidate_report["elapsed_seconds"],
            "runtime_percent_change": 100
            * (candidate_report["elapsed_seconds"] - control_report["elapsed_seconds"])
            / control_report["elapsed_seconds"],
            "control_matrix": matrix_control,
            "candidate_matrix": matrix_candidate,
            "matrix_delta": {
                field: matrix_candidate[field] - matrix_control[field]
                for field in ("rows", "columns", "nonzeros")
            },
        },
        "fisheries": fisheries,
        "existing_model_comparison": common_changes(control, candidate),
        "constraint_residuals_and_duals": exact_accounts(candidate),
    }
    if not report["identity"]["timestamps_ordered"]:
        report["status"] = "fail"
    if not report["solver"]["bounded_matches_normal"]:
        report["status"] = "fail"
    if report["constraint_residuals_and_duals"]["land_closure_max_abs_residual"] > 1e-8:
        report["status"] = "fail"
    max_service_residual = max(
        abs(item["residual"])
        for service in fisheries["service_balance_constraints"].values()
        for item in service.values()
    )
    report["constraint_residuals_and_duals"]["fisheries_service_max_abs_residual"] = max_service_residual
    if max_service_residual > 1e-7:
        report["status"] = "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare()
    except Exception as error:
        report = {"status": "fail", "error": str(error)}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
