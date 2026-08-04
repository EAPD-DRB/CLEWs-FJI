#!/usr/bin/env python3
"""Deterministically validate Fiji_v2.7 Fisheries source design before solving."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
STORAGE = REPO / "WebAPP" / "DataStorage"
SOURCE = STORAGE / "Fiji_v2.6"
DEFAULT_CANDIDATE = STORAGE / ".Fiji_v2.7-fisheries-candidate"
SCENARIO = "SC_0"
YEARS = [str(year) for year in range(2020, 2051)]
TECHS = {
    "TEC_fsh_cap_dsl",
    "TEC_fsh_cap_ele",
    "TEC_fsh_aq_dsl",
    "TEC_fsh_aq_ele",
    "TEC_fsh_post_dsl",
    "TEC_fsh_post_ele",
    "TEC_fsh_post_sol",
}
SERVICES = {
    "COM_fsh_cap": {
        "technologies": ["TEC_fsh_cap_dsl", "TEC_fsh_cap_ele"],
        "replacement": "TEC_fsh_cap_ele",
    },
    "COM_fsh_aq": {
        "technologies": ["TEC_fsh_aq_dsl", "TEC_fsh_aq_ele"],
        "replacement": "TEC_fsh_aq_ele",
    },
    "COM_fsh_post": {
        "technologies": [
            "TEC_fsh_post_dsl",
            "TEC_fsh_post_ele",
            "TEC_fsh_post_sol",
        ],
        "replacement": "TEC_fsh_post_ele",
    },
}
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
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def row_for(data: dict[str, Any], parameter: str, **identity: Any) -> dict[str, Any]:
    rows = data[parameter][SCENARIO]
    matches = [
        row for row in rows if all(row.get(field) == value for field, value in identity.items())
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
    if filename == "RYC.json" and any(
        marker in location
        for marker in (
            "SAD/SC_0{CommId=COM_x6kh9}",
            "SAD/SC_0{CommId=COM_sb105}",
            "SAD/SC_0{CommId=COM_9ek33}",
            "SAD/SC_0{CommId=COM_3drm3}",
            "SAD/SC_0{CommId=COM_mmv3k}",
        )
    ):
        return True
    if filename == "RYT.json" and any(
        marker in location
        for marker in (
            "TAL/SC_0{TechId=TEC_s2z92}",
            "TAU/SC_0{TechId=TEC_s2z92}",
            "TAL/SC_0{TechId=TEC_tfgsb}",
            "TAU/SC_0{TechId=TEC_tfgsb}",
        )
    ):
        year = location.rsplit("/", 1)[-1]
        return year in {"2020", "2021", "2022", "2023"}
    return False


def compare_existing(
    filename: str,
    old: Any,
    new: Any,
    location: str,
    unexpected: list[dict[str, Any]],
) -> None:
    if isinstance(old, dict):
        if not isinstance(new, dict):
            unexpected.append({"location": location, "before": old, "after": new})
            return
        for key, value in old.items():
            if key not in new:
                unexpected.append({"location": f"{location}/{key}", "before": value, "after": "<missing>"})
            else:
                compare_existing(filename, value, new[key], f"{location}/{key}", unexpected)
        return
    if isinstance(old, list):
        if not isinstance(new, list):
            unexpected.append({"location": location, "before": old, "after": new})
            return
        identities = [
            field
            for field in IDENTITY_FIELDS
            if old and all(isinstance(item, dict) and field in item for item in old)
        ]
        if identities:
            for old_item in old:
                identity = tuple((field, old_item[field]) for field in identities)
                matches = [
                    item
                    for item in new
                    if isinstance(item, dict)
                    and all(item.get(field) == value for field, value in identity)
                ]
                label = ",".join(f"{field}={value}" for field, value in identity)
                if len(matches) != 1:
                    unexpected.append(
                        {"location": f"{location}{{{label}}}", "before": old_item, "after": f"matches={len(matches)}"}
                    )
                else:
                    compare_existing(
                        filename, old_item, matches[0], f"{location}{{{label}}}", unexpected
                    )
        else:
            if len(new) < len(old):
                unexpected.append({"location": location, "before": len(old), "after": len(new)})
            for index, value in enumerate(old):
                compare_existing(filename, value, new[index], f"{location}[{index}]", unexpected)
        return
    if old != new and not allowed_existing_change(filename, location):
        unexpected.append({"location": location, "before": old, "after": new})


def boundary_checks(candidate: Path) -> dict[str, Any]:
    source_ryc = read_json(SOURCE / "RYC.json")
    candidate_ryc = read_json(candidate / "RYC.json")
    source_ryt = read_json(SOURCE / "RYT.json")
    candidate_ryt = read_json(candidate / "RYT.json")
    checks: list[dict[str, Any]] = []
    fixed = {
        "COM_x6kh9": 0.027923555,
        "COM_sb105": 0.004051114848,
        "COM_9ek33": 0.02025557424,
    }
    for commodity, expected in fixed.items():
        old = row_for(source_ryc, "SAD", CommId=commodity)
        new = row_for(candidate_ryc, "SAD", CommId=commodity)
        for year in YEARS:
            actual = float(old[year]) - float(new[year])
            checks.append(
                {
                    "flow": commodity,
                    "year": year,
                    "expected_removed": expected,
                    "actual_removed": actual,
                    "pass": math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12),
                }
            )
    old_grid = row_for(source_ryc, "SAD", CommId="COM_3drm3")
    new_grid = row_for(candidate_ryc, "SAD", CommId="COM_3drm3")
    for year in YEARS:
        expected = 0.000007789284 * (1.05 ** (int(year) - 2020))
        actual = float(old_grid[year]) - float(new_grid[year])
        checks.append(
            {
                "flow": "COM_3drm3",
                "year": year,
                "expected_removed": expected,
                "actual_removed": actual,
                "pass": math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12),
            }
        )
    old_water = row_for(source_ryc, "SAD", CommId="COM_mmv3k")
    new_water = row_for(candidate_ryc, "SAD", CommId="COM_mmv3k")
    for year in YEARS:
        expected = 0.00006026636 if int(year) <= 2024 else 0.0
        actual = float(old_water[year]) - float(new_water[year])
        checks.append(
            {
                "flow": "COM_mmv3k",
                "year": year,
                "expected_removed": expected,
                "actual_removed": actual,
                "pass": math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12),
            }
        )
    for tech_id, expected in (("TEC_s2z92", 0.11169422), ("TEC_tfgsb", 0.00506389356)):
        for parameter in ("TAL", "TAU"):
            old = row_for(source_ryt, parameter, TechId=tech_id)
            new = row_for(candidate_ryt, parameter, TechId=tech_id)
            for year in ("2020", "2021", "2022", "2023"):
                actual = float(old[year]) - float(new[year])
                checks.append(
                    {
                        "flow": f"{parameter}/{tech_id}",
                        "year": year,
                        "expected_removed": expected,
                        "actual_removed": actual,
                        "pass": math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12),
                    }
                )
    failures = [item for item in checks if not item["pass"]]
    return {"status": "pass" if not failures else "fail", "checks": len(checks), "failures": failures}


def envelope_checks(candidate: Path) -> dict[str, Any]:
    demand = read_json(candidate / "RYC.json")
    demand_profile = read_json(candidate / "RYCTs.json")
    annual = read_json(candidate / "RYT.json")
    regional = read_json(candidate / "RT.json")
    timeslices = read_json(candidate / "RYTTs.json")
    gen = read_json(candidate / "genData.json")
    ts_ids = [row["TsId"] for row in gen["osy-ts"]]
    cau = regional["CAU"][SCENARIO][0]
    life = regional["OL"][SCENARIO][0]
    records: list[dict[str, Any]] = []
    replacement_plans: dict[str, dict[str, float]] = {}
    for commodity, definition in SERVICES.items():
        sad = row_for(demand, "SAD", CommId=commodity)
        replacement = definition["replacement"]
        replacement_af = row_for(annual, "AF", TechId=replacement)
        investments: dict[str, float] = {}
        replacement_plans[commodity] = investments
        for year in YEARS:
            residual_effective = sum(
                float(row_for(annual, "RC", TechId=tech_id)[year])
                * float(row_for(annual, "AF", TechId=tech_id)[year])
                * float(cau[tech_id])
                for tech_id in definition["technologies"]
            )
            surviving_investment = sum(
                capacity
                for vintage, capacity in investments.items()
                if int(year) - int(vintage) < int(life[replacement])
            )
            replacement_effective = (
                surviving_investment * float(replacement_af[year]) * float(cau[replacement])
            )
            shortfall = max(0.0, float(sad[year]) - residual_effective - replacement_effective)
            if shortfall > 0:
                investments[year] = shortfall / (
                    float(replacement_af[year]) * float(cau[replacement])
                )
                surviving_investment += investments[year]
                replacement_effective += shortfall
            for ts_id in ts_ids:
                profile = row_for(demand_profile, "SDP", CommId=commodity, TsId=ts_id)
                cf = row_for(timeslices, "CF", TechId=replacement, TsId=ts_id)
                required = float(sad[year]) * float(profile[year])
                available = (
                    residual_effective + replacement_effective
                ) * float(cf[year]) * 0.25
                records.append(
                    {
                        "commodity": commodity,
                        "year": year,
                        "timeslice": ts_id,
                        "required_service": required,
                        "available_service": available,
                        "pass": available + 1e-12 >= required,
                    }
                )
    failures = [item for item in records if not item["pass"]]
    initial = [item for item in records if item["year"] == "2020"]
    return {
        "status": "pass" if not failures else "fail",
        "initial_year_status": "pass" if all(item["pass"] for item in initial) else "fail",
        "every_year_timeslice_checks": len(records),
        "replacement_plan": replacement_plans,
        "failures": failures,
    }


def validate(candidate: Path) -> dict[str, Any]:
    errors: list[str] = []
    gen_source = read_json(SOURCE / "genData.json")
    gen = read_json(candidate / "genData.json")
    tech_ids = [row["TechId"] for row in gen["osy-tech"]]
    comm_ids = [row["CommId"] for row in gen["osy-comm"]]
    if len(tech_ids) != len(set(tech_ids)) or len(comm_ids) != len(set(comm_ids)):
        errors.append("duplicate technology or commodity IDs")
    if set(tech_ids) - {row["TechId"] for row in gen_source["osy-tech"]} != TECHS:
        errors.append("new technology set differs from approved seven Fisheries technologies")
    if set(comm_ids) - {row["CommId"] for row in gen_source["osy-comm"]} != set(SERVICES):
        errors.append("new commodity set differs from approved three service commodities")

    annual = read_json(candidate / "RYT.json")
    ratios = read_json(candidate / "RYTCM.json")
    demand_profile = read_json(candidate / "RYCTs.json")
    for tech_id in TECHS:
        for year in YEARS:
            if float(row_for(annual, "TAL", TechId=tech_id)[year]) != 0:
                errors.append(f"positive Fisheries activity minimum {tech_id}/{year}")
            if float(row_for(annual, "TAMinCI", TechId=tech_id)[year]) != 0:
                errors.append(f"positive Fisheries investment minimum {tech_id}/{year}")
            if float(row_for(annual, "TAMaxCI", TechId=tech_id)[year]) < 999999:
                errors.append(f"finite Fisheries investment maximum {tech_id}/{year}")
        nonzero_modes = {
            int(row["MoId"])
            for parameter in ("IAR", "OAR")
            for row in ratios[parameter][SCENARIO]
            if row.get("TechId") == tech_id
            and any(abs(float(row[year])) > 1e-15 for year in YEARS)
        }
        if nonzero_modes != {1}:
            errors.append(f"unexpected active modes for {tech_id}: {sorted(nonzero_modes)}")

    for commodity in SERVICES:
        for year in YEARS:
            profile_sum = sum(
                float(row[year])
                for row in demand_profile["SDP"][SCENARIO]
                if row.get("CommId") == commodity
            )
            if not math.isclose(profile_sum, 1.0, abs_tol=1e-12):
                errors.append(f"demand profile does not sum to one: {commodity}/{year}")

    producers: dict[str, set[str]] = {}
    for tech in gen["osy-tech"]:
        for commodity in tech.get("OAR", []):
            producers.setdefault(commodity, set()).add(tech["TechId"])
    for carrier in ("COM_eev5t", "COM_3drm3", "COM_mmv3k"):
        if not producers.get(carrier):
            errors.append(f"Fisheries input carrier has no structural producer: {carrier}")

    unexpected: list[dict[str, Any]] = []
    for source_path in sorted(SOURCE.glob("*.json")):
        candidate_path = candidate / source_path.name
        if not candidate_path.is_file():
            unexpected.append(
                {"location": source_path.name, "before": "present", "after": "missing"}
            )
            continue
        compare_existing(
            source_path.name,
            read_json(source_path),
            read_json(candidate_path),
            "$",
            unexpected,
        )
    boundary = boundary_checks(candidate)
    envelope = envelope_checks(candidate)
    if unexpected:
        errors.append(f"{len(unexpected)} unexpected inherited source changes")
    if boundary["status"] != "pass":
        errors.append("boundary reconciliation failed")
    if envelope["status"] != "pass":
        errors.append("stock/vintage/service envelope failed")
    return {
        "status": "pass" if not errors else "fail",
        "candidate": str(candidate.resolve()),
        "errors": errors,
        "counts": {
            "technologies_before": len(gen_source["osy-tech"]),
            "technologies_after": len(gen["osy-tech"]),
            "commodities_before": len(gen_source["osy-comm"]),
            "commodities_after": len(gen["osy-comm"]),
        },
        "boundary_reconciliation": boundary,
        "stock_vintage_service_envelope": envelope,
        "unexpected_inherited_changes": unexpected[:100],
        "source_diff_allowlist": {
            "genData.json": "case identity/description plus exactly one group, three commodities and seven technologies",
            "RYC.json": "five aggregate SAD boundaries plus new Fisheries rows",
            "RYT.json": "two aggregate observed-activity boundaries in 2020-2023 plus new Fisheries rows",
            "all_other_source_JSON": "new structural rows/keys only; inherited cells unchanged",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = validate(args.candidate.resolve())
    except Exception as error:
        report = {"status": "fail", "errors": [str(error)]}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
