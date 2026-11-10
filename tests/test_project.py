import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from iat_lab import Project
from iat_lab.project import sha256


class ProjectTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / "build" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        assert Path(self.temp.name).resolve().is_relative_to(scratch.resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "baseline.blend").write_bytes(b"protected baseline")
        (self.root / "working.blend").write_bytes(b"editable copy")
        manifest = {"schema_version": 1, "baseline": {"path": "baseline.blend",
                    "sha256": sha256(self.root / "baseline.blend")},
                    "working_scene": "working.blend", "reference_files": []}
        (self.root / "iat-lab.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.project = Project.open(self.root)

    def test_detects_baseline_change(self):
        self.assertTrue(self.project.verify()["ok"])
        self.project.baseline.write_bytes(b"unexpected replacement")
        self.assertFalse(self.project.verify()["ok"])

    def test_working_scene_can_change_but_must_exist(self):
        self.project.working_scene.write_bytes(b"new lab design")
        self.assertTrue(self.project.verify()["ok"])
        self.project.working_scene.unlink()
        self.assertFalse(self.project.verify()["ok"])

    def test_project_paths_cannot_escape(self):
        with self.assertRaises(ValueError):
            self.project.path("../outside.blend")

    def test_import_does_not_load_blender(self):
        result = subprocess.run([sys.executable, "-c",
                                 "import sys, iat_lab; assert 'bpy' not in sys.modules"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
