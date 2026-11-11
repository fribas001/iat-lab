# Editing the lab model

Open `scenes/IAT_Lab.blend` with Blender 5.2.3 LTS. Use the scene selector for
the four plant/RIS variants. The embedded `START HERE.txt` contains the original
viewing and filtering guide; an exact text export is in `data/embedded/`.

For current environment edits, start with [Parametric environment](PARAMETRIC_ENVIRONMENT.md).
Select a `CTRL | …` object in `00 IAT Controls` and change its Geometry Nodes
modifier. The saved model has 19 assembly controllers. See
[radio materials](RADIO_MATERIALS.md) and [Sionna export](SIONNA_EXPORT.md) for
simulation preparation.

Read [Scene organization and visibility](SCENE_GUIDE.md) for the full collection
reference, hidden-object list, shared-data behavior and full-room viewing steps.
[Geometry Nodes and controls](GEOMETRY_NODES.md) explains both groups with flow
diagrams, control tables, saved values and filtering recipes.

The original collection hierarchy is retained, with `00 IAT Controls` added: laboratory RF geometry,
cutaway walls, close-pair Ficus, devices and guides, simulation results, cameras
and lighting. Unit settings are metric with a scale length of 1.0.

The two inherited path-display node groups are:

- `RIS path controls | existing Sionna filters + receiver and cell`
- `Sionna_Paths | embedded straight paths`

To change path visualization, select a `PATHS` object and use its Geometry Nodes
modifier. Changing those controls filters embedded results; it does not run a
new simulation. The reference text explains receiver, tile and cell indices.

The cutaway is saved as individual object eye and render flags. Enabling the
cutaway collection alone does not reveal its hidden objects. Switching scene
variants selects matching plants, glyphs, paths and heatmaps together; changing
only a path modifier's case switches does not update those other objects.

Save model edits into the working file or another named file under `scenes/`.
Keep the original copy under `assets/baseline/`. The project verifier checks the
original and the extracted reference records; it allows the working file to
change. Blender smoke checks still enforce the four registered scene names,
cameras, resolvable dependencies and a successful node-library round trip.

Use `scripts/inspect_scene.py -- --output runs/current_inventory.json` with the
Blender command in the README after editing. Its output does not capture all
possible Blender properties, evaluated mesh data, animation or external cache
contents. Preserve the `.blend` as well as the metadata.

The immutable initial inventory omits per-view-layer eye states and Blender
5.2's RNA-based modifier input values. The current snapshot API (schema 2) captures
them in `view_layers` and `modifier_inputs`. The detailed baseline guides use a
separate [inspection record](scene_reference.json) for the original values. See the
[read-only inspection snippet](GEOMETRY_NODES.md#8-inspecting-the-saved-controls)
before comparing modifier settings after an edit.

The initial scene has no external image, library, font, movie, sound or cache
file dependencies. If future edits add them, keep their source assets in this
repository and use Blender-relative paths or pack them into the `.blend`.
