#!/usr/bin/env python3
"""Deterministically validate the Fiji v2.9 Fisheries food/trade candidate."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
STORAGE = REPO / "WebAPP" / "DataStorage"
SOURCE = STORAGE / "Fiji_v2.8"
DEFAULT = STORAGE / ".Fiji_v2.9-population-fisheries-trade-candidate"
AUTHORITATIVE_FILES = (
    "genData.json",
    "RYC.json",
    "RYT.json",
    "RT.json",
    "RYTCM.json",
    "RYTM.json",
    "RYTTs.json",
)
sys.path.insert(0, str(REPO / "scripts"))

import create_fiji_v29_population_fisheries_trade as build  # noqa: E402


YEARS = build.YEARS
SCENARIO = build.SCENARIO
IDENTITY_FIELDS = (
    "TechId",
    "CommId",
    "EmisId",
    "ConId",
    "MoId",
    "TsId",
    "StgId",
    "SeId",
    "DtId",
    "DtbId",
    "TechGroupId",
    "ScenarioId",
)


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def row_for(data: dict[str, Any], parameter: str, **identity: Any) -> dict[str, Any]:
    matches = [
        row
        for row in data[parameter][SCENARIO]
        if all(row.get(field) == value for field, value in identity.items())
    ]
    if len(matches) != 1:
        raise AssertionError(f"{parameter}/{identity}: expected one row, found {len(matches)}")
    return matches[0]


def allowed_existing_change(filename: str, location: str) -> bool:
    if filename == "genData.json" and location in {
        "$/osy-casename",
        "$/osy-date",
        "$/osy-desc",
    }:
        return True
    if filename == "RYC.json" and "SAD/SC_0" in location:
        return any(
            f"CommId={comm_id}" in location
            for comm_id in (build.CAP_SERVICE, build.AQ_SERVICE, build.POST_SERVICE)
        )
    return False


def compare_old(filename: str, old: Any, new: Any, location: str, failures: list[Any]) -> None:
    if isinstance(old, dict):
        if not isinstance(new, dict):
            failures.append({"location": location, "before": old, "after": new})
            return
        for key, value in old.items():
            if key not in new:
                failures.append({"location": f"{location}/{key}", "after": "missing"})
            else:
                compare_old(filename, value, new[key], f"{location}/{key}", failures)
        return
    if isinstance(old, list):
        if not isinstance(new, list):
            failures.append({"location": location, "before": old, "after": new})
            return
        identities = [
            field
            for field in IDENTITY_FIELDS
            if old and all(isinstance(item, dict) and field in item for item in old)
        ]
        if identities:
            for item in old:
                matches = [
                    candidate
                    for candidate in new
                    if isinstance(candidate, dict)
                    and all(candidate.get(field) == item[field] for field in identities)
                ]
                label = ",".join(f"{field}={item[field]}" for field in identities)
                if len(matches) != 1:
                    failures.append({"location": f"{location}{{{label}}}", "matches": len(matches)})
                else:
                    compare_old(
                        filename, item, matches[0], f"{location}{{{label}}}", failures
                    )
        else:
            if len(new) < len(old):
                failures.append(
                    {"location": location, "before_length": len(old), "after_length": len(new)}
                )
            for index, item in enumerate(old):
                compare_old(filename, item, new[index], f"{location}[{index}]", failures)
        return
    if old != new and not allowed_existing_change(filename, location):
        failures.append({"location": location, "before": old, "after": new})


def value_for_ratio(
    parameter: str, tech_id: str, comm_id: str, mode: int, series: dict[str, Any]
) -> float:
    intensity = series["service_intensity"]
    inputs = {
        "TEC_fsh_cap_harv": {build.CAP_SERVICE: intensity["capture_pj_per_mt"]},
        "TEC_fsh_aq_harv": {build.AQ_SERVICE: intensity["aquaculture_pj_per_mt"]},
        "TEC_fsh_post_prc": {
            build.RAW_FISH: intensity["raw_mt_per_food_mt"],
            build.POST_SERVICE: intensity["post_pj_per_mt"],
        },
        "TEC_imp_fsh_food": {},
    }
    if mode != 1:
        return 0.0
    if parameter == "IAR":
        return inputs[tech_id].get(comm_id, 0.0)
    return 1.0 if comm_id == build.TECHNOLOGIES[tech_id]["output"] else 0.0


def validate(
    candidate: Path, generated: Path | None, control: Path | None = None
) -> dict[str, Any]:
    failures: list[Any] = []
    checks = 0
    input_data = read(build.DATA_PATH)
    expected = build.build_series(input_data)
    import_cost = float(input_data["model_policy"]["import_variable_cost"])
    accounting_capacity_cost = float(
        input_data["model_policy"]["accounting_capacity_regularization_cost"]
    )
    source_gen = read(SOURCE / "genData.json")
    gen = read(candidate / "genData.json")
    checks += 1
    if gen["osy-casename"] != "Fiji_v2.9":
        failures.append("wrong case identity")
    old_tech_ids = {row["TechId"] for row in source_gen["osy-tech"]}
    old_comm_ids = {row["CommId"] for row in source_gen["osy-comm"]}
    new_techs = {row["TechId"]: row for row in gen["osy-tech"] if row["TechId"] not in old_tech_ids}
    new_comms = {row["CommId"]: row for row in gen["osy-comm"] if row["CommId"] not in old_comm_ids}
    checks += 2
    if set(new_techs) != set(build.TECHNOLOGIES):
        failures.append({"new_technology_ids": sorted(new_techs)})
    if set(new_comms) != set(build.COMMODITIES):
        failures.append({"new_commodity_ids": sorted(new_comms)})
    for comm_id, spec in build.COMMODITIES.items():
        checks += 2
        if new_comms[comm_id]["Comm"] != spec["name"]:
            failures.append(f"wrong name for {comm_id}")
        if new_comms[comm_id]["UnitId"] != "Mt":
            failures.append(f"wrong unit for {comm_id}")
    for tech_id, spec in build.TECHNOLOGIES.items():
        checks += 4
        row = new_techs[tech_id]
        if row["Tech"] != spec["name"]:
            failures.append(f"wrong name for {tech_id}")
        if row["IAR"] != spec["inputs"] or row["OAR"] != [spec["output"]]:
            failures.append(f"wrong structural ratios for {tech_id}")
        if row["CapUnitId"] != "Mt/year" or row["ActUnitId"] != "Mt":
            failures.append(f"wrong activity/capacity unit for {tech_id}")
        if row["TG"] != [build.FISHERIES_GROUP]:
            failures.append(f"wrong technology group for {tech_id}")

    ryc = read(candidate / "RYC.json")
    ryt = read(candidate / "RYT.json")
    ratios = read(candidate / "RYTCM.json")
    modes = read(candidate / "RYTM.json")
    cf = read(candidate / "RYTTs.json")
    regional = read(candidate / "RT.json")
    year_split = read(candidate / "RYTs.json")["YS"][SCENARIO]
    for year in YEARS:
        checks += 1
        if not math.isclose(
            sum(float(row[year]) for row in year_split), 1.0, abs_tol=1e-12
        ):
            failures.append(f"year splits do not sum to one in {year}")

    for comm_id in (build.CAP_SERVICE, build.AQ_SERVICE, build.POST_SERVICE, build.RAW_FISH):
        aad = row_for(ryc, "AAD", CommId=comm_id)
        sad = row_for(ryc, "SAD", CommId=comm_id)
        for year in YEARS:
            checks += 2
            if float(aad[year]) != 0.0 or float(sad[year]) != 0.0:
                failures.append(f"intermediate commodity retains demand: {comm_id}/{year}")
    food_aad = row_for(ryc, "AAD", CommId=build.FOOD_FISH)
    food_sad = row_for(ryc, "SAD", CommId=build.FOOD_FISH)
    for year in YEARS:
        checks += 4
        if not math.isclose(
            float(food_aad[year]), expected["final_demand_mt"][year], abs_tol=1e-12
        ):
            failures.append(f"FSHFOOD AAD mismatch in {year}")
        if float(food_sad[year]) != 0.0:
            failures.append(f"FSHFOOD SAD must be zero in {year}")
        if not math.isclose(
            expected["final_demand_mt"][year],
            expected["domestic_food_mt"][year] + expected["export_demand_mt"][year],
            abs_tol=1e-12,
        ):
            failures.append(f"resident plus export identity fails in {year}")
        if expected["minimum_import_mt"][year] >= expected["final_demand_mt"][year]:
            failures.append(f"import floor eliminates domestic supply in {year}")

    for tech_id in build.TECHNOLOGIES:
        tal = row_for(ryt, "TAL", TechId=tech_id)
        tau = row_for(ryt, "TAU", TechId=tech_id)
        af = row_for(ryt, "AF", TechId=tech_id)
        max_ci = row_for(ryt, "TAMaxCI", TechId=tech_id)
        for year in YEARS:
            wanted_tal = (
                expected["minimum_import_mt"][year]
                if tech_id == "TEC_imp_fsh_food"
                else 0.0
            )
            wanted_tau_series = expected["annual_activity_upper_mt"].get(tech_id)
            wanted_tau = wanted_tau_series[year] if wanted_tau_series else 999999.0
            checks += 8
            if not math.isclose(float(tal[year]), wanted_tal, abs_tol=1e-12):
                failures.append(f"TAL mismatch {tech_id}/{year}")
            if not math.isclose(float(tau[year]), wanted_tau, abs_tol=1e-12):
                failures.append(f"TAU mismatch {tech_id}/{year}")
            if float(af[year]) != 1.0:
                failures.append(f"activity envelope mismatch {tech_id}/{year}")
            # Deterministic all-import feasibility witness. It is not the expected
            # economic dispatch; it proves that no commodity contradiction exists.
            activity = expected["final_demand_mt"][year] if tech_id == "TEC_imp_fsh_food" else 0.0
            if not (float(tal[year]) <= activity <= float(tau[year])):
                failures.append(f"all-import witness violates activity bound {tech_id}/{year}")
            annual = sum(activity * float(row[year]) for row in year_split)
            if not math.isclose(annual, activity, abs_tol=1e-12):
                failures.append(f"timeslice witness fails {tech_id}/{year}")
            if activity > float(max_ci[year]):
                failures.append(f"one-year capacity witness exceeds bound {tech_id}/{year}")
            if float(row_for(ryt, "RC", TechId=tech_id)[year]) != 0.0:
                failures.append(f"new accounting technology has residual stock {tech_id}/{year}")
            if not math.isclose(
                float(row_for(ryt, "CC", TechId=tech_id)[year]),
                accounting_capacity_cost,
                abs_tol=1e-15,
            ):
                failures.append(
                    f"accounting-capacity regularization mismatch {tech_id}/{year}"
                )
        for parameter in ("IAR", "OAR"):
            rows = [row for row in ratios[parameter][SCENARIO] if row.get("TechId") == tech_id]
            for row in rows:
                wanted = value_for_ratio(parameter, tech_id, row["CommId"], row["MoId"], expected)
                for year in YEARS:
                    checks += 1
                    if not math.isclose(float(row[year]), wanted, abs_tol=1e-12):
                        failures.append(
                            f"{parameter} mismatch {tech_id}/{row['CommId']}/{row['MoId']}/{year}"
                        )
        nonzero_modes = {
            row["MoId"]
            for parameter in ("IAR", "OAR")
            for row in ratios[parameter][SCENARIO]
            if row.get("TechId") == tech_id
            and any(abs(float(row[year])) > 0 for year in YEARS)
        }
        checks += 1
        if nonzero_modes != {1}:
            failures.append(f"{tech_id} has nonzero ratios outside mode 1: {nonzero_modes}")
        for row in cf["CF"][SCENARIO]:
            if row.get("TechId") == tech_id:
                for year in YEARS:
                    checks += 1
                    if float(row[year]) != 1.0:
                        failures.append(f"CF mismatch {tech_id}/{row['TsId']}/{year}")
        for parameter in ("VC", "TAMUL", "TADML", "TAIML", "TAMLL"):
            for row in modes[parameter][SCENARIO]:
                if row.get("TechId") != tech_id:
                    continue
                wanted = 0.0
                if parameter == "TAMUL":
                    wanted = 99999.0
                elif parameter == "VC" and tech_id == "TEC_imp_fsh_food" and row["MoId"] == 1:
                    wanted = import_cost
                for year in YEARS:
                    checks += 1
                    if float(row[year]) != wanted:
                        failures.append(f"{parameter} mismatch {tech_id}/{row['MoId']}/{year}")
        for parameter, wanted in (("CAU", 1.0), ("OL", 1.0)):
            checks += 1
            if float(regional[parameter][SCENARIO][0][tech_id]) != wanted:
                failures.append(f"RT/{parameter} mismatch {tech_id}")

    # Explicit 2025 mass-balance witness with both domestic subsectors at their
    # activity ceilings and additional imports covering the residual. This is
    # feasible by construction and does not force either domestic activity.
    year = "2025"
    capture = expected["capture_activity_upper_mt"][year]
    aquaculture = expected["aquaculture_activity_upper_mt"][year]
    domestic = capture + aquaculture
    imports = expected["final_demand_mt"][year] - domestic
    witness = {
        "capture_raw_mt": capture,
        "aquaculture_raw_mt": aquaculture,
        "import_food_mt": imports,
        "minimum_import_mt": expected["minimum_import_mt"][year],
        "domestic_raw_mt": domestic,
        "domestic_food_mt": domestic,
        "final_demand_mt": expected["final_demand_mt"][year],
        "capture_service_pj": capture
        * expected["service_intensity"]["capture_pj_per_mt"],
        "aquaculture_service_pj": aquaculture
        * expected["service_intensity"]["aquaculture_pj_per_mt"],
        "post_service_pj": domestic * expected["service_intensity"]["post_pj_per_mt"],
    }
    checks += 5
    if not math.isclose(
        witness["import_food_mt"] + witness["domestic_food_mt"],
        witness["final_demand_mt"],
        abs_tol=1e-12,
    ):
        failures.append("2025 FSHFOOD witness does not balance")
    if not math.isclose(witness["domestic_raw_mt"], witness["domestic_food_mt"], abs_tol=1e-12):
        failures.append("2025 FSHRAW witness does not balance")
    if witness["import_food_mt"] < witness["minimum_import_mt"]:
        failures.append("2025 cap-constrained import witness violates the import floor")
    if not math.isclose(
        witness["capture_raw_mt"], expected["capture_activity_upper_mt"][year], abs_tol=1e-12
    ):
        failures.append("2025 capture witness violates its upper envelope")
    if not math.isclose(
        witness["aquaculture_raw_mt"],
        expected["aquaculture_activity_upper_mt"][year],
        abs_tol=1e-12,
    ):
        failures.append("2025 aquaculture witness violates its upper envelope")

    unexpected: list[Any] = []
    for path in sorted(SOURCE.glob("*.json")):
        compare_old(path.name, read(path), read(candidate / path.name), "$", unexpected)
    checks += 1
    if unexpected:
        failures.append({"unexpected_existing_source_changes": unexpected[:50], "count": len(unexpected)})

    generated_checks: dict[str, Any] = {"status": "not_run"}
    if generated is not None:
        text = generated.read_text(encoding="utf-8")
        missing: list[str] = []
        for spec in build.TECHNOLOGIES.values():
            token = f"set MODEperTECHNOLOGY[{spec['name']}]:= 1;"
            if token not in text:
                missing.append(token)
        for token in (
            "[RE1,FSHCAPHARV,FSHCAPSERV,*,*]",
            "[RE1,FSHAQHARV,FSHAQSERV,*,*]",
            "[RE1,FSHPOSTPRC,FSHRAW,*,*]",
            "[RE1,FSHPOSTPRC,FSHPOSTSERV,*,*]",
            "[RE1,IMPFSHFOOD,FSHFOOD,*,*]",
        ):
            if token not in text:
                missing.append(token)
        generated_checks = {"status": "pass" if not missing else "fail", "missing": missing}
        checks += 9
        failures.extend(missing)

    control_comparison: dict[str, Any] = {"status": "not_run"}
    if control is not None:
        exact_matches: list[str] = []
        for filename in AUTHORITATIVE_FILES:
            before = read(control / filename)
            after = read(candidate / filename)
            if filename == "RYT.json":
                changed_values = 0
                for tech_id, wanted_series in expected["annual_activity_upper_mt"].items():
                    before_row = row_for(before, "TAU", TechId=tech_id)
                    after_row = row_for(after, "TAU", TechId=tech_id)
                    for year in YEARS:
                        checks += 2
                        if float(before_row[year]) != 999999.0:
                            failures.append(f"control TAU is not open: {tech_id}/{year}")
                        if not math.isclose(
                            float(after_row[year]), wanted_series[year], abs_tol=1e-12
                        ):
                            failures.append(f"candidate TAU mismatch: {tech_id}/{year}")
                        if before_row[year] != after_row[year]:
                            changed_values += 1
                        after_row[year] = before_row[year]
                checks += 2
                if changed_values != len(YEARS) * 2:
                    failures.append(
                        f"expected {len(YEARS) * 2} TAU values to change; found {changed_values}"
                    )
                if after != before:
                    failures.append("RYT.json differs outside the two intended TAU rows")
            elif after != before:
                failures.append(f"{filename} differs between control and candidate")
            else:
                exact_matches.append(filename)
        control_comparison = {
            "status": "pass" if not failures else "fail",
            "control": str(control),
            "authoritative_files": list(AUTHORITATIVE_FILES),
            "byte_semantic_matches_except_ryt": exact_matches,
            "intended_ryt_parameter": "TAU",
            "intended_technology_ids": list(expected["annual_activity_upper_mt"]),
            "changed_year_values": len(YEARS) * 2,
        }

    return {
        "status": "pass" if not failures else "fail",
        "candidate": str(candidate),
        "checks": checks,
        "failures": failures,
        "generated": generated_checks,
        "control_comparison": control_comparison,
        "all_import_feasibility_witness": "Open IMPFSHFOOD activity and one-year capacity can meet all FSHFOOD demand in every year; this proves feasibility but is not the expected high-cost dispatch.",
        "cap_constrained_2025_feasibility_witness": witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT)
    parser.add_argument("--generated", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.candidate, args.generated, args.control)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
