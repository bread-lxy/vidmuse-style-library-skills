#!/usr/bin/env python3
"""Export approved VidMuse staging records and one-reference-image manifests."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence

from validate_style_record import STAGING_SCHEMA_PATH, InputError, load_records, load_schema, validate_records


FIELDS = ["name", "tags", "description", "analysis", "promptSample", "imageUrl"]


def slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "style"


def load_prompt_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise InputError(f"prompt line {line_number} is not an object")
        rows.append(item)
    if not rows:
        raise InputError("preview prompt source is empty")
    return rows


def validate_prompts(records: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, str]:
    by_name: dict[str, str] = {}
    for row in rows:
        name = row.get("name")
        prompt = row.get("prompt")
        if not isinstance(name, str) or not name.strip():
            raise InputError("each prompt row needs a non-empty name")
        if name in by_name:
            raise InputError(f"duplicate preview prompt row: {name}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise InputError(f"{name} must have exactly one non-empty prompt")
        if set(row) != {"name", "prompt"}:
            raise InputError(f"{name} prompt row must contain exactly name and prompt")
        by_name[name] = prompt.strip()
    record_names = {item["name"] for item in records}
    prompt_names = set(by_name)
    if record_names != prompt_names:
        missing = sorted(record_names - prompt_names)
        extra = sorted(prompt_names - record_names)
        raise InputError(f"record/prompt names differ; missing={missing} extra={extra}")
    return by_name


def write_outputs(records: list[dict[str, Any]], prompts: dict[str, str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "previews").mkdir(parents=True, exist_ok=True)
    clean_records = []
    prompt_rows = []
    manifest_rows = []
    for style_index, source in enumerate(records, start=1):
        if set(source) != set(FIELDS):
            raise InputError(f"{source.get('name', style_index)} must contain exactly the six production fields")
        record = {field: source[field] for field in FIELDS}
        if record["imageUrl"] != "":
            raise InputError(f"{record['name']} imageUrl must be empty in staging delivery")
        clean_records.append(record)
        style_slug = slug(record["name"])
        prompt = prompts[record["name"]]
        filename = f"{style_index:03d}__{style_slug}__preview.png"
        row = {"styleIndex": style_index, "name": record["name"], "slug": style_slug, "prompt": prompt, "fileName": filename}
        prompt_rows.append(row)
        manifest_rows.append(row)

    styles_path = output_dir / "styles.json"
    styles_path.write_text(json.dumps(clean_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "styles.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in clean_records:
            row = dict(record)
            row["tags"] = json.dumps(row["tags"], ensure_ascii=False)
            writer.writerow(row)
    with (output_dir / "preview-prompts.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in prompt_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (output_dir / "preview-manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = ["styleIndex", "name", "slug", "prompt", "fileName"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    reloaded = json.loads(styles_path.read_text(encoding="utf-8"))
    if reloaded != clean_records:
        raise InputError("styles.json round-trip failed")
    with (output_dir / "styles.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    if len(csv_rows) != len(clean_records):
        raise InputError("styles.csv record count differs from JSON")
    for expected, actual in zip(clean_records, csv_rows):
        actual_tags = json.loads(actual["tags"])
        for field in FIELDS:
            value = actual_tags if field == "tags" else actual[field]
            if value != expected[field]:
                raise InputError(f"styles.csv round-trip failed for {expected['name']} field {field}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export VidMuse six-field staging records and one-reference-image manifests")
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        records = load_records(args.records)
        issues = validate_records(records, schema=load_schema(STAGING_SCHEMA_PATH))
        errors = [item for item in issues if item.severity == "error"]
        warnings = [item for item in issues if item.severity == "warning"]
        if errors or (args.strict and warnings):
            for item in issues:
                print(f"[{item.severity.upper()}] {item.name} {item.field} {item.code}: {item.message}", file=sys.stderr)
            return 1
        prompts = validate_prompts(records, load_prompt_rows(args.prompts))
        write_outputs(records, prompts, args.output_dir)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"PASS records={len(records)} previews={len(records)} output={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
