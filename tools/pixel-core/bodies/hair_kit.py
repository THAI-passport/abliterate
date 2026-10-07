#!/usr/bin/env python3
"""Write the hand-typed hair styles and headwear as rig layers for Body A and Body B.

Every grid here is typed by hand (face_builder_docs.md, Stages 3-4) and sits in the
head grid's own coordinates (pivot 0,0 = the head's top-left). The script only
writes files. The one derived step: side-view hair and headwear are lit from
straight above (highlight on the top rows only), so the `right` view is the exact
mirror of the typed `left` view; there is no light to re-place.

Letters:
  D = hair base (ink-2), H = hair highlight (screen-dark); both follow the hair swap.
  W / w = covering fabric light / dark; each wearer has a fixed, non-reserved ramp.
  Headwear letters are defined per piece in HEADWEAR_LEGEND.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HAIR_LEGEND = {"D": "ink-2", "H": "screen-dark"}
COVERING_LEGENDS = {
    "wrapped-farida": {"W": "felt-teal", "w": "screen-shadow"},
    "wrapped-fatou": {"W": "violet-dark", "w": "violet-shadow"},
    "covered-nasrin": {"W": "metal-2", "w": "metal-1"},
}
HEADWEAR_LEGEND = {
    "K": "ink-4", "M": "metal-1",                 # brimmed hat
    "G": "felt-green", "T": "felt-teal",          # eyeshade
    "R": "violet-dark", "r": "felt-oxblood",      # ball cap (oxblood; never the reserved ruin ramp)
    "V": "screen-base", "v": "screen-shadow",     # knit watch cap (navy)
    "S": "money-light", "s": "money-base",        # scrub cap
}


def g(text: str) -> list[str]:
    rows = [row.strip() for row in text.strip().splitlines()]
    assert len({len(row) for row in rows}) == 1, rows
    return rows


HAIR: dict[tuple[str, str, str], list[str]] = {}
COVERINGS: dict[tuple[str, str, str], list[str]] = {}
HEADWEAR: dict[tuple[str, str, str], list[str]] = {}


def hair(build: str, style: str, **views: str) -> None:
    for view, text in views.items():
        HAIR[(build, style, view)] = g(text)


def covering(build: str, style: str, **views: str) -> None:
    for view, text in views.items():
        COVERINGS[(build, style, view)] = g(text)


def headwear(build: str, piece: str, **views: str) -> None:
    for view, text in views.items():
        HEADWEAR[(build, piece, view)] = g(text)


# ======================================================================= Body A
# Head (face_builder_docs.md, "Heads with skulls"): down/up 14x13 with a domed crown
# (row 0 x4-9, row 1 x2-11, row 2 x1-12); left 15x13, deeper than the front, with
# the ear at x8-9 rows 6-8. Eyes on row 6, brows row 5: fringes stop at row 4.
# Side hair sits in front of the ear (sideburn) and behind it, never on it, except
# where the style covers the ears (long hair, wraps). Hair may add 1 px of volume
# outside the skull.

hair("body-a", "side-part", down="""
...HHH.DDDD...
.HHHHH.DDDDDD.
HHHHDDDDDDDDDD
HHDDDDDDDDDDDD
HD.......DDDDD
D............D
D............D""", up="""
...HHHDDDD....
.HHHHDDDDDDDD.
HHHDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
....HHHHHH.....
..HHHHHHHHHD...
.HHDDDDDDDDDD..
.DDDDDDDDDDDDD.
.D..DDDDDDDDDDD
.....DDDDDDDDDD
......DD..DDDDD
.......D..DDDDD
..........DDDDD
...........DDD.
............DD.""")

hair("body-a", "slicked-back", down="""
...DDDHDDDD...
.DDDDDHDDDDDD.
DDDDDDHDDDDDDD
DD..........DD
D............D
D............D""", up="""
...DDHHDDD....
.DDDHHDDDDDDD.
.DDHHDDDDDDDD.
DHHDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
....HHHHHH.....
..DHHHHHHHDD...
.DDDDDDDDDDDD..
..DDDDDDDDDDDD.
.....DDDDDDDDDD
.....DDDDDDDDDD
......D...DDDDD
..........DDDDD
..........DDDDD
...........DDD.
............DD.""")

hair("body-a", "buzz", down="""
....DDDDDD....
..DDDDDDDDDD..
.DDDDDDDDDDDD.
...DDDDDDDD...""", up="""
....DDDDDD....
..DDDDDDDDDD..
.DDDDDDDDDDDD.
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
.....DDDDD.....
...DDDDDDDDD...
..DDDDDDDDDDD..
....DDDDDDDDDD.
.......DDDDDDDD
.........DDDDDD
..........DDDD.
...........DD..""")

hair("body-a", "crew", down="""
...HHHDDDDD...
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
DDDDDDDDDDDDDD
D............D""", up="""
...HHHDDDDD...
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DD.DDDDD.DD..""", left="""
....HHHHHH.....
..HHHHHHHHHD...
.HDDDDDDDDDDD..
.D.DDDDDDDDDDD.
.....DDDDDDDDDD
......DDDDDDDDD
......D...DDDDD
..........DDDDD
...........DDD.
............DD.""")

hair("body-a", "bun", down="""
....HHHDDD....
.HHHDDDDDDDD..
HHD.DDDDDDDDDD
DD..........DD
D............D
D............D
D............D""", up="""
....DDDDDD....
.DDDDHHDDDDDD.
DDDDHDDHDDDDDD
DDDDHDDHDDDDDD
DDDDDHHDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
....HHHHH.HHH..
..DDDDDDDDHDDH.
.DDDDDDDDDDHDDH
..DDDDDDDDDDHD.
.....DDDDDDDDDD
......DDDDDDDDD
......D...DDDDD
..........DDDDD
..........DDDD.
...........DDD.
............DD.""")

hair("body-a", "ponytail", down="""
...HHHHDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
DD..........DD
D............D""", up="""
...HHHDDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.
.....HDD......
.....HDD......
.....HDD......
......D.......""", left="""
....HHHHHH.....
..DDDDDDDDDD...
.DDDDDDDDDDDH..
..DDDDDDDDDDDH.
.....DDDDDDDDDH
......DDDDDDDHD
......D...DDDHD
..........DDDHD
..........DDDDD
...........DDHD
.............HD
..............D""")

hair("body-a", "long-straight", down="""
...HHHH.DDD...
.HHHHHH.DDDDD.
HHHHH...DDDDDD
HHH.......DDDD
HH.........DDD
HH..........DD
H............D
H............D
H............D
H............D
H............D
HH..........DD
HH..........DD
HH..........DD
HD..........DD""", up="""
...HHHDDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.
.DDDDDDDDDDDD.
.DDDDDDDDDDDD.
..DDDDDDDDDD..""", left="""
....HHHHHH.....
..HHHHHHHHHD...
.HDDDDDDDDDDD..
.DDDDDDDDDDDDD.
.D..DDDDDDDDDDD
.....DDDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDD.
.......DDDDDDD.
.......DDDDDD..
........DDDD...""")

hair("body-a", "bob", down="""
...HHHH.DDD...
.HHHHHH.DDDDD.
HHHHH...DDDDDD
HHH.......DDDD
HH.........DDD
HH..........DD
H............D
H............D
H............D
HH..........DD
.HH........DD.
..HH......DD..""", up="""
...HHHDDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.
..DDDDDDDDDD..
...DDDDDDDD...""", left="""
....HHHHHH.....
..HHHHHHHHHD...
.HDDDDDDDDDDD..
.DDDDDDDDDDDDD.
.D..DDDDDDDDDDD
.....DDDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDDD
......DDDDDDDD.
.......DDDDDDD.
.......DDDDDD..""")

hair("body-a", "braid", down="""
...HHHHDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
DD..........DD
D............D""", up="""
...HHHDDDD....
.HHHDDDDDDDDD.
HHDDDDDDDDDDDD
HDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.
.....HDD......
.....DDH......
.....HDD......
.....DDH......
......D.......
......D.......""", left="""
....HHHHHH.....
..DDDDDDDDDD...
.DDDDDDDDDDDH..
..DDDDDDDDDDDH.
.....DDDDDDDDDH
.....DDDDDDDDDH
......DDDDDDDHD
......D...DDDHD
..........DDHDD
..........DDDHD
...........DHDD
...........DDHD
............HDD
............DDH
.............DD
..............D""")

hair("body-a", "curly-short", down="""
...HHD.HH.DD..
HHHDDHHDDHHDDD
HHDDHHDDHHDDDD
DDHD.DD.DD.DDD
D............D""", up="""
...HHD.HH.DD..
HHHDDHHDDHHDDD
HDDHHDDHHDDDDD
DDHHDDHHDDDDDD
HDDDDHHDDDHHDD
DDHHDDDDHHDDDD
DDDDDHHDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
....HH.DH.H....
.HHHDDHHDDHHD..
.HDDHHDDHHDDH..
.D.DDDDHHDDHDD.
.....DDDDDHHDDD
......DDDDDDDHD
......D...DDDDD
..........DDDD.
...........DDD.""")

hair("body-a", "natural-rounded", down="""
..DHHHDDDDDD..
DHHHHDDDDDDDDD
DHHDDDDDDDDDDD
DHD........DDD
DD..........DD
DD..........DD
D............D
D............D""", up="""
..DHHHDDDDDD..
DHHHHDDDDDDDDD
DHHDDDDDDDDDDD
DHDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
...HHHHHHHH....
.HHHHHHHHHHDD..
HDDDDDDDDDDDDD.
DDDDDDDDDDDDDDD
DD..DDDDDDDDDDD
D....DDDDDDDDDD
.....DDD..DDDDD
......DD..DDDDD
.......D..DDDDD
..........DDDDD
...........DDD.""")

hair("body-a", "bald-receding", down="""
..............
..............
..............
D............D
DD..........DD
DD..........DD
D............D""", up="""
..............
..............
..............
..............
..............
..............
..............
D............D
DD..........DD
.DDDDDDDDDDDD.
..DDDDDDDDDD..""", left="""
...............
...............
...............
...............
...............
...............
......D.....DDD
.......D....DDD
............DDD
............DD.""")

hair("body-a", "big-set-curls", down="""
..HHDHHDHHDD..
HHDHHDHHDDDDDD
HDHHDDHDDDDDDD
DDH........DDD
DD..........DD
DD..........DD
DD..........DD
D............D""", up="""
..HHDHHDHHDD..
HHDHHDHHDDDDDD
HDHHDDHDDHHDDD
DDHDDHHDDHDDDD
DHHDDDDHHDDDHD
DDDDHHDDDDHHDD
DDHHDDDHHDDDDD
DDDDDDDDDDDDDD
DDDDDDDDDDDDDD
.DDDDDDDDDDDD.""", left="""
...HHDHHDHH....
.HHDHHDHHDDHD..
HDHHDDHDDHDDHD.
DDH.DHHDDHDDHDD
DD...DDHHDDDHDD
D.....DDDDDDHDD
......DD..DDDDD
.......D..DHDDD
..........DDDD.
...........DD..""")

covering("body-a", "wrapped-farida", down="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWWwwwwwwwww
WWwwwwwwwwwwww
Ww..........ww
W............w""", up="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWwwwwwwwwww
WWWwwwwwwwwwww
WWwwwwwwwwwwww
Wwwwwwwwwwwwww
Wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
.wwwwWWwwwwww.
......WWw.....
......ww......""", left="""
...WWWWWWW.....
.WWWWWWWWWWww..
.Wwwwwwwwwwwww.
.wwwwwwwwwwwwww
.w...wwwwwwwwww
.....wwwwwwwwww
.....wwwwwwwwww
......wwwwwwwWw
.......wwwwwWWw
.........wwwww.
...........ww..""")

covering("body-a", "wrapped-fatou", down="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWWwwwwwwwww
WWwwwwwwwwwwww
Ww..........ww
W............w""", up="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWwwwwwwwwww
WWWwwwwwwwwwww
WWwwwwwwwwwwww
Wwwwwwwwwwwwww
Wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
.wwwwWWwwwwww.
......WWw.....
......ww......""", left="""
...WWWWWWW.....
.WWWWWWWWWWww..
.Wwwwwwwwwwwww.
.wwwwwwwwwwwwww
.w...wwwwwwwwww
.....wwwwwwwwww
.....wwwwwwwwww
......wwwwwwwWw
.......wwwwwWWw
.........wwwww.
...........ww..""")

# Plain shoulder covering. The retained tapered variant leaves a clean neck gap at
# rows 13-15; a square hem was also drawn and reviewed, but merged with the coverall.
covering("body-a", "covered-nasrin", down="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWwwwwwwwwww
WWwwwwwwwwwwww
Ww..........ww
W............w
W............w
W............w
W............w
W............w
W............w
W............w
WW..........ww
WWW........www
WWWW......wwww
.WWW......www.""", up="""
...WWWWwwww...
.WWWWWwwwwwww.
WWWWwwwwwwwwww
WWWwwwwwwwwwww
WWwwwwwwwwwwww
Wwwwwwwwwwwwww
Wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
wwwwwwwwwwwwww
.wwwwwwwwwwww.
..wwwwwwwwww..
...wwwwwwww...
....wwwwww....""", left="""
...WWWWWWW.....
.WWWWWWWWWWww..
.Wwwwwwwwwwwww.
.wwwwwwwwwwwwww
.w...wwwwwwwwww
.....wwwwwwwwww
.....wwwwwwwwww
......wwwwwwwww
.......wwwwwwww
.........wwwwww
..........wwwww
..........wwwww
..........wwwww
..........wwwww
.........wwwwww
........wwwwwww""")

