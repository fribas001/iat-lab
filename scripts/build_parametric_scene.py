"""Blender entry point: rebuild controls from the immutable baseline."""

import argparse
import sys
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab import Project
from iat_lab.nodes.parametric import build
from iat_lab.materials import load_catalog, write_catalog
from iat_lab.project import sha256

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="scenes/IAT_Lab.blend")
parser.add_argument("--replace", action="store_true", help="Explicitly replace an edited working model")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
project = Project.open(root)
source = project.path("assets/baseline/RIS_Full_Background_Close_Pair.blend")
output = (root / args.output).resolve()
if output == source.resolve():
    raise ValueError("Cannot overwrite the protected baseline")
if output.exists() and sha256(output) != sha256(source) and not args.replace:
    raise ValueError("Working model has edits. Choose a new output or pass --replace explicitly.")
assert project.verify()["ok"]
bpy.ops.wm.open_mainfile(filepath=str(source))
catalog_path = root / "config/radio_materials.json"
if not catalog_path.exists():
    write_catalog(catalog_path)
reference = build(root / "config/parametric_defaults.json", load_catalog(catalog_path))
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
print(f"Saved {len(reference['assemblies'])} parametric assemblies to {output}")
