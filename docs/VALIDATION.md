# Initial validation

Validated on 10 November 2026 with Python 3.12.10 and Blender 5.2.3 LTS on Windows.

- SHA-256 matches between the supplied source, protected baseline and working model.
- All eight extracted reference files match the manifest.
- Four Python tests pass: baseline tampering, editable working file, contained
  project paths and importing the package without Blender.
- Blender opens all four scene variants with their cameras and no external file
  dependencies reported by the inventory.
- The copied scene's object, collection, node and embedded-text metadata match
  the baseline inventory.
- The two node groups can be extracted into a library and appended into an empty
  Blender session with matching graph metadata and material references.

The Blender run printed a warning that its user extension-cache file was not
writable in the execution sandbox; the smoke test completed successfully.
No source or working `.blend` was saved by validation.

GitHub Actions runs the standard-library tests and input-integrity verification.
The Blender smoke test is run locally using the README command; it is not yet
automated in CI. Editable package installation was not tested in a new virtual
environment. No propagation solver or scientific model validation was run.
