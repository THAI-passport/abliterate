#!/usr/bin/env python3
"""Write the Stage 2 body parts (torso, arms, legs) for Body A and Body B.

Every grid below is hand-typed (face_builder_docs.md, Stage 2). This script only
writes them to `art/src/rig/<build>/parts/`. The single derived step is the far
leg in side views, which is the near leg recoloured one step darker for depth
(a recolour, not new geometry). Heads are owned by the face kit and untouched.

Conventions:
  L = skin light, B = skin base, S = skin shadow; light comes from the top left.
  Arms: the last two rows are the hand (outfits paint the rows above only).
  Legs: the last two rows are the shoe (outfits paint trousers above them).
  Proportions: Body A head y0-12, torso y13-20 (8 rows), legs y21-29 (9 rows);
  Body B head y1-13, torso y14-20 (7 rows), same legs.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEGEND = {"L": "skin-light-light", "B": "skin-warm-light", "S": "skin-deep-light"}
DARKER = {"L": "B", "B": "S", "S": "S", ".": "."}


def g(text: str) -> list[str]:
    rows = [row.strip() for row in text.strip().splitlines()]
    assert len({len(row) for row in rows}) == 1, rows
    return rows


def darker(rows: list[str]) -> list[str]:
    return ["".join(DARKER[c] for c in row) for row in rows]


# ---------------------------------------------------------------- Body A
A = {}
A["torso.down"] = g("""
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBSS
LBBBBBBBSS
SSSSSSSSSS""")
A["torso.down.upright"] = A["torso.down"]
A["torso.down.stoop"] = g("""
.SBBBBBBS.
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBBS
LBBBBBBBSS
LBBBBBBBSS
SSSSSSSSSS""")
A["torso.left"] = g("""
LBBBBS
LBBBBS
LBBBBS
LBBBBS
LBBBBS
LBBBBS
LBBBSS
SSSSSS""")
A["torso.left.upright"] = g("""
LBBBBS
LBBBBS
LBBBBS
LBBBBS
.LBBBS
.LBBBS
.LBBSS
.SSSSS""")
A["torso.left.stoop"] = g("""
LBBBBSS
LBBBBBS
LBBBBS.
LBBBBS.
LBBBBS.
LBBBBS.
LBBBSS.
SSSSSS.""")
A["torso.right"] = A["torso.left"]
A["torso.right.upright"] = g("""
LBBBBS
LBBBBS
LBBBBS
LBBBBS
LBBBS.
LBBBS.
LBBSS.
SSSSS.""")
A["torso.right.stoop"] = g("""
LLBBBBS
LBBBBBS
.LBBBBS
.LBBBBS
.LBBBBS
.LBBBBS
.LBBBSS
.SSSSSS""")

A["arm_l.down"] = g("""
.S
LS
LS
LS
LS
LS
LS
LB
BS""")
A["arm_r.down"] = g("""
B.
BS
BS
BS
BS
BS
BS
BB
SS""")
A["arm_l.down.reach"] = g("""
.S
LS
LS
LS
LB
BS""")
A["arm_r.down.reach"] = g("""
B.
BS
BS
BS
BB
SS""")
A["arm_l.left"] = g("""
SB
SB
SB
SB
SB
SB
SB
LB
BS""")
A["arm_r.left"] = g("""
SS
SS
SS
SS
SS
SS
SS
SS
SS""")
A["arm_l.left.reach"] = g("""
..SB
.SB.
SB..
LB..
BS..""")
A["arm_r.left.reach"] = g("""
SS
SS
SS
SS
SS
SS""")
A["arm_r.right"] = g("""
BS
BS
BS
BS
BS
BS
BS
LB
BS""")
A["arm_l.right"] = A["arm_r.left"]
A["arm_r.right.reach"] = g("""
BS..
.BS.
..BS
..LB
..BS""")
A["arm_l.right.reach"] = A["arm_r.left.reach"]

A["leg.down"] = g("""
LBBS
LBBS
LBBS
LBBS
LBBS
LBBS
LBBS
LBBS
SSSS""")
A["leg.down.passing"] = g("""
LBBS
LBBS
LBBS
LBBS
LLBS
LBBS
LBBS
SSSS
....""")
A["leg_l.down.turnout"] = g("""
.LBS
.LBS
.LBS
.LBS
.LBS
.LBS
.LBS
LBBS
SSS.""")
A["leg_r.down.turnout"] = g("""
LBS.
LBS.
LBS.
LBS.
LBS.
LBS.
LBS.
LBBS
.SSS""")
A["leg.down.sit"] = g("""
....
....
....
....
LBBS
LBBS
LBBS
LBBS
SSSS""")
A["leg.left"] = g("""
.LBS
.LBS
.LBS
.LBS
.LBS
.LBS
.LBS
LBBS
SSSS""")
A["leg.left.contact"] = g("""
.LBS
.LBS
.LBS
LBS.
LBS.
LBS.
LBS.
LBB.
SSS.""")
A["leg.left.passing"] = g("""
.LBS
.LBS
.LBS
..LB
..LB
..LB
..LB
.LBB
..SS""")
A["leg.left.sit"] = g("""
....
....
....
....
LBBB
LBS.
LBS.
LBB.
SSS.""")
A["leg.right"] = g("""
LBS.
LBS.
LBS.
LBS.
LBS.
LBS.
LBS.
LBBS
SSSS""")
A["leg.right.contact"] = g("""
LBS.
LBS.
LBS.
.LBS
.LBS
.LBS
.LBS
.LBB
.SSS""")
A["leg.right.passing"] = g("""
LBS.
LBS.
LBS.
LB..
LB..
LB..
LB..
LBB.
SS..""")
A["leg.right.sit"] = g("""
....
....
....
....
LBBB
.LBS
.LBS
.LBB
.SSS""")

# ---------------------------------------------------------------- Body B
B = {}
B["torso.down"] = g("""
LBBBBBBS
LBBBBBBS
LBBBBBBS
.LBBBBS.
.LBBBBS.
LBBBBBBS
LBBBBBSS
SSSSSSSS""")
B["torso.down.upright"] = B["torso.down"]
B["torso.down.stoop"] = g("""
.SBBBBS.
LBBBBBBS
LBBBBBBS
.LBBBBS.
.LBBBBS.
LBBBBBBS
LBBBBBSS
SSSSSSSS""")
B["torso.left"] = g("""
LBBBS
LBBBS
LBBBS
.LBBS
.LBBS
LBBBS
LBBSS
SSSSS""")
B["torso.left.upright"] = g("""
LBBBS
LBBBS
LBBBS
.LBBS
.LBBS
.LBBS
.LBSS
.SSSS""")
B["torso.left.stoop"] = g("""
LBBBSS
LBBBBS
LBBBS.
.LBBS.
.LBBS.
LBBBS.
LBBSS.
SSSSS.""")
B["torso.right"] = g("""
LBBBS
LBBBS
LBBBS
LBBS.
LBBS.
LBBBS
LBBSS
SSSSS""")
B["torso.right.upright"] = g("""
LBBBS
LBBBS
LBBBS
LBBS.
LBBS.
LBBS.
LBSS.
SSSS.""")
B["torso.right.stoop"] = g("""
LLBBBS
LBBBBS
.LBBBS
.LBBS.
.LBBS.
.LBBBS
.LBBSS
.SSSSS""")

B["arm_l.down"] = g("""
.S
LS
LS
LS
LS
LS
LS
.B
.S""")
B["arm_r.down"] = g("""
B.
BS
BS
BS
BS
BS
BS
B.
S.""")
B["arm_l.down.reach"] = g("""
.S
LS
LS
LS
.B
.S""")
B["arm_r.down.reach"] = g("""
B.
BS
BS
BS
B.
S.""")
B["arm_l.left"] = A["arm_l.left"]
B["arm_r.left"] = A["arm_r.left"]
B["arm_l.left.reach"] = A["arm_l.left.reach"]
B["arm_r.left.reach"] = A["arm_r.left.reach"]
B["arm_r.right"] = A["arm_r.right"]
B["arm_l.right"] = A["arm_l.right"]
B["arm_r.right.reach"] = A["arm_r.right.reach"]
B["arm_l.right.reach"] = A["arm_l.right.reach"]

B["leg.down"] = g("""
LBS
LBS
LBS
LBS
LBS
LBS
LBS
LBS
SSS""")
B["leg.down.passing"] = g("""
LBS
LBS
LBS
LBS
LLS
LBS
LBS
SSS
...""")
B["leg_l.down.turnout"] = g("""
LBS
LBS
LBS
LBS
LBS
LBS
LBS
LBS
SS.""")
B["leg_r.down.turnout"] = g("""
LBS
LBS
LBS
LBS
LBS
LBS
LBS
LBS
.SS""")
B["leg.down.sit"] = g("""
...
...
...
...
LBS
LBS
LBS
LBS
SSS""")
B["leg.left"] = g("""
.LS.
.LS.
.LS.
.LS.
.LS.
.LS.
.LS.
LBS.
SSS.""")
B["leg.left.contact"] = g("""
.LS.
.LS.
.LS.
LS..
LS..
LS..
LS..
LBS.
SSS.""")
B["leg.left.passing"] = g("""
.LS.
.LS.
.LS.
..LS
..LS
..LS
..LS
.LBS
..SS""")
B["leg.left.sit"] = g("""
....
....
....
....
LBBS
LS..
LS..
LBS.
SSS.""")
B["leg.right"] = g("""
.LS.
.LS.
.LS.
.LS.
.LS.
.LS.
.LS.
.LBS
.SSS""")
B["leg.right.contact"] = g("""
.LS.
.LS.
.LS.
..LS
..LS
..LS
..LS
.LBS
.SSS""")
B["leg.right.passing"] = g("""
.LS.
.LS.
.LS.
LS..
LS..
LS..
LS..
LBS.
SS..""")
B["leg.right.sit"] = g("""
....
....
....
....
LBBS
..LS
..LS
.LBS
.SSS""")

# Upright posture: square shoulders (the top row of each arm filled, not rounded),
# per character_design.md section 2. Side views keep the base arm.
for _parts in (A, B):
    _parts["arm_l.down.upright"] = ["LS"] + _parts["arm_l.down"][1:]
    _parts["arm_r.down.upright"] = ["BS"] + _parts["arm_r.down"][1:]
    for _side in ("left", "right"):
        for _arm in ("arm_l", "arm_r"):
            _parts[f"{_arm}.{_side}.upright"] = _parts[f"{_arm}.{_side}"]

# Body B is 1 px shorter than A, all in the torso (character_design.md section 2):
# its torsos are typed with the same shoulders, then one shoulder row is removed.
for _key in [k for k in B if k.startswith("torso.")]:
    B[_key] = B[_key][:1] + B[_key][2:]

# Hand anchors (x, y) inside each arm grid: the bottom hand pixel.
HAND = {
    "arm_l.down": (0, 8), "arm_r.down": (1, 8), "arm_l.down.reach": (0, 5), "arm_r.down.reach": (1, 5),
    "arm_l.left": (0, 8), "arm_r.left": (0, 8), "arm_l.left.reach": (0, 4), "arm_r.left.reach": (0, 5),
    "arm_r.right": (1, 8), "arm_l.right": (1, 8),
    "arm_l.down.upright": (0, 8), "arm_r.down.upright": (1, 8), "arm_l.left.upright": (0, 8),
    "arm_r.left.upright": (0, 8), "arm_r.right.upright": (1, 8), "arm_l.right.upright": (1, 8), "arm_r.right.reach": (3, 4), "arm_l.right.reach": (1, 5),
}
# Grids wider than their slot on the far side are placed by pivot.
PIVOT = {"torso.right.stoop": (1, 0), "arm_l.left.reach": (2, 0)}


def expand(parts: dict[str, list[str]]) -> dict[str, list[str]]:
    """Turn the typed set into the rig's full file list (all four directions)."""
    out: dict[str, list[str]] = {}
    for key, rows in parts.items():
        if key.startswith("leg."):
            continue
        out[key] = rows
    # Back view: the same drawings as the front (the light still comes from the top left).
    for key in list(out):
        if ".down" in key:
            out[key.replace(".down", ".up")] = out[key]
    # Legs: down/up share drawings; in side views leg_l is near on the left, leg_r near on the right.
    for variant in ("", ".contact", ".passing", ".sit"):
        down = parts.get("leg.down" + variant) or parts["leg.down"]
        for side in ("leg_l", "leg_r"):
            for view in ("down", "up"):
                out[f"{side}.{view}{variant}"] = down
        left, right = parts["leg.left" + variant], parts["leg.right" + variant]
        out[f"leg_l.left{variant}"] = left
        out[f"leg_r.left{variant}"] = darker(left)
        out[f"leg_r.right{variant}"] = right
        out[f"leg_l.right{variant}"] = darker(right)
    for side in ("leg_l", "leg_r"):
        for view in ("down", "up"):
            out[f"{side}.{view}.turnout"] = parts[f"{side}.down.turnout"]
        out[f"{side}.left.turnout"] = out[f"{side}.left"]
        out[f"{side}.right.turnout"] = out[f"{side}.right"]
    return out


