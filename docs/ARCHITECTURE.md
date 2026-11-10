# Architecture

The project borrows the separation of Python API, Blender integration, node
assets, tests and documentation from
[MolecularNodes](https://github.com/BradyAJohnston/MolecularNodes/blob/main/CONTRIBUTING.md),
inspected on 10 November 2026. No MolecularNodes code is copied.

| Layer | Responsibility | Dependency |
| --- | --- | --- |
| `iat_lab.project` | Resolve project paths; verify protected inputs | Python standard library |
| `iat_lab.cli` | Expose the project API through commands | Project API |
| `iat_lab.blender` | Read scenes, transforms, node controls and embedded records | Blender `bpy` |
| `iat_lab.nodes` | Inspect and extract the existing Geometry Nodes groups | Blender `bpy` |
| `scripts/` | Small command entry points | Public functions above |
| `assets/`, `scenes/`, `data/` | Original asset, editable model and reviewable metadata | Files in the checkout |

`import iat_lab` is safe outside Blender. An installed wheel contains Python
code; it does not bundle lab models or resolve assets relative to site-packages.
The caller supplies a checkout root.

MolecularNodes builds its node library from versioned Python definitions. Here,
the original `.blend` remains the authoritative definition of the two inherited
graphs. `build_node_library.py` extracts those graphs and their dependencies into
an ignored reusable library. The JSON inventory records sockets, connections,
selected node settings and modifier inputs for review. It is not a lossless
serializer and cannot rebuild the lab or the graphs on its own.

This boundary keeps the initial repository faithful to the supplied model.
Future graph refactoring can introduce versioned Python builders and compare
their evaluated geometry against this baseline before replacing the inherited
graphs. UI modules and extension packaging can be added when actual interactive
features exist; the first version does not ship an empty add-on.
