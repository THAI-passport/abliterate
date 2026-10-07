# Pixel core

`pixel_tool.py` is the one shared implementation used by the `pixel-art`,
`pixel-font`, `pixel-icon`, and `image-to-pixel` skills. It is deterministic and
uses one editable palette source: the JSON passed with `--palette`. Pillow is
its only runtime dependency; the BMFont and TrueType exporters are implemented
locally without font tooling packages.

Python 3.10+ and Pillow are required. On a new machine:

```bash
python3 -m pip install -r tools/pixel-core/requirements.txt
```

Canonical commands:

```bash
python3 tools/pixel-core/pixel_tool.py palette-export --palette art/palette/game.json --out-dir art/palette
python3 tools/pixel-core/pixel_tool.py validate art/src/rig/props/janitor-cart.txt --palette art/palette/game.json
python3 tools/pixel-core/pixel_tool.py render art/src/rig/props/janitor-cart.txt --palette art/palette/game.json --output build/art/janitor-cart.png
python3 tools/pixel-core/pixel_tool.py preview art/src/rig/props/janitor-cart.txt --palette art/palette/game.json --output build/art/previews/janitor-cart.png
python3 tools/pixel-core/pixel_tool.py build-assets art/src/sprites --palette art/palette/game.json --out-dir build/art/sprite-atlas
python3 tools/pixel-core/pixel_tool.py build-icons art/src/icons --palette art/palette/game.json --out-dir build/art/icons
python3 tools/pixel-core/pixel_tool.py build-font art/src/fonts/verdict-text --inline-icons art/src/icons-inline --palette art/palette/game.json --out-dir build/art/fonts --name "Verdict Text"
python3 tools/pixel-core/pixel_tool.py convert art/refs/sample-key-reference.png --palette art/palette/game.json --size 16x16 --output-grid art/src/converted/sample-key.txt --output-png build/art/converted/sample-key.png --preview build/art/previews/sample-key.png --category icon
python3 tools/pixel-core/pixel_tech.py rig-check art/src/rig/body-a/rig.json
python3 tools/pixel-core/pixel_tech.py rig-build art/src/rig/body-a/rig.json --appearance art/src/rig/appearances/mr-pitt.json --only-pose idle --direction down --out-dir art/build/rig/mr-pitt
python3 tools/pixel-core/pixel_tech.py rig-onion-skin art/src/rig/body-a/rig.json --appearance art/src/rig/appearances/mr-pitt.json --pose walk --direction down --output art/previews/rig/mr-pitt-walk-onion.png
```

`art/palette/game.json` is the sole hand-edited palette file. It contains the
locked Wyrm-Moth48 mapping and the primary deep-teal felt decision. Rerun
`palette-export` after any approved named-ramp addition to derive `game.hex`,
`game.gpl`, and `swatch.png`; never edit those derived files independently.

`validate` reports blocking errors for off-palette colours, partial alpha,
malformed frames, undefined symbols, missing or unknown categories, missing world
origins, and category size limits. Icons are exactly 16x16, inline icons exactly
12x12, and Verdict Text glyphs exactly 6x10; exceptions cannot override those
contracts. It reports review warnings for palette size/extremes, isolated pixels,
outline gaps, low contrast, and unsafe mirroring. A recorded `exception:` header
permits an intentionally oversized grid; it does not silence other checks.
Multi-frame `asset-build` calls also emit a nearest-neighbour `*-animated.gif`;
set `frame-hold:` to a positive count of 60 fps frames when the default of 8 is
not appropriate.

`build-assets` accepts text grids and indexed PNGs in one source folder and
emits a Phaser JSON atlas. Each PNG needs a same-stem JSON sidecar:

```json
{"palette":"game","category":"world","origin":[8,15]}
```

Palette entries may declare a `semantic` of `money`, `ruin`, or `skin`. Sources
using those reserved colors must declare the corresponding `semantic:` header
or sidecar field. Conversion excludes every reserved semantic by default; pass
`--semantic money`, `--semantic ruin`, or `--semantic skin` only when the
subject actually carries that meaning.

Glyph grids add `codepoint: U+0041`, `baseline: 8`, and optionally `advance: 6`.
The font build rejects mismatched heights/baselines and non-tabular digit
advances. It emits a Phaser-readable XML BMFont, a TTF, and a stable
`inline-icons.json` mapping for sorted 12x12 inline-icon filenames. Icon and
asset builds emit Phaser-compatible JSON atlases. Preview sheets use
nearest-neighbour scaling.

Run the tests from the repository root:

```bash
python3 -m unittest discover -s tools/pixel-core/tests -v
```
