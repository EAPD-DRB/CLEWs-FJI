#!/usr/bin/env python3
"""Validate removal of Fiji Phase 1D's inactive aggregate biomass shell."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
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
    / "legacy_removal_validation_summary.json"
)
OLD_POWER = "PWRBIOFJIXX01"
OLD_ID = "TEC_w665d"
ZERO_TOLERANCE = 1e-12
PARITY_TOLERANCE = 1e-8
AGGREGATE_TOLERANCE = 1e-6
PHASE1D_TECHNOLOGIES = {
    "SGCMILLFJI",
    "PWRBAGFJIXX01",
    "PWRWODFJIXX01",
}
LAND_MODE_SUBSTITUTES = {
    "LNDAGRFJIC01",
    "LNDAGRFJIC02",
    "LNDAGRFJIC04",
}
POWER_ACTIVITY_SUBSTITUTES = {
    "PWRHYDFJIXX01",
    "PWRSPVFJIXX01",
    "PWRWONFJIXX01",
}
RENEWABLE_ACCOUNTING_SUBSTITUTES = {
    "RNWHYDFJIXX",
    "RNWSPVFJIXX",
    "RNWWONFJIXX",
}
EXPECTED_ALTERNATE_TECHNOLOGIES = (
    LAND_MODE_SUBSTITUTES
    | POWER_ACTIVITY_SUBSTITUTES
    | RENEWABLE_ACCOUNTING_SUBSTITUTES
)
PHASE1D_COMMODITIES = {
    "CRPSGC",
    "SGCPROCFJI",
    "BAGEXPFJI",
    "BIOFJIXX",
    "ELCFJIXX01",
}
EXPECTED_WATER_SURPLUS_CHANGES = {
    ("WTREVTFJI", "2044"),
    ("WTREVTFJI", "2050"),
    ("WTRGRCFJI", "2044"),
    ("WTRGRCFJI", "2050"),
    ("WTRSURFJI", "2044"),
    ("WTRSURFJI", "2050"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate(run: Path, filename: str) -> Path:
    matches = sorted(run.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"{filename} not found below {run}")
    return matches[0]


def objective(run: Path) -> float:
    return float(rows(locate(run, "ObjectiveValue.csv"))[0]["ObjectiveValue"])


def table_map(
    run: Path,
    filename: str,
    keys: tuple[str, ...],
    value: str,
) -> dict[tuple[str, ...], float]:
    result: dict[tuple[str, ...], float] = {}
    for row in rows(locate(run, filename)):
        key = tuple(row[item] for item in keys)
        result[key] = result.get(key, 0.0) + float(row[value])
    return result


def compare_maps(
    control: dict[tuple[str, ...], float],
    candidate: dict[tuple[str, ...], float],
    *,
    technology_position: int | None = None,
    tolerance: float = PARITY_TOLERANCE,
) -> dict[str, Any]:
    keys = control.keys() | candidate.keys()
    if technology_position is not None:
        keys = {
            key
            for key in keys
            if key[technology_position] != OLD_POWER
        }
    differences = [
        {
            "key": key,
            "control": control.get(key, 0.0),
            "candidate": candidate.get(key, 0.0),
            "difference": candidate.get(key, 0.0)
            - control.get(key, 0.0),
        }
        for key in keys
        if not math.isclose(
            control.get(key, 0.0),
            candidate.get(key, 0.0),
            rel_tol=0,
            abs_tol=tolerance,
        )
    ]
    return {
        "rows_compared": len(keys),
        "rows_changed": len(differences),
        "maximum_absolute_difference": max(
            (abs(item["difference"]) for item in differences),
            default=0.0,
        ),
        "examples": sorted(
            differences, key=lambda item: item["key"]
        )[:10],
        "changed_technologies": sorted(
            {
                item["key"][technology_position]
                for item in differences
            }
        )
        if technology_position is not None
        else [],
        "tolerance": tolerance,
    }


_DROP = object()


def without_legacy(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("TechId") == OLD_ID:
            return _DROP
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == OLD_ID:
                continue
            cleaned = without_legacy(item)
            if cleaned is not _DROP:
                result[key] = cleaned
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            cleaned = without_legacy(item)
            if cleaned is not _DROP:
                result.append(cleaned)
        return result
    return value


def result_value(
    results: Path, symbol: str, indices: tuple[Any, ...]
) -> tuple[float, float]:
    label = f"{symbol}({','.join(str(value) for value in indices)})"
    match = re.search(
        rf"^\s*\d+\s+{re.escape(label)}\s+"
        r"([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$",
        results.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Missing result row: {label}")
    return float(match.group(1)), float(match.group(2))


def solver_table(
    results: Path, symbol: str
) -> dict[tuple[str, ...], tuple[float, float]]:
    """Return full-precision primal values and duals from GLPK's table."""

    table: dict[tuple[str, ...], tuple[float, float]] = {}
    prefix = f"{symbol}("
    for line in results.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        fields = line.split()
        if (
            len(fields) != 4
            or not fields[1].startswith(prefix)
            or not fields[1].endswith(")")
        ):
            continue
        indices = tuple(
            fields[1].split("(", 1)[1][:-1].split(",")
        )
        table[indices] = (float(fields[2]), float(fields[3]))
    return table


