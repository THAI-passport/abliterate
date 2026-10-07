---
name: pixel-art
description: Create new pixel sprites, tiles, UI frames, machines, and documents for this game as text grids or indexed PNGs, then validate, render, and preview them. For characters use pixel-rig; for changing existing art use pixel-refine (a brief) or pixel-cleanup (mechanical repair); pixel-font, pixel-icon, and image-to-pixel own their narrower asset types. Never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# Pixel Art

Create repository-native art that follows `AGENTS.md` and `docs/pixel_art.md`. Read the relevant category and size rules there before editing; this skill links to those decisions instead of restating them. The website is reference material, not a visual style guide.

## Boundaries

- This skill owns sprites, tiles, UI frames, documents, the text-grid source format, and atlas-ready outputs. Characters (parts, layers, poses, portraits) belong to `pixel-rig`.
- `tools/pixel-core/pixel_tool.py` owns palette loading, validation, rendering, and preview generation. Do not duplicate or bypass those checks.
- Edit sources under `art/src/`; treat `build/art/` as generated output. Use only `art/palette/game.json`.
- Never generate art with an AI image model. Draw grids in code, use the owner's hand-drawn work, or recolor CC0 material. Record every third-party source, author, URL, and licence in `art/CREDITS.md`.
- Keep player-facing art free of emoji, real brands and logos, and trademarked game names. Nothing may depict or imply self-harm (`docs/production.md`). Binary transparency and palette colors only. Never put developer jargon such as "seed", "procedural", or "generated" where a player could read it; signs, documents and screens use the names in `docs/dialogue.md`.
- A successful command is never approval. The owner approves art in the running game; never mark an asset approved on the owner's behalf.

## Build and review

From the repository root, validate, render, and make the required 1x/4x preview for one **text grid** with:

```bash
python3 tools/pixel-core/pixel_tool.py asset-build art/src/sprites/marble-column.txt --palette art/palette/game.json --out-dir build/art/sprites
```

`asset-build` takes text grids only. Indexed PNG sources (with a same-stem JSON sidecar declaring `palette`, `category`, and, for world sprites, `origin`) are built through the folder command, which packs mixed text-grid and PNG sources into one Phaser atlas:

```bash
python3 tools/pixel-core/pixel_tool.py build-assets art/src/sprites --palette art/palette/game.json --out-dir build/art/sprite-atlas
```

Text grids declare `category:` and `origin:` in their headers. Exact-size categories cannot use an exception: HUD icons are 16x16, inline icons 12x12, and Verdict Text glyphs 6x10 (`docs/pixel_art.md` section 14).

Colors tagged `semantic: money`, `semantic: ruin`, or `semantic: skin` in the palette are reserved. A source that uses one must declare the same semantic in its header or sidecar; ordinary props must use a non-reserved ramp.

Change the source and output category paths as needed. Fix every error; investigate every warning rather than suppressing it.

## Quality bar

- Judge every result at **1x on the background it will actually stand on** (each front's carpet, the house floors, the paper) before judging it at 4x. "It works at 4x on flat grey" is not a pass.
- Open and look at every output image before showing it: silhouette, top-left lighting, outlines, intentional single pixels, hard transparent edges, consistent pixel size, readability in context.
- Draw at least two variants for anything new and record in the commit why one won.
- Draw all directions or states the asset needs, never front-only. A missing state is a bug, not a shortcut.
- Placing pixels by coordinate (patches, pixel ops) is a tool, not a look: re-render the result in context and look at it before committing. Rule-generated detail that nobody has looked at does not ship.

Before commit, inspect the asset in the running game when practical (`playtest` screenshots).

## Handoff

- Commit at each phase boundary; a phase is a reviewable unit (one asset group, one fix set).
- If work stops mid-phase, leave a short progress note (done / left) in the task doc or the commit message so the next agent does not have to reconstruct it.
- Builders are deterministic and never skip regenerating an existing output: a changed input must change the output. Re-run the build and confirm the diff is exactly what you intended before committing.
