#!/usr/bin/env python3
"""Build a self-contained, source-hidden VidMuse concept review packet."""

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

from validate_concepts import load_jsonl, validate

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def opaque(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:8]}"


def image_data_url(path: Path) -> str | None:
    if path.suffix.casefold() not in IMAGE_SUFFIXES or not path.is_file():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def evidence_cards(ids: list[str], evidence: dict[str, dict[str, Any]], asset_root: Path, reveal: bool) -> str:
    cards = []
    for evidence_id in ids:
        item = evidence.get(evidence_id)
        if not item:
            cards.append('<div class="card missing">Missing evidence</div>')
            continue
        asset = (asset_root / item["localAssetPath"]).resolve()
        data_url = image_data_url(asset)
        visual = f'<img src="{data_url}" alt="evidence">' if data_url else '<div class="nonimage">Non-image evidence</div>'
        label = evidence_id if reveal else opaque("E", evidence_id)
        cards.append(f'<figure class="card">{visual}<figcaption>{html.escape(label)}</figcaption></figure>')
    return "".join(cards) or '<p class="empty">No evidence assigned.</p>'


def list_html(values: list[Any]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(str(value))}</li>" for value in values) + "</ul>" if values else '<p class="empty">None.</p>'


def render_packet(evidence_rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]], asset_root: Path, reveal: bool) -> str:
    evidence = {item["evidenceId"]: item for item in evidence_rows}
    labels = {item["hypothesisId"]: (item.get("anchor", {}).get("name") if reveal else item.get("anonymousLabel", opaque("C", item["hypothesisId"]))) for item in hypotheses}
    sections = []
    for item in hypotheses:
        hypothesis_id = item["hypothesisId"]
        display_id = hypothesis_id if reveal else opaque("C", hypothesis_id)
        title = labels[hypothesis_id]
        evidence_block = item.get("evidence", {})
        signature = item.get("signature", {})
        scope = item.get("scope", {})
        invariant_text = [f"{value.get('dimension')}: {value.get('rule')}" for value in signature.get("transferableInvariants", []) if isinstance(value, dict)]
        section = [
            f'<section id="{html.escape(display_id)}">',
            f'<h2>{html.escape(str(title))}</h2>',
            f'<p class="id">{html.escape(display_id)}</p>',
            '<h3>Source-free visual signature</h3>',
            f'<p>{html.escape(str(signature.get("summary") or ""))}</p>',
            list_html(invariant_text),
            '<h3>Scope and content dependency</h3>',
            f'<p>{html.escape(json.dumps(scope, ensure_ascii=False, sort_keys=True))}</p>',
            '<h3>Allowed variation</h3>', list_html(list(signature.get("allowedVariation") or [])),
            '<h3>Excluded source motifs</h3>', list_html(list(signature.get("excludedSourceMotifs") or [])),
            '<h3>Core evidence</h3>',
            f'<div class="grid">{evidence_cards(list(evidence_block.get("coreEvidenceIds") or []), evidence, asset_root, reveal)}</div>',
            '<h3>Variation evidence</h3>',
            f'<div class="grid">{evidence_cards(list(evidence_block.get("variationEvidenceIds") or []), evidence, asset_root, reveal)}</div>',
        ]
        for boundary_index, boundary in enumerate(item.get("boundary") or [], start=1):
            status = boundary.get("status", "unknown")
            neighbor_id = str(boundary.get("neighborHypothesisId") or "unknown")
            neighbor_label = labels.get(neighbor_id, neighbor_id if reveal else opaque("C", neighbor_id))
            section.append(f'<h3>Boundary {boundary_index}: {html.escape(str(neighbor_label))} ({html.escape(str(status))})</h3>')
            section.append(list_html(list(boundary.get("distinguishingRules") or [])))
            if status == "insufficient":
                section.append(f'<p class="warning">{html.escape(str(boundary.get("insufficiencyReason") or "Insufficient evidence"))}</p>')
            else:
                section.extend([
                    '<div class="pair"><div><h4>Target side</h4>',
                    f'<div class="grid">{evidence_cards(list(boundary.get("targetEvidenceIds") or []), evidence, asset_root, reveal)}</div></div>',
                    '<div><h4>Neighbor side</h4>',
                    f'<div class="grid">{evidence_cards(list(boundary.get("neighborEvidenceIds") or []), evidence, asset_root, reveal)}</div></div></div>',
                ])
        section.append("</section>")
        sections.append("".join(section))
    mode = "REVEALED" if reveal else "SOURCE-HIDDEN"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>VidMuse Concept Review</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;color:#171717;background:#f4f4f2}}header,section{{max-width:1440px;margin:0 auto 24px}}section{{background:#fff;border:1px solid #d5d5d0;padding:18px}}h2,h3,h4{{margin:0 0 10px}}h3{{margin-top:22px;border-top:1px solid #ddd;padding-top:14px}}.id{{color:#666}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}}.card{{margin:0;border:1px solid #ccc;background:#fafafa}}.card img,.nonimage{{width:100%;aspect-ratio:16/9;object-fit:contain;background:#111}}.nonimage{{display:grid;place-items:center;color:#fff}}figcaption{{font-size:12px;padding:6px;overflow-wrap:anywhere}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.warning{{border-left:4px solid #b66a00;padding:8px;background:#fff6e8}}.empty{{color:#777}}@media(max-width:800px){{.pair{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>VidMuse Concept Review</h1><p>{mode}. Review coherence, transferability, and visible boundaries before provenance or AI recommendations.</p></header>{''.join(sections)}</body></html>'''


