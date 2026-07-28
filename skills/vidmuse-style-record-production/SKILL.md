---
name: vidmuse-style-record-production
description: Convert approved VidMuse style concepts into the official six fields by following the complete canonical field standard, validate Planner and generation behavior, compile and package one final reference image per style, then upload the approved previews and produce a verified imageUrl-complete JSON/CSV delivery. Use after concept-stage approval or when rebuilding product records, previews, or URL-complete delivery files without changing the underlying style concept.
---

# VidMuse Style Record Production

Write product fields from approved visual evidence and boundaries. Do not use wording to rescue an invalid concept.

## Required Reading

Read the complete [style-library-field-standard.zh-CN.md](references/style-library-field-standard.zh-CN.md) in the current task before drafting any record. It is the content authority; this Skill summary, the schema, validator, authoring prompt, and examples cannot substitute for it. Then read [product-consumption.md](references/product-consumption.md) and [preview-generation.md](references/preview-generation.md). Use [record-authoring-prompt.md](references/record-authoring-prompt.md) for batch drafting only together with the full standard, and [quality-example.md](references/quality-example.md) only as a field-separation example. Before starting the final URL-backfill stage, also read [image-url-backfill.md](references/image-url-backfill.md) before uploading anything.

## 1. Confirm The Concept

Require:

- an `advance` decision accepted by the approved concept-stage review;
- the validated Anchor scope;
- transferable invariants and allowed variation;
- excluded source motifs;
- nearest-neighbor distinguishing rules;
- the concept-stage live-catalog comparison showing that the candidate has enough incremental value to proceed.

Do not draft from the Anchor name alone.

## 2. Derive The Fields

Use the complete field standard for every field. The evidence flow below is only the derivation order; it does not replace any content rule, field boundary, ordering rule, exception, or checklist in the standard:

1. `name`: translate the verified Anchor level into a clear user-facing identity.
2. `analysis`: preserve the complete, medium-appropriate visual mechanism and transfer limits.
3. `tags`: compress Analysis into ordered modality, family, distinctive controls, and optional visible finish.
4. `description`: add project fit, user intent, recommendation reason, and meaningful neighbor difference.
5. `promptSample`: compile the transferable visual recipe; it may repeat the name in its first phrase.
6. `imageUrl`: set to an empty string in staging output.

Keep fields free of source metadata, project-specific subjects and plots, model names, quality filler, weights, aspect ratios, resolutions, negative prompts, and generation commands. Preserve only generic motifs approved as necessary to a content-dependent style.

Validate draft records:

```powershell
python scripts/validate_style_record.py <records.json-or-jsonl> --staging --strict
```

## 3. Test Before Previewing

For each style, choose comparable test content inside both the target and nearest neighbor's declared scope. Use the same content on both sides, then vary content within the target's scope to confirm transfer. Do not require person, performance, interior, or environment tests when they are outside the style. This test verifies that the six fields preserve the approved distinction; it does not reopen official-library deduplication or concept admission. If the fields cannot preserve the boundary, revise the fields or return the concept to the concept stage.

Write `field-review.md` and `neighbor-review.md`. Obtain human approval before generating the full preview set.

## 4. Compile Preview Prompts

Use the compiler in `preview-generation.md` to create exactly one English prompt per style. It must use original, non-identifying content and make the approved visual identity legible without copying source content. Save one JSONL row per style to `preview-prompt-source.jsonl`:

```json
{"name": "Exact Style Name", "prompt": "..."}
```

## 5. Export Records And Image Tasks

Run the exporter before image generation so every prompt receives its final stable filename:

```powershell
python scripts/export_records.py `
  --records <style-records.staging.jsonl> `
  --prompts <preview-prompt-source.jsonl> `
  --output-dir <delivery-dir> `
  --strict
```

This creates `styles.json`, `styles.csv`, `preview-prompts.jsonl`, `preview-manifest.csv`, and an empty `previews/` directory.

## 6. Generate And Validate Images

Read each prompt and filename from `preview-manifest.csv`. Use the available image-generation tool to generate one image per style. Research frames are context only and must never be passed through as output previews.

Save each returned image to the exact manifest filename, for example:

```text
001__the-tree-of-life-inspired__preview.png
```

Validate the one-image-per-style package. If an image fails style or image QA, rewrite its prompt or regenerate it and replace the failed file; do not add extra candidates to the final package:

```powershell
python scripts/package_previews.py `
  --manifest <delivery-dir/preview-manifest.csv> `
  --preview-dir <delivery-dir/previews> `
  --strict
```

Deliver the approved `preview-export` directory and review reports with
`imageUrl` still empty. This frozen staging package is the input to the formal
sixth stage. Never write the admin from this Skill.

## 7. Upload And Backfill Image URLs

Run this formal next stage only after the one-image-per-style package is
approved. Follow `image-url-backfill.md` exactly.

- Use the dev CLI config and create a VidMuse thread with
  `--plugin-id Evals-bread-img`.
- Upload one final preview per manifest row in stable order, with queue-aware
  throttling.
- Make the Planner copy each upload to the physical
  `workspace/assets/images/` directory and return an ordered mapping.
- Verify each CDN URL independently. Local file existence is not URL proof.
- Run `scripts/backfill_image_urls.py` to join by exact `styleIndex`, `name`,
  and `fileName`.
- Save the Planner response as `06-url-backfill/planner-image-url-map.json`, then write the normalized result to the same stage directory; do not
  mutate the approved preview-export package.

The backfill output contains URL-complete six-field `styles.json` and
`styles.csv`, the raw Planner URL map, the normalized URL map, and the
network-validation report. Run production record validation with image checks,
then submit the complete `06-url-backfill/` package for sixth-stage approval.
This stage still does not create styles or write the admin.