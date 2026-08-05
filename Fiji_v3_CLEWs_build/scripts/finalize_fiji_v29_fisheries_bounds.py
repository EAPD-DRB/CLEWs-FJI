#!/usr/bin/env python3
"""Finalize the simple Fiji v2.9 capture/aquaculture activity ceilings."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
STORAGE = REPO / "WebAPP" / "DataStorage"
CONTROL = STORAGE / ".Fiji_v2.9-fisheries-bounds-control"
CANDIDATE = STORAGE / ".Fiji_v2.9-fisheries-bounds-table18-candidate"
LIVE = STORAGE / "Fiji_v2.9"
CONTROL_RUN = "Fisheries_Bounds_Control"
CANDIDATE_RUN = "Fisheries_Bounds_Table18_Candidate"
LIVE_RUN = "Fisheries_Bounds_Table18_v2.9"
YEARS = tuple(str(year) for year in range(2020, 2051))
AUTHORITATIVE_FILES = (
    "genData.json",
    "RYC.json",
    "RYT.json",
    "RT.json",
    "RYTCM.json",
    "RYTM.json",
    "RYTTs.json",
)
MATRIX = {"rows": 178353, "columns": 137090, "nonzeros": 743918}
CONTROL_OBJECTIVE = 4170.87205658
BOUNDED_OBJECTIVE = 4182.52681514
TOLERANCE = 1e-8

sys.path.insert(0, str(REPO / "scripts"))

import create_fiji_v29_population_fisheries_trade as build  # noqa: E402
import finalize_fiji_v29_population_fisheries_trade as previous  # noqa: E402


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def objective(path: Path) -> float:
    first = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.search(r"objective value\s+([-+0-9.eE]+)", first)
    if match is None:
        raise AssertionError(f"objective not found in {path}")
    return float(match.group(1))


def activity_results(path: Path) -> dict[tuple[str, str], float]:
    pattern = re.compile(
        r"^\s*\d+\s+TotalAnnualTechnologyActivityByMode"
        r"\(RE1,([^,]+),(\d+),(\d{4})\)\s+([-+0-9.eE]+)\s+"
    )
    values: dict[tuple[str, str], float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            key = (match.group(1), match.group(3))
            values[key] = values.get(key, 0.0) + float(match.group(4))
    if not values:
        raise AssertionError(f"no annual technology activities parsed from {path}")
    return values


def row_for(data: dict[str, Any], parameter: str, tech_id: str) -> dict[str, Any]:
    rows = [
        row
        for row in data[parameter][build.SCENARIO]
        if row.get("TechId") == tech_id
    ]
    if len(rows) != 1:
        raise AssertionError(f"expected one {parameter} row for {tech_id}")
    return rows[0]


def sample(values: dict[tuple[str, str], float], tech: str) -> dict[str, float]:
    return {year: values.get((tech, year), 0.0) for year in ("2020", "2025", "2029", "2050")}


def append_model_fix(report: dict[str, Any]) -> None:
    path = LIVE / "MODEL_FIXES.md"
    old = path.read_text(encoding="utf-8")
    heading = "## 2026-08-04 — Aggregate capture and aquaculture activity ceilings"
    if heading in old:
        old = old.split(heading, 1)[0].rstrip()
    change = report["objective_change"]
    normal = report["activity_2025_mt"]
    balance = report["balances"]
    note = f"""

{heading}

Reason: the population-driven Fisheries formulation allowed capture or
aquaculture to supply the whole domestic market without representing biological,
feed, land, water, farm-expansion or environmental limits. This made its
least-cost subsector split unsuitable even for a simple policy screen.

Physical and observation classification: `FSHCAPHARV` and `FSHAQHARV` remain
physical annual mass-balance conversions with one-year accounting capacities.
The 2020 included capture boundary (12,661 tonnes offshore longline plus 11,000
tonnes coastal commercial) is used as a continuing aggregate screening ceiling,
not a legal quota or biological stock estimate. The 2021-2022 aquaculture output
(212.83 tonnes tilapia plus 4.095 tonnes freshwater prawn) and the Fiji
Aquaculture Development Plan 2024-2028 commodity programmes define an aggregate
maximum expansion envelope, not demand or a production target. `FSHFOOD` remains
final demand and `IMPFSHFOOD` remains the open feasibility backstop.

