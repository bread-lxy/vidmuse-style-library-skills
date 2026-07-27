#!/usr/bin/env python3
"""Validate current VidMuse six-field style records.

The JSON Schema owns structural constraints. This module adds deterministic
semantic lint and optional preview-image checks that JSON Schema cannot express
cleanly. It intentionally does not attempt to prove artistic distinctiveness.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT.parent / "references" / "style-record.schema.json"
STAGING_SCHEMA_PATH = ROOT.parent / "references" / "style-record.staging.schema.json"
TAXONOMY_PATH = ROOT.parent / "references" / "style-library-taxonomy.json"


def load_visual_form_vocabulary(path: Path = TAXONOMY_PATH) -> tuple[set[str], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    vocabulary = payload.get("visual_form_vocabulary") or {}
    canonical: set[str] = set()
    aliases: dict[str, str] = {}
    for canonical_name, alias_values in vocabulary.items():
        canonical.add(canonical_name.casefold().strip())
        for alias in alias_values:
            aliases[str(alias).casefold().strip()] = canonical_name
    return canonical, aliases


VISUAL_FORM_TAGS, VISUAL_FORM_ALIASES = load_visual_form_vocabulary()

GENERIC_NAME_TOKENS = {
    "aesthetic",
    "beautiful",
    "cinematic",
    "cool",
    "dreamy",
    "emotional",
    "healing",
    "look",
    "modern",
    "mood",
    "nostalgic",
    "romantic",
    "soft",
    "style",
    "visual",
}
GENERIC_TAGS = {
    "aesthetic",
    "beautiful",
    "cinematic",
    "dreamy",
    "emotional",
    "high quality",
    "nostalgic",
    "romantic",
    "soft",
    "style",
}
ANCHOR_SUFFIXES = {"aesthetic", "cinematic", "inspired", "look", "style", "visuals"}

MODEL_RE = re.compile(
    r"\b(?:stable\s+diffusion|midjourney|seedream(?:\s*\d+(?:\.\d+)?)?|"
    r"nano\s+banana|imagen(?:\s*\d+)?|flux(?:\.\d+)?|dall[- ]?e(?:\s*\d+)?|"
    r"sdxl|comfyui|runway\s+gen[- ]?\d+|kling\s*\d+(?:\.\d+)?|"
    r"veo\s*\d+(?:\.\d+)?|sora\s*\d*)\b",
    re.IGNORECASE,
)
QUALITY_RE = re.compile(
    r"\b(?:masterpiece|best\s+quality|high\s+quality|ultra[- ]?detailed|"
    r"award[- ]winning|trending\s+on\s+artstation)\b",
    re.IGNORECASE,
)
WEIGHT_RE = re.compile(
    r"(?:\([^()]*:\s*\d+(?:\.\d+)?\)|\b[\w-]+::\d+(?:\.\d+)?|--\w+)",
    re.IGNORECASE,
)
PARAMETER_RE = re.compile(
    r"\b(?:cfg(?:\s+scale)?|sampler|steps?|seed)\s*[:=]\s*[\w.-]+",
    re.IGNORECASE,
)
RESOLUTION_RE = re.compile(
    r"(?:\b\d{3,5}\s*[x×]\s*\d{3,5}\b|\b(?:4k|8k|16k)\b)",
    re.IGNORECASE,
)
ASPECT_RE = re.compile(
    r"(?:\baspect\s+ratio\b|\b(?:16\s*:\s*9|9\s*:\s*16|4\s*:\s*3|1\s*:\s*1)\b|--ar\b)",
    re.IGNORECASE,
)
SOURCE_RE = re.compile(
    r"(?:\b(?:shotdeck|filmgrab|screenmusings|source\s+frames?|evidence\s+frames?|"
    r"candidate[_ -]?id|research_only)\b|[A-Za-z]:\\|(?:^|\s)(?:raw|evidence_frames?)/)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"(?:\b(?:TBD|TODO|FIXME)\b|\[[^\]]+\]|\{\{|\}\}|<[^>]+>)",
    re.IGNORECASE,
)
CHINESE_PUNCTUATION_RE = re.compile(r"[，。；：！？【】（）《》、]")
NEGATIVE_RE = re.compile(
    r"\b(?:negative\s+prompt|without|avoid|exclude|do\s+not|"
    r"no\s+(?:black\s+borders?|watermarks?|text|people|objects?))\b",
    re.IGNORECASE,
)
COMMAND_RE = re.compile(r"^\s*(?:generate|create|render|make|draw|produce)\b", re.IGNORECASE)
CONCRETE_CONTENT_RE = re.compile(
    r"\b(?:girl|boy|man|woman|child|children|couple|dog|cat|cyborg|"
    r"singer|dancer|actor|actress|car|building|bedroom|hotel\s+room|"
    r"walking|running|kissing|fighting|holding|sitting|standing|looking|"
    r"wearing|driving|dancing|singing|eating)\b",
    re.IGNORECASE,
)
CONTENT_MOTIF_RE = re.compile(
    r"\b(?:desert|city|street|bedroom|hotel|school|forest|stage|hallway|"
    r"rooftop|pool|spaceship)\b",
    re.IGNORECASE,
)
USAGE_RE = re.compile(
    r"\b(?:MVs?|music\s+videos?|visualizers?|videos?|films?|commercials?|"
    r"shorts?|reels?|album\s+visuals?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    field: str
    message: str
    record: int
    name: str


class InputError(ValueError):
    """Raised when an input file cannot be interpreted as style records."""


def _issue(
    issues: list[Issue],
    severity: str,
    code: str,
    field: str,
    message: str,
    index: int,
    name: str,
) -> None:
    issues.append(Issue(severity, code, field, message, index, name))


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load one JSON object, a JSON array, or JSONL records."""

    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc

    if not text.strip():
        raise InputError(f"input is empty: {path}")

    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InputError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise InputError(f"JSONL line {line_number} must be an object")
            records.append(item)
        if not records:
            raise InputError(f"input contains no records: {path}")
        return records

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}") from exc

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        if not payload:
            raise InputError(f"input contains no records: {path}")
        return payload
    raise InputError("JSON input must be one object or a non-empty array of objects")


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot load schema {path}: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    return schema