def write_index(path: Path, hypotheses: list[dict[str, Any]], reveal: bool) -> None:
    lines = ["# Candidate Index", "", "| Candidate | Label | Core | Variation | Boundaries |", "|---|---|---:|---:|---:|"]
    for item in hypotheses:
        public_id = item["hypothesisId"]
        display_id = public_id if reveal else opaque("C", public_id)
        label = item.get("anchor", {}).get("name") if reveal else item.get("anonymousLabel", display_id)
        block = item.get("evidence", {})
        lines.append(f"| `{display_id}` | {label} | {len(block.get('coreEvidenceIds') or [])} | {len(block.get('variationEvidenceIds') or [])} | {len(item.get('boundary') or [])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision_template(path: Path, hypotheses: list[dict[str, Any]]) -> None:
    if path.exists():
        return
    rows = []
    for item in hypotheses:
        recommendation = item.get("aiRecommendation") if isinstance(item.get("aiRecommendation"), dict) else {}
        rows.append({"hypothesisId": item["hypothesisId"], "decision": recommendation.get("outcome", "hold"), "canonicalHypothesisId": item["hypothesisId"], "resultingHypothesisIds": [], "relations": [], "reviewStatus": "ai_proposed", "evidenceActions": []})
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a self-contained VidMuse visual review packet")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--anonymous-candidates", type=Path)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reveal", action="store_true")
    args = parser.parse_args(argv)
    try:
        evidence = load_jsonl(args.evidence)
        hypotheses = load_jsonl(args.hypotheses)
        anonymous = load_jsonl(args.anonymous_candidates) if args.anonymous_candidates else None
        issues = validate(evidence, hypotheses, anonymous_candidates=anonymous)
        errors = [item for item in issues if item.severity == "error"]
        if errors:
            for item in errors:
                print(f"ERROR: {item.hypothesisId} {item.code}: {item.message}", file=sys.stderr)
            return 1
        args.output_dir.mkdir(parents=True, exist_ok=True)
        html_name = "revealed-review.html" if args.reveal else "blind-review.html"
        (args.output_dir / html_name).write_text(render_packet(evidence, hypotheses, args.asset_root.resolve(), args.reveal), encoding="utf-8")
        write_index(args.output_dir / "candidate-index.md", hypotheses, args.reveal)
        write_decision_template(args.output_dir / "decision-registry.ai-pre-review.jsonl", hypotheses)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output_dir} ({len(hypotheses)} hypotheses)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
