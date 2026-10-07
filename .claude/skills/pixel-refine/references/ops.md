# refine ops reference

All ops accept `"frames": [1, 2]` (1-based) to limit them; default is every frame. Pixel ops also
accept `"within": [x,y,width,height]`, `"where": "colour-name"`, or both. Selectors intersect and
test the source colour. Canvas resize and crop cannot be scoped.

| Op | Fields | Does |
|---|---|---|
| `recolor` | `map` | name → name (or `null` to clear) |
| `swap` | `file`, `set` (`group:set`) | a set from a swaps file; ramp sets allowed |
| `outline` | `color`, `diagonal` | 1-px outline on transparent pixels touching the figure |
| `strip-outline` | `color` | remove the outer outline (before re-shaping) |
| `shade` | `color`, `highlight`, `shadow`, `light` | rim-light every `color` pixel: edges toward the light get `highlight`, edges away get `shadow` |
| `orphans` | | replace isolated pixels with their surroundings |
| `holes` | | fill 1-px pinholes |
| `patch` | `file`, `at` | overlay a grid; `.` keeps what's there |
| `erase` | `rect` [x,y,w,h] | clear to transparent |
| `fill-rect` | `rect`, `color` | solid fill |
| `flood` | `at`, `color` | flood fill a same-colour region (`null` clears) |
| `pixels` | `set` [[x,y,name], ...] | exact pixels |
| `shift` | `dx`, `dy` | move everything |
| `flip` | `axis` `h`/`v` | mirror |
| `crop` | `size`, `at` | cut a region |
| `resize-canvas` | `size`, `anchor` (`bottom-center`, `top-left`, ...) | grow or shrink the canvas |

Recipe files (JSON lists of ops) are files **you** create for the task; the repo does not ship a
recipe library. Keep them next to your working notes or in `build/art/recipes/` — they are not
sources and are never committed under `art/src/`.
