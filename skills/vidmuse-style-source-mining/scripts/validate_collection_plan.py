#!/usr/bin/env python3
"""Validate a VidMuse source collection plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from jsonschema import Draft202012Validator


SCHEMA = Path(__file__).resolve().parent.parent / "references" / "collection-plan.schema.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a VidMuse source collection plan")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8-sig"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        for error in errors:
            field = ".".join(str(part) for part in error.absolute_path) or "$"
            print(f"[ERROR] {field}: {error.message}")
        return 1
    print("PASS collection plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())