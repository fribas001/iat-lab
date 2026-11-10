"""Build a reusable node library from the loaded scene; no scene save is performed."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iat_lab.nodes import build_library

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("build/nodes.blend"))
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
print("Extracted node groups:", build_library(args.output))
