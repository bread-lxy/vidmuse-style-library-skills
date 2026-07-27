#!/usr/bin/env python3
"""Validate the independent one-reference-image VidMuse preview package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence


FILE_RE = re.compile(r"^(\d{3})__([a-z0-9]+(?:-[a-z0-9]+)*)__preview\.png$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(manifest_path: Path, preview_dir: Path) -> dict[str, Any]:
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"styleIndex", "name", "slug", "prompt", "fileName"}
    if not rows:
        return {"errors": ["manifest is empty"], "warnings": [], "styles": 0, "images": 0}
    missing_columns = required - set(rows[0])
    if missing_columns:
        return {"errors": [f"missing columns: {', '.join(sorted(missing_columns))}"], "warnings": [], "styles": 0, "images": 0}
    errors: list[str] = []
    warnings: list[str] = []
    expected_files: set[str] = set()
    hashes: dict[str, str] = {}
    seen_styles: set[tuple[int, str, str]] = set()
    indexes: list[int] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            style_index = int(row["styleIndex"])
        except ValueError:
            errors.append(f"row {row_number}: styleIndex must be an integer")
            continue
        key = (style_index, row["name"], row["slug"])
        if key in seen_styles:
            errors.append(f"row {row_number}: style {style_index} {row['name']} has more than one reference image")
        seen_styles.add(key)
        indexes.append(style_index)
        expected_name = f"{style_index:03d}__{row['slug']}__preview.png"
        if row["fileName"] != expected_name or not FILE_RE.fullmatch(row["fileName"]):
            errors.append(f"row {row_number}: invalid filename {row['fileName']!r}; expected {expected_name!r}")
        if not row["prompt"].strip():
            errors.append(f"row {row_number}: prompt is empty")
        path = preview_dir / row["fileName"]
        expected_files.add(row["fileName"])
        if not path.is_file():
            errors.append(f"row {row_number}: missing image {row['fileName']}")
            continue
        try:
            from PIL import Image
            with Image.open(path) as image:
                image.verify()
        except (ImportError, OSError, ValueError) as exc:
            errors.append(f"row {row_number}: undecodable image {row['fileName']}: {exc}")
            continue
        digest = sha256(path)
        if digest in hashes:
            errors.append(f"row {row_number}: image duplicates {hashes[digest]}")
        else:
            hashes[digest] = row["fileName"]
    unique_indexes = sorted(set(indexes))
    if len(indexes) != len(unique_indexes):
        errors.append("each style index must appear exactly once")
    if unique_indexes != list(range(1, len(unique_indexes) + 1)):
        errors.append(f"style indexes are not contiguous from 1: {unique_indexes}")
    actual_files = {path.name for path in preview_dir.iterdir() if path.is_file()}
    extras = sorted(actual_files - expected_files)
    if extras:
        warnings.append(f"unmanifested files: {', '.join(extras)}")
    return {"errors": errors, "warnings": warnings, "styles": len(seen_styles), "images": len(expected_files)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one VidMuse reference image per style")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--preview-dir", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = validate(args.manifest, args.preview_dir)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload["passed"] = not payload["errors"] and (not args.strict or not payload["warnings"])
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'PASS' if payload['passed'] else 'FAIL'} styles={payload['styles']} images={payload['images']} errors={len(payload['errors'])} warnings={len(payload['warnings'])}")
    for message in payload["errors"]:
        print(f"[ERROR] {message}")
    for message in payload["warnings"]:
        print(f"[WARNING] {message}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
