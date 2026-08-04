#!/usr/bin/env python3
"""Create the checksum-covered Fiji v2.7 Fisheries portable delivery ZIP."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "docs" / "Fiji_v2.7_Fisheries"
LIVE = REPO / "WebAPP" / "DataStorage" / "Fiji_v2.7"
RESULT = LIVE / "res" / "Fisheries_v2.7" / "results.txt"
ARCHIVE = REPO / "docs" / "Fiji_v2.7_Fisheries-delivery.zip"
ARCHIVE_SHA = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")

REPRODUCTION_SCRIPTS = (
    "create_fiji_v27_fisheries.py",
    "validate_fiji_v27_fisheries_design.py",
    "run_fiji_v27_fisheries.py",
    "compare_fiji_v27_fisheries.py",
    "package_fiji_v27_fisheries.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def update_inventory() -> None:
    path = PACKAGE / "model" / "inputs" / "active_source_files.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0]) if rows else [
            "model_file",
            "role",
            "lineage_status",
            "primary_evidence_ids",
            "live_path",
        ]

    for row in rows:
        row["live_path"] = row["live_path"].replace(
            "WebAPP/DataStorage/Fiji_v2.6/",
            "WebAPP/DataStorage/Fiji_v2.7/",
        )
    if not any(row["model_file"] == "fisheries_v27_manifest.json" for row in rows):
        rows.append(
            {
                "model_file": "fisheries_v27_manifest.json",
                "role": "audit/supporting record",
                "lineage_status": "specific Fisheries v2.7 overlay",
                "primary_evidence_ids": (
                    "CALC_FSH_BOUNDARY CALC_FSH_RESIDUAL_STOCKS "
                    "CALC_FSH_SOLVER_VALIDATION"
                ),
                "live_path": (
                    "WebAPP/DataStorage/Fiji_v2.7/fisheries_v27_manifest.json"
                ),
            }
        )

    expected = {path.name for path in LIVE.glob("*.json")}
    actual = {row["model_file"] for row in rows}
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"Active source inventory mismatch: missing={missing}, extra={extra}"
        )

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_reproduction_scripts() -> None:
    target = PACKAGE / "scripts"
    target.mkdir(parents=True, exist_ok=True)
    for name in REPRODUCTION_SCRIPTS:
        shutil.copy2(REPO / "scripts" / name, target / name)


def archive_members() -> list[tuple[Path, str]]:
    members: list[tuple[Path, str]] = []
    for path in sorted(PACKAGE.rglob("*")):
        if path.is_file():
            relative = path.relative_to(PACKAGE).as_posix()
            members.append(
                (path, f"Fiji_v2.7_Fisheries/package/{relative}")
            )
    for path in sorted(LIVE.glob("*.json")):
        members.append(
            (path, f"Fiji_v2.7_Fisheries/model/source/{path.name}")
        )
    for name in ("README.md", "MODEL_FIXES.md"):
        path = LIVE / name
        members.append(
            (path, f"Fiji_v2.7_Fisheries/model/source/{path.name}")
        )
    members.append(
        (
            RESULT,
            "Fiji_v2.7_Fisheries/model/results/Fisheries_v2.7/results.txt",
        )
    )
    return members


def write_checksums() -> None:
    checksum_path = PACKAGE / "SHA256SUMS.txt"
    if checksum_path.exists():
        checksum_path.unlink()
    lines = [
        f"{sha256(path)}  {archive_name}"
        for path, archive_name in archive_members()
    ]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_archive() -> dict[str, object]:
    write_checksums()
    members = archive_members()
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="Fiji_v2.7_Fisheries-", suffix=".zip", dir=ARCHIVE.parent,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path, archive_name in members:
                archive.write(path, archive_name)
        with zipfile.ZipFile(temporary) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        temporary.replace(ARCHIVE)
    finally:
        if temporary.exists():
            temporary.unlink()

    digest = sha256(ARCHIVE)
    ARCHIVE_SHA.write_text(f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    return {
        "status": "pass",
        "archive": str(ARCHIVE),
        "archive_sha256": digest,
        "archive_size_bytes": ARCHIVE.stat().st_size,
        "member_count": len(members),
        "source_json_count": len(list(LIVE.glob("*.json"))),
        "result_sha256": sha256(RESULT),
        "excluded_generated_solver_files": [
            "data.txt",
            "data_processed.txt",
            "lp.lp",
        ],
    }


def main() -> None:
    if not PACKAGE.is_dir() or not LIVE.is_dir() or not RESULT.is_file():
        raise SystemExit("Required package, live case, or live result is missing")
    copy_reproduction_scripts()
    update_inventory()
    print(json.dumps(create_archive(), indent=2))


if __name__ == "__main__":
    main()
