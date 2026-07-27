#!/usr/bin/env python3
"""Build a source-hidden, self-contained EvidenceRecord contact sheet."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Sequence


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def render(rows: list[dict[str, Any]], asset_root: Path) -> str:
    cards = []
    for item in rows:
        evidence_id = str(item.get("evidenceId") or "unknown")
        anonymous = f"E-{hashlib.sha1(evidence_id.encode('utf-8')).hexdigest()[:8]}"
        path = (asset_root / str(item.get("localAssetPath") or "")).resolve()
        if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES:
            mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            visual = f'<img src="data:{mime};base64,{data}" alt="evidence">'
        else:
            visual = '<div class="asset">Non-image evidence</div>'
        capability = ", ".join(item.get("evidenceCapabilities") or [])
        cards.append(f'<figure>{visual}<figcaption><b>{html.escape(anonymous)}</b><br>{html.escape(str(item.get("unitType") or ""))}<br>{html.escape(capability)}</figcaption></figure>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Evidence Contact Sheet</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f3f3f0}}main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}}figure{{margin:0;border:1px solid #ccc;background:#fff}}img,.asset{{width:100%;aspect-ratio:16/9;object-fit:contain;background:#111}}.asset{{display:grid;place-items:center;color:#fff}}figcaption{{padding:7px;font-size:12px}}</style></head><body><h1>Source-Hidden Evidence Contact Sheet</h1><main>{''.join(cards)}</main></body></html>'''


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an EvidenceRecord contact sheet")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=240)
    args = parser.parse_args(argv)
    try:
        rows = [item for item in load_jsonl(args.evidence) if not item.get("duplicateOf") and not item.get("nearDuplicateOf")]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render(rows[:args.limit], args.asset_root.resolve()), encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output} records={min(len(rows), args.limit)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())