---
name: pixel-font
description: Create, edit, validate, and build this game's in-house pixel-font glyph grids, BMFont data, TTF export, and specimen sheets. Use for font glyphs and metrics, not ordinary sprites or icons.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# Pixel Font

Follow `AGENTS.md`, `docs/pixel_art.md`, and `docs/fonts-and-icons.md`. Fonts are drawn in house from repository glyph grids; do not trace, convert, or bundle a third-party font.

## Boundaries

- This skill owns glyph grids, glyph metrics, baselines, BMFont and TTF builds, and specimen sheets. `pixel-icon` owns the icon drawings and their inline-name mapping.
- The shared CLI owns palette checks, grid parsing, rendering, and exports. Keep source glyphs under `art/src/fonts/` and generated files under `build/art/fonts/`.
- Use `art/palette/game.json` as the sole color source. Glyph edges must be binary-transparent and all opaque pixels must be in the palette.
- Preserve the chosen font's declared cell height and baseline. For Verdict Text, glyphs are 6x10; digits must remain tabular so money columns align. Keep player-visible characters free of emoji.
- Glyphs are original project artwork. Do not derive outlines from commercial, free, or open-source fonts; that keeps the in-house fonts free of third-party font licences. Never generate glyphs with an AI image model, and never trace a font file.
- Keep player-visible text free of emoji, real brands, trademarked names and developer jargon such as "seed" or "procedural".

## Build and review

From the repository root, validate the full font and build its BMFont, TTF, and 1x/2x/4x specimen sheet with one command:

```bash
python3 tools/pixel-core/pixel_tool.py build-font art/src/fonts/verdict-text --inline-icons art/src/icons-inline --palette art/palette/game.json --out-dir build/art/fonts --name "Verdict Text"
```

The build emits a Phaser-readable XML BMFont (`.fnt` plus PNG), a loadable TTF, a specimen sheet, and `inline-icons.json`. Inline icon names are assigned stable private-use code points in sorted filename order; game text uses names such as `{cash}`, never the raw code points.

Fix every error and review every warning. Open the generated `*-specimen.png` with the host agent's image viewer. At native size, verify baseline and cap-height consistency, legibility, punctuation spacing, distinct confusable characters, and equal-width digits; at enlarged sizes, check for accidental holes, stray pixels, and broken strokes. Build success alone is not approval.

Inspect important text in the running game before commit when practical. Only the owner can give final in-context approval; a clean build is never marked approved on their behalf.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done / left) in the task doc or the commit message.
- The font build is deterministic and always regenerates: a changed glyph grid must change the BMFont, TTF and specimen. Re-run the build and confirm the diff before committing.
