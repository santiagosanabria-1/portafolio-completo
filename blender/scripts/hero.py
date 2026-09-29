"""Hero asset — CODE → SYSTEM → PRODUCT.

An exploded, three-layer stack seen in 3/4:
  * bottom  (CODE)    graphite plate with bars that read as lines of code
  * middle  (SYSTEM)  clear glass plate carrying a node graph and service modules
  * top     (PRODUCT) frosted glass slab in a graphite tray, one orange signal line
Loose pieces lift off the code layer towards the system layer, suggesting the
transformation. Rendered with a transparent film so the object floats on the page.

Run:  blender -b --factory-startup --python blender/scripts/hero.py
      (set PREVIEW=1 for a fast low-sample draft)
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c  # noqa: E402

PREVIEW = os.environ.get("PREVIEW") == "1"

c.reset_scene(seed=2026)

graphite = c.mat_graphite()
graphite_soft = c.mat_graphite("GraphiteSoft", roughness=0.5)
steel = c.mat_steel()
satin = c.mat_satin()
glass = c.mat_glass()
frosted = c.mat_glass("Frosted", roughness=0.22, tint=(0.86, 0.88, 0.93, 1))
orange = c.mat_emission("Orange", c.ORANGE, 6.0)
orange_soft = c.mat_emission("OrangeSoft", c.ORANGE, 1.6)
blue = c.mat_emission("Blue", c.BLUE, 5.0)

W, D = 3.2, 2.2          # plate footprint
Z_CODE, Z_SYS, Z_PROD = 0.0, 1.4, 2.8

# ---------------------------------------------------------------- CODE layer
c.rounded_box("CodePlate", (W, D, 0.1), (0, 0, Z_CODE), graphite, bevel=0.05)

row_y = -0.86
bar_h, bar_d = 0.035, 0.065
lifted = []
while row_y <= 0.87:
    x = -1.38 + random.choice([0, 0, 0.18, 0.36])      # indentation, like real code
    for _ in range(random.randint(1, 3)):
        length = random.uniform(0.18, 0.85)
        if x + length > 1.38:
            break
        roll = random.random()
        mat = orange_soft if roll < 0.06 else steel if roll < 0.2 else satin
        center = (x + length / 2, row_y, Z_CODE + 0.05 + bar_h / 2)
        bar = c.rounded_box("CodeBar", (length, bar_d, bar_h), center, mat, bevel=0.012, segments=3)
        if x + length > 0.75 and random.random() < 0.35:
            lifted.append(bar)
        x += length + random.uniform(0.07, 0.12)
    row_y += 0.155

# A few bars detach and drift up — code becoming a system.
for i, bar in enumerate(lifted[:5]):
    bar.location.z += 0.22 + i * 0.14
    bar.location.x += 0.25 + i * 0.07
    bar.rotation_euler = (c.deg(c.jitter(8)), c.deg(c.jitter(10)), c.deg(c.jitter(14)))

# -------------------------------------------------------------- SYSTEM layer
c.rounded_box("SystemPlate", (W, D, 0.055), (0, 0, Z_SYS), glass, bevel=0.025)

top = Z_SYS + 0.0275
nodes = {
    "a": (-1.15, -0.55), "b": (-0.35, -0.7), "c": (0.45, -0.35), "d": (1.1, -0.65),
    "e": (-0.9, 0.45), "f": (0.0, 0.25), "g": (0.85, 0.6), "h": (-0.2, 0.8),
}
edges = [("a", "b"), ("b", "c"), ("c", "d"), ("a", "e"), ("e", "f"), ("f", "c"),
         ("f", "g"), ("e", "h"), ("h", "g"), ("b", "f")]
node_r = 0.055
for key, (x, y) in nodes.items():
    mat = orange if key == "c" else blue if key == "e" else steel
    c.sphere(f"Node_{key}", node_r, (x, y, top + node_r), mat)
for a, b in edges:
    (x1, y1), (x2, y2) = nodes[a], nodes[b]
    c.rod(f"Edge_{a}{b}", (x1, y1, top + node_r), (x2, y2, top + node_r), 0.011, steel)

# Service modules sitting on some nodes.
for key, size in (("a", 0.26), ("g", 0.3), ("d", 0.22)):
    x, y = nodes[key]
    c.rounded_box(f"Module_{key}", (size, size, 0.12), (x, y, top + 0.06 + 0.11),
                  graphite_soft, bevel=0.03)

# ------------------------------------------------------------- PRODUCT layer
c.rounded_box("ProductTray", (W + 0.08, D + 0.08, 0.06), (0, 0, Z_PROD - 0.1), graphite, bevel=0.03)
# Soft backlight inside the tray: the frosted slab glows like a display.
screen_glow = c.mat_emission("ScreenGlow", "#8e9ab8", 0.5)
c.rounded_box("ScreenGlow", (W - 0.3, D - 0.3, 0.01), (0, 0, Z_PROD - 0.075), screen_glow, bevel=0.1)
c.rounded_box("ProductSlab", (W, D, 0.16), (0, 0, Z_PROD), frosted, bevel=0.06, segments=6)
slab_top = Z_PROD + 0.08
c.rounded_box("SignalLine", (1.3, 0.022, 0.012), (-0.7, -0.92, slab_top + 0.006), orange,
              bevel=0.005, segments=2)
c.sphere("StatusDot", 0.03, (1.35, -0.92, slab_top + 0.03), blue, segments=24)
# Abstract interface: three restrained bars, no readable content.
for i, (length, mat) in enumerate(((1.6, steel), (1.1, satin), (0.7, satin))):
    c.rounded_box(f"UiBar{i}", (length, 0.05, 0.01),
                  (-1.3 + length / 2, 0.55 - i * 0.16, slab_top + 0.005), mat, bevel=0.01, segments=2)

# ------------------------------------------------------------ structure rods
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * (W / 2 - 0.08), sy * (D / 2 - 0.08)
        c.rod("Pillar", (x, y, Z_CODE + 0.05), (x, y, Z_PROD - 0.13), 0.008, steel)

# Light path: a faint orange filament from the active node to the product.
x, y = nodes["c"]
c.rod("Filament", (x, y, top + node_r * 2), (x, y, Z_PROD - 0.13), 0.004, orange_soft)

# ------------------------------------------------------------ floating pieces
placed = 0
while placed < 14:
    x, y = random.uniform(-2.6, 2.6), random.uniform(-2.0, 2.0)
    if abs(x) < 1.9 and abs(y) < 1.4:
        continue                                        # keep the stack clear
    s = random.uniform(0.07, 0.2)
    z = random.uniform(-0.2, 3.2)
    mat = random.choice([glass, glass, graphite, graphite_soft, steel])
    c.rounded_box("Fragment", (s, s * random.uniform(0.6, 1.4), s), (x, y, z), mat,
                  bevel=s * 0.15, rotation=(c.deg(c.jitter(40)), c.deg(c.jitter(40)), c.deg(c.jitter(40))))
    placed += 1
c.rounded_box("FragmentAccent", (0.12, 0.12, 0.12), (2.05, -1.55, 1.7), orange_soft, bevel=0.02,
              rotation=(c.deg(20), c.deg(35), c.deg(10)))

# --------------------------------------------------------------- camera/light
target = (0, 0, 1.35)
c.camera((8.6, -9.0, 6.9), target, lens=68, fstop=5.6, focus_target=(0.3, -0.3, Z_SYS))
c.studio_lighting(target=target)
c.dark_world()

c.configure_cycles((1000, 900) if PREVIEW else (2200, 1980),
                   samples=48 if PREVIEW else 320, transparent=True)
c.save_and_render("hero-preview" if PREVIEW else "hero")
