# VidMuse Visual Style Ontology Decision Log

Status: Gate 3 reviewed record  
Last updated: 2026-07-14

This file records decisions that constrain `docs/style-clustering-standard.md` and the V1 anchor catalog. A later decision supersedes an earlier one when they conflict.

## D-001: Use cluster-first C+

- Status: accepted
- Decision: A V1 style category is defined by a repeatable and separable static visual signature. Directors, works, studios, movements, techniques, and community labels provide evidence or naming references; they do not automatically determine the category.
- Reason: entity-first grouping over-merges long careers and studio catalogs, while feature-only grouping fragments styles into colors, lighting traits, or content motifs.

## D-002: Keep the V1 model to three blocks

- Status: accepted
- Decision:
  - `StyleConcept = Signature + Scope + Boundary`
  - `AnchorSet = positive references + provenance + boundary negatives`
  - `ProductProfile = display/search fields + generation recipe + validation state`
- Reason: the seven-object research model clarified concepts but would add maintenance cost without improving Planner behavior in V1.

## D-003: Separate concept existence from product readiness

- Status: accepted
- Decision: stability and separability establish a `StyleConcept`. Product value and current executability determine whether it becomes an Active `ProductStyle`.
- Consequence: a historically or perceptually valid style can remain `concept_only` when the current Planner or generation stack cannot use it reliably.

## D-004: Give Anchor one meaning

- Status: accepted
- Decision: an Anchor is a concrete reference sample or reference source used to support and recognize a style. It never defines the style by itself.
- Consequence: person names, work names, movement names, and technique names are stored as provenance and may also become display labels or aliases after validation. V1 does not create multiple Anchor role types.

## D-005: Use a compact, orthogonal Scope

- Status: accepted, revised in Gate 3 review
- Decision: Scope records `realizationMedia` and controlled `contentDomains(mode + operator + values)`.
- Consequence: architecture is a content domain, not a medium; cross-media is derived from separately validated static evidence rather than stored as a pseudo-medium.

## D-006: Use three questions and five outcomes

- Status: accepted
- Decision:
  1. Stability: does the signature repeat inside the claimed Scope?
  2. Separability: does it remain distinguishable from the nearest neighbor without source names or iconic content?
  3. Product value: does a split change a real product action and produce a measurable selection or output difference?
- Outcomes: `merge`, `split`, `parent_child`, `related`, or `hold`.
- Consequence: Q1 and Q2 decide concept boundaries. Q3 decides production exposure. Over-merging and over-splitting are treated as equal risks.

## D-007: Cluster medium-appropriate evidence units, not source entities

- Status: accepted, revised in Gate 3 review
- Decision:
  - Static discovery supports `film_shot`, `photograph`, `artwork`, `architecture_view_set`, and `game_capture`.
  - Each unit has an independence key; crops, adjacent frames, repeated queries, and multiple views of one building do not create false independent observations.
  - Director, work, query, genre, character, location, and candidate labels are excluded from the style vector.
- Consequence: ShotDeck can support static film-shot discovery but cannot establish motion/editing, architectural-spatial, authorship, or cross-media claims by itself.

## D-008: Separate retrieval and generation tags

- Status: accepted, compatibility rule revised in Gate 3 review
- Decision: `retrievalTags` serve Planner/search; `generationTags` serve prompt compilation. Raw source tags are provenance only.
- Target contract: summary exposes retrieval tags and Scope; DSL/compiler consume generation tags only.
- Transitional rule: current backend `tags` project reviewed `generationTags` only. Mood, usage, aliases, and untested proper nouns are not projected merely to improve recall.

## D-009: Use tiered validation

- Status: accepted
- Decision:
  - Concept mandatory: stability and nearest-neighbor separability.
  - Production mandatory: product value, basic execution, and preview/name consistency.
  - Conditional: cross-media, content-scope, named-entity expectation, and legal/source tests.
  - Portfolio monitoring: cluster metrics, reviewer agreement, coverage, and confusion.
- Reason: ten universal hard gates would reject valid scoped styles and waste review effort.

## D-010: Use lightweight relations in V1

- Status: accepted
- Decision: each StyleConcept may have one primary parent, multiple related styles, aliases, and retrieval tags. Full multi-parent graph reasoning is deferred.

## D-011: Keep naming compatible with the current 79-style catalog

- Status: accepted
- Decision:
  - Recognizable person or creator collective: `X Inspired`.
  - Recognizable work or IP: `X Inspired`.
  - Established movement, subculture, or technique: established concise term.
  - Scope qualifier is added only when needed to prevent a false broad claim.
- Consequence: new names should resemble `Shunji Iwai Inspired`, `Blade Runner 2049 Inspired`, `Dreamcore`, and `Claymation`, not technical cluster IDs or long feature strings.

## D-012: Separate evidence, concept, and active scale

- Status: accepted
- Decision: evidence and candidate libraries may exceed 100. The number of StyleConcepts follows boundary evidence. Active ProductStyles follow product value and current retrieval capacity.
- Current constraint: the default plugin reads up to 100 official summary records in one call. This is an implementation limit, not an ontology limit; Top-K retrieval or indexed search may replace it later.

