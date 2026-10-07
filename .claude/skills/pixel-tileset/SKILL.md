---
name: pixel-tileset
description: Build connected tilesets and check tiles with tools/pixel-core/pixel_tech.py. autotile turns a small 4x3-tile source (a framed 3x3 patch plus four inner corners) into the full 47-tile blob set with a 256-mask lookup JSON and a sample map; seams warns about solid border lines that draw a grid and shows a 4x4 tiled preview. Use it for any tile that joins or repeats — carpets with borders, rugs, walls, paths, counters, the cage — and for seam-checking any floor or wall tile. A standalone tile or sprite is pixel-art's job. Never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# pixel-tileset

## Autotile (the 47-tile blob set)

Draw one source grid, `category: tile-source`, 64×48 for 16-px tiles:

- tile columns 0–2 × rows 0–2: a 3×3 framed patch (outer corners, edges, the centre fill);
- tile column 3, row 0: the four **inner corners**, one per quadrant (top-left quadrant = the
  concave corner that opens to the top left).

```bash
python3 tools/pixel-core/pixel_tech.py autotile art/src/tilesets/rug-autotile.txt \
  --filler art/src/tiles/front-1-rock-bottom-carpet.txt --out-dir build/art/tilesets/rug
```

Outputs: `tileset.png` (47 tiles, 8 per row), engine `tileset.json`, Tiled-compatible
`tileset.tsj` with Wang IDs and `neighborMask` tile properties, `sample-map.png` and
`tileset-preview.png`. Mask bits are N=1, E=2, S=4, W=8, NE=16, SE=32, SW=64, NW=128. Each tile is
built from four half-tile quadrants, so the source must keep its pattern continuous on a grid of
half-tiles (pattern periods that divide 8 are safe).

In the game, compute each cell's mask from its eight neighbours and look up the tile.

## Seams

```bash
python3 tools/pixel-core/pixel_tech.py seams art/src/tiles/casino-service-floor.txt --preview build/art/seams.png
```

Warns when an edge is one solid colour (it draws a grid line across the floor) and reports how
the opposite edges differ. Always look at the 4×4 preview: seams are a visual judgement.

## Rules

Tiles are 16×16 on the world grid (`pixel_art.md` section 4). Carpets stay mid-tone so characters
read on top; check with `pixel-rig`'s test sheet.

- Never generate tile art with an AI image model; sources are drawn grids (`docs/pixel_art.md`).
- No emoji, real brands or trademarked game names in any tile art.
- Nothing depicts or implies self-harm (`docs/production.md`).
- A passing `seams` run is not approval: judge the tiled result at 1× on the floor it will sit on,
  look at every preview, and draw at least two pattern variants for anything new. The owner
  approves in the running game; never mark a tile approved on their behalf.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done /
  left) in the task doc or the commit message.
- `autotile` and `seams` are deterministic and always regenerate: a changed source must change the
  output. Re-run them and confirm the diff before committing.
