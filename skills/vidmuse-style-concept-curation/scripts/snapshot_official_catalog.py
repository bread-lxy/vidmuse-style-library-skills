#!/usr/bin/env python3
"""Capture the current official VidMuse style catalog for concept-stage deduplication."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import urlparse


class SnapshotError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_config_path(environment: str) -> Path:
    if environment == "dev":
        configured = os.environ.get("VIDMUSE_DEV_CONFIG")
        fallback = Path.home() / ".vidmuse-dev" / "config.json"
    elif environment == "prod":
        configured = os.environ.get("VIDMUSE_PROD_CONFIG")
        fallback = Path.home() / ".vidmuse" / "config.json"
    else:
        raise SnapshotError(f"unsupported environment: {environment}")
    return Path(configured).expanduser().resolve() if configured else fallback.expanduser().resolve()


def infer_environment(base_url: str) -> str:
    hostname = urlparse(base_url).hostname
    if not hostname:
        raise SnapshotError(f"invalid CLI baseUrl: {base_url!r}")
    return "dev" if "dev" in hostname.lower() else "prod"


def load_config(path: Path, expected_environment: str) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise SnapshotError(f"{expected_environment} CLI config not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"cannot read CLI config {path}: {exc}") from exc
    base_url = payload.get("baseUrl") if isinstance(payload, dict) else None
    if not isinstance(base_url, str):
        raise SnapshotError(f"CLI config has no valid baseUrl: {path}")
    actual_environment = infer_environment(base_url)
    if actual_environment != expected_environment:
        raise SnapshotError(
            f"CLI config endpoint is {actual_environment}, but {expected_environment} was requested: {path}"
        )
    return base_url.rstrip("/")


def runner_env(config_path: Path | None) -> dict[str, str] | None:
    if config_path is None:
        return None
    env = os.environ.copy()
    env["VIDMUSE_CONFIG"] = str(config_path)
    return env


def run_json(command: list[str], runner: Callable[..., Any] = subprocess.run, env: dict[str, str] | None = None) -> dict[str, Any]:
    result = runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "command failed").strip()
        raise SnapshotError(f"{' '.join(command)}: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"command did not return JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SnapshotError("catalog response must be a JSON object")
    return payload


def capture(
    cli: str,
    page_size: int = 100,
    environment: str = "dev",
    config_path: Path | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    config_path = config_path or default_config_path(environment)
    endpoint = load_config(config_path, environment)
    env = runner_env(config_path)
    version_result = runner([cli, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if version_result.returncode != 0:
        raise SnapshotError((version_result.stderr or version_result.stdout or "cannot read CLI version").strip())
    styles: list[dict[str, Any]] = []
    offset = 0
    while True:
        command = [cli, "style", "list", "--scope", "official", "--limit", str(page_size), "--offset", str(offset), "--view", "summary", "--output", "json"]
        payload = run_json(command, runner, env)
        page = payload.get("data")
        if not isinstance(page, list):
            raise SnapshotError("catalog response data must be an array")
        if not all(isinstance(item, dict) for item in page):
            raise SnapshotError("catalog response contains a non-object style")
        styles.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return {
        "schemaVersion": 1,
        "capturedAt": utc_now(),
        "source": "vidmuse-cli",
        "cliVersion": version_result.stdout.strip(),
        "environment": environment,
        "endpoint": endpoint,
        "scope": "official",
        "pageSize": page_size,
        "styleCount": len(styles),
        "styles": styles,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture the live VidMuse official style catalog")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cli", default="vidmuse")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--environment", choices=("dev", "prod"), default="dev", help="catalog environment to query")
    parser.add_argument("--config", type=Path, help="explicit CLI config; defaults to the selected environment's config")
    args = parser.parse_args(argv)
    if args.page_size < 1 or args.page_size > 100:
        print("ERROR: --page-size must be between 1 and 100", file=sys.stderr)
        return 2
    cli = shutil.which(args.cli) or args.cli
    config_path = args.config.expanduser().resolve() if args.config else default_config_path(args.environment)
    try:
        payload = capture(cli, args.page_size, args.environment, config_path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
    except (OSError, SnapshotError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS styles={payload['styleCount']} capturedAt={payload['capturedAt']} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
