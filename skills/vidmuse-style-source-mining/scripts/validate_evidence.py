#!/usr/bin/env python3
"""Validate canonical VidMuse EvidenceRecords."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator


REQUIRED = {
    "evidenceId", "unitType", "medium", "source", "localAssetPath",
    "sourceGroupKey", "contextKey", "independenceKey", "styleFeatures",
    "contentFeatures", "evidenceCapabilities", "provenance", "licenseStatus",
    "researchOnly", "fileSha256", "differenceHash", "duplicateOf", "nearDuplicateOf",
}
LICENSES = {"research_only", "licensed", "generated", "public_domain", "unknown"}

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "references" / "evidence-record.schema.json"


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    record: int
    evidenceId: str
    message: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"line {line_number} is not an object")
        rows.append(item)
    if not rows:
        raise ValueError("evidence input is empty")
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(rows: list[dict[str, Any]], asset_root: Path | None) -> list[Issue]:
    issues = []
    ids = {}
    independence_keys = {}
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema)
    for index, row in enumerate(rows):
        evidence_id = str(row.get("evidenceId") or f"record-{index + 1}")
        for error in schema_validator.iter_errors(row):
            field = ".".join(str(part) for part in error.absolute_path) or "$"
            issues.append(Issue("error", f"schema.{error.validator}", index, evidence_id, f"{field}: {error.message}"))
        missing = sorted(REQUIRED - set(row))
        if missing:
            issues.append(Issue("error", "record.missing_fields", index, evidence_id, ", ".join(missing)))
        if evidence_id in ids:
            issues.append(Issue("error", "record.duplicate_id", index, evidence_id, f"duplicates record {ids[evidence_id] + 1}"))
        else:
            ids[evidence_id] = index
        independence_key = row.get("independenceKey")
        if isinstance(independence_key, str) and independence_key.strip():
            if independence_key in independence_keys:
                issues.append(Issue("warning", "record.repeated_independence_key", index, evidence_id, f"also used by record {independence_keys[independence_key] + 1}; merge repeated discoveries or justify separate units"))
            else:
                independence_keys[independence_key] = index
        for field in ("unitType", "medium", "source", "localAssetPath", "sourceGroupKey", "contextKey", "independenceKey"):
            if not isinstance(row.get(field), str) or not row.get(field, "").strip():
                issues.append(Issue("error", f"field.{field}", index, evidence_id, "must be a non-empty string"))
        if row.get("licenseStatus") not in LICENSES:
            issues.append(Issue("error", "license.invalid", index, evidence_id, f"invalid licenseStatus: {row.get('licenseStatus')}"))
        if not isinstance(row.get("researchOnly"), bool):
            issues.append(Issue("error", "license.research_only_type", index, evidence_id, "researchOnly must be boolean"))
        if row.get("licenseStatus") in {"research_only", "unknown"} and row.get("researchOnly") is False:
            issues.append(Issue("error", "license.unsafe_preview", index, evidence_id, "research-only or unknown evidence cannot be preview-safe"))
        capabilities = row.get("evidenceCapabilities")
        if not isinstance(capabilities, list) or not capabilities:
            issues.append(Issue("error", "capability.missing", index, evidence_id, "at least one evidence capability is required"))

        for field in ("styleFeatures", "contentFeatures", "provenance"):
            if not isinstance(row.get(field), dict):
                issues.append(Issue("error", f"field.{field}", index, evidence_id, "must be an object"))
        style = row.get("styleFeatures") if isinstance(row.get("styleFeatures"), dict) else {}
        content = row.get("contentFeatures") if isinstance(row.get("contentFeatures"), dict) else {}
        overlap = sorted(set(style) & set(content))
        if overlap:
            issues.append(Issue("error", "channels.overlap", index, evidence_id, f"style/content keys overlap: {', '.join(overlap)}"))
        if not any(style.values()):
            issues.append(Issue("warning", "style.no_features", index, evidence_id, "no source style features are available; use visual extraction before clustering"))
        if asset_root and isinstance(row.get("localAssetPath"), str):
            path = (asset_root / row["localAssetPath"]).resolve()
            try:
                path.relative_to(asset_root.resolve())
            except ValueError:
                issues.append(Issue("error", "asset.outside_root", index, evidence_id, row["localAssetPath"]))
            else:

                if not path.is_file():
                    issues.append(Issue("error", "asset.missing", index, evidence_id, row["localAssetPath"]))
                elif isinstance(row.get("fileSha256"), str) and sha256_file(path) != row["fileSha256"]:
                    issues.append(Issue("error", "asset.hash_mismatch", index, evidence_id, row["localAssetPath"]))

    id_set = set(ids)
    for index, row in enumerate(rows):
        evidence_id = str(row.get("evidenceId") or f"record-{index + 1}")
        for field in ("duplicateOf", "nearDuplicateOf"):
            target = row.get(field)
            if target is not None and target not in id_set:
                issues.append(Issue("error", "dedupe.unknown_target", index, evidence_id, f"{field}={target}"))
            if target == evidence_id:
                issues.append(Issue("error", "dedupe.self_reference", index, evidence_id, field))
    return sorted(issues, key=lambda item: (item.record, item.severity != "error", item.code))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate VidMuse EvidenceRecords")
    parser.add_argument("path", type=Path)
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        rows = load_jsonl(args.path)
        issues = validate(rows, args.asset_root.resolve() if args.asset_root else None)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    errors = [item for item in issues if item.severity == "error"]
    warnings = [item for item in issues if item.severity == "warning"]
    passed = not errors and (not args.strict or not warnings)
    payload = {"passed": passed, "records": len(rows), "errorCount": len(errors), "warningCount": len(warnings), "issues": [asdict(item) for item in issues]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if passed else 'FAIL'} records={len(rows)} errors={len(errors)} warnings={len(warnings)}")
        for item in issues:
            print(f"[{item.severity.upper()}] record={item.record + 1} id={item.evidenceId} {item.code}: {item.message}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())