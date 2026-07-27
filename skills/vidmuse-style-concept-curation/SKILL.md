---
name: vidmuse-style-concept-curation
description: Turn an approved VidMuse EvidenceRecord library into visually coherent, Anchor-based style hypotheses, blind review boards, nearest-neighbor boundaries, live official-library duplicate checks, and an AI-prepared decision registry for lightweight human review. Use when clustering or reclustering style evidence, choosing Anchor scope, separating parent and leaf-level styles, deduplicating against the official library, or deciding advance, merge, split, hold, and reject outcomes.
---

# VidMuse Style Concept Curation

Use Anchor to define what may be tested. Use visual evidence to decide whether the Anchor supports zero, one, or several styles.

## Required Reading

Read [style-clustering-rules.zh-CN.md](references/style-clustering-rules.zh-CN.md) first. It is the active boundary policy under D-024. Read [concept-contract.md](references/concept-contract.md) before creating machine records and use [concept-review-checklist.md](references/concept-review-checklist.md) for human adjudication. Files under `references/historical/` reproduce prior experiments and are not active requirements.

## 1. Confirm Inputs

Require an approved `evidence.jsonl` and its data-quality report. Carry the source rights summary as provenance, not as a reason to remove research evidence. Stop when evidence units or provenance cannot support independent comparison.

Capture the live official catalog for this run before public naming and final recommendations:

```powershell
python scripts/snapshot_official_catalog.py --environment dev --output <stage-dir>/official-style-catalog.json
```

The helper defaults to the dev environment and `~/.vidmuse-dev/config.json` (or `VIDMUSE_DEV_CONFIG`). Use `--environment prod` for the production catalog, or `--config` for an explicit config. It passes the selected config through `VIDMUSE_CONFIG`, verifies that its endpoint matches the requested environment, and then paginates `vidmuse style list --scope official`. The static admin HTML is only a fallback for field-shape context. If the CLI is unavailable, evidence work may continue, but concept approval waits unless the reviewer explicitly accepts the stale-catalog risk.

## 2. Build Candidate Ranges

- Establish concrete public Anchors from works, people, studios, movements, techniques, IP, community aesthetics, or other recognized references.
- Treat each Anchor as an evidence range, never as a guaranteed cluster.
- Keep feature-led discovery anonymous until it can be mapped to a valid public Anchor. Unanchored clusters may inform research but do not become official styles.
- Write `anonymous-candidates.jsonl` against `references/anonymous-candidate.schema.json` before provenance reveal. Use sealed opaque range references, never public names.
- Hide proper names and source labels during initial visual grouping.

## 3. Cluster And Interpret

Choose a medium-appropriate method:

- use structured metadata only when its visual coverage is adequate;
- use visual embeddings or model-assisted comparison when metadata is sparse;
- use hybrid consensus when the channels complement rather than duplicate one another.

Do not use content features, raw search tags, names, popularity, or critical reputation as membership evidence. A valid hypothesis needs a repeatable multi-feature grammar, allowed variation, excluded source motifs, and an explainable nearest-neighbor boundary.

## 4. Build Blind Review

Lock `anonymous-candidates.jsonl`, reveal provenance, then write canonical `hypotheses.jsonl`. Validate both and render:

```powershell
python scripts/validate_concepts.py `
  --evidence <evidence.jsonl> `
  --anonymous-candidates <anonymous-candidates.jsonl> `
  --hypotheses <hypotheses.jsonl> `
  --strict

python scripts/build_review_packet.py `
  --evidence <evidence.jsonl> `
  --anonymous-candidates <anonymous-candidates.jsonl> `
  --hypotheses <hypotheses.jsonl> `
  --asset-root <asset-root> `
  --output-dir <stage-dir>/review
```

Each packet must show core evidence, allowed variation, and disjoint boundary evidence. For parent/leaf or overlapping creator/project scopes, exclude the child source groups from the broad side and document what non-child breadth remains. Do not present one sibling as the whole parent range without a human coverage rationale. If either side lacks independent evidence, mark the boundary insufficient instead of recycling evidence.

## 5. Compare With The Live Catalog

Before any concept can advance, compare it with the saved live catalog and the same batch for exact or normalized names, aliases, parent/leaf relationships, and high-affinity visual recipes. For close matches, fetch the official full record with `vidmuse style get <styleId> --view full --output json` when summary fields are insufficient.

Write `catalog-comparison.md` with the nearest official style, relationship, and one concise incremental-value conclusion for each hypothesis. Also summarize this batch by visual form and Anchor type, then recommend an advance mix as counts or proportions for human judgment. The mix is advisory: it does not cap a category or automatically reject a sound concept. Use a simple product standard for individual concepts: an exact or near duplicate, or a high-affinity concept that would not change Planner choice or generation behavior, does not advance. A close concept may advance when its evidence supports a clearly different user choice and visual recipe. Do not invent universal similarity thresholds. Refresh the live snapshot immediately before concept-stage approval if the library changed during review.

## 6. Prepare Decisions For Human Review

AI may propose only:

- `advance`
- `merge`
- `split`
- `hold`
- `reject`

AI pre-populates one complete row per hypothesis in `decision-registry.jsonl` from the evidence-based recommendation. `parent_child`, `related`, and `alias` remain relations, not outcomes. The human reviews the packet and catalog comparison, edits only exceptions, and approves the concept stage as a batch. Add reviewer, time, and notes only for targeted confirmations or overrides; the approval event covers unchanged AI-proposed rows.