## D-013: Treat the final anchor catalog as a governed seed universe

- Status: accepted
- Decision: the catalog includes all 79 current backend names for compatibility plus curated proposed concepts that cover material gaps. Inclusion means "eligible for evidence collection and boundary testing," not "approved for immediate production."
- Statuses:
  - `existing_retain`: current entry appears conceptually sound enough to retain pending normal regression QA.
  - `existing_review`: current entry remains visible for compatibility but has a boundary, naming, or Scope issue to resolve.
  - `proposed`: new candidate eligible for evidence collection and the three-question review.
  - `concept_only`: valid concept that should not yet be Active.

## D-014: Make current implementation gaps activation blockers

- Status: accepted after independent adversarial review
- Decision: the present summary payload and DSL cannot enforce Scope or separate retrieval from prompt controls. New required-content styles cannot become Active until summary, DSL, and compiler expose the target contract.
- Reason: documentation in `description` does not create a deterministic Planner filter, and the current `tags` field is copied verbatim into prompts.

## D-015: Adopt reproducible V1 thresholds

- Status: accepted after independent adversarial review
- Decision: Q1 uses medium-aware minimum evidence, 25% source-level holdout, 75% invariant support, and 80% reviewer agreement. Q2 uses Top-5 neighbor generation, the two hardest neighbors, 12 matched comparisons per neighbor, 9/12 accuracy, and 80% agreement. Q3 uses a predeclared merge baseline and action-specific minimum effect.
- Consequence: thresholds may be recalibrated globally through this log after pilot data, but never relaxed for one famous or preferred candidate.

## D-016: Remove temporal identity from V1

- Status: superseded by evidence-scope confirmation
- Decision: the first reviewed draft introduced temporal identity fields, but the project corpus contains no continuous clips. V1 removes those fields entirely.
- Consequence: candidates requiring non-static evidence use the generic rejection state `out_of_scope` with reason `requires_non_static_evidence`; no dedicated identity field or synthetic value is inferred from stills.

## D-017: Treat the catalog as coverage hypotheses, not entity bins

- Status: superseded for official style candidate creation by D-024
- Decision: catalog reference sources guide sampling and later interpretation. AI discovery uses anonymous evidence IDs and anonymous hypothesis IDs before provenance is restored.
- Consequence: a director/work seed may map to zero, one, or several clusters; several seeds may merge into one StyleConcept; a discovered cluster may have no prior seed.

## D-018: Record actual Active state separately from conceptual disposition

- Status: accepted after independent adversarial review
- Decision: catalog `activation_state` distinguishes V1-ready `current_active`, visible-but-unvalidated `legacy_active_review`, and `inactive_candidate`; `v1_readiness` records the blocker independently.
- Consequence: all 79 current backend rows remain traceable as `legacy_active_review + blocked_runtime_contract`. Editorial disposition still distinguishes 29 retain from 50 review rows, but none is treated as V1 ground truth. Visible capacity remains 21 until the 100-record retrieval limit changes.

## D-019: Require machine-checkable records and deterministic policy fixtures

- Status: accepted after independent adversarial review
- Decision: the working template is paired with JSON Schema and cross-record lint; exploratory art-direction questions are separated from policy regression fixtures with one expected assertion.
- Reason: a prose checklist cannot prevent `active` records whose tests were never run or non-visible claims supported only by still images.

## D-020: Make Gate 3 static-evidence-only

- Status: accepted by product owner
- Decision: all V1 invariants, clusters, boundaries, and catalog hints must be provable from still images, photographs, artworks, static game captures, or architectural view sets.
- Excluded: camera movement, shot duration, editing, animation cadence, audiovisual synchronization, and any other rule requiring ordered frames.
- Product consequence: VidMuse may apply a validated static appearance recipe to image, storyboard-frame, or video-frame appearance generation. Product execution does not expand what the research corpus proves.

## D-021: Encode runtime gaps as deterministic activation blockers

- Status: accepted after final independent closure audit
- Decision: every ProductProfile records `activationReadiness`, including Scope visibility/filtering, DSL propagation, generation-tags-only projection, compiler contract version, and a full-prompt smoke test.
- Consequence: `active` requires every runtime flag and smoke-test assertion to pass. The current plugin may remain unchanged in this design phase, but its missing contract can no longer be hidden in prose.

## D-022: Treat catalog media and content values as unverified hints

- Status: accepted after final independent closure audit
- Decision: name-derived catalog columns are renamed `unverified_source_hint`, `unverified_media_hint`, and `unverified_content_hint`. They guide sampling only and cannot become Scope or Planner filters without evidence review.
- Consequence: each discovery batch caps proper-name-seeded proposals at 50%, reserves at least 30% for feature-led anonymous discovery, and uses at least 20% long-tail evidence groups outside current official labels.

## D-023: Make validation executable end to end