# ======================================================================= Body B
# Head: down/up 13x13, round (row 0 x4-8, row 1 x2-10, row 2 x1-11); left 14x13,
# deeper than the front, with the ear at x8-9 rows 5-7. Eyes on row 6.

hair("body-b", "side-part", down="""
...HH.DDDD...
.HHHH.DDDDDD.
HHHDDDDDDDDDD
HDDDDDDDDDDDD
HD......DDDDD
D...........D
D...........D""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
.DDDDDDDDDDD.""", left="""
....HHHHHH....
..HHHHHHHHD...
.HDDDDDDDDDD..
.DDDDDDDDDDDD.
.D..DDDDDDDDDD
.....DDD..DDDD
......D...DDDD
..........DDDD
...........DD.""")

hair("body-b", "slicked-back", down="""
...DDDHDDD...
.DDDDDHDDDDD.
DDDDDDHDDDDDD
DD.........DD
D...........D
D...........D""", up="""
...DDHHDDD...
.DDDHHDDDDDD.
.DDHHDDDDDDD.
DHHDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.""", left="""
....HHHHHH....
..DHHHHHHDD...
.DDDDDDDDDDD..
..DDDDDDDDDDD.
.....DDDDDDDDD
.....DDD..DDDD
..........DDDD
..........DDDD
...........DD.""")

