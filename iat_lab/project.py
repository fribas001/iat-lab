"""Repository paths and immutable-input verification, using only the standard library."""

import hashlib
import json
from pathlib import Path


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.manifest = json.loads((self.root / "iat-lab.json").read_text(encoding="utf-8"))
        if self.manifest.get("schema_version") != 1:
            raise ValueError("Unsupported iat-lab.json schema version")

    @classmethod
    def open(cls, root="."):
        return cls(root)

    def path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"Path escapes project: {relative}")
        return path

    @property
    def baseline(self):
        return self.path(self.manifest["baseline"]["path"])

    @property
    def working_scene(self):
        return self.path(self.manifest["working_scene"])

    def verify(self):
        """Check protected inputs; the working .blend is deliberately editable."""
        checks = []
        records = [self.manifest["baseline"], *self.manifest["reference_files"]]
        for record in records:
            path = self.path(record["path"])
            actual = sha256(path) if path.is_file() else None
            checks.append({"path": record["path"], "ok": actual == record["sha256"],
                           "expected": record["sha256"], "actual": actual})
        checks.append({"path": self.manifest["working_scene"],
                       "ok": self.working_scene.is_file(), "check": "exists (editable)"})
        return {"ok": all(check["ok"] for check in checks), "checks": checks}

    def summary(self):
        return {"name": self.manifest["name"], "root": str(self.root),
                "baseline": str(self.baseline), "working_scene": str(self.working_scene),
                "blender": self.manifest["blender"], "scenes": self.manifest["scenes"]}
