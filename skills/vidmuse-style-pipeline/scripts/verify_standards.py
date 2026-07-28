#!/usr/bin/env python3
"""Build or verify the VidMuse standards provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "references" / "standards-sources.json"
MANIFEST_PATH = ROOT / "references" / "standards-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def refresh(workspace_root: Path) -> int:
    config = load_json(CONFIG_PATH)
    entries = []
    failures = []
    for item in config["entries"]:
        source = workspace_root / item["sourcePath"]
        if not source.is_file():
            failures.append(f"missing source: {item['sourcePath']}")
            continue
        result = dict(item)
        result["sourceSha256"] = sha256(source)
        result["sourceBytes"] = source.stat().st_size
        if item.get("bundlePath"):
            bundled = SUITE_ROOT / item["bundlePath"]
            if not bundled.is_file():
                failures.append(f"missing bundle: {item['bundlePath']}")
                continue
            result["bundleSha256"] = sha256(bundled)
            result["bundleBytes"] = bundled.stat().st_size
            if result["sourceSha256"] != result["bundleSha256"] and not item.get("derived"):
                failures.append(f"bundle drift: {item['id']}")
        entries.append(result)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "workspaceRoot": str(workspace_root.resolve()),
        "entries": entries,
        "historicalExclusions": [
            "first-stage 284 field-shape candidates",
            "Phase 2 six legacy examples",
            "model filler and fixed aspect-ratio prompt rules",
            "Midterm text conflicting with the current human standard"
        ]
    }
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({len(entries)} entries)")
    return 0


def check(workspace_root: Path | None) -> int:
    try:
        manifest = load_json(MANIFEST_PATH)
    except FileNotFoundError:
        print("ERROR: standards-manifest.json is missing; run refresh", file=sys.stderr)
        return 1
    failures = []
    for item in manifest["entries"]:
        if item.get("bundlePath"):
            bundled = SUITE_ROOT / item["bundlePath"]
            if not bundled.is_file() or sha256(bundled) != item.get("bundleSha256"):
                failures.append(f"bundled reference drift: {item['id']}")
        if workspace_root:
            source = workspace_root / item["sourcePath"]
            if not source.is_file() or sha256(source) != item.get("sourceSha256"):
                failures.append(f"workspace source drift: {item['id']}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"PASS standards={len(manifest['entries'])} workspaceChecked={str(bool(workspace_root)).lower()}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify the VidMuse standards manifest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--workspace-root", type=Path, required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--workspace-root", type=Path)
    args = parser.parse_args(argv)
    return refresh(args.workspace_root.resolve()) if args.command == "refresh" else check(args.workspace_root.resolve() if args.workspace_root else None)


if __name__ == "__main__":
    raise SystemExit(main())