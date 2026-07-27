#!/usr/bin/env python3
"""Validate Fiji v2 source, assumption, calculation and model-file lineage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
DATA = PACKAGE / "data_sources"
PROJECTION = (
    DATA
    / "evidence"
    / "energy"
    / "fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv"
)
LOCATORS = (
    DATA
    / "evidence"
    / "energy"
    / "PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md"
)
MANIFEST = PACKAGE / "diagnostics" / "calibration_runs" / "build_manifest.json"
DEFAULT_OUTPUT = (
    PACKAGE
    / "diagnostics"
    / "calibration_runs"
    / "phase1c"
    / "data_lineage_validation_summary.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def refs(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def check(name: str, finding: Any, passed: bool) -> dict[str, Any]:
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "finding": finding,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    _, assumptions = read_csv(DATA / "ASSUMPTIONS.csv")
    _, calculations = read_csv(DATA / "CALCULATIONS.csv")
    _, model_map = read_csv(DATA / "MODEL_DATA_MAP.csv")
    source_text = (DATA / "DATA_SOURCES.md").read_text(encoding="utf-8")
    source_ids = set(re.findall(r"`(DS-[A-Z0-9.-]+)`", source_text))
    assumption_ids = {row["assumption_id"] for row in assumptions}
    calculation_ids = {row["calculation_id"] for row in calculations}
    map_ids = {row["map_id"] for row in model_map}

    checks: list[dict[str, Any]] = []
    ledger_counts = {
        "sources": len(source_ids),
        "assumptions": len(assumption_ids),
        "calculations": len(calculation_ids),
        "model_map": len(map_ids),
    }
    unique = (
        len(assumption_ids) == len(assumptions)
        and len(calculation_ids) == len(calculations)
        and len(map_ids) == len(model_map)
    )
    checks.append(check("Ledger identifiers are unique", ledger_counts, unique))

    missing_model_refs: dict[str, list[str]] = {}
    for row in model_map:
        missing = (
            refs(row["source_ids"]) - source_ids
            | refs(row["assumption_ids"]) - assumption_ids
            | refs(row["calculation_ids"]) - calculation_ids
        )
        if missing:
            missing_model_refs[row["map_id"]] = sorted(missing)
    checks.append(
        check(
            "Every MODEL_DATA_MAP reference resolves",
            missing_model_refs or "All references resolve",
            not missing_model_refs,
        )
    )

    missing_calculation_refs: dict[str, list[str]] = {}
    for row in calculations:
        missing = (
            refs(row["source_ids"]) - source_ids
            | refs(row["assumption_ids"]) - assumption_ids
        )
        if missing:
            missing_calculation_refs[row["calculation_id"]] = sorted(missing)
    checks.append(
        check(
            "Every CALCULATIONS reference resolves",
            missing_calculation_refs or "All references resolve",
            not missing_calculation_refs,
        )
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    phase = manifest["phase_1c_bottom_up_electricity"]
    evidence = phase["evidence"]
    expected_projection_hash = evidence["projection_sha256"]
    actual_projection_hash = sha256(PROJECTION)
    checks.append(
        check(
            "Projection evidence checksum matches the build manifest",
            {
                "expected": expected_projection_hash,
                "actual": actual_projection_hash,
            },
            actual_projection_hash == expected_projection_hash,
        )
    )

    _, projection_rows = read_csv(PROJECTION)
    years = [int(row["year"]) for row in projection_rows]
    history_differences = [
        abs(float(row["difference_from_phase1b_control_pj"]))
        for row in projection_rows
        if int(row["year"]) <= 2024
    ]
    projection_shape_ok = (
        years == list(range(2020, 2051))
        and max(history_differences, default=float("inf")) <= 1e-10
        and abs(
            float(projection_rows[-1]["bottom_up_gross_grid_requirement_pj"])
            - 7.237375886081
        )
        <= 1e-10
    )
    checks.append(
        check(
            "Projection evidence covers 2020-2050 and preserves history",
            {
                "years": [min(years), max(years)],
                "rows": len(years),
                "maximum_historical_control_difference_pj": max(
                    history_differences
                ),
                "gross_2050_pj": float(
                    projection_rows[-1][
                        "bottom_up_gross_grid_requirement_pj"
                    ]
                ),
            },
            projection_shape_ok,
        )
    )

    _, demand_rows = read_csv(
        PACKAGE / "model" / "inputs" / "SpecifiedAnnualDemand.csv"
    )
    demand = {
        (row["FUEL"], int(row["YEAR"])): float(row["VALUE"])
        for row in demand_rows
    }
    projection_fields = {
        "ELCFJIXX02": "direct_loss_and_boundary_overhead_pj",
        "COMELCFJIXX02": "commercial_grid_use_pj",
        "INDELCFJIXX02": "industrial_grid_use_pj",
        "RESELCFJIXX02": "grid_residential_use_pj",
    }
    maximum_input_difference = 0.0
    missing_input_rows: list[str] = []
    for row in projection_rows:
        year = int(row["year"])
        for commodity, field in projection_fields.items():
            key = (commodity, year)
            if key not in demand:
                missing_input_rows.append(f"{commodity}:{year}")
                continue
            maximum_input_difference = max(
                maximum_input_difference,
                abs(demand[key] - float(row[field])),
            )
    checks.append(
        check(
            "Frozen projection matches portable demand inputs",
            {
                "maximum_absolute_difference_pj": maximum_input_difference,
                "missing_rows": missing_input_rows,
            },
            not missing_input_rows and maximum_input_difference <= 1e-9,
        )
    )

    locator_text = LOCATORS.read_text(encoding="utf-8")
    required_sources = {
        "DS-EFL-AR-2024",
        "DS-FBS-ENERGY-ACCOUNT-2024",
        "DS-FIJI-LEDS-2018",
        "DS-FJI-MICS-2021",
    }
    missing_locator_sources = sorted(
        source for source in required_sources if source not in locator_text
    )
    missing_locator_hashes = sorted(
        digest
        for digest in evidence["external_source_sha256"].values()
        if digest not in locator_text
    )
    checks.append(
        check(
            "Active Phase 1C sources have locator and checksum records",
            {
                "missing_source_ids": missing_locator_sources,
                "missing_hashes": missing_locator_hashes,
            },
            not missing_locator_sources and not missing_locator_hashes,
        )
    )

    archive = PACKAGE / phase["portable_archive"]
    actual_archive_hash = sha256(archive)
    checks.append(
        check(
            "Portable archive checksum matches the build manifest",
            {
                "archive": str(archive.relative_to(PACKAGE)),
                "expected": phase["portable_archive_sha256"],
                "actual": actual_archive_hash,
            },
            actual_archive_hash == phase["portable_archive_sha256"],
        )
    )

    failures = [item for item in checks if item["status"] == "FAIL"]
    report = {
        "schema_version": 1,
        "model": "Fiji_v2",
        "phase": "1C bottom-up electricity",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failed_checks": len(failures),
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