hair("body-b", "buzz", down="""
....DDDDD....
..DDDDDDDDD..
.DDDDDDDDDDD.
...DDDDDDD...""", up="""
....DDDDD....
..DDDDDDDDD..
.DDDDDDDDDDD.
.DDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.""", left="""
.....DDDDD....
...DDDDDDDD...
..DDDDDDDDDD..
....DDDDDDDDD.
.......DDDDDDD
..........DDDD
..........DDD.
...........DD.""")

hair("body-b", "crew", down="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
DDDDDDDDDDDDD
D...........D""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DD.DDDDD.DD.""", left="""
....HHHHHH....
..HHHHHHHHD...
.HDDDDDDDDDD..
.D.DDDDDDDDDD.
.....DDDDDDDDD
.....DDD..DDDD
......D...DDDD
..........DDD.
...........DD.""")

hair("body-b", "bun", down="""
...HHHDDD....
.HHHDDDDDDDD.
HHD.DDDDDDDDD
DD.........DD
D...........D
D...........D
D...........D""", up="""
....DDDDD....
..DDDHHDDDD..
.DDDHDDHDDDD.
.DDDHDDHDDDDD
DDDDDHHDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
.DDDDDDDDDDD.""", left="""
....HHHHH.HH..
..DDDDDDDHDDH.
.DDDDDDDDDDHDH
..DDDDDDDDDDH.
.....DDDDDDDDD
.....DDD..DDDD
......D...DDDD
..........DDDD
..........DDD.
...........DD.""")

hair("body-b", "ponytail", down="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
DD.........DD
D...........D
D...........D""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
.....HDD.....
.....HDD.....
.....HDD.....
......D......""", left="""
....HHHHHH....
..DDDDDDDDD...
.DDDDDDDDDDH..
..DDDDDDDDDDH.
.....DDDDDDDDH
.....DDD..DDHD
......D...DDHD
..........DDHD
...........DHD
............HD
.............D
.............D""")

