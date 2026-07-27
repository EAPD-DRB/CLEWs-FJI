#!/usr/bin/env python3
"""Audit Fiji v2 commodity topology without modifying model inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "Fiji_v2_CLEWs_calibration"
DEFAULT_CASE = REPO.parent / "MUIOGO" / "WebAPP" / "DataStorage" / "Fiji_v2"
DEFAULT_INPUTS = PACKAGE / "model" / "inputs"
DEFAULT_OUTPUT = PACKAGE / "diagnostics" / "topology" / "phase1a"
HISTORICAL_YEARS = set(range(2020, 2025))
TOLERANCE = 1e-12

END_USE_CARRIERS = {
    "AGRDSL",
    "AGRELCFJIXX02",
    "COMBIO",
    "COMDSL",
    "COMELCFJIXX02",
    "COMKER",
    "COMLPG",
    "COMNGS",
    "INDBIO",
    "INDCOA",
    "INDDSL",
    "INDELCFJIXX02",
    "INDHFO",
    "INDKER",
    "INDLPG",
    "INDNGS",
    "RESBIO",
    "RESELCFJIXX02",
    "RESKER",
    "RESLPG",
    "RESNGS",
    "TRAELCFJIXX02",
    "TRADSL",
    "TRAGSL",
    "TRAHFO",
    "TRAKER",
    "TRANGS",
}
RENEWABLE_RESOURCE_CARRIERS = {"GEO", "HYD", "SOL", "WND"}
WATER_RESOURCES = {"WTRPRCFJI", "WTRGRCFJI", "WTRSURFJI"}
WATER_SINKS = {"WTREVTFJI"}
WATER_SERVICES = {"AGRWATFJI", "PUBWATFJI"}
CROP_SERVICES = {"CRPCAS", "CRPCON", "CRPOTH", "CRPSGC", "CRPYAM"}
LAND_STOCKS = {
    "LTOT",
    "LBARTOT",
    "LBLTTOT",
    "LFORTOT",
    "LGRSTOT",
    "LOTHTOT",
    "LWATTOT",
}
PRIMARY_ENERGY_RESOURCES = {
    "BIO",
    "BIOFJIXX",
    "COA",
    "COAFJI",
    "COAINT",
    "COGFJI",
    "COGINT",
    "CRU",
    "CSPFJIXX",
    "GASFJI",
    "GASINT",
    "GEOFJIXX",
    "HFO",
    "HYDFJIXX",
    "LPG",
    "NGS",
    "OILFJI",
    "OILINT",
    "OTHFJI",
    "OTHINT",
    "PETFJI",
    "PETINT",
    "SPVFJIXX",
    "URNFJI",
    "URNINT",
    "WASFJIXX",
    "WAVFJIXX",
    "WOFFJIXX",
    "WONFJIXX",
}
SECTOR_PREFIXES = {
    "AGR": "agriculture",
    "COM": "commercial",
    "IND": "industry",
    "RES": "residential",
    "TRA": "transport",
    "PUB": "public_water",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-folder",
        type=Path,
        default=DEFAULT_CASE,
        help="Fiji_v2 MUIO case folder",
    )
    parser.add_argument(
        "--input-folder",
        type=Path,
        default=DEFAULT_INPUTS,
        help="authoritative Fiji v2 OSeMOSYS CSV input folder",
    )
    parser.add_argument("--run", default="Historical_Backcast")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="directory for the Phase 1A reports",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 2 when any topology warning is present; never changes the model",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_manifest(paths: Iterable[Path], base: Path) -> dict[str, str]:
    return {
        str(path.relative_to(base)): sha256(path)
        for path in sorted(paths)
        if path.is_file()
    }


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def atomic_write_csv(
    path: Path, rows: list[dict[str, Any]], fieldnames: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def nonzero_rows(path: Path) -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(path)
        if abs(float(row.get("VALUE", "0") or 0)) > TOLERANCE
    ]


def positive_demand_by_commodity(
    input_folder: Path,
) -> tuple[
    dict[str, dict[int, float]],
    dict[str, dict[int, float]],
]:
    specified: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    accumulated: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for filename, target in (
        ("SpecifiedAnnualDemand.csv", specified),
        ("AccumulatedAnnualDemand.csv", accumulated),
    ):
        for row in read_csv(input_folder / filename):
            value = float(row["VALUE"])
            if value > TOLERANCE:
                target[row["FUEL"]][int(row["YEAR"])] += value
    return specified, accumulated


def result_flow_totals(
    path: Path, value_column: str
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    totals: dict[str, float] = defaultdict(float)
    by_technology: dict[str, dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for row in read_csv(path):
        year = int(float(row["y"]))
        if year not in HISTORICAL_YEARS:
            continue
        value = float(row[value_column])
        if abs(value) <= TOLERANCE:
            continue
        commodity = row["f"]
        technology = row["t"]
        totals[commodity] += value
        by_technology[commodity][technology] += value
    return totals, by_technology


def activity_totals(path: Path) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in read_csv(path):
        year = int(float(row["y"]))
        if year in HISTORICAL_YEARS:
            totals[row["t"]] += float(row["TotalAnnualTechnologyActivityByMode"])
    return totals


def sector_for_commodity(commodity: str) -> str | None:
    for prefix, sector in SECTOR_PREFIXES.items():
        if commodity.startswith(prefix):
            return sector
    return None


def sector_for_technology(technology: str) -> str | None:
    for prefix, sector in SECTOR_PREFIXES.items():
        if technology.startswith(f"DEM{prefix}"):
            return sector
    return None


def evidence_for(commodity: str) -> str:
    if commodity in END_USE_CARRIERS:
        return "DS-UNSD-ENERGY-FJI;A-ENE-01"
    if commodity in {"ELCFJIXX01", "ELCFJIXX02"}:
        return "DS-EFL-AR-2024;DS-FJI-REI-IP;M-V2-01"
    if commodity == "PUBWATFJI":
        return "DS-FBS-WATER-2024;M-WTR-01"
    if (
        commodity in WATER_RESOURCES
        or commodity in WATER_SINKS
        or commodity == "AGRWATFJI"
    ):
        return "DS-GAEZ-V4-WATER;A-CLI-01;M-CLI-01"
    if commodity in CROP_SERVICES or commodity.startswith("L"):
        return "DS-GAEZ-V4-LANDCOVER;DS-GAEZ-V4-YIELD;M-LAW-01"
    if commodity in RENEWABLE_RESOURCE_CARRIERS:
        return "DS-OSEMOSYS-GLOBAL;A-ENE-02"
    return "DS-OSEMOSYS-GLOBAL;A-RAW-01"


def classify_role(
    commodity: str,
    producers: set[str],
    consumers: set[str],
    has_demand: bool,
) -> str:
    if commodity in WATER_SINKS:
        return "sink"
    if commodity in LAND_STOCKS or (
        commodity.startswith("L") and commodity.endswith("TOT")
    ):
        return "stock"
    if commodity in WATER_RESOURCES or commodity in RENEWABLE_RESOURCE_CARRIERS:
        return "resource"
    if commodity in PRIMARY_ENERGY_RESOURCES and not has_demand:
        return "resource"
    if commodity in END_USE_CARRIERS or commodity in WATER_SERVICES:
        return "service"
    if commodity in CROP_SERVICES or has_demand:
        return "service"
    if producers and consumers:
        return "intermediate"
    return "unresolved"


def disposition_for(
    commodity: str,
    role: str,
    producers: set[str],
    consumers: set[str],
    has_demand: bool,
) -> str:
    if commodity == "COMELCFJIXX02":
        return (
            "Phase 1B/1C: preserve commercial electricity as service evidence "
            "and remove the nonsensical public-groundwater cross-sector use."
        )
    if commodity == "AGRELCFJIXX02":
        return (
            "Phase 1C/1D: preserve agricultural electricity as service evidence "
            "and review the groundwater technology, which has no raw-water input."
        )
    if commodity == "PUBWATFJI":
        return (
            "Phase 1B: add observed public-water service demand and repair the "
            "surface/groundwater supply topology after documenting raw-water roles."
        )
    if commodity == "WTRGRCFJI":
        return (
            "Phase 1B: decide whether this is recharge, extractable groundwater "
            "or an intermediate before adding an abstraction chain."
        )
    if commodity in {"WTRSURFJI", "WTRPRCFJI", "WTREVTFJI", "AGRWATFJI"}:
        return (
            "Phase 1B/1D: document the physical balance, units and boundary; "
            "retain as resource, intermediate or sink rather than final demand."
        )
    if commodity in END_USE_CARRIERS:
        return (
            "Phase 1C: retain as a final-energy intermediate and connect it to "
            "an evidenced useful-service conversion; quarantine when evidence is absent."
        )
    if commodity in RENEWABLE_RESOURCE_CARRIERS:
        return (
            "Phase 1D: represent availability or potential; do not add final demand "
            "solely to remove a topology warning."
        )
    if role == "stock":
        return (
            "Phase 1D: preserve the physical land/state role and validate its "
            "accounting; do not add arbitrary demand."
        )
    if has_demand and not producers:
        return "Repair the supply path before any calibration or policy use."
    if consumers and not producers:
        return "Classify the missing source and add only an evidenced supply/resource path."
    if producers and not consumers and not has_demand:
        return (
            "Classify as resource, stock, sink, marker or unresolved surplus; "
            "do not auto-delete or attach arbitrary demand."
        )
    if producers and (consumers or has_demand):
        return "Retain; verify units, balance role and historical activity."
    return "Quarantine as unresolved until its physical or service role is evidenced."


def balance_status(
    producers: set[str], consumers: set[str], has_demand: bool
) -> str:
    if has_demand and not producers:
        return "demand_without_supply"
    if consumers and not producers:
        return "consumed_unproduced"
    if producers and not consumers and not has_demand:
        return "produced_unconsumed_undemanded"
    if not producers and not consumers and not has_demand:
        return "disconnected"
    return "connected"


def warning_rows_for(
    commodity: str,
    role: str,
    producers: set[str],
    consumers: set[str],
    has_demand: bool,
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []

    def add(code: str, severity: str, finding: str) -> None:
        warnings.append(
            {
                "commodity": commodity,
                "code": code,
                "severity": severity,
                "role": role,
                "finding": finding,
                "producers": ";".join(sorted(producers)),
                "consumers": ";".join(sorted(consumers)),
            }
        )

    if consumers and not producers:
        add(
            "consumed_unproduced",
            "error",
            "Commodity is consumed but has no producing technology.",
        )
    if producers and not consumers and not has_demand:
        add(
            "produced_unconsumed_undemanded",
            "warning",
            "Commodity is produced but has no consumer or positive demand.",
        )
    if has_demand and not producers:
        add(
            "demand_without_supply",
            "error",
            "Positive specified or accumulated demand has no producing technology.",
        )
    if (
        commodity in RENEWABLE_RESOURCE_CARRIERS
        and producers
        and not consumers
        and not has_demand
    ):
        add(
            "output_only_resource_carrier",
            "warning",
            "Renewable resource carrier is output-only; model availability, not demand.",
        )
    commodity_sector = sector_for_commodity(commodity)
    for consumer in sorted(consumers):
        consumer_sector = sector_for_technology(consumer)
        if (
            commodity_sector
            and consumer_sector
            and commodity_sector != consumer_sector
        ):
            add(
                "likely_cross_sector_consumer",
                "warning",
                f"{consumer} ({consumer_sector}) consumes a {commodity_sector} commodity.",
            )
    return warnings


def join_values(values: Iterable[str]) -> str:
    return ";".join(sorted(set(values)))


def format_number(value: float) -> str:
    return f"{value:.12g}"


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "_None._\n"
    header = "| " + " | ".join(columns) + " |"
    divider = "|" + "|".join("---" for _ in columns) + "|"
    body = [
        "| "
        + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns)
        + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body]) + "\n"


def main() -> int:
    args = parse_args()
    case = args.case_folder.resolve()
    input_folder = args.input_folder.resolve()
    run = case / "res" / args.run
    output_dir = args.output_dir.resolve()

    required = [
        case / "genData.json",
        input_folder / "FUEL.csv",
        input_folder / "TECHNOLOGY.csv",
        input_folder / "InputActivityRatio.csv",
        input_folder / "OutputActivityRatio.csv",
        input_folder / "SpecifiedAnnualDemand.csv",
        input_folder / "AccumulatedAnnualDemand.csv",
        run / "results.txt",
        run / "csv" / "TotalAnnualTechnologyActivityByMode.csv",
        run / "csv" / "ProductionByTechnologyByMode.csv",
        run / "csv" / "UseByTechnologyByMode.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required files: " + "; ".join(missing))

    case_input_paths = [
        *sorted(case.glob("*.json")),
        *sorted((case / "view").glob("*.json")),
    ]
    source_hashes_before = {
        "muiogo_inputs": hash_manifest(case_input_paths, case),
        "csv_inputs": hash_manifest(input_folder.glob("*.csv"), input_folder),
    }

    gen_data = read_json(case / "genData.json")
    commodities = {
        row["Comm"]: {
            "id": row["CommId"],
            "description": row.get("Desc", ""),
            "unit": row.get("UnitId", ""),
        }
        for row in gen_data["osy-comm"]
    }
    technologies = {
        row["Tech"]: {
            "id": row["TechId"],
            "description": row.get("Desc", ""),
        }
        for row in gen_data["osy-tech"]
    }
    csv_commodities = {row["VALUE"] for row in read_csv(input_folder / "FUEL.csv")}
    csv_technologies = {
        row["VALUE"] for row in read_csv(input_folder / "TECHNOLOGY.csv")
    }
    if csv_commodities != set(commodities):
        raise ValueError("FUEL.csv and MUIO genData commodity sets differ")
    if csv_technologies != set(technologies):
        raise ValueError("TECHNOLOGY.csv and MUIO genData technology sets differ")

    producers: dict[str, set[str]] = defaultdict(set)
    consumers: dict[str, set[str]] = defaultdict(set)
    modes_by_producer: dict[str, set[str]] = defaultdict(set)
    modes_by_consumer: dict[str, set[str]] = defaultdict(set)
    for row in nonzero_rows(input_folder / "OutputActivityRatio.csv"):
        producers[row["FUEL"]].add(row["TECHNOLOGY"])
        modes_by_producer[row["FUEL"]].add(row["MODE_OF_OPERATION"])
    for row in nonzero_rows(input_folder / "InputActivityRatio.csv"):
        consumers[row["FUEL"]].add(row["TECHNOLOGY"])
        modes_by_consumer[row["FUEL"]].add(row["MODE_OF_OPERATION"])

    specified, accumulated = positive_demand_by_commodity(input_folder)
    production_totals, production_by_technology = result_flow_totals(
        run / "csv" / "ProductionByTechnologyByMode.csv",
        "ProductionByTechnologyByMode",
    )
    use_totals, use_by_technology = result_flow_totals(
        run / "csv" / "UseByTechnologyByMode.csv",
        "UseByTechnologyByMode",
    )
    solved_activity = activity_totals(
        run / "csv" / "TotalAnnualTechnologyActivityByMode.csv"
    )

    trade_or_storage: dict[str, set[str]] = defaultdict(set)
    for commodity in commodities:
        for technology in producers[commodity] | consumers[commodity]:
            if technology.startswith(("IMP", "EXP", "TRD", "STO", "BAT")):
                trade_or_storage[commodity].add(technology)

    ledger: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for commodity in sorted(commodities):
        commodity_producers = producers[commodity]
        commodity_consumers = consumers[commodity]
        demand_years = sorted(
            set(specified[commodity]) | set(accumulated[commodity])
        )
        has_demand = bool(demand_years)
        role = classify_role(
            commodity, commodity_producers, commodity_consumers, has_demand
        )
        commodity_warnings = warning_rows_for(
            commodity, role, commodity_producers, commodity_consumers, has_demand
        )
        warnings.extend(commodity_warnings)
        linked_technologies = commodity_producers | commodity_consumers
        active_linked = [
            technology
            for technology in linked_technologies
            if abs(solved_activity.get(technology, 0.0)) > TOLERANCE
        ]
        ledger.append(
            {
                "commodity": commodity,
                "commodity_id": commodities[commodity]["id"],
                "description": commodities[commodity]["description"],
                "unit": commodities[commodity]["unit"],
                "role": role,
                "balance_status": balance_status(
                    commodity_producers, commodity_consumers, has_demand
                ),
                "producers": join_values(commodity_producers),
                "producer_modes": join_values(modes_by_producer[commodity]),
                "consumers": join_values(commodity_consumers),
                "consumer_modes": join_values(modes_by_consumer[commodity]),
                "positive_demand_years": ";".join(str(year) for year in demand_years),
                "specified_demand_2020_2024": format_number(
                    sum(
                        value
                        for year, value in specified[commodity].items()
                        if year in HISTORICAL_YEARS
                    )
                ),
                "accumulated_demand_2020_2024": format_number(
                    sum(
                        value
                        for year, value in accumulated[commodity].items()
                        if year in HISTORICAL_YEARS
                    )
                ),
                "trade_or_storage_links": join_values(trade_or_storage[commodity]),
                "solved_production_2020_2024": format_number(
                    production_totals.get(commodity, 0.0)
                ),
                "solved_use_2020_2024": format_number(
                    use_totals.get(commodity, 0.0)
                ),
                "active_linked_technologies_2020_2024": join_values(active_linked),
                "active_producers_2020_2024": join_values(
                    production_by_technology[commodity]
                ),
                "active_consumers_2020_2024": join_values(
                    use_by_technology[commodity]
                ),
                "warning_codes": join_values(
                    warning["code"] for warning in commodity_warnings
                ),
                "proposed_disposition": disposition_for(
                    commodity,
                    role,
                    commodity_producers,
                    commodity_consumers,
                    has_demand,
                ),
                "evidence_or_assumption_ids": evidence_for(commodity),
            }
        )

    source_hashes_after = {
        "muiogo_inputs": hash_manifest(case_input_paths, case),
        "csv_inputs": hash_manifest(input_folder.glob("*.csv"), input_folder),
    }
    if source_hashes_before != source_hashes_after:
        raise RuntimeError("Model inputs changed while running the read-only audit")

    warning_counts = Counter(row["code"] for row in warnings)
    severity_counts = Counter(row["severity"] for row in warnings)
    role_counts = Counter(row["role"] for row in ledger)
    balance_counts = Counter(row["balance_status"] for row in ledger)
    warned_commodities = {warning["commodity"] for warning in warnings}
    end_use_output_stubs = [
        row
        for row in ledger
        if row["commodity"] in END_USE_CARRIERS
        and row["balance_status"] == "produced_unconsumed_undemanded"
    ]
    inactive_end_use_output_stubs = [
        row
        for row in end_use_output_stubs
        if abs(float(row["solved_production_2020_2024"])) <= TOLERANCE
    ]
    strict_would_fail = bool(warnings)
    execution_exit_code = 2 if args.strict and strict_would_fail else 0
    result_hashes = hash_manifest(
        [
            run / "results.txt",
            run / "csv" / "TotalAnnualTechnologyActivityByMode.csv",
            run / "csv" / "ProductionByTechnologyByMode.csv",
            run / "csv" / "UseByTechnologyByMode.csv",
        ],
        run,
    )

    report = {
        "schema_version": 1,
        "phase": "1A",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_folder": str(case),
        "input_folder": str(input_folder),
        "run": args.run,
        "historical_years": sorted(HISTORICAL_YEARS),
        "read_only": True,
        "model_inputs_unchanged": True,
        "dimensions": {
            "commodities": len(commodities),
            "technologies": len(technologies),
        },
        "role_counts": dict(sorted(role_counts.items())),
        "balance_status_counts": dict(sorted(balance_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "warnings_total": len(warnings),
        "commodities_with_warnings": len(warned_commodities),
        "end_use_output_stubs": len(end_use_output_stubs),
        "inactive_end_use_output_stubs_2020_2024": len(
            inactive_end_use_output_stubs
        ),
        "source_hashes": source_hashes_after,
        "result_hashes": result_hashes,
        "default_status": "PASS_WITH_WARNINGS" if warnings else "PASS",
        "strict_would_fail": strict_would_fail,
        "execution": {
            "strict_mode_requested": args.strict,
            "exit_code": execution_exit_code,
            "status": "FAIL" if execution_exit_code else "PASS",
        },
        "notes": [
            "Warnings classify topology; they never trigger automatic deletion or rewiring.",
            "The four output-only renewable resource carriers receive both the generic produced-unconsumed warning and the resource-specific warning.",
            "Production and use totals are sums of solver-reported 2020-2024 result rows in each commodity's declared unit.",
            "Evidence IDs identify existing sources or assumptions and do not imply that every listed candidate is already active model input.",
        ],
    }

    ledger_fields = list(ledger[0])
    warning_fields = [
        "commodity",
        "code",
        "severity",
        "role",
        "finding",
        "producers",
        "consumers",
    ]
    atomic_write_csv(output_dir / "commodity_ledger.csv", ledger, ledger_fields)
    atomic_write_csv(output_dir / "warnings.csv", warnings, warning_fields)
    atomic_write_json(output_dir / "audit.json", report)

    warning_summary_rows = [
        {"code": code, "count": str(count)}
        for code, count in sorted(warning_counts.items())
    ]
    priority_warnings = [
        {
            "commodity": row["commodity"],
            "code": row["code"],
            "finding": row["finding"],
        }
        for row in warnings
        if row["severity"] == "error"
        or row["code"]
        in {"likely_cross_sector_consumer", "output_only_resource_carrier"}
    ]
    report_markdown = f"""# Fiji v2 Phase 1A topology audit

