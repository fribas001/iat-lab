"""Behavioral checks for the parametric scene, run by Blender in background mode."""

import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab.nodes.parametric import controller_values, set_control

candidate = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else root / "scenes/IAT_Lab.blend"
bpy.ops.wm.open_mainfile(filepath=str(root / "assets/baseline/RIS_Full_Background_Close_Pair.blend"))
baseline = {o.name: np.array([list(o.matrix_world @ v.co) for v in o.data.vertices])
            for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(("PATHS", "HEATMAP", "Original bench"))}
hidden = {o.name: o.hide_render for o in bpy.data.objects}
bpy.ops.wm.open_mainfile(filepath=str(candidate.resolve()))
for scene in bpy.data.scenes:
    path_collection = bpy.data.collections["Paths | " + scene.name]
    heatmap_collection = bpy.data.collections["Heatmap | " + scene.name]
    assert len(path_collection.objects) == len(heatmap_collection.objects) == 1
    parent = next(c for c in scene.collection.children if path_collection.name in c.children)
    assert heatmap_collection.name in parent.children and len(parent.objects) == 0
for obj in bpy.context.scene.objects:
    obj.hide_set(False)
bpy.context.view_layer.update()

def vertices(name):
    obj = bpy.data.objects[name]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return np.array([list(evaluated.matrix_world @ v.co) for v in mesh.vertices]).reshape((-1, 3))
    finally:
        evaluated.to_mesh_clear()

maximum = 0.0
for name, expected in baseline.items():
    if name not in bpy.context.scene.objects:
        continue
    actual = vertices(name)
    assert actual.shape == expected.shape, (name, actual.shape, expected.shape)
    error = float(np.max(np.abs(actual - expected))) if actual.size else 0
    maximum = max(maximum, error)
    assert error < 5e-6, (name, error)
assert all(bpy.data.objects[name].hide_render == value for name, value in hidden.items())

wall_name = "Wall_Y_Min | RF 05"
foam_name = "Absorber_Wall_Y_Min | RF 07"
ctrl = bpy.data.objects["CTRL | Wall Y min"]
defaults = controller_values(ctrl)
before_wall, before_foam = vertices(wall_name), vertices(foam_name)
delta = np.array([0.25, 0.15, 0.1])
set_control(ctrl, "Position", np.array(defaults["Position"]) + delta)
np.testing.assert_allclose(vertices(wall_name), before_wall + delta, atol=2e-6)
np.testing.assert_allclose(vertices(foam_name), before_foam + delta, atol=2e-6)
set_control(ctrl, "Position", defaults["Position"])
set_control(ctrl, "Rotation", [0, 0, math.pi / 2])
rotation = np.array(Euler((0, 0, math.pi / 2)).to_matrix())
pivot = np.array(defaults["Position"])
np.testing.assert_allclose(vertices(wall_name), (before_wall - pivot) @ rotation.T + pivot, atol=2e-6)
np.testing.assert_allclose(vertices(foam_name), (before_foam - pivot) @ rotation.T + pivot, atol=2e-6)
set_control(ctrl, "Rotation", defaults["Rotation"])
size = np.array(defaults["Size"]) * [1.2, 1.5, 1.1]
set_control(ctrl, "Size", size)
actual_wall, actual_foam = vertices(wall_name), vertices(foam_name)
assert abs(np.ptp(actual_wall[:, 0]) - size[0]) < 2e-6
assert abs(np.ptp(actual_foam[:, 1]) - defaults["Absorber depth"]) < 2e-6
assert abs(actual_foam[:, 1].min() - actual_wall[:, 1].max() - defaults["Absorber gap"]) < 2e-6
set_control(ctrl, "Size", defaults["Size"])
set_control(ctrl, "Absorber enabled", False)
assert len(vertices(foam_name)) == 0 and len(vertices(wall_name)) == 8
set_control(ctrl, "Absorber enabled", True)
set_control(ctrl, "Enabled", False)
assert len(vertices(foam_name)) == 0 and len(vertices(wall_name)) == 0
set_control(ctrl, "Enabled", True)
optional = bpy.data.objects["CTRL | Wall Y max"]
assert len(vertices("Absorber_Wall_Y_Max | optional")) == 0
set_control(optional, "Absorber enabled", True)
assert len(vertices("Absorber_Wall_Y_Max | optional")) > 0
set_control(optional, "Absorber enabled", False)

for label, names in {
    "RIS aperture": ["RIS_508_Mount_and_Stand | RF 21", "RIS | exact 508 cell centres and profiles", "RIS cell glyphs | active ON blue, OFF dark"],
    "Scanner table": ["Scanner_Static | RF 18", "Scanner_Static | RF 19", "Scanner_Static | RF 20"],
    "Scanner sampling plane": ["RX grid | 2300 phase-centre samples"],
    "Plant 1": ["Plant1_Leaves", "Plant1_Pot"],
}.items():
    obj = bpy.data.objects["CTRL | " + label]
    initial = controller_values(obj)["Position"]
    snapshots = {name: vertices(name) for name in names}
    stand = vertices("RIS_508_Mount_and_Stand | RF 22")
    set_control(obj, "Position", np.array(initial) + delta)
    for name in names:
        np.testing.assert_allclose(vertices(name), snapshots[name] + delta, atol=3e-6)
    if label == "RIS aperture":
        np.testing.assert_array_equal(vertices("RIS_508_Mount_and_Stand | RF 22"), stand)
    set_control(obj, "Position", initial)

assert len(vertices("RIS | exact 508 cell centres and profiles")) == 508
assert len(vertices("RX grid | 2300 phase-centre samples")) == 2300
print(f"PASS: default vertices preserved (max error {maximum:.3g} m), wall transforms, attached absorbers, toggles, RIS/scanner/plant controls")
