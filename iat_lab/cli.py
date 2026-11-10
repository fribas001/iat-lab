"""Thin command wrappers around the project API."""

import argparse
import json

from .project import Project


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect and verify the IAT lab repository")
    parser.add_argument("--project", default=".", help="Repository root (default: current directory)")
    parser.add_argument("command", choices=("info", "verify"))
    args = parser.parse_args(argv)
    try:
        project = Project.open(args.project)
        result = project.verify() if args.command == "verify" else project.summary()
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"iat-lab: {error}\n")
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1
