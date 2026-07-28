#!/usr/bin/env python3
"""Remove Fiji Phase 1D's inactive aggregate biomass migration shell.

The cleanup is intentionally narrow. It refuses to remove
``PWRBIOFJIXX01`` unless source parameters and the selected control result
prove that the technology has zero capacity, investment and activity. The
structural deletion is then passed through MUIOGO ``UpdateCase`` so all
technology-indexed source JSON files are rebuilt from ``genData.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from apply_fiji_phase1d_cane_bagasse import (
    OLD_POWER,
    copy_case_sources,
    read_csv,
    read_json,
    run_update_case,
    source_fingerprints,
    update_reserve_proxy,
    write_csv,
    write_json,
)


PACKAGE = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = PACKAGE / "model" / "inputs"
DEFAULT_MUIOGO = Path(__file__).resolve().parents[3] / "MUIOGO"
BASE_SCENARIO = "SC_0"
ZERO_TOLERANCE = 1e-12
LEGACY_TECH_ID = "TEC_w665d"
REQUIRED_ZERO_PARAMETERS = (
    "RC",
    "TAMaxC",
    "TAMaxCI",
    "TAMinC",
    "TAMinCI",
    "TAL",
    "TAU",
)


def parameter_row(
    data: dict[str, Any], parameter: str, tech_id: str
) -> dict[str, Any]:
    rows = data[parameter][BASE_SCENARIO]
    matches = [row for row in rows if row.get("TechId") == tech_id]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {parameter} row for {tech_id}; "
            f"found {len(matches)}"
        )
    return matches[0]


def year_values(row: dict[str, Any]) -> dict[int, float]:
    return {
        int(key): float(value)
        for key, value in row.items()
        if str(key).isdigit()
    }


def locate_result(run_folder: Path, filename: str) -> Path:
    matches = sorted(run_folder.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"{filename} not found below {run_folder}")
    return matches[0]


def result_values(
    run_folder: Path, filename: str, technology: str
) -> list[float]:
    path = locate_result(run_folder, filename)
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    values: list[float] = []
    for row in rows:
        row_technology = (
            row.get("TECHNOLOGY")
            or row.get("Technology")
            or row.get("t")
        )
        if row_technology != technology:
            continue
        raw = (
            row.get("VALUE")
            or row.get("Value")
            or row.get(filename.removesuffix(".csv"))
        )
        if raw is not None:
            values.append(float(raw))
    return values


def deterministic_preconditions(
    case_path: Path, control_run: str
) -> dict[str, Any]:
    gen_data = read_json(case_path / "genData.json")
    matches = [
        item
        for item in gen_data["osy-tech"]
        if item["Tech"] == OLD_POWER
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {OLD_POWER} technology; found {len(matches)}"
        )
    legacy_id = str(matches[0]["TechId"])
    if legacy_id != LEGACY_TECH_ID:
        raise ValueError(
            f"Unexpected {OLD_POWER} ID {legacy_id}; expected "
            f"{LEGACY_TECH_ID}"
        )

    ryt = read_json(case_path / "RYT.json")
    nonzero_source: dict[str, dict[int, float]] = {}
    source_maxima: dict[str, float] = {}
    for parameter in REQUIRED_ZERO_PARAMETERS:
        values = year_values(parameter_row(ryt, parameter, legacy_id))
        source_maxima[parameter] = max(
            (abs(value) for value in values.values()), default=0.0
        )
        offending = {
            year: value
            for year, value in values.items()
            if abs(value) > ZERO_TOLERANCE
        }
        if offending:
            nonzero_source[parameter] = offending
    if nonzero_source:
        raise ValueError(
            f"{OLD_POWER} is not an inactive shell: "
            + json.dumps(nonzero_source, sort_keys=True)
        )

    run_folder = case_path / "res" / control_run
    if not run_folder.is_dir():
        raise FileNotFoundError(f"Control run not found: {run_folder}")
    result_maxima: dict[str, float] = {}
    for filename in (
        "TotalAnnualTechnologyActivityByMode.csv",
        "TotalCapacityAnnual.csv",
        "NewCapacity.csv",
    ):
        values = result_values(run_folder, filename, OLD_POWER)
        result_maxima[filename] = max(
            (abs(value) for value in values), default=0.0
        )
        if result_maxima[filename] > ZERO_TOLERANCE:
            raise ValueError(
                f"{OLD_POWER} has nonzero {filename} in {control_run}: "
                f"{result_maxima[filename]}"
            )

    return {
        "technology": OLD_POWER,
        "technology_id": legacy_id,
        "source_parameter_maxima": source_maxima,
        "control_run": control_run,
        "control_result_maxima": result_maxima,
    }


def prune_gen_data(
    gen_data: dict[str, Any], legacy_id: str
) -> dict[str, Any]:
    technologies = gen_data["osy-tech"]
    retained = [
        item for item in technologies if item["TechId"] != legacy_id
    ]
    if len(technologies) - len(retained) != 1:
        raise ValueError(
            f"Expected to remove one technology ID {legacy_id}"
        )
    gen_data["osy-tech"] = retained

    serialized = json.dumps(gen_data, ensure_ascii=False)
    if legacy_id in serialized or OLD_POWER in serialized:
        raise ValueError(
            f"Legacy technology remains referenced after removal: "
            f"{OLD_POWER}/{legacy_id}"
        )

    gen_data["osy-desc"] = (
        "Fiji v2 annual electricity model with Phase 1D FSC "
        "cane-bagasse-electricity closure and the superseded aggregate "
        "biomass technology removed."
    )
    gen_data["osy-date"] = date.today().isoformat()
    return gen_data


def verify_source_removal(
    case_path: Path, legacy_id: str
) -> dict[str, Any]:
    references: list[str] = []
    for path in sorted(case_path.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        if legacy_id in text or OLD_POWER in text:
            references.append(path.name)
    if references:
        raise ValueError(
            "Legacy technology remains in source JSON: "
            + ", ".join(references)
        )
    gen_data = read_json(case_path / "genData.json")
    return {
        "technologies": len(gen_data["osy-tech"]),
        "commodities": len(gen_data["osy-comm"]),
        "legacy_references": references,
    }


def install_case(
    *,
    source_case: Path,
    target_case: Path,
    muiogo_root: Path,
    control_run: str,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, Any]:
    preconditions = deterministic_preconditions(
        source_case, control_run
    )
    storage = source_case.parent
    before = source_fingerprints(source_case)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{target_case.name}.phase1d-cleanup-",
            dir=storage,
        )
    )
    try:
        copy_case_sources(source_case, stage)
        gen_data = prune_gen_data(
            read_json(stage / "genData.json"),
            preconditions["technology_id"],
        )
        gen_data["osy-casename"] = target_case.name
        write_json(stage / "genData.json", gen_data)
        run_update_case(muiogo_root, stage, gen_data)
        proxy = update_reserve_proxy(stage)
        removal = verify_source_removal(
            stage, preconditions["technology_id"]
        )
        after = source_fingerprints(stage)
        changed_files = sorted(
            name
            for name, digest in after.items()
            if before.get(name) != digest
        )

        report = {
            "dry_run": dry_run,
            "source_case": source_case.name,
            "target_case": target_case.name,
            "preconditions": preconditions,
            "changed_files": changed_files,
            "removal": removal,
            "reserve_proxy": proxy,
        }
        if dry_run:
            return report

        if target_case == source_case:
            for staged_file in sorted(stage.glob("*.json")):
                destination = target_case / staged_file.name
                temporary = destination.with_suffix(
                    destination.suffix + ".phase1d-cleanup"
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
                    target_case.name + ".phase1d-cleanup-backup"
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

        report["target_fingerprints_after"] = source_fingerprints(
            target_case
        )
        return report
    finally:
        if stage.exists() and stage != target_case:
            shutil.rmtree(stage)


def sync_csv_inputs(inputs: Path, dry_run: bool) -> dict[str, Any]:
    files: dict[str, int] = {}
    for path in sorted(inputs.glob("*.csv")):
        fields, rows = read_csv(path)
        if "TECHNOLOGY" in fields:
            retained = [
                row
                for row in rows
                if row["TECHNOLOGY"] != OLD_POWER
            ]
        elif path.name == "TECHNOLOGY.csv":
            retained = [
                row for row in rows if row["VALUE"] != OLD_POWER
            ]
        else:
            continue
        removed = len(rows) - len(retained)
        if not removed:
            continue
        files[path.name] = removed
        if not dry_run:
            write_csv(path, fields, retained)

    if not files:
        raise ValueError(
            f"No portable-input references found for {OLD_POWER}"
        )
    return {
        "dry_run": dry_run,
        "technology": OLD_POWER,
        "files": files,
        "rows_removed": sum(files.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muiogo-root", type=Path, default=DEFAULT_MUIOGO
    )
    parser.add_argument("--source-case", default="Fiji_v2")
    parser.add_argument(
        "--target-case",
        default="Fiji_v2_Phase1D_Legacy_Removal_Test",
    )
    parser.add_argument(
        "--control-run", default="Phase1D_Cane_Bagasse"
    )
    parser.add_argument(
        "--inputs", type=Path, default=DEFAULT_INPUTS
    )
    parser.add_argument("--sync-csv-inputs", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        help="optional path for the machine-readable cleanup report",
    )
    args = parser.parse_args()

    muiogo_root = args.muiogo_root.resolve()
    if not (muiogo_root / "API").is_dir():
        raise SystemExit(f"Not a MUIOGO repository: {muiogo_root}")
    storage = muiogo_root / "WebAPP" / "DataStorage"
    source_case = storage / args.source_case
    target_case = storage / args.target_case
    if not source_case.is_dir():
        raise SystemExit(f"Missing source case: {source_case}")

    report: dict[str, Any] = {
        "phase": "1D legacy-biomass structural cleanup",
        "date": date.today().isoformat(),
        "case": install_case(
            source_case=source_case,
            target_case=target_case,
            muiogo_root=muiogo_root,
            control_run=args.control_run,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        ),
    }
    if args.sync_csv_inputs:
        report["csv_inputs"] = sync_csv_inputs(
            args.inputs.resolve(), args.dry_run
        )
    if args.output is not None:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
