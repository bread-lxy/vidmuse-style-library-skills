#!/usr/bin/env python3
"""Validate VidMuse anonymous candidates, public hypotheses, and human decisions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent
OUTCOMES = {"advance", "merge", "split", "hold", "reject"}
CONFIDENCE = {"low", "medium", "high"}
DEPENDENCY_MODES = {"none", "preferred", "required"}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    hypothesisId: str
    message: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"{path.name}:{line_number} is not an object")
        rows.append(item)
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def load_validator(name: str) -> Draft202012Validator:
    schema = json.loads((ROOT / "references" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def schema_issues(rows: list[dict[str, Any]], schema_name: str, id_field: str, prefix: str) -> list[Issue]:
    validator = load_validator(schema_name)
    issues: list[Issue] = []
    for index, row in enumerate(rows):
        record_id = str(row.get(id_field) or f"record-{index + 1}")
        for error in sorted(validator.iter_errors(row), key=lambda item: (list(item.absolute_path), item.message)):
            field = ".".join(str(part) for part in error.absolute_path) or "$"
            issues.append(Issue("error", f"{prefix}.schema.{error.validator}", record_id, f"{field}: {error.message}"))
    return issues


def normalized_anchor(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", value.casefold())
    while tokens and tokens[-1] in {"inspired", "style", "aesthetic", "cinematic", "visuals"}:
        tokens.pop()
    return " ".join(tokens)


def anchor_membership_matches(row: dict[str, Any], anchor: dict[str, Any]) -> bool | None:
    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    memberships = provenance.get("anchorMemberships")
    if not isinstance(memberships, list) or not memberships:
        return None
    expected = normalized_anchor(str(anchor.get("name") or ""))
    expected_type = str(anchor.get("type") or "").casefold()
    for membership in memberships:
        if not isinstance(membership, dict):
            continue
        if normalized_anchor(str(membership.get("anchorName") or "")) == expected and str(membership.get("anchorType") or "").casefold() == expected_type:
            return True
    return False


def validate_anonymous(rows: list[dict[str, Any]], evidence: dict[str, dict[str, Any]]) -> list[Issue]:
    issues = schema_issues(rows, "anonymous-candidate.schema.json", "anonymousCandidateId", "anonymous")
    seen: set[str] = set()
    candidate_ids = {str(row.get("anonymousCandidateId")) for row in rows if row.get("anonymousCandidateId")}
    for row in rows:
        candidate_id = str(row.get("anonymousCandidateId") or "missing-id")
        if candidate_id in seen:
            issues.append(Issue("error", "anonymous.duplicate_id", candidate_id, "duplicate anonymous candidate ID"))
        seen.add(candidate_id)
        block = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
        members = set(block.get("memberEvidenceIds") or [])
        holdout = set(block.get("holdoutEvidenceIds") or [])
        if members & holdout:
            issues.append(Issue("error", "anonymous.member_holdout_overlap", candidate_id, ", ".join(sorted(members & holdout))))
        unknown = sorted((members | holdout) - set(evidence))
        if unknown:
            issues.append(Issue("error", "anonymous.unknown_evidence", candidate_id, ", ".join(unknown)))
        unknown_neighbors = sorted(set(row.get("candidateNeighbors") or []) - candidate_ids)
        if unknown_neighbors:
            issues.append(Issue("error", "anonymous.unknown_neighbor", candidate_id, ", ".join(unknown_neighbors)))
    return issues


def validate(
    evidence_rows: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    decisions: list[dict[str, Any]] | None = None,
    anonymous_candidates: list[dict[str, Any]] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    evidence: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(evidence_rows):
        evidence_id = str(item.get("evidenceId") or f"record-{index + 1}")
        if evidence_id in evidence:
            issues.append(Issue("error", "evidence.duplicate_id", evidence_id, "duplicate evidence ID would make membership ambiguous"))
            continue
        evidence[evidence_id] = item

    anonymous_ids: set[str] = set()
    if anonymous_candidates is not None:
        issues.extend(validate_anonymous(anonymous_candidates, evidence))
        anonymous_ids = {str(row.get("anonymousCandidateId")) for row in anonymous_candidates if row.get("anonymousCandidateId")}

    issues.extend(schema_issues(hypotheses, "style-hypothesis.schema.json", "hypothesisId", "hypothesis"))
    hypothesis_map: dict[str, dict[str, Any]] = {}
    assigned: dict[str, set[str]] = {}
    for item in hypotheses:
        hypothesis_id = str(item.get("hypothesisId") or "missing-id")
        if hypothesis_id in hypothesis_map:
            issues.append(Issue("error", "hypothesis.duplicate_id", hypothesis_id, "duplicate hypothesis ID"))
            continue
        hypothesis_map[hypothesis_id] = item
        if "finalOutcome" in item or "humanDecision" in item:
            issues.append(Issue("error", "decision.ai_final_outcome", hypothesis_id, "AI hypothesis record cannot contain a human outcome"))
        anonymous_id = str(item.get("anonymousCandidateId") or "")
        if anonymous_candidates is not None and anonymous_id not in anonymous_ids:
            issues.append(Issue("error", "anonymous.unlinked_hypothesis", hypothesis_id, anonymous_id or "missing anonymousCandidateId"))

        anchor = item.get("anchor") if isinstance(item.get("anchor"), dict) else {}
        signature = item.get("signature") if isinstance(item.get("signature"), dict) else {}
        invariants = signature.get("transferableInvariants") if isinstance(signature.get("transferableInvariants"), list) else []
        dimensions = {str(value.get("dimension")) for value in invariants if isinstance(value, dict) and value.get("dimension")}
        if len(dimensions) < 3:
            issues.append(Issue("error", "signature.too_narrow", hypothesis_id, "official candidates require at least three co-occurring invariant dimensions"))

        evidence_block = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        core = set(evidence_block.get("coreEvidenceIds") or [])
        variation = set(evidence_block.get("variationEvidenceIds") or [])
        assigned[hypothesis_id] = core | variation
        if core & variation:
            issues.append(Issue("error", "evidence.core_variation_overlap", hypothesis_id, ", ".join(sorted(core & variation))))
        referenced = set(core | variation)
        for invariant in invariants:
            if isinstance(invariant, dict):
                referenced.update(invariant.get("evidenceIds") or [])
        unknown = sorted(referenced - set(evidence))
        if unknown:
            issues.append(Issue("error", "evidence.unknown_id", hypothesis_id, ", ".join(unknown)))
        non_independent = sorted(value for value in core if value in evidence and (evidence[value].get("duplicateOf") or evidence[value].get("nearDuplicateOf")))
        if non_independent:
            issues.append(Issue("warning", "evidence.non_independent_core", hypothesis_id, ", ".join(non_independent)))
        membership_results = [anchor_membership_matches(evidence[value], anchor) for value in referenced if value in evidence]
        known_memberships = [result for result in membership_results if result is not None]
        if known_memberships and not any(known_memberships):
            issues.append(Issue("warning", "anchor.membership_unverified", hypothesis_id, "none of the assigned evidence records declares this Anchor membership"))

        scope = item.get("scope") if isinstance(item.get("scope"), dict) else {}
        dependency = scope.get("contentDependency") if isinstance(scope.get("contentDependency"), dict) else {}
        mode = dependency.get("mode")
        values = dependency.get("values")
        if mode not in DEPENDENCY_MODES or not isinstance(values, list):
            issues.append(Issue("error", "scope.content_dependency", hypothesis_id, "content dependency requires mode and values"))
        elif mode == "none" and values:
            issues.append(Issue("error", "scope.none_with_values", hypothesis_id, "none dependency cannot list required content"))
        elif mode in {"preferred", "required"} and not values:
            issues.append(Issue("error", "scope.dependency_without_values", hypothesis_id, "preferred/required dependency needs values"))

        recommendation = item.get("aiRecommendation") if isinstance(item.get("aiRecommendation"), dict) else {}
        if recommendation.get("outcome") not in OUTCOMES:
            issues.append(Issue("error", "recommendation.outcome", hypothesis_id, "invalid AI recommendation"))
        if recommendation.get("confidence") not in CONFIDENCE:
            issues.append(Issue("error", "recommendation.confidence", hypothesis_id, "invalid confidence"))

    for hypothesis_id, item in hypothesis_map.items():
        boundaries = item.get("boundary") if isinstance(item.get("boundary"), list) else []
        if not boundaries:
            issues.append(Issue("warning", "boundary.missing", hypothesis_id, "no nearest-neighbor boundary was supplied"))
        for index, boundary in enumerate(boundaries):
            if not isinstance(boundary, dict):
                continue
            neighbor_id = str(boundary.get("neighborHypothesisId") or "")
            status = boundary.get("status")
            if neighbor_id not in hypothesis_map:
                issues.append(Issue("error", "boundary.unknown_neighbor", hypothesis_id, neighbor_id or f"boundary {index + 1}"))
            if neighbor_id == hypothesis_id:
                issues.append(Issue("error", "boundary.self_neighbor", hypothesis_id, neighbor_id))
            target = set(boundary.get("targetEvidenceIds") or [])
            neighbor = set(boundary.get("neighborEvidenceIds") or [])
            if status == "insufficient":
                if not str(boundary.get("insufficiencyReason") or "").strip():
                    issues.append(Issue("error", "boundary.insufficiency_reason", hypothesis_id, "insufficient boundary requires a reason"))
                continue
            if status != "available":
                continue
            if not target or not neighbor:
                issues.append(Issue("error", "boundary.side_missing", hypothesis_id, "available boundary requires evidence on both sides"))
            if target & neighbor:
                issues.append(Issue("error", "boundary.shared_evidence", hypothesis_id, ", ".join(sorted(target & neighbor))))
            unknown_boundary = sorted((target | neighbor) - set(evidence))
            if unknown_boundary:
                issues.append(Issue("error", "boundary.unknown_evidence", hypothesis_id, ", ".join(unknown_boundary)))
            if not target.issubset(assigned.get(hypothesis_id, set())):
                issues.append(Issue("error", "boundary.target_not_member", hypothesis_id, ", ".join(sorted(target - assigned.get(hypothesis_id, set())))))
            if neighbor_id in assigned and not neighbor.issubset(assigned[neighbor_id]):
                issues.append(Issue("error", "boundary.neighbor_not_member", hypothesis_id, ", ".join(sorted(neighbor - assigned[neighbor_id]))))
            target_groups = {evidence[value].get("sourceGroupKey") for value in target if value in evidence}
            neighbor_groups = {evidence[value].get("sourceGroupKey") for value in neighbor if value in evidence}
            overlap = sorted(value for value in target_groups & neighbor_groups if value)
            if overlap:
                issues.append(Issue("error", "boundary.shared_source_group", hypothesis_id, ", ".join(overlap)))
            if not boundary.get("distinguishingRules"):
                issues.append(Issue("error", "boundary.rules_missing", hypothesis_id, "available boundary needs positive distinguishing rules"))

            reciprocal = [candidate for candidate in (hypothesis_map.get(neighbor_id, {}).get("boundary") or []) if isinstance(candidate, dict) and candidate.get("jointTestId") == boundary.get("jointTestId") and candidate.get("neighborHypothesisId") == hypothesis_id]
            if len(reciprocal) != 1:
                issues.append(Issue("error", "boundary.reciprocal_missing", hypothesis_id, str(boundary.get("jointTestId") or "missing jointTestId")))
            elif set(reciprocal[0].get("targetEvidenceIds") or []) != neighbor or set(reciprocal[0].get("neighborEvidenceIds") or []) != target:
                issues.append(Issue("error", "boundary.reciprocal_mismatch", hypothesis_id, str(boundary.get("jointTestId"))))

            if boundary.get("relationTest") == "parent_child":
                roles = {boundary.get("targetRole"), boundary.get("neighborRole")}
                exclusion = boundary.get("siblingExclusion") if isinstance(boundary.get("siblingExclusion"), dict) else {}
                if roles != {"parent", "child"}:
                    issues.append(Issue("error", "boundary.parent_child_roles", hypothesis_id, "parent-child test needs one parent side and one child side"))
                    continue
                child_groups = set(exclusion.get("childSourceGroupKeys") or [])
                broad_declared = set(exclusion.get("broadSideSourceGroupKeys") or [])
                broad_ids = target if boundary.get("targetRole") == "parent" else neighbor
                broad_actual = {evidence[value].get("sourceGroupKey") for value in broad_ids if value in evidence and evidence[value].get("sourceGroupKey")}
                if child_groups & broad_actual:
                    issues.append(Issue("error", "boundary.child_leak_into_parent", hypothesis_id, ", ".join(sorted(child_groups & broad_actual))))
                if broad_actual != broad_declared:
                    issues.append(Issue("error", "boundary.broad_groups_mismatch", hypothesis_id, f"declared={sorted(broad_declared)} actual={sorted(broad_actual)}"))
                if child_groups & broad_declared:
                    issues.append(Issue("error", "boundary.sibling_exclusion_overlap", hypothesis_id, ", ".join(sorted(child_groups & broad_declared))))
                if not str(exclusion.get("coverageRationale") or "").strip():
                    issues.append(Issue("error", "boundary.coverage_rationale_missing", hypothesis_id, "parent breadth requires a human-readable coverage rationale"))

    if decisions is not None:
        issues.extend(schema_issues(decisions, "decision-registry.schema.json", "hypothesisId", "decision"))
        seen: set[str] = set()
        for row in decisions:
            hypothesis_id = str(row.get("hypothesisId") or "missing-id")
            if hypothesis_id in seen:
                issues.append(Issue("error", "decision.duplicate", hypothesis_id, "duplicate decision row"))
            seen.add(hypothesis_id)
            if hypothesis_id not in hypothesis_map:
                issues.append(Issue("error", "decision.unknown_hypothesis", hypothesis_id, "decision does not match a hypothesis"))
            decision = row.get("decision")
            canonical = row.get("canonicalHypothesisId")
            if decision == "merge":
                if canonical not in hypothesis_map or canonical == hypothesis_id:
                    issues.append(Issue("error", "decision.merge_target", hypothesis_id, "merge target must be another existing hypothesis"))
            if decision == "split":
                resulting = set(row.get("resultingHypothesisIds") or [])
                if not resulting:
                    issues.append(Issue("error", "decision.split_targets", hypothesis_id, "split requires resulting hypothesis IDs"))
                unknown = sorted(resulting - set(hypothesis_map))
                if unknown:
                    issues.append(Issue("error", "decision.split_unknown_target", hypothesis_id, ", ".join(unknown)))
            for relation in row.get("relations") or []:
                if not isinstance(relation, dict):
                    continue
                target_id = relation.get("targetHypothesisId")
                if target_id not in hypothesis_map or target_id == hypothesis_id:
                    issues.append(Issue("error", "decision.relation_target", hypothesis_id, str(target_id)))
            for action in row.get("evidenceActions") or []:
                if not isinstance(action, dict):
                    continue
                unknown_evidence = sorted(set(action.get("evidenceIds") or []) - set(evidence))
                if unknown_evidence:
                    issues.append(Issue("error", "decision.action_unknown_evidence", hypothesis_id, ", ".join(unknown_evidence)))
                target_id = action.get("targetHypothesisId")
                if target_id is not None and target_id not in hypothesis_map:
                    issues.append(Issue("error", "decision.action_unknown_target", hypothesis_id, str(target_id)))
        undecided = sorted(set(hypothesis_map) - seen)
        if undecided:
            issues.append(Issue("warning", "decision.incomplete", "batch", ", ".join(undecided)))
    return sorted(issues, key=lambda item: (item.hypothesisId, item.severity != "error", item.code))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate VidMuse concept-stage records")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--anonymous-candidates", type=Path)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        evidence = load_jsonl(args.evidence)
        hypotheses = load_jsonl(args.hypotheses)
        anonymous_candidates = load_jsonl(args.anonymous_candidates) if args.anonymous_candidates else None
        decisions = load_jsonl(args.decisions) if args.decisions else None
        issues = validate(evidence, hypotheses, decisions, anonymous_candidates)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    errors = [item for item in issues if item.severity == "error"]
    warnings = [item for item in issues if item.severity == "warning"]
    passed = not errors and (not args.strict or not warnings)
    payload = {"passed": passed, "hypotheses": len(hypotheses), "errors": len(errors), "warnings": len(warnings), "issues": [asdict(item) for item in issues]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if passed else 'FAIL'} hypotheses={len(hypotheses)} errors={len(errors)} warnings={len(warnings)}")
        for item in issues:
            print(f"[{item.severity.upper()}] {item.hypothesisId} {item.code}: {item.message}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
