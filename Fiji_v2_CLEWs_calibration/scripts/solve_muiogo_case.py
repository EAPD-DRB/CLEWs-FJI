#!/usr/bin/env python3
"""Create, generate, and solve a Fiji v2 MUIO case run with CBC."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", nargs="?", default="Historical_Backcast")
    parser.add_argument(
        "--case",
        default="Fiji_v2",
        help="MUIO case directory under WebAPP/DataStorage/",
    )
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument(
        "--muiogo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="MUIOGO repository containing API/ and WebAPP/",
    )
    args = parser.parse_args()

    repo = args.muiogo_root.resolve()
    if not (repo / "API").is_dir() or not (repo / "WebAPP").is_dir():
        raise SystemExit(f"Not a MUIOGO repository: {repo}")
    sys.path.insert(0, str(repo / "API"))
    from Classes.Case.DataFileClass import DataFile

    case = args.case
    data_file = DataFile(case)
    scenarios = [
        {
            "ScenarioId": item["ScenarioId"],
            "Scenario": item["Scenario"],
            "Desc": item.get("Desc", ""),
            "Active": item["ScenarioId"] == "SC_0",
        }
        for item in data_file.genData["osy-scenarios"]
    ]
    run_data = {
        "Case": args.run,
        "CaseId": f"{case.lower().replace('_', '-')}-{args.run.lower()}",
        "Desc": (
            "Annual grid-supply backcast. 2020-2022 calibration and "
            "2023-2024 held-out validation."
        ),
        "Runtime": date.today().isoformat(),
        "Scenarios": scenarios,
    }
    run_path = repo / "WebAPP" / "DataStorage" / case / "res" / args.run
    if args.reuse_existing:
        if not run_path.is_dir():
            raise RuntimeError(f"Existing run not found: {run_path}")
    else:
        created = data_file.createCaseRun(args.run, run_data)
        if created.get("status_code") != "success":
            raise RuntimeError(json.dumps(created, indent=2))
    data_file.generateDatafile(args.run)
    result = data_file.run("cbc", args.run)
    payload = {
        "case": case,
        "run": args.run,
        "status": result.get("status_code"),
        "timer": result.get("timer"),
        "cbc": result.get("cbc_message", "")[-2000:],
        "glpk": result.get("glpk_message", "")[-2000:],
    }
    print(json.dumps(payload, indent=2))
    if result.get("status_code") != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
