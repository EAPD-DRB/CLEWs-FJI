#!/usr/bin/env python3
"""Create Fiji v2.9 with population-driven fish demand and trade backstop."""

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
SOURCE_NAME = "Fiji_v2.8"
DEFAULT_TARGET = ".Fiji_v2.9-population-fisheries-trade-candidate"
DATA_PATH = REPO / "scripts" / "data" / "fiji_v29_population_fisheries_trade.json"
SCENARIO = "SC_0"
YEARS = [str(year) for year in range(2020, 2051)]
FISHERIES_GROUP = "TG_fisheries"
CAPTURE_HARVEST = "TEC_fsh_cap_harv"
AQUACULTURE_HARVEST = "TEC_fsh_aq_harv"

CAP_SERVICE = "COM_fsh_cap"
AQ_SERVICE = "COM_fsh_aq"
POST_SERVICE = "COM_fsh_post"
RAW_FISH = "COM_fsh_raw"
FOOD_FISH = "COM_fsh_food"

COMMODITIES = {
    RAW_FISH: {
        "name": "FSHRAW",
        "description": "Aggregate raw fish landed by Fiji capture fisheries or aquaculture",
    },
    FOOD_FISH: {
        "name": "FSHFOOD",
        "description": "Aggregate market-weight fish available for resident food or domestic export",
    },
}

