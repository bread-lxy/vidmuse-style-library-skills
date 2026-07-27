# Preview Prompt And Image Production

## Compiler Input

For each approved record provide `name`, ordered `tags`, `description`, `analysis`, `promptSample`, evidence-supported visual summary, nearest-style boundary, content dependency, and excluded source content.

## Compiler Instruction

```text
You are the VidMuse Preview Prompt Compiler.

Create exactly one plain-English image prompt for the style's final original reference image.

Requirements:
1. Preserve the approved style identity expressed by the name, ordered tags, analysis, and prompt sample.
2. Choose original, non-identifying content appropriate to the medium and project use.
3. Each prompt must visibly demonstrate at least three highest-priority, medium-appropriate style traits. Color, lighting, lens, or spatial traits are required only when they define this style.
4. Choose content and composition that reveal the style within its declared scope without depending on a source-specific motif.
5. Preserve only a content motif that the approved content-dependency rule says is necessary for the style to exist.
6. Do not reproduce actors, protected characters, named locations, iconic scenes, titles, logos, dialogue, or recognizable text.
7. Do not mention research sources, evidence frames, model names, quality filler, weights, aspect ratio, resolution, negative prompts, or generation commands.

Return JSON only:
{"name": "<exact style name>", "prompt": "..."}
```

## Image Generation

Generate one image per style with the same model configuration for the batch. Model settings remain outside the style record and compiler output.

Save each returned asset using `NNN__style-name-slug__preview.png`. Use the smallest lossless transformation needed to preserve the generated image. Do not use research evidence as an output image or as an image-to-image source.

## Review

Reject a preview for weak or generic identity, subject-driven resemblance, missing core controls, protected identity or text, visible artifacts, or a closer match to a neighboring style. Rewrite the prompt or regenerate and replace a failed image. The final package contains exactly one approved reference image per style.