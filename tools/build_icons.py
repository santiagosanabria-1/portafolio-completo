"""Rasterise the favicon mark (assets/icons/favicon.svg) to PNG fallbacks.

    python tools/build_icons.py

The geometry mirrors favicon.svg (32-unit grid) so both stay in sync.
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "icons"
BARS = [((7, 8, 25, 11), "#f5f5f5"), ((7, 14.5, 19, 17.5), "#f5f5f5"), ((7, 21, 13, 24), "#ea5c25")]


def draw(size, radius_units=7):
    scale = size / 32
    supersample = 4
    big = size * supersample
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = scale * supersample
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius_units * s, fill="#111111")
    for (x0, y0, x1, y1), color in BARS:
        d.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), radius=1.5 * s, fill=color)
    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    draw(32).save(OUT / "favicon-32.png", optimize=True)
    # iOS applies its own mask, so the touch icon is a full-bleed square.
    draw(180, radius_units=0).save(OUT / "apple-touch-icon.png", optimize=True)
    for f in sorted(OUT.glob("*.png")):
        print(f.name, f.stat().st_size, "bytes")
