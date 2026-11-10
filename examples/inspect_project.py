"""Run from the repository: python examples/inspect_project.py"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from iat_lab import Project

project = Project.open(root)
for scene in project.summary()["scenes"]:
    print(scene)
assert project.verify()["ok"], "Protected source files have changed"