def has_non_english_letters(value: str) -> bool:
    """Return True for letter characters outside the Latin script."""

    for char in value:
        if not unicodedata.category(char).startswith("L"):
            continue
        if "LATIN" not in unicodedata.name(char, ""):
            return True
    return False


def normalized_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def anchor_tokens(name: str) -> list[str]:
    tokens = normalized_tokens(name)
    while tokens and tokens[-1] in ANCHOR_SUFFIXES:
        tokens.pop()
    return tokens or normalized_tokens(name)


def check_global_purity(
    field: str,
    value: str,
    issues: list[Issue],
    index: int,
    name: str,
) -> None:
    checks = [
        (MODEL_RE, "purity.model_term", "contains a model, adapter, or generation-system term"),
        (QUALITY_RE, "purity.quality_filler", "contains generic quality filler"),
        (WEIGHT_RE, "purity.weight_syntax", "contains prompt weighting or command syntax"),
        (PARAMETER_RE, "purity.model_parameter", "contains a model parameter"),
        (RESOLUTION_RE, "purity.resolution", "contains a resolution or pixel-quality instruction"),
        (ASPECT_RE, "purity.aspect_ratio", "contains an aspect-ratio instruction"),
        (SOURCE_RE, "purity.source_metadata", "contains research-source or local-path metadata"),
        (PLACEHOLDER_RE, "purity.placeholder", "contains a placeholder or work note"),
        (CHINESE_PUNCTUATION_RE, "purity.chinese_punctuation", "contains Chinese punctuation"),
    ]
    for pattern, code, message in checks:
        if pattern.search(value):
            _issue(issues, "error", code, field, message, index, name)

    if has_non_english_letters(value):
        _issue(
            issues,
            "error",
            "purity.non_english",
            field,
            "contains letters outside the Latin script",
            index,
            name,
        )


def validate_schema_record(
    record: dict[str, Any],
    validator: Draft202012Validator,
    index: int,
    issues: list[Issue],
) -> None:
    name = str(record.get("name") or f"record-{index + 1}")
    for error in sorted(validator.iter_errors(record), key=lambda item: (list(item.absolute_path), item.message)):
        field = ".".join(str(part) for part in error.absolute_path) or "$"
        _issue(
            issues,
            "error",
            f"schema.{error.validator}",
            field,
            error.message,
            index,
            name,
        )


