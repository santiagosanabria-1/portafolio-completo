"""Shared helpers for the portfolio Blender scenes.

Every scene script imports this module, builds its geometry from a fixed
random seed and renders through `render()`, so running the same script twice
produces the same image. Tested with Blender 5.2 LTS (Principled BSDF v2).
"""

import math
import os
import random

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCENES_DIR = os.path.join(ROOT, "scenes")
RENDERS_DIR = os.path.join(ROOT, "renders")

# Brand palette (sRGB hex) — kept in sync with css/tokens in styles.css.
ORANGE = "#EA5C25"
BLUE = "#384A90"
BACKGROUND = "#080808"


def hex_to_linear(hex_color, alpha=1.0):
    """Convert an sRGB hex string to the linear RGBA tuple Blender expects."""
    hex_color = hex_color.lstrip("#")
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (*[to_linear(c) for c in channels], alpha)


def reset_scene(seed):
    """Start from an empty scene and seed the RNG for reproducible layouts."""
    random.seed(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def _principled(name, **inputs):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    for key, value in inputs.items():
        socket = bsdf.inputs.get(key)
        if socket is None:
            raise KeyError(f"Principled BSDF has no input '{key}' in this Blender version")
        socket.default_value = value
    return mat


def mat_graphite(name="Graphite", roughness=0.32):
    return _principled(name, **{
        "Base Color": (0.018, 0.018, 0.021, 1),
        "Metallic": 1.0,
        "Roughness": roughness,
        "Anisotropic": 0.35,
    })


def mat_steel(name="Steel"):
    return _principled(name, **{
        "Base Color": (0.42, 0.42, 0.44, 1),
        "Metallic": 1.0,
        "Roughness": 0.22,
    })


def mat_glass(name="Glass", roughness=0.0, tint=(0.92, 0.94, 0.98, 1)):
    return _principled(name, **{
        "Base Color": tint,
        "Transmission Weight": 1.0,
        "Roughness": roughness,
        "IOR": 1.45,
        "Coat Weight": 0.3 if roughness == 0 else 0.0,
    })


def mat_satin(name="Satin", color=(0.05, 0.05, 0.055, 1)):
    """Dark non-metal used for the 'code line' bars and small modules."""
    return _principled(name, **{
        "Base Color": color,
        "Roughness": 0.45,
        "Specular IOR Level": 0.4,
    })


def mat_emission(name, hex_color, strength):
    """Accent material: the object is dark but glows in the brand color."""
    return _principled(name, **{
        "Base Color": hex_to_linear(hex_color),
        "Roughness": 0.3,
        "Emission Color": hex_to_linear(hex_color),
        "Emission Strength": strength,
    })


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

def rounded_box(name, size, location, material, bevel=0.04, segments=5, rotation=(0, 0, 0)):
    """A bevelled box — the base building block of every scene."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = min(bevel, min(size) * 0.49)
    mod.segments = segments
    mod.limit_method = "ANGLE"
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def sphere(name, radius, location, material, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location,
                                         segments=segments, ring_count=segments // 2)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def rod(name, start, end, radius, material):
    """A thin cylinder between two points (edges of the node graphs)."""
    start, end = Vector(start), Vector(end)
    direction = end - start
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=direction.length,
                                        location=(start + end) / 2, vertices=16)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


# --------------------------------------------------------------------------
# Camera, lights, world
# --------------------------------------------------------------------------

def camera(location, target, lens=70, fstop=None, focus_target=None):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    if fstop:
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = fstop
        focus = Vector(focus_target or target)
        cam_data.dof.focus_distance = (focus - Vector(location)).length
    bpy.context.scene.camera = cam
    return cam


def area_light(name, location, target, energy, size, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = shape
    data.size = size
    if size_y is not None:
        data.size_y = size_y
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    direction = Vector(target) - Vector(location)
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return light


def studio_lighting(accent_rim=True, exposure=1.0, target=(0, 0, 0.8)):
    """Cinematic three-point setup: soft key, cool fill, orange rim accent."""
    area_light("Key", (-4.5, -3.5, 6.5), target, 1500 * exposure, 4.5, color=(1.0, 0.97, 0.93))
    area_light("Fill", (5.5, -5.0, 1.5), target, 320 * exposure, 6.0, color=(0.72, 0.8, 1.0))
    area_light("Top", (0, 0, 9), (0, 0, 0), 450 * exposure, 8.0)
    # Long strip behind the subject: draws bright edges on glass and metal.
    area_light("Strip", (-1.0, 6.5, 4.0), target, 380 * exposure, 7.0, size_y=0.4)
    if accent_rim:
        area_light("RimOrange", (3.5, 5.0, 2.8), target, 520 * exposure, 2.5,
                   color=hex_to_linear(ORANGE)[:3])
        area_light("RimBlue", (-5.5, 3.5, 1.2), target, 320 * exposure, 3.0,
                   color=hex_to_linear(BLUE)[:3])


def dark_world(strength=0.35):
    """Near-black world: gives glass something to reflect without a visible backdrop."""
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_to_linear("#1a1c22")
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = world


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------

def configure_cycles(resolution, samples=256, transparent=True):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.get_devices()
    # Prefer the GPU when present; fall back to CPU silently only because the
    # result is identical, just slower.
    for backend in ("OPTIX", "CUDA"):
        if any(d.type == backend for d in prefs.devices):
            prefs.compute_device_type = backend
            for d in prefs.devices:
                d.use = d.type == backend
            scene.cycles.device = "GPU"
            break
    else:
        scene.cycles.device = "CPU"
    print(f"[render] device={scene.cycles.device} backend={prefs.compute_device_type}")

    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 12
    scene.cycles.glossy_bounces = 6
    scene.cycles.seed = 7

    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.cycles.film_transparent_glass = transparent

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15


def save_and_render(name):
    os.makedirs(SCENES_DIR, exist_ok=True)
    os.makedirs(RENDERS_DIR, exist_ok=True)
    blend_path = os.path.join(SCENES_DIR, f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
    out = os.path.join(RENDERS_DIR, f"{name}.png")
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"[render] wrote {out}")
    return out


def jitter(amount):
    return random.uniform(-amount, amount)


def deg(value):
    return math.radians(value)
