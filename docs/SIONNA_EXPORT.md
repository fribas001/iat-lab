# Reproducible export for Sionna RT 2.2

The exporter evaluates the saved Geometry Nodes controls, splits RF meshes by
material, and writes a Mitsuba scene with explicit radio-material definitions.
It needs Blender's bundled Python and does not require a Blender exporter add-on.
The optional runtime is pinned in [`requirements-sionna.txt`](../requirements-sionna.txt).

## Export the edited scene

Save your control changes in Blender first. From the repository root:

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $blender --background --factory-startup --disable-autoexec scenes/IAT_Lab.blend --python-exit-code 1 --python scripts/export_sionna.py -- --output runs/export-001 --scene '01 Plants - active RIS' --absorber-model archived-proxy
```

Choose a new or empty output directory for every run. Other valid scenes are
`02 Plants - reflective RIS`, `03 No plants - active RIS` and
`04 No plants - reflective RIS`. Use `--absorber-model ideal` for the ideal
absorber comparison. The CLI reads `config/radio_materials.json` by default;
`--materials` can select another explicit catalog.

| Output | Contents |
| --- | --- |
| `scene.xml` | Explicit `itu-radio-material`, `radio-material` or `absorber-radio-material` definitions, and references to physical meshes. |
| `meshes/*.ply` | Deterministic binary triangle meshes, in world metres, one material per shape. |
| `manifest.json` | Source `.blend` hash, all controller settings, shape/material mapping, per-mesh hashes, inclusion/exclusion, slab policy and modelling limitations. |
| `materials.json` | Resolved material catalog at the selected carrier. |
| `ris_cells.json` | Evaluated cell positions and surviving scalar point attributes, including saved states. |
| `receiver_grid.json` | Evaluated scanner sample positions and scalar attributes. |

The default plants-present scene exports **31 RF shapes**; a no-plant scene
exports **25**. Turning on the optional Y-max absorber adds one. Disabled
geometry contributes no triangles. Presentation hiding does not remove RF
walls: `iat_export` and evaluated node output determine membership.

Six room objects use single interior-facing slab surfaces. The Y-max wall keeps
its doorway. Material instances receive separate stable names when their slab
thickness differs, for example `itu_concrete__…`; the base catalog key remains
`itu_concrete`. The manifest records the exact relationship.

## Load and check in Sionna

Use a separate Python environment so simulation dependencies do not alter Blender:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-sionna.txt
.venv/Scripts/python.exe examples/load_sionna_export.py runs/export-001
```

The checker loads the XML with `merge_shapes=False`, sets the frequency to
23.8 GHz, and verifies every material's permittivity, conductivity and slab
thickness against the export manifest. For an optional ordinary-path sanity run:

```powershell
.venv/Scripts/python.exe examples/load_sionna_export.py runs/export-001 --trace
```

The example uses `iat_lab.sionna.load_export`. For the **ideal absorber** option,
this adapter handles a Sionna 2.2.0 compatibility defect: its frequency setter
calls `frequency_update`, but `AbsorberRadioMaterial` does not implement it.
The adapter adds a no-op to only those loaded frequency-independent instances.
Use this adapter for ideal-absorber exports; it does not patch the installed
package or change the absorber's scattering behavior.

This example uses isotropic antennas at the evaluated TX and target anchors,
10 dBm TX, depth 2, 10,000 samples and seed 42. It enables direct/specular paths
and disables diffuse reflection, refraction and diffraction. These settings
exercise loading and path computation; they are not a calibrated experiment.
Both anchor assemblies must be enabled to run the trace. An export with a
disabled anchor remains loadable and records that anchor as null.

On a Windows CPU installation, Dr.Jit may need a compatible LLVM library:

```powershell
$env:DRJIT_LIBLLVM_PATH = 'C:\Program Files\LLVM\bin\LLVM-C.dll'
```

That example path must exist on the machine; it is not a repository dependency.
Sionna chooses an available supported Mitsuba backend. The local checks used
`llvm_ad_mono_polarized`, Sionna RT 2.2.0, Mitsuba 3.9.1 and Dr.Jit 1.5.0.

## RIS and archived results

The export includes the RIS backing/stand as ordinary physical geometry and
exports the 508 aperture cells separately. **It does not turn the RIS into a
working programmable scattering surface in Sionna.** Active amplification,
per-cell phase response, state optimization and the archived two-hop calculation
need an explicit RIS solver integration. Changing the aperture geometry does
not re-optimize its frozen states.

Path tubes and heatmaps are excluded from RF geometry. They are stored baseline
results, not newly computed outputs. The example also uses ordinary ITU-metal
reflection, while the archived custom solver disabled metal reflections.
Consequently its result is not an attempted reproduction of those maps.

For Sionna's supported scene loading and material behavior, see
[Introduction to Sionna RT](https://nvlabs.github.io/sionna/rt/tutorials/Introduction.html)
and the [radio-material API](https://nvlabs.github.io/sionna/rt/api/radio_materials.html).
The [material supplement](RADIO_MATERIALS.md) explains the absorber and biological
material assumptions, and the limitations on transmission through detailed solids.

## Repeatability and validation

With unchanged saved geometry, control values and catalog, repeated exports
produce identical XML, PLY and metadata bytes. The exporter restores scene and
visibility state and does not save the `.blend`.

Run the repository's relevant local checks:

```powershell
python -m unittest discover -s tests -v
python -m iat_lab verify
& $blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_parametric.py
& $blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_export.py
& $blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_smoke.py
```

The tests cover baseline-position preservation, transform behavior, absorber
attachment/toggles, shared and independent assemblies, all four variants,
hidden-wall inclusion, wall slab/opening geometry, export determinism and
visibility restoration. See [validation results](VALIDATION.md).