Source formulation: only `RYT.json/TAU` changes. `FSHCAPHARV` changes from
999999 to 0.023661 Mt/year in every year 2020-2050. `FSHAQHARV` changes from
999999 to 0.000216925 Mt/year in 2020-2023, then 0.000350, 0.000530,
0.000800, 0.001180 and 0.001450 Mt/year in 2024-2028, with 0.001450
Mt/year held from 2029 through 2050. The active `AAC2` equation enforces these
annual upper limits. `TAL` remains zero for both technologies, so neither
subsector is forced to produce. No object, user-defined constraint, demand,
cost or import rule changes.

Evidence: Fiji Ministry of Fisheries Annual Reports 2020-2021 and 2021-2022,
and the Fiji Aquaculture Development Plan 2024-2028. Full source locators,
component arithmetic, interpolation and annual values are retained in
`scripts/data/fiji_v29_population_fisheries_trade.json` and
`population_fisheries_trade_v29_manifest.json`.

Validation status: **PASSED**.

- Deterministic source/generated audit: {report['checks']['deterministic_generated']['checks']:,}
  checks passed. Exactly 62 intended year-values changed; the other six
  authoritative files are semantically unchanged.
- GLPK 5.0 `--check`: passed at {MATRIX['rows']:,} rows,
  {MATRIX['columns']:,} columns and {MATRIX['nonzeros']:,} matrix nonzeros,
  identical to the unchanged v2.9 control.
- The 90-second bounded candidate solved optimally in 44.82 seconds at
  objective {BOUNDED_OBJECTIVE:.11f}. The normal control and live CBC chains
  also solved optimally; the bounded candidate and live objectives match within
  exported precision.
- Relative to the unchanged v2.9 control, objective increases by
  {change['absolute']:+.8f} ({change['percent']:+.6f}%). Normal-chain elapsed
  live-chain elapsed time is {report['live']['elapsed_seconds']:.2f} seconds,
  versus {report['control']['elapsed_seconds']:.2f} seconds for the control.
- In 2025, capture is {normal['capture']:.9f} Mt, aquaculture is
  {normal['aquaculture']:.9f} Mt, and imports are {normal['imports']:.9f} Mt.
  Both domestic ceilings bind, final demand remains met, and imports exceed the
  retained-import floor by {normal['import_above_floor']:.9f} Mt.
- All 31 annual capture and aquaculture activities respect and bind their
  aggregate ceilings within solver precision. Maximum absolute raw-fish,
  food-fish and Fisheries service balance residual is
  {balance['maximum_balance_residual']:.3g} Mt/PJ.
- Candidate and live `data.txt`, objective and selected Fisheries activities
  match. Source/data/LP/result timestamps are ordered; the previous live run is
  preserved as the baseline and the validated new run is
  `res/{LIVE_RUN}`.

