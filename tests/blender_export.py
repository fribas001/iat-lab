"""Export behavior: hidden RF walls, material separation, variants and repeatability."""

import json
import struct
import sys
import tempfile
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab.blender.export_sionna import export_scene
from iat_lab.nodes.parametric import set_control

candidate = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else root / "scenes/IAT_Lab.blend"
bpy.ops.wm.open_mainfile(filepath=str(candidate.resolve()))
scratch = root / "build/tests"
scratch.mkdir(parents=True, exist_ok=True)
hidden = {(s.name, o.name): (o.hide_get(view_layer=s.view_layers[0]), o.hide_render)
          for s in bpy.data.scenes for o in s.objects}
with tempfile.TemporaryDirectory(dir=scratch) as directory:
    path = Path(directory)
    assert path.resolve().is_relative_to(scratch.resolve())
    first = export_scene(path / "first", "01 Plants - active RIS")
    again = export_scene(path / "again", "01 Plants - active RIS")
    assert first == again
    for file in (path / "first").rglob("*"):
        if file.is_file():
            assert file.read_bytes() == (path / "again" / file.relative_to(path / "first")).read_bytes()
    names = {o["source_object"] for o in first["objects"]}
    assert len(names) == 31
    assert {"Wall_X_Min | RF 03", "Wall_X_Max | RF 04", "Lab_Ceiling | RF 02"} <= names
    assert not any(n.startswith(("PATHS", "HEATMAP", "Original bench")) for n in names)
    assert "Absorber_Wall_Y_Max | optional" not in names
    slabs = [o for o in first["objects"] if o["surface_policy"] == "single_slab_surface"]
    assert len(slabs) == 6
    door_wall = next(o for o in slabs if o["source_object"] == "Wall_Y_Max | RF 06")
    assert door_wall["triangles"] == 6 and door_wall["vertices"] == 8
    # A door opening must remain a hole, not become a solid rectangular proxy.
    payload = (path / "first" / door_wall["file"]).read_bytes()
    offset = payload.index(b"end_header\n") + len(b"end_header\n")
    points = [struct.unpack_from("<3f", payload, offset + i * 12) for i in range(8)]
    faces = [struct.unpack_from("<B3i", payload, offset + 8 * 12 + i * 13)[1:] for i in range(6)]
    area = 0
    for face in faces:
        a, b, c = (points[i] for i in face)
        area += abs((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0])) / 2
    assert abs(area - (3.41 * 3.6 - 0.98 * 2.3)) < 1e-4, area
    assert all(o["triangles"] == 2 for o in slabs if o["source_object"] != "Wall_Y_Max | RF 06")
    assert len(json.loads((path / "first/ris_cells.json").read_text())["positions_m"]) == 508
    assert len(json.loads((path / "first/receiver_grid.json").read_text())["positions_m"]) == 2300
    no_plants = export_scene(path / "no-plants", "03 No plants - active RIS")
    assert len(no_plants["objects"]) == 25
    assert not any(o["source_object"].startswith("Plant") for o in no_plants["objects"])
    ideal = export_scene(path / "ideal", "02 Plants - reflective RIS", "ideal")
    assert any(m["model"] == "ideal_absorber" for m in ideal["material_instances"].values())
    assert not any(m["catalog_key"] == "iat_absorber_proxy" for m in ideal["material_instances"].values())
    set_control(bpy.data.objects["CTRL | Wall Y max"], "Absorber enabled", True)
    added = export_scene(path / "added-panel", "04 No plants - reflective RIS")
    assert len(added["objects"]) == 26
    set_control(bpy.data.objects["CTRL | Wall Y max"], "Absorber enabled", False)
    set_control(bpy.data.objects["CTRL | TX assembly"], "Enabled", False)
    no_tx = export_scene(path / "no-tx", "01 Plants - active RIS")
    assert no_tx["anchors_m"]["tx"] is None
    set_control(bpy.data.objects["CTRL | TX assembly"], "Enabled", True)
assert hidden == {(s.name, o.name): (o.hide_get(view_layer=s.view_layers[0]), o.hide_render)
                  for s in bpy.data.scenes for o in s.objects}
print("PASS: reproducible exports, 4 variants, hidden-wall inclusion, six single-surface slabs, door opening, absorber modes, anchors and visibility restoration")
