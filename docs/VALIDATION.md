# Validation

Validated on 10 November 2026 with Python 3.12.10 and Blender 5.2.3 LTS on Windows.
The optional environment used Sionna RT 2.2.0, Mitsuba 3.9.1, Dr.Jit 1.5.0
and the `llvm_ad_mono_polarized` CPU backend.

## Parametric model and materials

- The protected `.blend` and eight reference files retain their manifest hashes.
- The working model has 19 assembly controllers and 44 node groups.
- Default mesh vertices match original world positions to a maximum absolute
  coordinate difference of **1.79e-7 m** (under 0.2 micrometres).
- Tests exercise wall translation, rotation and size; attached absorber position,
  independent depth and switches; the optional fourth panel; RIS, scanner,
  receiver-grid and plant movement; and independent RIS stand behavior.
- Four scenes retain cameras and resolvable dependencies. All node groups
  survive extraction and append with matching metadata.
- Each scene's results parent has distinct Paths and Heatmap children, retaining
  its original result objects. The working model has 21 collections.
- Ten standard-library tests pass, covering input integrity, material reference
  values, frozen-frequency handling, catalog overrides and explicit absorber status.
- Matching camera renders were reviewed; see the
  [layout comparison](PARAMETRIC_ENVIRONMENT.md#default-layout-comparison).
- Native Cycles interior previews use the complete room envelope, procedural
  optical finishes and repeatable camera/light presets. Image settings and
  source/model hashes accompany the PNGs; see [preview workflow](PREVIEWS.md).

## Export and runtime

- Repeated exports have identical XML, PLY and metadata bytes.
- All four variants export successfully: 31 default shapes with plants, 25 without.
  Optional absorber enablement changes the expected count.
- Hidden RF walls are included; presentation geometry and archived results are excluded.
- Six room slabs export as single surfaces. The doorway retains its opening and
  expected wall area. Export restores presentation visibility afterwards.
- RIS and receiver exports retain 508 cells and 2,300 scanner points.
- Absorber proxy/ideal selection and disabled-anchor handling are checked.
- Sionna RT 2.2.0 loads both the proxy and ideal-absorber exports (31 shapes),
  verifying material types and the applicable permittivity, conductivity and
  thickness at 23.8 GHz. The ideal option uses the documented frequency-update
  compatibility adapter.
- Both options completed an ordinary-path sanity trace with finite coefficients and delay
  array shape `(1, 1, 7)`: isotropic antennas, 10 dBm TX, depth 2, 10,000 samples,
  seed 42, direct/specular paths only.

The Windows sandbox emitted nonfatal Blender thumbnail/extension-cache and
Dr.Jit disk-cache warnings. Saves, in-memory JIT evaluation and tests completed.
No protected baseline or extracted reference record was changed.

## Limits

These checks establish software behavior, geometry preservation and runtime
compatibility. They do not identify the real absorber, characterize leaf/pot
materials, survey the room, reproduce active-RIS propagation or validate a new
result against measurements. The example disables refraction through detailed solids.

GitHub Actions runs standard-library tests and protected-input verification.
Blender and Sionna integration checks were run locally; they are not currently
installed or run by the GitHub workflow.
