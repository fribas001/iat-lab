"""blender -b --factory-startup --disable-autoexec scene.blend -P this.py -- --output file.json"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iat_lab.blender.snapshot import export_texts, write_snapshot

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--texts", type=Path)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
print(write_snapshot(args.output))
if args.texts:
    export_texts(args.texts)
