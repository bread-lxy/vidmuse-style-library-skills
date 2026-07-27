# Anonymous Candidate, Style Hypothesis, And Decision Contract

The concept stage separates anonymous visual discovery, public naming, live-catalog comparison, and reviewed disposition because each answers a different question.

## 1. Anonymous Candidate

Write `anonymous-candidates.jsonl` before revealing source names. Each row contains only an opaque candidate ID and label, visual signature, evidence membership, holdout, neighbor candidates, sealed Anchor-range references, and uncertainty. It must not contain public Anchor names, creators, work titles, query labels, or provenance.

`sealedRangeRefs` preserves the Anchor-first collection range without exposing its name to the visual reviewer. The mapping from a sealed range to a public Anchor remains outside the blind packet until reveal.

## 2. Public Style Hypothesis

After the anonymous grouping is locked, reveal provenance and write `hypotheses.jsonl`:

```json
{
  "hypothesisId": "hyp-0001",
  "anonymousCandidateId": "anon-0001",
  "anonymousLabel": "Cluster 0001",
  "anchor": {"type": "movement", "name": "Public anchor name", "scope": "Evidence range being tested"},
  "scope": {"media": ["graphic_print"], "contentDependency": {"mode": "none", "values": []}},
  "signature": {
    "summary": "Source-free repeatable visual grammar.",
    "transferableInvariants": [
      {"dimension": "mark_making", "rule": "Observable positive rule.", "evidenceIds": ["evidence-1"]}
    ],
    "allowedVariation": ["Variation that remains inside the style."],
    "excludedSourceMotifs": ["Character, prop, location, or iconic scene."]
  },
  "evidence": {"coreEvidenceIds": ["evidence-1"], "variationEvidenceIds": ["evidence-2"]},
  "boundary": [
    {
      "jointTestId": "boundary-0001",
      "neighborHypothesisId": "hyp-0002",
      "relationTest": "peer",
      "targetEvidenceIds": ["evidence-1"],
      "neighborEvidenceIds": ["evidence-3"],
      "distinguishingRules": ["Positive visible difference."],
      "status": "available"
    }
  ],
  "aiRecommendation": {"outcome": "advance", "confidence": "medium", "reason": "Evidence-based recommendation, not a final decision."}
}
```

Use at least three co-occurring invariant dimensions. Evidence quantity is medium- and source-dependent under D-024; never pad a weak range to satisfy a number.

Every available peer boundary is reciprocal and uses the same `jointTestId`. Target-side evidence belongs to the current hypothesis; neighbor-side evidence belongs to the named neighbor. The two sides share neither evidence nor source groups.

For a parent/child test, add `relationTest: "parent_child"`, `targetRole`, `neighborRole`, and `siblingExclusion`. The broad side excludes the child source groups and declares the non-child groups it covers. A single sibling must not be silently presented as the entire parent range: explain breadth in `coverageRationale` or mark the test `insufficient`. This is a human breadth judgment, not a universal numeric threshold.

## 3. Live Official-Catalog Comparison

Capture `official-style-catalog.json` through the VidMuse CLI during the current concept review. Do not reuse a bundled list of names as the duplicate-check source. Write `catalog-comparison.md` with one concise row per hypothesis:

- nearest official style name and ID, or `none`;
- relation: `exact`, `alias`, `parent_child`, `high_affinity`, or `distinct`;
- whether the candidate changes Planner choice and generation behavior;
- conclusion: advance to decision review, merge/retain the existing style, hold, or reject.

Use product meaning, not a universal similarity number. Exact and near duplicates and high-affinity candidates with little incremental value should not reach record production. A close leaf may advance when its evidence supports a clear user-facing choice and a visibly different recipe.

In the same `catalog-comparison.md`, summarize candidate counts and proportions by visual form and Anchor type, then recommend an advance mix. This is a nonbinding portfolio recommendation for human judgment: it cannot impose a category quota, cap, or automatic rejection.

## 4. AI Pre-Review And Human Exceptions

AI writes exactly one complete JSON object per hypothesis to `decision-registry.jsonl`:

```json
{
  "hypothesisId": "hyp-0001",
  "decision": "advance",
  "canonicalHypothesisId": "hyp-0001",
  "resultingHypothesisIds": [],
  "relations": [{"type": "parent_child", "targetHypothesisId": "hyp-0002", "role": "parent"}],
  "reviewStatus": "ai_proposed",
  "evidenceActions": []
}
```

Decisions are `advance`, `merge`, `split`, `hold`, or `reject`. `parent_child`, `related`, and `alias` are relationships, not outcomes.

- `merge`: set `canonicalHypothesisId` to the retained same-batch hypothesis. An official-library duplicate is normally rejected as already represented and explained in `catalog-comparison.md`.
- `split`: list every resulting hypothesis in `resultingHypothesisIds` and describe evidence movement in structured `evidenceActions`.
- `hold`: state the missing evidence or test in `notes` when it is not already clear from the hypothesis recommendation.
- Human reviewers inspect the complete AI pre-review and edit only exceptions. Set `reviewStatus` to `human_confirmed` for a targeted confirmation or `human_overridden` for a changed decision; those rows record reviewer and time, and overrides also explain why.
- The concept-stage approval event is the human batch acceptance for every unchanged `ai_proposed` row.
