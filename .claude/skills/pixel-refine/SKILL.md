---
name: pixel-refine
description: Change existing pixel art to a brief with tools/pixel-core/pixel_tech.py refine. It applies a recipe of deterministic ops to a text grid (recolour, ramp swaps, outline add or strip, top-left rim shading, patches, erase, fill, flood, single pixels, shift, flip, crop, resize canvas) and writes a before/after/changed-pixels preview. Use it whenever someone wants an existing sprite, tile, icon, prop or character changed, fixed, recoloured, re-shaded or re-shaped, including review notes such as "the chandelier reads as a trident". For mechanical repair only (unzoom, stray pixels, too many colours) use pixel-cleanup; for brand-new art use pixel-art. Never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# pixel-refine

This is how a brief ("make the horseshoe read at 1×", "the arms shouldn't float") becomes a change
to an existing grid. **You** interpret the brief and decide the edits; the tool applies them
exactly, keeps the file on the palette, and shows what changed.

## Workflow

1. Read the source grid and render it at 8× (`pixel_tool.py render ...` or the diff preview of an
   empty recipe). Say what's wrong in pixel terms: which rows, which colours, which silhouette.
2. Write a recipe (JSON list of ops; see `references/ops.md`). For shape changes, draw a small
   **patch** grid (`.` keeps what's under it) and place it with `patch`; use `erase` to clear.
   Recipe and patch files are ones you create for the task — they live in your workspace or
   `build/art/recipes/`, never under `art/src/`.
3. Run it to a new file first, never over the source:

   ```bash
   python3 tools/pixel-core/pixel_tech.py refine art/src/sprites/gold-chandelier.txt \
     --ops '[{"op": "pixels", "set": [[15, 10, "gold-light"]]}]' \
     --output build/art/refine/gold-chandelier.txt \
     --preview build/art/refine/gold-chandelier-diff.png
   ```

4. Open the preview: before, after, and the changed pixels in magenta, at 6×. Iterate.
5. When it's right, run it with `--output` pointing at the source, validate with
   `pixel_tool.py validate`, rebuild the asset, and look at it at 1× in context.

Full op table: `references/ops.md`. Recipe examples: `references/recipes.md`.

## Quality bar

- Judge every result at **1× on the background the asset actually stands on** before judging the
  6× diff preview. The diff shows what changed; only the real background shows whether it works.
- Open and look at every output image before showing it. A clean run is not a look.
- For anything shaped new (a patch, a redrawn region), try at least two variants and record in the
  commit why one won.
- Re-render every state and direction the asset has — a fix applied to `down` but not `up` is a
  half fix. `frames`, `within` and `where` selectors exist so one recipe covers all of them.
- Placing pixels by coordinate is a tool, not a look: every `patch` or `pixels` result gets looked
  at in context before commit.

## Rules

- Keep the palette, the category's size, and any `semantic:` header. The tool refuses off-palette
  names.
- Top-left light, outlines on world objects, no stray single pixels unless they're deliberate
  highlights.
- Keep player-facing art free of emoji, real brands, trademarked game names and self-harm imagery
  (`AGENTS.md`, `docs/production.md`); never expose developer jargon such as "seed" or
  "procedural" where a player could read it.
- Record in the commit what the brief was and what changed.
- A successful refine is not approval. The owner approves in the running game; never mark art
  approved on their behalf.

## Handoff

- Commit at each phase boundary; a phase is a reviewable unit (one asset's brief, one fix set).
- If work stops mid-phase, leave a short progress note (done / left) in the task doc or the commit
  message so the next agent does not have to reconstruct it.
- Recipes are deterministic: the same recipe on the same source gives the same grid. If a builder
  wraps refine, it must never skip regenerating an existing output — a changed input must change
  the output. Re-run the build and confirm the diff before committing.
