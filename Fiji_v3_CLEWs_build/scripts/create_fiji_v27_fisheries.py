#!/usr/bin/env python3
"""Create a disposable Fiji_v2.7 candidate with a non-forcing Fisheries sector."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
import sys
import types
from datetime import date
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
STORAGE = REPO / "WebAPP" / "DataStorage"
SOURCE_NAME = "Fiji_v2.6"
DEFAULT_TARGET = ".Fiji_v2.7-fisheries-candidate"
SCENARIO = "SC_0"
YEARS = [str(year) for year in range(2020, 2051)]
FISHERIES_GROUP = "TG_fisheries"
CO2 = "EMI_0"
DSL = "COM_eev5t"
GRID = "COM_3drm3"
PUBLIC_WATER = "COM_mmv3k"
AGR_SERVICE = "COM_x6kh9"
IND_HEAT_SERVICE = "COM_sb105"
IND_ELECTRICITY = "COM_9ek33"
AGR_DIESEL_TECH = "TEC_s2z92"
IND_DIESEL_TECH = "TEC_tfgsb"
CAP_SERVICE = "COM_fsh_cap"
AQ_SERVICE = "COM_fsh_aq"
POST_SERVICE = "COM_fsh_post"

TECHNOLOGIES = {
    "TEC_fsh_cap_dsl": {
        "name": "FSHCAPDSL",
        "description": "Fisheries capture fleet propulsion using diesel",
        "inputs": [DSL],
        "output": CAP_SERVICE,
        "emissions": [CO2],
        "iar": {DSL: 1.0 / 0.30},
        "ear": 0.247,
        "availability": 0.90,
        "life": 15,
        "capital_cost": 31.688087814,
        "fixed_cost": 1.5844043907,
        "records": "PAR_FSH_CAP_DSL_IAR; PAR_FSH_CAP_DSL_RC; PAR_FSH_CO2",
    },
    "TEC_fsh_cap_ele": {
        "name": "FSHCAPELE",
        "description": "Fisheries capture fleet propulsion using grid electricity",
        "inputs": [GRID],
        "output": CAP_SERVICE,
        "emissions": [],
        "iar": {GRID: 1.0 / 0.75},
        "ear": None,
        "availability": 0.90,
        "life": 15,
        "capital_cost": 95.064263442,
        "fixed_cost": 2.85192790326,
        "records": "PAR_FSH_CAP_ELE_IAR; PAR_FSH_OPEN_BOUNDS",
    },
    "TEC_fsh_aq_dsl": {
        "name": "FSHAQDSL",
        "description": "Fisheries aquaculture pumps and equipment using diesel",
        "inputs": [DSL],
        "output": AQ_SERVICE,
        "emissions": [CO2],
        "iar": {DSL: 1.0 / 0.30},
        "ear": 0.247,
        "availability": 0.90,
        "life": 12,
        "capital_cost": 38.025705377,
        "fixed_cost": 1.90128526885,
        "records": "PAR_FSH_AQ_DSL_IAR; PAR_FSH_CO2",
    },
    "TEC_fsh_aq_ele": {
        "name": "FSHAQELE",
        "description": "Fisheries aquaculture pumps and equipment using grid electricity",
        "inputs": [GRID],
        "output": AQ_SERVICE,
        "emissions": [],
        "iar": {GRID: 1.0 / 0.75},
        "ear": None,
        "availability": 0.90,
        "life": 12,
        "capital_cost": 47.532131721,
        "fixed_cost": 1.42596395163,
        "records": "PAR_FSH_AQ_ELE_IAR; PAR_FSH_AQ_ELE_RC",
    },
    "TEC_fsh_post_dsl": {
        "name": "FSHPOSTDSL",
        "description": "Fisheries cold-chain and processing equipment using diesel",
        "inputs": [DSL, PUBLIC_WATER],
        "output": POST_SERVICE,
        "emissions": [CO2],
        "iar": {DSL: 1.0 / 0.80, PUBLIC_WATER: 0.0031318921365820793},
        "ear": 0.092625,
        "availability": 0.95,
        "life": 15,
        "capital_cost": 38.025705377,
        "fixed_cost": 1.90128526885,
        "records": "PAR_FSH_POST_DSL_IAR; PAR_FSH_POST_WATER_DSL; PAR_FSH_POST_DSL_RC; PAR_FSH_CO2",
    },
    "TEC_fsh_post_ele": {
        "name": "FSHPOSTELE",
        "description": "Fisheries cold-chain and processing equipment using grid electricity",
        "inputs": [GRID, PUBLIC_WATER],
        "output": POST_SERVICE,
        "emissions": [],
        "iar": {GRID: 1.0 / 0.75, PUBLIC_WATER: 0.0031318921365820793},
        "ear": None,
        "availability": 0.95,
        "life": 15,
        "capital_cost": 28.519279033,
        "fixed_cost": 0.85557837099,
        "records": "PAR_FSH_POST_ELE_IAR; PAR_FSH_POST_WATER_ELE; PAR_FSH_POST_ELE_RC",
    },
    "TEC_fsh_post_sol": {
        "name": "FSHPOSTSOL",
        "description": "Integrated solar-powered fisheries freezer and cold-chain equipment",
        "inputs": [PUBLIC_WATER],
        "output": POST_SERVICE,
        "emissions": [],
        "iar": {PUBLIC_WATER: 0.0031318921365820793},
        "ear": None,
        "availability": 0.95,
        "life": 10,
        "capital_cost": 126.752351256,
        "fixed_cost": 2.53504702512,
        "records": "PAR_FSH_POST_WATER_SOL; PAR_FSH_POST_SOL_RC",
    },
}


dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)
sys.path.insert(0, str(REPO / "API"))

from Classes.Base import Config  # noqa: E402
from Classes.Case.UpdateCaseClass import UpdateCase  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".codex-tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_for(data: dict[str, Any], parameter: str, **identity: Any) -> dict[str, Any]:
    rows = data[parameter][SCENARIO]
    matches = [
        row for row in rows if all(row.get(field) == value for field, value in identity.items())
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {parameter} row for {identity}, found {len(matches)}"
        )
    return matches[0]


def set_years(row: dict[str, Any], values: float | dict[str, float]) -> None:
    for year in YEARS:
        row[year] = values[year] if isinstance(values, dict) else values


def service_commodities() -> list[dict[str, str]]:
    return [
        {
            "CommId": CAP_SERVICE,
            "Comm": "FSHCAPSERV",
            "Desc": "Fisheries capture-fleet motive useful service; PAR_FSH_CAP_DEMAND.",
            "UnitId": "PJ",
        },
        {
            "CommId": AQ_SERVICE,
            "Comm": "FSHAQSERV",
            "Desc": "Fisheries aquaculture operations useful service; PAR_FSH_AQ_DEMAND.",
            "UnitId": "PJ",
        },
        {
            "CommId": POST_SERVICE,
            "Comm": "FSHPOSTSERV",
            "Desc": "Fisheries cold-chain and processing useful service; PAR_FSH_POST_DEMAND.",
            "UnitId": "PJ",
        },
    ]


def technology_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for tech_id, spec in TECHNOLOGIES.items():
        records.append(
            {
                "TechId": tech_id,
                "Tech": spec["name"],
                "Desc": (
                    f"{spec['description']}. Physical conversion; open activity and "
                    f"investment; residual stock may idle. Records: {spec['records']}."
                ),
                "CapUnitId": "PJ/year",
                "ActUnitId": "PJ",
                "IAR": spec["inputs"],
                "OAR": [spec["output"]],
                "EAR": spec["emissions"],
                "INCR": [],
                "ITCR": [],
                "TG": [FISHERIES_GROUP],
            }
        )
    return records


def build_gen(source: dict[str, Any]) -> dict[str, Any]:
    gen = copy.deepcopy(source)
    existing_tech_ids = {row["TechId"] for row in gen["osy-tech"]}
    existing_comm_ids = {row["CommId"] for row in gen["osy-comm"]}
    collisions = (set(TECHNOLOGIES) & existing_tech_ids) | (
        {CAP_SERVICE, AQ_SERVICE, POST_SERVICE} & existing_comm_ids
    )
    if collisions:
        raise AssertionError(f"Fisheries identifiers already exist: {sorted(collisions)}")
    gen["osy-casename"] = "Fiji_v2.7"
    gen["osy-date"] = str(date.today())
    gen["osy-desc"] = (
        "Fiji v2.7 with a source-traceable, non-forcing Fisheries sector covering "
        "capture propulsion, aquaculture operations, and combined cold-chain/processing; "
        "derived from the solved Fiji_v2.6 environmental-accounting case."
    )
    gen["osy-techGroups"].append(
        {
            "TechGroup": "Fisheries",
            "TechGroupId": FISHERIES_GROUP,
            "Desc": "Capture fleet, aquaculture, cold-chain and fish-processing technologies.",
        }
    )
    gen["osy-comm"].extend(service_commodities())
    gen["osy-tech"].extend(technology_records())
    return gen


def residual_series() -> dict[str, dict[str, float]]:
    path = REPO / "docs" / "Fiji_v2.7_Fisheries" / "calculations" / "residual-capacity-series.csv"
    import csv

    result = {tech_id: {year: 0.0 for year in YEARS} for tech_id in TECHNOLOGIES}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            result[row["technology"]][row["year"]] = float(row["residual_capacity"])
    return result


def overlay_demands(case: Path) -> dict[str, Any]:
    data = read_json(case / "RYC.json")
    capture = {year: 0.033508266 for year in YEARS}
    aquaculture = {
        year: 0.000005841963 * (1.05 ** (int(year) - 2020)) for year in YEARS
    }
    aquaculture_input = {
        year: 0.000007789284 * (1.05 ** (int(year) - 2020)) for year in YEARS
    }
    post = {year: 0.019242795528 for year in YEARS}
    for commodity, values in (
        (CAP_SERVICE, capture),
        (AQ_SERVICE, aquaculture),
        (POST_SERVICE, post),
    ):
        set_years(row_for(data, "SAD", CommId=commodity), values)
        set_years(row_for(data, "AAD", CommId=commodity), 0.0)

    boundary = {
        "agriculture_service_removed": {},
        "industry_heat_removed": {},
        "industry_electricity_removed": {},
        "grid_aquaculture_removed": {},
        "public_water_removed": {},
    }
    corrections = (
        (AGR_SERVICE, 0.027923555, "agriculture_service_removed"),
        (IND_HEAT_SERVICE, 0.004051114848, "industry_heat_removed"),
        (IND_ELECTRICITY, 0.02025557424, "industry_electricity_removed"),
    )
    for commodity, decrement, key in corrections:
        row = row_for(data, "SAD", CommId=commodity)
        for year in YEARS:
            before = float(row[year])
            after = before - decrement
            if after < -1e-12:
                raise AssertionError(f"negative boundary after correction: {commodity}/{year}")
            row[year] = max(0.0, after)
            boundary[key][year] = {"before": before, "removed": decrement, "after": row[year]}

    grid = row_for(data, "SAD", CommId=GRID)
    for year in YEARS:
        before = float(grid[year])
        removed = aquaculture_input[year]
        after = before - removed
        if after < -1e-12:
            raise AssertionError(f"negative grid boundary after aquaculture correction: {year}")
        grid[year] = max(0.0, after)
        boundary["grid_aquaculture_removed"][year] = {
            "before": before,
            "removed": removed,
            "after": grid[year],
        }

    water = row_for(data, "SAD", CommId=PUBLIC_WATER)
    for year in YEARS:
        before = float(water[year])
        removed = 0.00006026636 if int(year) <= 2024 else 0.0
        after = before - removed
        if after < -1e-12:
            raise AssertionError(f"negative public-water boundary after correction: {year}")
        water[year] = max(0.0, after)
        boundary["public_water_removed"][year] = {
            "before": before,
            "removed": removed,
            "after": water[year],
        }
    write_json(case / "RYC.json", data)
    return boundary


def overlay_annual_technology(case: Path, rc: dict[str, dict[str, float]]) -> dict[str, Any]:
    data = read_json(case / "RYT.json")
    parameters = {
        "AF": lambda spec: spec["availability"],
        "CC": lambda spec: spec["capital_cost"],
        "FC": lambda spec: spec["fixed_cost"],
        "RC": None,
        "TAL": lambda spec: 0.0,
        "TAU": lambda spec: 999999.0,
        "TAMinC": lambda spec: 0.0,
        "TAMaxC": lambda spec: 999999.0,
        "TAMinCI": lambda spec: 0.0,
        "TAMaxCI": lambda spec: 999999.0,
    }
    for parameter, getter in parameters.items():
        for tech_id, spec in TECHNOLOGIES.items():
            values: float | dict[str, float]
            values = rc[tech_id] if parameter == "RC" else float(getter(spec))
            set_years(row_for(data, parameter, TechId=tech_id), values)

    pin_changes: dict[str, Any] = {}
    for tech_id, decrement in (
        (AGR_DIESEL_TECH, 0.11169422),
        (IND_DIESEL_TECH, 0.00506389356),
    ):
        pin_changes[tech_id] = {}
        lower = row_for(data, "TAL", TechId=tech_id)
        upper = row_for(data, "TAU", TechId=tech_id)
        for year in ("2020", "2021", "2022", "2023"):
            if not math.isclose(float(lower[year]), float(upper[year]), abs_tol=1e-12):
                raise AssertionError(f"expected exact inherited observed boundary {tech_id}/{year}")
            before = float(lower[year])
            after = before - decrement
            if after < -1e-12:
                raise AssertionError(f"negative aggregate activity after correction {tech_id}/{year}")
            lower[year] = max(0.0, after)
            upper[year] = max(0.0, after)
            pin_changes[tech_id][year] = {
                "before": before,
                "removed": decrement,
                "after": lower[year],
            }
    write_json(case / "RYT.json", data)
    return pin_changes


def overlay_region_technology(case: Path) -> None:
    data = read_json(case / "RT.json")
    for parameter, values in (
        ("CAU", {tech_id: 1.0 for tech_id in TECHNOLOGIES}),
        ("OL", {tech_id: spec["life"] for tech_id, spec in TECHNOLOGIES.items()}),
    ):
        rows = data[parameter][SCENARIO]
        if len(rows) != 1:
            raise AssertionError(f"expected one region row in RT/{parameter}")
        rows[0].update(values)
    write_json(case / "RT.json", data)


def overlay_ratios(case: Path) -> None:
    data = read_json(case / "RYTCM.json")
    for parameter in ("IAR", "OAR"):
        for row in data[parameter][SCENARIO]:
            tech_id = row.get("TechId")
            if tech_id not in TECHNOLOGIES:
                continue
            spec = TECHNOLOGIES[tech_id]
            value = 0.0
            if row["MoId"] == 1:
                if parameter == "IAR":
                    value = float(spec["iar"].get(row["CommId"], 0.0))
                elif row["CommId"] == spec["output"]:
                    value = 1.0
            set_years(row, value)
    write_json(case / "RYTCM.json", data)


def overlay_emissions(case: Path) -> None:
    data = read_json(case / "RYTEM.json")
    for row in data["EAR"][SCENARIO]:
        tech_id = row.get("TechId")
        if tech_id not in TECHNOLOGIES:
            continue
        spec = TECHNOLOGIES[tech_id]
        value = float(spec["ear"]) if row["MoId"] == 1 and spec["ear"] is not None else 0.0
        set_years(row, value)
    write_json(case / "RYTEM.json", data)


def overlay_modes(case: Path) -> None:
    data = read_json(case / "RYTM.json")
    defaults = {"TADML": 0.0, "TAIML": 0.0, "TAMLL": 0.0, "TAMUL": 99999.0, "VC": 0.0}
    for parameter, value in defaults.items():
        for row in data[parameter][SCENARIO]:
            if row.get("TechId") in TECHNOLOGIES:
                set_years(row, value)
    write_json(case / "RYTM.json", data)


def overlay_timeslices(case: Path) -> None:
    capacity = read_json(case / "RYTTs.json")
    for row in capacity["CF"][SCENARIO]:
        if row.get("TechId") in TECHNOLOGIES:
            set_years(row, 1.0)
    write_json(case / "RYTTs.json", capacity)

    demand_profile = read_json(case / "RYCTs.json")
    for row in demand_profile["SDP"][SCENARIO]:
        if row.get("CommId") in {CAP_SERVICE, AQ_SERVICE, POST_SERVICE}:
            set_years(row, 0.25)
    write_json(case / "RYCTs.json", demand_profile)


def source_hashes(source: Path) -> dict[str, str]:
    return {path.name: digest(path) for path in sorted(source.glob("*.json"))}


def create(target_name: str, overwrite: bool) -> dict[str, Any]:
    source = STORAGE / SOURCE_NAME
    target = STORAGE / target_name
    if not source.is_dir() or source.is_symlink():
        raise FileNotFoundError(f"invalid source case: {source}")
    if target.exists():
        if not overwrite:
            raise FileExistsError(f"target already exists: {target}")
        if target.is_symlink() or target.resolve() == source.resolve():
            raise ValueError("unsafe target")
        shutil.rmtree(target)
    before = source_hashes(source)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("res"))
    gen = build_gen(read_json(target / "genData.json"))
    write_json(target / "genData.json", gen)
    Config.DATA_STORAGE = STORAGE
    UpdateCase(target.name, gen).updateCase()
    write_json(target / "genData.json", gen)

    rc = residual_series()
    boundary = overlay_demands(target)
    pin_changes = overlay_annual_technology(target, rc)
    overlay_region_technology(target)
    overlay_ratios(target)
    overlay_emissions(target)
    overlay_modes(target)
    overlay_timeslices(target)

    if source_hashes(source) != before:
        raise AssertionError("Fiji_v2.6 source changed during candidate generation")
    manifest = {
        "status": "created",
        "source_case": SOURCE_NAME,
        "target_folder": target.name,
        "case_identity": "Fiji_v2.7",
        "model_format_version": gen["osy-version"],
        "source_hashes": before,
        "new_technology_ids": sorted(TECHNOLOGIES),
        "new_commodity_ids": [CAP_SERVICE, AQ_SERVICE, POST_SERVICE],
        "new_group_id": FISHERIES_GROUP,
        "boundary_corrections": boundary,
        "observed_activity_boundary_corrections": pin_changes,
        "residual_capacity_series": rc,
        "generation_path": "UpdateCase(target, genData).updateCase() then source overlays",
        "equation_map": {
            "demand": "EBb4_EnergyBalanceEachYear4_ICR in model.v.5.4.txt",
            "timeslice_capacity": "CAa4_Constraint_Capacity in model.v.5.4.txt",
            "annual_capacity": "CAb1_PlannedMaintenance in model.v.5.4.txt",
            "activity_limits": "AAC2/AAC3; open for all Fisheries technologies",
            "investment_limits": "TAC2/TAC3 and TCC1/TCC2; open for all Fisheries technologies",
            "mode_limits": "LU1/LU2; zero lower and host-open upper",
        },
    }
    write_json(target / "fisheries_v27_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-name", default=DEFAULT_TARGET)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        result = create(args.target_name, args.overwrite)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
