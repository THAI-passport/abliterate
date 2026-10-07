---
name: pixel-nineslice
description: Build stretchable UI frames (dialogue boxes, panels, buttons, the phone, letters, the wager tray) with tools/pixel-core/pixel_tech.py nineslice. From one small frame grid and its slice insets it writes the PNG, a Phaser nine-slice JSON config, and previews at several sizes built by tiling the edges and centre (never stretching pixels). Use it for any frame that must stretch or repeat at different sizes, including animated frames such as a blinking cursor. A fixed-size UI element or icon is pixel-art's job. Never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# pixel-nineslice

Draw the frame once, small (for example 24×24), `category: ui`, with a `slice: left,top,right,bottom`
header giving the fixed corner sizes.

```bash
python3 tools/pixel-core/pixel_tech.py nineslice art/src/ui/dialogue-panel.txt \
  --out-dir build/art/ui --size 48x32 --size 160x48 --size 240x64
```

Outputs `<name>.png`, `<name>.json` (`leftWidth`, `topHeight`, `rightWidth`, `bottomHeight`,
`mode: tile`) and `<name>-preview.png`.

For a multi-frame source, it also writes `<name>-frames.png`, `<name>-anims.json` and a blinking
`<name>-preview.gif`. Set the speed with `--frame-ms`. The shipped example is
`art/src/ui/dialogue-cursor.txt`.

## Rules

- Corners are fixed; edges and centre **repeat**. Draw edges and the centre as patterns that tile
  (a flat colour, or a pattern whose period divides the middle span). Never let Phaser stretch
  pixel art: use the tiled mode, or render with this tool's `nineslice` function.
- Layout stability (house rule 8): a panel's size never changes when a result appears.
- No emoji or browser-native dialogs; the interface voice is in `docs/dialogue.md` section 18.
- Never generate frame art with an AI image model. Nothing depicts or implies self-harm
  (`docs/production.md`); no real brands or trademarked names in any frame art.
- Judge the built previews at 1× at the size the panel is actually used at, look at every output,
  and try at least two corner/edge treatments for anything new. A clean build is not approval: the
  owner approves in the running game, and nothing is marked approved on their behalf.

## Handoff

- Commit at each phase boundary; if work stops mid-phase, leave a short progress note (done /
  left) in the task doc or the commit message.
- The build is deterministic and always regenerates: a changed frame grid or inset must change the
  outputs. Re-run the build and confirm the diff before committing.
