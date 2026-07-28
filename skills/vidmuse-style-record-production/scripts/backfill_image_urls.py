#!/usr/bin/env python3
"""Backfill verified preview-image URLs into VidMuse six-field deliveries."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


FIELDS = ["name", "tags", "description", "analysis", "promptSample", "imageUrl"]
MAP_FIELDS = {"styleIndex", "name", "fileName", "imageUrl"}
FORBIDDEN_URL_PARTS = ("/work/", "/tmp/", "aion-runtime-", "aion-user-base-")


class BackfillError(ValueError):
    pass


def load_json_array(path: Path, label: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or not payload:
        raise BackfillError(f"{label} must be a non-empty JSON array")
    if not all(isinstance(item, dict) for item in payload):
        raise BackfillError(f"{label} must contain only JSON objects")
    return payload


def load_preview_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"styleIndex", "name", "fileName"}
    if not rows:
        raise BackfillError("preview manifest is empty")
    if not required.issubset(rows[0]):
        raise BackfillError(f"preview manifest must contain {sorted(required)}")
    return rows


def validate_url_shape(url: str, file_name: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise BackfillError(f"{file_name} imageUrl must be an absolute HTTPS URL")
    lowered = unquote(parsed.path).casefold()
    if any(part in lowered for part in FORBIDDEN_URL_PARTS):
        raise BackfillError(f"{file_name} imageUrl exposes a local runtime path")
    if Path(unquote(parsed.path)).name != file_name:
        raise BackfillError(f"{file_name} does not match the final imageUrl path")


def validate_mapping(
    records: list[dict[str, Any]],
    manifest_rows: list[dict[str, str]],
    mapping_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not (len(records) == len(manifest_rows) == len(mapping_rows)):
        raise BackfillError(
            "record, preview-manifest, and URL-map counts differ: "
            f"{len(records)}, {len(manifest_rows)}, {len(mapping_rows)}"
        )
    normalized: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for index, (record, manifest, mapping) in enumerate(
        zip(records, manifest_rows, mapping_rows), start=1
    ):
        if set(record) != set(FIELDS):
            raise BackfillError(f"record {index} must contain exactly the six production fields")
        if record["imageUrl"] != "":
            raise BackfillError(f"{record['name']} source imageUrl must be empty")
        if set(mapping) != MAP_FIELDS:
            raise BackfillError(f"URL-map row {index} must contain exactly {sorted(MAP_FIELDS)}")
        try:
            manifest_index = int(manifest["styleIndex"])
        except (TypeError, ValueError) as exc:
            raise BackfillError(f"preview-manifest row {index} has an invalid styleIndex") from exc
        if manifest_index != index or mapping["styleIndex"] != index:
            raise BackfillError(f"styleIndex mismatch at row {index}")
        expected_name = record["name"]
        expected_file = manifest["fileName"]
        if manifest["name"] != expected_name or mapping["name"] != expected_name:
            raise BackfillError(f"name mismatch at row {index}: expected {expected_name}")
        if mapping["fileName"] != expected_file:
            raise BackfillError(f"fileName mismatch at row {index}: expected {expected_file}")
        url = mapping["imageUrl"]
        if not isinstance(url, str) or not url:
            raise BackfillError(f"{expected_name} imageUrl is empty")
        validate_url_shape(url, expected_file)
        if url.casefold() in seen_urls:
            raise BackfillError(f"duplicate imageUrl: {url}")
        seen_urls.add(url.casefold())
        normalized.append(
            {
                "styleIndex": index,
                "name": expected_name,
                "fileName": expected_file,
                "imageUrl": url,
            }
        )
    return normalized


def image_signature(content: bytes) -> str | None:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def check_url(url: str, file_name: str, timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Range": "bytes=0-31",
            "User-Agent": "VidMuseStyleBackfill/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            content_type = response.headers.get_content_type()
            content = response.read(32)
    except Exception as exc:
        raise BackfillError(f"{file_name} imageUrl is unreachable: {exc}") from exc
    if status not in {200, 206}:
        raise BackfillError(f"{file_name} imageUrl returned HTTP {status}")
    if not content_type.startswith("image/"):
        raise BackfillError(f"{file_name} returned {content_type}, not image/*")
    signature = image_signature(content)
    if signature is None:
        raise BackfillError(f"{file_name} response has no recognized image signature")
    expected = Path(file_name).suffix.casefold().lstrip(".")
    if expected == "jpg":
        expected = "jpeg"
    if expected in {"png", "jpeg", "webp"} and signature != expected:
        raise BackfillError(
            f"{file_name} extension expects {expected}, but response signature is {signature}"
        )
    return {
        "styleIndex": None,
        "fileName": file_name,
        "imageUrl": url,
        "httpStatus": status,
        "contentType": content_type,
        "signature": signature,
        "bytesSampled": len(content),
        "valid": True,
    }


def backfill_records(
    records: list[dict[str, Any]], mapping_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record, mapping in zip(records, mapping_rows):
        current = {field: record[field] for field in FIELDS}
        current["imageUrl"] = mapping["imageUrl"]
        output.append(current)
    return output


def write_outputs(
    output_dir: Path,
    records: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    validations: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    styles_path = output_dir / "styles.json"
    styles_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "styles.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for source in records:
            row = dict(source)
            row["tags"] = json.dumps(row["tags"], ensure_ascii=False)
            writer.writerow(row)
    (output_dir / "image-url-map.json").write_text(
        json.dumps(mapping_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "url-validation.json").write_text(
        json.dumps(validations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if json.loads(styles_path.read_text(encoding="utf-8")) != records:
        raise BackfillError("styles.json round-trip failed")
    with (output_dir / "styles.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        csv_rows = list(csv.DictReader(handle))
    if len(csv_rows) != len(records):
        raise BackfillError("styles.csv record count differs from JSON")
    for expected, actual in zip(records, csv_rows):
        actual_tags = json.loads(actual["tags"])
        for field in FIELDS:
            value = actual_tags if field == "tags" else actual[field]
            if value != expected[field]:
                raise BackfillError(
                    f"styles.csv round-trip failed for {expected['name']} field {field}"
                )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Strictly map verified preview URLs into VidMuse six-field JSON/CSV"
    )
    parser.add_argument("--styles", type=Path, required=True)
    parser.add_argument("--preview-manifest", type=Path, required=True)
    parser.add_argument("--url-map", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--skip-url-check",
        action="store_true",
        help="skip network verification; never use for a final backfill",
    )
    args = parser.parse_args(argv)
    try:
        records = load_json_array(args.styles, "styles")
        manifest_rows = load_preview_manifest(args.preview_manifest)
        mapping_rows = validate_mapping(
            records,
            manifest_rows,
            load_json_array(args.url_map, "URL map"),
        )
        validations: list[dict[str, Any]] = []
        if not args.skip_url_check:
            for row in mapping_rows:
                result = check_url(row["imageUrl"], row["fileName"], args.timeout)
                result["styleIndex"] = row["styleIndex"]
                validations.append(result)
        else:
            validations = [
                {
                    "styleIndex": row["styleIndex"],
                    "fileName": row["fileName"],
                    "imageUrl": row["imageUrl"],
                    "valid": None,
                    "reason": "network verification skipped",
                }
                for row in mapping_rows
            ]
        write_outputs(
            args.output_dir,
            backfill_records(records, mapping_rows),
            mapping_rows,
            validations,
        )
    except (OSError, json.JSONDecodeError, BackfillError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    checked = 0 if args.skip_url_check else len(mapping_rows)
    print(
        f"PASS records={len(mapping_rows)} checkedUrls={checked} output={args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