- Status: accepted after final independent closure audit
- Decision: the record validator runs Draft 2020-12 Schema first, then cross-field semantic lint. Q1/Q2/Q3 measurements, per-medium evidence/holdout coverage, preview-name results, and runtime readiness are required structures.
- Consequence: R01-R12 have an executable runner, and regression tests cover illegal schema values, non-static claims in identity/generation fields, cross-media gaps, prompt pollution, threshold bypasses, and activation bypasses.

## D-024: Adopt Anchor-first rules for official style candidate creation

- Status: accepted by product owner
- Decision:
  - The same director, work, or movement does not automatically constitute one style. An Anchor defines the candidate material range, not the clustering result.
  - Official style candidates start from a pre-existing, explainable Anchor. AI visual clustering validates, splits, and deduplicates Anchor-based candidates; it does not turn an unanchored visual cluster directly into an official style.
  - Admission requires stable visual rules, distinguishable generation results, and a meaningful Planner selection difference. Visual-filter quantity is not treated as style-library richness.
  - The approved focused rules are recorded in [style-clustering-rules.zh-CN.md](../../vidmuse-style-concept-curation/references/style-clustering-rules.zh-CN.md).
- Supersedes: D-017's allowance for an anonymous cluster with no prior seed to become an official style candidate. Anonymous visual clusters may still support research and duplicate discovery, but do not enter the official library directly.
- Scope: this decision does not adopt additional numeric evidence thresholds or additional static/video evidence rules.

## D-025: Adopt the model-agnostic six-field V2 production contract

- Status: superseded by D-026 for content semantics; retained as the history of the first machine-contract implementation
- Decision:
  - New style records use exactly `name`, `tags`, `description`, `analysis`, `promptSample`, and `imageUrl`, with English-only production content.
  - `tags` are the concise high-priority signature; `promptSample` is a 6-10 phrase style shell; `analysis` uses one fixed five-section structure across modalities.
  - Model names, quality filler, weighting, output parameters, negative instructions, source metadata, and concrete narrative content are not style-library data.
  - V1 is frozen for historical reproducibility; new and rewritten records use V2 only.
- Implementation clarification: because the first tag must equal `name`, its limit inherits the 48-character name limit. The remaining feature tags retain the approved 40-character limit; the joined total remains 180.
- Artifacts: `docs/style-library-field-standard.zh-CN.md`, `style-library-schema-taxonomy/style-record.schema.json`, and `style-library-schema-taxonomy/validate_style_record.py`.

## D-026: Make the human content standard authoritative

- Status: accepted by product owner and implemented on 2026-07-17
- Decision:
  - The six production fields remain `name`, `tags`, `description`, `analysis`, `promptSample`, and `imageUrl`; no production metadata fields are added.
  - Content logic comes before character counts, fixed sentence counts, validator severities, or one universal Analysis template. Backend and plugin implementation should adapt to the content contract.
  - Full-catalog matching reads `name + tags`; shortlisted candidates use `description`; confirmed styles use `analysis + promptSample`; `imageUrl` is the user's visual proof.
  - `tags` are an ordered, prompt-safe visual fingerprint. `analysis` adapts to medium and includes temporal rules only when they are style-defining. `promptSample` is a model-agnostic style shell placed after image content.
  - Preview images use original neutral content by default, with narrowly scoped exceptions for content-dependent Anchors such as Poolcore.
- Consequence: the previous V2 numeric limits, fixed headings, and strict validator remain technical reference material until engineering constraints are redesigned. They cannot reject semantically valid content or override the human standard.
- Artifact: `docs/style-library-field-standard.zh-CN.md`.

## D-027: Make the style pipeline catalog-aware and medium-adaptive

- Status: accepted by product owner and implemented on 2026-07-27
- Decision:
  - Capture the official catalog from the environment selected for the run before the first source-plan review, but use it only as reported context; it must not alter collection scope, priority, sampling, or stop conditions. Refresh it during concept review for duplicate and incremental-value decisions, summarize the candidate mix, and give a nonbinding advance-proportion recommendation for human judgment.
  - Evidence capabilities are source-adaptive. Images and frames can support static appearance; retained continuous media can support motion, editing, or timing when its adapter preserves the required order and context.
  - Define transferability and neighbor tests within each style's declared scope. Use medium-appropriate visual dimensions rather than requiring cinematography fields or universal person/performance/interior/environment tests.
  - Use an extensible canonical visual-form vocabulary. Known aliases must normalize to the canonical term; plausible new forms and content-dependent generic motifs require human review instead of automatic rejection.
- Consequence: ShotDeck remains a valid film-source adapter, but film fields, still-image assumptions, and cinematography assumptions do not define the reusable contract. Deterministic prompt pollution remains a hard error; open taxonomy and scoped content judgments remain review decisions.
- Artifacts: `docs/style-clustering-rules.zh-CN.md`, `docs/style-library-field-standard.zh-CN.md`, `style-library-schema-taxonomy/style-library-taxonomy.json`, and the four reusable VidMuse style Skills.
