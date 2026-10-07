#!/usr/bin/env python3
"""Draw the dashboard's fallback pixel font: the characters Silkscreen, Pixelify Sans
and VT323 lack (accented Latin, Cyrillic, typographic punctuation, arrows).

Letters are small caps (5 px tall, 5 wide, advance 6), the way Silkscreen draws them, so
lower case reuses the capital shape. Accents are separate 5-wide marks stacked above the
letter. Everything below is original artwork. Writes the glyph grids to
art/src/fonts/pixel-fallback/, builds the TTF with tools/pixel-core, and converts it
to public/fonts/pixel-fallback.woff2.

    python3 art/build_fallback_font.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "art/src/fonts/pixel-fallback"
BUILD = ROOT / "build/art/fonts"
W, H, BASELINE, TOP = 6, 10, 8, 3  # cell, baseline row, first row of a 5 px letter

LETTERS = {  # five rows of five, then optional descender rows
    "A": [".###.", "#...#", "#####", "#...#", "#...#"],
    "B": ["####.", "#...#", "####.", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "###..", "#....", "#####"],
    "F": ["#####", "#....", "###..", "#....", "#...."],
    "G": [".####", "#....", "#..##", "#...#", ".####"],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "Z": ["#####", "...#.", "..#..", ".#...", "#####"],
    "Đ": ["####.", ".#..#", "###.#", ".#..#", "####."],
    "Ħ": ["#####", "#...#", "#####", "#...#", "#...#"],
    "Ł": ["#....", "##...", "#....", "#....", "#####"],
    "Ŧ": ["#####", "..#..", "#####", "..#..", "..#.."],
    "Œ": [".####", "#.#..", "#.###", "#.#..", ".####"],
    "ı": [".###.", "..#..", "..#..", "..#..", ".###."],
    # Cyrillic shapes that are not Latin ones (А В Е К М Н О Р С Т Х reuse Latin)
    "Б": ["#####", "#....", "####.", "#...#", "####."],
    "Г": ["#####", "#....", "#....", "#....", "#...."],
    "Д": ["..##.", ".#.#.", "#...#", "#...#", "#####", "#...#"],
    "Ж": ["#.#.#", ".###.", "..#..", ".###.", "#.#.#"],
    "З": ["####.", "....#", ".###.", "....#", "####."],
    "И": ["#...#", "#..##", "#.#.#", "##..#", "#...#"],
    "Л": ["..###", ".#..#", "#...#", "#...#", "#...#"],
    "П": ["#####", "#...#", "#...#", "#...#", "#...#"],
    "У": ["#...#", "#...#", ".####", "....#", "####."],
    "Ф": ["..#..", ".###.", "#.#.#", ".###.", "..#.."],
    "Ц": ["#..#.", "#..#.", "#..#.", "#..#.", "#####", "....#"],
    "Ч": ["#...#", "#...#", ".####", "....#", "....#"],
    "Ш": ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    "Щ": ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####", "....#"],
    "Ъ": ["##...", ".#...", ".###.", ".#..#", ".###."],
    "Ы": ["#...#", "#...#", "###.#", "#..##", "###.#"],
    "Ь": ["#....", "#....", "####.", "#...#", "####."],
    "Э": [".###.", "....#", "..###", "....#", ".###."],
    "Ю": ["#.##.", "#.#.#", "###.#", "#.#.#", "#.##."],
    "Я": [".####", "#...#", ".####", "..#.#", "#...#"],
    "Є": [".###.", "#....", "###..", "#....", ".###."],
    "Ґ": ["...#.", "#####", "#....", "#....", "#...."],
}
LETTERS.update({  # Greek shapes that are not Latin or Cyrillic ones (Α Β Ε Ζ Η Ι Κ Μ Ν Ο Ρ Τ Υ Χ reuse Latin)
    "Δ": ["..#..", ".#.#.", "#...#", "#...#", "#####"],
    "Θ": [".###.", "#...#", "#####", "#...#", ".###."],
    "Λ": ["..#..", ".#.#.", "#...#", "#...#", "#...#"],
    "Ξ": ["#####", ".....", ".###.", ".....", "#####"],
    "Σ": ["#####", "#....", ".#...", "#....", "#####"],
    "Ψ": ["#.#.#", "#.#.#", ".###.", "..#..", "..#.."],
    "Ω": [".###.", "#...#", "#...#", ".#.#.", "##.##"],
})
GREEK_SHARED = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
                "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X", "Γ": "Г", "Π": "П", "Φ": "Ф"}
LATIN_FOR_CYR = dict(zip("АВЕКМНОРСТХІ", "ABEKMHOPCTXI"))
LETTERS.update({c: LETTERS[l] for c, l in LATIN_FOR_CYR.items()})
LETTERS.update({c: LETTERS[l] for c, l in GREEK_SHARED.items()})

MARKS = {  # two rows, drawn at rows 0-1 (rows 8-9 for "below"); the ring uses rows 0-2
    "acute": ["...#.", "..#.."], "grave": [".#...", "..#.."],
    "circ": ["..#..", ".#.#."], "caron": [".#.#.", "..#.."],
    "breve": ["#...#", ".###."], "macron": [".###.", "....."],
    "dot": [".....", "..#.."], "diaer": [".....", ".#.#."],
    "ring": ["..#..", ".#.#.", "..#.."], "dacute": ["..#.#", ".#.#."],
    "tilde": [".##.#", "#..#."], "apos": ["....#", "...#."],
    "cedilla": ["..#..", ".##.."], "ogonek": ["...#.", "....#"],
    "comma": ["..#..", ".#..."],
}
BELOW = {"cedilla", "ogonek", "comma"}

# letter + mark for every composed capital; the lower-case code point reuses the grid
ACCENTED = {
    "À": ("A", "grave"), "Á": ("A", "acute"), "Ā": ("A", "macron"), "Ă": ("A", "breve"),
    "Ą": ("A", "ogonek"), "Ć": ("C", "acute"), "Ĉ": ("C", "circ"), "Ċ": ("C", "dot"),
    "Č": ("C", "caron"), "Ď": ("D", "apos"), "Ē": ("E", "macron"), "Ĕ": ("E", "breve"),
    "Ė": ("E", "dot"), "Ę": ("E", "ogonek"), "Ě": ("E", "caron"), "Ĝ": ("G", "circ"),
    "Ğ": ("G", "breve"), "Ġ": ("G", "dot"), "Ģ": ("G", "comma"), "Ĥ": ("H", "circ"),
    "Ĩ": ("I", "tilde"), "Ī": ("I", "macron"), "Ĭ": ("I", "breve"), "Į": ("I", "ogonek"),
    "İ": ("I", "dot"), "Ĵ": ("J", "circ"), "Ķ": ("K", "comma"), "Ĺ": ("L", "acute"),
    "Ļ": ("L", "comma"), "Ľ": ("L", "apos"), "Ń": ("N", "acute"), "Ņ": ("N", "comma"),
    "Ň": ("N", "caron"), "Ō": ("O", "macron"), "Ŏ": ("O", "breve"), "Ő": ("O", "dacute"),
    "Ŕ": ("R", "acute"), "Ŗ": ("R", "comma"), "Ř": ("R", "caron"), "Ś": ("S", "acute"),
    "Ŝ": ("S", "circ"), "Ş": ("S", "cedilla"), "Š": ("S", "caron"), "Ţ": ("T", "cedilla"),
    "Ť": ("T", "apos"), "Ũ": ("U", "tilde"), "Ū": ("U", "macron"), "Ŭ": ("U", "breve"),
    "Ů": ("U", "ring"), "Ű": ("U", "dacute"), "Ų": ("U", "ogonek"), "Ŵ": ("W", "circ"),
    "Ŷ": ("Y", "circ"), "Ÿ": ("Y", "diaer"), "Ź": ("Z", "acute"), "Ż": ("Z", "dot"),
    "Ž": ("Z", "caron"), "Ё": ("Е", "diaer"), "Й": ("И", "breve"), "Ї": ("І", "diaer"),
    "Ç": ("C", "cedilla"),
    "Ά": ("Α", "acute"), "Έ": ("Ε", "acute"), "Ή": ("Η", "acute"), "Ί": ("Ι", "acute"),
    "Ό": ("Ο", "acute"), "Ύ": ("Υ", "acute"), "Ώ": ("Ω", "acute"), "Ϊ": ("Ι", "diaer"),
    "Ϋ": ("Υ", "diaer"),
}
# stand-alone shapes (no lower-case twin): their own code points
SYMBOLS = {
    "‐": [(5, ".###..")], "‑": [(5, ".###..")], "−": [(5, ".###..")],
    "–": [(5, "#####.")], "—": [(5, "######")],
    "‘": [(3, "..#..."), (4, "..##.."), (5, "..##..")],
    "’": [(3, "..##.."), (4, "..##.."), (5, "..#...")],
    "“": [(3, "#..#.."), (4, "##.##."), (5, "##.##.")],
    "”": [(3, "##.##."), (4, "##.##."), (5, "#..#..")],
    "„": [(6, "##.##."), (7, "##.##."), (8, "#..#..")],
    "…": [(7, "#.#.#.")],
    "•": [(5, "..##.."), (6, "..##..")],
    "×": [(4, ".#.#.."), (5, "..#..."), (6, ".#.#..")],
    "‹": [(3, "...#.."), (4, "..#..."), (5, ".#...."), (6, "..#..."), (7, "...#..")],
    "›": [(3, ".#...."), (4, "..#..."), (5, "...#.."), (6, "..#..."), (7, ".#....")],
    "«": [(3, "..#.#."), (4, ".#.#.."), (5, "#.#..."), (6, ".#.#.."), (7, "..#.#.")],
    "»": [(3, "#.#..."), (4, ".#.#.."), (5, "..#.#."), (6, ".#.#.."), (7, "#.#...")],
    "←": [(3, "..#..."), (4, ".#...."), (5, "#####."), (6, ".#...."), (7, "..#...")],
    "→": [(3, "..#..."), (4, "...#.."), (5, "#####."), (6, "...#.."), (7, "..#...")],
    "↑": [(3, "..#..."), (4, ".###.."), (5, "#.#.#."), (6, "..#..."), (7, "..#...")],
    "↓": [(3, "..#..."), (4, "..#..."), (5, "#.#.#."), (6, ".###.."), (7, "..#...")],
    "✓": [(4, "....#."), (5, "#..#.."), (6, ".##..."), (7, "..#...")],
    "✕": [(4, "#...#."), (5, ".#.#.."), (6, "..#..."), (7, ".#.#.."), (8, "#...#.")],
    "€": [(3, "..###."), (4, ".#...."), (5, "####.."), (6, ".#...."), (7, "..###.")],
    "№": [(3, "#.#..."), (4, "##..#."), (5, "#.#.#."), (6, "#..##."), (7, "#...#.")],
}


def mark_rows(name, rows):
    """Rows (index -> 5-char string) a mark occupies."""
    if name in BELOW:
        return dict(zip((8, 9), rows))
    return dict(zip((0, 1, 2), rows))


def glyph(rows):
    grid = [[0] * W for _ in range(H)]
    for y, text in rows.items():
        for x, c in enumerate(text):
            if c == "#":
                grid[y][x] = 1
    return ["".join("k" if v else "." for v in row) for row in grid]


def letter_rows(letter):
    shape = LETTERS[letter]
    return {TOP + i: r for i, r in enumerate(shape)}


def write(cp, rows, label):
    name = f"u{cp:04x}.txt"
    body = "\n".join(glyph(rows))
    (SRC / name).write_text(
        f"size: {W}x{H}\npalette: dashboard\nframes: 1\ncategory: glyph\ncodepoint: U+{cp:04X}\n"
        f"baseline: {BASELINE}\nadvance: {W}\n# {label}\nlegend:\n  k = cream-3\nframe 1:\n{body}\n",
        encoding="utf-8")


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    for old in SRC.glob("*.txt"):
        old.unlink()
    count = 0

    def both(upper, rows):
        nonlocal count
        lower = upper.lower()
        write(ord(upper), rows, upper)
        count += 1
        if len(lower) == 1 and lower != upper:
            write(ord(lower), rows, lower)
            count += 1

    for ch in LETTERS:
        if ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or ch == "ı":
            continue  # plain Latin letters are only bases; the fonts have them
        if ch == "ı":
            continue
        both(ch, letter_rows(ch))
    write(ord("ı"), letter_rows("I"), "dotless i")
    count += 1
    for ch, (base, mark) in ACCENTED.items():
        rows = letter_rows(base)
        for y, text in mark_rows(mark, MARKS[mark]).items():
            rows[y] = rows.get(y, ".....")
            rows[y] = "".join("#" if "#" in (a, b) else "." for a, b in zip(rows[y], text))
        both(ch, rows)
    write(0x3C2, letter_rows("Σ"), "final sigma")
    count += 1
    for cp, rows in SYMBOLS.items():
        write(ord(cp), dict(rows), f"symbol {cp}")
        count += 1
    print(f"{count} glyphs written to {SRC}")
    tool = ROOT / "tools/pixel-core/pixel_tool.py"
    subprocess.run([sys.executable, str(tool), "build-font", str(SRC), "--palette",
                    str(ROOT / "art/palette/dashboard.json"), "--out-dir", str(BUILD),
                    "--name", "Streambot Fallback"], check=True)
    from fontTools.ttLib import TTFont
    font = TTFont(BUILD / "pixel-fallback.ttf")
    font.flavor = "woff2"
    font["head"].unitsPerEm = 714  # 5 px caps (500 units) = 0.7 em, the cap height Silkscreen and Pixelify draw
    font.save(ROOT / "public/fonts/pixel-fallback.woff2")


if __name__ == "__main__":
    main()
