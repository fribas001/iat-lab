# Editing the lab model

Open `scenes/IAT_Lab.blend` with Blender 5.2.3 LTS. Use the scene selector for
the four plant/RIS variants. The embedded `START HERE.txt` contains the original
viewing and filtering guide; an exact text export is in `data/embedded/`.

The collection hierarchy is preserved from the source: laboratory RF geometry,
cutaway walls, close-pair Ficus, devices and guides, simulation results, cameras
and lighting. Unit settings are metric with a scale length of 1.0.

The two node groups are:

- `RIS path controls | existing Sionna filters + receiver and cell`
- `Sionna_Paths | embedded straight paths`

To change path visualization, select a `PATHS` object and use its Geometry Nodes
modifier. Changing those controls filters embedded results; it does not run a
new simulation. The reference text explains receiver, tile and cell indices.

Save model edits into the working file or another named file under `scenes/`.
Keep the original copy under `assets/baseline/`. The project verifier checks the
original and the extracted reference records; it allows the working file to
change. Blender smoke checks still enforce the four registered scene names,
cameras, resolvable dependencies and a successful node-library round trip.

Use `scripts/inspect_scene.py -- --output runs/current_inventory.json` with the
Blender command in the README after editing. Its output does not capture all
possible Blender properties, evaluated mesh data, animation or external cache
contents. Preserve the `.blend` as well as the metadata.

The initial scene has no external image, library, font, movie, sound or cache
file dependencies. If future edits add them, keep their source assets in this
repository and use Blender-relative paths or pack them into the `.blend`.
