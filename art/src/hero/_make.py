# Hero: a short single-fan GTX 750-style card (no brand marks), its label redacted.
# Primitives below place pixels; the result is re-rendered and looked at before shipping.
W, H = 72, 44
g = [["." for _ in range(W)] for _ in range(H)]
def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < W and 0 <= y < H: g[y][x] = c
def box(x0, y0, x1, y1, fill, line="k"):
    rect(x0, y0, x1, y1, line); rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)

# bracket (left, steel) with vents
box(1, 4, 7, 40, "G")
rect(2, 5, 2, 39, "w")                       # top-left light
for y in range(8, 30, 3): rect(4, y, 5, y + 1, "k")
rect(3, 34, 6, 36, "g")
# PCB peeks below the shroud
box(7, 30, 62, 36, "a")
# PCIe fingers
for x in range(14, 58, 2): rect(x, 37, x, 39, "G")
rect(13, 37, 58, 37, "k"); rect(36, 37, 37, 39, ".")   # key notch
rect(13, 40, 58, 40, "k")
for x in range(15, 58, 2): g[38][x] = "k"; g[39][x] = "k"
# shroud
box(7, 6, 64, 31, "b")
rect(8, 7, 63, 7, "g")                         # top highlight
rect(8, 30, 63, 30, "a")                       # underside shade
for x in range(10, 62, 4): g[28][x] = "a"      # grille dots
# fan (circle) on the right half
cx, cy, r = 44, 18, 10
for y in range(H):
    for x in range(W):
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d <= r + 0.5:
            g[y][x] = "k" if d > r - 0.6 else ("a" if d > 3.6 else "g")
# blades: five dark arcs
import math
for i in range(5):
    for t in range(4, r - 1):
        a = i * 2 * math.pi / 5 + t * 0.12
        x, y = round(cx + t * math.cos(a)), round(cy + t * math.sin(a))
        g[y][x] = "G"
rect(cx - 1, cy - 1, cx + 1, cy + 1, "k"); g[cy][cx] = "o"   # hub with an orange cap
# label sticker, redacted
box(11, 11, 29, 21, "w")
rect(13, 13, 27, 14, "k")                      # redaction bar 1 (the name)
rect(13, 17, 22, 18, "k")                      # redaction bar 2 (the model)
rect(24, 17, 27, 18, "o")                      # one bar in the action colour
# shadow under the card
rect(9, 41, 64, 42, "S")

legend = {"k": "ink", "a": "ink-2", "b": "grey-1", "g": "grey-2", "G": "grey-3", "w": "paper", "o": "act-2", "S": "paper-2"}
import pathlib
p = pathlib.Path(__file__).parent / "gtx-hero.txt"
p.write_text(f"size: {W}x{H}\npalette: site\nframes: 1\ncategory: ui\nlegend:\n" + "".join(f"  {k} = {v}\n" for k, v in legend.items())
             + "frame 1:\n" + "\n".join("".join(r) for r in g) + "\n")
