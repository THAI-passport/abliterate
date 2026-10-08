#!/usr/bin/env python3
"""
Generate the Open Graph preview image (1200x630 PNG) for abliterate.app.
- Background: --paper (#f4f2ec)
- Palette: art/palette/site.json
- Logo mark (integer scaled from art/src/logo/mark-32.txt / public/img/mark-32.png)
- "Models that say yes." in Silkscreen
- GTX card (integer scaled from art/src/hero/gtx-hero.txt / public/img/gtx-hero.png)
- Notched frame with hard offset shadow
- Output in public/og/default.png (< 150 KB)
"""

import json
import io
import pathlib
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

# 1. Load palette
with open(REPO_ROOT / "art/palette/site.json") as f:
    pal_data = json.load(f)
PAL = {c["name"]: c["hex"] for c in pal_data["colors"]}

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

C_PAPER = hex_to_rgb(PAL["paper"])       # (244, 242, 236)
C_PAPER2 = hex_to_rgb(PAL["paper-2"])    # (233, 230, 220)
C_INK = hex_to_rgb(PAL["ink"])           # (17, 17, 17)
C_INK2 = hex_to_rgb(PAL["ink-2"])        # (43, 42, 40)
C_GREY1 = hex_to_rgb(PAL["grey-1"])      # (74, 72, 67)
C_GREY2 = hex_to_rgb(PAL["grey-2"])      # (138, 134, 124)
C_ACT2 = hex_to_rgb(PAL["act-2"])        # (255, 74, 28)
C_ACT1 = hex_to_rgb(PAL["act-1"])        # (184, 48, 15)

# 2. Load fonts
def load_woff2_font(rel_path, size):
    font_path = REPO_ROOT / rel_path
    tt = TTFont(str(font_path))
    tt.flavor = None
    buf = io.BytesIO()
    tt.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)

font_silk_title = load_woff2_font("public/fonts/silkscreen-400.woff2", 52)
font_silk_brand = load_woff2_font("public/fonts/silkscreen-700.woff2", 28)
font_silk_sub   = load_woff2_font("public/fonts/silkscreen-400.woff2", 20)
font_silk_cap   = load_woff2_font("public/fonts/silkscreen-400.woff2", 15)
font_vt_tag     = load_woff2_font("public/fonts/vt323.woff2", 24)

# 3. Canvas setup
W, H = 1200, 630
img = Image.new("RGBA", (W, H), C_PAPER)
draw = ImageDraw.Draw(img)

