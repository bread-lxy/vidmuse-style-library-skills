#!/usr/bin/env python3
"""Build or verify the self-contained VidMuse Skill standards manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = ROOT.parent
MANIFEST_PATH = ROOT / "references" / "standards-manifest.json"
BUNDLED_REFERENCES = (
    ("clustering-rules", "vidmuse-style-concept-curation/references/style-clustering-rules.zh-CN.md"),
    ("field-standard", "vidmuse-style-record-production/references/style-library-field-standard.zh-CN.md"),
    ("decision-log", "vidmuse-style-pipeline/references/decision-log.md"),
    ("style-record-schema", "vidmuse-style-record-production/references/style-record.schema.json"),
    ("style-record-validator", "vidmuse-style-record-production/scripts/validate_style_record.py"),
    ("style-taxonomy", "vidmuse-style-record-production/references/style-library-taxonomy.json"),
    ("boundary-fixtures", "vidmuse-style-concept-curation/references/boundary-fixtures.yaml"),
    ("duplicate-review", "vidmuse-style-concept-curation/references/duplicate-high-affinity-review.zh-CN.md"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refresh() -> int:
    entries = []
    missing = []
    for identifier, relative_path in BUNDLED_REFERENCES:
        path = SUITE_ROOT / relative_path
        if not path.is_file():
            missing.append(relative_path)
            continue
        entries.append({
            "id": identifier,
            "path": relative_path,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    if missing:
        for relative_path in missing:
            print(f"ERROR: missing bundled reference: {relative_path}", file=sys.stderr)
        return 1
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scope": "self-contained-skill-bundle",
        "entries": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({len(entries)} entries)")
    return 0


def check() -> int:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print("ERROR: standards-manifest.json is missing; run refresh", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid standards manifest: {exc}", file=sys.stderr)
        return 1
    failures = []
    for item in manifest.get("entries", []):
        relative_path = item.get("path")
        path = SUITE_ROOT / relative_path if isinstance(relative_path, str) else None
        if path is None or not path.is_file():
            failures.append(f"missing bundled reference: {relative_path}")
        elif sha256(path) != item.get("sha256"):
            failures.append(f"bundled reference drift: {item.get('id', relative_path)}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"PASS standards={len(manifest.get('entries', []))}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify bundled VidMuse standards")
    parser.add_argument("command", choices=("refresh", "check"))
    args = parser.parse_args(argv)
    return refresh() if args.command == "refresh" else check()


if __name__ == "__main__":
    raise SystemExit(main())
