#!/usr/bin/env python3
"""Build the traceable Fiji v2 annual electricity calibration experiment.

The script always starts from the immutable Fiji_CLEWs_Global inputs and MUIO
parameter JSON, then applies the documented v2 transformations. It does not
copy or delete solver results.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
RAW_PACKAGE = REPO / "Fiji_CLEWs_Global"
V2_PACKAGE = REPO / "Fiji_v2_CLEWs_calibration"
RAW_INPUTS = RAW_PACKAGE / "model" / "inputs"
V2_INPUTS = V2_PACKAGE / "model" / "inputs"
RAW_CASE = REPO / "WebAPP" / "DataStorage" / "Fiji_CLEWs_Global"
V2_CASE = REPO / "WebAPP" / "DataStorage" / "Fiji_v2"
EVIDENCE = (
    V2_PACKAGE
    / "data_sources"
    / "evidence"
    / "calibration"
    / "historical_electricity_2020_2024.csv"
)
MANIFEST = V2_PACKAGE / "diagnostics" / "calibration_runs" / "build_manifest.json"

HISTORICAL_YEARS = tuple(range(2020, 2025))
CALIBRATION_YEARS = (2020, 2021, 2022)
VALIDATION_YEARS = (2023, 2024)
PJ_PER_MWH = 0.0000036
CAPACITY_TO_ACTIVITY = 31.536

TECHNOLOGIES = {
    "biomass": "PWRBIOFJIXX01",
    "hydro": "PWRHYDFJIXX01",
    "oil": "PWROILFJIXX01",
    "wind": "PWRWONFJIXX01",
}
REMOVED_UPSTREAM_TECHNOLOGIES = {"PWRTRNA01"}
REMOVED_UPSTREAM_FUELS = {"ELCFJI01", "ELCFJI02"}
REMOVE_JSON_VALUE = object()
OBSERVED_CAPACITY_GW = {
    "biomass": 0.034,
    "hydro": 0.1334,
    "oil": 0.182,
    "wind": 0.0098,
}
RAW_2021_CAPACITY_GW = {
    "biomass": 0.0697,
    "hydro": 0.209,
    "oil": 0.074,
    "wind": 0.010,
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def extend_csv_to_2020(path: Path) -> bool:
    fields, rows = read_csv(path)
    if path.name == "YEAR.csv":
        values = [row["VALUE"] for row in rows]
        if "2020" not in values:
            rows.insert(0, {"VALUE": "2020"})
            write_csv(path, fields, rows)
        return True
    if "YEAR" not in fields:
        return False
    if any(row["YEAR"] == "2020" for row in rows):
        return True
    expanded: list[dict[str, str]] = []
    for row in rows:
        if row["YEAR"] == "2021":
            clone = dict(row)
            clone["YEAR"] = "2020"
            expanded.append(clone)
        expanded.append(row)
    write_csv(path, fields, expanded)
    return True


def update_csv(
    path: Path,
    predicate: Callable[[dict[str, str]], bool],
    value: Callable[[dict[str, str]], float] | float,
) -> int:
    fields, rows = read_csv(path)
    changed = 0
    for row in rows:
        if predicate(row):
            new_value = value(row) if callable(value) else value
            row["VALUE"] = f"{float(new_value):.12g}"
            changed += 1
    write_csv(path, fields, rows)
    return changed


def remove_upstream_branch_from_csvs() -> dict[str, int]:
    """Remove the malformed land-code transmission branch from every CSV."""
    removed: dict[str, int] = {}
    for path in sorted(V2_INPUTS.glob("*.csv")):
        fields, rows = read_csv(path)
        kept: list[dict[str, str]] = []
        for row in rows:
            remove = (
                ("TECHNOLOGY" in fields and row["TECHNOLOGY"] in REMOVED_UPSTREAM_TECHNOLOGIES)
                or ("FUEL" in fields and row["FUEL"] in REMOVED_UPSTREAM_FUELS)
                or (
                    path.name == "TECHNOLOGY.csv"
                    and row["VALUE"] in REMOVED_UPSTREAM_TECHNOLOGIES
                )
                or (
                    path.name == "FUEL.csv"
                    and row["VALUE"] in REMOVED_UPSTREAM_FUELS
                )
            )
            if remove:
                removed[path.name] = removed.get(path.name, 0) + 1
            else:
                kept.append(row)
        if len(kept) != len(rows):
            write_csv(path, fields, kept)
    return removed


def load_evidence() -> dict[int, dict[str, str]]:
    _, rows = read_csv(EVIDENCE)
    return {int(row["year"]): row for row in rows}


def fitted_availability(
    evidence: dict[int, dict[str, str]], generation_field: str, capacity_gw: float
) -> float:
    mean_mwh = sum(
        float(evidence[year][generation_field]) for year in CALIBRATION_YEARS
    ) / len(CALIBRATION_YEARS)
    return mean_mwh * PJ_PER_MWH / (capacity_gw * CAPACITY_TO_ACTIVITY)


def clone_raw_files() -> None:
    V2_INPUTS.mkdir(parents=True, exist_ok=True)
    for source in RAW_INPUTS.glob("*.csv"):
        shutil.copy2(source, V2_INPUTS / source.name)
    V2_CASE.mkdir(parents=True, exist_ok=True)
    for source in RAW_CASE.glob("*.json"):
        shutil.copy2(source, V2_CASE / source.name)
    # MUIO stores run-stack metadata in ``view/``. Seed it only for a fresh
    # target and never reset an existing view during an idempotent rebuild.
    if not (V2_CASE / "view").is_dir() and (RAW_CASE / "view").is_dir():
        shutil.copytree(RAW_CASE / "view", V2_CASE / "view")


def add_2020_to_json(value: Any) -> None:
    if isinstance(value, dict):
        if "2021" in value and "2020" not in value:
            value["2020"] = value["2021"]
        for child in value.values():
            add_2020_to_json(child)
    elif isinstance(value, list):
        for child in value:
            add_2020_to_json(child)


def remove_entities_from_json(
    value: Any, targets: set[str]
) -> tuple[Any, int]:
    """Remove rows, list members, and mapping keys that reference target IDs."""
    if isinstance(value, dict):
        if any(
            isinstance(child, str) and child in targets
            for child in value.values()
        ):
            return REMOVE_JSON_VALUE, 1
        cleaned: dict[str, Any] = {}
        removed = 0
        for key, child in value.items():
            if key in targets:
                removed += 1
                continue
            cleaned_child, child_removed = remove_entities_from_json(child, targets)
            removed += child_removed
            if cleaned_child is not REMOVE_JSON_VALUE:
                cleaned[key] = cleaned_child
        return cleaned, removed
    if isinstance(value, list):
        cleaned_list: list[Any] = []
        removed = 0
        for child in value:
            if isinstance(child, str) and child in targets:
                removed += 1
                continue
            cleaned_child, child_removed = remove_entities_from_json(child, targets)
            removed += child_removed
            if cleaned_child is not REMOVE_JSON_VALUE:
                cleaned_list.append(cleaned_child)
        return cleaned_list, removed
    return value, 0


def parameter_rows(data: dict[str, Any], parameter: str) -> list[dict[str, Any]]:
    scenarios = data.get(parameter, {})
    if not isinstance(scenarios, dict):
        return []
    return scenarios.get("SC_0", [])


def set_json_parameter(
    data: dict[str, Any],
    parameter: str,
    id_field: str,
    entity_id: str,
    values: dict[int, float],
) -> int:
    changed = 0
    for row in parameter_rows(data, parameter):
        if row.get(id_field) == entity_id:
            for year, value in values.items():
                row[str(year)] = value
                changed += 1
    return changed


def transform_muiogo(
    historical_demand: dict[int, float],
    future_demand: dict[int, float],
    residual_capacity: dict[str, dict[int, float]],
    biomass_af: float,
    wind_af: float,
) -> dict[str, Any]:
    gen_path = V2_CASE / "genData.json"
    gen_data = json.loads(gen_path.read_text(encoding="utf-8"))
    tech_ids = {item["Tech"]: item["TechId"] for item in gen_data["osy-tech"]}
    commodity_ids = {item["Comm"]: item["CommId"] for item in gen_data["osy-comm"]}
    removed_ids = {
        tech_ids[name] for name in REMOVED_UPSTREAM_TECHNOLOGIES
    } | {
        commodity_ids[name] for name in REMOVED_UPSTREAM_FUELS
    }
    removal_targets = (
        REMOVED_UPSTREAM_TECHNOLOGIES
        | REMOVED_UPSTREAM_FUELS
        | removed_ids
    )
    json_removals: dict[str, int] = {}

    json_paths = [
        path
        for path in V2_CASE.rglob("*.json")
        if "res" not in path.relative_to(V2_CASE).parts
    ]
    for path in json_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        add_2020_to_json(data)
        cleaned, removed = remove_entities_from_json(data, removal_targets)
        if cleaned is REMOVE_JSON_VALUE:
            raise ValueError(f"Branch removal unexpectedly removed JSON root: {path}")
        if removed:
            json_removals[str(path.relative_to(V2_CASE))] = removed
        path.write_text(json.dumps(cleaned, indent=4) + "\n", encoding="utf-8")

    gen_data = json.loads(gen_path.read_text(encoding="utf-8"))
    tech_ids = {item["Tech"]: item["TechId"] for item in gen_data["osy-tech"]}
    commodity_ids = {item["Comm"]: item["CommId"] for item in gen_data["osy-comm"]}
    power_ids = [
        item["TechId"]
        for item in gen_data["osy-tech"]
        if str(item["Tech"]).startswith("PWR")
        and item["Tech"] != "PWRTRNFJIXX"
    ]

    gen_data["osy-casename"] = "Fiji_v2"
    gen_data["osy-desc"] = (
        "Fiji v2 annual electricity backcast: 2020-2022 calibration; "
        "2023-2024 held-out validation. Land, water, and agriculture remain "
        "uncalibrated."
    )
    gen_data["osy-date"] = date.today().isoformat()
    years = [str(year) for year in gen_data["osy-years"]]
    if "2020" not in years:
        years.insert(0, "2020")
    gen_data["osy-years"] = years
    gen_path.write_text(json.dumps(gen_data, indent=4) + "\n", encoding="utf-8")

    demand_values = historical_demand | future_demand
    parameter_files = [V2_CASE / "RYT.json", V2_CASE / "view" / "RYT.json"]
    for path in parameter_files:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for name, technology in TECHNOLOGIES.items():
            set_json_parameter(
                data,
                "RC",
                "TechId",
                tech_ids[technology],
                residual_capacity[name],
            )
        set_json_parameter(
            data,
            "AF",
            "TechId",
            tech_ids[TECHNOLOGIES["biomass"]],
            {year: biomass_af for year in range(2020, 2051)},
        )
        set_json_parameter(
            data,
            "AF",
            "TechId",
            tech_ids[TECHNOLOGIES["wind"]],
            {year: wind_af for year in HISTORICAL_YEARS},
        )
        for power_id in power_ids:
            set_json_parameter(
                data,
                "TAMaxCI",
                "TechId",
                power_id,
                {year: 0.0 for year in HISTORICAL_YEARS},
            )
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    for path in (V2_CASE / "RYC.json", V2_CASE / "view" / "RYC.json"):
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        set_json_parameter(
            data,
            "SAD",
            "CommId",
            commodity_ids["ELCFJIXX02"],
            demand_values,
        )
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    marker = V2_CASE / "reserve_margin_proxy.json"
    if marker.is_file():
        data = json.loads(marker.read_text(encoding="utf-8"))
        data["status"] = "DERIVED_VALUES_REQUIRE_CHECKING"
        data["check_command"] = (
            "python3 Fiji_v2_CLEWs_calibration/scripts/"
            "manage_reserve_margin_proxy.py WebAPP/DataStorage/Fiji_v2 --check"
        )
        data["update_command"] = (
            "python3 Fiji_v2_CLEWs_calibration/scripts/"
            "manage_reserve_margin_proxy.py WebAPP/DataStorage/Fiji_v2 --update"
        )
        marker.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    return {
        "technology_ids": {
            technology: tech_ids[technology]
            for technology in TECHNOLOGIES.values()
        },
        "demand_commodity_id": commodity_ids["ELCFJIXX02"],
        "power_technologies_blocked_2020_2024": len(power_ids),
        "removed_upstream_electricity_branch": {
            "technologies": sorted(REMOVED_UPSTREAM_TECHNOLOGIES),
            "fuels": sorted(REMOVED_UPSTREAM_FUELS),
            "muiogo_ids": sorted(removed_ids),
            "json_references_removed": json_removals,
        },
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    clone_raw_files()
    evidence = load_evidence()

    extended = 0
    for path in sorted(V2_INPUTS.glob("*.csv")):
        extended += int(extend_csv_to_2020(path))
    csv_branch_removals = remove_upstream_branch_from_csvs()

    historical_demand = {
        year: float(evidence[year]["total_generation_mwh"]) * PJ_PER_MWH
        for year in HISTORICAL_YEARS
    }
    demand_path = V2_INPUTS / "SpecifiedAnnualDemand.csv"
    _, demand_rows = read_csv(demand_path)
    raw_demand = {
        int(row["YEAR"]): float(row["VALUE"])
        for row in demand_rows
        if row["FUEL"] == "ELCFJIXX02"
    }
    future_scale = historical_demand[2024] / raw_demand[2024]
    future_demand = {
        year: raw_demand[year] * future_scale for year in range(2025, 2051)
    }
    update_csv(
        demand_path,
        lambda row: row["FUEL"] == "ELCFJIXX02"
        and int(row["YEAR"]) in historical_demand | future_demand,
        lambda row: (historical_demand | future_demand)[int(row["YEAR"])],
    )

    biomass_af = fitted_availability(
        evidence, "ipp_mwh", OBSERVED_CAPACITY_GW["biomass"]
    )
    wind_af = fitted_availability(
        evidence, "wind_mwh", OBSERVED_CAPACITY_GW["wind"]
    )

    rc_path = V2_INPUTS / "ResidualCapacity.csv"
    _, rc_rows = read_csv(rc_path)
    raw_rc = {
        (row["TECHNOLOGY"], int(row["YEAR"])): float(row["VALUE"]) for row in rc_rows
    }
    residual_capacity: dict[str, dict[int, float]] = {}
    for name, technology in TECHNOLOGIES.items():
        scale = OBSERVED_CAPACITY_GW[name] / RAW_2021_CAPACITY_GW[name]
        residual_capacity[name] = {}
        for year in range(2020, 2051):
            if year in HISTORICAL_YEARS:
                value = OBSERVED_CAPACITY_GW[name]
            else:
                value = raw_rc[(technology, year)] * scale
            residual_capacity[name][year] = value
        update_csv(
            rc_path,
            lambda row, technology=technology: row["TECHNOLOGY"] == technology,
            lambda row, name=name: residual_capacity[name][int(row["YEAR"])],
        )

    af_path = V2_INPUTS / "AvailabilityFactor.csv"
    update_csv(
        af_path,
        lambda row: row["TECHNOLOGY"] == TECHNOLOGIES["biomass"],
        biomass_af,
    )
    update_csv(
        af_path,
        lambda row: row["TECHNOLOGY"] == TECHNOLOGIES["wind"]
        and int(row["YEAR"]) in HISTORICAL_YEARS,
        wind_af,
    )

    technologies = {
        row["VALUE"]
        for row in read_csv(V2_INPUTS / "TECHNOLOGY.csv")[1]
        if row["VALUE"].startswith("PWR") and row["VALUE"] != "PWRTRNFJIXX"
    }
    hist_set = set(HISTORICAL_YEARS)
    blocked = update_csv(
        V2_INPUTS / "TotalAnnualMaxCapacityInvestment.csv",
        lambda row: row["TECHNOLOGY"] in technologies
        and int(row["YEAR"]) in hist_set,
        0.0,
    )

    muiogo = transform_muiogo(
        historical_demand,
        future_demand,
        residual_capacity,
        biomass_af,
        wind_af,
    )

    manifest = {
        "schema_version": 1,
        "build_date": date.today().isoformat(),
        "raw_package": str(RAW_PACKAGE.relative_to(REPO)),
        "raw_case": str(RAW_CASE.relative_to(REPO)),
        "target_package": str(V2_PACKAGE.relative_to(REPO)),
        "target_case": str(V2_CASE.relative_to(REPO)),
        "calibration_years": list(CALIBRATION_YEARS),
        "validation_years": list(VALIDATION_YEARS),
        "evidence_file": str(EVIDENCE.relative_to(REPO)),
        "evidence_sha256": sha256(EVIDENCE),
        "parameters": {
            "biomass_availability_factor": biomass_af,
            "wind_availability_factor_2020_2024": wind_af,
            "future_demand_scale_from_raw": future_scale,
            "observed_capacity_gw": OBSERVED_CAPACITY_GW,
            "historical_supply_requirement_pj": historical_demand,
        },
        "implementation": {
            "csv_files_extended_to_2020": extended,
            "removed_upstream_electricity_branch_csv_rows": csv_branch_removals,
            "historical_power_investment_cells_set_to_zero": blocked,
            **muiogo,
        },
        "claim_boundary": (
            "Annual national grid-supply mix only. Total supply and installed "
            "fleet are exogenous. No land, water, agriculture, hourly dispatch, "
            "reliability, network, or reservoir calibration claim."
        ),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
