"""Turn raw Blender renders and project screenshots into web-ready assets.

    python tools/optimize_images.py

Inputs
  blender/renders/{hero,workspace,contact}.png   (from blender/scripts/*.py)
  assets/src/projects/*.png                      (full-page screenshots, 16:10 crops)
Outputs
  blender/renders/*.webp      high-quality masters kept in the repo
  assets/img/*.webp           responsive variants referenced by index.html
  assets/img/og-image.jpg     1200x630 social preview

Requires Pillow (pip install pillow).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RENDERS = ROOT / "blender" / "renders"
SHOTS = ROOT / "assets" / "src" / "projects"
OUT = ROOT / "assets" / "img"
BG = (8, 8, 8)  # --color-bg


def trim_alpha(img, pad_ratio=0.04):
    """Crop transparent margins, keeping a small breathing room."""
    bbox = img.getchannel("A").point(lambda a: 255 if a > 6 else 0).getbbox()
    if not bbox:
        return img
    pad = int(max(img.size) * pad_ratio)
    left, top, right, bottom = bbox
    return img.crop((max(left - pad, 0), max(top - pad, 0),
                     min(right + pad, img.width), min(bottom + pad, img.height)))


def flatten(img):
    base = Image.new("RGBA", img.size, BG + (255,))
    base.alpha_composite(img.convert("RGBA"))
    return base.convert("RGB")


def save_variants(img, stem, widths, quality, keep_alpha):
    results = []
    for width in widths:
        if width > img.width:
            continue
        height = round(img.height * width / img.width)
        resized = img.resize((width, height), Image.LANCZOS)
        if not keep_alpha:
            resized = resized.convert("RGB")
        path = OUT / f"{stem}-{width}.webp"
        resized.save(path, "WEBP", quality=quality, method=6, alpha_quality=90)
        results.append((path, resized.size))
    return results


def report(results):
    for path, (w, h) in results:
        print(f"  {path.relative_to(ROOT)}  {w}x{h}  {path.stat().st_size / 1024:.0f} KB")


def process_renders():
    specs = {
        # stem: (widths, quality, keep_alpha, trim)
        "hero": ((1500, 1100, 720), 82, True, True),
        "workspace": ((1920, 1280, 768), 76, False, False),
        "contact": ((1600, 1100, 720), 80, True, True),
    }
    for stem, (widths, quality, keep_alpha, trim) in specs.items():
        src = RENDERS / f"{stem}.png"
        if not src.exists():
            print(f"skip {stem}: {src} missing (run blender/scripts/{stem}.py)")
            continue
        img = Image.open(src).convert("RGBA")
        if trim:
            img = trim_alpha(img)
        img = img if keep_alpha else flatten(img)
        img.save(RENDERS / f"{stem}.webp", "WEBP", quality=90, method=6)
        print(f"{stem}: master {img.size}")
        report(save_variants(img, stem, widths, quality, keep_alpha))


def process_screenshots():
    if not SHOTS.exists():
        return
    for src in sorted(SHOTS.glob("*.png")):
        img = Image.open(src).convert("RGB")
        # Normalise every capture to a 16:10 frame from the top of the page.
        target_h = round(img.width * 10 / 16)
        img = img.crop((0, 0, img.width, min(target_h, img.height)))
        print(f"{src.stem}: {img.size}")
        report(save_variants(img, src.stem, (1200, 720), 78, False))


def build_og_image():
    hero = RENDERS / "hero.png"
    if not hero.exists():
        return
    canvas = Image.new("RGB", (1200, 630), BG)
    art = trim_alpha(Image.open(hero).convert("RGBA"))
    art.thumbnail((620, 600), Image.LANCZOS)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.alpha_composite(art, (1200 - art.width - 40, (630 - art.height) // 2))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")

    draw = ImageDraw.Draw(canvas)
    fonts = Path("C:/Windows/Fonts")
    try:
        title = ImageFont.truetype(str(fonts / "segoeuisb.ttf"), 64)
        sub = ImageFont.truetype(str(fonts / "segoeui.ttf"), 30)
    except OSError:
        title = sub = ImageFont.load_default()
    draw.text((72, 236), "Santiago Sanabria", font=title, fill=(245, 245, 245))
    draw.text((72, 322), "Full Stack Developer", font=sub, fill=(161, 161, 170))
    draw.rectangle((72, 386, 132, 389), fill=(234, 92, 37))
    path = OUT / "og-image.jpg"
    canvas.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    print(f"og-image: {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    process_renders()
    process_screenshots()
    build_og_image()
