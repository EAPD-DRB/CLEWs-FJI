#!/usr/bin/env python3
"""Validate Fiji Phase 1B public water against source, export and baseline."""

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


REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "Fiji_v2_CLEWs_calibration"
DEFAULT_MUIOGO = REPO.parent / "MUIOGO"
DEFAULT_INPUTS = PACKAGE / "model" / "inputs"
DEFAULT_OUTPUT = (
    PACKAGE
    / "diagnostics"
    / "calibration_runs"
    / "phase1b"
    / "validation_summary.json"
)
EXPECTED_DEMAND = {
    2020: 0.070079,
    2021: 0.071071,
    2022: 0.069294,
    2023: 0.068332,
    2024: 0.067091,
}
EXPECTED_SURFACE_EXTRACTION = {
    2020: 0.143660,
    2021: 0.140979,
    2022: 0.141298,
    2023: 0.138941,
    2024: 0.151467,
}
WATER_TECHNOLOGIES = {"DEMPUBGWTFJI", "DEMPUBSURFJI", "WTRABSFJI"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parameter_rows(data: dict[str, Any], parameter: str) -> list[dict[str, Any]]:
    return data[parameter]["SC_0"]


def parameter_row(
    data: dict[str, Any], parameter: str, **identifiers: Any
) -> dict[str, Any]:
    matches = [
        row
        for row in parameter_rows(data, parameter)
        if all(row.get(key) == value for key, value in identifiers.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {identifiers}, found {len(matches)}"
        )
    return matches[0]


def close_map(
    actual: dict[int, float],
    expected: dict[int, float],
    tolerance: float = 1e-9,
) -> bool:
    return actual.keys() == expected.keys() and all(
        math.isclose(actual[year], value, rel_tol=0, abs_tol=tolerance)
        for year, value in expected.items()
    )


def table_map(
    path: Path,
    key_fields: tuple[str, ...],
    value_field: str | None = None,
) -> dict[tuple[str, ...], float]:
    data = rows(path)
    if not data:
        return {}
    if value_field is None:
        value_field = list(data[0])[-1]
    return {
        tuple(row[field] for field in key_fields): float(row[value_field])
        for row in data
    }


def result_row(path: Path, symbol: str, indices: list[Any]) -> tuple[float, float]:
    label = f"{symbol}({','.join(str(item) for item in indices)})"
    pattern = re.compile(
        rf"^\s*\d+\s+{re.escape(label)}\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    if not match:
        raise ValueError(f"Result row not found: {label}")
    return float(match.group(1)), float(match.group(2))


def objective(path: Path) -> float:
    return float(rows(path)[0]["ObjectiveValue"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--muiogo-root", type=Path, default=DEFAULT_MUIOGO)
    parser.add_argument("--case", default="Fiji_v2_Phase1B_Test")
    parser.add_argument("--run", default="Phase1B_Public_Water")
    parser.add_argument("--baseline-case", default="Fiji_v2")
    parser.add_argument("--baseline-run", default="Historical_Backcast")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    muiogo = args.muiogo_root.resolve()
    case = muiogo / "WebAPP" / "DataStorage" / args.case
    run = case / "res" / args.run
    baseline = (
        muiogo
        / "WebAPP"
        / "DataStorage"
        / args.baseline_case
        / "res"
        / args.baseline_run
    )
    inputs = args.inputs.resolve()
    output = args.output.resolve()

    required = [
        case / "genData.json",
        case / "R.json",
        case / "RYC.json",
        case / "RYCTs.json",
        case / "RYTCM.json",
        case / "RYT.json",
        run / "data.txt",
        run / "data_processed.txt",
        run / "lp.lp",
        run / "results.txt",
        run / "csv" / "ObjectiveValue.csv",
        baseline / "results.txt",
        baseline / "csv" / "ObjectiveValue.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required artifacts: " + "; ".join(missing))

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

    gen_data = read_json(case / "genData.json")
    tech_by_name = {item["Tech"]: item for item in gen_data["osy-tech"]}
    comm_by_name = {item["Comm"]: item for item in gen_data["osy-comm"]}
    check(
        "Phase 1B dimensions and entities are present",
        len(tech_by_name) == 131
        and len(comm_by_name) == 104
        and "WTRABSFJI" in tech_by_name
        and "WTRGWRFJI" in comm_by_name,
        {
            "technologies": len(tech_by_name),
            "commodities": len(comm_by_name),
        },
        "genData.json",
    )

    expected_water_units = {
        "WTRPRCFJI",
        "WTREVTFJI",
        "WTRGRCFJI",
        "WTRSURFJI",
        "WTRGWRFJI",
        "AGRWATFJI",
        "PUBWATFJI",
    }
    wrong_units = {
        name: comm_by_name[name]["UnitId"]
        for name in expected_water_units
        if comm_by_name[name]["UnitId"] != "km3"
    }
    check(
        "Water commodity metadata uses km3",
        not wrong_units,
        wrong_units or "All seven water commodities use km3",
        "genData.json",
    )

    groundwater_tech = tech_by_name["DEMPUBGWTFJI"]
    raw_groundwater_id = comm_by_name["WTRGWRFJI"]["CommId"]
    check(
        "Public groundwater consumes raw groundwater, not commercial electricity",
        groundwater_tech["IAR"] == [raw_groundwater_id]
        and comm_by_name["COMELCFJIXX02"]["CommId"] not in groundwater_tech["IAR"],
        {"IAR": groundwater_tech["IAR"]},
        "genData.json",
    )

    csv_iar = rows(inputs / "InputActivityRatio.csv")
    bad_public_electricity = [
        row
        for row in csv_iar
        if row["TECHNOLOGY"] == "DEMPUBGWTFJI"
        and row["FUEL"] == "COMELCFJIXX02"
    ]
    raw_groundwater_rows = [
        row
        for row in csv_iar
        if row["TECHNOLOGY"] == "DEMPUBGWTFJI"
        and row["FUEL"] == "WTRGWRFJI"
    ]
    portable_quarantine = {}
    portable_quarantine_pass = True
    for filename in (
        "TotalTechnologyAnnualActivityUpperLimit.csv",
        "TotalAnnualMaxCapacityInvestment.csv",
    ):
        quarantine_rows = [
            row
            for row in rows(inputs / filename)
            if row["TECHNOLOGY"] == "DEMPUBGWTFJI"
        ]
        portable_quarantine[filename] = len(quarantine_rows)
        portable_quarantine_pass &= len(quarantine_rows) == 31 and all(
            float(row["VALUE"]) == 0.0 for row in quarantine_rows
        )
    check(
        "Portable source carries the corrected and quarantined groundwater route",
        not bad_public_electricity
        and len(raw_groundwater_rows) == 31
        and all(float(row["VALUE"]) == 1.0 for row in raw_groundwater_rows)
        and portable_quarantine_pass,
        {
            "bad_commercial_electricity_rows": len(bad_public_electricity),
            "raw_groundwater_rows": len(raw_groundwater_rows),
            "quarantine_rows": portable_quarantine,
        },
        "model/inputs/InputActivityRatio.csv and public-groundwater bounds",
    )

    comm_ids = {name: item["CommId"] for name, item in comm_by_name.items()}
    tech_ids = {name: item["TechId"] for name, item in tech_by_name.items()}
    rytcm = read_json(case / "RYTCM.json")
    relation_specs = [
        ("IAR", "WTRABSFJI", "WTRGRCFJI"),
        ("OAR", "WTRABSFJI", "WTRGWRFJI"),
        ("IAR", "DEMPUBGWTFJI", "WTRGWRFJI"),
        ("OAR", "DEMPUBGWTFJI", "PUBWATFJI"),
        ("IAR", "DEMPUBSURFJI", "WTRSURFJI"),
        ("OAR", "DEMPUBSURFJI", "PUBWATFJI"),
    ]
    relationships = {}
    relationship_pass = True
    for parameter, technology, commodity in relation_specs:
        row = parameter_row(
            rytcm,
            parameter,
            TechId=tech_ids[technology],
            CommId=comm_ids[commodity],
            MoId=1,
        )
        relationships[f"{parameter}:{technology}:{commodity}"] = {
            year: float(row[str(year)]) for year in EXPECTED_DEMAND
        }
        if parameter == "IAR" and technology == "DEMPUBSURFJI":
            expected = {
                year: EXPECTED_SURFACE_EXTRACTION[year] / EXPECTED_DEMAND[year]
                for year in EXPECTED_DEMAND
            }
        else:
            expected = {year: 1.0 for year in EXPECTED_DEMAND}
        relationship_pass &= close_map(
            relationships[f"{parameter}:{technology}:{commodity}"], expected
        )
    check(
        "UpdateCase preserved all Phase 1B activity relationships",
        relationship_pass,
        relationships,
        "RYTCM.json",
    )

    demand_row = parameter_row(
        read_json(case / "RYC.json"),
        "SAD",
        CommId=comm_ids["PUBWATFJI"],
    )
    actual_demand = {
        year: float(demand_row[str(year)]) for year in EXPECTED_DEMAND
    }
    check(
        "Public-water annual demand matches the FBoS billed-delivery boundary",
        close_map(actual_demand, EXPECTED_DEMAND),
        actual_demand,
        "RYC.json; FBoS water-account extract",
    )

    rycts = read_json(case / "RYCTs.json")
    ryts = read_json(case / "RYTs.json")
    profile_matches = True
    profile_sums = {year: 0.0 for year in EXPECTED_DEMAND}
    for timeslice in gen_data["osy-ts"]:
        ts_id = timeslice["TsId"]
        profile = parameter_row(
            rycts, "SDP", CommId=comm_ids["PUBWATFJI"], TsId=ts_id
        )
        year_split = parameter_row(ryts, "YS", TsId=ts_id)
        for year in EXPECTED_DEMAND:
            profile_value = float(profile[str(year)])
            profile_sums[year] += profile_value
            profile_matches &= math.isclose(
                profile_value,
                float(year_split[str(year)]),
                rel_tol=0,
                abs_tol=1e-12,
            )
    profile_matches &= all(
        math.isclose(value, 1.0, rel_tol=0, abs_tol=1e-12)
        for value in profile_sums.values()
    )
    check(
        "Annual-only public demand uses a normalized flat-rate profile",
        profile_matches,
        profile_sums,
        "RYCTs.json; RYTs.json",
    )

    ryt = read_json(case / "RYT.json")
    quarantine = {}
    quarantine_pass = True
    for parameter in ("TAU", "TAMaxCI"):
        row = parameter_row(
            ryt, parameter, TechId=tech_ids["DEMPUBGWTFJI"]
        )
        values = [float(row[str(year)]) for year in range(2020, 2051)]
        quarantine[parameter] = {
            "minimum": min(values),
            "maximum": max(values),
        }
        quarantine_pass &= all(value == 0.0 for value in values)
    check(
        "Public groundwater is quarantined for 2020-2050",
        quarantine_pass,
        quarantine,
        "RYT.json",
    )

    generated = (run / "data_processed.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    mapping_checks = {
        "groundwater_mode": "set MODEperTECHNOLOGY[DEMPUBGWTFJI]:= 1;"
        in generated,
        "surface_mode": "set MODEperTECHNOLOGY[DEMPUBSURFJI]:= 1;"
        in generated,
        "abstraction_mode": "set MODEperTECHNOLOGY[WTRABSFJI]:= 1;"
        in generated,
        "raw_groundwater_consumer": (
            "set MODExTECHNOLOGYperFUELin[WTRGWRFJI]:= (1, DEMPUBGWTFJI);"
            in generated
        ),
        "commercial_electricity_has_no_consumers": (
            "set MODExTECHNOLOGYperFUELin[COMELCFJIXX02]:=;" in generated
        ),
    }
    check(
        "Generated derived sets contain the intended Phase 1B mappings",
        all(mapping_checks.values()),
        mapping_checks,
        "data_processed.txt",
    )

    first_line = (run / "results.txt").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()[0]
    matrix_artifacts = {
        name: (run / name).stat().st_size
        for name in ("data.txt", "data_processed.txt", "lp.lp", "results.txt")
    }
    check(
        "Generation, preprocessing, matrix construction and CBC solve completed",
        first_line.startswith("Optimal")
        and all(size > 0 for size in matrix_artifacts.values()),
        {"solver": first_line, "artifact_bytes": matrix_artifacts},
        "MUIO DataFile generation/run chain",
    )

    result_path = run / "results.txt"
    public_activity = {}
    public_balance = {}
    surface_balance = {}
    groundwater_activity = {}
    abstraction_activity = {}
    result_pass = True
    for year, expected in EXPECTED_DEMAND.items():
        public_activity[year], _ = result_row(
            result_path,
            "TotalAnnualTechnologyActivityByMode",
            ["RE1", "DEMPUBSURFJI", 1, year],
        )
        public_balance[year], public_dual = result_row(
            result_path,
            "EBb4_EnergyBalanceEachYear4",
            ["RE1", "PUBWATFJI", year],
        )
        surface_balance[year], surface_dual = result_row(
            result_path,
            "EBb4_EnergyBalanceEachYear4",
            ["RE1", "WTRSURFJI", year],
        )
        groundwater_activity[year], _ = result_row(
            result_path,
            "TotalAnnualTechnologyActivityByMode",
            ["RE1", "DEMPUBGWTFJI", 1, year],
        )
        abstraction_activity[year], _ = result_row(
            result_path,
            "TotalAnnualTechnologyActivityByMode",
            ["RE1", "WTRABSFJI", 1, year],
        )
        result_pass &= (
            math.isclose(public_activity[year], expected, rel_tol=0, abs_tol=1e-9)
            and math.isclose(public_balance[year], expected, rel_tol=0, abs_tol=1e-9)
            and math.isclose(
                public_activity[year]
                * EXPECTED_SURFACE_EXTRACTION[year]
                / EXPECTED_DEMAND[year],
                EXPECTED_SURFACE_EXTRACTION[year],
                rel_tol=0,
                abs_tol=1e-9,
            )
            and surface_balance[year] > 0
            and groundwater_activity[year] == 0
            and abstraction_activity[year] == 0
            and public_dual == 0
            and surface_dual == 0
        )
    check(
        "Solved public-water delivery and raw-surface use close exactly",
        result_pass,
        {
            "surface_delivery_activity_km3": public_activity,
            "public_balance_activity_km3": public_balance,
            "remaining_surface_balance_km3": surface_balance,
            "groundwater_delivery_activity_km3": groundwater_activity,
            "groundwater_abstraction_activity_km3": abstraction_activity,
            "reported_balance_duals": 0.0,
        },
        "results.txt; FBoS water-account extract",
    )

    baseline_objective = objective(baseline / "csv" / "ObjectiveValue.csv")
    phase1b_objective = objective(run / "csv" / "ObjectiveValue.csv")
    objective_difference = phase1b_objective - baseline_objective
    objective_pct = 100.0 * objective_difference / abs(baseline_objective)
    discount_rate = float(read_json(case / "R.json")["DR"]["SC_0"][0]["value"])
    first_year = min(int(year) for year in gen_data["osy-years"])
    expected_water_cost = sum(
        value
        * 0.0001
        / ((1.0 + discount_rate) ** (year - first_year + 0.5))
        for year, value in EXPECTED_DEMAND.items()
    )
    check(
        "Objective change is limited to the added water-service operating cost",
        math.isclose(
            objective_difference,
            expected_water_cost,
            rel_tol=0,
            abs_tol=1e-8,
        ),
        {
            "baseline": baseline_objective,
            "phase1b": phase1b_objective,
            "difference": objective_difference,
            "percent_change": objective_pct,
            "expected_discounted_water_cost": expected_water_cost,
            "difference_from_expected": objective_difference - expected_water_cost,
        },
        "ObjectiveValue.csv for baseline and Phase 1B",
    )

    activity_file = "TotalAnnualTechnologyActivityByMode.csv"
    base_activity = table_map(
        baseline / "csv" / activity_file, ("t", "m", "y")
    )
    new_activity = table_map(run / "csv" / activity_file, ("t", "m", "y"))
    all_existing_nonwater = {
        key for key in base_activity if key[0] not in WATER_TECHNOLOGIES
    }
    missing_nonwater = sorted(all_existing_nonwater - new_activity.keys())
    changed_nonwater = {
        key: (base_activity[key], new_activity[key])
        for key in all_existing_nonwater & new_activity.keys()
        if not math.isclose(
            base_activity[key], new_activity[key], rel_tol=0, abs_tol=1e-9
        )
    }
    check(
        "No existing non-water technology activity changed",
        not missing_nonwater and not changed_nonwater,
        {
            "compared_rows": len(all_existing_nonwater),
            "missing_rows": len(missing_nonwater),
            "changed_rows": len(changed_nonwater),
        },
        f"baseline and Phase 1B {activity_file}",
    )

    emission_file = "AnnualTechnologyEmission.csv"
    base_emissions = table_map(
        baseline / "csv" / emission_file, ("r", "e", "t", "y")
    )
    new_emissions = table_map(run / "csv" / emission_file, ("r", "e", "t", "y"))
    emission_keys = set(base_emissions)
    changed_emissions = {
        key: (base_emissions[key], new_emissions.get(key))
        for key in emission_keys
        if key not in new_emissions
        or not math.isclose(
            base_emissions[key], new_emissions[key], rel_tol=0, abs_tol=1e-9
        )
    }
    check(
        "No existing technology emissions changed",
        not changed_emissions,
        {
            "compared_rows": len(emission_keys),
            "changed_rows": len(changed_emissions),
        },
        f"baseline and Phase 1B {emission_file}",
    )

    newest_input = max(
        path.stat().st_mtime for path in case.glob("*.json") if path.is_file()
    )
    result_artifacts = [
        run / "data.txt",
        run / "data_processed.txt",
        run / "lp.lp",
        run / "results.txt",
        run / "csv" / "ObjectiveValue.csv",
    ]
    timestamp_pass = all(path.stat().st_mtime >= newest_input for path in result_artifacts)
    check(
        "Result timestamps and case identity match Phase 1B",
        timestamp_pass
        and gen_data["osy-casename"] == args.case
        and args.case in str(run),
        {
            "case_name": gen_data["osy-casename"],
            "run": str(run),
            "all_results_newer_than_inputs": timestamp_pass,
        },
        "genData.json and run artifacts",
    )

    failures = [item for item in checks if item["status"] == "FAIL"]
    report = {
        "schema_version": 1,
        "phase": "1B public water",
        "status": "PASS" if not failures else "FAIL",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "case": args.case,
        "run": args.run,
        "baseline_case": args.baseline_case,
        "baseline_run": args.baseline_run,
        "checks": checks,
        "failed_checks": len(failures),
        "artifact_hashes": {
            str(path.relative_to(case)): sha256(path)
            for path in result_artifacts
        },
        "known_limitations": [
            "No Fiji-specific public-water pumping/treatment electricity intensity.",
            "Public groundwater is structurally represented but quarantined.",
            "Annual-only water evidence is allocated with a flat-rate profile.",
            "No future public-water demand is projected after 2024.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