hair("body-b", "long-straight", down="""
...HHH.DDD...
.HHHHH.DDDDD.
HHHH....DDDDD
HHH.......DDD
HH.........DD
HH.........DD
H...........D
H...........D
H...........D
H...........D
HH.........DD
HH.........DD
HH.........DD
HD.........DD""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
.DDDDDDDDDDD.
..DDDDDDDDD..""", left="""
....HHHHHH....
..HHHHHHHHD...
.HDDDDDDDDDD..
.DDDDDDDDDDDD.
.D..DDDDDDDDDD
.....DDDDDDDDD
.....DDDDDDDDD
.....DDDDDDDDD
......DDDDDDDD
......DDDDDDDD
......DDDDDDD.
......DDDDDDD.
.......DDDDDD.
........DDDD..""")

hair("body-b", "bob", down="""
...HHH.DDD...
.HHHHH.DDDDD.
HHHH....DDDDD
HHH.......DDD
HH.........DD
HH.........DD
H...........D
H...........D
H...........D
HH.........DD
.HH.......DD.
..HH.....DD..""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
..DDDDDDDDD..
...DDDDDDD...""", left="""
....HHHHHH....
..HHHHHHHHD...
.HDDDDDDDDDD..
.DDDDDDDDDDDD.
.D..DDDDDDDDDD
.....DDDDDDDDD
.....DDDDDDDDD
.....DDDDDDDDD
......DDDDDDDD
......DDDDDDD.
......DDDDDDD.
.......DDDDDD.""")

