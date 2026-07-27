#!/usr/bin/env python3
"""Run a resumable, approval-gated VidMuse style production workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


SCHEMA_VERSION = 1
STAGES = [
    {
        "id": "source-plan",
        "directory": "01-source-plan",
        "required": ["official-style-catalog.json", "source-assessment.md", "collection-plan.json", "sample"],
    },
    {
        "id": "evidence",
        "directory": "02-evidence",
        "required": ["raw-manifest.jsonl", "mapping.json", "evidence.jsonl", "quarantine.json", "data-quality.md", "assets", "review/contact-sheet.html"],
    },
    {
        "id": "concept",
        "directory": "03-concepts",
        "required": ["anonymous-candidates.jsonl", "hypotheses.jsonl", "official-style-catalog.json", "catalog-comparison.md", "review/candidate-index.md", "review/blind-review.html", "decision-registry.jsonl"],
    },
    {
        "id": "records",
        "directory": "04-records",
        "required": ["style-records.staging.jsonl", "field-review.md", "neighbor-review.md"],
    },
    {
        "id": "preview-export",
        "directory": "05-preview-export",
        "required": ["styles.json", "styles.csv", "preview-prompts.jsonl", "preview-manifest.csv", "previews"],
    },
]
STAGE_INDEX = {item["id"]: index for index, item in enumerate(STAGES)}


class PipelineError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def event_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "style-run"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_artifact(path: Path) -> str:
    if path.is_file():
        if path.stat().st_size == 0:
            raise PipelineError(f"required file is empty: {path}")
        return f"file:{sha256_file(path)}"
    if path.is_dir():
        files = sorted(item for item in path.rglob("*") if item.is_file())
        if not files:
            raise PipelineError(f"required directory is empty: {path}")
        digest = hashlib.sha256()
        for item in files:
            relative = item.relative_to(path).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(sha256_file(item).encode("ascii"))
            digest.update(b"\n")
        return f"tree:{digest.hexdigest()}"
    raise PipelineError(f"required artifact is missing: {path}")


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "run-manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise PipelineError(f"run is not initialized: {run_dir}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"invalid run manifest: {exc}") from exc
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise PipelineError(f"unsupported run schema: {payload.get('schemaVersion')}")
    return payload


def save_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updatedAt"] = utc_now()
    atomic_write_json(run_dir / "run-manifest.json", manifest)
    write_progress(run_dir, manifest)


def write_progress(run_dir: Path, manifest: dict[str, Any]) -> None:
    lines = [
        f"# {manifest['name']}",
        "",
        f"Run ID: `{manifest['runId']}`",
        f"Updated: `{manifest['updatedAt']}`",
        "",
        "| Stage | Status | Approval |",
        "|---|---|---|",
    ]
    for definition in STAGES:
        stage = manifest["stages"][definition["id"]]
        approval = stage.get("approval") or ""
        lines.append(f"| `{definition['id']}` | `{stage['status']}` | `{approval}` |")
    lines.extend(["", "Use `run_pipeline.py status <run-dir>` to verify artifact drift.", ""])
    (run_dir / "progress.md").write_text("\n".join(lines), encoding="utf-8")


def stage_definition(stage_id: str) -> dict[str, Any]:
    try:
        return STAGES[STAGE_INDEX[stage_id]]
    except KeyError as exc:
        raise PipelineError(f"unknown stage: {stage_id}") from exc


def stage_artifacts(run_dir: Path, definition: dict[str, Any]) -> dict[str, str]:
    base = run_dir / definition["directory"]
    return {relative: hash_artifact(base / relative) for relative in definition["required"]}


def previous_approved(manifest: dict[str, Any], stage_id: str) -> bool:
    index = STAGE_INDEX[stage_id]
    return index == 0 or manifest["stages"][STAGES[index - 1]["id"]]["status"] == "approved"


def write_event(run_dir: Path, stage_id: str, outcome: str, reviewer: str, note: str, artifacts: dict[str, str]) -> str:
    name = f"{event_stamp()}__{stage_id}__{outcome}.json"
    path = run_dir / "approvals" / name
    atomic_write_json(
        path,
        {
            "schemaVersion": 1,
            "stage": stage_id,
            "outcome": outcome,
            "reviewer": reviewer,
            "note": note,
            "recordedAt": utc_now(),
            "artifactHashes": artifacts,
        },
    )
    return path.relative_to(run_dir).as_posix()


def command_init(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest_path = run_dir / "run-manifest.json"
    if manifest_path.exists():
        raise PipelineError(f"run already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    for definition in STAGES:
        (run_dir / definition["directory"]).mkdir(parents=True, exist_ok=True)
    (run_dir / STAGES[0]["directory"] / "sample").mkdir(parents=True, exist_ok=True)
    (run_dir / STAGES[-1]["directory"] / "previews").mkdir(parents=True, exist_ok=True)
    (run_dir / "approvals").mkdir(parents=True, exist_ok=True)

    standards_hash = None
    if args.standards_manifest:
        standards_path = args.standards_manifest.resolve()
        if not standards_path.is_file():
            raise PipelineError(f"standards manifest not found: {standards_path}")
        standards_hash = sha256_file(standards_path)

    created = utc_now()
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": f"{slug(args.name)}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "name": args.name,
        "sources": args.source,
        "createdAt": created,
        "updatedAt": created,
        "standards": {
            "manifestPath": str(args.standards_manifest.resolve()) if args.standards_manifest else None,
            "manifestSha256": standards_hash,
        },
        "stages": {},
    }
    for index, definition in enumerate(STAGES):
        manifest["stages"][definition["id"]] = {
            "status": "ready" if index == 0 else "blocked",
            "directory": definition["directory"],
            "requiredArtifacts": definition["required"],
            "approval": None,
            "history": [],
        }
    save_manifest(run_dir, manifest)
    print(f"initialized {run_dir}")


def command_start(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest = load_manifest(run_dir)
    stage = manifest["stages"][args.stage]
    if not previous_approved(manifest, args.stage):
        raise PipelineError(f"upstream stage is not approved: {args.stage}")
    if any(item["status"] == "in_progress" for item in manifest["stages"].values()):
        raise PipelineError("another stage is already in progress")
    if stage["status"] not in {"ready", "rejected"}:
        raise PipelineError(f"stage cannot start from status {stage['status']}; reopen it first if needed")
    stage["status"] = "in_progress"
    stage["history"].append({"event": "started", "at": utc_now(), "by": args.worker})
    save_manifest(run_dir, manifest)
    print(f"started {args.stage}")


def command_approve(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest = load_manifest(run_dir)
    if not previous_approved(manifest, args.stage):
        raise PipelineError(f"upstream stage is not approved: {args.stage}")
    stage = manifest["stages"][args.stage]
    if stage["status"] not in {"ready", "in_progress", "rejected"}:
        raise PipelineError(f"stage cannot be approved from status {stage['status']}")
    hashes = stage_artifacts(run_dir, stage_definition(args.stage))
    event = write_event(run_dir, args.stage, "approved", args.reviewer, args.note, hashes)
    stage["status"] = "approved"
    stage["approval"] = event
    stage["history"].append({"event": "approved", "at": utc_now(), "eventFile": event})
    next_index = STAGE_INDEX[args.stage] + 1
    if next_index < len(STAGES):
        next_stage = manifest["stages"][STAGES[next_index]["id"]]
        if next_stage["status"] == "blocked":
            next_stage["status"] = "ready"
    save_manifest(run_dir, manifest)
    print(f"approved {args.stage}: {event}")


def command_reject(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest = load_manifest(run_dir)
    stage = manifest["stages"][args.stage]
    if stage["status"] not in {"ready", "in_progress"}:
        raise PipelineError(f"stage cannot be rejected from status {stage['status']}")
    event = write_event(run_dir, args.stage, "rejected", args.reviewer, args.note, {})
    stage["status"] = "rejected"
    stage["history"].append({"event": "rejected", "at": utc_now(), "eventFile": event})
    save_manifest(run_dir, manifest)
    print(f"rejected {args.stage}: {event}")


def command_reopen(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest = load_manifest(run_dir)
    index = STAGE_INDEX[args.stage]
    event = write_event(run_dir, args.stage, "reopened", args.reviewer, args.note, {})
    for offset, definition in enumerate(STAGES[index:], start=index):
        stage = manifest["stages"][definition["id"]]
        if stage.get("approval"):
            stage["history"].append({"event": "approval_staled", "at": utc_now(), "approval": stage["approval"]})
        stage["approval"] = None
        stage["status"] = "ready" if offset == index and previous_approved(manifest, definition["id"]) else "blocked"
    manifest["stages"][args.stage]["history"].append({"event": "reopened", "at": utc_now(), "eventFile": event})
    save_manifest(run_dir, manifest)
    print(f"reopened from {args.stage}; artifacts were preserved")


def approval_drift(run_dir: Path, manifest: dict[str, Any], stage_id: str) -> list[str]:
    stage = manifest["stages"][stage_id]
    if stage["status"] != "approved" or not stage.get("approval"):
        return []
    event_path = run_dir / stage["approval"]
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
        current = stage_artifacts(run_dir, stage_definition(stage_id))
    except (OSError, json.JSONDecodeError, PipelineError) as exc:
        return [str(exc)]
    expected = event.get("artifactHashes", {})
    return [name for name in sorted(set(expected) | set(current)) if expected.get(name) != current.get(name)]


def command_status(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    manifest = load_manifest(run_dir)
    drift_count = 0
    print(f"run={manifest['runId']} name={manifest['name']}")
    for definition in STAGES:
        stage_id = definition["id"]
        drift = approval_drift(run_dir, manifest, stage_id)
        drift_count += len(drift)
        suffix = f" drift={','.join(drift)}" if drift else ""
        print(f"{stage_id:15} {manifest['stages'][stage_id]['status']:12}{suffix}")
    approved = all(manifest["stages"][item["id"]]["status"] == "approved" for item in STAGES)
    print(f"complete={str(approved and drift_count == 0).lower()} driftCount={drift_count}")
    if args.fail_on_incomplete and (not approved or drift_count):
        raise PipelineError("run is incomplete or has artifact drift")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a gated VidMuse style-library production run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("run_dir", type=Path)
    init_parser.add_argument("--name", required=True)
    init_parser.add_argument("--source", action="append", required=True)
    init_parser.add_argument("--standards-manifest", type=Path)
    init_parser.set_defaults(func=command_init)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("run_dir", type=Path)
    start_parser.add_argument("--stage", choices=STAGE_INDEX, required=True)
    start_parser.add_argument("--worker", required=True)
    start_parser.set_defaults(func=command_start)

    for command, func in (("approve", command_approve), ("reject", command_reject), ("reopen", command_reopen)):
        item = subparsers.add_parser(command)
        item.add_argument("run_dir", type=Path)
        item.add_argument("--stage", choices=STAGE_INDEX, required=True)
        item.add_argument("--reviewer", required=True)
        item.add_argument("--note", required=True)
        item.set_defaults(func=func)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("run_dir", type=Path)
    status_parser.add_argument("--fail-on-incomplete", action="store_true")
    status_parser.set_defaults(func=command_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())