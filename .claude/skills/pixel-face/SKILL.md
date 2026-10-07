---
name: pixel-face
description: Build this game's character heads and faces with the hand-drawn face kit in art/src/rig/face-kit and its face-compose/face-sheet tools. Use whenever a head outline, face part (eyes, brows, nose, mouth, glasses, stubble, beard, moustache, age lines) or composed face is drawn, placed, recoloured, reviewed or extended, for overworld sprites and 64x64 dialogue portraits (drawn with real shading). Never generate geometry with a tool, never generate portrait pixels with a script, and never use an AI image model.
---
> **In this repo (stream recorder bot):** copied from `~/Desktop/thegame`. "This game" means the
> dashboard in `web/`. The tool is `tools/pixel-core/` (needs Pillow: `pip install -r tools/pixel-core/requirements.txt`).
> There is no `art/palette/game.json` here: always pass `--palette` explicitly, using the dashboard palette
> once one exists under `art/palette/`. Game docs it mentions (`docs/pixel_art.md` etc.) don't exist here;
> `AGENTS.md` is the rule file. Website icons are Lucide (see AGENTS.md), so pixel-icon is for pixel artwork only.


# pixel-face

Faces are **hand-drawn text grids** in `art/src/rig/face-kit/`, snapped into named
slots by `tools/pixel-core/face_kit.py`. The tool places and recolours; it never
draws: no formula produces a pixel that is not in a checked-in grid. Every head
outline and every part is typed by hand. Read `docs/character_design.md` (sections
1, 3, 4, 6 and 12) before drawing anything; it owns the look.

## Files

| Path | Holds |
|---|---|
| `art/src/rig/face-kit/kit.json` | Slots per build and direction, part groups, face combos, reservations |
| `art/src/rig/face-kit/heads/a-round-down.txt` and its 31 siblings | Four hand-drawn shapes per build and direction (`round`, `long`, `square-jaw`, `narrow-chin`; body-a 14x13 front, 15x13 profile; body-b 13x13 front, 14x13 profile), skin ramp only, no outline (the rig adds it) |
| `art/src/rig/face-kit/parts/eyes-dot.body-a.down.txt` and its siblings | Face part patches; a per-build override drops the build into the file name (`eyes-dot.body-b.down.txt`) because eye spacing differs per build |
| `art/src/rig/body-a/parts/head.down.txt` and siblings | Installed copies of the kit heads (written by `face_kit.install_heads`) |
| `art/src/rig/body-a/layers/face-plain/head.down.txt` and siblings | Composed face layers the rig wears |

Conventions: heads and skin parts are drawn in the `skin-light` ramp (shadow
`skin-deep-light`, base `skin-warm-light`, light `skin-light-light`) and swapped
per skin ramp. Sprite heads use all three tones: top-left light, base face plane,
and shadow under the hairline and chin and down the far cheek. Brows, beards and
moustaches are drawn in `ink-2` (hair base) and swapped per hair ramp; eyes are
`ink-1` and are never recoloured; glasses are `ink-4`; neutral mouths use a skin
shadow tone. Profile views draw the nose as a 2 px bump in the head grid itself,
so side views have no nose part. `up` shows shape and ear shading but no face slots.

## Commands

```bash
pt() { python3 tools/pixel-core/pixel_tech.py "$@"; }
pt face-compose --kit art/src/rig/face-kit --build body-a --direction down \
  --head narrow-chin --eyes narrow --brows flat --nose long --mouth off-centre \
  --marks far-lid --skin skin:medium --hair hair:black \
  --output-grid build/art/rig/face-pitt.txt --preview build/art/rig/face-pitt.png
pt face-compose --kit art/src/rig/face-kit --build body-a --face glasses \
  --appearance corporate-janitor --write-layer face-glasses
pt face-sheet --kit art/src/rig/face-kit --output art/previews/face-kit/face-kit-sheet.png
```

`face-compose` snaps parts onto a selected head (`--face` names a combo in `kit.json`, or
pass `--head/--eyes/--brows/--nose/--mouth/--marks/--glasses/--stubble/--beard/--moustache/--age-lines`
directly), recolours per `--skin`/`--hair`, checks reservations and part fit, and
writes `--output-grid`, `--preview` (1x and 4x) and/or `--write-layer` (all four
directions as a rig layer). A complete face layer uses `mode: replace` at the rig's
`part` z-level so its selected silhouette replaces the installed round base head;
overlay-only features such as Joe's moustache keep `mode: over`. `face-sheet` writes the labelled review sheet (every
face x skin x build at 1x and 4x), a `-carpet` companion when `--carpet` names
carpet tiles, and a `--directions` sheet (default on, one face in all four views).
Builds are deterministic: same input, byte-identical output; never skip an existing
output, always overwrite.