def validate_semantics(record: dict[str, Any], index: int, issues: list[Issue]) -> None:
    name = record.get("name") if isinstance(record.get("name"), str) else f"record-{index + 1}"

    for field in ("name", "description", "analysis", "promptSample"):
        value = record.get(field)
        if not isinstance(value, str):
            continue
        if value != value.strip():
            _issue(issues, "error", "content.outer_whitespace", field, "has leading or trailing whitespace", index, name)
        check_global_purity(field, value, issues, index, name)

    tags = record.get("tags")
    if isinstance(tags, list):
        text_tags = [tag for tag in tags if isinstance(tag, str)]
        for tag_index, tag in enumerate(text_tags):
            field = f"tags.{tag_index}"
            if tag != tag.strip():
                _issue(issues, "error", "content.outer_whitespace", field, "has leading or trailing whitespace", index, name)
            check_global_purity(field, tag, issues, index, name)
            if "," in tag or ";" in tag or len(tag.split()) > 7:
                _issue(issues, "error", "tags.sentence_like", field, "must be one concise phrase, not a list or sentence", index, name)
            if tag.casefold().strip() in GENERIC_TAGS:
                _issue(issues, "warning", "tags.generic", field, "is too generic to distinguish this style", index, name)

        normalized = [tag.casefold().strip() for tag in text_tags]
        if len(set(normalized)) != len(normalized):
            _issue(issues, "error", "tags.duplicate_casefold", "tags", "contains case-insensitive duplicates", index, name)
        if text_tags:
            first_tag = text_tags[0].casefold().strip()
            if first_tag in VISUAL_FORM_ALIASES:
                _issue(issues, "warning", "tags.visual_form_alias", "tags.0", f"use canonical visual form {VISUAL_FORM_ALIASES[first_tag]!r}", index, name)
            elif first_tag not in VISUAL_FORM_TAGS:
                _issue(issues, "advisory", "tags.visual_form_review", "tags.0", "is not in the current visual-form vocabulary; review and add it if valid", index, name)

    if isinstance(record.get("name"), str):
        significant = [token for token in normalized_tokens(record["name"]) if token not in GENERIC_NAME_TOKENS]
        if not significant:
            _issue(issues, "warning", "name.generic_anchor", "name", "does not expose a concrete anchor", index, name)

    description = record.get("description")
    if isinstance(description, str):
        if not USAGE_RE.search(description):
            _issue(issues, "warning", "description.usage_missing", "description", "does not state an applicable video or MV intent", index, name)

    prompt = record.get("promptSample")
    if isinstance(prompt, str):
        clauses = [clause.strip() for clause in prompt.split(",")]
        if any(not clause for clause in clauses):
            _issue(issues, "error", "prompt.empty_phrase", "promptSample", "contains an empty comma-separated phrase", index, name)


        if NEGATIVE_RE.search(prompt):
            _issue(issues, "error", "prompt.negative_instruction", "promptSample", "contains a negative instruction", index, name)
        if COMMAND_RE.search(prompt):
            _issue(issues, "error", "prompt.generation_command", "promptSample", "starts with a generation command", index, name)
        if CONCRETE_CONTENT_RE.search(prompt):
            _issue(issues, "advisory", "prompt.content_review", "promptSample", "contains concrete content; confirm it is a necessary generic motif rather than project-specific content", index, name)
        if re.search(r"https?://|[{}]", prompt, re.IGNORECASE):
            _issue(issues, "error", "prompt.non_style_payload", "promptSample", "contains a URL or structured-data fragment", index, name)

        motifs = {match.group(0).casefold() for match in CONTENT_MOTIF_RE.finditer(prompt)}
        name_words = set(normalized_tokens(record.get("name", "") if isinstance(record.get("name"), str) else ""))
        unexplained_motifs = {motif for motif in motifs if motif not in name_words}
        if len(unexplained_motifs) >= 2:
            _issue(issues, "advisory", "prompt.content_dependency_review", "promptSample", "uses multiple scene motifs; review against the approved content-dependent boundary", index, name)

        normalized_clauses = [" ".join(normalized_tokens(clause)) for clause in clauses if clause]
        if len(set(normalized_clauses)) != len(normalized_clauses):
            _issue(issues, "error", "prompt.duplicate_phrase", "promptSample", "contains duplicate phrases", index, name)