def aggregate_activity(
    table: dict[tuple[str, ...], tuple[float, float]]
) -> dict[tuple[str, str], float]:
    totals: dict[tuple[str, str], float] = {}
    for (_, technology, _, year), (value, _) in table.items():
        if technology == OLD_POWER:
            continue
        key = (technology, year)
        totals[key] = totals.get(key, 0.0) + value
    return totals


def technology_group_activity(
    totals: dict[tuple[str, str], float],
    technologies: set[str],
) -> dict[tuple[str], float]:
    grouped: dict[tuple[str], float] = {}
    for (technology, year), value in totals.items():
        if technology in technologies:
            key = (year,)
            grouped[key] = grouped.get(key, 0.0) + value
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muiogo-root", type=Path, default=DEFAULT_MUIOGO
    )
    parser.add_argument("--control-case", default="Fiji_v2")
    parser.add_argument(
        "--control-run", default="Phase1D_Cane_Bagasse"
    )
    parser.add_argument(
        "--candidate-case",
        default="Fiji_v2_Phase1D_Legacy_Removal_Test",
    )
    parser.add_argument(
        "--candidate-run", default="Phase1D_Legacy_Removal"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    storage = (
        args.muiogo_root.resolve() / "WebAPP" / "DataStorage"
    )
    control_case = storage / args.control_case
    candidate_case = storage / args.candidate_case
    control_run = control_case / "res" / args.control_run
    candidate_run = candidate_case / "res" / args.candidate_run

    required = [
        control_case / "genData.json",
        candidate_case / "genData.json",
        control_case / "RYT.json",
        candidate_case / "RYT.json",
    ]
    for run in (control_run, candidate_run):
        required.extend(
            [
                run / "data.txt",
                run / "data_processed.txt",
                run / "lp.lp",
                run / "results.txt",
                locate(run, "ObjectiveValue.csv"),
                locate(run, "TotalAnnualTechnologyActivityByMode.csv"),
                locate(run, "TotalCapacityAnnual.csv"),
                locate(run, "NewCapacity.csv"),
                locate(run, "AnnualTechnologyEmission.csv"),
                locate(run, "EBb4_EnergyBalanceEachYear4_ICR.csv"),
                locate(run, "Demand.csv"),
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

    control_gen = read_json(control_case / "genData.json")
    candidate_gen = read_json(candidate_case / "genData.json")
    control_tech = {
        item["Tech"]: item["TechId"]
        for item in control_gen["osy-tech"]
    }
    candidate_tech = {
        item["Tech"]: item["TechId"]
        for item in candidate_gen["osy-tech"]
    }
    check(
        "Candidate removes exactly the legacy technology",
        OLD_POWER in control_tech
        and OLD_POWER not in candidate_tech
        and len(control_tech) == 134
        and len(candidate_tech) == 133
        and (
            set(control_tech) - {OLD_POWER}
            == set(candidate_tech)
        ),
        {
            "control_technologies": len(control_tech),
            "candidate_technologies": len(candidate_tech),
            "removed": sorted(set(control_tech) - set(candidate_tech)),
            "added": sorted(set(candidate_tech) - set(control_tech)),
        },
        "control and candidate genData.json",
    )

    control_ryt = read_json(control_case / "RYT.json")
    source_maxima: dict[str, float] = {}
    for parameter in (
        "RC",
        "TAMaxC",
        "TAMaxCI",
        "TAMinC",
        "TAMinCI",
        "TAL",
        "TAU",
    ):
        matches = [
            row
            for row in control_ryt[parameter]["SC_0"]
            if row.get("TechId") == OLD_ID
        ]
        if len(matches) != 1:
            source_maxima[parameter] = math.inf
            continue
        source_maxima[parameter] = max(
            (
                abs(float(value))
                for key, value in matches[0].items()
                if str(key).isdigit()
            ),
            default=0.0,
        )
    check(
        "Control source forces zero legacy stock, investment and activity",
        all(
            value <= ZERO_TOLERANCE
            for value in source_maxima.values()
        ),
        source_maxima,
        "control RYT.json; CAa2, NCC1, CAa4 and AAC2",
    )

    control_activity = table_map(
        control_run,
        "TotalAnnualTechnologyActivityByMode.csv",
        ("t", "m", "y"),
        "TotalAnnualTechnologyActivityByMode",
    )
    control_capacity = table_map(
        control_run,
        "TotalCapacityAnnual.csv",
        ("t", "y"),
        "TotalCapacityAnnual",
    )
    control_new = table_map(
        control_run,
        "NewCapacity.csv",
        ("t", "y"),
        "NewCapacity",
    )
    legacy_result_maxima = {
        "activity": max(
            (
                abs(value)
                for key, value in control_activity.items()
                if key[0] == OLD_POWER
            ),
            default=0.0,
        ),
        "capacity": max(
            (
                abs(value)
                for key, value in control_capacity.items()
                if key[0] == OLD_POWER
            ),
            default=0.0,
        ),
        "new_capacity": max(
            (
                abs(value)
                for key, value in control_new.items()
                if key[0] == OLD_POWER
            ),
            default=0.0,
        ),
    }
    check(
        "Control results contain no legacy stock, investment or activity",
        all(
            value <= ZERO_TOLERANCE
            for value in legacy_result_maxima.values()
        ),
        legacy_result_maxima,
        "control result CSVs",
    )

    candidate_json_references = [
        path.name
        for path in sorted(candidate_case.glob("*.json"))
        if OLD_ID in path.read_text(encoding="utf-8")
        or OLD_POWER in path.read_text(encoding="utf-8")
    ]
    generated_references = [
        path.name
        for path in (
            candidate_run / "data.txt",
            candidate_run / "data_processed.txt",
            candidate_run / "lp.lp",
            candidate_run / "results.txt",
        )
        if OLD_POWER
        in path.read_text(encoding="utf-8", errors="replace")
    ]
    check(
        "Legacy technology is absent from candidate sources and generated artifacts",
        not candidate_json_references and not generated_references,
        {
            "source_references": candidate_json_references,
            "generated_references": generated_references,
        },
        "candidate source JSON and generated run artifacts",
    )

    source_mismatches: list[str] = []
    for control_path in sorted(control_case.glob("*.json")):
        if control_path.name in {
            "genData.json",
            "reserve_margin_proxy.json",
        }:
            continue
        candidate_path = candidate_case / control_path.name
        if not candidate_path.is_file():
            source_mismatches.append(
                f"{control_path.name}: missing candidate file"
            )
            continue
        if without_legacy(read_json(control_path)) != read_json(
            candidate_path
        ):
            source_mismatches.append(control_path.name)
    check(
        "Every nonlegacy source parameter survives UpdateCase unchanged",
        not source_mismatches,
        source_mismatches or "All source parameters match after filtering the legacy ID",
        "control/candidate source JSON structural comparison",
    )

    candidate_status = (
        candidate_run / "results.txt"
    ).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    check(
        "Candidate generation, preprocessing, GLPK matrix and CBC solve completed",
        candidate_status.startswith("Optimal")
        and (candidate_run / "data_processed.txt").stat().st_size > 0
        and (candidate_run / "lp.lp").stat().st_size > 0,
        {
            "status": candidate_status,
            "data_processed_bytes": (
                candidate_run / "data_processed.txt"
            ).stat().st_size,
            "lp_bytes": (candidate_run / "lp.lp").stat().st_size,
        },
        "candidate data_processed.txt, lp.lp and results.txt",
    )

    control_objective = objective(control_run)
    candidate_objective = objective(candidate_run)
    check(
        "Objective is unchanged within numerical tolerance",
        math.isclose(
            control_objective,
            candidate_objective,
            rel_tol=0,
            abs_tol=PARITY_TOLERANCE,
        ),
        {
            "control": control_objective,
            "candidate": candidate_objective,
            "difference": candidate_objective - control_objective,
            "difference_percent": (
                100
                * (candidate_objective - control_objective)
                / abs(control_objective)
            ),
        },
        "ObjectiveValue.csv",
    )

    candidate_activity = table_map(
        candidate_run,
        "TotalAnnualTechnologyActivityByMode.csv",
        ("t", "m", "y"),
        "TotalAnnualTechnologyActivityByMode",
    )
    mode_activity_comparison = compare_maps(
        control_activity,
        candidate_activity,
        technology_position=0,
    )
    structural_comparisons = {
        "capacity": compare_maps(
            control_capacity,
            table_map(
                candidate_run,
                "TotalCapacityAnnual.csv",
                ("t", "y"),
                "TotalCapacityAnnual",
            ),
            technology_position=0,
        ),
        "new_capacity": compare_maps(
            control_new,
            table_map(
                candidate_run,
                "NewCapacity.csv",
                ("t", "y"),
                "NewCapacity",
            ),
            technology_position=0,
        ),
        "emissions": compare_maps(
            table_map(
                control_run,
                "AnnualTechnologyEmission.csv",
                ("t", "e", "y"),
                "AnnualTechnologyEmission",
            ),
            table_map(
                candidate_run,
                "AnnualTechnologyEmission.csv",
                ("t", "e", "y"),
                "AnnualTechnologyEmission",
            ),
            technology_position=0,
        ),
        "demand": compare_maps(
            table_map(
                control_run,
                "Demand.csv",
                ("l", "f", "y"),
                "Demand",
            ),
            table_map(
                candidate_run,
                "Demand.csv",
                ("l", "f", "y"),
                "Demand",
            ),
        ),
    }

    control_solver_activity = solver_table(
        control_run / "results.txt",
        "TotalAnnualTechnologyActivityByMode",
    )
    candidate_solver_activity = solver_table(
        candidate_run / "results.txt",
        "TotalAnnualTechnologyActivityByMode",
    )
    control_aggregate_activity = aggregate_activity(
        control_solver_activity
    )
    candidate_aggregate_activity = aggregate_activity(
        candidate_solver_activity
    )

    def selected_activity(
        values: dict[tuple[str, str], float],
        technologies: set[str],
        *,
        include: bool,
    ) -> dict[tuple[str, str], float]:
        return {
            key: value
            for key, value in values.items()
            if (key[0] in technologies) == include
        }

    aggregate_comparisons = {
        "unaffected_technology_year_activity": compare_maps(
            selected_activity(
                control_aggregate_activity,
                EXPECTED_ALTERNATE_TECHNOLOGIES,
                include=False,
            ),
            selected_activity(
                candidate_aggregate_activity,
                EXPECTED_ALTERNATE_TECHNOLOGIES,
                include=False,
            ),
            technology_position=0,
            tolerance=AGGREGATE_TOLERANCE,
        ),
        "phase1d_chain_technology_year_activity": compare_maps(
            selected_activity(
                control_aggregate_activity,
                PHASE1D_TECHNOLOGIES,
                include=True,
            ),
            selected_activity(
                candidate_aggregate_activity,
                PHASE1D_TECHNOLOGIES,
                include=True,
            ),
            technology_position=0,
            tolerance=AGGREGATE_TOLERANCE,
        ),
        "land_technology_year_activity": compare_maps(
            selected_activity(
                control_aggregate_activity,
                LAND_MODE_SUBSTITUTES,
                include=True,
            ),
            selected_activity(
                candidate_aggregate_activity,
                LAND_MODE_SUBSTITUTES,
                include=True,
            ),
            technology_position=0,
            tolerance=AGGREGATE_TOLERANCE,
        ),
        "power_group_year_activity": compare_maps(
            technology_group_activity(
                control_aggregate_activity,
                POWER_ACTIVITY_SUBSTITUTES,
            ),
            technology_group_activity(
                candidate_aggregate_activity,
                POWER_ACTIVITY_SUBSTITUTES,
            ),
            tolerance=AGGREGATE_TOLERANCE,
        ),
        "renewable_accounting_group_year_activity": compare_maps(
            technology_group_activity(
                control_aggregate_activity,
                RENEWABLE_ACCOUNTING_SUBSTITUTES,
            ),
            technology_group_activity(
                candidate_aggregate_activity,
                RENEWABLE_ACCOUNTING_SUBSTITUTES,
            ),
            tolerance=AGGREGATE_TOLERANCE,
        ),
    }
    alternate_mode_scope_ok = set(
        mode_activity_comparison["changed_technologies"]
    ) <= EXPECTED_ALTERNATE_TECHNOLOGIES
    check(
        "Stocks, investment, emissions, demands, Phase 1D flows and aggregate services are unchanged",
        all(
            item["rows_changed"] == 0
            for item in structural_comparisons.values()
        )
        and all(
            item["rows_changed"] == 0
            for item in aggregate_comparisons.values()
        )
        and alternate_mode_scope_ok,
        {
            "strict_comparisons": structural_comparisons,
            "aggregate_comparisons": aggregate_comparisons,
            "alternate_optimum_mode_activity": (
                mode_activity_comparison
            ),
            "alternate_mode_changes_within_expected_scope": (
                alternate_mode_scope_ok
            ),
        },
        (
            "control/candidate result CSVs and full-precision "
            "results.txt; changes within the declared substitute groups "
            "are alternate optimal allocations"
        ),
    )

    control_balance = solver_table(
        control_run / "results.txt",
        "EBb4_EnergyBalanceEachYear4",
    )
    candidate_balance = solver_table(
        candidate_run / "results.txt",
        "EBb4_EnergyBalanceEachYear4",
    )
    balance_keys = control_balance.keys() | candidate_balance.keys()
    primal_differences = [
        {
            "key": key,
            "control": control_balance.get(key, (0.0, 0.0))[0],
            "candidate": candidate_balance.get(key, (0.0, 0.0))[0],
            "difference": (
                candidate_balance.get(key, (0.0, 0.0))[0]
                - control_balance.get(key, (0.0, 0.0))[0]
            ),
        }
        for key in sorted(balance_keys)
        if abs(
            candidate_balance.get(key, (0.0, 0.0))[0]
            - control_balance.get(key, (0.0, 0.0))[0]
        )
        > PARITY_TOLERANCE
    ]
    changed_balance_indices = {
        (item["key"][1], item["key"][2])
        for item in primal_differences
    }
    phase1d_balance_difference = max(
        (
            abs(
                candidate_balance.get(key, (0.0, 0.0))[0]
                - control_balance.get(key, (0.0, 0.0))[0]
            )
            for key in balance_keys
            if key[1] in PHASE1D_COMMODITIES
        ),
        default=0.0,
    )
    control_minimum_balance = min(
        value for value, _ in control_balance.values()
    )
    candidate_minimum_balance = min(
        value for value, _ in candidate_balance.values()
    )
    discounted_dual_comparison = compare_maps(
        table_map(
            control_run,
            "EBb4_EnergyBalanceEachYear4_ICR.csv",
            ("f", "y"),
            "EBb4_EnergyBalanceEachYear4_ICR",
        ),
        table_map(
            candidate_run,
            "EBb4_EnergyBalanceEachYear4_ICR.csv",
            ("f", "y"),
            "EBb4_EnergyBalanceEachYear4_ICR",
        ),
    )
    check(
        "Annual commodity balances remain feasible and physical-chain residuals are unchanged",
        control_minimum_balance >= -PARITY_TOLERANCE
        and candidate_minimum_balance >= -PARITY_TOLERANCE
        and changed_balance_indices
        <= EXPECTED_WATER_SURPLUS_CHANGES
        and phase1d_balance_difference <= PARITY_TOLERANCE,
        {
            "control_minimum_primal_balance": (
                control_minimum_balance
            ),
            "candidate_minimum_primal_balance": (
                candidate_minimum_balance
            ),
            "changed_primal_balance_rows": len(
                primal_differences
            ),
            "changed_primal_balance_indices": sorted(
                changed_balance_indices
            ),
            "maximum_primal_balance_difference": max(
                (
                    abs(item["difference"])
                    for item in primal_differences
                ),
                default=0.0,
            ),
            "maximum_phase1d_balance_difference": (
                phase1d_balance_difference
            ),
            "discounted_shadow_price_changes": (
                discounted_dual_comparison
            ),
            "interpretation": (
                "Only nonbinding water-surplus balances move. "
                "Shadow prices are not unique under this alternate "
                "optimum and are recorded, not used as a parity gate."
            ),
        },
        (
            "full-precision results.txt EBb4 primal activities; "
            "EBb4_EnergyBalanceEachYear4_ICR.csv contains discounted "
            "duals/shadow prices"
        ),
    )

    years = [int(year) for year in candidate_gen["osy-years"]]
    dual_differences: dict[int, dict[str, float]] = {}
    for year in years:
        control_value, control_dual = result_value(
            control_run / "results.txt",
            "EBb4_EnergyBalanceEachYear4",
            ("RE1", "BAGEXPFJI", year),
        )
        candidate_value, candidate_dual = result_value(
            candidate_run / "results.txt",
            "EBb4_EnergyBalanceEachYear4",
            ("RE1", "BAGEXPFJI", year),
        )
        dual_differences[year] = {
            "control_residual": control_value,
            "candidate_residual": candidate_value,
            "residual_difference": candidate_value - control_value,
            "dual_difference": candidate_dual - control_dual,
        }
    check(
        "Bagasse-balance residuals remain numerically zero in every year",
        all(
            abs(item["control_residual"]) <= PARITY_TOLERANCE
            and abs(item["candidate_residual"])
            <= PARITY_TOLERANCE
            for item in dual_differences.values()
        ),
        {
            "maximum_residual_difference": max(
                abs(item["residual_difference"])
                for item in dual_differences.values()
            ),
            "maximum_dual_difference": max(
                abs(item["dual_difference"])
                for item in dual_differences.values()
            ),
            "dual_interpretation": (
                "The changed bagasse shadow price is an allowed "
                "alternate-optimum effect; primal closure is the gate."
            ),
        },
        "results.txt EBb4_EnergyBalanceEachYear4",
    )

    source_timestamp = max(
        path.stat().st_mtime
        for path in candidate_case.glob("*.json")
    )
    result_paths = [
        candidate_run / "data.txt",
        candidate_run / "data_processed.txt",
        candidate_run / "lp.lp",
        candidate_run / "results.txt",
        locate(candidate_run, "ObjectiveValue.csv"),
    ]
    oldest_result_timestamp = min(
        path.stat().st_mtime for path in result_paths
    )
    check(
        "Candidate results postdate source inputs and identify the intended case/run",
        oldest_result_timestamp >= source_timestamp
        and candidate_case.name == args.candidate_case
        and candidate_run.name == args.candidate_run,
        {
            "case": candidate_case.name,
            "run": candidate_run.name,
            "source_timestamp": datetime.fromtimestamp(
                source_timestamp, timezone.utc
            ).isoformat(),
            "oldest_result_timestamp": datetime.fromtimestamp(
                oldest_result_timestamp, timezone.utc
            ).isoformat(),
        },
        "candidate source and generated artifact timestamps",
    )

    failures = [
        item for item in checks if item["status"] == "FAIL"
    ]
    report = {
        "schema_version": 1,
        "phase": "1D legacy-biomass structural cleanup",
        "status": "PASS" if not failures else "FAIL",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "control": {
            "case": args.control_case,
            "run": args.control_run,
        },
        "candidate": {
            "case": args.candidate_case,
            "run": args.candidate_run,
        },
        "checks": checks,
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failed_checks": len(failures),
        "artifacts": {
            str(path.relative_to(candidate_case)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in result_paths
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
