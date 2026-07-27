# Adaptive Source Reconnaissance

## Inspect

1. Open the real browse/search experience.
2. Identify entity types, filters, result pagination, detail pages, media URLs, and stable IDs.
3. Compare visible metadata with any public endpoint or downloadable dataset.
4. Test one item from discovery through local download and provenance capture.
5. Read accessible terms, license, attribution, robots, authentication, rate, and redistribution information. Record these as provenance and downstream-use facts; do not use preview eligibility alone to narrow the research corpus.

## Plan

Write `collection-plan.json` with:

- source name and URLs;
- media and evidence-unit hypothesis;
- collection route and fallback;
- discovery queries or coverage strata;
- raw fields and their confidence;
- checkpoint and dedupe keys;
- rights handling;
- pilot success and stop conditions;
- expected style/content/provenance channel mapping.

The plan may use source-specific fields. Only the resulting EvidenceRecord is universal.

## Pilot

Collect a small but structurally representative sample. It must exercise every intended discovery route, detail extraction path, media type, and major error mode. Validate stable IDs, source links, asset integrity, extraction repeatability, clustering viability, query memberships, and rights metadata capture. A research-only or unknown rights state is recorded, not treated as a failed pilot.

Scale only after the reviewer accepts the source assessment and pilot.

## Full Collection

Checkpoint after each item or page. Reopening a query must not duplicate an asset. Preserve every query membership and choose the richest raw record as the canonical row. Keep failed rows in quarantine with a reason; do not silently drop them.