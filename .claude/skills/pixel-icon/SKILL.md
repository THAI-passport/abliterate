---
name: pixel-icon
description: Create, edit, validate, and atlas this game's 16x16 HUD icons and 12x12 inline-text icons. Use for symbolic game artwork and inline icon mappings, never platform emoji.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# Pixel Icon

Follow `AGENTS.md`, `docs/pixel_art.md`, and `docs/fonts-and-icons.md`. Icons replace emoji everywhere a player sees a symbol.

## Boundaries

- This skill owns the 16x16 and 12x12 icon grids, their Phaser atlas, and the named inline-icon set consumed by fonts. `pixel-font` owns glyph metrics and font export.
- Store 16x16 HUD grids under `art/src/icons/` and 12x12 inline-text grids under `art/src/icons-inline/`; treat `build/art/icons/` as generated. Use `art/palette/game.json` as the only palette.
- The shared CLI owns validation, rendering, packing, and preview generation. Do not hand-edit generated atlas coordinates or bypass validation.
- Draw icons in house. Never paste emoji, platform glyphs, real logos, branded card art, or trademarked game symbols. Never generate an icon with an AI image model. CC0 source material is allowed only when its author, URL, and licence are recorded in `art/CREDITS.md`.
- Prefer a clear silhouette and one dominant visual idea. Inline text refers to icons by stable names such as `{chip}`, never by raw private-use code points.
- Declare `semantic: money` or `semantic: ruin` when an icon intentionally uses those reserved palette ramps. Do not borrow a reserved ramp for an unrelated object.

## Build and review

From the repository root, validate all icon grids and build the atlas, metadata, and 1x/4x preview with one command:

```bash
python3 tools/pixel-core/pixel_tool.py build-icons art/src/icons --palette art/palette/game.json --out-dir build/art/icons --columns 8
```

Fix every error and inspect every warning. Open `build/art/icons/icons-preview.png` with the host agent's image viewer. Check every icon at 1x for immediate recognition and at 4x for stray pixels, outline gaps, inconsistent stroke weight, and accidental asymmetry. Also verify contrast on the intended light and dark UI backgrounds. A clean build is not visual approval.

The font build separately consumes `art/src/icons-inline/`, validates every grid at exactly 12x12, and writes the stable name-to-private-use mapping alongside the BMFont.

## Quality bar

- Judge every icon at **1× on the light and dark UI backgrounds it will actually sit on** before judging it at 4×.
- Open and look at every output image before showing it.
- Draw at least two variants for any new icon and record in the commit why one won; icons must not be confused with their neighbours at 12 px (`docs/assets_design.md` section 14).
- Never generate geometry by rule where a drawn icon is expected; a placed detail gets looked at in context before commit.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done / left) in the task doc or the commit message.
- The icon build is deterministic and always regenerates: a changed grid must change the atlas and preview. Re-run the build and confirm the diff before committing.

Inspect the atlas in the running game before commit when practical. The owner provides final approval in context; nothing is marked approved on their behalf.
