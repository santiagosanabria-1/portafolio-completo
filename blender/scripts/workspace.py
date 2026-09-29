"""Projects/Process asset — an abstract digital workspace.

A main display tilted in space, floating glass panels at several depths,
small modules, nodes and connections. Code is represented only as rows of
light bars (no readable text). The cluster sits on the right of the frame so
the left side stays free for section copy. Transparent film: the optimizer
flattens it over the page background colour.

Run:  blender -b --factory-startup --python blender/scripts/workspace.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

PREVIEW = os.environ.get("PREVIEW") == "1"

c.reset_scene(seed=4242)

graphite = c.mat_graphite()
steel = c.mat_steel()
satin = c.mat_satin()
glass = c.mat_glass()
smoked = c.mat_glass("Smoked", roughness=0.08, tint=(0.35, 0.37, 0.42, 1))
code_dim = c.mat_emission("CodeDim", "#6f7da8", 0.75)
code_blue = c.mat_emission("CodeBlue", c.BLUE, 3.0)
code_orange = c.mat_emission("CodeOrange", c.ORANGE, 3.5)
node_orange = c.mat_emission("NodeOrange", c.ORANGE, 8.0)
node_blue = c.mat_emission("NodeBlue", c.BLUE, 7.0)


def to_world(origin, rotation, local):
    return Vector(origin) + Euler(rotation).to_matrix() @ Vector(local)


def panel(name, origin, rotation, size, material, rows=0, row_mats=None, frame=True):
    """A thin rounded panel; optional rows of light bars 'written' on its face."""
    w, h = size
    c.rounded_box(name, (w, 0.04, h), origin, material, bevel=0.03, rotation=rotation)
    if frame:
        c.rounded_box(name + "Frame", (w + 0.06, 0.02, h + 0.06),
                      to_world(origin, rotation, (0, 0.035, 0)), graphite, bevel=0.03, rotation=rotation)
    anchors = []
    if rows:
        top = h / 2 - 0.22
        step = (h - 0.44) / max(rows - 1, 1)
        for r in range(rows):
            x = -w / 2 + 0.2 + random.choice([0, 0, 0.16, 0.32])
            for _ in range(random.randint(1, 3)):
                length = random.uniform(0.12, w * 0.35)
                if x + length > w / 2 - 0.2:
                    break
                roll = random.random()
                mat = (row_mats or {}).get("accent") if roll < 0.07 else \
                    (row_mats or {}).get("hi") if roll < 0.25 else (row_mats or {}).get("base")
                local = (x + length / 2, -0.03, top - r * step)
                c.rounded_box(name + "Row", (length, 0.012, 0.035),
                              to_world(origin, rotation, local), mat, bevel=0.01, segments=2,
                              rotation=rotation)
                x += length + random.uniform(0.06, 0.12)
    for corner in ((-w / 2, h / 2), (w / 2, h / 2), (-w / 2, -h / 2), (w / 2, -h / 2)):
        anchors.append(to_world(origin, rotation, (corner[0], 0, corner[1])))
    return anchors


rows_mats = {"base": code_dim, "hi": code_blue, "accent": code_orange}

# Main display — the anchor of the composition.
main_rot = (c.deg(4), 0, c.deg(-34))
main = panel("Display", (1.2, 0, 1.6), main_rot, (4.2, 2.5), smoked, rows=13, row_mats=rows_mats)

# Floating secondary panels at different depths.
p1 = panel("PanelBack", (3.8, 2.6, 2.9), (c.deg(6), 0, c.deg(-38)), (1.9, 1.2), smoked, rows=6,
           row_mats=rows_mats)
p2 = panel("PanelFront", (3.1, -2.4, 0.35), (c.deg(-8), 0, c.deg(-14)), (1.5, 0.95), glass, rows=4,
           row_mats=rows_mats)
p3 = panel("PanelHigh", (-1.2, 1.4, 3.3), (c.deg(10), 0, c.deg(-8)), (1.3, 0.8), glass, rows=3,
           row_mats=rows_mats)
p4 = panel("PanelLow", (-1.0, -0.9, -0.2), (c.deg(-72), 0, c.deg(-20)), (1.6, 1.0), smoked, rows=0,
           frame=True)

# Nodes and connections between the panels.
node_points = [
    (main[1], node_blue), (p1[2], None), (p2[1], node_orange), (p3[3], None), (main[2], None),
]
spheres = []
for i, (pt, mat) in enumerate(node_points):
    c.sphere(f"Node{i}", 0.06 if mat else 0.04, pt, mat or steel)
    spheres.append(pt)
links = [(0, 1), (0, 2), (3, 4), (4, 2)]
for a, b in links:
    c.rod(f"Link{a}{b}", spheres[a], spheres[b], 0.008, steel)

# A small cluster of modules — services around the display.
for i in range(7):
    s = random.uniform(0.16, 0.34)
    loc = (random.uniform(-0.8, 4.4), random.uniform(-3.0, 3.0), random.uniform(-0.6, 3.8))
    if Vector(loc).to_2d().length < 1.2:
        continue
    mat = random.choice([graphite, graphite, steel, glass])
    c.rounded_box(f"Module{i}", (s, s, s), loc, mat, bevel=s * 0.18,
                  rotation=(c.deg(c.jitter(25)), c.deg(c.jitter(25)), c.deg(c.jitter(25))))
c.rounded_box("ModuleAccent", (0.18, 0.18, 0.18), (4.6, -0.8, 2.6), code_orange, bevel=0.03,
              rotation=(c.deg(18), c.deg(30), c.deg(12)))

# Fine dust of fragments for depth.
for i in range(18):
    s = random.uniform(0.03, 0.08)
    loc = (random.uniform(-2.5, 6.0), random.uniform(-4.0, 4.0), random.uniform(-1.2, 4.6))
    c.rounded_box(f"Dust{i}", (s, s, s), loc, random.choice([glass, graphite, steel]), bevel=s * 0.2,
                  rotation=(c.deg(c.jitter(45)), c.deg(c.jitter(45)), 0))

target = (1.6, 0, 1.5)
# Camera placed so the cluster lands on the right two thirds of a 16:9 frame.
c.camera((-6.5, -11.5, 4.2), (-0.6, 0, 1.5), lens=42, fstop=2.2, focus_target=(1.2, 0, 1.6))
c.studio_lighting(target=target, exposure=0.9)
c.dark_world(0.3)

c.configure_cycles((1200, 675) if PREVIEW else (2400, 1350),
                   samples=48 if PREVIEW else 256, transparent=True)
c.save_and_render("workspace-preview" if PREVIEW else "workspace")