hair("body-b", "braid", down="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
DD.........DD
D...........D""", up="""
...HHHDDDD...
.HHHDDDDDDDD.
HHDDDDDDDDDDD
HDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.
.....HDD.....
.....DDH.....
.....HDD.....
.....DDH.....
......D......
......D......""", left="""
....HHHHHH....
..DDDDDDDDD...
.DDDDDDDDDDH..
..DDDDDDDDDDH.
.....DDDDDDDDH
.....DDD..DDHD
......D...DDHD
..........DHDD
..........DDHD
...........HDD
...........DDH
............DD
............HD
............DD
.............D""")

hair("body-b", "curly-short", down="""
...HHDDHHD...
.HHDDHHDDHHD.
HHDDHHDDHHDDD
DDHD.DD.DD.DD
D...........D""", up="""
...HHDDHHD...
.HHDDHHDDHHD.
HDDHHDDHHDDDD
DDHHDDHHDDDDD
HDDDDHHDDDHHD
DDHHDDDDHHDDD
DDDDDHHDDDDDD
.DDDDDDDDDDD.""", left="""
....HHDDHH....
..HHDDHHDDH...
.HDDHHDDHHDD..
.D.DDDDHHDDHD.
.....DDDDDHHDD
.....DDD..DDHD
......D...DDDD
..........DDD.
...........DD.""")

hair("body-b", "natural-rounded", down="""
..DHHHDDDDD..
DHHHHDDDDDDDD
DHHDDDDDDDDDD
DHD.......DDD
DD.........DD
DD.........DD
D...........D
D...........D""", up="""
..DHHHDDDDD..
DHHHHDDDDDDDD
DHHDDDDDDDDDD
DHDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.""", left="""
...HHHHHHHH...
.HHHHHHHHHHD..
HDDDDDDDDDDDD.
DDDDDDDDDDDDDD
DD..DDDDDDDDDD
D....DDD..DDDD
......DD..DDDD
.......D..DDDD
..........DDDD
...........DD.""")

hair("body-b", "bald-receding", down="""
.............
.............
.............
D...........D
DD.........DD
DD.........DD
D...........D""", up="""
.............
.............
.............
.............
.............
.............
.............
D...........D
DD.........DD
.DDDDDDDDDDD.
..DDDDDDDDD..""", left="""
..............
..............
..............
..............
..............
............DD
......D....DDD
...........DDD
...........DDD
...........DD.""")

hair("body-b", "big-set-curls", down="""
..HHDHHDHHD..
HHDHHDHHDDDDD
HDHHDDHDDDDDD
DDH.......DDD
DD.........DD
DD.........DD
DD.........DD
D...........D""", up="""
..HHDHHDHHD..
HHDHHDHHDDDDD
HDHHDDHDDHHDD
DDHDDHHDDHDDD
DHHDDDDHHDDHD
DDDDHHDDDDHHD
DDHHDDDHHDDDD
DDDDDDDDDDDDD
.DDDDDDDDDDD.""", left="""
...HHDHHDHH...
.HHDHHDHHDDHD.
HDHHDDHDDHDDH.
DDH.DHHDDHDDHD
DD...DDHHDDDHD
D....DDD..DDHD
......DD..DDDD
.......D..DHDD
..........DDD.
...........DD.""")

covering("body-b", "wrapped-farida", down="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWwwwwwwwwwww
Ww.........ww
W...........w""", up="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWWwwwwwwwwww
WWwwwwwwwwwww
Wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
.wwwwWWwwwww.
.....WWw.....
.....ww......""", left="""
...WWWWWWW....
.WWWWWWWWWww..
.Wwwwwwwwwwww.
.wwwwwwwwwwwww
.w...wwwwwwwww
.....wwwwwwwww
.....wwwwwwwww
......wwwwwwWw
.......wwwwWWw
.........wwww.
..........ww..""")

covering("body-b", "wrapped-fatou", down="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWwwwwwwwwwww
Ww.........ww
W...........w""", up="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWWwwwwwwwwww
WWwwwwwwwwwww
Wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
.wwwwWWwwwww.
.....WWw.....
.....ww......""", left="""
...WWWWWWW....
.WWWWWWWWWww..
.Wwwwwwwwwwww.
.wwwwwwwwwwwww
.w...wwwwwwwww
.....wwwwwwwww
.....wwwwwwwww
......wwwwwwWw
.......wwwwWWw
.........wwww.
..........ww..""")

covering("body-b", "covered-nasrin", down="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWwwwwwwwwwww
Ww.........ww
W...........w
W...........w
W...........w
W...........w
W...........w
W...........w
W...........w
WW.........ww
WWW.......www
WWW.......www
.WW.......ww.""", up="""
...WWWwwww...
.WWWWWwwwwww.
WWWWwwwwwwwww
WWWwwwwwwwwww
WWwwwwwwwwwww
Wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
wwwwwwwwwwwww
.wwwwwwwwwww.
..wwwwwwwww..
...wwwwwww...
....wwwww....
.....www.....""", left="""
...WWWWWWW....
.WWWWWWWWWww..
.Wwwwwwwwwwww.
.wwwwwwwwwwwww
.w...wwwwwwwww
.....wwwwwwwww
.....wwwwwwwww
......wwwwwwww
.......wwwwwww
.........wwwww
.........wwwww
.........wwwww
.........wwwww
.........wwwww
........wwwwww
.......wwwwwww""")

