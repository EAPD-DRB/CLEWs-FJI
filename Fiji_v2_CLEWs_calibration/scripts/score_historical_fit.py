#!/usr/bin/env python3
"""Score Fiji v2 annual electricity outputs against 2020-2024 observations."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "Fiji_v2_CLEWs_calibration"
CASE = REPO / "WebAPP" / "DataStorage" / "Fiji_v2"
EVIDENCE = (
    PACKAGE
    / "data_sources"
    / "evidence"
    / "calibration"
    / "historical_electricity_2020_2024.csv"
)
OUT = PACKAGE / "diagnostics" / "calibration_runs" / "historical_fit"
TECHNOLOGIES = {
    "biomass_ipp": (
        "PWRBIOFJIXX01",
        "PWRBAGFJIXX01",
        "PWRWODFJIXX01",
    ),
    "hydro": ("PWRHYDFJIXX01",),
    "thermal": ("PWROILFJIXX01",),
    "wind": ("PWRWONFJIXX01",),
}
OBSERVATION_FIELDS = {
    "biomass_ipp": "ipp_mwh",
    "hydro": "hydro_mwh",
    "thermal": "thermal_mwh",
    "wind": "wind_mwh",
}
PJ_TO_GWH = 1.0 / 0.0036


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
        "--output-dir",
        type=Path,
        default=OUT,
        help="directory for refreshed historical-fit diagnostics",
    )
    return parser.parse_args()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def locate_result(run_folder: Path, filename: str) -> Path:
    candidates = sorted(run_folder.rglob(filename))
    if not candidates:
        raise FileNotFoundError(f"{filename} not found below {run_folder}")
    return candidates[0]


def parse_production(run_folder: Path) -> dict[tuple[str, int], float]:
    path = locate_result(run_folder, "TotalAnnualTechnologyActivityByMode.csv")
    result: dict[tuple[str, int], float] = defaultdict(float)
    for row in rows(path):
        technology = row.get("TECHNOLOGY") or row.get("Technology") or row.get("t")
        year = row.get("YEAR") or row.get("Year") or row.get("y")
        value = (
            row.get("VALUE")
            or row.get("Value")
            or row.get("TotalAnnualTechnologyActivityByMode")
        )
        if technology and year and value:
            result[(technology, int(float(year)))] += float(value) * PJ_TO_GWH
    return result


def pct_error(model: float, observed: float) -> float | None:
    return None if observed == 0 else 100.0 * (model - observed) / observed


def main() -> None:
    args = parse_args()
    case_folder = args.case_folder.resolve()
    run_folder = case_folder / "res" / args.run
    output_dir = args.output_dir.resolve()
    if not (case_folder / "genData.json").is_file():
        raise FileNotFoundError(f"Not a MUIO case folder: {case_folder}")
    if not run_folder.is_dir():
        raise FileNotFoundError(f"Saved run not found: {run_folder}")

    evidence = {int(row["year"]): row for row in rows(EVIDENCE)}
    production = parse_production(run_folder)
    comparisons: list[dict[str, Any]] = []

    for year in sorted(evidence):
        split = evidence[year]["split"]
        model_by_category = {
            category: sum(
                production.get((technology, year), 0.0)
                for technology in technologies
            )
            for category, technologies in TECHNOLOGIES.items()
        }
        for category, model_gwh in model_by_category.items():
            observed_gwh = float(evidence[year][OBSERVATION_FIELDS[category]]) / 1000
            forcing = (
                "H"
                if split == "calibration" and category in {"biomass_ipp", "wind"}
                else "E"
            )
            comparisons.append(
                {
                    "year": year,
                    "split": split,
                    "outcome": f"{category}_generation",
                    "forcing_class": forcing,
                    "observed_gwh": observed_gwh,
                    "model_gwh": model_gwh,
                    "error_gwh": model_gwh - observed_gwh,
                    "absolute_error_gwh": abs(model_gwh - observed_gwh),
                    "percent_error": pct_error(model_gwh, observed_gwh),
                    "source_id": "DS-EFL-AR-2024",
                }
            )

        observed_total = float(evidence[year]["total_generation_mwh"]) / 1000
        model_total = sum(model_by_category.values())
        observed_renewable = sum(
            float(evidence[year][field]) / 1000
            for field in ("hydro_mwh", "wind_mwh", "solar_mwh", "ipp_mwh")
        )
        model_renewable = (
            model_by_category["hydro"]
            + model_by_category["wind"]
            + model_by_category["biomass_ipp"]
        )
        comparisons.extend(
            [
                {
                    "year": year,
                    "split": split,
                    "outcome": "total_grid_supply",
                    "forcing_class": "J",
                    "observed_gwh": observed_total,
                    "model_gwh": model_total,
                    "error_gwh": model_total - observed_total,
                    "absolute_error_gwh": abs(model_total - observed_total),
                    "percent_error": pct_error(model_total, observed_total),
                    "source_id": "DS-EFL-AR-2024",
                },
                {
                    "year": year,
                    "split": split,
                    "outcome": "renewable_share",
                    "forcing_class": "E",
                    "observed_gwh": 100 * observed_renewable / observed_total,
                    "model_gwh": 100 * model_renewable / model_total,
                    "error_gwh": 100
                    * (model_renewable / model_total - observed_renewable / observed_total),
                    "absolute_error_gwh": abs(
                        100
                        * (
                            model_renewable / model_total
                            - observed_renewable / observed_total
                        )
                    ),
                    "percent_error": None,
                    "source_id": "DS-EFL-AR-2024",
                },
            ]
        )

    scored = [
        row
        for row in comparisons
        if row["forcing_class"] == "E" and row["outcome"] != "wind_generation"
    ]
    by_split: dict[str, dict[str, float]] = {}
    for split in ("calibration", "validation"):
        subset = [row for row in scored if row["split"] == split]
        energy_rows = [
            row
            for row in subset
            if row["outcome"].endswith("_generation")
            and row["observed_gwh"] >= 1
        ]
        share_rows = [row for row in subset if row["outcome"] == "renewable_share"]
        by_split[split] = {
            "generation_mae_gwh": sum(row["absolute_error_gwh"] for row in energy_rows)
            / len(energy_rows),
            "generation_mape_percent": sum(
                abs(row["percent_error"]) for row in energy_rows
            )
            / len(energy_rows),
            "renewable_share_mae_percentage_points": sum(
                row["absolute_error_gwh"] for row in share_rows
            )
            / len(share_rows),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = output_dir / "history_comparisons.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(comparisons[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(comparisons)

    tolerances = {
        "biomass_ipp_generation": (0.20, 1.0),
        "hydro_generation": (0.15, 1.5),
        "thermal_generation": (0.20, 1.5),
        "wind_generation": (1.00, 0.05),
        "total_grid_supply": (0.01, 0.10),
        "renewable_share": (0.10, 1.5),
    }
    assessment_rows: list[dict[str, Any]] = []
    for row in comparisons:
        tolerance, weight = tolerances[row["outcome"]]
        is_share = row["outcome"] == "renewable_share"
        assessment_rows.append(
            {
                "domain": "energy",
                "metric": row["outcome"].replace("_", " "),
                "observed": row["observed_gwh"],
                "modeled": row["model_gwh"],
                "tolerance": tolerance,
                "forcing_class": row["forcing_class"],
                "phase": row["split"],
                "weight": weight,
                "year": row["year"],
                "period": "annual",
                "region": "Fiji national grid-supply aggregate",
                "unit": "percent" if is_share else "GWh",
                "source": row["source_id"],
                "constraint_refs": (
                    "SpecifiedAnnualDemand; ResidualCapacity; AvailabilityFactor; "
                    "CapacityFactor; TotalAnnualMaxCapacityInvestment"
                ),
                "notes": (
                    "Total supply is a supplied J boundary and earns no demand-"
                    "reproduction claim. Calibration-period IPP/biomass and wind "
                    "availabilities use the same period and are H. The 2023-2024 "
                    "outputs use parameters frozen before validation."
                ),
            }
        )

    capacity_metrics = {
        "hydro": ("hydro_capacity_mw", 133.4),
        "thermal": ("thermal_capacity_mw", 182.0),
        "wind": ("wind_capacity_mw", 9.8),
        "biomass_ipp": ("biomass_capacity_mw", 34.0),
    }
    capacity_evidence = evidence[2021]
    for category, (field, modeled_mw) in capacity_metrics.items():
        assessment_rows.append(
            {
                "domain": "energy",
                "metric": f"{category.replace('_', ' ')} installed capacity",
                "observed": float(capacity_evidence[field]),
                "modeled": modeled_mw,
                "tolerance": 0.02,
                "forcing_class": "J",
                "phase": "calibration",
                "weight": 0.25,
                "year": 2021,
                "period": "year end / reported installed fleet",
                "region": "Fiji national grid-supply aggregate",
                "unit": "MW",
                "source": "DS-FJI-REI-IP",
                "constraint_refs": "ResidualCapacity",
                "notes": (
                    "Observed installed stock is a justified exogenous initial "
                    "condition; it is not endogenous reproduction."
                ),
            }
        )
    assessment_path = output_dir / "assessment_comparisons.csv"
    with assessment_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(assessment_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(assessment_rows)

    try:
        assessment_reference = str(assessment_path.relative_to(PACKAGE.parent))
    except ValueError:
        assessment_reference = str(assessment_path)

    summary = {
        "run": args.run,
        "case_folder": str(case_folder),
        "calibration_years": [2020, 2021, 2022],
        "validation_years": [2023, 2024],
        "metrics": by_split,
        "assessment_comparisons": assessment_reference,
        "credit_rule": (
            "Only class E rows receive independent reproduction credit. "
            "Demand/total supply and fleet are J. Calibration-period biomass "
            "and wind are H because their annual availability factors were "
            "estimated from 2020-2022 outcomes; their frozen 2023-2024 values "
            "are E. Wind is excluded from aggregate MAPE because its observed "
            "output is below 1 GWh and percentage errors are unstable."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
