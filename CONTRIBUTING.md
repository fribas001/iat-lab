# Contributing

Work from a checkout with Python 3.11+ and Blender 5.2.3 LTS. No additional
Python packages are needed for the supplied validation commands.

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

Generated node libraries, render outputs and Blender backup files are ignored.
The two initial `.blend` copies share identical bytes, so Git stores one content
blob. Git LFS is not required for this approximately 12 MB starting model.
