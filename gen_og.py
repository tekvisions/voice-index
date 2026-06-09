#!/usr/bin/env python3
"""Render og.png (1200x630) for The Voice AI Index — "on-air / booth" card.
Near-black booth, electric-lime level-meter + ON-AIR badge, heavy broadcast title.
Pillow only; graceful fallback if unavailable."""
from __future__ import annotations

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIME = (182, 255, 46)
BG = (10, 11, 13)
INK = (238, 241, 243)
MUTED = (154, 160, 168)


def _font(paths, size):
    from PIL import ImageFont
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        print("Pillow not available — skipping og.png")
        return 0
    try:
        data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
        count, cats = data.get("count", 0), len(data.get("categories", []))
    except Exception:
        count, cats = 0, 0

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # faint tape scanlines
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(15, 16, 19))

    title_fonts = ["/System/Library/Fonts/Supplemental/Impact.ttf",
                   "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    mono = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    f_h1 = _font(title_fonts, 96)
    f_kick = _font(mono, 24)
    f_badge = _font(mono, 22)
    f_stat = _font(mono, 27)

    # ON AIR badge + wordmark equalizer
    bx, by = 70, 72
    for i, h in enumerate([14, 30, 20, 26]):
        d.rounded_rectangle([bx + i * 9, by + (30 - h), bx + i * 9 + 5, by + 30], radius=2, fill=LIME)
    d.rounded_rectangle([bx + 50, by + 2, bx + 158, by + 30], radius=5, outline=LIME, width=2)
    d.text((bx + 62, by + 7), "● ON AIR", font=f_badge, fill=LIME)
    d.text((bx + 178, by + 6), "THE VOICE AI INDEX", font=f_kick, fill=MUTED)

    # heavy broadcast title
    d.text((66, 170), "THE VOICE & SPEECH", font=f_h1, fill=INK)
    d.text((66, 270), "STACK, ", font=f_h1, fill=INK)
    # measure "STACK, " to place lime "ON AIR."
    try:
        w_stack = d.textlength("STACK, ", font=f_h1)
    except Exception:
        w_stack = 360
    d.text((66 + w_stack, 270), "ON AIR.", font=f_h1, fill=LIME)

    # lime level-meter strip
    mx, my, mh = 70, 452, 56
    for i in range(64):
        h = 10 + int((mh - 10) * abs(math.sin(i * 0.7) * 0.6 + math.sin(i * 0.23) * 0.4))
        d.rounded_rectangle([mx + i * 16, my + (mh - h), mx + i * 16 + 7, my + mh], radius=2, fill=LIME)

    d.text((70, 540), f"{count} tools  ·  {cats} categories  ·  ranked daily by GitHub momentum",
           font=f_stat, fill=MUTED)

    img.save(os.path.join(HERE, "og.png"))
    print(f"wrote og.png ({count} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
