#!/usr/bin/env python3
"""Generate, preprocess, or solve a Fiji_v2.7 Fisheries run through MUIO."""

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
DEFAULT_CASE = ".Fiji_v2.7-fisheries-candidate"
DEFAULT_RUN = "Fisheries_v2.7"
sys.path.insert(0, str(REPO / "API"))

from Classes.Case.DataFileClass import DataFile  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_run(model: DataFile, case: str, run: str) -> None:
    run_path = STORAGE / case / "res" / run
    if run_path.is_dir():
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
            "CaseId": "RUN_FSH_V27",
            "Desc": "Fiji v2.7 Fisheries validation and release run.",
            "Runtime": date.today().isoformat(),
            "Scenarios": scenarios,
        },
    )
    if response.get("status_code") != "success":
        raise RuntimeError(json.dumps(response, indent=2))


def generate(case: str, run: str) -> dict[str, object]:
    started = time.time()
    model = DataFile(case)
    ensure_run(model, case, run)
    model.generateDatafile(run)
    run_path = STORAGE / case / "res" / run
    model.preprocessData(run_path / "data.txt", run_path / "data_processed.txt")
    return {
        "status": "generated",
        "case": case,
        "case_identity": model.genData["osy-casename"],
        "run": run,
        "model": str(model.osemosysFile.resolve()),
        "elapsed_seconds": time.time() - started,
        "hashes": {
            "data.txt": digest(run_path / "data.txt"),
            "data_processed.txt": digest(run_path / "data_processed.txt"),
        },
    }


def solve(case: str, run: str, report_path: Path | None) -> dict[str, object]:
    started = time.time()
    model = DataFile(case)
    ensure_run(model, case, run)
    model.generateDatafile(run)
    generation_seconds = time.time() - started
    response = model.run("CBC", run)
    run_path = STORAGE / case / "res" / run
    first_line = (run_path / "results.txt").read_text(encoding="utf-8").splitlines()[0]
    objective_match = re.search(r"objective value\s+([-+0-9.eE]+)", first_line)
    matrix_match = re.search(
        r"(\d+) rows, (\d+) columns, (\d+) non-zeros", response.get("glpk_message", "")
    )
    if response.get("status_code") != "success" or objective_match is None:
        raise RuntimeError(json.dumps(response, indent=2))
    report: dict[str, object] = {
        "status": "optimal",
        "case": case,
        "case_identity": model.genData["osy-casename"],
        "run": run,
        "solver": "CBC",
        "model": str(model.osemosysFile.resolve()),
        "objective": float(objective_match.group(1)),
        "first_line": first_line,
        "generation_seconds": generation_seconds,
        "elapsed_seconds": time.time() - started,
        "timer": response.get("timer"),
        "matrix": (
            {
                "rows": int(matrix_match.group(1)),
                "columns": int(matrix_match.group(2)),
                "nonzeros": int(matrix_match.group(3)),
            }
            if matrix_match
            else None
        ),
        "hashes": {
            name: digest(run_path / name)
            for name in ("data.txt", "data_processed.txt", "lp.lp", "results.txt")
        },
        "cbc_tail": response.get("cbc_message", "")[-3000:],
        "glpk_tail": response.get("glpk_message", "")[-3000:],
    }
    if report_path:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("generate", "solve"))
    parser.add_argument("--case", default=DEFAULT_CASE)
    parser.add_argument("--run", default=DEFAULT_RUN)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = (
            generate(args.case, args.run)
            if args.phase == "generate"
            else solve(args.case, args.run, args.report)
        )
    except Exception as error:
        print(json.dumps({"status": "fail", "error": str(error)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
