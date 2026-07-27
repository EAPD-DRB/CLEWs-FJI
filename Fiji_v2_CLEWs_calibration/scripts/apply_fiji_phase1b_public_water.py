#!/usr/bin/env python3
"""Apply Fiji Phase 1B public-water closure reproducibly.

The transformation is intentionally narrow:

* add a raw-groundwater abstraction layer between annual recharge and public
  water supply;
* remove the unsupported commercial-electricity input from public groundwater;
* quarantine public groundwater until Fiji-specific source and pumping data
  are available;
* impose observed 2020-2024 billed public-water delivery as annual demand; and
* represent reported purification/distribution losses through the observed
  annual surface-water input-to-delivery ratio.

Structural MUIO edits are passed through ``UpdateCase``. Solver files and
saved results are never copied into or edited by this script.
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
HISTORICAL_YEARS = tuple(range(2020, 2025))

# Fiji Bureau of Statistics, Fiji's Experimental Environmental Account for
# Water 2024, Appendix, unit ML. Public delivery is the sum of billed
# household, government, commercial and carted-water use.
PUBLIC_WATER_ML = {
    2020: {
        "surface_extracted": 143_660.0,
        "purification_loss": 6_227.0,
        "distribution_loss": 67_354.0,
        "delivered": 70_079.0,
    },
    2021: {
        "surface_extracted": 140_979.0,
        "purification_loss": 6_421.0,
        "distribution_loss": 63_487.0,
        "delivered": 71_071.0,
    },
    2022: {
        "surface_extracted": 141_298.0,
        "purification_loss": 6_937.0,
        "distribution_loss": 65_067.0,
        "delivered": 69_294.0,
    },
    2023: {
        "surface_extracted": 138_941.0,
        "purification_loss": 6_144.0,
        "distribution_loss": 64_465.0,
        "delivered": 68_332.0,
    },
    2024: {
        "surface_extracted": 151_467.0,
        "purification_loss": 6_849.0,
        "distribution_loss": 77_527.0,
        "delivered": 67_091.0,
    },
}

NEW_TECH_NAME = "WTRABSFJI"
NEW_TECH_ID = "TEC_phase1b_wtrabs"
NEW_COMM_NAME = "WTRGWRFJI"
NEW_COMM_ID = "COM_phase1b_wtrgwr"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(value, stream, indent=4)
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


def entity_map(items: list[dict[str, Any]], name_field: str, id_field: str) -> dict[str, str]:
    return {str(item[name_field]): str(item[id_field]) for item in items}


def require_entities(mapping: dict[str, str], names: set[str], kind: str) -> None:
    missing = sorted(names - mapping.keys())
    if missing:
        raise ValueError(f"Missing required {kind}: {', '.join(missing)}")


def update_gen_data(gen_data: dict[str, Any]) -> dict[str, Any]:
    technologies = gen_data["osy-tech"]
    commodities = gen_data["osy-comm"]
    tech_ids = entity_map(technologies, "Tech", "TechId")
    comm_ids = entity_map(commodities, "Comm", "CommId")

    require_entities(
        tech_ids,
        {"DEMPUBGWTFJI", "DEMPUBSURFJI", "DEMAGRGWTFJI", "DEMAGRSURFJI"},
        "technologies",
    )
    require_entities(
        comm_ids,
        {
            "COMELCFJIXX02",
            "WTRGRCFJI",
            "WTRSURFJI",
            "WTRPRCFJI",
            "WTREVTFJI",
            "PUBWATFJI",
            "AGRWATFJI",
        },
        "commodities",
    )
    if NEW_TECH_NAME in tech_ids and tech_ids[NEW_TECH_NAME] != NEW_TECH_ID:
        raise ValueError(
            f"Collision: {NEW_TECH_NAME} uses {tech_ids[NEW_TECH_NAME]}, "
            f"expected {NEW_TECH_ID}"
        )
    if NEW_TECH_ID in tech_ids.values() and NEW_TECH_NAME not in tech_ids:
        raise ValueError(f"Collision: {NEW_TECH_ID} belongs to another technology")
    if NEW_COMM_NAME in comm_ids and comm_ids[NEW_COMM_NAME] != NEW_COMM_ID:
        raise ValueError(
            f"Collision: {NEW_COMM_NAME} uses {comm_ids[NEW_COMM_NAME]}, "
            f"expected {NEW_COMM_ID}"
        )
    if NEW_COMM_ID in comm_ids.values() and NEW_COMM_NAME not in comm_ids:
        raise ValueError(f"Collision: {NEW_COMM_ID} belongs to another commodity")

    new_commodity = {
        "CommId": NEW_COMM_ID,
        "Comm": NEW_COMM_NAME,
        "Desc": (
            "Raw groundwater abstracted from modeled annual recharge; "
            "Phase 1B placeholder, inactive until Fiji public-groundwater "
            "evidence is supplied."
        ),
        "UnitId": "km3",
    }
    if NEW_COMM_NAME in comm_ids:
        next(
            item for item in commodities if item["Comm"] == NEW_COMM_NAME
        ).update(new_commodity)
    else:
        commodities.append(new_commodity)
    comm_ids[NEW_COMM_NAME] = NEW_COMM_ID

    water_group = next(
        (
            group
            for item in technologies
            if item["Tech"] == "DEMPUBSURFJI"
            for group in item.get("TG", [])
        ),
        None,
    )
    if water_group is None:
        raise ValueError("DEMPUBSURFJI has no water technology group")

    new_technology = {
        "TechId": NEW_TECH_ID,
        "Tech": NEW_TECH_NAME,
        "Desc": (
            "Groundwater abstraction accounting layer: annual recharge "
            "to raw abstracted groundwater. Inactive in Phase 1B."
        ),
        "CapUnitId": "km3/year",
        "ActUnitId": "km3",
        "IAR": [comm_ids["WTRGRCFJI"]],
        "OAR": [NEW_COMM_ID],
        "EAR": [],
        "INCR": [],
        "ITCR": [],
        "TG": [water_group],
    }
    if NEW_TECH_NAME in tech_ids:
        next(
            item for item in technologies if item["Tech"] == NEW_TECH_NAME
        ).update(new_technology)
    else:
        technologies.append(new_technology)

    commodity_metadata = {
        "WTRPRCFJI": ("Annual precipitation water flux.", "km3"),
        "WTREVTFJI": ("Annual evapotranspiration water flux.", "km3"),
        "WTRGRCFJI": (
            "Modeled annual groundwater recharge from land-water balance.",
            "km3",
        ),
        "WTRSURFJI": ("Modeled annual surface-water runoff resource.", "km3"),
        "AGRWATFJI": ("Delivered agricultural water service.", "km3"),
        "PUBWATFJI": ("Billed public-water delivery service.", "km3"),
    }
    for item in commodities:
        if item["Comm"] in commodity_metadata:
            item["Desc"], item["UnitId"] = commodity_metadata[item["Comm"]]

    technology_metadata = {
        "DEMAGRGWTFJI": (
            "Agricultural groundwater delivery; retained for later "
            "agriculture-water calibration."
        ),
        "DEMAGRSURFJI": (
            "Agricultural surface-water delivery; retained for later "
            "agriculture-water calibration."
        ),
        "DEMPUBGWTFJI": (
            "Public groundwater delivery from raw abstracted groundwater; "
            "quarantined pending Fiji source and pumping evidence."
        ),
        "DEMPUBSURFJI": (
            "Public surface-water supply from modeled runoff to billed "
            "delivery; historical ratios include reported water losses."
        ),
    }
    for item in technologies:
        name = item["Tech"]
        if name in technology_metadata:
            item["Desc"] = technology_metadata[name]
            item["CapUnitId"] = "km3/year"
            item["ActUnitId"] = "km3"
        if name == "DEMPUBGWTFJI":
            item["IAR"] = [NEW_COMM_ID]
        elif name == "DEMPUBSURFJI":
            item["IAR"] = [comm_ids["WTRSURFJI"]]

    gen_data["osy-desc"] = (
        "Fiji v2 annual electricity backcast with Phase 1B public-water "
        "closure. Public delivery is observed for 2020-2024; public "
        "groundwater remains quarantined pending Fiji-specific evidence."
    )
    gen_data["osy-date"] = date.today().isoformat()
    return gen_data


def rows_for_parameter(data: dict[str, Any], parameter: str) -> list[dict[str, Any]]:
    try:
        return data[parameter]["SC_0"]
    except KeyError as exc:
        raise ValueError(f"Missing SC_0 rows for {parameter}") from exc


def set_year_values(
    data: dict[str, Any],
    parameter: str,
    predicate: Any,
    values: dict[int, float],
) -> int:
    matches = 0
    for row in rows_for_parameter(data, parameter):
        if predicate(row):
            matches += 1
            for year, value in values.items():
                row[str(year)] = value
    if matches != 1:
        raise ValueError(f"Expected one {parameter} row, found {matches}")
    return matches


def apply_parameter_values(case_path: Path) -> dict[str, Any]:
    gen_data = read_json(case_path / "genData.json")
    tech_ids = entity_map(gen_data["osy-tech"], "Tech", "TechId")
    comm_ids = entity_map(gen_data["osy-comm"], "Comm", "CommId")
    years = [int(year) for year in gen_data["osy-years"]]

    rytcm_path = case_path / "RYTCM.json"
    rytcm = read_json(rytcm_path)
    all_years_one = {year: 1.0 for year in years}
    surface_ratios = {
        year: values["surface_extracted"] / values["delivered"]
        for year, values in PUBLIC_WATER_ML.items()
    }
    relation_values = [
        ("IAR", NEW_TECH_ID, comm_ids["WTRGRCFJI"], all_years_one),
        ("OAR", NEW_TECH_ID, NEW_COMM_ID, all_years_one),
        ("IAR", tech_ids["DEMPUBGWTFJI"], NEW_COMM_ID, all_years_one),
        ("OAR", tech_ids["DEMPUBGWTFJI"], comm_ids["PUBWATFJI"], all_years_one),
        ("IAR", tech_ids["DEMPUBSURFJI"], comm_ids["WTRSURFJI"], surface_ratios),
        ("OAR", tech_ids["DEMPUBSURFJI"], comm_ids["PUBWATFJI"], all_years_one),
    ]
    for parameter, tech_id, comm_id, values in relation_values:
        set_year_values(
            rytcm,
            parameter,
            lambda row, tech_id=tech_id, comm_id=comm_id: (
                row.get("TechId") == tech_id
                and row.get("CommId") == comm_id
                and int(row.get("MoId", -1)) == 1
            ),
            values,
        )
    write_json(rytcm_path, rytcm)

    demand_km3 = {
        year: values["delivered"] / 1_000_000.0
        for year, values in PUBLIC_WATER_ML.items()
    }
    ryc_path = case_path / "RYC.json"
    ryc = read_json(ryc_path)
    set_year_values(
        ryc,
        "SAD",
        lambda row: row.get("CommId") == comm_ids["PUBWATFJI"],
        demand_km3,
    )
    write_json(ryc_path, ryc)

    year_split = read_json(case_path / "RYTs.json")
    split_by_timeslice: dict[str, dict[int, float]] = {}
    for row in rows_for_parameter(year_split, "YS"):
        split_by_timeslice[row["TsId"]] = {
            year: float(row[str(year)]) for year in HISTORICAL_YEARS
        }

    rycts_path = case_path / "RYCTs.json"
    rycts = read_json(rycts_path)
    profile_rows = 0
    for row in rows_for_parameter(rycts, "SDP"):
        if row.get("CommId") == comm_ids["PUBWATFJI"]:
            profile_rows += 1
            for year, value in split_by_timeslice[row["TsId"]].items():
                row[str(year)] = value
    if profile_rows != len(gen_data["osy-ts"]):
        raise ValueError(
            f"Expected {len(gen_data['osy-ts'])} public demand-profile rows, "
            f"found {profile_rows}"
        )
    write_json(rycts_path, rycts)

    ryt_path = case_path / "RYT.json"
    ryt = read_json(ryt_path)
    quarantine = {year: 0.0 for year in years}
    set_year_values(
        ryt,
        "TAU",
        lambda row: row.get("TechId") == tech_ids["DEMPUBGWTFJI"],
        quarantine,
    )
    set_year_values(
        ryt,
        "TAMaxCI",
        lambda row: row.get("TechId") == tech_ids["DEMPUBGWTFJI"],
        quarantine,
    )
    write_json(ryt_path, ryt)

    return {
        "public_demand_km3": demand_km3,
        "surface_input_per_delivered": surface_ratios,
        "groundwater_quarantine_years": [min(years), max(years)],
        "demand_profile": "YearSplit (flat annual delivery rate)",
        "reserve_proxy_update_required": True,
        "pumping_electricity": (
            "Not parameterized: no Fiji-specific intensity was found and "
            "gross grid supply already includes water-sector electricity."
        ),
    }


def copy_case_sources(source: Path, stage: Path) -> None:
    for source_file in sorted(source.glob("*.json")):
        shutil.copy2(source_file, stage / source_file.name)
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


def run_update_case(muiogo_root: Path, stage: Path, gen_data: dict[str, Any]) -> None:
    sys.path.insert(0, str(muiogo_root / "API"))
    from Classes.Base import Config
    from Classes.Case.UpdateCaseClass import UpdateCase

    Config.DATA_STORAGE = stage.parent
    UpdateCase(stage.name, gen_data).updateCase()


def install_case(
    *,
    source_case: Path,
    target_case: Path,
    muiogo_root: Path,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, Any]:
    storage = source_case.parent
    before = source_fingerprints(source_case)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{target_case.name}.phase1b-", dir=storage)
    )
    try:
        copy_case_sources(source_case, stage)
        gen_data = update_gen_data(read_json(stage / "genData.json"))
        gen_data["osy-casename"] = target_case.name
        write_json(stage / "genData.json", gen_data)
        run_update_case(muiogo_root, stage, gen_data)
        parameters = apply_parameter_values(stage)
        after = source_fingerprints(stage)
        changed_files = sorted(
            name for name, digest in after.items() if before.get(name) != digest
        )

        if dry_run:
            return {
                "dry_run": True,
                "source_case": source_case.name,
                "target_case": target_case.name,
                "changed_files": changed_files,
                "parameters": parameters,
            }

        if target_case == source_case:
            for staged_file in sorted(stage.glob("*.json")):
                destination = target_case / staged_file.name
                temporary = destination.with_suffix(destination.suffix + ".phase1b")
                shutil.copy2(staged_file, temporary)
                os.replace(temporary, destination)
        else:
            if target_case.exists():
                if not overwrite:
                    raise FileExistsError(
                        f"Target exists: {target_case}; pass --overwrite"
                    )
                backup = target_case.with_name(target_case.name + ".phase1b-backup")
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
            "source_fingerprints_before": before,
            "target_fingerprints_after": source_fingerprints(target_case),
        }
    finally:
        if stage.exists() and stage != target_case:
            shutil.rmtree(stage)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", newline="", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def append_set_value(path: Path, value: str) -> bool:
    fields, rows = read_csv(path)
    if any(row["VALUE"] == value for row in rows):
        return False
    rows.append({"VALUE": value})
    write_csv(path, fields, rows)
    return True


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


def sync_csv_inputs(inputs: Path, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {
            "dry_run": True,
            "inputs": str(inputs),
            "planned": [
                NEW_TECH_NAME,
                NEW_COMM_NAME,
                "public-water activity ratios",
                "public-water annual demand/profile",
                "public-groundwater quarantine",
            ],
        }

    append_set_value(inputs / "TECHNOLOGY.csv", NEW_TECH_NAME)
    append_set_value(inputs / "FUEL.csv", NEW_COMM_NAME)
    years = list(range(2020, 2051))

    surface_iar = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": "DEMPUBSURFJI",
            "FUEL": "WTRSURFJI",
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": (
                PUBLIC_WATER_ML[year]["surface_extracted"]
                / PUBLIC_WATER_ML[year]["delivered"]
                if year in HISTORICAL_YEARS
                else 1.0
            ),
        }
        for year in years
    ]
    groundwater_iar = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": "DEMPUBGWTFJI",
            "FUEL": NEW_COMM_NAME,
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": 1.0,
        }
        for year in years
    ]
    abstraction_iar = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": NEW_TECH_NAME,
            "FUEL": "WTRGRCFJI",
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": 1.0,
        }
        for year in years
    ]
    iar_removed, iar_added = replace_parameter_rows(
        inputs / "InputActivityRatio.csv",
        remove=lambda row: row["TECHNOLOGY"] in {
            "DEMPUBGWTFJI",
            "DEMPUBSURFJI",
            NEW_TECH_NAME,
        },
        additions=surface_iar + groundwater_iar + abstraction_iar,
    )

    abstraction_oar = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": NEW_TECH_NAME,
            "FUEL": NEW_COMM_NAME,
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": 1.0,
        }
        for year in years
    ]
    oar_removed, oar_added = replace_parameter_rows(
        inputs / "OutputActivityRatio.csv",
        remove=lambda row: row["TECHNOLOGY"] == NEW_TECH_NAME,
        additions=abstraction_oar,
    )

    demand_rows = [
        {
            "REGION": "GLOBAL",
            "FUEL": "PUBWATFJI",
            "YEAR": year,
            "VALUE": PUBLIC_WATER_ML[year]["delivered"] / 1_000_000.0,
        }
        for year in HISTORICAL_YEARS
    ]
    demand_removed, demand_added = replace_parameter_rows(
        inputs / "SpecifiedAnnualDemand.csv",
        remove=lambda row: row["FUEL"] == "PUBWATFJI",
        additions=demand_rows,
    )

    ys_fields, ys_rows = read_csv(inputs / "YearSplit.csv")
    del ys_fields
    year_split = {
        (row["TIMESLICE"], int(row["YEAR"])): float(row["VALUE"])
        for row in ys_rows
    }
    timeslices = sorted({row["TIMESLICE"] for row in ys_rows})
    profile_rows = [
        {
            "REGION": "GLOBAL",
            "FUEL": "PUBWATFJI",
            "TIMESLICE": timeslice,
            "YEAR": year,
            "VALUE": year_split[(timeslice, year)],
        }
        for timeslice in timeslices
        for year in HISTORICAL_YEARS
    ]
    profile_removed, profile_added = replace_parameter_rows(
        inputs / "SpecifiedDemandProfile.csv",
        remove=lambda row: row["FUEL"] == "PUBWATFJI",
        additions=profile_rows,
    )

    quarantine_rows = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": "DEMPUBGWTFJI",
            "YEAR": year,
            "VALUE": 0.0,
        }
        for year in years
    ]
    tau_removed, tau_added = replace_parameter_rows(
        inputs / "TotalTechnologyAnnualActivityUpperLimit.csv",
        remove=lambda row: row["TECHNOLOGY"] == "DEMPUBGWTFJI",
        additions=quarantine_rows,
    )
    max_ci_removed, max_ci_added = replace_parameter_rows(
        inputs / "TotalAnnualMaxCapacityInvestment.csv",
        remove=lambda row: row["TECHNOLOGY"] == "DEMPUBGWTFJI",
        additions=quarantine_rows,
    )

    return {
        "dry_run": False,
        "inputs": str(inputs),
        "technology_added": NEW_TECH_NAME,
        "commodity_added": NEW_COMM_NAME,
        "rows": {
            "InputActivityRatio": {"removed": iar_removed, "added": iar_added},
            "OutputActivityRatio": {"removed": oar_removed, "added": oar_added},
            "SpecifiedAnnualDemand": {
                "removed": demand_removed,
                "added": demand_added,
            },
            "SpecifiedDemandProfile": {
                "removed": profile_removed,
                "added": profile_added,
            },
            "TotalTechnologyAnnualActivityUpperLimit": {
                "removed": tau_removed,
                "added": tau_added,
            },
            "TotalAnnualMaxCapacityInvestment": {
                "removed": max_ci_removed,
                "added": max_ci_added,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--muiogo-root",
        type=Path,
        default=DEFAULT_MUIOGO,
        help="MUIOGO repository containing API/ and WebAPP/",
    )
    parser.add_argument("--source-case", default="Fiji_v2")
    parser.add_argument("--target-case", default="Fiji_v2_Phase1B_Test")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument(
        "--sync-csv-inputs",
        action="store_true",
        help="Also update the portable otoole CSV source inputs.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    muiogo_root = args.muiogo_root.resolve()
    if not (muiogo_root / "API").is_dir():
        raise SystemExit(f"Not a MUIOGO repository: {muiogo_root}")
    storage = muiogo_root / "WebAPP" / "DataStorage"
    source_case = storage / args.source_case
    target_case = storage / args.target_case
    if not source_case.is_dir():
        raise SystemExit(f"Missing source case: {source_case}")

    report = {
        "phase": "1B public water",
        "date": date.today().isoformat(),
        "case": install_case(
            source_case=source_case,
            target_case=target_case,
            muiogo_root=muiogo_root,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        ),
    }
    if args.sync_csv_inputs:
        report["csv_inputs"] = sync_csv_inputs(args.inputs.resolve(), args.dry_run)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
