#!/usr/bin/env python3
"""Generate or solve a Fiji v2.9 population/Fisheries/trade run through MUIO."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
STORAGE = REPO / "WebAPP" / "DataStorage"
DEFAULT_CASE = ".Fiji_v2.9-population-fisheries-trade-candidate"
DEFAULT_RUN = "Population_Fisheries_Trade_v2.9"
sys.path.insert(0, str(REPO / "API"))

from Classes.Case.DataFileClass import DataFile  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_run(model: DataFile, case: str, run: str) -> None:
    if (STORAGE / case / "res" / run).is_dir():
        return
    scenarios = [
        {
            "ScenarioId": item["ScenarioId"],
            "Scenario": item["Scenario"],
            "Desc": item.get("Desc", ""),
            "Active": item["ScenarioId"] == "SC_0",
        }
        for item in model.genData["osy-scenarios"]
    ]
    response = model.createCaseRun(
        run,
        {
            "Case": run,
            "CaseId": "RUN_FJI_V29_POP_FISHERIES_TRADE",
            "Desc": "Fiji v2.9 population-driven Fisheries food demand and 2025 trade validation.",
            "Runtime": date.today().isoformat(),
            "Scenarios": scenarios,
        },
    )
    if response.get("status_code") != "success":
        raise RuntimeError(json.dumps(response, indent=2))


def run(case: str, run_name: str, solve: bool) -> dict[str, object]:
    started = time.time()
    model = DataFile(case)
    ensure_run(model, case, run_name)
    model.generateDatafile(run_name)
    run_path = STORAGE / case / "res" / run_name
    model.preprocessData(run_path / "data.txt", run_path / "data_processed.txt")
    report: dict[str, object] = {
        "status": "generated",
        "case": case,
        "case_identity": model.genData["osy-casename"],
        "run": run_name,
        "model": str(model.osemosysFile.resolve()),
        "generation_seconds": time.time() - started,
    }
    if solve:
        response = model.run("CBC", run_name)
        first = (run_path / "results.txt").read_text(encoding="utf-8").splitlines()[0]
        objective = re.search(r"objective value\s+([-+0-9.eE]+)", first)
        matrix = re.search(
            r"(\d+) rows, (\d+) columns, (\d+) non-zeros", response.get("glpk_message", "")
        )
        if response.get("status_code") != "success" or objective is None:
            raise RuntimeError(json.dumps(response, indent=2))
        report.update(
            status="optimal",
            objective=float(objective.group(1)),
            first_line=first,
            elapsed_seconds=time.time() - started,
            timer=response.get("timer"),
            matrix=(
                {
                    "rows": int(matrix.group(1)),
                    "columns": int(matrix.group(2)),
                    "nonzeros": int(matrix.group(3)),
                }
                if matrix
                else None
            ),
        )
    report["hashes"] = {
        name: digest(run_path / name)
        for name in ("data.txt", "data_processed.txt")
        + (("lp.lp", "results.txt") if solve else ())
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("generate", "solve"))
    parser.add_argument("--case", default=DEFAULT_CASE)
    parser.add_argument("--run", default=DEFAULT_RUN)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.case, args.run, args.phase == "solve")
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"status": "fail", "error": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