## Reservations

Some faces belong to one character (`character_design.md` section 9):

| Part | Allow-list |
|---|---|
| `mouth/smile` | `corporate-janitor` |
| `moustache/on` | `joe-*`, `dealer-winston` (the single exception, kept by the owner 2026-09-28) |
| `mouth/displeased` | `replacement-kenji` |

`face-compose --appearance <name>` enforces the list and refuses anyone else;
`--context portrait` exempts portrait work, because portraits carry all
expression. Changing the allow-list is an owner decision, not a code change.
Neutral mouth styles are not reserved: decision 38 requires one on every named
sprite face, and each must remain visible after mapping to `skin-deep`.

## Head anatomy (never draw a flat head)

A head is a skull, not a box. The first kit shipped side views 10 px deep under a
14 px-wide front, with a straight back edge: every character looked like half their
brain was missing (owner, 2026-09-28). These rules are enforced by
`test_heads_are_anatomical` in `tools/pixel-core/tests/test_face_kit.py`:

- **Profiles are deeper than the front is wide.** A skull measures more front to back
  than ear to ear. Body A: front 14, profile 15. Body B: front 13, profile 14. Move the
  head's rig placement so the deeper profile fits the canvas; never cut the skull.
- **The cranium sits behind the ear.** In a profile, roughly half the head lies behind
  the ear; the face takes the front third. Draw the ear (a small C in the skin shadow,
  behind the jaw at eye-to-nose height) so the eye has a landmark to sit in front of.
- **The back of the skull is round.** It bulges past the neck and curves in under the
  occiput; no straight vertical back edge longer than 5 rows, and the bottom row is
  narrower than the widest row.
- **The crown is domed.** The top row spans at most 60% of the widest row, and the
  head widens over at least three rows before reaching full width.
- **Hair follows the skull, not a lid.** Hair adds 1 px of volume outside the skull at
  most, sits in front of the ear (sideburn) and behind it, and covers the ear only when
  the style does (long hair, wraps). Side-view hair is retyped whenever a head changes.
- **Check it by looking.** Render the bare heads (`face-sheet` directions sheet) and a
  few dressed characters in all four views at 1x before anything else; if the side
  view is narrower than the front, stop and redraw.

## Sprite face distinctness (decision 38)

The first hand-drawn kit was rejected in the owner's 2026-09-28 review. One outline
per build, dot eyes, one nose and mouthless ordinary faces made hair carry identity.
Do not repair that kit by reshuffling its existing combos. The replacement contract is:

- Draw four skull-safe head shapes per build — round, long, square jaw and narrow chin —
  in all four directions on the existing 16x32 canvas. `up` shows shape and shaded ears.
- Shade every head in three skin-ramp tones with top-left light, a far-cheek shadow column,
  and shadow under the hairline and chin. No pillow shading, dithering or noise.
- Expand hand-typed parts to include 2 px-high or 2 px-wide eyes where useful, a light
  pixel beside selected pupils, tired lids; flat, arched, angled-stern, thick and sparse
  brows in the hair ramp; dot, long 2 px and broad noses in skin shadow; neutral 1 px,
  neutral 2 px, lip-shadow and off-centre mouths; cheek/blush pixels, freckles, a mole,
  eye bags and front-view ear shading.
- Glasses, stubble, beard and age lines appear only where the character's look sheet lists
  them. Smile stays corporate-only, displeased stays Kenji-only, and moustache stays Joe-only
  with Winston as the single recorded exception.
- A composition is head outline + eyes + brows + nose + mouth + extras. No two principals,
  original janitors or dealers share one. Replacements may repeat only when hair or skin differs.
  Same-person player outfits share a face; each Joe inherits the taken original plus moustache.
- On a hair-masked front sheet, every principal and original differs from every other by at
  least 3 face pixels. Grey only hair and headwear; never recolour or hide the face itself.
- Test every named face for a mouth and for visible eyes and mouth on `skin-deep`. The accepted
  deep-skin eye contrast exception does not excuse a mouth disappearing into the head.

Enforce those composition, 3-pixel, mouth and deep-skin visibility rules in
`tools/pixel-core/tests/test_face_kit.py` as the replacement grids land. A Phase 2 or Phase 3
kit commit cannot defer the tests or weaken a threshold to make its own art pass.

Before applying the kit cast-wide, prove 2-3 variants each of Pitt, Teller, Walt and Gus at
1x and 4x on all four skin ramps and the Rock Bottom and Golden Parachute carpets. Include the
hair-masked sheet, record every loser in `face_builder_docs.md`, and stop for the owner's pick.
The assignments live in `docs/character_design.md` section 4. Nothing is approved on inference.

## Portraits (64x64, real shading)

