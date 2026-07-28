# VidMuse Style Pipeline Contract

## Stage Order

| Stage | Directory | Required artifacts |
|---|---|---|
| `source-plan` | `01-source-plan` | `official-style-catalog.json`, `source-assessment.md`, `collection-plan.json`, `sample/` |
| `evidence` | `02-evidence` | `raw-manifest.jsonl`, `mapping.json`, `evidence.jsonl`, `quarantine.json`, `data-quality.md`, `assets/`, `review/contact-sheet.html` |
| `concept` | `03-concepts` | `anonymous-candidates.jsonl`, `hypotheses.jsonl`, `official-style-catalog.json`, `catalog-comparison.md`, `review/candidate-index.md`, `review/blind-review.html`, `decision-registry.jsonl` |
| `records` | `04-records` | `style-records.staging.jsonl`, `field-review.md`, `neighbor-review.md` |
| `preview-export` | `05-preview-export` | `styles.json`, `styles.csv`, `preview-prompts.jsonl`, `preview-manifest.csv`, `previews/` |
| `url-backfill` | `06-url-backfill` | `planner-image-url-map.json`, `styles.json`, `styles.csv`, `image-url-map.json`, `url-validation.json` |

`preview-export` is the immutable staging delivery and therefore keeps
`imageUrl` empty. `url-backfill` is the formal next stage: it uploads only the
approved final previews, verifies their browser-accessible HTTPS URLs, and
produces the final six-field delivery without changing stage 05.

## Approval Semantics

- `blocked`: an upstream stage is not approved.
- `ready`: the stage may start.
- `in_progress`: artifacts are being produced or reviewed.
- `approved`: required artifacts were accepted and their hashes were frozen.
- `rejected`: the reviewer rejected the current package.
- `stale`: an upstream decision, artifact, or standard changed.

An approval is an immutable event file. Reopening keeps the old event and marks affected stages stale. Approval never deletes or replaces artifacts.

## Manifest Compatibility

New runs use manifest schema version 2 and contain all six stages. A version 1
five-stage manifest remains readable: the controller adds `url-backfill` in
memory as `ready` when `preview-export` is already approved, otherwise as
`blocked`. The upgrade is persisted only when a mutating command saves the
manifest. Existing stage artifacts, approvals, notes, and hashes are preserved.
A migrated run is not complete until the sixth stage is approved.

## Run Invariants

1. Only one stage may be `in_progress`.
2. A stage cannot be approved while its predecessor is unapproved.
3. Required files and directories must exist and be non-empty.
4. Hash drift after approval blocks completion.
5. Final completion requires all six stages approved and drift-free.
6. `url-backfill` may upload only the one approved final preview per style from `05-preview-export/`; it must preserve that directory and write only to `06-url-backfill/`.
7. URL-backfill approval requires exact record/manifest/raw-map/normalized-map alignment, successful external URL validation, production six-field validation with image checks, and lossless JSON/CSV round-trip.
8. Source-plan approval requires a current official-catalog snapshot from the environment selected for the run, with the config endpoint verified against that selection. It is report-only context and cannot alter collection scope, priority, sampling strata, or stop conditions.
9. Concept approval requires a refreshed live official-catalog snapshot captured during the current concept review, plus current duplicate comparison and a nonbinding candidate-mix recommendation for human judgment. The static admin snapshot cannot satisfy either catalog invariant.
10. The concept decision registry may remain AI-proposed row by row; the concept-stage approval event is the human's batch acceptance, with only exceptions edited in the registry.
11. Final preview delivery contains exactly one generated reference image per style.
12. Admin writes, style creation, and plugin modification remain out of scope.

## Standard Output Shape

Stage 05 `styles.json` is a JSON array. Each record contains exactly:

```json
{
  "name": "string",
  "tags": ["string"],
  "description": "string",
  "analysis": "string",
  "promptSample": "string",
  "imageUrl": ""
}
```

Stage 05 `styles.csv` contains those six columns. `tags` is a JSON array encoded
inside the CSV cell. Stage 06 preserves the exact six-field shape and replaces
`imageUrl` with the externally verified HTTPS URL for the corresponding final
preview. No working metadata is added to either delivery.