def draw_notched_box(draw, x0, y0, x1, y1, fill, border=C_INK, border_w=4, notch=8, shadow=C_INK, shadow_offset=(8, 8)):
    sx, sy = shadow_offset
    if sx or sy:
        # Shadow polygon with notched corners
        spoly = [
            (x0 + sx + notch, y0 + sy),
            (x1 + sx - notch, y0 + sy),
            (x1 + sx, y0 + sy + notch),
            (x1 + sx, y1 + sy - notch),
            (x1 + sx - notch, y1 + sy),
            (x0 + sx + notch, y1 + sy),
            (x0 + sx, y1 + sy - notch),
            (x0 + sx, y0 + sy + notch),
        ]
        draw.polygon(spoly, fill=shadow)

    # Box body with notched corners
    bpoly = [
        (x0 + notch, y0),
        (x1 - notch, y0),
        (x1, y0 + notch),
        (x1, y1 - notch),
        (x1 - notch, y1),
        (x0 + notch, y1),
        (x0, y1 - notch),
        (x0, y0 + notch),
    ]
    draw.polygon(bpoly, fill=fill)

    # Border lines
    # Top, Right, Bottom, Left
    draw.line([(x0 + notch, y0 + border_w // 2), (x1 - notch, y0 + border_w // 2)], fill=border, width=border_w)
    draw.line([(x1 - border_w // 2, y0 + notch), (x1 - border_w // 2, y1 - notch)], fill=border, width=border_w)
    draw.line([(x1 - notch, y1 - border_w // 2), (x0 + notch, y1 - border_w // 2)], fill=border, width=border_w)
    draw.line([(x0 + border_w // 2, y1 - notch), (x0 + border_w // 2, y0 + notch)], fill=border, width=border_w)
    # 4 diagonal corner cuts
    draw.line([(x0 + notch, y0), (x0, y0 + notch)], fill=border, width=border_w)
    draw.line([(x1 - notch, y0), (x1, y0 + notch)], fill=border, width=border_w)
    draw.line([(x1, y1 - notch), (x1 - notch, y1)], fill=border, width=border_w)
    draw.line([(x0, y1 - notch), (x0 + notch, y1)], fill=border, width=border_w)

# Outer notched frame
OUTER_MARGIN = 40
draw_notched_box(
    draw,
    OUTER_MARGIN,
    OUTER_MARGIN,
    W - OUTER_MARGIN - 8,
    H - OUTER_MARGIN - 8,
    fill=C_PAPER,
    border=C_INK,
    border_w=4,
    notch=12,
    shadow=C_INK,
    shadow_offset=(8, 8)
)

# Header: Logo mark (scaled 2x = 64x64) + brand text "abliterate"
mark_img = Image.open(REPO_ROOT / "public/img/mark-32.png").convert("RGBA")
mark_64 = mark_img.resize((64, 64), Image.Resampling.NEAREST)

# Outline around mark
mark_x, mark_y = 80, 80
draw.rectangle([mark_x - 4, mark_y - 4, mark_x + 64 + 3, mark_y + 64 + 3], fill=C_INK)
img.paste(mark_64, (mark_x, mark_y), mark_64)

# Brand wordmark "abliterate"
draw.text((mark_x + 80, mark_y + 16), "abliterate", fill=C_INK, font=font_silk_brand)

# Subtle action tag in header
tag_text = "API STOREFRONT"
tag_box_x = 440
draw.text((tag_box_x, mark_y + 20), tag_text, fill=C_ACT2, font=font_silk_sub)

# Horizontal separator rule
draw.line([(70, 168), (W - 80, 168)], fill=C_PAPER2, width=3)
draw.line([(70, 171), (W - 80, 171)], fill=C_INK, width=2)

# Left Column: Headline and subcopy
head_x, head_y = 80, 215
draw.text((head_x, head_y), "Models that", fill=C_INK, font=font_silk_title)
draw.text((head_x, head_y + 68), "say yes.", fill=C_ACT2, font=font_silk_title)

# Tagline and definition
sub_y = head_y + 155
draw.text((head_x, sub_y), "OpenAI-compatible API for abliterated models.", fill=C_INK, font=font_silk_sub)
draw.text((head_x, sub_y + 36), "Uncensored open weights. Pay per token or subscribe.", fill=C_GREY1, font=font_silk_sub)

# Badges at bottom of left column
badges = [
    ("NO-LOGGING PLEDGE", C_PAPER2, C_INK),
    ("CREDITS FROM $10", C_PAPER2, C_INK),
    ("OPENAI FORMAT", C_PAPER2, C_INK),
]
bx = head_x
by = sub_y + 92
for btext, bbg, bfg in badges:
    bw = len(btext) * 11 + 24
    draw_notched_box(draw, bx, by, bx + bw, by + 34, fill=bbg, border=C_INK, border_w=2, notch=4, shadow_offset=(0, 0))
    draw.text((bx + 12, by + 4), btext, fill=bfg, font=font_vt_tag)
    bx += bw + 16

# Right Column: Notched Art Box containing the GTX 750 hero card
art_box_w, art_box_h = 420, 310
art_box_x = W - 80 - art_box_w
art_box_y = 195

draw_notched_box(
    draw,
    art_box_x,
    art_box_y,
    art_box_x + art_box_w,
    art_box_y + art_box_h,
    fill=C_PAPER2,
    border=C_INK,
    border_w=4,
    notch=8,
    shadow=C_INK,
    shadow_offset=(6, 6)
)

# GTX Hero Card: 72x44 scaled 4x = 288x176
gtx_img = Image.open(REPO_ROOT / "public/img/gtx-hero.png").convert("RGBA")
gtx_scaled = gtx_img.resize((72 * 4, 44 * 4), Image.Resampling.NEAREST)

gtx_x = art_box_x + (art_box_w - 288) // 2
gtx_y = art_box_y + (art_box_h - 176) // 2 - 18
img.paste(gtx_scaled, (gtx_x, gtx_y), gtx_scaled)

# Redaction bar under the card / caption box
cap_text = "The dev's GTX 750. Label redacted."
cap_bbox = font_silk_cap.getbbox(cap_text)
cap_w = cap_bbox[2] - cap_bbox[0]
draw.text((art_box_x + (art_box_w - cap_w) // 2, art_box_y + art_box_h - 40), cap_text, fill=C_INK2, font=font_silk_cap)

# Save to public/og/default.png (convert to RGB / optimize)
out_path = REPO_ROOT / "public/og/default.png"
# Save as optimized PNG
rgb_img = img.convert("RGB")
rgb_img.save(out_path, format="PNG", optimize=True)

size_kb = out_path.stat().st_size / 1024
print(f"Generated {out_path} ({size_kb:.1f} KB)")
assert size_kb < 150, f"Image size {size_kb} KB exceeds 150 KB limit!"
