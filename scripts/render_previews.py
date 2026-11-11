"""Render repeatable Cycles repository previews without saving the loaded model."""

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab.project import sha256

VIEWS = {
    "overview": {"position": (0.45, 4.70, 2.50), "target": (1.75, 1.20, 1.30), "lens_mm": 22},
    "top": {"position": (1.705, 2.70, 3.20), "target": (1.705, 1.45, 0.55), "lens_mm": 16},
    "detail": {"position": (0.55, 2.75, 1.70), "target": (1.35, 0.67, 1.18), "lens_mm": 35},
}
parser = argparse.ArgumentParser()
parser.add_argument("--output", default="docs/images/cycles")
parser.add_argument("--view", choices=list(VIEWS), default="overview")
parser.add_argument("--samples", type=int, default=64)
parser.add_argument("--width", type=int, default=1440)
parser.add_argument("--height", type=int, default=900)
parser.add_argument("--hide-results", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
if min(args.samples, args.width, args.height) < 1:
    raise ValueError("Samples and image dimensions must be positive")
out = (root / args.output).resolve()
out.mkdir(parents=True, exist_ok=True)


def render_one():
    scene = bpy.data.scenes["01 Plants - active RIS"]
    bpy.context.window.scene = scene
    # Restore the complete physical room for interior photography. Leave archived
    # scanner/bench references hidden, and respect the optional fourth absorber toggle.
    revealed = []
    for obj in scene.objects:
        if obj.name.startswith(("Wall_", "Lab_Floor", "Lab_Ceiling", "Absorber_Wall_", "Pipes_", "Light_Fixtures")):
            obj.hide_render = False
            obj.hide_viewport = False
            obj.hide_set(False)
            revealed.append(obj.name)
    for collection in scene.collection.children:
        if collection.name.startswith(("01 RF", "02 RF")):
            collection.hide_render = False
            collection.hide_viewport = False
            layer = bpy.context.view_layer.layer_collection.children[collection.name]
            layer.exclude = False
            layer.hide_viewport = False

    def aim(obj, target):
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

    # The original presentation softboxes sit partly outside the room. Place the
    # preview lights inside it so the restored walls do not block the illumination.
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.hide_render = True
    lights = [
        ((1.70, 1.45, 3.10), (1.70, 1.45, 0.0), 450, 2.0),
        ((1.70, 4.00, 3.10), (1.70, 3.00, 0.0), 300, 2.0),
        ((0.55, 4.40, 2.70), (1.70, 1.30, 1.0), 180, 1.5),
    ]
    for i, (position, target, energy, size) in enumerate(lights):
        data = bpy.data.lights.new(f"Preview interior softbox {i + 1}", "AREA")
        data.energy, data.shape, data.size = energy, "DISK", size
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        aim(obj, target)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.035
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.seed = 42
    scene.cycles.max_bounces = 8
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.0
    if args.hide_results:
        for obj in scene.objects:
            if obj.name.startswith(("PATHS", "HEATMAP")):
                obj.hide_render = True
    record = {"engine": "Cycles", "device": "CPU", "blender": bpy.app.version_string,
              "scene": scene.name, "source_blend_sha256": sha256(Path(bpy.data.filepath)),
              "samples": args.samples, "adaptive_threshold": 0.035, "denoiser": "OpenImageDenoise",
              "seed": 42, "resolution": [args.width, args.height], "view_transform": "AgX",
              "exposure": 0.0, "walls": "all four walls, floor and ceiling visible",
              "revealed_objects": sorted(revealed), "interior_lights": lights,
              "archived_results_visible": not args.hide_results, "views": {}}
    for name, settings in VIEWS.items():
        if args.view != name:
            continue
        data = bpy.data.cameras.new("Preview interior " + name)
        data.lens, data.sensor_width, data.clip_start, data.clip_end = settings["lens_mm"], 36, 0.01, 100
        camera = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(camera)
        camera.location = settings["position"]
        aim(camera, settings["target"])
        scene.camera = camera
        target = out / (name + ".png")
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        record["views"][name] = {"camera": camera.name, **settings,
                                 "file": target.name, "sha256": sha256(target)}
        print("PREVIEW SAVED", target, flush=True)
    (out / (args.view + "_settings.json")).write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


render_one()
