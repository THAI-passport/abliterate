# Recipe examples

## Re-shade a flat shape and outline it

```json
[
  {"op": "strip-outline", "color": "ink-1"},
  {"op": "shade", "color": "gold-base", "highlight": "gold-light", "shadow": "gold-dark"},
  {"op": "outline", "color": "ink-1"},
  {"op": "orphans"}
]
```

## Recolour a prop for another front

```json
[{"op": "recolor", "map": {"violet-base": "felt-teal", "violet-dark": "screen-dark"}}]
```

## Fix a silhouette with a patch

Draw the patch grid (same size as the area to fix; `.` keeps pixels) — recipe and patch files are
ones you create for the task, e.g. under `build/art/recipes/` — then:

```json
[
  {"op": "patch", "file": "horseshoe-nails.txt", "at": [2, 3]},
  {"op": "pixels", "set": [[4, 6, "ink-1"], [11, 6, "ink-1"]]},
  {"op": "outline", "color": "ink-1"}
]
```

## Make room for a taller sprite, feet fixed

```json
[{"op": "resize-canvas", "size": [16, 32], "anchor": "bottom-center"}]
```

Inline recipes work too: `--ops '[{"op": "orphans"}]'`.
