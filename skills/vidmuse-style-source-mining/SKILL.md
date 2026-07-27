---
name: vidmuse-style-source-mining
description: Research and collect a public or local visual-material source, then normalize images, artworks, spatial views, game captures, film or animation frames, continuous video, and other reviewable visual units into a traceable, deduplicated, source-agnostic VidMuse EvidenceRecord library. Use before style clustering to produce separate source-plan and evidence review packages without treating source labels as style truth.
---

# VidMuse Style Source Mining

Adapt to the source instead of forcing a universal scraper. Keep the output contract stable even when collection methods differ.

## 1. Reconnoiter Before Collecting

Read [source-reconnaissance.md](references/source-reconnaissance.md) and [evidence-contract.md](references/evidence-contract.md). Use the bundled source-assessment and data-quality templates; validate collection plans against `references/collection-plan.schema.json`.

Inspect the real source with the browser, public APIs, downloadable datasets, or local files. Before the first source-plan review, capture the current official style catalog from the environment selected for the run and save it as `official-style-catalog.json`; verify that the config endpoint matches that selection. Report the catalog's visible visual-form distribution, obvious gaps, and the limits of that reading. This snapshot is review context only: it must not change the source scope, sampling strata, collection priority, or stop conditions.

Establish:

- discoverable entities and Anchor candidates;
- search, browse, detail, pagination, and asset-download paths;
- which metadata is observed, inferred, missing, or unreliable;
- the evidence unit and whether it supports static appearance, continuous motion, editing structure, or other declared claims;
- source-group, context, and independence policies for this source;
- target coverage, sampling strata, and explicit stop conditions;
- terms, license, attribution, login, rate, and publication facts for provenance and downstream reuse decisions.

Write `official-style-catalog.json`, `source-assessment.md`, `collection-plan.json`, and a real pilot under `sample/`. Validate the plan with `python scripts/validate_collection_plan.py <collection-plan.json>`. Scale after the pilot proves that extraction and evidence normalization work. A human may comment on scope or method, but `research_only`, `unknown`, or downstream publication limits do not by themselves narrow or stop research collection.

## 2. Collect Adaptively

Choose the strongest reliable route for this source: browser automation, documented/public endpoint, dataset download, or local import. Let the model design source-specific extraction, but preserve these invariants:

- save source URL or stable source ID and collection time;
- save the local asset and its relationship to every query/Anchor that found it;
- resume without duplicating assets;
- retain raw source values before normalization;
- quarantine missing, corrupt, inaccessible, or ambiguous items;
- do not bypass access controls or conceal source restrictions; record them without treating downstream preview eligibility as a collection filter.

The ShotDeck case study in [shotdeck-case-study.md](references/shotdeck-case-study.md) is an example, not a universal schema.

## 3. Normalize Evidence

Create a mapping file from the source fields to the canonical contract. Start from [mapping.example.json](references/mapping.example.json). When source metadata lacks observable visual features, apply [visual-feature-extraction.md](references/visual-feature-extraction.md) to the assets before strict validation.

```powershell
python scripts/normalize_evidence.py `
  --input <raw.jsonl-or-csv> `
  --mapping <mapping.json> `
  --asset-root <asset-root> `
  --output <evidence.jsonl> `
  --quarantine <quarantine.json> `
  --report <data-quality.md>

python scripts/validate_evidence.py <evidence.jsonl> --asset-root <asset-root> --strict

python scripts/build_evidence_contact_sheet.py `
  --evidence <evidence.jsonl> `
  --asset-root <asset-root> `
  --output <stage-dir>/review/contact-sheet.html
```

Separate:

- `styleFeatures`: visually observable membership evidence;
- `contentFeatures`: people, objects, story, location, or scene content;
- `provenance`: source entities, creators, works, queries, and acquisition facts.

Never move a value between those channels merely to improve clustering.

## 4. Deliver The Evidence Gate

Produce:

- `raw-manifest.jsonl`;
- `evidence.jsonl`;
- `quarantine.json`;
- `data-quality.md`;
- `mapping.json`, the local `assets/` tree, and a contact sheet generated with `build_evidence_contact_sheet.py`;
- coverage by medium, source group, context, style-feature field, rights state, and evidence capability.

The human reviewer approves evidence quality and coverage, not a claim that every record is a style or that every collected asset is eligible for public reuse. Research evidence remains collectible when its rights state is `research_only` or `unknown`; that state is carried forward for later use decisions.