#!/usr/bin/env python3
"""Install, update, or check Fiji's MUIO reserve-margin UDC proxy.

The current MUIO formulation does not expose OSeMOSYS reserve-margin tags.
For this Fiji model, the missing capacity-adequacy condition is represented
with MUIO's existing annual user-defined constraint:

    -sum(CapacityToActivityUnit * capacity_credit * TotalCapacityAnnual)
        <= -maximum_timeslice_demand_rate * reserve_margin

The right-hand side is derived from live MUIO demand data. It therefore becomes
stale if demand, its profile, YearSplit, or the reserve-margin assumption
changes. The default command checks for that condition and exits nonzero when
the proxy needs to be regenerated. ``--update`` regenerates it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


BASE_SCENARIO = "SC_0"
MARKER_FILENAME = "reserve_margin_proxy.json"
WARNING = (
    "DERIVED RESERVE PROXY: run manage_reserve_margin_proxy.py --check after "
    "changing annual demand, demand profile, YearSplit, CapacityToActivityUnit, "
    "capacity credits, reserve margin, model years, timeslices, or scenarios. "
    "Run it with --update before solving when the check reports STALE."
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=4)
        stream.write("\n")
    temporary.replace(path)


def require_case_file(case_folder: Path, filename: str) -> Path:
    path = case_folder / filename
    if not path.is_file():
        raise ValueError(f"Missing MUIO case file: {path}")
    return path


def rows_by_key(
    data: dict[str, Any],
    parameter: str,
    scenario: str,
    key_fields: tuple[str, ...],
) -> dict[tuple[str, ...], dict[str, Any]]:
    try:
        rows = data[parameter][scenario]
    except KeyError:
        return {}
    return {
        tuple(str(row[field]) for field in key_fields): row
        for row in rows
        if all(field in row for field in key_fields)
    }


def effective_row(
    data: dict[str, Any],
    parameter: str,
    scenario: str,
    key_fields: tuple[str, ...],
    key: tuple[str, ...],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    base = rows_by_key(data, parameter, BASE_SCENARIO, key_fields).get(key)
    scenario_row = rows_by_key(data, parameter, scenario, key_fields).get(key)
    return base, scenario_row


def effective_year_value(
    data: dict[str, Any],
    parameter: str,
    scenario: str,
    key_fields: tuple[str, ...],
    key: tuple[str, ...],
    year: str,
) -> float:
    base, override = effective_row(data, parameter, scenario, key_fields, key)
    value = override.get(year) if override is not None else None
    if value is None and base is not None:
        value = base.get(year)
    if value is None:
        label = ", ".join(f"{field}={item}" for field, item in zip(key_fields, key))
        raise ValueError(
            f"No effective {parameter} value for scenario={scenario}, {label}, year={year}"
        )
    return float(value)


def effective_scalar_map(
    data: dict[str, Any], parameter: str, scenario: str
) -> dict[str, float]:
    try:
        base_rows = data[parameter][BASE_SCENARIO]
    except KeyError as error:
        raise ValueError(f"Missing {parameter}.{BASE_SCENARIO}") from error
    result: dict[str, float] = {}
    for row in base_rows:
        for key, value in row.items():
            if value is not None:
                result[str(key)] = float(value)
    for row in data[parameter].get(scenario, []):
        for key, value in row.items():
            if value is not None:
                result[str(key)] = float(value)
    return result


def reserve_margin_for(config: dict[str, Any], scenario: str) -> float:
    margins = config["reserve_margin_by_scenario"]
    value = margins.get(scenario, margins.get(BASE_SCENARIO))
    if value is None:
        raise ValueError(
            f"No reserve margin for {scenario} and no {BASE_SCENARIO} fallback"
        )
    value = float(value)
    if value < 0:
        raise ValueError(f"Reserve margin must be nonnegative, got {value}")
    return value


def validate_config(config: dict[str, Any]) -> None:
    required = {
        "constraint_id",
        "constraint_name",
        "demand_commodity",
        "reserve_margin_by_scenario",
        "capacity_credit_by_technology",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ValueError(f"Proxy configuration is missing: {', '.join(missing)}")
    if not config["capacity_credit_by_technology"]:
        raise ValueError("At least one technology capacity credit is required")
    for technology, credit in config["capacity_credit_by_technology"].items():
        credit = float(credit)
        if not 0 <= credit <= 1:
            raise ValueError(
                f"Capacity credit for {technology} must be between 0 and 1"
            )


def load_case(case_folder: Path) -> dict[str, Any]:
    filenames = (
        "genData.json",
        "RT.json",
        "RYC.json",
        "RYCTs.json",
        "RYTs.json",
        "RYCn.json",
        "RYTCn.json",
    )
    return {
        filename: read_json(require_case_file(case_folder, filename))
        for filename in filenames
    }


def case_maps(gen_data: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    commodity_ids = {
        str(item["Comm"]): str(item["CommId"]) for item in gen_data["osy-comm"]
    }
    technology_ids = {
        str(item["Tech"]): str(item["TechId"]) for item in gen_data["osy-tech"]
    }
    return commodity_ids, technology_ids


def expected_proxy(
    case_data: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    gen_data = case_data["genData.json"]
    commodity_ids, technology_ids = case_maps(gen_data)
    demand_name = str(config["demand_commodity"])
    if demand_name not in commodity_ids:
        raise ValueError(f"Demand commodity is absent from MUIO: {demand_name}")
    demand_id = commodity_ids[demand_name]

    missing_technologies = sorted(
        set(config["capacity_credit_by_technology"]) - technology_ids.keys()
    )
    if missing_technologies:
        raise ValueError(
            "Capacity-credit technologies are absent from MUIO: "
            + ", ".join(missing_technologies)
        )

    years = [str(year) for year in gen_data["osy-years"]]
    scenarios = [
        str(scenario["ScenarioId"]) for scenario in gen_data["osy-scenarios"]
    ]
    timeslices = [
        (str(timeslice["TsId"]), str(timeslice["Ts"]))
        for timeslice in gen_data["osy-ts"]
    ]

    scenario_payload: dict[str, Any] = {}
    for scenario in scenarios:
        margin = reserve_margin_for(config, scenario)
        capacity_to_activity = effective_scalar_map(
            case_data["RT.json"], "CAU", scenario
        )
        constants: dict[str, float] = {}
        peak_timeslices: dict[str, str] = {}
        coefficients: dict[str, dict[str, float]] = {}

        for year in years:
            demand = effective_year_value(
                case_data["RYC.json"],
                "SAD",
                scenario,
                ("CommId",),
                (demand_id,),
                year,
            )
            rates: list[tuple[float, str]] = []
            for timeslice_id, timeslice_name in timeslices:
                profile = effective_year_value(
                    case_data["RYCTs.json"],
                    "SDP",
                    scenario,
                    ("CommId", "TsId"),
                    (demand_id, timeslice_id),
                    year,
                )
                year_split = effective_year_value(
                    case_data["RYTs.json"],
                    "YS",
                    scenario,
                    ("TsId",),
                    (timeslice_id,),
                    year,
                )
                if year_split <= 0:
                    raise ValueError(
                        f"YearSplit must be positive for {scenario}, "
                        f"{timeslice_name}, {year}"
                    )
                rates.append((demand * profile / year_split * margin, timeslice_name))
            peak_rate, peak_timeslice = max(rates)
            constants[year] = -peak_rate
            peak_timeslices[year] = peak_timeslice

        for technology_name, credit in sorted(
            config["capacity_credit_by_technology"].items()
        ):
            technology_id = technology_ids[technology_name]
            if technology_id not in capacity_to_activity:
                raise ValueError(
                    f"No effective CapacityToActivityUnit for {technology_name} "
                    f"in {scenario}"
                )
            coefficient = -float(credit) * capacity_to_activity[technology_id]
            coefficients[technology_id] = {
                year: coefficient for year in years
            }

        scenario_payload[scenario] = {
            "reserve_margin": margin,
            "constants": constants,
            "peak_timeslices": peak_timeslices,
            "coefficients": coefficients,
        }

    fingerprint_source = {
        "constraint_id": config["constraint_id"],
        "constraint_name": config["constraint_name"],
        "demand_commodity": demand_name,
        "capacity_credit_by_technology": config[
            "capacity_credit_by_technology"
        ],
        "scenarios": scenario_payload,
    }
    encoded = json.dumps(
        fingerprint_source, sort_keys=True, separators=(",", ":")
    ).encode()
    return {
        "years": years,
        "scenarios": scenarios,
        "timeslices": [name for _, name in timeslices],
        "demand_commodity_id": demand_id,
        "technology_ids": {
            name: technology_ids[name]
            for name in config["capacity_credit_by_technology"]
        },
        "scenario_payload": scenario_payload,
        "input_fingerprint_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def upsert_constraint(
    gen_data: dict[str, Any],
    config: dict[str, Any],
    technology_ids: dict[str, str],
) -> None:
    constraint_id = str(config["constraint_id"])
    constraint = {
        "ConId": constraint_id,
        "Con": str(config["constraint_name"]),
        "Desc": WARNING,
        "Tag": 0,
        "CM": [
            technology_ids[name]
            for name in config["capacity_credit_by_technology"]
        ],
    }
    constraints = gen_data.setdefault("osy-constraints", [])
    for index, existing in enumerate(constraints):
        if existing.get("ConId") == constraint_id:
            constraints[index] = constraint
            break
    else:
        constraints.append(constraint)


def replace_constraint_rows(
    parameter_data: dict[str, Any],
    parameter: str,
    scenarios: list[str],
    constraint_id: str,
    new_rows: dict[str, list[dict[str, Any]]],
) -> None:
    by_scenario = parameter_data.setdefault(parameter, {})
    for scenario in scenarios:
        kept = [
            row
            for row in by_scenario.get(scenario, [])
            if row.get("ConId") != constraint_id
        ]
        by_scenario[scenario] = kept + new_rows[scenario]


def install_proxy(
    case_folder: Path,
    case_data: dict[str, Any],
    config: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    constraint_id = str(config["constraint_id"])
    upsert_constraint(
        case_data["genData.json"], config, expected["technology_ids"]
    )

    constant_rows: dict[str, list[dict[str, Any]]] = {}
    coefficient_rows: dict[str, list[dict[str, Any]]] = {}
    zero_rows: dict[str, list[dict[str, Any]]] = {}
    for scenario in expected["scenarios"]:
        payload = expected["scenario_payload"][scenario]
        constant_rows[scenario] = [
            {"ConId": constraint_id, **payload["constants"]}
        ]
        coefficient_rows[scenario] = []
        zero_rows[scenario] = []
        for technology_id, values in payload["coefficients"].items():
            coefficient_rows[scenario].append(
                {
                    "TechId": technology_id,
                    "ConId": constraint_id,
                    **values,
                }
            )
            zero_rows[scenario].append(
                {
                    "TechId": technology_id,
                    "ConId": constraint_id,
                    **{year: 0 for year in expected["years"]},
                }
            )

    replace_constraint_rows(
        case_data["RYCn.json"],
        "UCC",
        expected["scenarios"],
        constraint_id,
        constant_rows,
    )
    replace_constraint_rows(
        case_data["RYTCn.json"],
        "CCM",
        expected["scenarios"],
        constraint_id,
        coefficient_rows,
    )
    for parameter in ("CAM", "CNCM"):
        replace_constraint_rows(
            case_data["RYTCn.json"],
            parameter,
            expected["scenarios"],
            constraint_id,
            zero_rows,
        )

    for filename in ("genData.json", "RYCn.json", "RYTCn.json"):
        write_json(case_folder / filename, case_data[filename])

    marker = {
        "schema_version": 1,
        "status": "DERIVED_VALUES_REQUIRE_CHECKING",
        "warning": WARNING,
        "check_command": (
            "python3 Fiji_CLEWs_Global/scripts/manage_reserve_margin_proxy.py "
            "WebAPP/DataStorage/Fiji_CLEWs_Global --check"
        ),
        "update_command": (
            "python3 Fiji_CLEWs_Global/scripts/manage_reserve_margin_proxy.py "
            "WebAPP/DataStorage/Fiji_CLEWs_Global --update"
        ),
        "configuration": config,
        "last_synced_input_fingerprint_sha256": expected[
            "input_fingerprint_sha256"
        ],
    }
    write_json(case_folder / MARKER_FILENAME, marker)


def append_mismatch(
    mismatches: list[dict[str, Any]],
    location: str,
    expected: Any,
    actual: Any,
) -> None:
    mismatches.append(
        {"location": location, "expected": expected, "actual": actual}
    )


def values_close(actual: Any, expected: float, tolerance: float) -> bool:
    try:
        return math.isclose(
            float(actual), expected, rel_tol=tolerance, abs_tol=tolerance
        )
    except (TypeError, ValueError):
        return False


def check_proxy(
    case_folder: Path,
    case_data: dict[str, Any],
    config: dict[str, Any],
    expected: dict[str, Any],
    tolerance: float,
) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    constraint_id = str(config["constraint_id"])
    expected_tech_ids = set(expected["technology_ids"].values())

    constraints = [
        item
        for item in case_data["genData.json"].get("osy-constraints", [])
        if item.get("ConId") == constraint_id
    ]
    if len(constraints) != 1:
        append_mismatch(
            mismatches,
            "genData.json:constraint count",
            1,
            len(constraints),
        )
    else:
        constraint = constraints[0]
        structural_expected = {
            "Con": config["constraint_name"],
            "Tag": 0,
            "CM": expected_tech_ids,
        }
        structural_actual = {
            "Con": constraint.get("Con"),
            "Tag": constraint.get("Tag"),
            "CM": set(constraint.get("CM", [])),
        }
        for field in structural_expected:
            if structural_actual[field] != structural_expected[field]:
                append_mismatch(
                    mismatches,
                    f"genData.json:{constraint_id}:{field}",
                    sorted(structural_expected[field])
                    if isinstance(structural_expected[field], set)
                    else structural_expected[field],
                    sorted(structural_actual[field])
                    if isinstance(structural_actual[field], set)
                    else structural_actual[field],
                )

    marker_path = case_folder / MARKER_FILENAME
    marker = read_json(marker_path) if marker_path.is_file() else {}
    fingerprint = marker.get("last_synced_input_fingerprint_sha256")
    if fingerprint != expected["input_fingerprint_sha256"]:
        append_mismatch(
            mismatches,
            f"{MARKER_FILENAME}:input fingerprint",
            expected["input_fingerprint_sha256"],
            fingerprint,
        )
    if marker.get("configuration") != config:
        append_mismatch(
            mismatches,
            f"{MARKER_FILENAME}:configuration snapshot",
            config,
            marker.get("configuration"),
        )

    for scenario in expected["scenarios"]:
        payload = expected["scenario_payload"][scenario]
        for year, expected_constant in payload["constants"].items():
            try:
                actual = effective_year_value(
                    case_data["RYCn.json"],
                    "UCC",
                    scenario,
                    ("ConId",),
                    (constraint_id,),
                    year,
                )
            except ValueError:
                actual = None
            if not values_close(actual, expected_constant, tolerance):
                append_mismatch(
                    mismatches,
                    f"UCC:{scenario}:{year}",
                    expected_constant,
                    actual,
                )

        for technology_id, values in payload["coefficients"].items():
            for year, expected_coefficient in values.items():
                try:
                    actual = effective_year_value(
                        case_data["RYTCn.json"],
                        "CCM",
                        scenario,
                        ("TechId", "ConId"),
                        (technology_id, constraint_id),
                        year,
                    )
                except ValueError:
                    actual = None
                if not values_close(actual, expected_coefficient, tolerance):
                    append_mismatch(
                        mismatches,
                        f"CCM:{scenario}:{technology_id}:{year}",
                        expected_coefficient,
                        actual,
                    )
            for parameter in ("CAM", "CNCM"):
                for year in expected["years"]:
                    try:
                        actual = effective_year_value(
                            case_data["RYTCn.json"],
                            parameter,
                            scenario,
                            ("TechId", "ConId"),
                            (technology_id, constraint_id),
                            year,
                        )
                    except ValueError:
                        actual = None
                    if not values_close(actual, 0.0, tolerance):
                        append_mismatch(
                            mismatches,
                            f"{parameter}:{scenario}:{technology_id}:{year}",
                            0,
                            actual,
                        )

    scenario_summary = {}
    for scenario, payload in expected["scenario_payload"].items():
        constants = payload["constants"]
        scenario_summary[scenario] = {
            "reserve_margin": payload["reserve_margin"],
            "first_year_requirement": -constants[expected["years"][0]],
            "last_year_requirement": -constants[expected["years"][-1]],
            "peak_timeslices": sorted(set(payload["peak_timeslices"].values())),
        }
    return {
        "status": "CURRENT" if not mismatches else "STALE",
        "case_folder": str(case_folder.resolve()),
        "constraint_id": constraint_id,
        "constraint_name": config["constraint_name"],
        "warning": WARNING,
        "input_fingerprint_sha256": expected["input_fingerprint_sha256"],
        "scenarios": scenario_summary,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def main() -> int:
    script_path = Path(__file__).resolve()
    package = script_path.parents[1]
    repository = script_path.parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Check or regenerate the Fiji MUIO reserve-margin UDC proxy. "
            "Checking is the default and never edits the case."
        )
    )
    parser.add_argument(
        "case_folder",
        nargs="?",
        type=Path,
        default=repository / "WebAPP/DataStorage/Fiji_CLEWs_Global",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="check the proxy and exit 2 if its derived values are stale (default)",
    )
    mode.add_argument(
        "--update",
        action="store_true",
        help="regenerate the proxy from current case data, then check it",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=package / "muio/reserve_margin_proxy_config.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optionally write the complete machine-readable check report",
    )
    parser.add_argument("--tolerance", type=float, default=1e-10)
    args = parser.parse_args()

    try:
        case_folder = args.case_folder.resolve()
        config = read_json(args.config.resolve())
        validate_config(config)
        case_data = load_case(case_folder)
        expected = expected_proxy(case_data, config)
        if args.update:
            install_proxy(case_folder, case_data, config, expected)
            case_data = load_case(case_folder)
        report = check_proxy(
            case_folder, case_data, config, expected, args.tolerance
        )
        if args.report:
            write_json(args.report.resolve(), report)

        print(
            f"{report['status']}: {report['constraint_name']} "
            f"({report['mismatch_count']} mismatch(es))"
        )
        for scenario, summary in report["scenarios"].items():
            print(
                f"  {scenario}: reserve margin={summary['reserve_margin']}, "
                f"requirement {expected['years'][0]}="
                f"{summary['first_year_requirement']:.12g}, "
                f"{expected['years'][-1]}="
                f"{summary['last_year_requirement']:.12g}, "
                f"peak timeslice(s)={','.join(summary['peak_timeslices'])}"
            )
        if report["mismatches"]:
            for mismatch in report["mismatches"][:10]:
                print(
                    f"  STALE {mismatch['location']}: "
                    f"expected={mismatch['expected']!r}, "
                    f"actual={mismatch['actual']!r}"
                )
            if len(report["mismatches"]) > 10:
                print(
                    f"  ... {len(report['mismatches']) - 10} more; "
                    "use --report for the complete list"
                )
            print("Run the same command with --update before solving.")
            return 2
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
