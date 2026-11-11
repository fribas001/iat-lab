# Architecture

The project borrows the separation of Python API, Blender integration, node
assets, tests and documentation from
[MolecularNodes](https://github.com/BradyAJohnston/MolecularNodes/blob/main/CONTRIBUTING.md),
inspected on 10 November 2026. No MolecularNodes code is copied.

| Layer | Responsibility | Dependency |
| --- | --- | --- |
| `iat_lab.project` | Resolve project paths; verify protected inputs | Python standard library |
| `iat_lab.cli` | Expose the project API through commands | Project API |
| `iat_lab.blender` | Read scene state; export evaluated RF meshes and explicit Sionna XML | Blender `bpy` |
| `iat_lab.nodes` | Build environment controls; inspect and extract Geometry Nodes groups | Blender `bpy` |
| `iat_lab.materials` | Evaluate and validate the radio-material catalog | Python standard library |
| `iat_lab.sionna` | Load exported scenes and handle pinned-runtime compatibility | Optional Sionna RT 2.2, imported only on use |
| `scripts/` | Small command entry points | Public functions above |
| `assets/`, `scenes/`, `data/`, `config/` | Original asset, editable model, protected references and editable configuration | Files in the checkout |

`import iat_lab` is safe outside Blender. An installed wheel contains Python
code; it does not bundle lab models or resolve assets relative to site-packages.
The caller supplies a checkout root.

The new environment graphs have versioned Python definitions in
`iat_lab.nodes.parametric`, following the node-library-builder approach. The
protected original supplies detailed mesh topology. Building adds controllers,
member transforms and material assignments while preserving the default layout.
Assembly values pass through named attributes on a controller point and are
read by Object Info / Sample Index nodes. There are no runtime Python handlers.

The original `.blend` remains the authoritative definition of the two inherited
path-display graphs. `build_node_library.py` extracts all loaded Geometry Nodes
and dependencies into an ignored reusable library. Schema-2 inventory captures
actual Blender 5.2 modifier inputs and view-layer eye states. The immutable
initial inventory omitted those fields; the separate
[inspection record](scene_reference.json) remains baseline evidence. Inventories
are review metadata, not lossless serializers.

The exporter evaluates geometry independently of cutaway hiding, uses explicit
RF inclusion, splits by catalog material and converts six room slabs to single
surfaces with thickness. It writes deterministic XML/PLY plus provenance, RIS
cell data and receiver samples. Sionna is an optional external runtime; neither
the standard-library API nor Blender's controls import it.

This preserves the archived study while adding an editable geometry and export
workflow. Active RIS propagation, updated heatmaps and material characterization
remain separate scientific work, as described in [Sionna export](SIONNA_EXPORT.md)
and [radio materials](RADIO_MATERIALS.md).
