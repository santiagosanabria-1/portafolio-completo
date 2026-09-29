"""Contact asset — BUILD → SHIP → CONNECT, without words.

Left: a solid glass-and-graphite monolith (build). It breaks into a stream of
small modules drifting right (ship), which progressively align into a thin
line that ends in a single glowing orange node (connect). Very minimal,
transparent film, wide aspect for the closing section.

Run:  blender -b --factory-startup --python blender/scripts/contact.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c  # noqa: E402

PREVIEW = os.environ.get("PREVIEW") == "1"

c.reset_scene(seed=77)

graphite = c.mat_graphite()
steel = c.mat_steel()
glass = c.mat_glass()
frosted = c.mat_glass("Frosted", roughness=0.18, tint=(0.86, 0.88, 0.93, 1))
orange = c.mat_emission("Orange", c.ORANGE, 5.0)
orange_soft = c.mat_emission("OrangeSoft", c.ORANGE, 2.0)
blue = c.mat_emission("Blue", c.BLUE, 4.0)

# BUILD — the monolith: graphite core wrapped in a glass shell, cut in modules.
cell = 0.34
gap = 0.035
cols, depth, rows = 3, 3, 6
for ix in range(cols):
    for iy in range(depth):
        for iz in range(rows):
            # The right face progressively erodes towards the top: pieces leave.
            if ix == cols - 1 and iz >= rows - 1 - iy * 2:
                continue
            mat = glass if (ix + iy + iz) % 3 == 0 else graphite
            loc = (-3.2 + ix * (cell + gap), (iy - 1) * (cell + gap), iz * (cell + gap) + cell / 2)
            c.rounded_box("Block", (cell, cell, cell), loc, mat, bevel=0.035)

# SHIP — the modules stream out, shrinking and aligning as they travel.
count = 30
for i in range(count):
    t = i / (count - 1)                       # 0 near the monolith, 1 near the node
    x = -2.1 + t * 5.0
    spread = (1 - t) ** 1.6
    y = c.jitter(0.9) * spread
    z = 1.45 + math.sin(t * math.pi) * 0.35 * (1 - t) + c.jitter(0.8) * spread
    s = cell * (1 - 0.72 * t) * random.uniform(0.8, 1.05)
    rot = (c.deg(c.jitter(55) * spread), c.deg(c.jitter(55) * spread), c.deg(c.jitter(55) * spread))
    mat = glass if random.random() < 0.4 else steel if t > 0.7 else graphite
    c.rounded_box("Shard", (s, s, s), (x, y, z), mat, bevel=s * 0.12, rotation=rot)

# CONNECT — a thin line resolving into one node.
c.rod("Line", (2.2, 0, 1.45), (4.1, 0, 1.45), 0.006, orange_soft)
c.sphere("Node", 0.085, (4.2, 0, 1.45), orange)
c.sphere("NodeHalo", 0.16, (4.2, 0, 1.45), c.mat_glass("Halo", roughness=0.05))
c.sphere("Satellite", 0.03, (4.55, 0.35, 1.8), blue, segments=24)

target = (0.4, 0, 1.2)
c.camera((-2.4, -12.2, 3.9), target, lens=50, fstop=4.0, focus_target=(0.6, 0, 1.4))
c.studio_lighting(target=target, exposure=0.95)
c.dark_world(0.3)

c.configure_cycles((1200, 600) if PREVIEW else (2400, 1200),
                   samples=48 if PREVIEW else 256, transparent=True)
c.save_and_render("contact-preview" if PREVIEW else "contact")