def write(build: str, parts: dict[str, list[str]]) -> int:
    folder = ROOT / "art/src/rig" / build / "parts"
    for old in folder.glob("*.txt"):
        if not old.name.startswith("head."):
            old.unlink()
    count = 0
    for key, rows in sorted(expand(parts).items()):
        part, view = key.split(".")[:2]
        headers = [f"size: {len(rows[0])}x{len(rows)}", "palette: game", "frames: 1"]
        px, py = PIVOT.get(key, (0, 0))
        headers.append(f"pivot: {px},{py}")
        if part.startswith("arm"):
            bits = key.split(".")
            bits[1] = "down" if bits[1] == "up" else bits[1]
            hx, hy = HAND[".".join(bits)]
            headers.append(f"anchor-hand: {hx},{hy}")
        headers.append("semantic: skin")
        used = sorted({c for row in rows for c in row} - {"."})
        legend = ["  . = transparent"] + [f"  {c} = {LEGEND[c]}" for c in used]
        text = [f"# {build} {key}; hand-typed, Stage 2 chibi proportions (face_builder_docs.md)."]
        text += headers + ["legend:"] + legend + ["grid:"] + rows
        (folder / f"{key}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
        count += 1
    return count


if __name__ == "__main__":
    print("body-a", write("body-a", A))
    print("body-b", write("body-b", B))
