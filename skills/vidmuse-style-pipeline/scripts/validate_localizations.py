#!/usr/bin/env python3
"""Verify that VidMuse Chinese Skill review mirrors match their English sources."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Sequence


SKILLS = (
    "vidmuse-style-pipeline",
    "vidmuse-style-source-mining",
    "vidmuse-style-concept-curation",
    "vidmuse-style-record-production",
)
MARKER_PREFIX = "<!-- source_sha256: "
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_hash(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(MARKER_PREFIX) and line.endswith(" -->"):
            return line[len(MARKER_PREFIX):-4]
    return None


def fenced_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    language: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("```"):
            if language is None:
                language = line[3:].strip()
                body = []
            else:
                blocks.append((language, "\n".join(body)))
                language = None
                body = []
        elif language is not None:
            body.append(line)
    return blocks


def link_targets(text: str) -> list[str]:
    return sorted(target.strip() for target in LINK_RE.findall(text))


def has_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def validate(skills_root: Path) -> list[str]:
    errors: list[str] = []
    for name in SKILLS:
        skill_dir = skills_root / name
        english_path = skill_dir / "SKILL.md"
        chinese_path = skill_dir / "SKILL.zh-CN.md"
        if not english_path.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue
        if not chinese_path.is_file():
            errors.append(f"{name}: missing SKILL.zh-CN.md")
            continue
        english = english_path.read_text(encoding="utf-8")
        chinese = chinese_path.read_text(encoding="utf-8")
        actual_hash = source_hash(chinese)
        expected_hash = sha256_text(english)
        if actual_hash is None:
            errors.append(f"{name}: Chinese mirror has no source_sha256 marker")
        elif actual_hash != expected_hash:
            errors.append(f"{name}: Chinese mirror is stale; expected {expected_hash}")
        if not has_cjk(chinese):
            errors.append(f"{name}: Chinese mirror contains no CJK text")
        if fenced_blocks(english) != fenced_blocks(chinese):
            errors.append(f"{name}: executable code blocks differ from English source")
        if link_targets(english) != link_targets(chinese):
            errors.append(f"{name}: reference link targets differ from English source")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate VidMuse Skill Chinese review mirrors")
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--skills-root", type=Path, default=default_root)
    args = parser.parse_args(argv)
    errors = validate(args.skills_root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS localizedSkills={len(SKILLS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
