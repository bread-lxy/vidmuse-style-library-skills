# Source-Of-Truth Order

Use the first applicable source below. A lower tier cannot override a higher tier.

## 1. Human Content Authority

- `style-clustering-rules.zh-CN.md`: what counts as a style and how Anchor scope is chosen.
- `style-library-field-standard.zh-CN.md`: what each production field means and how it is written.
- Decision log D-024 to D-027: Anchor-first official candidates, model-agnostic six fields, human standard authority, and catalog-aware medium adaptation.

## 2. Current Product Facts

- Live `vidmuse style list --scope official` results captured from the environment selected for the run, with the config endpoint verified against that selection: current names, tags, IDs, and duplicate-check scope.
- Current admin HTML snapshot: fallback evidence for visible field shape and historical comparison only.
- Default plugin style selector and prompt compiler: actual field consumption.
- Current schema and validator: machine shape and deterministic lint.

Product facts describe current behavior. They do not redefine style content.

The live official catalog is a runtime input, so it is saved inside each run rather than hashed into the bundled standards manifest. If live CLI access is unavailable, source mining may continue, but no concept may be approved from a static catalog alone unless the reviewer explicitly accepts that stale-data risk.

## 3. Reusable Execution Evidence

- Phase 3 evidence preparation, clustering, sibling-exclusion review, and decision registry.
- Batch 001/002 review and 24 productization candidates.
- Duplicate/high-affinity retention review.
- Boundary fixtures and regression tests.

## 4. Historical Evidence Only

Never use these as current templates:

- the first 284 field-shape candidates;
- the six Phase 2 examples;
- rules requiring `(masterpiece)`, `best quality`, `16:9`, or `No black borders`;
- Midterm text that conflicts with the current field standard.

Historical artifacts may explain failures and compatibility. They cannot admit or author a new style.