# IAT Lab

Editable Blender model of the IAT laboratory setup, organized as a reusable
Python project following the architectural ideas of MolecularNodes.

Open **[`scenes/IAT_Lab.blend`](scenes/IAT_Lab.blend)** in **Blender 5.2.3 LTS**.
It is an exact copy of the supplied full-background, close-pair model. All four
scene variants, cameras, path controls, materials and embedded results are retained.

| Scene | Setup |
| --- | --- |
| 01 Plants - active RIS | Close-pair plants with active RIS |
| 02 Plants - reflective RIS | Close-pair plants with reflective RIS |
| 03 No plants - active RIS | Matched computational baseline |
| 04 No plants - reflective RIS | Matched computational baseline |

## Understand the model

- [Scene organization and visibility](docs/SCENE_GUIDE.md): all 12 collections,
  scene membership, shared objects, cameras and the exact cutaway visibility rules.
- [Geometry Nodes and controls](docs/GEOMETRY_NODES.md): both groups, flow diagrams,
  every exposed control, saved scene settings and practical filtering recipes.
- [Inspection record](docs/scene_reference.json): machine-readable collection
  contents, visibility flags, socket interfaces and saved modifier values.

## Repository layout

```text
iat_lab/                       reusable Python API and command-line interface
  project.py                   manifest, paths and baseline verification
  blender/                     Blender scene inventory and text export
  nodes/                       Geometry Nodes inspection and asset extraction
assets/baseline/               original .blend, protected by SHA-256
scenes/IAT_Lab.blend            editable working model
data/baseline_inventory.json   reviewable scene and node metadata
data/embedded/                 text and numerical records extracted from the model
scripts/                      thin Blender entry points
examples/                     Python API example
tests/                        Python checks and Blender integration smoke test
docs/                         scene/node guides, architecture, workflows and provenance
.github/workflows/             automated Python and input-integrity checks
build/, runs/, renders/        local generated outputs, ignored by Git
```

## Inspect and validate

Python 3.11+ is sufficient for the project API and integrity checks; there are
no runtime dependencies outside Blender. Run these commands from the repository:

```powershell
python -m iat_lab info
python -m iat_lab verify
python -m unittest discover -s tests -v
```

Optional install into your own virtual environment: `python -m pip install -e .`.
The installed command is `iat-lab`. Code is packaged; scene assets stay in the
checkout. Outside the checkout, use `iat-lab --project C:\path\to\iat-lab info`.

## Blender tools

On Windows, point `$blender` to your Blender executable:

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $blender --background --factory-startup --disable-autoexec scenes/IAT_Lab.blend --python-exit-code 1 --python scripts/inspect_scene.py -- --output runs/current_inventory.json
& $blender --background --factory-startup --disable-autoexec scenes/IAT_Lab.blend --python-exit-code 1 --python scripts/build_node_library.py -- --output build/nodes.blend
& $blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_smoke.py
```

These commands inspect the scene or extract reusable node assets without saving
over the working model. In Blender, use **File > Append** and choose the
**NodeTree** folder of `build/nodes.blend` to reuse the groups in another file.

For the first modelling change, edit `scenes/IAT_Lab.blend`, save it, capture a
new inventory under `runs/`, and commit the model with a description of the change.
See [Blender workflow](docs/BLENDER.md) and [contributing](CONTRIBUTING.md).

## Architecture reference and scope

The [MolecularNodes contribution guide](https://github.com/BradyAJohnston/MolecularNodes/blob/main/CONTRIBUTING.md)
informs the separation of reusable functions, Blender integration, node assets,
tests and documentation. MolecularNodes is an architecture reference, not a dependency.

This first version structures the existing lab model. It does not yet provide
an installable Blender extension, regenerate the lab from Python, or rerun the
embedded propagation results. The existing two node graphs visualize paths;
they are not a procedural plant generator. See [architecture](docs/ARCHITECTURE.md),
[provenance](docs/PROVENANCE.md) and [rights](docs/RIGHTS.md).
