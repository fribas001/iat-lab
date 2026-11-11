"""Run with Blender on the edited scene; never saves or changes the .blend."""

import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from iat_lab.blender.export_sionna import export_scene

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True, help="New or empty export directory")
parser.add_argument("--scene", default="01 Plants - active RIS")
parser.add_argument("--absorber-model", choices=["archived-proxy", "ideal"], default="archived-proxy")
parser.add_argument("--materials", default=str(root / "config/radio_materials.json"))
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
report = export_scene(args.output, args.scene, args.absorber_model, materials_file=args.materials)
print(f"Exported {len(report['objects'])} material-separated RF meshes to {args.output}")
for message in report["limitations"]:
    print("MODEL SCOPE:", message)
