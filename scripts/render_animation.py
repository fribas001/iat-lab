"""Render a small interior camera loop; run through Blender in background mode."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab.project import sha256

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="build/setup-animation")
parser.add_argument("--frames", type=int, default=48)
parser.add_argument("--fps", type=int, default=8)
parser.add_argument("--width", type=int, default=640)
parser.add_argument("--height", type=int, default=400)
parser.add_argument("--engine", choices=["eevee", "cycles"], default="eevee")
parser.add_argument("--samples", type=int, default=16)
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--end", type=int, default=None, help="Exclusive frame index; useful for previews")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
if min(args.frames, args.fps, args.width, args.height, args.samples) < 1:
    raise ValueError("Frame count, fps, dimensions and samples must be positive")
end = args.frames if args.end is None else args.end
if not 0 <= args.start < end <= args.frames:
    raise ValueError("Invalid frame range")
out = (root / args.output).resolve()
out.mkdir(parents=True, exist_ok=True)
scene = bpy.data.scenes["01 Plants - active RIS"]
bpy.context.window.scene = scene
for obj in scene.objects:
    if obj.name.startswith(("Wall_", "Lab_Floor", "Lab_Ceiling", "Absorber_Wall_", "Pipes_", "Light_Fixtures")):
        obj.hide_render = obj.hide_viewport = False
        obj.hide_set(False)
for collection in scene.collection.children:
    if collection.name.startswith(("01 RF", "02 RF")):
        collection.hide_render = collection.hide_viewport = False
        layer = bpy.context.view_layer.layer_collection.children[collection.name]
        layer.exclude = layer.hide_viewport = False


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


for obj in scene.objects:
    if obj.type == "LIGHT":
        obj.hide_render = True
lights = [
    ((1.7, 1.45, 3.10), (1.7, 1.45, 0), 450, 2.0),
    ((1.7, 4.00, 3.10), (1.7, 3.00, 0), 300, 2.0),
    ((0.55, 4.40, 2.70), (1.7, 1.3, 1.0), 180, 1.5),
]
for i, (location, target, power, size) in enumerate(lights):
    data = bpy.data.lights.new(f"Animation softbox {i + 1}", "AREA")
    data.energy, data.shape, data.size = power, "DISK", size
    lamp = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(lamp)
    lamp.location = location
    aim(lamp, target)
scene.render.engine = "BLENDER_EEVEE" if args.engine == "eevee" else "CYCLES"
scene.render.threads_mode, scene.render.threads = "FIXED", 8
if args.engine == "cycles":
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.seed = 42
    scene.cycles.max_bounces = 6
else:
    scene.eevee.taa_render_samples = args.samples
scene.render.resolution_x, scene.render.resolution_y = args.width, args.height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = 0
data = bpy.data.cameras.new("Animation interior camera")
data.lens, data.sensor_width, data.clip_start, data.clip_end = 24, 36, 0.01, 100
camera = bpy.data.objects.new(data.name, data)
scene.collection.objects.link(camera)
scene.camera = camera
results = [obj for obj in scene.objects if obj.name.startswith(("PATHS", "HEATMAP"))]
record = {"source_blend_sha256": sha256(Path(bpy.data.filepath)), "blender": bpy.app.version_string,
          "scene": scene.name, "engine": scene.render.engine, "samples": args.samples,
          "frame_count": args.frames, "fps": args.fps, "resolution": [args.width, args.height],
          "walls": "All four walls, floor and ceiling visible", "lights": lights,
          "scope": "Camera tour; result overlays are archived, not a new RF simulation",
          "frames": []}
for index in range(args.start, end):
    phase = 2 * math.pi * index / args.frames
    camera.location = (0.90 - 0.45 * math.cos(phase), 4.55 + 0.12 * math.sin(phase),
                       2.35 + 0.12 * math.sin(phase))
    aim(camera, (1.65, 1.25, 1.10))
    visible = args.frames // 3 <= index < 5 * args.frames // 6
    for obj in results:
        obj.hide_render = not visible
    bpy.context.view_layer.update()
    target = out / f"frame_{index:04d}.png"
    scene.render.filepath = str(target)
    bpy.ops.render.render(write_still=True)
    record["frames"].append({"index": index, "file": target.name, "sha256": sha256(target),
                             "camera_position": list(camera.location), "archived_results_visible": visible})
    (out / "frames.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"ANIMATION FRAME {index + 1}/{args.frames}", flush=True)
# The scene and its original camera/visibility settings are not saved over.
