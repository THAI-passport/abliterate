# pixel-rig formats

## rig.json

```json
{
  "name": "body-a",
  "palette": "art/palette/game.json",
  "canvas": [16, 32],
  "origin": [8, 30],
  "directions": ["down", "up", "left", "right"],
  "mirror": {"right": "left"},
  "fallback": {"up": "down"},
  "part_dir": "parts",
  "layer_dir": "layers",
  "prop_dir": "../props",
  "poses": "../poses.json",
  "swaps": "../swaps.json",
  "postures": {"upright": {"variants": {"head": "upright", "torso": "upright"}}},
  "parts": {"head": {"down": [3, 2], "left": [3, 2]}},
  "draw_order": {"down": ["leg_l", "leg_r", "torso", "arm_l", "arm_r", "head"]},
  "groups": {"upper": ["head", "torso", "arm_l", "arm_r"]},
  "outline": {"mode": "outer", "color": "ink-1", "diagonal": false},
  "shadow": {"color": "ink-3", "rows": [8, 6]}
}
```

- `origin`: the feet point; the contact shadow's first row is drawn on it, one width per `rows` entry.
- `parts[part][direction]`: where the part's pivot lands on the canvas.
- `mirror`: a direction built by flipping another. `fallback`: a direction that reuses another's
  part drawings, placements and draw order when its own are missing (parts only).
- `groups` (plus the built-in `all`) can be targeted by poses.
- `outline.mode`: `outer` adds a 1-px outline around the figure; `none` leaves parts as drawn.

## Part grids

The normal text-grid format (`docs/pixel_art.md` section 14), one frame, named
`<part>.<direction>[.<variant>].txt`, with an optional `pivot: x,y` header (default `0,0`). The
pivot is the point placed at the rig position, so a `reach` arm can extend left of its shoulder.
Add `semantic: skin` when skin colours are used. Arms may name `anchor-hand: x,y`; a held prop
names `anchor-grip: x,y`.

Limb naming: `arm_l`/`leg_l` are the limbs on the viewer's left in the front view and the **near**
limbs in profile; `arm_r`/`leg_r` are the others. Keep names identical across directions.

## poses.json

```json
{"poses": {
  "walk": {"hold": 8, "frames": [{"leg_l": {"dy": -1}}, {"upper": {"dy": 1}}],
           "directions": {"left": {"frames": [{"leg_l": {"dx": -1}}]}}},
  "hand-over": {"hold": [12, 6, 30], "loop": false,
                "keys": [{}, {"arm_r": {"variant": "reach", "dy": -1}}], "inbetween": 1}
}}
```

- A frame maps a part or group to `{"dx", "dy", "variant", "hide"}`. Group and part offsets add up.
- `hold` is in 60 fps ticks: one number for every frame, or a list.
- `keys` + `inbetween`: offsets are interpolated (rounded half away from zero); variants switch at
  the midpoint.
- `loop: false` makes a one-shot animation.

## swaps.json

```json
{"skin": {"deep": {"from_ramp": "skin-light", "to_ramp": "skin-deep"}},
 "cloth": {"charcoal": {"violet-base": "metal-2", "violet-dark": "metal-1"}}}
```

A set is a name-to-name map or a ramp-to-ramp map by position. Swaps apply after composition, in
one pass (no chaining), before the outline and shadow.

## Layers

`layers/<name>/layer.json` (optional) plus drawn grids named like parts.

```json
{"z": "part", "mode": "over", "fallback": false,
 "paint": [{"part": "torso", "rows": [1, 7], "map": {"skin-light-light": "paper"}},
           {"part": "arm_r", "variant": "reach", "directions": ["down"], "rows": [0, 2], "map": {}},
           {"part": "arm_l", "rows": [0, 2], "base_only": true, "map": {}}]}
```

- Paint rules recolour the part's own pixels in part coordinates (`rows`, `cols`, inclusive).
  `variant` limits a rule to one variant; `base_only` limits it to the undrawn base; `directions`
  limits directions (the drawn direction, so `left` also covers the mirrored `right`).
- Drawn grids ride on the part: same pivot, same offsets. `z: top` draws after all parts,
  `z: bottom` before; `mode: replace` hides the part under the layer.

## Appearances

```json
{"name": "suit", "layers": ["face-basic", "hair-short", "suit-jacket", "shirt", "trousers"],
 "swaps": ["skin:light", "cloth:charcoal"], "posture": "upright", "shadow": true,
 "poseOverrides": {"walk": {"hold": [8, 8, 9, 8]}},
 "heldProps": [{"name": "card", "part": "arm_r", "poses": ["hand-over"]}],
 "timeVariants": {"later": {"layers": {"add": ["grey-temples"], "remove": []}}},
 "frameLayers": {"walk/down/2": {"add": ["coat-tail-lag"], "remove": []}}}
```

Layers paint and draw in list order; later drawn layers sit on top of earlier ones on the same part.
`frameLayers` keys are `pose/frame` or `pose/direction/frame` (1-based). The more specific key is
applied second. Each override may `add` and/or `remove` layer names.

- A rig posture profile supplies default part variants and may contain `poseOverrides`.
- Appearance `poseOverrides` merge after the posture. `heldProps` may filter by `poses`,
  `directions` and 1-based `frames`.
- A named `timeVariants` patch can replace or add/remove layers and swaps, and change any other
  appearance field. Select it with `--variant`.
- `familyInherit` names `layerPrefixes` and `swapGroups` to copy from `--family-appearance`.
- `shadow: false` suppresses the rig's contact shadow.
- A layer with `"asymmetric": true` must provide the explicit target direction when the rig would
  otherwise mirror it.

## Portrait kit

A native 64×64 portrait kit (decision 37; per `art/src/rig/face-kit/`; drawn by hand with
real shading in the `pixel-face` skill's Stage 5) holds `base.txt` and layer files, each exactly
64×64 (`PORTRAIT_SIZE` in `pixel_tech.py`; other sizes are refused). The committed 48×48
portraits are legacy starters to redraw. `rig-portrait-kit --layer ...`
composes them in order, with optional
palette swaps. The command never scales the 16×32 overworld sprite.
