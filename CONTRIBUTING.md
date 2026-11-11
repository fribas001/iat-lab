# Contributing

Work from a checkout with Python 3.11+ and Blender 5.2.3 LTS. No additional
Python packages are needed for the standard-library and Blender checks.
Optional Sionna checks use a separate environment with `requirements-sionna.txt`.

Keep reusable logic in `iat_lab/`; scripts should parse arguments and call that
API. Import `bpy` only in Blender-specific modules. Future Blender UI operators
should call the same API as scripts.

Keep `assets/baseline/` and `data/` as the original reference. Edit the working
model under `scenes/`. When intentionally adopting a new baseline, retain the old
version in Git and update the provenance and manifest together. Do not update
hashes merely to silence an unexpected verification failure.

For a model change, describe the scene, objects, dimensions or controls changed.
Attach a before/after view when the change is visual. For code changes, run:

```powershell
python -m unittest discover -s tests -v
python -m iat_lab verify
```

Run the Blender smoke command from the README for changes to models or Blender
adapters. It checks scene availability and a node-library extraction/append round
trip. It does not establish electromagnetic correctness.

For environment/export changes, also run `tests/blender_parametric.py` and
`tests/blender_export.py` with Blender, as shown in [Sionna export](docs/SIONNA_EXPORT.md).
Preserve the baseline and rebuild to a new file when testing graph changes.
Material catalog edits need a frequency-qualified source and status.

Generated node libraries, render outputs and Blender backup files are ignored.
The initial two `.blend` copies shared one Git blob; the parametric working model
now has its own versioned content. Generated exports belong under `runs/` or `build/`.
