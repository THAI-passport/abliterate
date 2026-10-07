---
name: image-to-pixel
description: Convert a rights-cleared photo or drawing into a deterministic palette-mapped pixel grid, PNG, and side-by-side preview. Use for reference conversion, not prompt-generated art or final unreviewed assets.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# Image to Pixel

Follow `AGENTS.md`, `docs/pixel_art.md`, and `docs/fonts-and-icons.md`. This is a deterministic image conversion workflow, not AI image generation.

## Rights gate

Before converting, establish that the input is the owner's own photo or drawing, or is explicitly CC0. Do not use AI-generated images, search-result images, unclear licences, attribution-only licences, or trademarked logos. Keep repository references in `art/refs/`; for CC0 inputs, record the author, source URL, licence, and any changes in `art/CREDITS.md`.

## Boundaries

- This skill owns crop/downscale, optional ordered dithering, nearest-palette mapping, editable-grid output, and the source-versus-result preview.
- The shared CLI owns palette loading and deterministic conversion. Use only `art/palette/game.json`; never add an ad hoc color to improve one conversion.
- Conversion is a starting point. Afterward, clean the grid by hand: remove accidental isolated pixels, clarify the silhouette, add a deliberate one-pixel outline where appropriate, and validate/build it with `pixel-icon` or `pixel-art`.

## Convert and review

From the repository root, convert the shipped reference sample into a 16x16 icon source, rendered PNG, and side-by-side preview with one command (change the output paths and target size to the asset's documented size):

```bash
python3 tools/pixel-core/pixel_tool.py convert art/refs/sample-key-reference.png --palette art/palette/game.json --size 16x16 --output-grid build/art/converted/object.txt --output-png build/art/converted/object.png --preview build/art/converted/preview.png --crop cover --category icon --origin 8,15
```

Choose the documented target size for the asset; use dithering only where `docs/pixel_art.md` permits it. The example writes under `build/art/` so a conversion never pollutes sources by accident; once the grid is cleaned up by hand it moves to its home under `art/src/` with its sidecar. Converting the same input with the same options must produce the same grid.

By default the converter excludes palette colors reserved for `money`, `ruin`, and `skin`. If the subject genuinely has one of those meanings, pass `--semantic money`, `--semantic ruin`, or `--semantic skin`; the generated grid records that declaration. Do not enable a semantic merely to obtain a convenient color.

Open the side-by-side preview with the host agent's image viewer. At 1x, judge silhouette and recognizability rather than fidelity to every source detail; at 4x, inspect clusters, outline continuity, stray pixels, and palette mapping. Never ship the raw conversion without this eye review and manual cleanup. Nothing depicts or implies self-harm, and no brand, trademark or emoji survives into the cleaned grid (`AGENTS.md`, `docs/production.md`). The owner gives final approval in the running game; nothing is marked approved on their behalf.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done / left) in the task doc or the commit message.
- Conversion is deterministic: the same input and options give the same grid, always regenerated, never skipped. Re-run and confirm the diff before committing.
