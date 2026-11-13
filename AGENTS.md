# IAT Lab repository instructions

## Start here

Read README.md, CONTRIBUTING.md and docs/ARCHITECTURE.md. For scene changes read
docs/SCENE_GUIDE.md and docs/PARAMETRIC_ENVIRONMENT.md; for RF/export changes read
docs/SIONNA_EXPORT.md, docs/RADIO_MATERIALS.md and docs/LAB_REFERENCES.md.
The editable model is scenes/IAT_Lab.blend.

## Architecture and protected inputs

Keep reusable logic in iat_lab/ and scripts as thin API entry points. Keep bpy
imports in Blender-specific modules and Sionna optional and external. The project
API must import outside Blender. Preserve the versioned Python definitions of
environment graphs and the original model's inherited path-display graphs.

Protect assets/baseline/ and data/ as original references. Test rebuilds in a new
file; edit the working scene rather than overwriting the original. An intentional
baseline revision must retain the prior version and update provenance and the
manifest together. Never change hashes merely to suppress verification failures.
Keep all scene variants, shared-object behavior and documented visibility rules.

Preserve stable controller/attribute names, types, units and default layouts.
Record material sources, frequency applicability and qualification status.
Keep RF inclusion separate from presentation visibility, and preserve deterministic
world-metre exports, slab policy and per-material mesh assignments.

## Runtime, outputs and evidence

Use the documented Python/Blender versions and requirements-sionna.txt for the
optional external runtime. Do not install Sionna into Blender or silently modify
installed packages or personal preferences. Use structured subprocess arguments
and hidden background processes on Windows.

Use new or empty output directories under runs/, build/ or renders/ as documented.
Keep generated libraries, exports, renders, backups, environments, credentials and
machine-local paths out of Git. The protected and working .blend files are
intentional versioned assets.

Archived path tubes and heatmaps remain historical results. Geometry edits do not
recompute them, and exporting RIS cells does not implement active RIS scattering.
Preserve the labels for absorber proxies and unresolved material assumptions.
Presentation-only work can reuse archived evidence; claims about changed RF
geometry require matching new calculations with recorded input/runtime hashes,
settings and limitations.

## Validation

For code or model changes, run from the repository root:

```text
python -m unittest discover -s tests -v
python -m iat_lab verify
```

Run tests/blender_smoke.py for model/Blender adapter changes. Environment/export
changes also require tests/blender_parametric.py and tests/blender_export.py,
using the factory-startup, disable-autoexec commands in docs/SIONNA_EXPORT.md.
Check the optional external Sionna loader when changing its adapter. Preserve the
source model and visibility state during inspection/export.

Include before/after views for visual changes. Inspect actual exits and outputs.
These checks establish specified software/data contracts, not calibrated RIS or
material accuracy. For documentation-only changes, verify paths and commands;
Blender renders and native RF jobs are unnecessary.

## Documentation and delivery

Update affected scene, material, export and validation guides with the change.
Keep instructions reproducible and report the environment, executed checks,
results and outstanding limitations. Preserve model/reference provenance and
the rights documented in docs/RIGHTS.md.

This is a public repository; include only assets with the documented redistribution
rights. Preserve published versions and use matching source commits and checksums
for authorized release artifacts. Push or publish within the user's authorized task.