Dialogue portraits are **64x64** (owner, 2026-09-28, decision 37; `docs/pixel_art.md`
sections 4 and 7, `docs/character_design.md` section 8). The game stays at 480x270:
the portrait is where a face carries expression, so it gets a full drawing pass, not
flat blocks. The committed 48x48 grids in `art/src/rig/portraits/` are legacy
starters with 2x2 eyes and no shading; redraw them, never upscale them.

**Absolute ban on script-generated portraits.** No script or code may write, generate,
or derive portrait pixels: loops, repeated string math (`"b"*12 + "c"*16`), or procedural
generators are strictly forbidden. They produce mechanical, lifeless results: vertical
bisecting split lines, staircase jaws, rectangular eyes, and helmet hair. The portrait
`.txt` files must be the source of truth, hand-typed pixel by pixel or edited with
`pixel-refine` patches.

**Style test gate.** Before drawing full-cast portraits or expression sets, a style
test must be conducted on **Mr. Pitt neutral only** across three distinct artistic
styles:
1. **Soft and friendly** (Stardew-like chibi): larger eyes with sclera whites, iris,
   pupil, and 1 px catchlight; rounded shapes; blush tone; fewer harsh lines.
2. **Graphic and flat:** bold deadpan casino satire tone, strong silhouette, 2–3
   bold tones, crisp planar cuts.
3. **Semi-realistic:** organic facial planes (brow ridge, zygomatic cheekbone, chin pad,
   jaw angle), sculpted top-left lighting, detailed hair lock clusters.

**Visible 4-stage progression.** Each style must be developed and presented in four
visible stages:
1. **Silhouette:** outer form, head proportions, hair volume, curved shoulder slope.
2. **3 Values:** form lighting, facial planes; light strictly follows 3D volume from
   the top left, never a straight vertical split.
3. **Colour:** palette mapping to skin, hair, suit, tie.
4. **Details:** eyes with shaped lids, white, iris, pupil, 1 px specular catchlight;
   shaded nose bridge without outline; clustered hair with broken hairline; lapels
   and collar folds; earpiece.

**Judge in context at 1× and 4×.** Each stage and finished style must be previewed
inside the actual 480×270 in-game dialogue frame (`src/game/ui/dialogue.ts`) at native
1× and 4× zoom before proceeding. Stop and obtain explicit owner approval before
drawing any other character or expression.

**Skin ramp friction (for brightness test).** The current `skin-light` ramp transitions
from pink highlight (`#fcd1c9`) to greyish beige (`#c4a793`) to grey-brown (`#6b554d`).
Its shadows shift grey and lifeless. Appealing skin requires shadows that shift warmer
and redder, plus a dedicated blush tone for cheeks, nose, and ears.

**Frame.** Head and shoulders, chibi-leaning: the head is about 60% of the frame
(roughly 36-40 px tall, 30-36 px wide), eye line around rows 26-30, shoulders
cut by the bottom edge. Same hair, headwear, glasses and signature as the sprite.

**The checklist (every portrait, every expression):**

1. **Light from the top left.** Every shadow falls down and right, following form.
2. **Skin in four tones** of its ramp: highlight (forehead, left cheekbone, nose
   ridge), base, shadow, deep shadow. Shadow shapes: under the brow ridge, down
   the far (right) side of the nose, under the nose, under the lower lip, under
   the jaw onto the neck, and the far cheek. Draw in the `skin-light` ramp and
   swap per skin, as sprites do.
3. **Eyes** at least 3 px wide: a white (`paper` or `screen-highlight`), an iris,
   an `ink-1` pupil, an upper lid line in `ink-1` or the ramp's darkest; a
   1 px catchlight at the top left. The lower lid is a skin shadow, not a line.
4. **Brows** 1-2 px thick in the hair ramp's dark tone; they carry most of the
   expression.
5. **Nose by shading**, never an outline: a highlight on the ridge, shadow on the
   far side and under the tip, a 1 px nostril hint at most.
6. **Mouth** a 1 px line in a darker skin or lip tone; the corners set the
   expression; the lower lip is a highlight with a shadow under it.
7. **Hair in clusters**, three tones plus a top-left highlight band; a broken,
   natural hairline, never a ruler-straight edge or a flat fill.
8. **Selective outline:** `ink-1` on the outer silhouette only; inside the face
   and where forms overlap, use the ramp's darkest tone.
9. **Clothes** in three tones with fold shadows; collars and lapels overlap the neck.
10. **Never:** script or loop generation of portrait pixels, dithering or noise on
    skin, pillow shading (a dark rim all round), banding (parallel lines of tones),
    orphan single pixels, the reserved `money` or `ruin` colours, anything that
    depicts or implies self-harm.

