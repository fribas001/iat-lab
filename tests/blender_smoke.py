"""Run with factory-startup Blender; validate the scene and reusable node library."""

import json
import sys
import tempfile
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from iat_lab import Project
from iat_lab.blender.snapshot import capture
from iat_lab.nodes import build_library, snapshot_group

project = Project.open(root)
assert project.verify()["ok"], "Protected inputs failed verification"
bpy.ops.wm.open_mainfile(filepath=str(project.working_scene))
snapshot = capture()
assert [s["name"] for s in snapshot["scenes"]] == project.manifest["scenes"]
assert all(s["camera"] for s in snapshot["scenes"]), "A scene has no camera"
assert not [d for d in snapshot["dependencies"] if not d["exists"]], "Missing dependencies"
assert not any(t["use_module"] for t in snapshot["embedded_texts"]), "Auto-run text found"
reference = json.loads(project.path("data/baseline_inventory.json").read_text(encoding="utf-8"))
assert snapshot["node_groups"], "No node groups"

# Compare the initial copy in full while its saved bytes still match the baseline.
# Once editing begins, scene names/cameras/dependencies and library round trips remain checked.
if snapshot["saved_file_sha256"] == reference["saved_file_sha256"]:
    for key in ("scenes", "collections", "objects", "node_groups", "embedded_texts"):
        assert snapshot[key] == reference[key], f"Baseline copy changed: {key}"

expected = {group["name"]: group for group in snapshot["node_groups"]}
scratch = root / "build" / "tests"
scratch.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=scratch) as directory:
    assert Path(directory).resolve().is_relative_to(scratch.resolve())
    output = Path(directory) / "nodes.blend"
    build_library(output)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(output), link=False) as (source, target):
        target.node_groups = source.node_groups
    actual = {g.name: snapshot_group(g) for g in bpy.data.node_groups}
    assert actual == expected, "Node library extraction changed the graphs"
assert project.verify()["ok"], "Validation modified protected inputs"
print("PASS: scene variants, cameras, assets, baseline fidelity and node library round trip")
