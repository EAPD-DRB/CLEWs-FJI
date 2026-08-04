#!/usr/bin/env python3
"""Validate Fiji v2.9 ledgers against retained evidence and live source JSON."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
if SCRIPT.parent.name == "scripts" and SCRIPT.parent.parent.parent.name == "docs":
    PACKAGE = SCRIPT.parent.parent
    REPO = SCRIPT.parents[3]
else:
    REPO = SCRIPT.parents[1]
    PACKAGE = REPO / "docs" / "Fiji_v2.9_Population_Crop_Fisheries_Trade"

LIVE = REPO / "WebAPP" / "DataStorage" / "Fiji_v2.9"
V28 = REPO / "WebAPP" / "DataStorage" / "Fiji_v2.8"
YEARS = [str(year) for year in range(2020, 2051)]
SCENARIO = "SC_0"
AUTHORITATIVE_FILES = (
    "genData.json",
    "RYC.json",
    "RYT.json",
    "RT.json",
    "RYTCM.json",
    "RYTM.json",
    "RYTTs.json",
)

CROPS = {
    "CAS": ("COM_nj0y1", "TEC_imp_crop_cas", "CRPCAS", "IMPCRPCAS"),
    "YAM": ("COM_kdi0c", "TEC_imp_crop_yam", "CRPYAM", "IMPCRPYAM"),
    "CON": ("COM_u8mne", "TEC_imp_crop_con", "CRPCON", "IMPCRPCON"),
    "OTH": ("COM_hqpyh", "TEC_imp_crop_oth", "CRPOTH", "IMPCRPOTH"),
    "SGC": ("COM_phase1d_sgcproc", "TEC_imp_sugar_fji", "SGCPROCFJI", "IMPSUGFJI"),
}

FISH_COMMODITIES = {
    "COM_fsh_cap": "FSHCAPSERV",
    "COM_fsh_aq": "FSHAQSERV",
    "COM_fsh_post": "FSHPOSTSERV",
    "COM_fsh_raw": "FSHRAW",
    "COM_fsh_food": "FSHFOOD",
}
FISH_TECHNOLOGIES = {
    "TEC_fsh_cap_harv": "FSHCAPHARV",
    "TEC_fsh_aq_harv": "FSHAQHARV",
    "TEC_fsh_post_prc": "FSHPOSTPRC",
    "TEC_imp_fsh_food": "IMPFSHFOOD",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def row_for(data: dict[str, Any], parameter: str, **identity: Any) -> dict[str, Any]:
    rows = [
        row
        for row in data[parameter][SCENARIO]
        if all(row.get(field) == value for field, value in identity.items())
    ]
    if len(rows) != 1:
        raise AssertionError(
            f"{parameter}/{identity}: expected exactly one row; found {len(rows)}"
        )
    return rows[0]


class Audit:
    def __init__(self) -> None:
        self.checks = 0
        self.failures: list[dict[str, Any]] = []

    def equal(self, label: str, actual: Any, expected: Any) -> None:
        self.checks += 1
        if actual != expected:
            self.failures.append(
                {"check": label, "actual": actual, "expected": expected}
            )

    def close(
        self, label: str, actual: Any, expected: Any, tolerance: float = 1e-12
    ) -> None:
        self.checks += 1
        try:
            valid = math.isclose(
                float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance
            )
        except (TypeError, ValueError):
            valid = False
        if not valid:
            self.failures.append(
                {
                    "check": label,
                    "actual": actual,
                    "expected": expected,
                    "absolute_tolerance": tolerance,
                }
            )

    def series(
        self,
        label: str,
        actual: dict[str, Any],
        expected: dict[str, Any],
        tolerance: float = 1e-12,
    ) -> None:
        for year in YEARS:
            self.close(f"{label}/{year}", actual[year], expected[year], tolerance)


def calculation_outputs() -> dict[str, Any]:
    rows = read_csv(PACKAGE / "data_sources" / "CALCULATIONS.csv")
    outputs: dict[str, Any] = {}
    for row in rows:
        value = row["output_value"]
        try:
            outputs[row["calculation_id"]] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            outputs[row["calculation_id"]] = value
    return outputs


def validate() -> dict[str, Any]:
    audit = Audit()
    crop = read_json(V28 / "population_crop_trade_v28_manifest.json")
    fish = read_json(LIVE / "population_fisheries_trade_v29_manifest.json")
    final = read_json(LIVE / "validation_population_fisheries_trade_v29_final.json")
    calculations = calculation_outputs()

    config = (PACKAGE / "config" / "config.yaml").read_text(encoding="utf-8")
    for line in (
        "country: Fiji",
        "iso3: FJI",
        "case: Fiji_v2.9",
        "scenario: SC_0",
        "horizon: 2020-2050",
        "live_case: WebAPP/DataStorage/Fiji_v2.9",
    ):
        audit.equal(f"config/{line.split(':', 1)[0]}", line in config, True)

    copied_files = {
        REPO / "scripts" / "data" / "fiji_v28_population_crop_trade.json": PACKAGE
        / "data_sources"
        / "snapshots"
        / "fiji_v28_population_crop_trade.json",
        REPO / "scripts" / "data" / "fiji_v29_population_fisheries_trade.json": PACKAGE
        / "data_sources"
        / "snapshots"
        / "fiji_v29_population_fisheries_trade.json",
        V28 / "population_crop_trade_v28_manifest.json": PACKAGE
        / "model"
        / "inputs"
        / "population_crop_trade_v28_manifest.json",
        LIVE / "population_fisheries_trade_v29_manifest.json": PACKAGE
        / "model"
        / "inputs"
        / "population_fisheries_trade_v29_manifest.json",
        V28 / "validation_population_crop_trade_v28_final.json": PACKAGE
        / "validation"
        / "population_crop_trade_v28_final.json",
        LIVE / "validation_population_fisheries_trade_v29_live_design.json": PACKAGE
        / "validation"
        / "population_fisheries_trade_v29_source.json",
        LIVE / "validation_population_fisheries_trade_v29_live_generated_design.json": PACKAGE
        / "validation"
        / "population_fisheries_trade_v29_generated.json",
        LIVE / "validation_population_fisheries_trade_v29_live_solve.json": PACKAGE
        / "validation"
        / "population_fisheries_trade_v29_live_solve.json",
        LIVE / "validation_population_fisheries_trade_v29_final.json": PACKAGE
        / "validation"
        / "population_fisheries_trade_v29_final.json",
    }
    copied_hashes: dict[str, dict[str, Any]] = {}
    for source, retained in copied_files.items():
        source_hash = sha256(source)
        retained_hash = sha256(retained) if retained.is_file() else None
        audit.equal(f"retained-copy/{retained.name}", retained_hash, source_hash)
        copied_hashes[retained.relative_to(PACKAGE).as_posix()] = {
            "source": source.relative_to(REPO).as_posix(),
            "sha256": retained_hash,
            "matches_source": retained_hash == source_hash,
        }

    required_calculations = {
        "CALC_FOOD_POPULATION_FJI_2020_2050": fish["population_people"],
        "CALC_CROP_V28_FINAL_DEMAND": crop["final_demand_mt"],
        "CALC_CROP_V28_IMPORT_FLOOR": crop["minimum_import_mt"],
        "CALC_FISH_V29_FINAL_DEMAND": fish["final_demand_mt"],
        "CALC_FISH_V29_IMPORT_FLOOR": fish["minimum_import_mt"],
        "CALC_FISH_V29_CAPTURE_INTENSITY": fish["service_intensity"][
            "capture_pj_per_mt"
        ],
        "CALC_FISH_V29_AQUACULTURE_INTENSITY": fish["service_intensity"][
            "aquaculture_pj_per_mt"
        ],
        "CALC_FISH_V29_POST_INTENSITY": fish["service_intensity"][
            "post_pj_per_mt"
        ],
    }
    for calculation_id, expected in required_calculations.items():
        audit.equal(
            f"calculation-present/{calculation_id}",
            calculation_id in calculations,
            True,
        )
        if calculation_id not in calculations:
            continue
        actual = calculations[calculation_id]
        if isinstance(expected, dict):
            if expected and set(expected) == set(YEARS):
                audit.series(f"ledger-output/{calculation_id}", actual, expected)
            else:
                for key, value in expected.items():
                    audit.series(
                        f"ledger-output/{calculation_id}/{key}", actual[key], value
                    )
        else:
            audit.close(f"ledger-output/{calculation_id}", actual, expected)

    ledgers = {
        name: read_csv(PACKAGE / "data_sources" / f"{name}.csv")
        for name in ("SOURCES", "ASSUMPTIONS", "MODEL_MAP", "GAPS", "CHANGES")
    }
    required_ids = {
        "SOURCES": {
            "SRC_FOOD_UN_WPP2024_FJI",
            "SRC_FOOD_FAOSTAT_FBS_FIJI_2021_23",
            "SRC_FOOD_COMTRADE_CROPS_FJI_2025",
            "SRC_FOOD_COMTRADE_FISH_FJI_2025",
            "SRC_FIJI_V28_VALIDATION",
            "SRC_FIJI_V29_VALIDATION",
        },
        "ASSUMPTIONS": {
            "ASM_FOOD_PER_CAPITA_CONSTANT",
            "ASM_FOOD_TOURISM_EXCLUDED",
            "ASM_CROP_IMPORT_BACKSTOP",
            "ASM_FISH_IMPORT_BACKSTOP",
            "ASM_FISH_RETAINED_IMPORT_METHOD",
            "ASM_FISH_RAW_FOOD_ONE_TO_ONE",
        },
        "MODEL_MAP": {
            "MAP_CROP_V28_FINAL_DEMAND",
            "MAP_CROP_V28_IMPORT_FLOOR",
            "MAP_FISH_V29_FINAL_DEMAND",
            "MAP_FISH_V29_IMPORT_FLOOR",
            "MAP_FISH_V29_MASS_RATIOS",
            "MAP_FISH_V29_SHOCK_VALIDATION",
        },
        "CHANGES": {"CHG_CROP_POP_TRADE_V28", "CHG_FSH_POP_TRADE_V29"},
    }
    id_fields = {
        "SOURCES": "source_id",
        "ASSUMPTIONS": "assumption_id",
        "MODEL_MAP": "map_id",
        "CHANGES": "change_id",
    }
    for ledger, wanted in required_ids.items():
        present = {row[id_fields[ledger]] for row in ledgers[ledger]}
        for item in wanted:
            audit.equal(f"ledger-id/{ledger}/{item}", item in present, True)
    gap_items = {row["item"] for row in ledgers["GAPS"]}
    for phrase in (
        "nutritional requirement",
        "crop export re-export",
        "fish market-weight",
        "capture",
        "aquaculture",
    ):
        audit.equal(
            f"gap-coverage/{phrase}",
            any(phrase in item.lower() for item in gap_items),
            True,
        )

    maps = {row["map_id"]: row for row in ledgers["MODEL_MAP"]}
    for map_id in (
        "MAP_CROP_DEMAND_CAS",
        "MAP_CROP_DEMAND_YAM",
        "MAP_CROP_DEMAND_CON",
        "MAP_CROP_DEMAND_OTH",
    ):
        audit.equal(
            f"supersession/{map_id}",
            maps[map_id]["superseded_by"],
            "CHG_CROP_POP_TRADE_V28",
        )
    for map_id in (
        "MAP_FSH_DEMAND_CAPTURE",
        "MAP_FSH_DEMAND_AQUACULTURE",
        "MAP_FSH_DEMAND_POSTHARVEST",
    ):
        audit.equal(
            f"supersession/{map_id}",
            maps[map_id]["superseded_by"],
            "CHG_FSH_POP_TRADE_V29",
        )

    gen = read_json(LIVE / "genData.json")
    ryc = read_json(LIVE / "RYC.json")
    ryt = read_json(LIVE / "RYT.json")
    rt = read_json(LIVE / "RT.json")
    ratios = read_json(LIVE / "RYTCM.json")
    modes = read_json(LIVE / "RYTM.json")
    timeslices = read_json(LIVE / "RYTTs.json")
    tech_names = {row["TechId"]: row["Tech"] for row in gen["osy-tech"]}
    comm_names = {row["CommId"]: row["Comm"] for row in gen["osy-comm"]}

    for crop_id, (comm_id, tech_id, comm_name, tech_name) in CROPS.items():
        audit.equal(f"crop-commodity-name/{comm_id}", comm_names.get(comm_id), comm_name)
        audit.equal(f"crop-import-tech-name/{tech_id}", tech_names.get(tech_id), tech_name)
        audit.series(
            f"live/RYC/AAD/{comm_id}",
            row_for(ryc, "AAD", CommId=comm_id),
            crop["final_demand_mt"][crop_id],
        )
        audit.series(
            f"live/RYT/TAL/{tech_id}",
            row_for(ryt, "TAL", TechId=tech_id),
            crop["minimum_import_mt"][crop_id],
        )
        for year in YEARS:
            audit.close(
                f"live/RYT/TAU/{tech_id}/{year}",
                row_for(ryt, "TAU", TechId=tech_id)[year],
                999999.0,
            )
            audit.close(
                f"live/RYTM/VC/{tech_id}/1/{year}",
                row_for(modes, "VC", TechId=tech_id, MoId=1)[year],
                10.0,
            )
        audit.close(
            f"live/RT/OL/{tech_id}", rt["OL"][SCENARIO][0][tech_id], 1.0
        )
        audit.close(
            f"live/RT/CAU/{tech_id}", rt["CAU"][SCENARIO][0][tech_id], 1.0
        )
        output = row_for(ratios, "OAR", TechId=tech_id, CommId=comm_id, MoId=1)
        for year in YEARS:
            audit.close(f"live/RYTCM/OAR/{tech_id}/{year}", output[year], 1.0)

    for comm_id, comm_name in FISH_COMMODITIES.items():
        audit.equal(f"fish-commodity-name/{comm_id}", comm_names.get(comm_id), comm_name)
    for tech_id, tech_name in FISH_TECHNOLOGIES.items():
        audit.equal(f"fish-technology-name/{tech_id}", tech_names.get(tech_id), tech_name)

    audit.series(
        "live/RYC/AAD/COM_fsh_food",
        row_for(ryc, "AAD", CommId="COM_fsh_food"),
        fish["final_demand_mt"],
    )
    for comm_id in ("COM_fsh_cap", "COM_fsh_aq", "COM_fsh_post", "COM_fsh_raw"):
        for parameter in ("AAD", "SAD"):
            row = row_for(ryc, parameter, CommId=comm_id)
            for year in YEARS:
                audit.close(f"live/RYC/{parameter}/{comm_id}/{year}", row[year], 0.0)
    food_sad = row_for(ryc, "SAD", CommId="COM_fsh_food")
    for year in YEARS:
        audit.close(f"live/RYC/SAD/COM_fsh_food/{year}", food_sad[year], 0.0)

    ratio_spec = {
        "TEC_fsh_cap_harv": (
            {"COM_fsh_cap": fish["service_intensity"]["capture_pj_per_mt"]},
            "COM_fsh_raw",
        ),
        "TEC_fsh_aq_harv": (
            {"COM_fsh_aq": fish["service_intensity"]["aquaculture_pj_per_mt"]},
            "COM_fsh_raw",
        ),
        "TEC_fsh_post_prc": (
            {
                "COM_fsh_raw": fish["service_intensity"]["raw_mt_per_food_mt"],
                "COM_fsh_post": fish["service_intensity"]["post_pj_per_mt"],
            },
            "COM_fsh_food",
        ),
        "TEC_imp_fsh_food": ({}, "COM_fsh_food"),
    }
    for tech_id, (inputs, output_comm) in ratio_spec.items():
        tal_expected = (
            fish["minimum_import_mt"]
            if tech_id == "TEC_imp_fsh_food"
            else {year: 0.0 for year in YEARS}
        )
        audit.series(
            f"live/RYT/TAL/{tech_id}",
            row_for(ryt, "TAL", TechId=tech_id),
            tal_expected,
        )
        for year in YEARS:
            audit.close(
                f"live/RYT/TAU/{tech_id}/{year}",
                row_for(ryt, "TAU", TechId=tech_id)[year],
                999999.0,
            )
            audit.close(
                f"live/RYT/AF/{tech_id}/{year}",
                row_for(ryt, "AF", TechId=tech_id)[year],
                1.0,
            )
            audit.close(
                f"live/RYT/CC/{tech_id}/{year}",
                row_for(ryt, "CC", TechId=tech_id)[year],
                1e-6,
                1e-15,
            )
            audit.close(
                f"live/RYTM/VC/{tech_id}/1/{year}",
                row_for(modes, "VC", TechId=tech_id, MoId=1)[year],
                200.0 if tech_id == "TEC_imp_fsh_food" else 0.0,
            )
        for comm_id, wanted in inputs.items():
            row = row_for(ratios, "IAR", TechId=tech_id, CommId=comm_id, MoId=1)
            for year in YEARS:
                audit.close(
                    f"live/RYTCM/IAR/{tech_id}/{comm_id}/{year}", row[year], wanted
                )
        output = row_for(
            ratios, "OAR", TechId=tech_id, CommId=output_comm, MoId=1
        )
        for year in YEARS:
            audit.close(
                f"live/RYTCM/OAR/{tech_id}/{output_comm}/{year}", output[year], 1.0
            )
        for row in timeslices["CF"][SCENARIO]:
            if row.get("TechId") == tech_id:
                for year in YEARS:
                    audit.close(
                        f"live/RYTTs/CF/{tech_id}/{row['TsId']}/{year}",
                        row[year],
                        1.0,
                    )
        audit.close(f"live/RT/OL/{tech_id}", rt["OL"][SCENARIO][0][tech_id], 1.0)
        audit.close(
            f"live/RT/CAU/{tech_id}", rt["CAU"][SCENARIO][0][tech_id], 1.0
        )

    live_hashes: dict[str, str] = {}
    for filename in AUTHORITATIVE_FILES:
        current_hash = sha256(LIVE / filename)
        live_hashes[filename] = current_hash
        audit.equal(
            f"authoritative-source-hash/{filename}",
            current_hash,
            final["authoritative_source_hashes"][filename]["live"],
        )
    audit.equal("final-validation/status", final["status"], "pass")
    for check, passed in final["required_checks"].items():
        audit.equal(f"final-validation/required-check/{check}", passed, True)
    audit.close("final-validation/live-objective", final["live"]["objective"], 4170.87205658)
    audit.equal(
        "final-validation/live-matrix",
        final["live"]["matrix"],
        {"rows": 178353, "columns": 137090, "nonzeros": 743918, "objrow_nonzeros": 26288},
    )

    return {
        "status": "pass" if not audit.failures else "fail",
        "case": "Fiji_v2.9",
        "package": PACKAGE.relative_to(REPO).as_posix(),
        "live_case": LIVE.relative_to(REPO).as_posix(),
        "checks": audit.checks,
        "failure_count": len(audit.failures),
        "failures": audit.failures,
        "retained_copy_hashes": copied_hashes,
        "authoritative_live_source_hashes": live_hashes,
        "verified_scope": [
            "six-ledger identifiers and supersession",
            "retained input snapshots, manifests and validation reports",
            "population, crop demand/import and fish demand/import calculation outputs",
            "live crop final demand and import backstops",
            "live fish commodities, technologies, final demand, import floor, ratios, costs and envelopes",
            "authoritative source hashes and final solver validation",
        ],
        "documentation_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PACKAGE / "validation" / "ledger_live_consistency.json",
    )
    args = parser.parse_args()
    report = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
