#!/usr/bin/env python3
"""Apply Fiji Phase 1C sector-electricity accounting and projections.

Two reproducible checkpoints are supported:

``accounting``
    Split observed 2020-2024 gross grid demand into commercial, industrial,
    grid-residential and direct loss/residual demand. Leave the inherited
    aggregate projection unchanged from 2025.

``bottom-up``
    Use the same historical split, then replace the inherited aggregate
    projection with independent sector paths from 2025 to 2050.

Only source parameter files are changed. The script never copies or edits a
generated solver data file or result archive.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = PACKAGE / "model" / "inputs"
DEFAULT_MUIOGO = Path(__file__).resolve().parents[3] / "MUIOGO"
HISTORICAL_EVIDENCE = (
    PACKAGE
    / "data_sources"
    / "evidence"
    / "energy"
    / "fiji_energy_account_2024_electricity_boundary_2020_2024.csv"
)
DEFAULT_PROJECTION_EVIDENCE = (
    PACKAGE
    / "data_sources"
    / "evidence"
    / "energy"
    / "fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv"
)
PROXY_CONFIG = PACKAGE / "muio" / "reserve_margin_proxy_config.json"

BASE_SCENARIO = "SC_0"
HISTORICAL_YEARS = tuple(range(2020, 2025))
DEMAND_COMMODITIES = (
    "ELCFJIXX02",
    "COMELCFJIXX02",
    "INDELCFJIXX02",
    "RESELCFJIXX02",
)
SECTOR_ADAPTERS = (
    "DEMCOMELCFJIXX02",
    "DEMINDELCFJIXX02",
    "DEMRESELCFJIXX02",
)

# Fiji LEDS, BAU Unconditional scenario.
COMMERCIAL_GROWTH = 0.026
INDUSTRIAL_GROWTH = 0.020
HOUSEHOLD_GROWTH = 0.0038
BASE_HOUSEHOLDS_2013 = 182_282.0

# Fiji MICS 2021, Table SR.2.1. These are central-grid access rates, not total
# electrification rates; off-grid household electricity is outside ELC demand.
URBAN_GRID_ACCESS = 0.939
RURAL_GRID_ACCESS = 0.742

URBAN_FRACTION = {
    2013: 0.5298,
    2020: 0.5557,
    2025: 0.5737,
    2030: 0.5897,
    2035: 0.6051,
    2040: 0.6201,
    2045: 0.6346,
    2050: 0.6493,
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(value, stream, indent=4, ensure_ascii=False)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_fingerprints(case_path: Path) -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted(case_path.glob("*.json"))
        if path.is_file()
    }


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(
    path: Path, fields: list[str], rows: list[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", newline="", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def interpolate(year: int, milestones: dict[int, float]) -> float:
    points = sorted(milestones)
    if year <= points[0]:
        return milestones[points[0]]
    if year >= points[-1]:
        return milestones[points[-1]]
    lower = max(point for point in points if point <= year)
    upper = min(point for point in points if point >= year)
    if lower == upper:
        return milestones[lower]
    position = (year - lower) / (upper - lower)
    return milestones[lower] + position * (
        milestones[upper] - milestones[lower]
    )


def blended_intensity(
    year: int,
    *,
    conventional: float,
    efficient: float,
    efficient_share: dict[int, float],
) -> float:
    share = interpolate(year, efficient_share)
    return conventional * (1.0 - share) + efficient * share


def household_driver(year: int) -> dict[str, float]:
    """Return the LEDS/MICS central-grid household electricity driver."""
    households = BASE_HOUSEHOLDS_2013 * (
        (1.0 + HOUSEHOLD_GROWTH) ** (year - 2013)
    )
    urban_share = interpolate(year, URBAN_FRACTION)
    urban_grid_households = households * urban_share * URBAN_GRID_ACCESS
    rural_grid_households = (
        households * (1.0 - urban_share) * RURAL_GRID_ACCESS
    )

    refrigerator_intensity = blended_intensity(
        year,
        conventional=480.0,
        efficient=440.0,
        efficient_share={2014: 0.0, 2030: 1.0, 2050: 1.0},
    )
    lighting_intensity = blended_intensity(
        year,
        conventional=301.0,
        efficient=243.0,
        efficient_share={2015: 0.0, 2030: 1.0, 2050: 1.0},
    )
    air_conditioning_intensity = blended_intensity(
        year,
        conventional=1500.0,
        efficient=1300.0,
        efficient_share={2020: 0.0, 2030: 0.30, 2050: 1.0},
    )
    television_intensity = blended_intensity(
        year,
        conventional=240.0,
        efficient=150.0,
        efficient_share={2020: 0.0, 2030: 1.0, 2050: 1.0},
    )

    urban_refrigerator_adoption = interpolate(
        year, {2014: 0.75, 2030: 0.80, 2050: 0.90}
    )
    rural_refrigerator_adoption = interpolate(
        year, {2014: 0.66, 2030: 0.70, 2050: 0.80}
    )
    urban_air_conditioning_adoption = interpolate(
        year, {2020: 0.05, 2050: 0.20}
    )

    urban_kwh_per_grid_household = (
        urban_refrigerator_adoption * refrigerator_intensity
        + lighting_intensity
        + urban_air_conditioning_adoption * air_conditioning_intensity
        + 0.90 * television_intensity
        + 500.0
    )
    rural_kwh_per_grid_household = (
        rural_refrigerator_adoption * refrigerator_intensity
        + lighting_intensity
        + 0.90 * television_intensity
        + 500.0
    )
    composite_kwh = (
        urban_grid_households * urban_kwh_per_grid_household
        + rural_grid_households * rural_kwh_per_grid_household
    )
    return {
        "households": households,
        "urban_fraction": urban_share,
        "urban_grid_households": urban_grid_households,
        "rural_grid_households": rural_grid_households,
        "urban_kwh_per_grid_household": urban_kwh_per_grid_household,
        "rural_kwh_per_grid_household": rural_kwh_per_grid_household,
        "composite_kwh": composite_kwh,
    }


def historical_rows() -> dict[int, dict[str, float]]:
    _, rows = read_csv(HISTORICAL_EVIDENCE)
    result: dict[int, dict[str, float]] = {}
    for row in rows:
        year = int(row["year"])
        result[year] = {
            key: float(value)
            for key, value in row.items()
            if key not in {"year", "source_and_calculation"} and value != ""
        }
    if set(result) != set(HISTORICAL_YEARS):
        raise ValueError(
            f"Historical evidence must cover {HISTORICAL_YEARS[0]}-"
            f"{HISTORICAL_YEARS[-1]}"
        )
    return result


def bottom_up_projection(years: list[int]) -> dict[int, dict[str, float]]:
    history = historical_rows()
    anchor = history[2024]
    anchor_end_use = (
        anchor["commercial_grid_use_pj"]
        + anchor["industrial_grid_use_pj"]
        + anchor["inferred_grid_domestic_use_pj"]
    )
    overhead_ratio = (
        anchor["distribution_loss_pj"]
        + anchor["residual_station_use_and_boundary_reconciliation_pj"]
    ) / anchor_end_use
    residential_anchor_driver = household_driver(2024)["composite_kwh"]

    result: dict[int, dict[str, float]] = {}
    for year in years:
        if year in history:
            item = history[year]
            commercial = item["commercial_grid_use_pj"]
            industrial = item["industrial_grid_use_pj"]
            residential = item["inferred_grid_domestic_use_pj"]
            direct = (
                item["distribution_loss_pj"]
                + item[
                    "residual_station_use_and_boundary_reconciliation_pj"
                ]
            )
            driver = household_driver(year)
            basis = "observed"
        else:
            driver = household_driver(year)
            commercial = anchor["commercial_grid_use_pj"] * (
                (1.0 + COMMERCIAL_GROWTH) ** (year - 2024)
            )
            industrial = anchor["industrial_grid_use_pj"] * (
                (1.0 + INDUSTRIAL_GROWTH) ** (year - 2024)
            )
            residential = anchor["inferred_grid_domestic_use_pj"] * (
                driver["composite_kwh"] / residential_anchor_driver
            )
            direct = overhead_ratio * (
                commercial + industrial + residential
            )
            basis = "projected"
        gross = commercial + industrial + residential + direct
        result[year] = {
            "ELCFJIXX02": direct,
            "COMELCFJIXX02": commercial,
            "INDELCFJIXX02": industrial,
            "RESELCFJIXX02": residential,
            "gross_grid_requirement_pj": gross,
            "overhead_ratio_on_end_use": overhead_ratio,
            "households": driver["households"],
            "urban_fraction": driver["urban_fraction"],
            "urban_grid_households": driver["urban_grid_households"],
            "rural_grid_households": driver["rural_grid_households"],
            "urban_kwh_per_grid_household": driver[
                "urban_kwh_per_grid_household"
            ],
            "rural_kwh_per_grid_household": driver[
                "rural_kwh_per_grid_household"
            ],
            "residential_driver_index_2024_1": (
                driver["composite_kwh"] / residential_anchor_driver
            ),
            "basis": basis,
        }
    return result


def parameter_row(
    data: dict[str, Any],
    parameter: str,
    **identifiers: Any,
) -> dict[str, Any]:
    matches = [
        row
        for row in data[parameter][BASE_SCENARIO]
        if all(row.get(key) == value for key, value in identifiers.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {identifiers}, "
            f"found {len(matches)}"
        )
    return matches[0]


def copy_case_sources(source: Path, stage: Path) -> None:
    for source_file in sorted(source.glob("*.json")):
        shutil.copy2(source_file, stage / source_file.name)
    for name in ("README.md",):
        if (source / name).is_file():
            shutil.copy2(source / name, stage / name)
    view_source = source / "view"
    view_target = stage / "view"
    view_target.mkdir()
    for name in ("resData.json", "viewDefinitions.json"):
        if (view_source / name).is_file():
            shutil.copy2(view_source / name, view_target / name)
    if not (view_target / "resData.json").is_file():
        write_json(view_target / "resData.json", {"osy-cases": []})
    if not (view_target / "viewDefinitions.json").is_file():
        write_json(view_target / "viewDefinitions.json", {})


def inherited_demand(case_path: Path, comm_ids: dict[str, str]) -> dict[int, float]:
    data = read_json(case_path / "RYC.json")
    row = parameter_row(
        data, "SAD", CommId=comm_ids["ELCFJIXX02"]
    )
    return {
        int(year): float(row[str(year)])
        for year in read_json(case_path / "genData.json")["osy-years"]
    }


def aggregate_demand(case_path: Path) -> dict[int, float]:
    """Return total annual demand across the Phase 1C electricity boundary."""
    gen_data = read_json(case_path / "genData.json")
    comm_ids = {
        str(item["Comm"]): str(item["CommId"])
        for item in gen_data["osy-comm"]
    }
    missing = sorted(set(DEMAND_COMMODITIES) - comm_ids.keys())
    if missing:
        raise ValueError(
            f"Comparison case {case_path.name} is missing demand commodities: "
            + ", ".join(missing)
        )
    data = read_json(case_path / "RYC.json")
    years = [int(year) for year in gen_data["osy-years"]]
    totals = {year: 0.0 for year in years}
    for commodity in DEMAND_COMMODITIES:
        row = parameter_row(data, "SAD", CommId=comm_ids[commodity])
        for year in years:
            totals[year] += float(row[str(year)])
    return totals


def demand_for_checkpoint(
    *,
    checkpoint: str,
    years: list[int],
    inherited: dict[int, float],
    projected: dict[int, dict[str, float]],
) -> dict[int, dict[str, float]]:
    result: dict[int, dict[str, float]] = {}
    for year in years:
        if checkpoint == "bottom-up" or year in HISTORICAL_YEARS:
            result[year] = {
                commodity: projected[year][commodity]
                for commodity in DEMAND_COMMODITIES
            }
        else:
            result[year] = {
                "ELCFJIXX02": inherited[year],
                "COMELCFJIXX02": 0.0,
                "INDELCFJIXX02": 0.0,
                "RESELCFJIXX02": 0.0,
            }
    return result


def apply_parameter_values(
    case_path: Path, checkpoint: str
) -> dict[str, Any]:
    gen_data_path = case_path / "genData.json"
    gen_data = read_json(gen_data_path)
    years = [int(year) for year in gen_data["osy-years"]]
    comm_ids = {
        str(item["Comm"]): str(item["CommId"])
        for item in gen_data["osy-comm"]
    }
    tech_ids = {
        str(item["Tech"]): str(item["TechId"])
        for item in gen_data["osy-tech"]
    }
    missing = sorted(set(DEMAND_COMMODITIES) - comm_ids.keys())
    if missing:
        raise ValueError("Missing demand commodities: " + ", ".join(missing))
    missing_adapters = sorted(set(SECTOR_ADAPTERS) - tech_ids.keys())
    if missing_adapters:
        raise ValueError(
            "Missing sector adapters: " + ", ".join(missing_adapters)
        )

    projected = bottom_up_projection(years)
    inherited = inherited_demand(case_path, comm_ids)
    demand = demand_for_checkpoint(
        checkpoint=checkpoint,
        years=years,
        inherited=inherited,
        projected=projected,
    )

    ryc_path = case_path / "RYC.json"
    ryc = read_json(ryc_path)
    for commodity in DEMAND_COMMODITIES:
        row = parameter_row(
            ryc, "SAD", CommId=comm_ids[commodity]
        )
        for year in years:
            row[str(year)] = demand[year][commodity]
    write_json(ryc_path, ryc)

    rycts_path = case_path / "RYCTs.json"
    rycts = read_json(rycts_path)
    aggregate_profiles: dict[tuple[str, int], float] = {}
    for timeslice in gen_data["osy-ts"]:
        timeslice_id = str(timeslice["TsId"])
        row = parameter_row(
            rycts,
            "SDP",
            CommId=comm_ids["ELCFJIXX02"],
            TsId=timeslice_id,
        )
        for year in years:
            aggregate_profiles[(timeslice_id, year)] = float(
                row[str(year)]
            )
    for commodity in DEMAND_COMMODITIES:
        for timeslice in gen_data["osy-ts"]:
            timeslice_id = str(timeslice["TsId"])
            row = parameter_row(
                rycts,
                "SDP",
                CommId=comm_ids[commodity],
                TsId=timeslice_id,
            )
            for year in years:
                row[str(year)] = (
                    aggregate_profiles[(timeslice_id, year)]
                    if demand[year][commodity] > 0
                    else 0.0
                )
    write_json(rycts_path, rycts)

    # The inherited 0.0001 default variable cost is only a numerical
    # placeholder. These 1:1 accounting adapters must not change the
    # objective when gross electricity demand is unchanged.
    rytm_path = case_path / "RYTM.json"
    rytm = read_json(rytm_path)
    for technology in SECTOR_ADAPTERS:
        row = parameter_row(
            rytm,
            "VC",
            TechId=tech_ids[technology],
            MoId=1,
        )
        for year in years:
            row[str(year)] = 0.0
    write_json(rytm_path, rytm)

    gen_data["osy-desc"] = (
        "Fiji v2 Phase 1C electricity accounting"
        + (
            " with observed 2020-2024 sector demand and Fiji LEDS "
            "bottom-up/sector-specific projections for 2025-2050."
            if checkpoint == "bottom-up"
            else " checkpoint with observed 2020-2024 sector demand."
        )
    )
    gen_data["osy-date"] = date.today().isoformat()
    write_json(gen_data_path, gen_data)

    first_projection = 2025
    last_year = max(years)
    return {
        "checkpoint": checkpoint,
        "historical_reconciliation": {
            year: {
                "gross_pj": sum(demand[year].values()),
                "inherited_gross_pj": inherited[year],
                "difference_pj": sum(demand[year].values())
                - inherited[year],
            }
            for year in HISTORICAL_YEARS
        },
        "projection": {
            "first_year": first_projection,
            "last_year": last_year,
            "gross_pj": {
                first_projection: sum(demand[first_projection].values()),
                last_year: sum(demand[last_year].values()),
            },
            "inherited_gross_pj": {
                first_projection: inherited[first_projection],
                last_year: inherited[last_year],
            },
        },
        "profiles": (
            "Existing aggregate ELC profile applied to each positive "
            "demand component; sector-specific profiles are not available."
        ),
        "sector_adapter_variable_cost": 0.0,
    }


def update_reserve_proxy(case_path: Path) -> dict[str, Any]:
    sys.path.insert(0, str(PACKAGE / "scripts"))
    from manage_reserve_margin_proxy import (
        check_proxy,
        expected_proxy,
        install_proxy,
        load_case,
        validate_config,
    )

    config = read_json(PROXY_CONFIG)
    validate_config(config)
    case_data = load_case(case_path)
    expected = expected_proxy(case_data, config)
    install_proxy(case_path, case_data, config, expected)
    refreshed = load_case(case_path)
    report = check_proxy(
        case_path, refreshed, config, expected, tolerance=1e-10
    )
    if report["status"] != "CURRENT":
        raise RuntimeError(
            "Reserve-margin proxy did not refresh cleanly: "
            + json.dumps(report["mismatches"][:3])
        )
    return {
        "status": report["status"],
        "mismatch_count": report["mismatch_count"],
        "input_fingerprint_sha256": expected[
            "input_fingerprint_sha256"
        ],
    }


def install_case(
    *,
    source_case: Path,
    target_case: Path,
    checkpoint: str,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, Any]:
    storage = source_case.parent
    before = source_fingerprints(source_case)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{target_case.name}.phase1c-", dir=storage
        )
    )
    try:
        copy_case_sources(source_case, stage)
        gen_data = read_json(stage / "genData.json")
        gen_data["osy-casename"] = target_case.name
        write_json(stage / "genData.json", gen_data)
        parameters = apply_parameter_values(stage, checkpoint)
        proxy = update_reserve_proxy(stage)
        after = source_fingerprints(stage)
        changed_files = sorted(
            name for name, digest in after.items()
            if before.get(name) != digest
        )

        if dry_run:
            return {
                "dry_run": True,
                "source_case": source_case.name,
                "target_case": target_case.name,
                "changed_files": changed_files,
                "parameters": parameters,
                "reserve_proxy": proxy,
            }

        if target_case == source_case:
            for staged_file in sorted(stage.glob("*.json")):
                destination = target_case / staged_file.name
                temporary = destination.with_suffix(
                    destination.suffix + ".phase1c"
                )
                shutil.copy2(staged_file, temporary)
                os.replace(temporary, destination)
        else:
            if target_case.exists():
                if not overwrite:
                    raise FileExistsError(
                        f"Target exists: {target_case}; pass --overwrite"
                    )
                backup = target_case.with_name(
                    target_case.name + ".phase1c-backup"
                )
                if backup.exists():
                    shutil.rmtree(backup)
                target_case.rename(backup)
                try:
                    stage.rename(target_case)
                except Exception:
                    backup.rename(target_case)
                    raise
                shutil.rmtree(backup)
                stage = target_case
            else:
                stage.rename(target_case)
                stage = target_case

        return {
            "dry_run": False,
            "source_case": source_case.name,
            "target_case": target_case.name,
            "changed_files": changed_files,
            "parameters": parameters,
            "reserve_proxy": proxy,
            "source_fingerprints_before": before,
            "target_fingerprints_after": source_fingerprints(target_case),
        }
    finally:
        if stage.exists() and stage != target_case:
            shutil.rmtree(stage)


def replace_parameter_rows(
    path: Path,
    *,
    remove: Any,
    additions: list[dict[str, Any]],
) -> tuple[int, int]:
    fields, rows = read_csv(path)
    kept = [row for row in rows if not remove(row)]
    removed = len(rows) - len(kept)
    normalized = [
        {field: str(row[field]) for field in fields}
        for row in additions
    ]
    write_csv(path, fields, kept + normalized)
    return removed, len(normalized)


def csv_projection(
    *,
    inputs: Path,
    source_case: Path,
    checkpoint: str,
    dry_run: bool,
) -> dict[str, Any]:
    gen_data = read_json(source_case / "genData.json")
    years = [int(year) for year in gen_data["osy-years"]]
    comm_ids = {
        str(item["Comm"]): str(item["CommId"])
        for item in gen_data["osy-comm"]
    }
    projected = bottom_up_projection(years)
    inherited = inherited_demand(source_case, comm_ids)
    demand = demand_for_checkpoint(
        checkpoint=checkpoint,
        years=years,
        inherited=inherited,
        projected=projected,
    )
    if dry_run:
        return {
            "dry_run": True,
            "inputs": str(inputs),
            "checkpoint": checkpoint,
        }

    demand_rows = [
        {
            "REGION": "GLOBAL",
            "FUEL": commodity,
            "YEAR": year,
            "VALUE": f"{demand[year][commodity]:.12g}",
        }
        for commodity in DEMAND_COMMODITIES
        for year in years
        if demand[year][commodity] > 0
    ]
    demand_removed, demand_added = replace_parameter_rows(
        inputs / "SpecifiedAnnualDemand.csv",
        remove=lambda row: row["FUEL"] in DEMAND_COMMODITIES,
        additions=demand_rows,
    )

    _, existing_profiles = read_csv(
        inputs / "SpecifiedDemandProfile.csv"
    )
    profile_lookup = {
        (row["TIMESLICE"], int(row["YEAR"])): float(row["VALUE"])
        for row in existing_profiles
        if row["FUEL"] == "ELCFJIXX02"
    }
    timeslices = sorted(
        {timeslice for timeslice, _ in profile_lookup}
    )
    profile_rows = [
        {
            "REGION": "GLOBAL",
            "FUEL": commodity,
            "TIMESLICE": timeslice,
            "YEAR": year,
            "VALUE": f"{profile_lookup[(timeslice, year)]:.12g}",
        }
        for commodity in DEMAND_COMMODITIES
        for timeslice in timeslices
        for year in years
        if demand[year][commodity] > 0
    ]
    profile_removed, profile_added = replace_parameter_rows(
        inputs / "SpecifiedDemandProfile.csv",
        remove=lambda row: row["FUEL"] in DEMAND_COMMODITIES,
        additions=profile_rows,
    )
    variable_cost_rows = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": technology,
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": 0.0,
        }
        for technology in SECTOR_ADAPTERS
        for year in years
    ]
    variable_cost_removed, variable_cost_added = replace_parameter_rows(
        inputs / "VariableCost.csv",
        remove=lambda row: (
            row["TECHNOLOGY"] in SECTOR_ADAPTERS
            and int(row["MODE_OF_OPERATION"]) == 1
        ),
        additions=variable_cost_rows,
    )
    return {
        "dry_run": False,
        "inputs": str(inputs),
        "checkpoint": checkpoint,
        "SpecifiedAnnualDemand": {
            "removed": demand_removed,
            "added": demand_added,
        },
        "SpecifiedDemandProfile": {
            "removed": profile_removed,
            "added": profile_added,
        },
        "VariableCost": {
            "removed": variable_cost_removed,
            "added": variable_cost_added,
        },
    }


def write_projection_evidence(
    path: Path,
    source_case: Path,
    comparison_case: Path,
) -> dict[str, Any]:
    gen_data = read_json(source_case / "genData.json")
    years = [int(year) for year in gen_data["osy-years"]]
    comparison = aggregate_demand(comparison_case)
    if set(comparison) != set(years):
        raise ValueError(
            "Projection and comparison cases do not cover identical years"
        )
    projection = bottom_up_projection(years)
    fields = [
        "year",
        "basis",
        "commercial_grid_use_pj",
        "industrial_grid_use_pj",
        "grid_residential_use_pj",
        "direct_loss_and_boundary_overhead_pj",
        "bottom_up_gross_grid_requirement_pj",
        "phase1b_accounting_control_gross_grid_requirement_pj",
        "difference_from_phase1b_control_pj",
        "overhead_ratio_on_end_use",
        "households",
        "urban_fraction",
        "urban_grid_households",
        "rural_grid_households",
        "urban_kwh_per_grid_household",
        "rural_kwh_per_grid_household",
        "residential_driver_index_2024_1",
    ]
    rows = []
    for year in years:
        item = projection[year]
        rows.append(
            {
                "year": year,
                "basis": item["basis"],
                "commercial_grid_use_pj": f"{item['COMELCFJIXX02']:.12f}",
                "industrial_grid_use_pj": f"{item['INDELCFJIXX02']:.12f}",
                "grid_residential_use_pj": f"{item['RESELCFJIXX02']:.12f}",
                "direct_loss_and_boundary_overhead_pj": (
                    f"{item['ELCFJIXX02']:.12f}"
                ),
                "bottom_up_gross_grid_requirement_pj": (
                    f"{item['gross_grid_requirement_pj']:.12f}"
                ),
                "phase1b_accounting_control_gross_grid_requirement_pj": (
                    f"{comparison[year]:.12f}"
                ),
                "difference_from_phase1b_control_pj": (
                    f"{item['gross_grid_requirement_pj'] - comparison[year]:.12f}"
                ),
                "overhead_ratio_on_end_use": (
                    f"{item['overhead_ratio_on_end_use']:.12f}"
                ),
                "households": f"{item['households']:.6f}",
                "urban_fraction": f"{item['urban_fraction']:.8f}",
                "urban_grid_households": (
                    f"{item['urban_grid_households']:.6f}"
                ),
                "rural_grid_households": (
                    f"{item['rural_grid_households']:.6f}"
                ),
                "urban_kwh_per_grid_household": (
                    f"{item['urban_kwh_per_grid_household']:.6f}"
                ),
                "rural_kwh_per_grid_household": (
                    f"{item['rural_kwh_per_grid_household']:.6f}"
                ),
                "residential_driver_index_2024_1": (
                    f"{item['residential_driver_index_2024_1']:.12f}"
                ),
            }
        )
    write_csv(path, fields, rows)
    return {
        "path": str(path),
        "rows": len(rows),
        "comparison_case": str(comparison_case),
        "sha256": sha256(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        choices=("accounting", "bottom-up"),
        default="bottom-up",
    )
    parser.add_argument(
        "--muiogo-root", type=Path, default=DEFAULT_MUIOGO
    )
    parser.add_argument("--source-case", default="Fiji_v2")
    parser.add_argument("--target-case")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--sync-csv-inputs", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument(
        "--evidence-only",
        action="store_true",
        help="Write the projection evidence CSV without creating a case.",
    )
    parser.add_argument(
        "--projection-evidence",
        type=Path,
        default=DEFAULT_PROJECTION_EVIDENCE,
    )
    parser.add_argument(
        "--comparison-case",
        default="Fiji_v2_Phase1C_Accounting_Test",
        help=(
            "Accounting-control case used only for projection-evidence "
            "comparison columns."
        ),
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    muiogo_root = args.muiogo_root.resolve()
    if not (muiogo_root / "API").is_dir():
        raise SystemExit(f"Not a MUIOGO repository: {muiogo_root}")
    storage = muiogo_root / "WebAPP" / "DataStorage"
    source_case = storage / args.source_case
    if not source_case.is_dir():
        raise SystemExit(f"Missing source case: {source_case}")
    comparison_case = storage / args.comparison_case
    if (
        args.evidence_only or args.write_evidence
    ) and not comparison_case.is_dir():
        raise SystemExit(f"Missing comparison case: {comparison_case}")
    if args.evidence_only:
        if args.dry_run:
            raise SystemExit("--evidence-only cannot be combined with --dry-run")
        print(
            json.dumps(
                {
                    "phase": "1C sector electricity",
                    "date": date.today().isoformat(),
                    "projection_evidence": write_projection_evidence(
                        args.projection_evidence.resolve(),
                        source_case,
                        comparison_case,
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    target_name = args.target_case or (
        "Fiji_v2_Phase1C_Accounting_Test"
        if args.checkpoint == "accounting"
        else "Fiji_v2_Phase1C_BottomUp_Test"
    )
    target_case = storage / target_name

    report: dict[str, Any] = {
        "phase": "1C sector electricity",
        "date": date.today().isoformat(),
        "case": install_case(
            source_case=source_case,
            target_case=target_case,
            checkpoint=args.checkpoint,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        ),
    }
    if args.sync_csv_inputs:
        report["csv_inputs"] = csv_projection(
            inputs=args.inputs.resolve(),
            source_case=source_case,
            checkpoint=args.checkpoint,
            dry_run=args.dry_run,
        )
    if args.write_evidence and not args.dry_run:
        report["projection_evidence"] = write_projection_evidence(
            args.projection_evidence.resolve(),
            source_case,
            comparison_case,
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