def check_image_url(url: str, index: int, name: str, issues: list[Issue], timeout: float = 15.0) -> None:
    """Fetch an image and validate that it is a decodable image asset."""

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "VidMuse-Style-Validator/2.0", "Accept": "image/*"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            final_url = response.geturl()
            content_type = response.headers.get_content_type()
            data = response.read(25 * 1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _issue(issues, "error", "image.unreachable", "imageUrl", f"cannot fetch image: {exc}", index, name)
        return

    if status < 200 or status >= 300:
        _issue(issues, "error", "image.http_status", "imageUrl", f"HTTP status is {status}", index, name)
        return
    if not final_url.lower().startswith("https://"):
        _issue(issues, "error", "image.https_downgrade", "imageUrl", "redirected to a non-HTTPS URL", index, name)
    if not content_type.lower().startswith("image/"):
        _issue(issues, "error", "image.content_type", "imageUrl", f"content type is {content_type}, not image/*", index, name)
        return
    if len(data) > 25 * 1024 * 1024:
        _issue(issues, "error", "image.too_large", "imageUrl", "image exceeds the 25 MiB validation limit", index, name)
        return

    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except ImportError:
        _issue(issues, "error", "image.decoder_unavailable", "imageUrl", "Pillow is required for --check-image", index, name)
        return
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        _issue(issues, "error", "image.decode", "imageUrl", f"response is not a decodable image: {exc}", index, name)
        return

def validate_records(
    records: Sequence[dict[str, Any]],
    *,
    check_image: bool = False,
    schema: dict[str, Any] | None = None,
) -> list[Issue]:
    schema = schema or load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues: list[Issue] = []
    for index, record in enumerate(records):
        validate_schema_record(record, validator, index, issues)
        validate_semantics(record, index, issues)
        if check_image and isinstance(record.get("imageUrl"), str) and record["imageUrl"].startswith("https://"):
            check_image_url(record["imageUrl"], index, str(record.get("name") or f"record-{index + 1}"), issues)

    seen_names: dict[str, int] = {}
    for index, record in enumerate(records):
        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        key = " ".join(name.casefold().split())
        if key in seen_names:
            first_index = seen_names[key]
            _issue(
                issues,
                "error",
                "name.duplicate_casefold",
                "name",
                f"duplicates record {first_index + 1} after case and whitespace normalization",
                index,
                name,
            )
        else:
            seen_names[key] = index
    return sorted(issues, key=lambda issue: (issue.record, issue.severity != "error", issue.field, issue.code))


def result_payload(path: Path, record_count: int, issues: Iterable[Issue], strict: bool) -> dict[str, Any]:
    issue_list = list(issues)
    errors = [asdict(issue) for issue in issue_list if issue.severity == "error"]
    warnings = [asdict(issue) for issue in issue_list if issue.severity == "warning"]
    advisories = [asdict(issue) for issue in issue_list if issue.severity == "advisory"]
    passed = not errors and (not strict or not warnings)
    return {
        "standard": "VidMuse current six-field style record",
        "path": str(path),
        "records": record_count,
        "strict": strict,
        "passed": passed,
        "errorCount": len(errors),
        "warningCount": len(warnings),
        "advisoryCount": len(advisories),
        "issues": errors + warnings + advisories,
    }


def render_text(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["passed"] else "FAIL"
    lines = [
        f"{status} {payload['path']}",
        f"records={payload['records']} errors={payload['errorCount']} warnings={payload['warningCount']} advisories={payload['advisoryCount']} strict={str(payload['strict']).lower()}",
    ]
    for issue in payload["issues"]:
        lines.append(
            f"[{issue['severity'].upper()}] record={issue['record'] + 1} name={issue['name']!r} "
            f"field={issue['field']} code={issue['code']}: {issue['message']}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate current VidMuse six-field style records")
    parser.add_argument("path", type=Path, help="JSON object, JSON array, or JSONL input")
    parser.add_argument("--strict", action="store_true", help="treat warnings, but not human-review advisories, as validation failures")
    parser.add_argument("--staging", action="store_true", help="allow an intentionally empty imageUrl before upload")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    parser.add_argument("--check-image", action="store_true", help="fetch and validate preview images")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records = load_records(args.path)
        schema_path = STAGING_SCHEMA_PATH if args.staging else SCHEMA_PATH
        issues = validate_records(records, check_image=args.check_image, schema=load_schema(schema_path))
    except InputError as exc:
        if args.format == "json":
            print(json.dumps({"passed": False, "inputError": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    payload = result_payload(args.path, len(records), issues, args.strict)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
