---
name: pixel-cleanup
description: Mechanically repair pixel art with tools/pixel-core/pixel_tech.py. Unzoom restores the native pixel grid of an enlarged image (it detects the scale and offset) and maps it to the palette; remove-bg clears a flat background from the edges; reduce limits a grid to its N most-used colours; lint reports isolated pixels, pinholes and doubled outlines; fix repairs isolated pixels and pinholes. Use it when art arrives upscaled, on a solid background, or with too many colours, or for a generic "tidy this". When the change serves a design brief (recolour to a spec, re-shape a silhouette), use pixel-refine instead; new art belongs to pixel-art. Never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# pixel-cleanup

| Command | Use it for |
|---|---|
| `unzoom IMAGE --output-grid G.txt [--remove-background] [--category C] [--preview P.png]` | An enlarged screenshot or export of pixel art. Detects the integer scale and grid offset, samples each cell, maps to the palette, writes a text grid. `--scale N` overrides detection. |
| `remove-bg IMAGE --output OUT.png [--tolerance N]` | A flat background colour touching the image border becomes transparent. |
| `reduce G.txt --max N [--keep name] --output OUT.txt` | Keep the N most-used colours (plus any `--keep`), remapping the rest to the nearest kept colour. |
| `lint G.txt [--outline ink-1]` | Isolated pixels, pinholes, 2×2 blocks of outline colour. Warnings, never errors. |
| `fix G.txt [--output OUT.txt] [--preview P.png]` | Fix isolated pixels and pinholes, with a before/after preview. |

All of them take `--palette` (default `art/palette/game.json`).

## Rules

- Only rights-cleared sources: the owner's own drawings or screenshots, CC0 material, or this
  repo's own renders. Record third-party sources in `art/CREDITS.md`. Never clean up output from
  an AI image model and pass it off as ours: the game uses no image models (`production.md`).
- Lint findings need a human look: a single highlight pixel on a coin is deliberate; one on a flat
  wall is noise.
- After cleanup, validate with `pixel_tool.py validate` and review the result at **1× on the
  background it stands on** before 4×. Cleanup that "works" only enlarged isn't done.
- Keep player-facing art free of emoji, real brands, trademarked game names and self-harm imagery
  (`AGENTS.md`, `docs/production.md`).
- A clean lint is not approval. The owner approves in the running game; never mark art approved on
  their behalf.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done /
  left) in the task doc or the commit message so the next agent can pick it up.
- Cleanup is deterministic: the same command on the same input gives the same output. A builder
  that wraps cleanup must never skip regenerating an existing output — a changed input must change
  the output. Re-run and confirm the diff before committing.