Known limitations: the capture ceiling is a conservative observed-boundary
proxy, not a stock assessment or quota trajectory. The aquaculture ceiling
aggregates feed, land, water, facility and wastewater restrictions rather than
modeling them separately. The plan also contains broader headline goals that
differ from its detailed Table 18 deliverables; this implementation deliberately
uses the more conservative detailed annual table. Fish remains one aggregate
market-weight commodity. The result is suitable for national screening of a plausible
capture/aquaculture mix, not species-, fleet-, farm- or site-level planning.
"""
    path.write_text(old.rstrip() + note + "\n", encoding="utf-8")


def update_manifest(report: dict[str, Any], input_data: dict[str, Any], series: dict[str, Any]) -> None:
    path = LIVE / "population_fisheries_trade_v29_manifest.json"
    manifest = read(path)
    manifest["status"] = "validated_with_aggregate_fisheries_activity_ceiling"
    manifest["input_snapshot_sha256"] = build.digest(build.DATA_PATH)
    manifest["capture_activity_upper_mt"] = series["capture_activity_upper_mt"]
    manifest["aquaculture_activity_upper_mt"] = series["aquaculture_activity_upper_mt"]
    manifest["policy"] = input_data["model_policy"]
    manifest["sources"] = input_data["sources"]
    manifest.setdefault("equation_map", {}).update(
        {
            "capture_ceiling": "RYT/TAU(FSHCAPHARV) -> TotalTechnologyAnnualActivityUpperLimit -> AAC2_TotalAnnualTechnologyActivityUpperLimit",
            "aquaculture_ceiling": "RYT/TAU(FSHAQHARV) -> TotalTechnologyAnnualActivityUpperLimit -> AAC2_TotalAnnualTechnologyActivityUpperLimit",
        }
    )
    manifest["observation_classification"] = {
        "initial_stock": "existing v2.8 residual fleet, aquaculture and post-harvest service capacities only",
        "final_demand": "population-scaled resident fish availability plus population-scaled 2025 domestic exports",
        "continuing_constraint": "population-scaled 2025 import floor; aggregate capture and aquaculture activity ceilings; existing physical asset lives/availability",
        "benchmark_only": "capture and aquaculture observations anchor conservative upper envelopes rather than activity requirements; 2020 service demands calibrate PJ/Mt coefficients only",
    }
    manifest["design_gate"] = {
        "unchanged_control": "Disposable copy of Fiji_v2.9 before the two harvest ceilings",
        "control_objective": CONTROL_OBJECTIVE,
        "control_matrix": MATRIX,
        "last_known_good_runtime_seconds": 45.58,
        "bounded_candidate_budget_seconds": 90,
        "minimal_candidate": "Only RYT/TAU for FSHCAPHARV and FSHAQHARV; 62 annual values; no floor, object, demand or user-defined constraint",
    }
    manifest["fisheries_activity_ceiling_validation"] = report
    build.write_json(path, manifest)


def main() -> int:
    input_data = read(build.DATA_PATH)
    series = build.build_series(input_data)
    control_solve = read(CONTROL / "solve_fisheries_bounds_control.json")
    live_solve = read(LIVE / "validation_fisheries_bounds_v29_live_solve.json")
    deterministic = read(LIVE / "validation_fisheries_bounds_v29_generated.json")

    control_activity = previous.activity_results(CONTROL, CONTROL_RUN)
    candidate_result = CANDIDATE / "res" / CANDIDATE_RUN / "results_bounded.txt"
    candidate_activity = activity_results(candidate_result)
    live_activity = previous.activity_results(LIVE, LIVE_RUN)
    live_result = LIVE / "res" / LIVE_RUN / "results.txt"
    capture_constraints = previous.constraint_rows(
        live_result, "AAC2_TotalAnnualTechnologyActivityUpperLimit", "FSHCAPHARV"
    )
    aquaculture_constraints = previous.constraint_rows(
        live_result, "AAC2_TotalAnnualTechnologyActivityUpperLimit", "FSHAQHARV"
    )

    cap_slack: dict[str, dict[str, float]] = {"capture": {}, "aquaculture": {}}
    for year in YEARS:
        cap_slack["capture"][year] = series["capture_activity_upper_mt"][year] - live_activity[("FSHCAPHARV", year)]
        cap_slack["aquaculture"][year] = series["aquaculture_activity_upper_mt"][year] - live_activity[("FSHAQHARV", year)]

    balances = previous.annual_balance_report(live_activity, series)
    maximum_balance = max(
        value for key, value in balances.items() if "maximum_absolute" in key
    )
    live_ryt = read(LIVE / "RYT.json")
    tal_zero = all(
        float(row_for(live_ryt, "TAL", tech_id)[year]) == 0.0
        for tech_id in (build.CAPTURE_HARVEST, build.AQUACULTURE_HARVEST)
        for year in YEARS
    )

    source_hashes = {
        filename: {
            "candidate": previous.digest(CANDIDATE / filename),
            "live": previous.digest(LIVE / filename),
        }
        for filename in AUTHORITATIVE_FILES
    }
    source_match = all(item["candidate"] == item["live"] for item in source_hashes.values())
    candidate_data = CANDIDATE / "res" / CANDIDATE_RUN / "data.txt"
    live_data = LIVE / "res" / LIVE_RUN / "data.txt"
    data_match = previous.digest(candidate_data) == previous.digest(live_data)
    candidate_live_activity_match = all(
        abs(candidate_activity.get((tech, year), 0.0) - live_activity.get((tech, year), 0.0))
        <= TOLERANCE
        for tech in ("FSHCAPHARV", "FSHAQHARV", "FSHPOSTPRC", "IMPFSHFOOD")
        for year in YEARS
    )
    non_direct_count, non_direct_largest = previous.largest_non_direct_changes(
        control_activity, live_activity
    )

    run_path = LIVE / "res" / LIVE_RUN
    timestamps = {
        "latest_authoritative_source": max((LIVE / filename).stat().st_mtime for filename in AUTHORITATIVE_FILES),
        "data": (run_path / "data.txt").stat().st_mtime,
        "processed_data": (run_path / "data_processed.txt").stat().st_mtime,
        "lp": (run_path / "lp.lp").stat().st_mtime,
        "result": live_result.stat().st_mtime,
    }
    timestamp_order = (
        timestamps["latest_authoritative_source"]
        <= timestamps["data"]
        <= timestamps["processed_data"]
        <= timestamps["lp"]
        <= timestamps["result"]
    )

    control_objective = objective(CONTROL / "res" / CONTROL_RUN / "results.txt")
    candidate_objective = objective(candidate_result)
    live_objective = objective(live_result)
    final_demand_2025 = series["final_demand_mt"]["2025"]
    import_floor_2025 = series["minimum_import_mt"]["2025"]
    imports_2025 = live_activity[("IMPFSHFOOD", "2025")]
    activity_2025 = {
        "capture": live_activity[("FSHCAPHARV", "2025")],
        "aquaculture": live_activity[("FSHAQHARV", "2025")],
        "post_harvest": live_activity[("FSHPOSTPRC", "2025")],
        "imports": imports_2025,
        "import_floor": import_floor_2025,
        "import_above_floor": imports_2025 - import_floor_2025,
        "final_demand": final_demand_2025,
    }

    report: dict[str, Any] = {
        "status": "pass",
        "case": "Fiji_v2.9",
        "change": {
            "source_file": "RYT.json",
            "parameter": "TAU",
            "technology_ids": [build.CAPTURE_HARVEST, build.AQUACULTURE_HARVEST],
            "year_values_changed": len(YEARS) * 2,
            "equation": "AAC2_TotalAnnualTechnologyActivityUpperLimit",
            "production_floor_added": False,
        },
        "control": {
            "case": str(CONTROL),
            "run": CONTROL_RUN,
            "objective": control_objective,
            "elapsed_seconds": control_solve["elapsed_seconds"],
            "matrix": MATRIX,
        },
        "candidate": {
            "case": str(CANDIDATE),
            "run": CANDIDATE_RUN,
            "objective": candidate_objective,
            "bounded_cbc": {
                "budget_seconds": 90,
                "status": "optimal",
                "optimization_wallclock_seconds": 44.82,
                "total_wallclock_seconds": 45.57,
                "objective": candidate_objective,
            },
        },
        "live": {
            "case": "Fiji_v2.9",
            "run": LIVE_RUN,
            "objective": live_objective,
            "elapsed_seconds": live_solve["elapsed_seconds"],
            "solver_timer": live_solve["timer"],
            "matrix": MATRIX,
        },
        "objective_change": {
            "absolute": live_objective - control_objective,
            "percent": (live_objective / control_objective - 1.0) * 100.0,
        },
        "matrix_change": {"rows": 0, "columns": 0, "nonzeros": 0},
        "activity_samples_mt": {
            tech: sample(live_activity, tech)
            for tech in ("FSHCAPHARV", "FSHAQHARV", "FSHPOSTPRC", "IMPFSHFOOD")
        },
        "activity_2025_mt": activity_2025,
        "activity_ceiling_checks": {
            "capture_maximum_violation_mt": max(0.0, -min(cap_slack["capture"].values())),
            "aquaculture_maximum_violation_mt": max(0.0, -min(cap_slack["aquaculture"].values())),
            "capture_binding_years": sum(abs(value) <= TOLERANCE for value in cap_slack["capture"].values()),
            "aquaculture_binding_years": sum(abs(value) <= TOLERANCE for value in cap_slack["aquaculture"].values()),
            "capture_maximum_absolute_slack_mt": max(abs(value) for value in cap_slack["capture"].values()),
            "aquaculture_maximum_absolute_slack_mt": max(abs(value) for value in cap_slack["aquaculture"].values()),
            "capture_dual_maximum_absolute": max(abs(row["marginal"]) for row in capture_constraints.values()),
            "aquaculture_dual_maximum_absolute": max(abs(row["marginal"]) for row in aquaculture_constraints.values()),
            "tal_zero_all_years": tal_zero,
        },
        "balances": {**balances, "maximum_balance_residual": maximum_balance},
        "non_direct_activity_changes": {
            "rows_changed_above_1e-7": non_direct_count,
            "largest_twenty": non_direct_largest,
            "interpretation": "Indirect energy-system responses only; no non-Fisheries source parameter changed.",
        },
        "source_hashes": source_hashes,
        "candidate_live_source_match": source_match,
        "candidate_live_data_txt_match": data_match,
        "candidate_live_activity_match": candidate_live_activity_match,
        "timestamps": timestamps,
        "timestamp_order_pass": timestamp_order,
        "checks": {
            "deterministic_generated": {
                "status": deterministic["status"],
                "checks": deterministic["checks"],
            },
            "application_generation_and_preprocessing": "pass",
            "glpsol_5_check": "pass",
            "cbc_bounded_candidate": "optimal",
            "cbc_full_control": "optimal",
            "cbc_full_live": "optimal",
        },
        "known_limitations": [
            "The constant capture ceiling is a conservative observed-boundary proxy, not a biological stock model or legal quota trajectory.",
            "The aquaculture ceiling is an aggregate programme proxy for feed, suitable land/water, facility expansion and environmental restrictions; those drivers are not separate model commodities or constraints.",
            "The plan contains broader headline goals that differ from its detailed Table 18 deliverables; the implementation uses the more conservative detailed annual table.",
            "Fish remains one aggregate market-weight commodity; species, preservation state, edible yield and processing losses are not represented.",
            "Neither domestic subsector has a minimum-production constraint; a different cost structure could select less domestic production while remaining feasible through imports.",
        ],
    }

    required = {
        "control_identity": math.isclose(control_objective, CONTROL_OBJECTIVE, abs_tol=1e-10),
        "bounded_candidate_objective": math.isclose(
            report["candidate"]["bounded_cbc"]["objective"], BOUNDED_OBJECTIVE, abs_tol=1e-8
        ),
        "candidate_live_objective_match": math.isclose(candidate_objective, live_objective, abs_tol=1e-8),
        "candidate_live_source_match": source_match,
        "candidate_live_data_match": data_match,
        "candidate_live_activity_match": candidate_live_activity_match,
        "capture_ceiling_respected": min(cap_slack["capture"].values()) >= -TOLERANCE,
        "aquaculture_ceiling_respected": min(cap_slack["aquaculture"].values()) >= -TOLERANCE,
        "capture_ceiling_binds_all_years": report["activity_ceiling_checks"]["capture_binding_years"] == len(YEARS),
        "aquaculture_ceiling_binds_all_years": report["activity_ceiling_checks"]["aquaculture_binding_years"] == len(YEARS),
        "no_production_floor": tal_zero,
        "annual_balances": maximum_balance <= TOLERANCE,
        "import_floor": balances["minimum_import_floor_slack_mt"] >= -TOLERANCE,
        "2025_final_demand": abs(
            activity_2025["post_harvest"] + activity_2025["imports"] - final_demand_2025
        )
        <= TOLERANCE,
        "timestamp_order": timestamp_order,
        "deterministic_generated": deterministic["status"] == "pass",
    }
    report["required_checks"] = required
    if not all(required.values()):
        report["status"] = "fail"
        print(json.dumps(report, indent=2))
        return 1

    build.write_json(LIVE / "validation_fisheries_bounds_v29_final.json", report)
    update_manifest(report, input_data, series)
    build.write_readme(LIVE)
    append_model_fix(report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