TECHNOLOGIES = {
    CAPTURE_HARVEST: {
        "name": "FSHCAPHARV",
        "description": "Mass-link conversion from capture-fleet useful service to raw landed fish",
        "inputs": [CAP_SERVICE],
        "output": RAW_FISH,
        "classification": "physical mass-balance conversion; not additional fleet stock",
    },
    AQUACULTURE_HARVEST: {
        "name": "FSHAQHARV",
        "description": "Mass-link conversion from aquaculture operations useful service to raw harvested fish",
        "inputs": [AQ_SERVICE],
        "output": RAW_FISH,
        "classification": "physical mass-balance conversion; not additional aquaculture equipment stock",
    },
    "TEC_fsh_post_prc": {
        "name": "FSHPOSTPRC",
        "description": "Mass-link conversion from raw fish and post-harvest useful service to market-weight fish",
        "inputs": [RAW_FISH, POST_SERVICE],
        "output": FOOD_FISH,
        "classification": "physical mass-balance conversion; not duplicate cold-chain equipment stock",
    },
    "TEC_imp_fsh_food": {
        "name": "IMPFSHFOOD",
        "description": "Imported market-weight fish backstop supplying FSHFOOD",
        "inputs": [],
        "output": FOOD_FISH,
        "classification": "accounting backstop/pass-through; not physical domestic stock",
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


def source_hashes(source: Path) -> dict[str, str]:
    return {path.name: digest(path) for path in sorted(source.glob("*.json"))}


def row_for(data: dict[str, Any], parameter: str, **identity: Any) -> dict[str, Any]:
    matches = [
        row
        for row in data[parameter][SCENARIO]
        if all(row.get(field) == value for field, value in identity.items())
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {parameter} row for {identity}, found {len(matches)}"
        )
    return matches[0]


def set_years(row: dict[str, Any], value: float | dict[str, float]) -> None:
    for year in YEARS:
        row[year] = value[year] if isinstance(value, dict) else value


def build_series(data: dict[str, Any]) -> dict[str, Any]:
    population = {year: float(value) for year, value in data["population_people"].items()}
    if sorted(population) != YEARS:
        raise AssertionError("population series must cover every model year 2020-2050")
    food_observations = {
        year: float(value)
        for year, value in data["resident_food_observations_kg_per_person"].items()
        if year.isdigit()
    }
    if sorted(food_observations) != ["2021", "2022", "2023"]:
        raise AssertionError("resident food observations must cover 2021-2023")
    food_kg_per_person = sum(food_observations.values()) / len(food_observations)
    trade = data["trade_2025_net_weight_kg"]
    gross_imports_2025_kg = sum(float(value) for value in trade["imports"].values())
    re_exports_2025_kg = sum(float(value) for value in trade["re_exports"].values())
    if set(trade["imports"]) != set(trade["re_exports"]):
        raise AssertionError("import and re-export HS headings must match")
    retained_imports_by_hs_kg = {
        code: max(float(value) - float(trade["re_exports"][code]), 0.0)
        for code, value in trade["imports"].items()
    }
    imports_2025_kg = sum(retained_imports_by_hs_kg.values())
    exports_2025_kg = sum(float(value) for value in trade["domestic_exports"].values())
    reference_population = population["2025"]
    domestic_food: dict[str, float] = {}
    minimum_import: dict[str, float] = {}
    export_demand: dict[str, float] = {}
    final_demand: dict[str, float] = {}
    for year in YEARS:
        scale = population[year] / reference_population
        domestic_food[year] = food_kg_per_person * population[year] / 1_000_000_000.0
        minimum_import[year] = imports_2025_kg * scale / 1_000_000_000.0
        export_demand[year] = exports_2025_kg * scale / 1_000_000_000.0
        final_demand[year] = domestic_food[year] + export_demand[year]
        if minimum_import[year] >= final_demand[year]:
            raise AssertionError(f"import floor removes all domestic fish supply in {year}")
    calibration = data["service_calibration_2020"]
    capture_mt = float(calibration["capture_landings_tonnes"]) / 1_000_000.0
    aquaculture_mt = float(calibration["aquaculture_harvest_tonnes"]) / 1_000_000.0
    post_mt = float(calibration["post_harvest_throughput_tonnes"]) / 1_000_000.0
    service_intensity = {
        "capture_pj_per_mt": float(calibration["capture_service_pj"]) / capture_mt,
        "aquaculture_pj_per_mt": float(calibration["aquaculture_service_pj"]) / aquaculture_mt,
        "post_pj_per_mt": float(calibration["post_service_pj"]) / post_mt,
        "raw_mt_per_food_mt": 1.0 / float(calibration["market_output_per_raw_input"]),
    }
    if not all(math.isfinite(value) and value > 0 for value in service_intensity.values()):
        raise AssertionError("invalid service-to-fish calibration coefficient")

    limits = data["fisheries_activity_upper_limit_tonnes"]
    capture_anchor = limits["capture"]["2020_anchor"]
    capture_tonnes = float(capture_anchor["total"])
    if not math.isclose(
        capture_tonnes,
        float(capture_anchor["offshore_longline"])
        + float(capture_anchor["coastal_commercial"]),
        abs_tol=1e-12,
    ):
        raise AssertionError("capture ceiling components do not sum to the total")
    if not math.isclose(
        capture_tonnes,
        float(calibration["capture_landings_tonnes"]),
        abs_tol=1e-12,
    ):
        raise AssertionError("capture ceiling does not match the included calibration boundary")
    capture_activity_upper_mt = {
        year: capture_tonnes / 1_000_000.0 for year in YEARS
    }

    aquaculture = limits["aquaculture"]
    observed = aquaculture["observed_total_2021_2022"]
    observed_total = float(observed["total"])
    if not math.isclose(
        observed_total,
        float(observed["tilapia"]) + float(observed["freshwater_prawn"]),
        abs_tol=1e-12,
    ):
        raise AssertionError("observed aquaculture components do not sum to the total")
    programme = aquaculture["programme_components"]
    if sorted(programme) != [str(year) for year in range(2024, 2029)]:
        raise AssertionError("aquaculture programme must cover 2024-2028")
    for year, components in programme.items():
        component_total = sum(
            float(components[name])
            for name in ("tilapia", "freshwater_prawn", "shrimp")
        )
        if not math.isclose(component_total, float(components["total"]), abs_tol=1e-12):
            raise AssertionError(f"aquaculture programme components do not sum in {year}")
    aquaculture_activity_upper_mt: dict[str, float] = {}
    for year in YEARS:
        numeric_year = int(year)
        if numeric_year <= 2023:
            tonnes = observed_total
        elif numeric_year <= 2028:
            tonnes = float(programme[year]["total"])
        else:
            tonnes = float(programme["2028"]["total"])
        aquaculture_activity_upper_mt[year] = tonnes / 1_000_000.0
    if any(
        aquaculture_activity_upper_mt[YEARS[index]]
        > aquaculture_activity_upper_mt[YEARS[index + 1]]
        for index in range(len(YEARS) - 1)
    ):
        raise AssertionError("aquaculture activity ceiling must be non-decreasing")
    return {
        "population": population,
        "food_observations_kg_per_person": food_observations,
        "food_kg_per_person": food_kg_per_person,
        "gross_imports_2025_kg": gross_imports_2025_kg,
        "re_exports_2025_kg": re_exports_2025_kg,
        "retained_imports_by_hs_kg": retained_imports_by_hs_kg,
        "imports_2025_kg": imports_2025_kg,
        "domestic_exports_2025_kg": exports_2025_kg,
        "domestic_food_mt": domestic_food,
        "minimum_import_mt": minimum_import,
        "export_demand_mt": export_demand,
        "final_demand_mt": final_demand,
        "minimum_domestic_supply_mt": {
            year: final_demand[year] - minimum_import[year] for year in YEARS
        },
        "service_intensity": service_intensity,
        "capture_activity_upper_mt": capture_activity_upper_mt,
        "aquaculture_activity_upper_mt": aquaculture_activity_upper_mt,
        "annual_activity_upper_mt": {
            CAPTURE_HARVEST: capture_activity_upper_mt,
            AQUACULTURE_HARVEST: aquaculture_activity_upper_mt,
        },
    }


def commodity_records() -> list[dict[str, str]]:
    return [
        {
            "CommId": comm_id,
            "Comm": spec["name"],
            "Desc": f"{spec['description']}; numerical unit is million tonnes.",
            "UnitId": "Mt",
        }
        for comm_id, spec in COMMODITIES.items()
    ]


def technology_records() -> list[dict[str, Any]]:
    return [
        {
            "TechId": tech_id,
            "Tech": spec["name"],
            "Desc": (
                f"{spec['description']}. {spec['classification'].capitalize()}; "
                "open activity and one-year accounting capacity."
            ),
            "CapUnitId": "Mt/year",
            "ActUnitId": "Mt",
            "IAR": spec["inputs"],
            "OAR": [spec["output"]],
            "EAR": [],
            "INCR": [],
            "ITCR": [],
            "TG": [FISHERIES_GROUP],
        }
        for tech_id, spec in TECHNOLOGIES.items()
    ]


def build_gen(source: dict[str, Any]) -> dict[str, Any]:
    gen = copy.deepcopy(source)
    existing_tech_ids = {row["TechId"] for row in gen["osy-tech"]}
    existing_tech_names = {row["Tech"] for row in gen["osy-tech"]}
    existing_comm_ids = {row["CommId"] for row in gen["osy-comm"]}
    existing_comm_names = {row["Comm"] for row in gen["osy-comm"]}
    collisions = (
        set(TECHNOLOGIES) & existing_tech_ids
        | {spec["name"] for spec in TECHNOLOGIES.values()} & existing_tech_names
        | set(COMMODITIES) & existing_comm_ids
        | {spec["name"] for spec in COMMODITIES.values()} & existing_comm_names
    )
    if collisions:
        raise AssertionError(f"Fisheries mass-link identifiers already exist: {sorted(collisions)}")
    if not any(row["TechGroupId"] == FISHERIES_GROUP for row in gen["osy-techGroups"]):
        raise AssertionError("existing Fiji Fisheries technology group is missing")
    required_services = {CAP_SERVICE, AQ_SERVICE, POST_SERVICE}
    if not required_services.issubset(existing_comm_ids):
        raise AssertionError("existing Fisheries service commodities are missing")
    gen["osy-casename"] = "Fiji_v2.9"
    gen["osy-date"] = str(date.today())
    gen["osy-desc"] = (
        "Fiji v2.9: resident fish-food demand and 2025 retained fish imports/domestic exports "
        "scale with UN WPP 2024 population; capture, aquaculture and post-harvest "
        "services are pulled endogenously through fish mass balances. Derived from solved Fiji_v2.8."
    )
    gen["osy-comm"].extend(commodity_records())
    gen["osy-tech"].extend(technology_records())
    return gen


def overlay_demands(case: Path, series: dict[str, Any]) -> None:
    data = read_json(case / "RYC.json")
    for comm_id in (CAP_SERVICE, AQ_SERVICE, POST_SERVICE, RAW_FISH):
        set_years(row_for(data, "AAD", CommId=comm_id), 0.0)
        set_years(row_for(data, "SAD", CommId=comm_id), 0.0)
    set_years(row_for(data, "AAD", CommId=FOOD_FISH), series["final_demand_mt"])
    set_years(row_for(data, "SAD", CommId=FOOD_FISH), 0.0)
    write_json(case / "RYC.json", data)


def overlay_annual_technology(
    case: Path, series: dict[str, Any], accounting_capacity_cost: float
) -> None:
    data = read_json(case / "RYT.json")
    for tech_id in TECHNOLOGIES:
        activity_upper = series["annual_activity_upper_mt"].get(tech_id, 999999.0)
        for parameter, values in (
            ("COTU", 0.0),
            ("TAU", activity_upper),
            (
                "TAL",
                series["minimum_import_mt"] if tech_id == "TEC_imp_fsh_food" else 0.0,
            ),
            ("TAMinCI", 0.0),
            ("TAMinC", 0.0),
            ("TAMaxCI", 999999.0),
            ("TAMaxC", 999999.0),
            ("RC", 0.0),
            ("FC", 0.0),
            ("CC", accounting_capacity_cost),
            ("AF", 1.0),
        ):
            set_years(row_for(data, parameter, TechId=tech_id), values)
    write_json(case / "RYT.json", data)


def overlay_region_technology(case: Path) -> None:
    data = read_json(case / "RT.json")
    for parameter, value in (("CAU", 1.0), ("OL", 1)):
        rows = data[parameter][SCENARIO]
        if len(rows) != 1:
            raise AssertionError(f"expected one RT/{parameter} region row")
        for tech_id in TECHNOLOGIES:
            rows[0][tech_id] = value
    write_json(case / "RT.json", data)


def overlay_ratios(case: Path, series: dict[str, Any]) -> None:
    data = read_json(case / "RYTCM.json")
    intensity = series["service_intensity"]
    inputs = {
        "TEC_fsh_cap_harv": {CAP_SERVICE: intensity["capture_pj_per_mt"]},
        "TEC_fsh_aq_harv": {AQ_SERVICE: intensity["aquaculture_pj_per_mt"]},
        "TEC_fsh_post_prc": {
            RAW_FISH: intensity["raw_mt_per_food_mt"],
            POST_SERVICE: intensity["post_pj_per_mt"],
        },
        "TEC_imp_fsh_food": {},
    }
    for parameter in ("IAR", "OAR"):
        for row in data[parameter][SCENARIO]:
            tech_id = row.get("TechId")
            if tech_id not in TECHNOLOGIES:
                continue
            value = 0.0
            if row["MoId"] == 1:
                if parameter == "IAR":
                    value = inputs[tech_id].get(row["CommId"], 0.0)
                elif row["CommId"] == TECHNOLOGIES[tech_id]["output"]:
                    value = 1.0
            set_years(row, value)
    write_json(case / "RYTCM.json", data)


def overlay_modes(case: Path, import_variable_cost: float) -> None:
    data = read_json(case / "RYTM.json")
    for parameter in ("TADML", "TAIML", "TAMLL", "TAMUL", "VC"):
        for row in data[parameter][SCENARIO]:
            tech_id = row.get("TechId")
            if tech_id not in TECHNOLOGIES:
                continue
            if parameter == "TAMUL":
                value = 99999.0
            elif parameter == "VC" and tech_id == "TEC_imp_fsh_food" and row["MoId"] == 1:
                value = import_variable_cost
            else:
                value = 0.0
            set_years(row, value)
    write_json(case / "RYTM.json", data)


def overlay_timeslices(case: Path) -> None:
    data = read_json(case / "RYTTs.json")
    for row in data["CF"][SCENARIO]:
        if row.get("TechId") in TECHNOLOGIES:
            set_years(row, 1.0)
    write_json(case / "RYTTs.json", data)


def add_model_fixes_note(case: Path) -> None:
    path = case / "MODEL_FIXES.md"
    old = path.read_text(encoding="utf-8") if path.exists() else "# Fiji v2.9 model fixes\n"
    heading = "## 2026-08-04 — Population-driven Fisheries food demand and trade"
    if heading in old:
        return
    note = f"""

{heading}

Reason: Fiji v2.8 fixes Fisheries useful-service demands independently of the
amount of fish residents need. Fiji v2.9 adds an explicit annual fish mass
balance so population, domestic exports and imports determine how much capture,
aquaculture and post-harvest service is required.

Physical classification: `FSHRAW` and `FSHFOOD` are mass commodities.
`FSHCAPHARV`, `FSHAQHARV` and `FSHPOSTPRC` are one-year mass-link conversions;
their capacity is an accounting envelope rather than additional physical fleet,
farm or cold-chain stock. The seven v2.7 Fisheries service technologies remain
physical stocks/conversions. `IMPFSHFOOD` is an accounting backstop. `FSHFOOD`
is the final demand. Observed 2020 harvest and service values are calibration
benchmarks, not activity pins.

Source formulation: `RYC.json/AAD` for `FSHFOOD` equals resident food
availability plus domestic exports, both population-scaled. `RYT.json/TAL`
sets the population-scaled 2025 retained-import floor, with no upper import
limit. Retained imports are the sum of positive same-HS differences between
imports and reported re-exports, preventing processing/re-export throughput
from displacing domestic production. The
former `SAD` values for `FSHCAPSERV`, `FSHAQSERV` and `FSHPOSTSERV` are zero;
the mass-link technologies pull those services through `RYTCM.json/IAR`.
Tourism is not added. `RYT.json/TAU` limits `FSHCAPHARV` to the included 2020
capture boundary (23,661 tonnes/year) and `FSHAQHARV` to the observed and
programme-based aggregate envelope (216.925 tonnes/year through 2023, rising
to 1,450 tonnes/year in 2028). These are non-forcing screening ceilings, not a
legal quota, biological stock model or production target. No trade-price
response is imposed and imports remain the feasibility backstop.

Source files changed: `genData.json`, `RYC.json`, `RYT.json`, `RT.json`,
`RYTCM.json`, `RYTM.json`, and `RYTTs.json`. A disclosed `CC=1e-6` numerical
tie-breaker keeps the four accounting capacities at their minimum feasible
values instead of arbitrary open upper bounds. The evidence snapshot and all
annual series are in `population_fisheries_trade_v29_manifest.json` and
`scripts/data/fiji_v29_population_fisheries_trade.json`.

Validation status: **NOT YET COMPLETE**. This entry is created with the
disposable candidate and must be replaced with deterministic, generation,
GLPK, CBC, control-comparison and live-regeneration results before promotion.

Known limitations: fish is one aggregate market-weight commodity; species,
preservation state, edible yield and processing losses are not represented.
Feed, biological stocks, catch quotas, aquaculture land/water, farm expansion
and wastewater are represented only by the two aggregate activity ceilings,
not as explicit resources or equations. The import variable cost is a
screening penalty, not a border price.

Canonical documentation and schema ledger: `Fiji_v2.9_CLEWs_build/`
contains the six schema ledgers, retained evidence, calculation notes and
validation reports for the v2.8 crop and v2.9 Fisheries changes.
"""
    path.write_text(old.rstrip() + note + "\n", encoding="utf-8")


def write_readme(case: Path) -> None:
    (case / "README.md").write_text(
        """# Fiji v2.9

Fiji v2.9 extends the solved Fiji v2.8 CLEWs case with a population-driven
Fisheries food balance and explicit retained-import and domestic-export demand.

Two aggregate mass commodities are added: `FSHRAW` for domestic landed fish
and `FSHFOOD` for fish available to residents or domestic exports. Capture and
aquaculture useful services produce `FSHRAW`; post-harvest useful service turns
it into `FSHFOOD`. `IMPFSHFOOD` is an open, high-cost accounting backstop that
can meet additional demand if domestic production falls.

Annual `FSHFOOD` final demand is resident food availability plus 2025 domestic
exports, both scaled with the UN WPP 2024 medium population pathway. The
minimum import activity is the population-scaled 2025 retained-import proxy,
calculated from imports net of reported re-exports by HS heading. Tourism is
excluded.

Two non-forcing annual production ceilings prevent either domestic subsector
from expanding without limit: capture is capped at 23,661 tonnes/year, and
aquaculture follows an observed/programme envelope from 216.925 tonnes/year
through 2023 to 1,450 tonnes/year from 2028. Neither subsector has a production
floor; imports remain open if domestic supply is insufficient.

Permanent values reside in `genData.json` and the source `R*.json` files.
`population_fisheries_trade_v29_manifest.json` records the evidence snapshot,
annual series, assumptions and equation map. The validated bounded live run is
`res/Fisheries_Bounds_Table18_v2.9`; the former unconstrained run is preserved at
`res/Population_Fisheries_Trade_v2.9` as a baseline. See `MODEL_FIXES.md` and
`validation_fisheries_bounds_v29_final.json` for the complete solver chain,
baseline comparison and limitations.

The canonical six-ledger provenance package is
`Fiji_v2.9_CLEWs_build/`. It documents sources,
calculations, assumptions, source-to-model mappings, gaps and changes for the
v2.8 crop and v2.9 Fisheries demand/trade layers.

Important limitation: the capture ceiling is an observed-boundary proxy rather
than a legal quota or biological stock model. The aquaculture ceiling aggregates
feed, land, water, farm-expansion and environmental restrictions into a single
programme envelope. The resulting mix is a defensible screening representation,
not a species-level or facility-level forecast.
""",
        encoding="utf-8",
    )


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
    source_before = source_hashes(source)
    input_data = read_json(DATA_PATH)
    series = build_series(input_data)

    shutil.copytree(source, target, ignore=shutil.ignore_patterns("res"))
    gen = build_gen(read_json(target / "genData.json"))
    write_json(target / "genData.json", gen)
    Config.DATA_STORAGE = STORAGE
    UpdateCase(target.name, gen).updateCase()
    write_json(target / "genData.json", gen)

    overlay_demands(target, series)
    overlay_annual_technology(
        target,
        series,
        float(input_data["model_policy"]["accounting_capacity_regularization_cost"]),
    )
    overlay_region_technology(target)
    overlay_ratios(target, series)
    overlay_modes(target, float(input_data["model_policy"]["import_variable_cost"]))
    overlay_timeslices(target)
    add_model_fixes_note(target)
    write_readme(target)

    if source_hashes(source) != source_before:
        raise AssertionError("Fiji_v2.8 source changed during candidate generation")
    manifest = {
        "status": "created_not_yet_solver_validated",
        "source_case": SOURCE_NAME,
        "target_folder": target.name,
        "case_identity": "Fiji_v2.9",
        "model_format_version": gen["osy-version"],
        "source_hashes": source_before,
        "input_snapshot": str(DATA_PATH.relative_to(REPO)),
        "input_snapshot_sha256": digest(DATA_PATH),
        "new_technology_ids": list(TECHNOLOGIES),
        "new_technology_names": [spec["name"] for spec in TECHNOLOGIES.values()],
        "new_commodity_ids": list(COMMODITIES),
        "new_commodity_names": [spec["name"] for spec in COMMODITIES.values()],
        "population_people": series["population"],
        "resident_food_observations_kg_per_person": series["food_observations_kg_per_person"],
        "resident_food_kg_per_person": series["food_kg_per_person"],
        "gross_imports_2025_kg": series["gross_imports_2025_kg"],
        "reported_re_exports_2025_kg": series["re_exports_2025_kg"],
        "retained_imports_by_hs_kg": series["retained_imports_by_hs_kg"],
        "retained_imports_2025_kg": series["imports_2025_kg"],
        "domestic_exports_2025_kg": series["domestic_exports_2025_kg"],
        "domestic_food_mt": series["domestic_food_mt"],
        "minimum_import_mt": series["minimum_import_mt"],
        "export_demand_mt": series["export_demand_mt"],
        "final_demand_mt": series["final_demand_mt"],
        "minimum_domestic_supply_mt": series["minimum_domestic_supply_mt"],
        "capture_activity_upper_mt": series["capture_activity_upper_mt"],
        "aquaculture_activity_upper_mt": series["aquaculture_activity_upper_mt"],
        "service_intensity": series["service_intensity"],
        "policy": input_data["model_policy"],
        "sources": input_data["sources"],
        "generation_path": "UpdateCase(target, genData).updateCase() then source-parameter overlays",
        "equation_map": {
            "final_demand": "RYC/AAD(FSHFOOD) -> AccumulatedAnnualDemand -> EBb4_EnergyBalanceEachYear4_ICR",
            "minimum_import": "RYT/TAL(IMPFSHFOOD) -> TotalTechnologyAnnualActivityLowerLimit -> AAC3_TotalAnnualTechnologyActivityLowerLimit",
            "capture_ceiling": "RYT/TAU(FSHCAPHARV) -> TotalTechnologyAnnualActivityUpperLimit -> AAC2_TotalAnnualTechnologyActivityUpperLimit",
            "aquaculture_ceiling": "RYT/TAU(FSHAQHARV) -> TotalTechnologyAnnualActivityUpperLimit -> AAC2_TotalAnnualTechnologyActivityUpperLimit",
            "mass_links": "RYTCM/IAR,OAR -> RateOfUse/RateOfProduction -> EBb4 annual balances for FSHCAPSERV, FSHAQSERV, FSHPOSTSERV, FSHRAW and FSHFOOD",
            "import_penalty": "RYTM/VC -> AnnualVariableOperatingCost -> OC1/objective",
            "capacity": "RYT/AF, RT/CAU and RYTTs/CF -> CAa4/CAb1 activity envelopes; one-year zero-cost mass-link capacity is not physical stock",
        },
        "observation_classification": {
            "initial_stock": "existing v2.8 residual fleet, aquaculture and post-harvest service capacities only",
            "final_demand": "population-scaled resident fish availability plus population-scaled 2025 domestic exports",
            "continuing_constraint": "population-scaled 2025 import floor; aggregate capture and aquaculture activity ceilings; existing physical asset lives/availability",
            "benchmark_only": "2020 capture landings and 2021-2022 aquaculture output become conservative upper-envelope anchors, not activity requirements; service demands calibrate PJ/Mt coefficients only",
        },
        "technology_classification": {
            "existing_fisheries_service_technologies": "physical stocks/conversions",
            "FSHCAPHARV_FSHAQHARV_FSHPOSTPRC": "mass-balance conversions with accounting capacity envelopes; the two harvest conversions also have annual aggregate activity ceilings",
            "IMPFSHFOOD": "accounting import backstop/pass-through",
            "FSHFOOD_AAD": "demand",
        },
        "design_gate": {
            "unchanged_control": "Fiji_v2.9 / Population_Fisheries_Trade_v2.9 before harvest ceilings; objective 4170.87205658; matrix 178353x137090 with 743918 nonzeros",
            "last_known_good_runtime_seconds": 45.58,
            "bounded_candidate_budget_seconds": 90,
            "minimal_candidate": "source-only RYT/TAU edits for FSHCAPHARV and FSHAQHARV; no production floor, new object or user-defined constraint",
        },
        "diagnostic_history": [
            {
                "variant": "gross 2025 imports used as resident-market floor; VC=1000",
                "status": "rejected after optimal diagnostic solve",
                "objective": 4541.58329113,
                "reason": "All 0.024718111534 Mt of imports included processing/re-export throughput, leaving only 0.007006786663 Mt for Fiji production and breaking the intended retained-import boundary.",
            },
            {
                "variant": "retained imports by HS; VC=1000",
                "status": "screening-cost pilot only",
                "objective": 4223.57790759,
                "maximum_FSHFOOD_dual_discounted": 111.38863,
                "maximum_FSHFOOD_dual_undiscounted": 138.737130672,
                "decision": "Set final screening VC to 200, above the observed domestic marginal value but below the provisional 1000.",
            },
        ],
    }
    write_json(target / "population_fisheries_trade_v29_manifest.json", manifest)
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
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_case": result["source_case"],
                "target_folder": result["target_folder"],
                "case_identity": result["case_identity"],
                "new_technologies": result["new_technology_names"],
                "new_commodities": result["new_commodity_names"],
                "resident_food_kg_per_person": result["resident_food_kg_per_person"],
                "imports_2025_mt": result["minimum_import_mt"]["2025"],
                "domestic_exports_2025_mt": result["export_demand_mt"]["2025"],
                "final_demand_2025_mt": result["final_demand_mt"]["2025"],
                "minimum_domestic_supply_2025_mt": result["minimum_domestic_supply_mt"]["2025"],
                "service_intensity": result["service_intensity"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