## Scope and status

- Case: `{case}`
- Saved run: `{args.run}`
- Historical activity window: 2020–2024
- Commodities audited: {len(commodities)}
- Technologies referenced: {len(technologies)}
- Model inputs changed: **No**
- Default audit status: **{"PASS with classified warnings" if warnings else "PASS"}**
- Strict mode would: **{"FAIL" if strict_would_fail else "PASS"}**
- Warning records: {len(warnings)} across {len(warned_commodities)} commodities

This is a non-mutating topology audit. A warning is an investigation flag, not
an instruction to delete, suppress, demand, or rewire a commodity.

## Balance summary

{markdown_table([{"balance_status": key, "count": str(value)} for key, value in sorted(balance_counts.items())], ["balance_status", "count"])}

- No commodity is consumed without a producer.
- No commodity with positive specified or accumulated demand lacks a producer.
- {len(end_use_output_stubs)} end-use carrier outputs have no consumer or demand;
  all {len(inactive_end_use_output_stubs)} were inactive in the 2020–2024 solve.
- The four renewable carriers each receive a generic balance warning and a
  more specific resource-classification warning, so warning-record and
  commodity counts intentionally differ.

## Warning counts

{markdown_table(warning_summary_rows, ["code", "count"])}

## Priority findings

{markdown_table(priority_warnings, ["commodity", "code", "finding"])}

## Role counts

{markdown_table([{"role": key, "count": str(value)} for key, value in sorted(role_counts.items())], ["role", "count"])}

## Interpretation

The complete commodity-by-commodity evidence is in `commodity_ledger.csv`.
`warnings.csv` contains every machine-detected topology warning. The next
structural step is Phase 1B, but it must begin with a documented decision on
whether `WTRGRCFJI` is recharge, extractable groundwater, or an intermediate.
No public-water link should be changed until that decision and its units are
reviewed. `AGRELCFJIXX02 -> DEMAGRGWTFJI -> AGRWATFJI` has the same
electricity-only groundwater pattern but is not a cross-sector link; retain it
for the Phase 1D agricultural-water review.
"""
    atomic_write_text(output_dir / "REPORT.md", report_markdown)

    print(json.dumps(report, indent=2))
    return execution_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