# ======================================================================= Headwear
# Drawn over hair, on the same domed crowns and deep profiles. Mr. M's brim throws a
# band of shadow over the eyes (his eyes are never seen). Teller's eyeshade sits on
# the forehead above the brows.

headwear("body-a", "brimmed-hat", down="""
...MMMKKKK....
..MMMKKKKKKK..
.MMKKKKKKKKKK.
.KKKKKKKKKKKK.
MMMMKKKKKKKKKK
KKKKKKKKKKKKKK
..KKKKKKKKKK..""", up="""
...MMMKKKK....
..MMMKKKKKKK..
.MMKKKKKKKKKK.
.KKKKKKKKKKKK.
MMMMKKKKKKKKKK
KKKKKKKKKKKKKK""", left="""
....MMMMMM.....
...MMMKKKKK....
..MKKKKKKKKK...
..KKKKKKKKKKK..
MMMMKKKKKKKKKKK
KKKKKKKKKKKKKKK
.KKK...........""")
headwear("body-a", "eyeshade", down="""
..............
..............
.GGGGGGGGGGGG.
GGGGGGGGGGGGGG
TTTTTTTTTTTTTT""", up="""
..............
..............
.GGGGGGGGGGGG.
GGGGGGGGGGGGGG""", left="""
...............
...............
..GGGGGGGGGGG..
.GGGGGGGGGGGGG.
TTTT...........""")
headwear("body-a", "ball-cap", down="""
...RRRRrrrr...
.RRRRrrrrrrrr.
RRRrrrrrrrrrrr
RRrrrrrrrrrrrr
rrrrrrrrrrrrrr""", up="""
...RRRRrrrr...
.RRRRrrrrrrrr.
RRRrrrrrrrrrrr
Rrrrrrrrrrrrrr
rrrrrrrrrrrrrr""", left="""
....RRRRRR.....
..RRRRRRRRRr...
.RRrrrrrrrrrr..
.rrrrrrrrrrrrr.
rrrr...........""")
headwear("body-a", "watch-cap", down="""
...VVVVvvvv...
.VVVVvvvvvvvv.
VVVvvvvvvvvvvv
VVVVVVVVVVVVVV
vvvvvvvvvvvvvv""", up="""
...VVVVvvvv...
.VVVVvvvvvvvv.
VVVvvvvvvvvvvv
VVVVVVVVVVVVVV
vvvvvvvvvvvvvv""", left="""
....VVVVVV.....
..VVVVVVVVVv...
.VVvvvvvvvvvv..
.VVVVVVVVVVVVV.
.vvvvvvvvvvvvvv""")
headwear("body-a", "scrub-cap", down="""
...SSSSssss...
.SSSSssssssss.
SSSsssssssssss
SSssssssssssss
s............s""", up="""
...SSSSssss...
.SSSSssssssss.
SSSsssssssssss
Ssssssssssssss
ssssssssssssss
ssssssssssssss
......ss......""", left="""
....SSSSSS.....
..SSSSSSSSSs...
.SSssssssssss..
.sssssssssssss.
.s...ssssssssss
.........ssssss
............ss.""")

