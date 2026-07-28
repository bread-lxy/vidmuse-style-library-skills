---
name: vidmuse-style-pipeline
description: Orchestrate a complete, resumable VidMuse style-library production run from a new visual source through evidence normalization, live-catalog-aware Anchor concept review, six-field records, one reference image per style, and a verified imageUrl-complete JSON/CSV delivery. Use when starting, resuming, auditing, or rerunning a multi-stage batch of official VidMuse style candidates. Keep human review lightweight but explicit at stage boundaries and never write the online admin.
---

# VidMuse Style Pipeline

Coordinate the three stage skills. Keep judgment inside the relevant stage and keep state, approvals, standards drift, and final delivery here.

## Start Or Resume

1. Read [pipeline-contract.md](references/pipeline-contract.md) and [source-of-truth.md](references/source-of-truth.md).
2. Verify the bundled standards snapshot:

```powershell
python scripts/verify_standards.py check
```

3. Initialize a run, or inspect an existing one:

```powershell
python scripts/run_pipeline.py init <run-dir> --name "<run name>" --source "<source>"
python scripts/run_pipeline.py status <run-dir>
```

4. Work only on the stage reported as `ready` or `in_progress`.
5. Use the matching stage skill and place its standard artifacts in the stage directory.
6. Ask the human reviewer to inspect the complete stage package. Record an approval only after they explicitly accept it:

```powershell
python scripts/run_pipeline.py approve <run-dir> --stage <stage> --reviewer "<name>" --note "<decision>"
```

Approval freezes hashes of all required artifacts. Do not silently regenerate an approved stage.

## Stage Routing

| Stage | Use | Required decision |
|---|---|---|
| `source-plan` | `vidmuse-style-source-mining` | Source structure, collection viability, pilot strategy, and a report-only snapshot of the selected official catalog; catalog gaps and rights do not narrow research collection |
| `evidence` | `vidmuse-style-source-mining` | Evidence quality, independence, coverage |
| `concept` | `vidmuse-style-concept-curation` | Live official-catalog comparison plus advance, merge, split, hold, or reject |
| `records` | `vidmuse-style-record-production` | Six-field fidelity and neighbor separation |
| `preview-export` | `vidmuse-style-record-production` | One final reference image per style and package integrity |
| `url-backfill` | `vidmuse-style-record-production` | Exact record/image mapping, externally valid HTTPS URLs, and URL-complete package integrity |

AI pre-populates the complete concept decision registry. The human reviews the batch and edits only exceptions; the stage approval records acceptance of all unedited AI proposals.

## Finalize URL-Complete Delivery

After `preview-export` approval, run `url-backfill` as the formal sixth stage.
Call the upload and backfill flow in `vidmuse-style-record-production`, write
its artifacts to `06-url-backfill/`, and obtain stage approval after every URL
and JSON/CSV output passes validation. Preserve the approved
`05-preview-export/` package unchanged; the sixth stage derives from it rather
than replacing it.

## Reopen Safely

When an approved input, standard, or decision changes, reopen from the earliest affected stage:

```powershell
python scripts/run_pipeline.py reopen <run-dir> --stage <stage> --reviewer "<name>" --note "<reason>"
```

This marks the stage and all downstream approvals stale. It preserves every artifact, approval, and note.

## Non-Negotiable Rules

- Keep research evidence separate from generated previews and production output.
- Keep source metadata out of visual membership features and production prompts.
- Capture the official catalog from the environment selected for the run before the first source-plan review, and verify that the config endpoint matches that selection. Treat this first snapshot as report-only context that cannot steer collection. Refresh it during concept review for current duplicate checks and a nonbinding candidate-mix recommendation. Static admin snapshots are field-shape fallback only.
- Keep `imageUrl` empty in the approved `preview-export` staging package. The formal `url-backfill` stage then uploads only those approved final previews and produces the URL-complete delivery.
- Run URL backfill against the VidMuse dev environment with the `Evals-bread-img` plugin. Preserve the approved preview-export package, verify every final HTTPS image URL independently, and write the sixth-stage delivery separately.
- Do not call the admin create API or modify the plugin.
- Treat bundled standards as authoritative in the order documented in `source-of-truth.md`.
- If standards drift, stop and report the changed source before continuing.

## Completion

The run is complete only when all six stages are approved, `status` reports no
artifact drift, all staging records pass strict validation, JSON/CSV
round-trip, and every style has exactly one correctly named final reference
image. The final stage additionally requires exact
record/manifest/URL-map alignment, successful external network validation for
every image, production validation of the URL-complete records, and
URL-complete JSON/CSV round-trip in `06-url-backfill/`.