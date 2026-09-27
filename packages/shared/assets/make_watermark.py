#!/usr/bin/env python3
"""Regenerate watermark.png (free-plan overlay): white wordmark with a soft shadow on a transparent canvas."""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

name = os.environ.get("APP_NAME", "VideoStudio")
W, H = 900, 200
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
font = None
for cand in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    if Path(cand).exists():
        font = ImageFont.truetype(cand, 120); break
font = font or ImageFont.load_default(120)
d = ImageDraw.Draw(im)
bbox = d.textbbox((0, 0), name, font=font)
x, y = (W - (bbox[2] - bbox[0])) // 2 - bbox[0], (H - (bbox[3] - bbox[1])) // 2 - bbox[1]
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).text((x + 4, y + 6), name, font=font, fill=(0, 0, 0, 200))
shadow = shadow.filter(ImageFilter.GaussianBlur(6))
im = Image.alpha_composite(im, shadow)
ImageDraw.Draw(im).text((x, y), name, font=font, fill=(255, 255, 255, 255))
out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("watermark.png"))
im.save(out, "PNG", optimize=True)
print("wrote", out, im.size)