headwear("body-b", "brimmed-hat", down="""
...MMKKKKK...
..MMKKKKKKK..
.MMKKKKKKKKK.
.KKKKKKKKKKKK
MMMKKKKKKKKKK
KKKKKKKKKKKKK
..KKKKKKKKK..""", up="""
...MMKKKKK...
..MMKKKKKKK..
.MMKKKKKKKKK.
.KKKKKKKKKKKK
MMMKKKKKKKKKK
KKKKKKKKKKKKK""", left="""
....MMMMMM....
...MMMKKKK....
..MKKKKKKKK...
..KKKKKKKKKK..
MMMKKKKKKKKKKK
KKKKKKKKKKKKKK
.KKK..........""")
headwear("body-b", "eyeshade", down="""
.............
.............
.GGGGGGGGGGG.
GGGGGGGGGGGGG
TTTTTTTTTTTTT""", up="""
.............
.............
.GGGGGGGGGGG.
.GGGGGGGGGGGG""", left="""
..............
..............
..GGGGGGGGGG..
.GGGGGGGGGGGG.
TTTT..........""")
headwear("body-b", "ball-cap", down="""
...RRRrrrr...
.RRRRrrrrrrr.
RRRrrrrrrrrrr
RRrrrrrrrrrrr
rrrrrrrrrrrrr""", up="""
...RRRrrrr...
.RRRRrrrrrrr.
RRRrrrrrrrrrr
Rrrrrrrrrrrrr
rrrrrrrrrrrrr""", left="""
....RRRRRR....
..RRRRRRRRr...
.RRrrrrrrrrr..
.rrrrrrrrrrrr.
rrrr..........""")
headwear("body-b", "watch-cap", down="""
...VVVvvvv...
.VVVVvvvvvvv.
VVVvvvvvvvvvv
VVVVVVVVVVVVV
vvvvvvvvvvvvv""", up="""
...VVVvvvv...
.VVVVvvvvvvv.
VVVvvvvvvvvvv
VVVVVVVVVVVVV
vvvvvvvvvvvvv""", left="""
....VVVVVV....
..VVVVVVVVv...
.VVvvvvvvvvv..
.VVVVVVVVVVVV.
.vvvvvvvvvvvvv""")
headwear("body-b", "scrub-cap", down="""
...SSSssss...
.SSSSsssssss.
SSSssssssssss
SSsssssssssss
s...........s""", up="""
...SSSssss...
.SSSSsssssss.
SSSssssssssss
Sssssssssssss
sssssssssssss
sssssssssssss
.....ss......""", left="""
....SSSSSS....
..SSSSSSSSs...
.SSsssssssss..
.ssssssssssss.
.s...sssssssss
.........sssss
...........ss.""")