**Expressions** are the same drawing with brows, lids, mouth and at most a 1 px
head tilt changed: neutral, pleased, displeased and the look sheet's special.

**Workflow.**

1. `pt rig-portrait` writes a 4x bust starter (64x64) from the sprite: use it only
   to place proportions and colours, then type the portrait over it.
2. Complete the 3-style Mr. Pitt neutral test in 4 visible stages, judge in the
   dialogue box at 1× and 4×, and stop for owner style selection.
3. Draw 2-3 variants of the neutral, render each at 1x and 4x, pick one, and record
   the loser and why in `face_builder_docs.md`.
4. Kit work (player, sibling): `pt rig-portrait-kit` composes a 64x64 `base.txt`
   plus full-size 64x64 layers and refuses any other size (`PORTRAIT_SIZE` in
   `pixel_tech.py`).
5. Validate every file (portrait category, 64x64 maximum, no reserved colours), then
   look at each one next to the sprite at 1x and 4x, and in the dialogue box's 64x64
   slot (`src/game/ui/dialogue.ts`) once the build includes portraits.
6. When the redraws pass, drop the portrait exclusion in `tools/art/build.mjs`
   (step 6) and add a pixel-core test that validates every committed portrait at 64x64.

## How to work

1. **Type the grid, do not derive it.** Draw a part by writing its text grid:
   type the pixels, render, look. Never compute a silhouette, symmetric line or
   spacing rule in code; never write loops or scripts that generate portrait
   pixels. The only formulas allowed are the slot anchors that place a finished
   grid.
2. **Iterate visibly.** Draw at least 2-3 variants of any new head or part, put
   them side by side at 1x and 4x on every skin ramp, pick one, and record the
   loser and the reason in `face_builder_docs.md`. Losers stay out of the kit.
3. **Judge at 1x, on carpet.** Decisions are made on the front carpets
   (e.g. `art/src/tiles/front-2-second-chance-carpet.txt`), not on a flat background at 4x. The 4x
   zoom is for seeing 1x pixels, not for judging.
4. **All four directions.** Down, up, left and right for every part that shows.
   `right` profiles are hand-typed as the exact mirror of the left silhouette
   with the light re-placed (the top-left rim never flips); `face_kit` fails a
   part that lands outside its head or on a transparent head pixel.
5. **Consistency.** The same person must read as the same person in all four
   directions and in the portrait. Slot anchors are per build and direction in
   `kit.json`; move a part by moving its anchor, never by editing positions into
   the patch.

## Quality bar

- Run `pt face-sheet` and open every output with the image viewer before
  committing; a successful command is not approval.
- Readability answers recorded per stage in `face_builder_docs.md`: facing
  readable at 1x; tired differs from plain; glasses read as glasses; eyes stay
  visible on deep and dark skin; every mouth stays visible on deep skin; the
  hair-masked composition tests pass; no carpet makes the face stop reading.
- Contrast checks flag failures; never silently change a skin, hair or carpet
  colour. The palette is the owner's.
- The firm line holds in faces: ruin, gauntness, hollow eyes or anything that
  depicts or implies self-harm is never drawn. Faces show age and tiredness only
  as the design doc allows.
- Nothing player-facing gets emoji, developer jargon, or real brands, and
  nothing is marked approved on the owner's behalf.

## Handoff

- Commit after each stage with only your own files; other agents commit here.
- Builders (`face-compose`, `face-sheet`, `build_cast_art.py`) are deterministic;
  re-run and confirm no diff before committing.
- If you stop mid-stage, leave a progress note in `face_builder_docs.md` so the
  next session can pick up the variant trail.

## Extending the kit

- **New part style:** type `parts/<part>-<style>.<dir>.txt` (and per-build
  overrides if the spacing differs), add the style to `kit.json` parts, then a
  face combo if the cast needs one. Add the style to the tests' expectations.
- **New face combo:** add it to `faces` in `kit.json`; reserved combos need an
  allow-list entry and the owner's word.
- **New head shape:** type all four direction grids for that build, preserving the
  anatomy rules and canvas; refit hair and headwear by hand, add the shape to the
  manifest and distinctness tests, then run the full variant and carpet review.
- **New build (Body C was closed 2026-09-28; a new build needs the owner's word):** draw its four head outlines at its decided
  size, add a `builds` entry with slots, and wire the rig part placements.
- **Portraits (Stage 5):** 64x64 with real shading; see "Portraits" above.
  Portrait composition sets `--context portrait`, which exempts expressions from
  the sprite reservations.
- Head sizes and the body proportions under them are owned by
  `docs/character_design.md` section 4; the rig placements live in
  `art/src/rig/body-a/rig.json` and `art/src/rig/body-b/rig.json` and are re-fitted when bodies change.
