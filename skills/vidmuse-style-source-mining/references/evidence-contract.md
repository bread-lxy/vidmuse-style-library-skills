# Canonical EvidenceRecord

The contract represents visual evidence, not a style and not a source-specific row.

## Required Fields

| Field | Meaning |
|---|---|
| `evidenceId` | Stable ID unique within the corpus |
| `unitType` | Medium-appropriate unit such as `film_frame`, `video_segment`, `photograph`, `artwork`, `architecture_view`, or `game_capture` |
| `medium` | Visual realization medium |
| `source` | Stable URL or source identifier |
| `localAssetPath` | Local asset path relative to the declared asset root |
| `sourceGroupKey` | Work, collection, building, project, or other source-level independence group |
| `contextKey` | Scene, sequence, session, facade/view set, or other local context |
| `independenceKey` | One independent evidence unit |
| `styleFeatures` | Observable image-formation features allowed for clustering |
| `contentFeatures` | Subjects, objects, actions, story, locations, and motifs |
| `evidenceCapabilities` | Claims the unit can actually support |
| `provenance` | Creators, works, queries, raw IDs, timestamps, and collection facts |
| `licenseStatus` | `research_only`, `licensed`, `generated`, `public_domain`, or `unknown` |
| `researchOnly` | Whether the asset is prohibited from production preview use |
| `fileSha256` | Exact-duplicate hash |
| `differenceHash` | Optional image perceptual hash |
| `duplicateOf` | Canonical exact duplicate or null |
| `nearDuplicateOf` | Canonical near duplicate or null |

## Evidence Capabilities

- `static_appearance`: color, light, composition, form, texture, and optical finish visible in an image or frame.
- `continuous_motion`: camera, subject, graphic, or material movement observable across an ordered clip.
- `temporal_structure`: duration, repetition, cadence, transition, or sequence behavior observable from preserved temporal evidence.
- `editing_pattern`: shot-to-shot organization supported by a sequence with edit boundaries.
- `authorship_context`: reliable creator/work provenance; never a visual membership feature.

Capability names are extensible because sources differ. Each declared capability must be justified by the retained evidence unit and its adapter. Static evidence supports static claims; temporal claims require evidence that preserves order, duration, and the relevant context.

## Channel Separation

`styleFeatures` may include medium-appropriate observable color, value, light or volume, spatial organization, shape, mark-making, material, rendering, optical character, layout, graphic layering, movement, transition, editing rhythm, and temporal structure when the evidence capability supports them.

`contentFeatures` includes identity, actors, characters, props, architecture subjects, locations, plot, actions, genre labels, emotions, and source search tags unless a reviewed content-dependent style requires them later.

`provenance` includes names and source facts. It may define Anchor membership after visual discovery but must not drive the initial cluster.

## Independence Policies By Source

The three keys are source-adaptive, but their meaning must be fixed in `collection-plan.json` before the pilot is approved. A repeated discovery never creates a second evidence row; record all Anchor/query memberships in provenance.

| Source family | `sourceGroupKey` | `contextKey` | `independenceKey` |
|---|---|---|---|
| Extracted film, animation, or MV frames | work or production project | scene or sequence | independent frame after adjacent-frame and near-duplicate collapse |
| Continuous video or clip collections | work, episode, MV, performance, or production project | sequence, scene, take, or edit passage | independent clip or sequence after overlap and near-duplicate collapse |
| Artwork | work, series, or collection at the level of the claim | whole work or related detail set | original work; detail crops remain in the same context and are not independent |
| Architecture | building or project | facade, room, or coordinated view set | independent view set or photograph, as declared for the hypothesis |
| Photography | project or series | session, location, or contact-sheet context | original photograph after burst and near-duplicate collapse |
| Game capture | title, level family, or authored environment set | encounter, location, or sequence | independent capture after repeated-angle collapse |

The policy must answer what can be counted independently, what must remain grouped, and what source-level unit must be excluded together during a boundary test. Do not copy film assumptions into artwork, architecture, or other media.

## Anchor Membership

Anchor discovery belongs in `provenance.anchorMemberships`, as an array of objects such as `{ "anchorType": "work", "anchorName": "...", "basis": "source_metadata" }`. Membership is many-to-many: one evidence record may support several candidate ranges. It is never duplicated solely because two Anchors found it, and it remains hidden during feature-led clustering.
