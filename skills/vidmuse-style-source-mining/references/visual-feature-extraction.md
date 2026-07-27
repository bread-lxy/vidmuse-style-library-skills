# Model-Assisted Visual Feature Extraction

Use this only when source metadata does not already provide reliable observable visual features. Route each retained evidence unit to an analyzer that can inspect its actual form: image models for still assets and temporal/video analysis for ordered clips or sequences.

## Input

For each asset provide only:

- anonymous evidence ID;
- medium and unit type;
- declared evidence capabilities;
- the visual asset or a reviewable proxy that preserves the ordering and context required by its declared capabilities.

Hide Anchor names, creator/work names, query labels, popularity, genre, story, and existing style names during extraction.

## Choose Dimensions By Medium

Use only dimensions that explain how the current medium forms its visible result:

| Medium | Useful dimensions |
|---|---|
| Live-action image or frame | lens and image formation, exposure, lighting, composition and space, optical or post-process finish |
| Continuous video | the applicable frame-level dimensions plus camera/subject movement, duration, cadence, transitions, and editing structure supported by the retained sequence |
| Photography | photographic process, composition, tonality, lighting, optics and surface finish |
| Painting and drawing | mark-making, line, shape, pigment or paper, color relationships and pictorial space |
| 2D illustration or animation frame | line, deformation, color, planar depth and drawn surface |
| 3D or game capture | modeling, proportion, material response, rendering and spatial organization |
| Graphic design | layout, graphic shape, type relationship when present, color system and print or digital surface |
| Architecture or spatial design | massing, geometry, material, scale, spatial rhythm and the role of light in space |
| Mixed media | layer structure, medium edges, compositing and material relationships |

Do not force lens, camera, lighting, or every listed dimension onto media where they do not define the image. Leave unsupported dimensions absent rather than filling them with generic language.

## Extraction Prompt

```text
Analyze this visual evidence for later style clustering.

Return objective, positive, observable features only. Select medium-appropriate dimensions from the routing guidance above. Describe visible mechanisms rather than filling a universal photography template.

Separate any subject, character, object, action, location, story, or semantic motif into contentFeatures. Do not use proper names, genre, mood labels without visible mechanisms, quality judgments, or a known style label as styleFeatures. Match every claim to the declared evidence capability: temporal features require ordered temporal evidence, while still assets support only features visible in those assets.

Return JSON only:
{
  "evidenceId": "<anonymous id>",
  "styleFeatures": {"dimension": ["observable phrase"]},
  "contentFeatures": {"dimension": ["observable content phrase"]},
  "uncertain": ["claim that needs human review"]
}
```

## Review And Merge

1. Review a representative sample against the actual assets.
2. Normalize synonymous feature values without erasing meaningful differences.
3. Merge approved extracted values into the raw adapter rows before `normalize_evidence.py`.
4. Preserve extractor version and review notes in provenance.
5. Reject or quarantine features that merely restate content, Anchor identity, or claims unsupported by the retained evidence capability.