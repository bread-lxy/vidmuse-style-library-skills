#!/usr/bin/env python3
"""Normalize source-specific rows into canonical VidMuse EvidenceRecords."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Sequence


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class NormalizationError(RuntimeError):
    pass


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.casefold() == ".jsonl":
        rows = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise NormalizationError(f"line {line_number} is not an object")
            rows.append(item)
        return rows
    payload = json.loads(text)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise NormalizationError("input must be a JSON object, JSON array, JSONL, or CSV")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise NormalizationError(f"mapping must be an object: {path}")
    return payload


def get_path(row: dict[str, Any], dotted: str | None) -> Any:
    if not dotted:
        return None
    current: Any = row
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip()


def slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean(value))
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    result = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return result or hashlib.sha1(clean(value).encode("utf-8")).hexdigest()[:12]


def values(value: Any) -> list[str]:
    source = value if isinstance(value, list) else [] if value in (None, "") else [value]
    return sorted({clean(item) for item in source if clean(item)})


def map_object(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, list[str]]:
    return {key: values(get_path(row, path)) for key, path in mapping.items() if values(get_path(row, path))}

def mapped_values(row: dict[str, Any], item: dict[str, Any], literal_key: str, field_key: str) -> list[str]:
    field_path = item.get(field_key)
    if field_path:
        return values(get_path(row, field_path))
    return values(item.get(literal_key))


def map_anchor_memberships(row: dict[str, Any], mapping: dict[str, Any]) -> list[dict[str, str]]:
    mappings = mapping.get("anchorMembershipFields") or []
    if not mappings:
        return []
    if not isinstance(mappings, list):
        raise NormalizationError("mapping.anchorMembershipFields must be an array")
    memberships = []
    for item in mappings:
        if not isinstance(item, dict):
            raise NormalizationError("each anchorMembershipFields item must be an object")
        anchor_types = mapped_values(row, item, "anchorType", "anchorTypeField")
        anchor_names = mapped_values(row, item, "anchorName", "anchorNameField")
        bases = mapped_values(row, item, "basis", "basisField")
        if len(anchor_types) != 1 or not anchor_names or len(bases) != 1:
            raise NormalizationError("anchor membership requires one type, one basis, and at least one name")
        for anchor_name in anchor_names:
            memberships.append({"anchorType": anchor_types[0], "anchorName": anchor_name, "basis": bases[0]})
    unique = {json.dumps(item, ensure_ascii=False, sort_keys=True): item for item in memberships}
    return [unique[key] for key in sorted(unique)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difference_hash(path: Path) -> str | None:
    if path.suffix.casefold() not in IMAGE_SUFFIXES:
        return None
    try:
        from PIL import Image
        with Image.open(path) as image:
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            resized = image.convert("L").resize((9, 8), resampling)
            source = resized.get_flattened_data() if hasattr(resized, "get_flattened_data") else resized.getdata()
            pixels = list(source)
    except (ImportError, OSError, ValueError):
        return None
    bits = []
    for row in range(8):
        offset = row * 9
        bits.extend(pixels[offset + col] > pixels[offset + col + 1] for col in range(8))
    number = sum((1 << index) for index, bit in enumerate(bits) if bit)
    return f"{number:016x}"


def hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def resolve_asset(asset_root: Path, value: Any) -> tuple[Path, str]:
    text = clean(value)
    if not text:
        raise NormalizationError("missing local asset path")
    candidate = Path(text)
    path = candidate if candidate.is_absolute() else asset_root / candidate
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(asset_root.resolve()).as_posix()
    except ValueError as exc:
        raise NormalizationError(f"asset is outside asset root: {text}") from exc
    if not resolved.is_file():
        raise NormalizationError(f"asset is missing: {text}")
    return resolved, relative


def merge_dict_lists(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(left)
    for key, value in right.items():
        if key not in result or result[key] in (None, "", [], {}):
            result[key] = deepcopy(value)
        elif isinstance(result[key], list) and isinstance(value, list):
            combined = result[key] + value
            if all(isinstance(item, dict) for item in combined):
                result[key] = [json.loads(item) for item in sorted({json.dumps(item, ensure_ascii=False, sort_keys=True) for item in combined})]
            else:
                result[key] = sorted({clean(item) for item in combined if clean(item)})
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dict_lists(result[key], value)
    return result


def merge_discoveries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["evidenceId"]].append(record)
    merged = []
    for evidence_id in sorted(grouped):
        items = grouped[evidence_id]
        base = deepcopy(max(items, key=lambda item: sum(bool(value) for value in item.values())))
        for item in items:
            base["styleFeatures"] = merge_dict_lists(base["styleFeatures"], item["styleFeatures"])
            base["contentFeatures"] = merge_dict_lists(base["contentFeatures"], item["contentFeatures"])
            base["provenance"] = merge_dict_lists(base["provenance"], item["provenance"])
            base["evidenceCapabilities"] = sorted(set(base["evidenceCapabilities"] + item["evidenceCapabilities"]))
        base["discoveryCount"] = len(items)
        merged.append(base)
    return merged


def normalize(rows: list[dict[str, Any]], mapping: dict[str, Any], asset_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_name = clean(mapping.get("sourceName"))
    if not source_name:
        raise NormalizationError("mapping.sourceName is required")
    fields = mapping.get("fields") or {}
    defaults = mapping.get("defaults") or {}
    records = []
    quarantine = []

    for index, row in enumerate(rows, start=1):
        try:
            raw_id = clean(get_path(row, fields.get("id")))
            source = clean(get_path(row, fields.get("source")))
            asset, relative_asset = resolve_asset(asset_root, get_path(row, fields.get("localAssetPath")))
            identity = raw_id or source or relative_asset
            evidence_id = f"{slug(source_name)}-{slug(identity)}"
            source_group = clean(get_path(row, fields.get("sourceGroupKey"))) or f"{slug(source_name)}-unknown-group"
            context = clean(get_path(row, fields.get("contextKey"))) or f"{slug(source_group)}/unknown-context"
            independence = clean(get_path(row, fields.get("independenceKey"))) or f"{slug(source_group)}/{slug(identity)}"
            capabilities_value = get_path(row, fields.get("evidenceCapabilities"))
            capabilities = values(capabilities_value) or values(defaults.get("evidenceCapabilities"))
            if not capabilities:
                capabilities = ["static_appearance"]
            license_status = clean(get_path(row, fields.get("licenseStatus"))) or clean(defaults.get("licenseStatus")) or "unknown"
            research_only = bool(defaults.get("researchOnly", license_status in {"research_only", "unknown"}))
            if fields.get("researchOnly"):
                value = get_path(row, fields["researchOnly"])
                if isinstance(value, bool):
                    research_only = value
                elif clean(value).casefold() in {"true", "1", "yes"}:
                    research_only = True
                elif clean(value).casefold() in {"false", "0", "no"}:
                    research_only = False
            file_hash = sha256_file(asset)
            provenance = map_object(row, mapping.get("provenanceFields") or {})
            anchor_memberships = map_anchor_memberships(row, mapping)
            if anchor_memberships:
                provenance["anchorMemberships"] = anchor_memberships
            record = {
                "evidenceId": evidence_id,
                "unitType": clean(get_path(row, fields.get("unitType"))) or clean(defaults.get("unitType")) or "unknown",
                "medium": clean(get_path(row, fields.get("medium"))) or clean(defaults.get("medium")) or "unknown",
                "source": source or f"local:{relative_asset}",
                "localAssetPath": relative_asset,
                "sourceGroupKey": slug(source_group),
                "contextKey": slug(context),
                "independenceKey": slug(independence),
                "styleFeatures": map_object(row, mapping.get("styleFields") or {}),
                "contentFeatures": map_object(row, mapping.get("contentFields") or {}),
                "evidenceCapabilities": capabilities,
                "provenance": provenance,
                "licenseStatus": license_status,
                "researchOnly": research_only,
                "fileSha256": file_hash,
                "differenceHash": difference_hash(asset),
                "duplicateOf": None,
                "nearDuplicateOf": None,
            }
            records.append(record)
        except (NormalizationError, OSError, ValueError) as exc:
            quarantine.append({"rawIndex": index, "reason": str(exc), "sourceId": clean(get_path(row, fields.get("id")))})

    records = merge_discoveries(records)
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_hash[record["fileSha256"]].append(record)
    for group in by_hash.values():
        canonical = min(group, key=lambda item: item["evidenceId"])
        for item in group:
            if item is not canonical:
                item["duplicateOf"] = canonical["evidenceId"]

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if not record["duplicateOf"] and record["differenceHash"]:
            groups[record["sourceGroupKey"]].append(record)
    for group in groups.values():
        group.sort(key=lambda item: item["evidenceId"])
        for index, record in enumerate(group):
            for other in group[:index]:
                if hamming(record["differenceHash"], other["differenceHash"]) <= 4:
                    record["nearDuplicateOf"] = other["evidenceId"]
                    break
    return records, quarantine


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_quarantine(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.casefold() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        write_jsonl(path, rows)


def write_report(path: Path, rows: list[dict[str, Any]], quarantine: list[dict[str, Any]], raw_count: int) -> None:
    independent = [row for row in rows if not row["duplicateOf"] and not row["nearDuplicateOf"]]
    media = Counter(row["medium"] for row in rows)
    licenses = Counter(row["licenseStatus"] for row in rows)
    capabilities = Counter(value for row in rows for value in row["evidenceCapabilities"])
    coverage = Counter(key for row in rows for key, value in row["styleFeatures"].items() if value)
    source_groups = Counter(row["sourceGroupKey"] for row in rows)
    contexts = Counter(row["contextKey"] for row in rows)
    content_coverage = Counter(key for row in rows for key, value in row["contentFeatures"].items() if value)
    provenance_coverage = Counter(key for row in rows for key, value in row["provenance"].items() if value)
    max_source_share = max(source_groups.values(), default=0) / max(len(rows), 1)
    max_context_share = max(contexts.values(), default=0) / max(len(rows), 1)
    lines = [
        "# Evidence Data Quality",
        "",
        f"- Raw rows: {raw_count}",
        f"- Canonical evidence: {len(rows)}",
        f"- Independent evidence: {len(independent)}",
        f"- Quarantined rows: {len(quarantine)}",
        f"- Exact duplicates: {sum(bool(row['duplicateOf']) for row in rows)}",
        f"- Near duplicates: {sum(bool(row['nearDuplicateOf']) for row in rows)}",
        f"- Source groups: {len(source_groups)} (max concentration {max_source_share:.1%})",
        f"- Contexts: {len(contexts)} (max concentration {max_context_share:.1%})",
        f"- Evidence without source visual features: {sum(not any(row['styleFeatures'].values()) for row in rows)}",
        "",
        "## Medium",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(media.items()))
    lines.extend(["", "## License", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(licenses.items()))
    lines.extend(["", "## Evidence Capability", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(capabilities.items()))
    lines.extend(["", "## Style Feature Coverage", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(coverage.items()))
    lines.extend(["", "## Content Feature Coverage (excluded from clustering)", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(content_coverage.items()))
    lines.extend(["", "## Provenance Coverage (not a visual membership feature)", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(provenance_coverage.items()))
    lines.extend(["", "## Review Risks", "", "- Confirm source-group and context concentration are acceptable for the intended Anchor scopes.", "- Confirm every unknown or research-only license remains excluded from production previews.", "- Confirm model-extracted style features are visibly supported and do not copy content motifs."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize source rows into VidMuse EvidenceRecords")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--quarantine", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        rows = load_rows(args.input)
        mapping = load_json(args.mapping)
        records, quarantine = normalize(rows, mapping, args.asset_root.resolve())
        write_jsonl(args.output, records)
        write_quarantine(args.quarantine, quarantine)
        if args.report:
            write_report(args.report, records, quarantine, len(rows))
    except (OSError, json.JSONDecodeError, NormalizationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"raw": len(rows), "evidence": len(records), "quarantine": len(quarantine)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())