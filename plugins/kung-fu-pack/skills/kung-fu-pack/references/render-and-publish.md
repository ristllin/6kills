# Render diagrams and publish the pack

Concrete commands for step 5 (render) and step 6 (publish). Run from the pack's `assets/` dir unless
noted. No em dashes in any generated text, including diagram labels and the page title.

## Render diagram HTML to PNG (headless Chrome)

`gen.js` writes one `.html` per diagram at a fixed canvas size. Screenshot each at 2x for crisp text.
Find a Chrome/Chromium binary (macOS path shown; `setup.sh` reports what exists):

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # or chromium / google-chrome
render() {  # name  width  height
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size=$2,$3 \
    --screenshot="$1.png" "file://$PWD/$1.html" >/dev/null 2>&1
}
render 01-layered-stack 1600 1120
```

Set `--window-size` to exactly the diagram's canvas WxH (the template's `fit()` scales the viz to the
viewport width, so scale stays 1 and the capture is clean). Then **Read each PNG** to eyeball it
before using it; regenerate if text clips or overlaps.

## Publish to Notion (upload PNGs, embed, create/update)

1. For each PNG, ask for an upload URL with the `notion-create-file-upload` MCP tool
   (`filename: "<name>.png"`). It returns `upload_url` and `upload_headers`.
2. POST the bytes (short-lived URL, ~10 min window):
   ```bash
   curl -s -X POST "$UPLOAD_URL" -H "authorization: $BEARER" \
     -F "file=@01-layered-stack.png;type=image/png"
   ```
   The response has `status: uploaded` and `markdown_source: file-upload://<id>`.
3. Embed in the page body as `![alt](file-upload://<id>)` and pass the body to
   `notion-create-pages` (new) or `notion-update-page` with `command: replace_content` (existing).
   Default to a **draft** when no destination is named; **confirm before overwriting** an existing
   page. Fix the page **title** separately with `update_properties` if it would carry a dash.
4. Fetch the page back and confirm the images resolve (they become signed S3 URLs on fetch).

Fallback if direct upload is unavailable: `notion-create-attachment` accepts inline SVG/HTML
`content` (<=200KB) or a public `source_url`, or a `source_file_id` from step 1.

## Publish as self-contained HTML

Inline each PNG as base64 so the file is portable (no external assets):

```bash
python3 - <<'PY'
import base64, pathlib
pngs = {p.stem: base64.b64encode(p.read_bytes()).decode() for p in pathlib.Path('.').glob('*.png')}
# build out/page.html: <img src="data:image/png;base64,{pngs['01-layered-stack']}">
PY
```

Wrap the body in a minimal dark-mode HTML shell matching the diagram palette. Write to `../out/page.html`.

## Publish as local Markdown

Write `../out/page.md` with the body, referencing diagrams relatively
(`![alt](../assets/01-layered-stack.png)`). Zero dependencies; good for git.

## Local preview server

Serve the pack for live viewing:

```bash
cd ../out && python3 -m http.server 8787   # then open http://localhost:8787/page.html
```
