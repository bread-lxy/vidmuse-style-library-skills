# ShotDeck Case Study

ShotDeck validated the workflow but is not the generic contract.

## What Worked

- A real browser session handled login and discovery.
- Detail metadata came from the item-detail endpoint, with visible-modal fallback.
- Resume identity used `shot_id::query_id`, while repeated discoveries of the same shot were later merged.
- Local media, source URL, query memberships, credits, and visual metadata remained traceable.
- Exact hashes and perceptual hashes removed duplicate and near-duplicate evidence.
- Style metadata and content metadata were separated before clustering.

## Frozen Results

- 5,807 raw rows.
- 5,703 valid rows.
- 5,057 unique ShotDeck IDs.
- 4,839 local-image evidence records in the Phase 3 frozen manifest.
- 4,825 independent records after dedupe.

## What Must Not Generalize

- `film_title`, `shot_time`, `directors`, and `cinematographers` are ShotDeck provenance fields.
- `film_shot` and five-minute scene buckets are film-specific evidence choices.
- ShotDeck color/light/composition labels are one source's ontology.
- Metadata consensus is not proof of a coherent visual recipe.
- `framing` duplicated `frame_size` in 95.3% of the corpus and must not receive duplicate weight.
- All ShotDeck assets remain `research_only` and cannot become production preview images.