# Every grid is typed at its head's width, so the rig can mirror `left` into
# `right` pixel for pixel and nothing hangs off the head's box.
WIDTHS = {("body-a", "down"): 14, ("body-a", "up"): 14, ("body-a", "left"): 15,
          ("body-b", "down"): 13, ("body-b", "up"): 13, ("body-b", "left"): 14}
for (build, _name, view), rows in list(HAIR.items()) + list(COVERINGS.items()) + list(HEADWEAR.items()):
    assert len(rows[0]) == WIDTHS[(build, view)], (build, _name, view, len(rows[0]))


def mirror(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def write_layer(build: str, name: str, views: dict[str, list[str]], legend: dict[str, str], note: str) -> None:
    folder = ROOT / "art/src/rig" / build / "layers" / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.txt"):
        old.unlink()
    (folder / "layer.json").write_text(json.dumps({"z": "top", "all_directions": True}, indent=2) + "\n", encoding="utf-8")
    views = dict(views)
    views["right"] = mirror(views["left"])
    for view in ("down", "up", "left", "right"):
        rows = views[view]
        used = sorted({c for row in rows for c in row} - {"."})
        text = [f"# {build} {name}, {view}; {note}",
                f"size: {len(rows[0])}x{len(rows)}", "palette: game", "frames: 1", "pivot: 0,0",
                "legend:", "  . = transparent"] + [f"  {c} = {legend[c]}" for c in used] + ["grid:"] + rows
        (folder / f"head.{view}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")


HEADS = {"body-a": "a", "body-b": "b"}


def _head_rows(build: str, view: str) -> list[str]:
    text = (ROOT / "art/src/rig/face-kit/heads" / f"{HEADS[build]}-round-{view}.txt").read_text(encoding="utf-8")
    return text.split("grid:\n", 1)[1].split()


def hairline(build: str, style: str, view: str) -> list[str]:
    """The ink-4 hairline (character_design.md section 3): the hair's own pixels that
    touch the bare face take ink-4. No new pixel is drawn; it recolours the edge of the
    hand-typed hair where it meets skin, for the hair and skin pairs that need it."""
    hair_rows, head = HAIR[(build, style, view)], _head_rows(build, view)
    if view != "down":
        # Front only: from behind it reads as a band across the nape, and in profile as
        # cracks around the ear. The face, where contrast matters, faces the camera.
        return ["." * len(row) for row in hair_rows]
    out = []
    for y, row in enumerate(hair_rows):
        line = ""
        for x, c in enumerate(row):
            touches = False
            if c in "DH":
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= ny < len(head) and 0 <= nx < len(head[0]) and head[ny][nx] != ".":
                        covered = ny < len(hair_rows) and nx < len(row) and hair_rows[ny][nx] != "."
                        touches = touches or not covered
            line += "L" if touches else "."
        out.append(line)
    return out


def main() -> None:
    styles = sorted({(b, s) for b, s, _ in HAIR})
    for build, style in styles:
        views = {v: HAIR[(build, style, v)] for v in ("down", "up", "left")}
        write_layer(build, f"hair-{style}", views, HAIR_LEGEND, "hand-typed hair (hair_kit.py).")
    for build, style in styles:
        views = {v: hairline(build, style, v) for v in ("down", "up", "left")}
        write_layer(build, f"hairline-{style}", views, {"L": "ink-4"}, "ink-4 hairline derived from the hand-typed hair (hair_kit.py).")
    coverings = sorted({(b, s) for b, s, _ in COVERINGS})
    for build, style in coverings:
        views = {v: COVERINGS[(build, style, v)] for v in ("down", "up", "left")}
        write_layer(build, f"hair-{style}", views, COVERING_LEGENDS[style], "hand-typed covering (hair_kit.py).")
    pieces = sorted({(b, p) for b, p, _ in HEADWEAR})
    for build, piece in pieces:
        views = {v: HEADWEAR[(build, piece, v)] for v in ("down", "up", "left")}
        write_layer(build, f"headwear-{piece}", views, HEADWEAR_LEGEND, "hand-typed headwear (hair_kit.py).")
    print(len(styles), "hair layers,", len(coverings), "covering layers,", len(pieces), "headwear layers")


if __name__ == "__main__":
    main()
