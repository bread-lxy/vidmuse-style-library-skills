# Image URL Backfill

This is the formal sixth stage after `preview-export` approval. Upload only the
approved final preview listed for each style, keep `05-preview-export/`
unchanged, and write all raw and normalized URL artifacts to
`06-url-backfill/`. Do not begin while the preview package is unapproved.

## Stage Inputs And Outputs

Inputs from stage 05:

- `styles.json` with an empty `imageUrl` in every record;
- `preview-manifest.csv` with the stable style order and final filenames;
- exactly one approved file per manifest row in `previews/`.

Required stage 06 artifacts:

- `planner-image-url-map.json`: the Planner's ordered response, preserved as raw provenance;
- `styles.json`: the final URL-complete six-field records;
- `styles.csv`: the lossless CSV equivalent;
- `image-url-map.json`: the normalized exact mapping;
- `url-validation.json`: external HTTP and image-signature validation results.

## Runtime

Use the VidMuse dev CLI config explicitly:

```powershell
$env:VIDMUSE_CONFIG = Join-Path $HOME ".vidmuse-dev\config.json"
```

Verify the selected config points to the dev endpoint before creating a thread.
Create the thread with:

```powershell
vidmuse thread create --plugin-id Evals-bread-img --text "<setup prompt>" -o json
```

Confirm the returned thread options contain:

```json
{"plugin_id": "Evals-bread-img"}
```

## Upload

Upload exactly the one final image listed for each style in
`preview-manifest.csv`.

- Send files in manifest order.
- Include `styleIndex` and `fileName` in each upload message.
- Wait until `vidmuse thread status <threadId>` returns `waiting` before sending
  the next message. A busy queue returns HTTP 409.
- Prefer one file per message. Large multi-file creates can exceed the CLI
  request deadline.
- After every upload, inspect message history and confirm the attachment has a
  real `files[].file_path`.

## Planner Instruction

After all files arrive, tell the Planner to:

1. Resolve every source from the corresponding upload message.
2. Copy the original bytes to the exact runtime path
   `{thread_root}/workspace/assets/images/{fileName}`.
3. Verify the copied file exists and is non-empty.
4. Return an ordered JSON array with exactly `styleIndex`, `name`, `fileName`,
   and `imageUrl`.
5. Build URLs as:

```text
https://vidmuse-dev.sandcdn.com/v2/static/{thread_id}/workspace/assets/images/{fileName}
```

The physical `workspace/` directory is required. Copying to
`{thread_root}/assets/images/` produces plausible-looking URLs that return 404.
Never expose `/work/`, `/tmp/`, `aion-runtime-*`, or other runtime paths.

Save the returned array without reordering or manual rewriting as:

```text
<run-dir>/06-url-backfill/planner-image-url-map.json
```

## Verify And Backfill

Do not trust local existence or Planner text as URL proof. Require an external
HTTP response of `200` or `206`, an `image/*` content type, and a recognized
image signature.

Run:

```powershell
python scripts/backfill_image_urls.py `
  --styles <run-dir/05-preview-export/styles.json> `
  --preview-manifest <run-dir/05-preview-export/preview-manifest.csv> `
  --url-map <run-dir/06-url-backfill/planner-image-url-map.json> `
  --output-dir <run-dir/06-url-backfill>
```

The script joins rows by ordered `styleIndex`, exact `name`, and exact
`fileName`; rejects duplicates, local paths, filename mismatches, unreachable
URLs, non-image responses, and invalid signatures; and writes the four derived
stage artifacts.

Run final production validation:

```powershell
python scripts/validate_style_record.py `
  <run-dir/06-url-backfill/styles.json> `
  --strict `
  --check-image
```

Never use `--skip-url-check` for a final delivery. Approve `url-backfill` only
after the raw and normalized maps align exactly, every validation row has
`valid: true`, production validation passes, and JSON/CSV round-trip is
lossless. This stage does not upload records to the admin and does not create
styles.
