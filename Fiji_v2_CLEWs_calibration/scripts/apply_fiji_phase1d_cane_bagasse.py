#!/usr/bin/env python3
"""Apply Fiji Phase 1D cane-bagasse-electricity closure reproducibly.

Two checkpoints are supported:

``accounting``
    Add the mill and split the inherited 34 MW aggregate biomass fleet into
    25 MW bagasse and 9 MW wood-residue technologies while retaining the
    inherited aggregate availability. The bagasse resource is deliberately
    non-binding through an explicitly artificial high output ratio. This is
    the structural parity control, not a physical coefficient.

``physical``
    Use FSC cane throughput, an IRENA 42 bar cogeneration export coefficient,
    and a separately calibrated wood-residue availability. Bagasse generation
    is limited by cane processed at the mill, while wood-residue generation is
    capped at the separately observed residual resource level. Neither branch
    can expand generation merely because the inherited aggregate biomass
    technology allowed unconstrained new investment.

Structural edits pass through MUIOGO ``UpdateCase``. Permanent changes are
made only in source JSON and portable CSV inputs; generated solver files and
results are never edited or copied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
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
DEFAULT_EVIDENCE = (
    PACKAGE
    / "data_sources"
    / "evidence"
    / "energy"
    / "fiji_phase1d_cane_bagasse_power_balance_2020_2024.csv"
)
PROXY_CONFIG = PACKAGE / "muio" / "reserve_margin_proxy_config.json"

BASE_SCENARIO = "SC_0"
HISTORICAL_YEARS = tuple(range(2020, 2025))
CALIBRATION_YEARS = tuple(range(2020, 2023))

OLD_POWER = "PWRBIOFJIXX01"
MILL = "SGCMILLFJI"
BAGASSE_POWER = "PWRBAGFJIXX01"
WOOD_POWER = "PWRWODFJIXX01"
RAW_CANE = "CRPSGC"
PROCESSED_CANE = "SGCPROCFJI"
EXPORTABLE_BAGASSE = "BAGEXPFJI"
WOOD_FUEL = "BIOFJIXX"
GRID_OUTPUT = "ELCFJIXX01"

NEW_TECH_IDS = {
    MILL: "TEC_phase1d_sgcmill",
    BAGASSE_POWER: "TEC_phase1d_pwrbag",
    WOOD_POWER: "TEC_phase1d_pwrwood",
}
NEW_COMM_IDS = {
    PROCESSED_CANE: "COM_phase1d_sgcproc",
    EXPORTABLE_BAGASSE: "COM_phase1d_bagexp",
}

# FSC operating tables, crushing seasons 2020-2024. Quantities are tonnes.
FSC_OPERATIONS = {
    2020: {
        "cane_t": 1_729_171,
        "sugar_t": 151_589,
        "molasses_t": 82_767,
        "report": "FSC 2021 Annual Report",
        "locator": "PDF p. 15, 2020 Season Key Operating Data",
    },
    2021: {
        "cane_t": 1_417_185,
        "sugar_t": 133_209,
        "molasses_t": 71_710,
        "report": "FSC 2022 Annual Report",
        "locator": "PDF pp. 14-15, 2021 Key Operating Data",
    },
    2022: {
        "cane_t": 1_639_004,
        "sugar_t": 155_812,
        "molasses_t": 74_178,
        "report": "FSC 2023 Annual Report",
        "locator": "PDF pp. 16-17, 2022 Season Key Operating Data",
    },
    2023: {
        "cane_t": 1_565_586,
        "sugar_t": 139_628,
        "molasses_t": 71_939,
        "report": "FSC 2024 Annual Report",
        "locator": "PDF pp. 20-21, 2023 operating data",
    },
    2024: {
        "cane_t": 1_331_922,
        "sugar_t": 126_522,
        "molasses_t": 64_191,
        "report": "FSC 2025 Annual Report",
        "locator": "PDF p. 21, Targets vs Achievements for 2024 Season",
    },
}

IPP_MWH = {
    2020: 67_094.0,
    2021: 61_053.0,
    2022: 73_471.0,
    2023: 76_115.0,
    2024: 63_799.0,
}

# Government of Fiji REI plan: FSC Lautoka 5 MW + FSC Labasa 20 MW and
# Tropik Wood 9 MW. The old aggregate fleet is 34 MW.
BAGASSE_CAPACITY_GW = 0.025
WOOD_CAPACITY_GW = 0.009
AGGREGATE_CAPACITY_GW = BAGASSE_CAPACITY_GW + WOOD_CAPACITY_GW

# IRENA (2019), Table 3.1: 42 bar, 400 C, 500 kg process steam/t cane,
# no straw: 25.4 kWh of export electricity per tonne cane. The inherited
# Fiji biomass generator uses 3.82 PJ fuel per PJ electricity.
EXPORT_KWH_PER_T_CANE = 25.4
POWER_HEAT_RATE = 3.82
PJ_PER_MWH = 0.0000036
EXPORT_ELECTRICITY_PJ_PER_MT_CANE = (
    EXPORT_KWH_PER_T_CANE * 1_000_000 / 1_000_000 * 0.0036
)
EXPORTABLE_BAGASSE_PJ_PER_MT_CANE = (
    EXPORT_ELECTRICITY_PJ_PER_MT_CANE * POWER_HEAT_RATE
)
GROSS_BAGASSE_T_PER_T_CANE = 0.280
ACCOUNTING_BAGASSE_PJ_PER_MT_CANE = 10.0


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


def entity_map(
    items: list[dict[str, Any]], name_field: str, id_field: str
) -> dict[str, str]:
    return {str(item[name_field]): str(item[id_field]) for item in items}


def require_entities(
    mapping: dict[str, str], names: set[str], kind: str
) -> None:
    missing = sorted(names - mapping.keys())
    if missing:
        raise ValueError(f"Missing required {kind}: {', '.join(missing)}")


def rows_for_parameter(
    data: dict[str, Any], parameter: str
) -> list[dict[str, Any]]:
    try:
        return data[parameter][BASE_SCENARIO]
    except KeyError as exc:
        raise ValueError(
            f"Missing {BASE_SCENARIO} rows for {parameter}"
        ) from exc


def parameter_row(
    data: dict[str, Any],
    parameter: str,
    **identifiers: Any,
) -> dict[str, Any]:
    matches = [
        row
        for row in rows_for_parameter(data, parameter)
        if all(row.get(key) == value for key, value in identifiers.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {identifiers}, "
            f"found {len(matches)}"
        )
    return matches[0]


def year_values(row: dict[str, Any], years: list[int]) -> dict[int, float]:
    return {year: float(row[str(year)]) for year in years}


def set_years(row: dict[str, Any], values: dict[int, float]) -> None:
    for year, value in values.items():
        row[str(year)] = float(value)


def cane_throughput(
    years: list[int], inherited_mt: dict[int, float]
) -> dict[int, float]:
    """Return million tonnes of cane processed in each model year."""
    result = {
        year: FSC_OPERATIONS[year]["cane_t"] / 1_000_000.0
        for year in HISTORICAL_YEARS
    }
    anchor = result[2024]
    inherited_anchor = inherited_mt[2024]
    for year in years:
        if year > 2024:
            result[year] = anchor * inherited_mt[year] / inherited_anchor
    return result


def bagasse_generation_mwh(cane_t: float) -> float:
    return cane_t * EXPORT_KWH_PER_T_CANE / 1000.0


def wood_availability() -> float:
    residual_mwh = [
        IPP_MWH[year]
        - bagasse_generation_mwh(FSC_OPERATIONS[year]["cane_t"])
        for year in CALIBRATION_YEARS
    ]
    mean_mwh = sum(residual_mwh) / len(residual_mwh)
    return mean_mwh / (WOOD_CAPACITY_GW * 1000.0 * 8.76 * 1000.0)


WOOD_AVAILABILITY = wood_availability()
WOOD_GENERATION_MWH = (
    sum(
        IPP_MWH[year]
        - bagasse_generation_mwh(FSC_OPERATIONS[year]["cane_t"])
        for year in CALIBRATION_YEARS
    )
    / len(CALIBRATION_YEARS)
)
WOOD_ACTIVITY_UPPER_PJ = WOOD_GENERATION_MWH * PJ_PER_MWH


def update_gen_data(
    gen_data: dict[str, Any], checkpoint: str
) -> dict[str, Any]:
    technologies = gen_data["osy-tech"]
    commodities = gen_data["osy-comm"]
    tech_ids = entity_map(technologies, "Tech", "TechId")
    comm_ids = entity_map(commodities, "Comm", "CommId")
    require_entities(
        tech_ids,
        {OLD_POWER, "RNWBIOFJIXX", "LNDAGRFJIC01"},
        "technologies",
    )
    require_entities(
        comm_ids,
        {RAW_CANE, WOOD_FUEL, GRID_OUTPUT},
        "commodities",
    )

    for name, expected_id in NEW_COMM_IDS.items():
        if name in comm_ids and comm_ids[name] != expected_id:
            raise ValueError(
                f"Collision: {name} uses {comm_ids[name]}, "
                f"expected {expected_id}"
            )
        if expected_id in comm_ids.values() and name not in comm_ids:
            raise ValueError(f"Collision: {expected_id} belongs elsewhere")
    for name, expected_id in NEW_TECH_IDS.items():
        if name in tech_ids and tech_ids[name] != expected_id:
            raise ValueError(
                f"Collision: {name} uses {tech_ids[name]}, "
                f"expected {expected_id}"
            )
        if expected_id in tech_ids.values() and name not in tech_ids:
            raise ValueError(f"Collision: {expected_id} belongs elsewhere")

    new_commodities = {
        PROCESSED_CANE: {
            "CommId": NEW_COMM_IDS[PROCESSED_CANE],
            "Comm": PROCESSED_CANE,
            "Desc": (
                "Sugarcane processed at FSC mills; final cane-throughput "
                "service replacing direct raw-cane demand."
            ),
            "UnitId": "Mt",
        },
        EXPORTABLE_BAGASSE: {
            "CommId": NEW_COMM_IDS[EXPORTABLE_BAGASSE],
            "Comm": EXPORTABLE_BAGASSE,
            "Desc": (
                "Exportable bagasse fuel energy after mill process-energy "
                "requirements; central engineering proxy."
            ),
            "UnitId": "PJ",
        },
    }
    for name, record in new_commodities.items():
        if name in comm_ids:
            next(item for item in commodities if item["Comm"] == name).update(
                record
            )
        else:
            commodities.append(record)
        comm_ids[name] = record["CommId"]

    raw_cane = next(
        item for item in commodities if item["Comm"] == RAW_CANE
    )
    raw_cane["Desc"] = (
        "Harvested sugarcane delivered to mills; numerical unit is million "
        "tonnes under the upstream FAOSTAT / 1,000,000 conversion."
    )
    raw_cane["UnitId"] = "Mt"

    land_group = next(
        item for item in technologies if item["Tech"] == "LNDAGRFJIC01"
    )["TG"][0]
    power_group = next(
        item for item in technologies if item["Tech"] == OLD_POWER
    )["TG"][0]
    new_technologies = {
        MILL: {
            "TechId": NEW_TECH_IDS[MILL],
            "Tech": MILL,
            "Desc": (
                "FSC mill accounting layer: raw cane to processed cane and "
                "exportable bagasse energy."
            ),
            "CapUnitId": "Mt/year",
            "ActUnitId": "Mt",
            "IAR": [comm_ids[RAW_CANE]],
            "OAR": [
                comm_ids[PROCESSED_CANE],
                comm_ids[EXPORTABLE_BAGASSE],
            ],
            "EAR": [],
            "INCR": [],
            "ITCR": [],
            "TG": [land_group],
        },
        BAGASSE_POWER: {
            "TechId": NEW_TECH_IDS[BAGASSE_POWER],
            "Tech": BAGASSE_POWER,
            "Desc": (
                "FSC Lautoka and Labasa bagasse cogeneration supplying the "
                "grid; 25 MW documented 2021 stock."
            ),
            "CapUnitId": "GW",
            "ActUnitId": "PJ",
            "IAR": [comm_ids[EXPORTABLE_BAGASSE]],
            "OAR": [comm_ids[GRID_OUTPUT]],
            "EAR": [],
            "INCR": [],
            "ITCR": [],
            "TG": [power_group],
        },
        WOOD_POWER: {
            "TechId": NEW_TECH_IDS[WOOD_POWER],
            "Tech": WOOD_POWER,
            "Desc": (
                "Tropik Wood residue-fired grid generator; 9 MW documented "
                "2021 stock."
            ),
            "CapUnitId": "GW",
            "ActUnitId": "PJ",
            "IAR": [comm_ids[WOOD_FUEL]],
            "OAR": [comm_ids[GRID_OUTPUT]],
            "EAR": [],
            "INCR": [],
            "ITCR": [],
            "TG": [power_group],
        },
    }
    for name, record in new_technologies.items():
        if name in tech_ids:
            next(item for item in technologies if item["Tech"] == name).update(
                record
            )
        else:
            technologies.append(record)

    old = next(item for item in technologies if item["Tech"] == OLD_POWER)
    old["Desc"] = (
        "Retired aggregate biomass shell; replaced in Phase 1D by separate "
        "bagasse and wood-residue technologies."
    )
    gen_data["osy-desc"] = (
        "Fiji v2 annual electricity model with Phase 1D FSC "
        f"cane-bagasse-electricity closure ({checkpoint} checkpoint)."
    )
    gen_data["osy-date"] = date.today().isoformat()
    return gen_data


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


def run_update_case(
    muiogo_root: Path, stage: Path, gen_data: dict[str, Any]
) -> None:
    sys.path.insert(0, str(muiogo_root / "API"))
    from Classes.Base import Config
    from Classes.Case.UpdateCaseClass import UpdateCase

    Config.DATA_STORAGE = stage.parent
    UpdateCase(stage.name, gen_data).updateCase()


def copy_single_tech_parameters(
    case_path: Path, old_id: str, new_ids: list[str]
) -> None:
    path = case_path / "RT.json"
    data = read_json(path)
    for parameter in data.values():
        values = parameter[BASE_SCENARIO][0]
        for new_id in new_ids:
            values[new_id] = values[old_id]
    write_json(path, data)


def copy_year_tech_parameters(
    case_path: Path,
    filename: str,
    old_id: str,
    new_ids: list[str],
) -> None:
    path = case_path / filename
    data = read_json(path)
    for parameter, scenarios in data.items():
        rows = scenarios[BASE_SCENARIO]
        old_rows = [row for row in rows if row.get("TechId") == old_id]
        for old_row in old_rows:
            identity = {
                key: value
                for key, value in old_row.items()
                if key != "TechId" and not str(key).isdigit()
            }
            for new_id in new_ids:
                targets = [
                    row
                    for row in rows
                    if row.get("TechId") == new_id
                    and all(row.get(key) == value for key, value in identity.items())
                ]
                if len(targets) != 1:
                    raise ValueError(
                        f"Expected one {filename}:{parameter} target for "
                        f"{new_id}, {identity}; found {len(targets)}"
                    )
                for key, value in old_row.items():
                    if str(key).isdigit():
                        targets[0][key] = value
    write_json(path, data)


def set_relations(
    case_path: Path,
    tech_ids: dict[str, str],
    comm_ids: dict[str, str],
    checkpoint: str,
    years: list[int],
) -> None:
    path = case_path / "RYTCM.json"
    data = read_json(path)
    new_ids = set(NEW_TECH_IDS.values())
    for parameter in ("IAR", "OAR"):
        for row in rows_for_parameter(data, parameter):
            if row.get("TechId") in new_ids:
                set_years(row, {year: 0.0 for year in years})

    def relation(
        parameter: str,
        technology: str,
        commodity: str,
        value: float,
    ) -> None:
        row = parameter_row(
            data,
            parameter,
            TechId=tech_ids[technology],
            CommId=comm_ids[commodity],
            MoId=1,
        )
        set_years(row, {year: value for year in years})

    bagasse_ratio = (
        ACCOUNTING_BAGASSE_PJ_PER_MT_CANE
        if checkpoint == "accounting"
        else EXPORTABLE_BAGASSE_PJ_PER_MT_CANE
    )
    relation("IAR", MILL, RAW_CANE, 1.0)
    relation("OAR", MILL, PROCESSED_CANE, 1.0)
    relation("OAR", MILL, EXPORTABLE_BAGASSE, bagasse_ratio)
    relation("IAR", BAGASSE_POWER, EXPORTABLE_BAGASSE, POWER_HEAT_RATE)
    relation("OAR", BAGASSE_POWER, GRID_OUTPUT, 1.0)
    relation("IAR", WOOD_POWER, WOOD_FUEL, POWER_HEAT_RATE)
    relation("OAR", WOOD_POWER, GRID_OUTPUT, 1.0)
    write_json(path, data)


def apply_parameter_values(
    case_path: Path, checkpoint: str
) -> dict[str, Any]:
    gen_data = read_json(case_path / "genData.json")
    tech_ids = entity_map(gen_data["osy-tech"], "Tech", "TechId")
    comm_ids = entity_map(gen_data["osy-comm"], "Comm", "CommId")
    years = [int(year) for year in gen_data["osy-years"]]
    old_id = tech_ids[OLD_POWER]
    power_ids = [tech_ids[BAGASSE_POWER], tech_ids[WOOD_POWER]]

    ryc_path = case_path / "RYC.json"
    ryc = read_json(ryc_path)
    inherited_row = parameter_row(
        ryc, "AAD", CommId=comm_ids[RAW_CANE]
    )
    inherited = year_values(inherited_row, years)
    throughput = (
        inherited
        if checkpoint == "accounting"
        else cane_throughput(years, inherited)
    )
    set_years(inherited_row, {year: 0.0 for year in years})
    processed_row = parameter_row(
        ryc, "AAD", CommId=comm_ids[PROCESSED_CANE]
    )
    set_years(processed_row, throughput)
    write_json(ryc_path, ryc)

    copy_single_tech_parameters(case_path, old_id, power_ids)
    # RYTCn custom-constraint rows are rebuilt by update_reserve_proxy below.
    for filename in ("RYT.json", "RYTM.json", "RYTTs.json"):
        copy_year_tech_parameters(case_path, filename, old_id, power_ids)

    rt_path = case_path / "RT.json"
    rt = read_json(rt_path)
    mill_id = tech_ids[MILL]
    for parameter, value in {
        "CAU": 1.0,
        "DRI": 0.05,
        "OL": 30,
        "TMPAL": 0.0,
        "TMPAU": 999999.0,
    }.items():
        rt[parameter][BASE_SCENARIO][0][mill_id] = value
    write_json(rt_path, rt)

    ryt_path = case_path / "RYT.json"
    ryt = read_json(ryt_path)
    all_zero = {year: 0.0 for year in years}
    for parameter in ("RC", "TAMaxC", "TAMaxCI", "TAU"):
        set_years(
            parameter_row(ryt, parameter, TechId=old_id), all_zero
        )

    old_rc = year_values(
        parameter_row(ryt, "RC", TechId=tech_ids[BAGASSE_POWER]), years
    )
    # The rows were copied before the aggregate technology was disabled.
    for technology, share in (
        (BAGASSE_POWER, BAGASSE_CAPACITY_GW / AGGREGATE_CAPACITY_GW),
        (WOOD_POWER, WOOD_CAPACITY_GW / AGGREGATE_CAPACITY_GW),
    ):
        set_years(
            parameter_row(ryt, "RC", TechId=tech_ids[technology]),
            {year: old_rc[year] * share for year in years},
        )

    old_af = year_values(
        parameter_row(ryt, "AF", TechId=tech_ids[BAGASSE_POWER]), years
    )
    if checkpoint == "physical":
        bagasse_af = {year: 1.0 for year in years}
        wood_af = {year: WOOD_AVAILABILITY for year in years}
    else:
        bagasse_af = old_af
        wood_af = old_af
    set_years(
        parameter_row(ryt, "AF", TechId=tech_ids[BAGASSE_POWER]),
        bagasse_af,
    )
    set_years(
        parameter_row(ryt, "AF", TechId=tech_ids[WOOD_POWER]),
        wood_af,
    )
    if checkpoint == "physical":
        set_years(
            parameter_row(ryt, "TAU", TechId=tech_ids[WOOD_POWER]),
            {year: WOOD_ACTIVITY_UPPER_PJ for year in years},
        )

    mill_values = {
        "AF": {year: 1.0 for year in years},
        "CC": {year: 0.0 for year in years},
        "COTU": {year: 0.0 for year in years},
        "FC": {year: 0.0 for year in years},
        "RC": {year: 2.1 for year in years},
        "TAL": {year: 0.0 for year in years},
        "TAMaxC": {year: 2.1 for year in years},
        "TAMaxCI": {year: 0.0 for year in years},
        "TAMinC": {year: 0.0 for year in years},
        "TAMinCI": {year: 0.0 for year in years},
        "TAU": throughput,
    }
    for parameter, values in mill_values.items():
        set_years(
            parameter_row(ryt, parameter, TechId=mill_id), values
        )
    write_json(ryt_path, ryt)

    rytts_path = case_path / "RYTTs.json"
    rytts = read_json(rytts_path)
    mill_cf_rows = [
        row
        for row in rows_for_parameter(rytts, "CF")
        if row.get("TechId") == mill_id
    ]
    if len(mill_cf_rows) != len(gen_data["osy-ts"]):
        raise ValueError("Unexpected mill CapacityFactor row count")
    for row in mill_cf_rows:
        set_years(row, {year: 1.0 for year in years})
    write_json(rytts_path, rytts)

    rytm_path = case_path / "RYTM.json"
    rytm = read_json(rytm_path)
    for parameter in ("VC",):
        for row in rows_for_parameter(rytm, parameter):
            if row.get("TechId") == mill_id:
                set_years(row, {year: 0.0 for year in years})
    write_json(rytm_path, rytm)

    set_relations(
        case_path, tech_ids, comm_ids, checkpoint, years
    )
    return {
        "checkpoint": checkpoint,
        "cane_throughput_mt": throughput,
        "bagasse_capacity_gw": BAGASSE_CAPACITY_GW,
        "wood_capacity_gw": WOOD_CAPACITY_GW,
        "export_kwh_per_t_cane": EXPORT_KWH_PER_T_CANE,
        "exportable_bagasse_pj_per_mt_cane": (
            ACCOUNTING_BAGASSE_PJ_PER_MT_CANE
            if checkpoint == "accounting"
            else EXPORTABLE_BAGASSE_PJ_PER_MT_CANE
        ),
        "power_heat_rate": POWER_HEAT_RATE,
        "wood_availability": (
            old_af[years[0]]
            if checkpoint == "accounting"
            else WOOD_AVAILABILITY
        ),
        "wood_generation_upper_pj": (
            None
            if checkpoint == "accounting"
            else WOOD_ACTIVITY_UPPER_PJ
        ),
        "old_aggregate_disabled": True,
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
    muiogo_root: Path,
    checkpoint: str,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, Any]:
    storage = source_case.parent
    before = source_fingerprints(source_case)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{target_case.name}.phase1d-", dir=storage
        )
    )
    try:
        copy_case_sources(source_case, stage)
        gen_data = update_gen_data(
            read_json(stage / "genData.json"), checkpoint
        )
        gen_data["osy-casename"] = target_case.name
        write_json(stage / "genData.json", gen_data)
        run_update_case(muiogo_root, stage, gen_data)
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
                    destination.suffix + ".phase1d"
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
                    target_case.name + ".phase1d-backup"
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
    normalized = [
        {field: str(row[field]) for field in fields}
        for row in additions
    ]
    write_csv(path, fields, kept + normalized)
    return len(rows) - len(kept), len(normalized)


def clone_power_rows(inputs: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(inputs.glob("*.csv")):
        fields, rows = read_csv(path)
        if "TECHNOLOGY" not in fields:
            continue
        if path.name in {
            "InputActivityRatio.csv",
            "OutputActivityRatio.csv",
        }:
            continue
        source_rows = [
            row for row in rows if row["TECHNOLOGY"] == OLD_POWER
        ]
        if not source_rows:
            continue
        kept = [
            row
            for row in rows
            if row["TECHNOLOGY"]
            not in {BAGASSE_POWER, WOOD_POWER}
        ]
        additions = []
        for technology in (BAGASSE_POWER, WOOD_POWER):
            for source in source_rows:
                cloned = dict(source)
                cloned["TECHNOLOGY"] = technology
                additions.append(cloned)
        write_csv(path, fields, kept + additions)
        counts[path.name] = len(additions)
    return counts


def sync_csv_inputs(
    *,
    inputs: Path,
    source_case: Path,
    checkpoint: str,
    dry_run: bool,
) -> dict[str, Any]:
    gen_data = read_json(source_case / "genData.json")
    years = [int(year) for year in gen_data["osy-years"]]
    ryc = read_json(source_case / "RYC.json")
    comm_ids = entity_map(gen_data["osy-comm"], "Comm", "CommId")
    inherited_raw = year_values(
        parameter_row(ryc, "AAD", CommId=comm_ids[RAW_CANE]), years
    )
    if all(value == 0.0 for value in inherited_raw.values()):
        throughput = year_values(
            parameter_row(
                ryc, "AAD", CommId=comm_ids[PROCESSED_CANE]
            ),
            years,
        )
    else:
        throughput = (
            inherited_raw
            if checkpoint == "accounting"
            else cane_throughput(years, inherited_raw)
        )
    if dry_run:
        return {
            "dry_run": True,
            "checkpoint": checkpoint,
            "technologies": list(NEW_TECH_IDS),
            "commodities": list(NEW_COMM_IDS),
        }

    for technology in NEW_TECH_IDS:
        append_set_value(inputs / "TECHNOLOGY.csv", technology)
    for commodity in NEW_COMM_IDS:
        append_set_value(inputs / "FUEL.csv", commodity)
    cloned = clone_power_rows(inputs)

    _, old_rc_rows = read_csv(inputs / "ResidualCapacity.csv")
    old_rc = {
        int(row["YEAR"]): float(row["VALUE"])
        for row in old_rc_rows
        if row["TECHNOLOGY"] == OLD_POWER
    }
    _, old_af_rows = read_csv(inputs / "AvailabilityFactor.csv")
    old_af = {
        int(row["YEAR"]): float(row["VALUE"])
        for row in old_af_rows
        if row["TECHNOLOGY"] == OLD_POWER
    }
    if set(old_rc) != set(years) or set(old_af) != set(years):
        raise ValueError("Incomplete aggregate biomass CSV parameter rows")

    demand_rows = [
        {
            "REGION": "GLOBAL",
            "FUEL": PROCESSED_CANE,
            "YEAR": year,
            "VALUE": f"{throughput[year]:.12g}",
        }
        for year in years
    ]
    aad = replace_parameter_rows(
        inputs / "AccumulatedAnnualDemand.csv",
        remove=lambda row: row["FUEL"] in {RAW_CANE, PROCESSED_CANE},
        additions=demand_rows,
    )

    bagasse_ratio = (
        ACCOUNTING_BAGASSE_PJ_PER_MT_CANE
        if checkpoint == "accounting"
        else EXPORTABLE_BAGASSE_PJ_PER_MT_CANE
    )
    iar_rows = []
    oar_rows = []
    for year in years:
        for technology, fuel, value in (
            (MILL, RAW_CANE, 1.0),
            (BAGASSE_POWER, EXPORTABLE_BAGASSE, POWER_HEAT_RATE),
            (WOOD_POWER, WOOD_FUEL, POWER_HEAT_RATE),
        ):
            iar_rows.append(
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": technology,
                    "FUEL": fuel,
                    "MODE_OF_OPERATION": 1,
                    "YEAR": year,
                    "VALUE": f"{value:.12g}",
                }
            )
        for technology, fuel, value in (
            (MILL, PROCESSED_CANE, 1.0),
            (MILL, EXPORTABLE_BAGASSE, bagasse_ratio),
            (BAGASSE_POWER, GRID_OUTPUT, 1.0),
            (WOOD_POWER, GRID_OUTPUT, 1.0),
        ):
            oar_rows.append(
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": technology,
                    "FUEL": fuel,
                    "MODE_OF_OPERATION": 1,
                    "YEAR": year,
                    "VALUE": f"{value:.12g}",
                }
            )
    iar = replace_parameter_rows(
        inputs / "InputActivityRatio.csv",
        remove=lambda row: row["TECHNOLOGY"]
        in {MILL, BAGASSE_POWER, WOOD_POWER},
        additions=iar_rows,
    )
    oar = replace_parameter_rows(
        inputs / "OutputActivityRatio.csv",
        remove=lambda row: row["TECHNOLOGY"]
        in {MILL, BAGASSE_POWER, WOOD_POWER},
        additions=oar_rows,
    )

    rc_rows = []
    af_rows = []
    max_capacity_rows = []
    max_investment_rows = []
    activity_upper_rows = []
    for year in years:
        for technology, share in (
            (BAGASSE_POWER, BAGASSE_CAPACITY_GW / AGGREGATE_CAPACITY_GW),
            (WOOD_POWER, WOOD_CAPACITY_GW / AGGREGATE_CAPACITY_GW),
        ):
            rc_rows.append(
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": technology,
                    "YEAR": year,
                    "VALUE": f"{old_rc[year] * share:.12g}",
                }
            )
        rc_rows.extend(
            [
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": OLD_POWER,
                    "YEAR": year,
                    "VALUE": 0.0,
                },
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": MILL,
                    "YEAR": year,
                    "VALUE": 2.1,
                },
            ]
        )
        for technology, value in (
            (
                BAGASSE_POWER,
                old_af[year] if checkpoint == "accounting" else 1.0,
            ),
            (
                WOOD_POWER,
                old_af[year]
                if checkpoint == "accounting"
                else WOOD_AVAILABILITY,
            ),
            (MILL, 1.0),
        ):
            af_rows.append(
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": technology,
                    "YEAR": year,
                    "VALUE": f"{value:.12g}",
                }
            )
        max_capacity_rows.extend(
            [
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": OLD_POWER,
                    "YEAR": year,
                    "VALUE": 0.0,
                },
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": MILL,
                    "YEAR": year,
                    "VALUE": 2.1,
                },
            ]
        )
        max_investment_rows.extend(
            [
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": OLD_POWER,
                    "YEAR": year,
                    "VALUE": 0.0,
                },
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": MILL,
                    "YEAR": year,
                    "VALUE": 0.0,
                },
            ]
        )
        activity_upper_rows.extend(
            [
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": OLD_POWER,
                    "YEAR": year,
                    "VALUE": 0.0,
                },
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": MILL,
                    "YEAR": year,
                    "VALUE": f"{throughput[year]:.12g}",
                },
            ]
        )
        if checkpoint == "physical":
            activity_upper_rows.append(
                {
                    "REGION": "GLOBAL",
                    "TECHNOLOGY": WOOD_POWER,
                    "YEAR": year,
                    "VALUE": f"{WOOD_ACTIVITY_UPPER_PJ:.12g}",
                }
            )

    affected_techs = {OLD_POWER, MILL, BAGASSE_POWER, WOOD_POWER}
    rc = replace_parameter_rows(
        inputs / "ResidualCapacity.csv",
        remove=lambda row: row["TECHNOLOGY"] in affected_techs,
        additions=rc_rows,
    )
    af = replace_parameter_rows(
        inputs / "AvailabilityFactor.csv",
        remove=lambda row: row["TECHNOLOGY"]
        in {MILL, BAGASSE_POWER, WOOD_POWER},
        additions=af_rows,
    )
    max_capacity = replace_parameter_rows(
        inputs / "TotalAnnualMaxCapacity.csv",
        remove=lambda row: row["TECHNOLOGY"] in {OLD_POWER, MILL},
        additions=max_capacity_rows,
    )
    max_investment = replace_parameter_rows(
        inputs / "TotalAnnualMaxCapacityInvestment.csv",
        remove=lambda row: row["TECHNOLOGY"] in {OLD_POWER, MILL},
        additions=max_investment_rows,
    )
    activity_upper = replace_parameter_rows(
        inputs / "TotalTechnologyAnnualActivityUpperLimit.csv",
        remove=lambda row: row["TECHNOLOGY"]
        in (
            {OLD_POWER, MILL, WOOD_POWER}
            if checkpoint == "physical"
            else {OLD_POWER, MILL}
        ),
        additions=activity_upper_rows,
    )

    capacity_to_activity = replace_parameter_rows(
        inputs / "CapacityToActivityUnit.csv",
        remove=lambda row: row["TECHNOLOGY"] == MILL,
        additions=[
            {
                "REGION": "GLOBAL",
                "TECHNOLOGY": MILL,
                "VALUE": 1.0,
            }
        ],
    )
    operational_life = replace_parameter_rows(
        inputs / "OperationalLife.csv",
        remove=lambda row: row["TECHNOLOGY"] == MILL,
        additions=[
            {
                "REGION": "GLOBAL",
                "TECHNOLOGY": MILL,
                "VALUE": 30,
            }
        ],
    )
    _, cf_rows = read_csv(inputs / "CapacityFactor.csv")
    timeslices = sorted({row["TIMESLICE"] for row in cf_rows})
    mill_cf = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": MILL,
            "TIMESLICE": timeslice,
            "YEAR": year,
            "VALUE": 1.0,
        }
        for timeslice in timeslices
        for year in years
    ]
    capacity_factor = replace_parameter_rows(
        inputs / "CapacityFactor.csv",
        remove=lambda row: row["TECHNOLOGY"] == MILL,
        additions=mill_cf,
    )
    mill_vc = [
        {
            "REGION": "GLOBAL",
            "TECHNOLOGY": MILL,
            "MODE_OF_OPERATION": 1,
            "YEAR": year,
            "VALUE": 0.0,
        }
        for year in years
    ]
    variable_cost = replace_parameter_rows(
        inputs / "VariableCost.csv",
        remove=lambda row: row["TECHNOLOGY"] == MILL,
        additions=mill_vc,
    )
    return {
        "dry_run": False,
        "checkpoint": checkpoint,
        "cloned_power_rows": cloned,
        "AccumulatedAnnualDemand": aad,
        "InputActivityRatio": iar,
        "OutputActivityRatio": oar,
        "ResidualCapacity": rc,
        "AvailabilityFactor": af,
        "TotalAnnualMaxCapacity": max_capacity,
        "TotalAnnualMaxCapacityInvestment": max_investment,
        "TotalTechnologyAnnualActivityUpperLimit": activity_upper,
        "CapacityToActivityUnit": capacity_to_activity,
        "OperationalLife": operational_life,
        "CapacityFactor": capacity_factor,
        "VariableCost": variable_cost,
    }


def write_evidence(path: Path) -> dict[str, Any]:
    fields = [
        "year",
        "split",
        "cane_crushed_t",
        "sugar_made_t",
        "molasses_t",
        "gross_bagasse_proxy_t",
        "export_electricity_coefficient_kwh_per_t_cane",
        "bagasse_export_electricity_mwh",
        "bagasse_exportable_fuel_pj",
        "observed_aggregate_ipp_mwh",
        "residual_wood_generation_mwh",
        "implied_wood_availability",
        "active_wood_availability",
        "active_wood_generation_upper_pj",
        "fsc_source",
        "fsc_locator",
        "engineering_source",
        "engineering_locator",
        "generation_source",
        "generation_locator",
    ]
    rows = []
    for year in HISTORICAL_YEARS:
        item = FSC_OPERATIONS[year]
        bagasse_mwh = bagasse_generation_mwh(item["cane_t"])
        residual = IPP_MWH[year] - bagasse_mwh
        implied_af = residual / (
            WOOD_CAPACITY_GW * 1000.0 * 8.76 * 1000.0
        )
        rows.append(
            {
                "year": year,
                "split": (
                    "calibration"
                    if year in CALIBRATION_YEARS
                    else "validation"
                ),
                "cane_crushed_t": item["cane_t"],
                "sugar_made_t": item["sugar_t"],
                "molasses_t": item["molasses_t"],
                "gross_bagasse_proxy_t": (
                    f"{item['cane_t'] * GROSS_BAGASSE_T_PER_T_CANE:.3f}"
                ),
                "export_electricity_coefficient_kwh_per_t_cane": (
                    EXPORT_KWH_PER_T_CANE
                ),
                "bagasse_export_electricity_mwh": f"{bagasse_mwh:.6f}",
                "bagasse_exportable_fuel_pj": (
                    f"{bagasse_mwh * PJ_PER_MWH * POWER_HEAT_RATE:.12f}"
                ),
                "observed_aggregate_ipp_mwh": IPP_MWH[year],
                "residual_wood_generation_mwh": f"{residual:.6f}",
                "implied_wood_availability": f"{implied_af:.12f}",
                "active_wood_availability": f"{WOOD_AVAILABILITY:.12f}",
                "active_wood_generation_upper_pj": (
                    f"{WOOD_ACTIVITY_UPPER_PJ:.12f}"
                ),
                "fsc_source": item["report"],
                "fsc_locator": item["locator"],
                "engineering_source": (
                    "IRENA, Sugarcane bioenergy in Southern Africa (2019)"
                ),
                "engineering_locator": (
                    "PDF p. 37, Table 3.1, 42 bar / 400 C / 500 kg "
                    "steam per t cane / no straw"
                ),
                "generation_source": "Energy Fiji Limited 2024 Annual Report",
                "generation_locator": (
                    "printed p. 88, Generation Statistics for the Past "
                    "Ten (10) Years"
                ),
            }
        )
    write_csv(path, fields, rows)
    return {
        "path": str(path),
        "rows": len(rows),
        "sha256": sha256(path),
        "wood_availability": WOOD_AVAILABILITY,
        "wood_generation_upper_pj": WOOD_ACTIVITY_UPPER_PJ,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        choices=("accounting", "physical"),
        default="physical",
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
        help="Write the frozen evidence table without creating a case.",
    )
    parser.add_argument(
        "--evidence", type=Path, default=DEFAULT_EVIDENCE
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

    if args.evidence_only:
        if args.dry_run:
            raise SystemExit("--evidence-only cannot be combined with --dry-run")
        print(
            json.dumps(
                {
                    "phase": "1D cane-bagasse-electricity",
                    "date": date.today().isoformat(),
                    "evidence": write_evidence(args.evidence.resolve()),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    target_name = args.target_case or (
        "Fiji_v2_Phase1D_Accounting_Test"
        if args.checkpoint == "accounting"
        else "Fiji_v2_Phase1D_Physical_Test"
    )
    target_case = storage / target_name
    report: dict[str, Any] = {
        "phase": "1D cane-bagasse-electricity",
        "date": date.today().isoformat(),
        "case": install_case(
            source_case=source_case,
            target_case=target_case,
            muiogo_root=muiogo_root,
            checkpoint=args.checkpoint,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        ),
    }
    if args.sync_csv_inputs:
        report["csv_inputs"] = sync_csv_inputs(
            inputs=args.inputs.resolve(),
            source_case=source_case,
            checkpoint=args.checkpoint,
            dry_run=args.dry_run,
        )
    if args.write_evidence and not args.dry_run:
        report["evidence"] = write_evidence(args.evidence.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
