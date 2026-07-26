#!/usr/bin/env python3
"""Validate the Fiji raw model, no-forcing status, and provenance ledgers."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "model" / "inputs"
RESULTS = ROOT / "model" / "results"
DIAGNOSTICS = ROOT / "diagnostics"
GWH_PER_PJ = 1_000_000 / 3_600
DATA_SOURCES = ROOT / "data_sources"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write an empty diagnostic: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def value_map(path: Path) -> tuple[dict[tuple[str, ...], float], list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        keys = [column for column in (reader.fieldnames or []) if column != "VALUE"]
        rows = list(reader)
    return (
        {tuple(row[column] for column in keys): float(row["VALUE"]) for row in rows},
        keys,
    )


checks: list[dict[str, object]] = []


def add_check(
    category: str,
    check: str,
    passed: bool,
    finding: str,
    evidence: str,
) -> None:
    checks.append(
        {
            "Category": category,
            "Check": check,
            "Status": "PASS" if passed else "FAIL",
            "Finding": finding,
            "Evidence": evidence,
        }
    )


# Solver completion and model dimensions
solution_lines = (ROOT / "model" / "data.sol").read_text(
    encoding="utf-8", errors="replace"
).splitlines()
solution_status = solution_lines[0] if solution_lines else ""
solver_metadata = (ROOT / "model" / "solver_status.txt").read_text(encoding="utf-8")
add_check(
    "Solver",
    "Raw model has an optimal solution",
    solution_status.startswith("Optimal") and "Status: Optimal" in solver_metadata,
    solution_status or "No solution status",
    "model/data.sol; model/solver_status.txt",
)
add_check(
    "Solver",
    "Solver metadata declares no historical forcing",
    "Historical forcing added: No" in solver_metadata,
    "Historical forcing added: No"
    if "Historical forcing added: No" in solver_metadata
    else "Declaration absent",
    "model/solver_status.txt",
)

# Core model structure
years = sorted(int(float(row["VALUE"])) for row in read_rows(INPUTS / "YEAR.csv"))
add_check(
    "Structure",
    "Model horizon is continuous from 2021 through 2050",
    years == list(range(2021, 2051)),
    f"{years[0]}-{years[-1]} ({len(years)} years)" if years else "No years",
    "model/inputs/YEAR.csv",
)

required_results = [
    "AnnualEmissions.csv",
    "ProductionByTechnologyAnnual.csv",
    "TotalCapacityAnnual.csv",
    "TotalTechnologyAnnualActivity.csv",
]
missing_results = [name for name in required_results if not (RESULTS / name).is_file()]
add_check(
    "Results",
    "Required raw result tables are present",
    not missing_results,
    "All present" if not missing_results else f"Missing: {', '.join(missing_results)}",
    "model/results",
)

# Duplicate OSeMOSYS input indices
duplicate_count = 0
input_row_count = 0
input_files = sorted(INPUTS.glob("*.csv"))
for csv_path in input_files:
    rows = read_rows(csv_path)
    input_row_count += len(rows)
    if not rows:
        continue
    key_columns = [column for column in rows[0] if column != "VALUE"] or list(rows[0])
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(row[column] for column in key_columns)
        if key in seen:
            duplicate_count += 1
        seen.add(key)
add_check(
    "Integrity",
    "OSeMOSYS inputs have unique parameter indices",
    duplicate_count == 0,
    f"{duplicate_count} duplicate rows across {input_row_count} data rows",
    f"{len(input_files)} CSV files in model/inputs",
)

# Equality constraints are the mechanism previously used to force historical results.
limit_pairs = [
    (
        "TotalTechnologyAnnualActivityLowerLimit.csv",
        "TotalTechnologyAnnualActivityUpperLimit.csv",
    ),
    (
        "TechnologyActivityByModeLowerLimit.csv",
        "TechnologyActivityByModeUpperLimit.csv",
    ),
    ("TotalAnnualMinCapacity.csv", "TotalAnnualMaxCapacity.csv"),
    (
        "TotalAnnualMinCapacityInvestment.csv",
        "TotalAnnualMaxCapacityInvestment.csv",
    ),
]
positive_equality_locks: list[dict[str, object]] = []
for lower_name, upper_name in limit_pairs:
    lower, lower_keys = value_map(INPUTS / lower_name)
    upper, upper_keys = value_map(INPUTS / upper_name)
    if lower_keys != upper_keys:
        positive_equality_locks.append(
            {
                "parameter_pair": f"{lower_name} / {upper_name}",
                "index": "SCHEMA_MISMATCH",
                "value": "",
            }
        )
        continue
    for key, lower_value in lower.items():
        upper_value = upper.get(key)
        if (
            upper_value is not None
            and lower_value > 0
            and math.isclose(lower_value, upper_value, rel_tol=0, abs_tol=1e-12)
        ):
            positive_equality_locks.append(
                {
                    "parameter_pair": f"{lower_name} / {upper_name}",
                    "index": " | ".join(key),
                    "value": lower_value,
                }
            )
add_check(
    "No forcing",
    "No positive lower-equals-upper activity or capacity locks",
    not positive_equality_locks,
    f"{len(positive_equality_locks)} positive equality locks",
    "Four activity/capacity lower-upper parameter pairs",
)

# Reject the result-fitting configuration and source hooks removed from this version.
forbidden_keys = [
    "crop_yield_factors",
    "historical_availability_factors",
    "historical_generation_shares",
    "power_capacity_calibration",
    "power_capacity_calibration_gw",
]
config_paths = [ROOT / "config" / "config.yaml", ROOT / "overrides" / "config.yaml"]
config_hits: list[str] = []
for config_path in config_paths:
    config_text = config_path.read_text(encoding="utf-8")
    for key in forbidden_keys:
        if re.search(rf"(?m)^{re.escape(key)}\s*:", config_text):
            config_hits.append(f"{config_path.relative_to(ROOT)}:{key}")
source_path = ROOT / "overrides" / "workflow" / "scripts" / "clewsy.py"
source_text = source_path.read_text(encoding="utf-8")
source_hits = [
    token
    for token in [*forbidden_keys, "calibrate_power_system"]
    if token in source_text
]
add_check(
    "No forcing",
    "Calibration hooks are absent from configuration and generator source",
    not config_hits and not source_hits,
    (
        "No calibration hooks"
        if not config_hits and not source_hits
        else f"Found: {', '.join(config_hits + source_hits)}"
    ),
    "config/config.yaml; overrides/config.yaml; overrides/workflow/scripts/clewsy.py",
)

# Structural country adaptation retained: the model domain represents Fiji's land area.
land_rows = read_rows(ROOT / "geospatial" / "FJI_land_cells_with_attributes.csv")
land_area = sum(float(row["sqkm"]) for row in land_rows)
add_check(
    "Country adaptation",
    "Fiji land-cell area is preserved",
    math.isclose(land_area, 18_273.0, rel_tol=0, abs_tol=1.0),
    f"{land_area:.3f} km2",
    "geospatial/FJI_land_cells_with_attributes.csv",
)

# Philippines-v12-style provenance structure
required_tracking_files = [
    ROOT / "documentation" / "CURRENT_MODEL.md",
    ROOT / "documentation" / "MODEL_STRUCTURE.md",
    ROOT / "documentation" / "KNOWN_LIMITATIONS.md",
    ROOT / "documentation" / "CALIBRATION_PROTOCOL.md",
    ROOT / "documentation" / "HISTORY.md",
    DATA_SOURCES / "DATA_SOURCES.md",
    DATA_SOURCES / "ASSUMPTIONS.csv",
    DATA_SOURCES / "CALCULATIONS.csv",
    DATA_SOURCES / "MODEL_DATA_MAP.csv",
    ROOT / "config" / "upstream_versions.json",
    ROOT.parent / "WebAPP" / "DataStorage" / "Fiji_CLEWs_Global" / "README.md",
    ROOT.parent
    / "WebAPP"
    / "DataStorage"
    / "Fiji_CLEWs_Global"
    / "documentation"
    / "README.md",
]
missing_tracking_files = [
    str(path.relative_to(ROOT.parent))
    for path in required_tracking_files
    if not path.is_file()
]
add_check(
    "Provenance",
    "Required current documentation and provenance ledgers are present",
    not missing_tracking_files,
    (
        "All present"
        if not missing_tracking_files
        else f"Missing: {', '.join(missing_tracking_files)}"
    ),
    "documentation; data_sources; config/upstream_versions.json; active case README",
)

source_text = (DATA_SOURCES / "DATA_SOURCES.md").read_text(encoding="utf-8")
source_ids = set(re.findall(r"`(DS-[A-Z0-9.-]+)`", source_text))
assumption_rows = read_rows(DATA_SOURCES / "ASSUMPTIONS.csv")
calculation_rows = read_rows(DATA_SOURCES / "CALCULATIONS.csv")
map_rows = read_rows(DATA_SOURCES / "MODEL_DATA_MAP.csv")


def id_values(rows: list[dict[str, str]], column: str) -> list[str]:
    return [row[column].strip() for row in rows if row[column].strip()]


def split_ids(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


assumption_id_values = id_values(assumption_rows, "assumption_id")
calculation_id_values = id_values(calculation_rows, "calculation_id")
map_id_values = id_values(map_rows, "map_id")
assumption_ids = set(assumption_id_values)
calculation_ids = set(calculation_id_values)
unique_ledger_ids = (
    len(assumption_ids) == len(assumption_id_values)
    and len(calculation_ids) == len(calculation_id_values)
    and len(set(map_id_values)) == len(map_id_values)
)
add_check(
    "Provenance",
    "Source, assumption, calculation, and map identifiers are unique",
    unique_ledger_ids,
    (
        f"{len(source_ids)} sources; {len(assumption_ids)} assumptions; "
        f"{len(calculation_ids)} calculations; {len(map_id_values)} map rows"
    ),
    "data_sources/",
)

unresolved_references: set[str] = set()
for row in calculation_rows:
    unresolved_references.update(
        source_id
        for source_id in split_ids(row["source_ids"])
        if source_id not in source_ids
    )
    unresolved_references.update(
        assumption_id
        for assumption_id in split_ids(row["assumption_ids"])
        if assumption_id not in assumption_ids
    )
for row in map_rows:
    unresolved_references.update(
        source_id
        for source_id in split_ids(row["source_ids"])
        if source_id not in source_ids
    )
    unresolved_references.update(
        assumption_id
        for assumption_id in split_ids(row["assumption_ids"])
        if assumption_id not in assumption_ids
    )
    unresolved_references.update(
        calculation_id
        for calculation_id in split_ids(row["calculation_ids"])
        if calculation_id not in calculation_ids
    )
add_check(
    "Provenance",
    "All ledger cross-references resolve",
    not unresolved_references,
    (
        "All references resolve"
        if not unresolved_references
        else f"Unresolved: {', '.join(sorted(unresolved_references))}"
    ),
    "data_sources/ASSUMPTIONS.csv; CALCULATIONS.csv; MODEL_DATA_MAP.csv",
)

upstream_versions = json.loads(
    (ROOT / "config" / "upstream_versions.json").read_text(encoding="utf-8")
)
pinned_commits = [
    upstream_versions["workflow"]["commit"],
    *(
        record["commit"]
        for record in upstream_versions["submodules"].values()
    ),
]
baseline_backups = sorted((ROOT / "backups").glob("*_pre_tracking_2026-07-25.zip"))
add_check(
    "Reproducibility",
    "Upstream revisions and immutable pre-tracking backups are retained",
    all(re.fullmatch(r"[0-9a-f]{40}", commit) for commit in pinned_commits)
    and len(baseline_backups) == 2
    and all(path.stat().st_size > 0 for path in baseline_backups),
    f"{len(pinned_commits)} pinned commits; {len(baseline_backups)} baseline archives",
    "config/upstream_versions.json; backups/",
)

# Historical values are comparison data only. Failing to match them is not a QA failure.
capacity_targets = {
    "PWRHYDFJIXX01": ("Hydropower", 133.4),
    "PWROILFJIXX01": ("Oil-fired thermal", 182.0),
    "PWRWONFJIXX01": ("Wind", 9.8),
    "PWRBIOFJIXX01": ("Biomass", 34.0),
}
generation_targets = {
    "PWRHYDFJIXX01": ("Hydropower", 544.0),
    "PWROILFJIXX01": ("Oil-fired thermal", 327.0),
    "PWRWONFJIXX01": ("Wind", 0.2),
    "PWRBIOFJIXX01": ("Biomass", 61.0),
}
crop_targets = {
    "LNDSGCHRTOT": ("Sugar cane", 380.0),
    "LNDCONHRTOT": ("Coconut", 54.2),
    "LNDYAMHRTOT": ("Taro/yam/root proxy", 43.46),
    "LNDCASHRTOT": ("Cassava", 35.95),
    "LNDOTHHRTOT": ("Other crops aggregate", 116.76),
}

capacity_rows = read_rows(RESULTS / "TotalCapacityAnnual.csv")
capacity_2021 = {
    row["TECHNOLOGY"]: float(row["VALUE"]) * 1000
    for row in capacity_rows
    if int(float(row["YEAR"])) == 2021
}
production_rows = read_rows(RESULTS / "ProductionByTechnologyAnnual.csv")
generation = {
    (row["TECHNOLOGY"], int(float(row["YEAR"]))): (
        float(row["VALUE"]) * GWH_PER_PJ
    )
    for row in production_rows
    if row["FUEL"] == "ELCFJIXX01"
}
activity_rows = read_rows(RESULTS / "TotalTechnologyAnnualActivity.csv")
activity_2021 = {
    row["TECHNOLOGY"]: float(row["VALUE"]) * 1000
    for row in activity_rows
    if int(float(row["YEAR"])) == 2021
}

comparisons: list[dict[str, object]] = []


def add_comparison(
    system: str,
    metric: str,
    label: str,
    technology: str,
    historical_year: int,
    model_year: int,
    observed: float,
    modelled: float,
    unit: str,
    source: str,
) -> None:
    gap_percent = 100 * (modelled - observed) / observed
    comparisons.append(
        {
            "System": system,
            "Metric": metric,
            "Technology_or_crop": label,
            "Model_technology": technology,
            "Historical_year": historical_year,
            "Model_year": model_year,
            "Observed": f"{observed:.9g}",
            "Modelled": f"{modelled:.9g}",
            "Unit": unit,
            "Gap_percent": f"{gap_percent:.6f}",
            "Applied_in_raw_model": "False",
            "Interpretation": "Diagnostic only; not fitted",
            "Source": source,
        }
    )


for technology, (label, observed) in capacity_targets.items():
    add_comparison(
        "Electricity",
        "Installed capacity",
        label,
        technology,
        2021,
        2021,
        observed,
        capacity_2021.get(technology, 0.0),
        "MW",
        "Fiji REI Investment Plan",
    )
for technology, (label, observed) in generation_targets.items():
    add_comparison(
        "Electricity",
        "Generation",
        label,
        technology,
        2021,
        2021,
        observed,
        generation.get((technology, 2021), 0.0),
        "GWh",
        "Fiji REI Investment Plan",
    )
for technology, (label, observed) in crop_targets.items():
    add_comparison(
        "Agriculture",
        "Harvested area",
        label,
        technology,
        2020,
        2021,
        observed,
        activity_2021.get(technology, 0.0),
        "km2",
        "FAOSTAT",
    )

trajectory: list[dict[str, object]] = []
for year in range(2021, 2026):
    for technology, (label, _) in generation_targets.items():
        trajectory.append(
            {
                "Year": year,
                "Technology": technology,
                "Label": label,
                "Raw_generation_GWh": f"{generation.get((technology, year), 0.0):.9g}",
                "Historical_constraint_applied": "False",
            }
        )

DIAGNOSTICS.mkdir(exist_ok=True)
write_rows(DIAGNOSTICS / "technical_qa.csv", checks)
write_rows(DIAGNOSTICS / "raw_vs_history.csv", comparisons)
write_rows(
    DIAGNOSTICS / "raw_electricity_trajectory_2021_2025.csv",
    trajectory,
)

audit = {
    "model": "Fiji CLEWs Global raw uncalibrated model",
    "historical_forcing_added": False,
    "status": "PASS" if all(row["Status"] == "PASS" for row in checks) else "FAIL",
    "checks_passed": sum(row["Status"] == "PASS" for row in checks),
    "checks_total": len(checks),
    "positive_equality_locks": positive_equality_locks,
    "calibration_config_hits": config_hits,
    "calibration_source_hits": source_hits,
    "historical_comparison_is_diagnostic_only": True,
}
with (DIAGNOSTICS / "no_forcing_audit.json").open("w", encoding="utf-8") as handle:
    json.dump(audit, handle, indent=2)
    handle.write("\n")

validation_summary = {
    "model": "Fiji CLEWs Global raw uncalibrated model",
    "generated": "2026-07-25",
    "status": audit["status"],
    "checks_passed": audit["checks_passed"],
    "checks_total": audit["checks_total"],
    "numerical_model_inputs_changed_by_tracking_reorganization": False,
    "historical_forcing_added": False,
    "provenance_structure": "Philippines v12 convention",
    "technical_report": "diagnostics/technical_qa.csv",
}
with (DIAGNOSTICS / "validation_summary.json").open(
    "w", encoding="utf-8"
) as handle:
    json.dump(validation_summary, handle, indent=2)
    handle.write("\n")

failed = [row for row in checks if row["Status"] == "FAIL"]
print(
    f"{len(checks) - len(failed)}/{len(checks)} "
    "technical/no-forcing/provenance checks passed."
)
print(f"Detailed report: {DIAGNOSTICS / 'technical_qa.csv'}")
print(f"Historical comparison: {DIAGNOSTICS / 'raw_vs_history.csv'}")
if failed:
    for row in failed:
        print(f"FAIL: {row['Category']} — {row['Check']}", file=sys.stderr)
    sys.exit(1)
