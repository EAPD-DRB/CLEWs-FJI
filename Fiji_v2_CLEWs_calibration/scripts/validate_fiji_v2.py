#!/usr/bin/env python3
"""Validate Fiji v2's technical integrity, provenance, and declared fit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from manage_reserve_margin_proxy import (
    check_proxy,
    expected_proxy,
    load_case,
    read_json,
    validate_config,
)


REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "Fiji_v2_CLEWs_calibration"
INPUTS = ROOT / "model" / "inputs"
CASE = REPO / "WebAPP" / "DataStorage" / "Fiji_v2"
FIT = ROOT / "diagnostics" / "calibration_runs" / "historical_fit"
OUTPUT = ROOT / "diagnostics" / "calibration_runs" / "validation_summary.json"
EVIDENCE = (
    ROOT
    / "data_sources"
    / "evidence"
    / "calibration"
    / "historical_electricity_2020_2024.csv"
)
REMOVED_UPSTREAM_TECHNOLOGIES = {"PWRTRNA01"}
REMOVED_UPSTREAM_FUELS = {"ELCFJI01", "ELCFJI02"}
REMOVED_OHC_TECHNOLOGIES = {"DEMINDOHC"}
REMOVED_OHC_FUELS = {"INDOHC", "OHC"}
EXPECTED_PHASE1B_TECHNOLOGIES = 131
EXPECTED_PHASE1B_COMMODITIES = 104


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


checks: list[dict[str, Any]] = []


def check(name: str, passed: bool, finding: str, evidence: str) -> None:
    checks.append(
        {
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "finding": finding,
            "evidence": evidence,
        }
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-folder",
        type=Path,
        default=CASE,
        help="Fiji_v2 MUIO case folder (defaults to the colocated MUIOGO case)",
    )
    parser.add_argument("--run", default="Historical_Backcast")
    parser.add_argument(
        "--fit-folder",
        type=Path,
        default=FIT,
        help="folder containing the refreshed historical-fit diagnostics",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="path for the machine-readable validation summary",
    )
    return parser.parse_args()


def value_map(path: Path) -> tuple[list[str], dict[tuple[str, ...], float]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = [field for field in (reader.fieldnames or []) if field != "VALUE"]
        values = {
            tuple(row[field] for field in fields): float(row["VALUE"]) for row in reader
        }
    return fields, values


def main() -> None:
    args = parse_args()
    case = args.case_folder.resolve()
    run = case / "res" / args.run
    fit_folder = args.fit_folder.resolve()
    output = args.output.resolve()
    if not (case / "genData.json").is_file():
        raise FileNotFoundError(f"Not a MUIO case folder: {case}")
    if not run.is_dir():
        raise FileNotFoundError(f"Saved run not found: {run}")

    first_line = (run / "results.txt").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()[0]
    check(
        f"{args.run} solve is optimal",
        first_line.startswith("Optimal"),
        first_line,
        f"WebAPP/DataStorage/Fiji_v2/res/{args.run}/results.txt",
    )

    years = [int(row["VALUE"]) for row in read_rows(INPUTS / "YEAR.csv")]
    gen_data = json.loads((case / "genData.json").read_text(encoding="utf-8"))
    check(
        "CSV and MUIO horizons are identical and continuous",
        years == list(range(2020, 2051))
        and [str(year) for year in years] == gen_data["osy-years"],
        f"{years[0]}-{years[-1]}, {len(years)} years",
        "model/inputs/YEAR.csv; WebAPP/DataStorage/Fiji_v2/genData.json",
    )

    technology_count = len(gen_data["osy-tech"])
    commodity_count = len(gen_data["osy-comm"])
    check(
        "MUIO dimensions match the Phase 1B Fiji structure",
        technology_count == EXPECTED_PHASE1B_TECHNOLOGIES
        and commodity_count == EXPECTED_PHASE1B_COMMODITIES,
        f"{technology_count} technologies; {commodity_count} commodities",
        "WebAPP/DataStorage/Fiji_v2/genData.json",
    )

    branch_references: list[str] = []
    for path in INPUTS.glob("*.csv"):
        for row_number, row in enumerate(read_rows(path), start=2):
            if any(
                value in REMOVED_UPSTREAM_TECHNOLOGIES | REMOVED_UPSTREAM_FUELS
                for value in row.values()
            ):
                branch_references.append(f"{path.name}:{row_number}")
    muiogo_technologies = {item["Tech"] for item in gen_data["osy-tech"]}
    muiogo_fuels = {item["Comm"] for item in gen_data["osy-comm"]}
    branch_references.extend(
        f"genData:{name}"
        for name in sorted(
            (muiogo_technologies & REMOVED_UPSTREAM_TECHNOLOGIES)
            | (muiogo_fuels & REMOVED_UPSTREAM_FUELS)
        )
    )
    check(
        "Malformed land-code electricity branch is absent",
        not branch_references,
        (
            "PWRTRNA01, ELCFJI01, and ELCFJI02 removed"
            if not branch_references
            else "; ".join(branch_references[:10])
        ),
        "model/inputs/*.csv; WebAPP/DataStorage/Fiji_v2/genData.json",
    )

    ohc_references: list[str] = []
    ohc_targets = REMOVED_OHC_TECHNOLOGIES | REMOVED_OHC_FUELS
    for path in INPUTS.glob("*.csv"):
        for row_number, row in enumerate(read_rows(path), start=2):
            if any(value in ohc_targets for value in row.values()):
                ohc_references.append(f"{path.name}:{row_number}")
    ohc_references.extend(
        f"genData:{name}"
        for name in sorted(
            (muiogo_technologies & REMOVED_OHC_TECHNOLOGIES)
            | (muiogo_fuels & REMOVED_OHC_FUELS)
        )
    )
    ohc_pattern = re.compile(r"(?<![A-Z0-9_])(DEMINDOHC|INDOHC|OHC)(?![A-Z0-9_])")
    runtime_paths = [
        *sorted(case.glob("*.json")),
        *sorted((case / "view").glob("*.json")),
        run / "data.txt",
        run / "data_processed.txt",
        run / "results.txt",
    ]
    for path in runtime_paths:
        if path.is_file() and ohc_pattern.search(
            path.read_text(encoding="utf-8", errors="replace")
        ):
            ohc_references.append(str(path.relative_to(case)))
    check(
        "Unsupported other-hydrocarbons branch is absent",
        not ohc_references,
        (
            "OHC, DEMINDOHC, and INDOHC removed"
            if not ohc_references
            else "; ".join(ohc_references[:10])
        ),
        "model/inputs/*.csv; active MUIO JSON; regenerated solver files",
    )

    input_ratios = read_rows(INPUTS / "InputActivityRatio.csv")
    output_ratios = read_rows(INPUTS / "OutputActivityRatio.csv")
    annual_demand = read_rows(INPUTS / "SpecifiedAnnualDemand.csv")
    valid_chain = (
        "PWRTRNFJIXX" in muiogo_technologies
        and {"ELCFJIXX01", "ELCFJIXX02"} <= muiogo_fuels
        and any(
            row["TECHNOLOGY"] == "PWRTRNFJIXX"
            and row["FUEL"] == "ELCFJIXX01"
            and float(row["VALUE"]) != 0
            for row in input_ratios
        )
        and any(
            row["TECHNOLOGY"] == "PWRTRNFJIXX"
            and row["FUEL"] == "ELCFJIXX02"
            and float(row["VALUE"]) != 0
            for row in output_ratios
        )
        and any(
            row["TECHNOLOGY"] != "PWRTRNFJIXX"
            and row["FUEL"] == "ELCFJIXX01"
            and float(row["VALUE"]) != 0
            for row in output_ratios
        )
        and any(
            row["FUEL"] == "ELCFJIXX02" and float(row["VALUE"]) > 0
            for row in annual_demand
        )
    )
    check(
        "Valid grid-node electricity chain remains connected",
        valid_chain,
        (
            "generation -> ELCFJIXX01 -> PWRTRNFJIXX -> ELCFJIXX02 -> demand"
            if valid_chain
            else "One or more links in the retained FJIXX chain are missing"
        ),
        "InputActivityRatio.csv; OutputActivityRatio.csv; SpecifiedAnnualDemand.csv",
    )

    duplicate_count = 0
    row_count = 0
    for path in INPUTS.glob("*.csv"):
        rows = read_rows(path)
        row_count += len(rows)
        if not rows:
            continue
        key_fields = [field for field in rows[0] if field != "VALUE"] or list(rows[0])
        keys = [tuple(row[field] for field in key_fields) for row in rows]
        duplicate_count += len(keys) - len(set(keys))
    check(
        "OSeMOSYS input indices are unique",
        duplicate_count == 0,
        f"{duplicate_count} duplicates across {row_count} rows",
        "Fiji_v2_CLEWs_calibration/model/inputs/*.csv",
    )

    bound_pairs = (
        ("TotalTechnologyAnnualActivityLowerLimit.csv", "TotalTechnologyAnnualActivityUpperLimit.csv"),
        ("TechnologyActivityByModeLowerLimit.csv", "TechnologyActivityByModeUpperLimit.csv"),
        ("TotalAnnualMinCapacity.csv", "TotalAnnualMaxCapacity.csv"),
        ("TotalAnnualMinCapacityInvestment.csv", "TotalAnnualMaxCapacityInvestment.csv"),
    )
    positive_equalities: list[tuple[str, tuple[str, ...], float]] = []
    for lower_name, upper_name in bound_pairs:
        lower_fields, lower = value_map(INPUTS / lower_name)
        upper_fields, upper = value_map(INPUTS / upper_name)
        if lower_fields != upper_fields:
            positive_equalities.append(("schema mismatch", (), math.nan))
            continue
        for key, lower_value in lower.items():
            upper_value = upper.get(key)
            if (
                upper_value is not None
                and lower_value > 0
                and math.isclose(lower_value, upper_value, abs_tol=1e-12)
            ):
                positive_equalities.append(
                    (f"{lower_name}/{upper_name}", key, lower_value)
                )
    check(
        "No positive lower-equals-upper history locks",
        not positive_equalities,
        f"{len(positive_equalities)} positive exact locks",
        "Four activity/capacity lower-upper parameter pairs",
    )

    proxy_config = read_json(ROOT / "muio" / "reserve_margin_proxy_config.json")
    validate_config(proxy_config)
    case_data = load_case(case)
    expected_reserve_proxy = expected_proxy(case_data, proxy_config)
    reserve_proxy_report = check_proxy(
        case, case_data, proxy_config, expected_reserve_proxy, 1e-10
    )
    check(
        "Reserve-margin proxy matches the active inputs",
        reserve_proxy_report["status"] == "CURRENT",
        (
            f"{reserve_proxy_report['status']}; "
            f"{reserve_proxy_report['mismatch_count']} mismatch(es)"
        ),
        "WebAPP/DataStorage/Fiji_v2/reserve_margin_proxy.json and active inputs",
    )

    expected_hashes = {
        "EFL_2024_Annual_Report.pdf": "b3427b8e597399f31aabc2ab315b1a72a24138e20cd8faa5c3fec2894f0fe956",
        "Fiji_REI_Investment_Plan_2023.pdf": "3d291fad4853905d40486f253d974483a9b788881c6ea9e02e6ba725989790e1",
    }
    hash_mismatches = []
    bundled_source_count = 0
    for filename, expected in expected_hashes.items():
        path = ROOT / "data_sources" / "evidence" / "external" / filename
        if not path.exists():
            continue
        bundled_source_count += 1
        actual = sha256(path)
        if actual != expected:
            hash_mismatches.append(f"{filename}: {actual}")
    check(
        "Primary-source checksums are registered and bundled files match",
        not hash_mismatches,
        (
            f"{len(expected_hashes)} source hashes registered; "
            f"{bundled_source_count} source files bundled"
            if not hash_mismatches
            else "; ".join(hash_mismatches)
        ),
        "data_sources/evidence/calibration/SOURCE_EXTRACTS.md",
    )

    manifest = json.loads(
        (ROOT / "diagnostics" / "calibration_runs" / "build_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    check(
        "Build manifest pins evidence and the calibration/validation split",
        manifest["evidence_sha256"] == sha256(EVIDENCE)
        and manifest["calibration_years"] == [2020, 2021, 2022]
        and manifest["validation_years"] == [2023, 2024],
        (
            f"evidence {manifest['evidence_sha256']}; calibration "
            f"{manifest['calibration_years']}; validation {manifest['validation_years']}"
        ),
        "diagnostics/calibration_runs/build_manifest.json",
    )

    fit = json.loads((fit_folder / "summary.json").read_text(encoding="utf-8"))
    validation = fit["metrics"]["validation"]
    check(
        "Held-out material generation fit meets the declared annual threshold",
        validation["generation_mape_percent"] <= 15,
        f"2023-2024 MAPE {validation['generation_mape_percent']:.3f}%",
        str(fit_folder / "summary.json"),
    )
    check(
        "Held-out renewable-share fit meets the declared annual threshold",
        validation["renewable_share_mae_percentage_points"] <= 7.5,
        (
            "2023-2024 renewable-share MAE "
            f"{validation['renewable_share_mae_percentage_points']:.3f} percentage points"
        ),
        str(fit_folder / "summary.json"),
    )

    comparison_rows = read_rows(fit_folder / "history_comparisons.csv")
    heldout = [row for row in comparison_rows if row["split"] == "validation"]
    worst_material = max(
        (
            abs(float(row["percent_error"])),
            f"{row['year']} {row['outcome']}",
        )
        for row in heldout
        if row["outcome"].endswith("_generation")
        and float(row["observed_gwh"]) >= 1
    )
    check(
        "No held-out material annual generation outcome misses by more than 20%",
        worst_material[0] <= 20,
        f"Worst: {worst_material[1]} at {worst_material[0]:.3f}%",
        str(fit_folder / "history_comparisons.csv"),
    )

    active_input_files = [
        path
        for path in case.glob("*.json")
        if path.is_file()
    ]
    newest_input_mtime = max(path.stat().st_mtime for path in active_input_files)
    result_files = [
        run / "data.txt",
        run / "data_processed.txt",
        run / "lp.lp",
        run / "results.txt",
        run / "csv" / "ObjectiveValue.csv",
    ]
    missing_result_files = [str(path) for path in result_files if not path.is_file()]
    oldest_result_mtime = (
        min(path.stat().st_mtime for path in result_files)
        if not missing_result_files
        else 0
    )
    check(
        "Regenerated run is newer than the active model inputs",
        not missing_result_files and oldest_result_mtime >= newest_input_mtime,
        (
            "All required run artifacts postdate the active inputs"
            if not missing_result_files and oldest_result_mtime >= newest_input_mtime
            else f"Missing/stale artifacts: {missing_result_files}"
        ),
        f"MUIO source JSON and {args.run} generated artifacts",
    )

    failed = [item for item in checks if item["status"] == "FAIL"]
    result = {
        "schema_version": 1,
        "model": "Fiji_v2",
        "run": args.run,
        "status": "PASS" if not failed else "FAIL",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "case_folder": str(case),
            "dimensions": {
                "technologies": technology_count,
                "commodities": commodity_count,
                "years": len(years),
                "timeslices": len(gen_data["osy-ts"]),
            },
            "artifacts": {
                str(path.relative_to(case)): {
                    "sha256": sha256(path),
                    "modified_at": datetime.fromtimestamp(
                        path.stat().st_mtime, timezone.utc
                    ).isoformat(),
                }
                for path in result_files
            },
            "reserve_margin_proxy": reserve_proxy_report,
        },
        "checks": checks,
        "failed_checks": len(failed),
        "scope": (
            "Technical, annual national grid-supply energy calibration and "
            "Phase 1B public-water closure; not a validation of the full "
            "land-water-agriculture nexus."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
