# Current VidMuse Field Consumption

This reference records current product behavior. The human field standard remains authoritative for content.

## Selection

- `style list --scope official --view summary` returns `id`, `name`, `tags`, and `imageUrl`.
- The current Planner selects from `name + tags`; `imageUrl` calibrates user expectation.
- `style get <id> --view full` returns `description`, `analysis`, and `promptSample` after confirmation or an exact result.
- At larger library sizes, use the first tag layers for coarse filtering and read shortlisted descriptions for reranking. The current default selector's 100-item summary limit is an implementation constraint, not a content rule.

## Generation

- T2I, T2V, and I2I copy `visualStyle.tags` verbatim to the prompt front.
- `promptSample` is the baseline style shell after project content.
- `analysis` expands missing medium- and shot-appropriate visual detail.
- `description` is selection rationale and does not enter the generation prompt.

## Implications

- Tags must be both retrieval-useful and visually executable.
- Retrieval-only music, audience, or project labels belong in Description, not Tags.
- Prompt Sample may repeat the Anchor name when it materially improves execution.
- Model adapters, quality settings, aspect ratio, resolution, and negative prompts belong to the calling layer.