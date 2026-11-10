# Model provenance

The repository starts from the user-selected file:

```text
RIS_Repository_Structure_Update_2026-11-08/blender/archive/RIS_Full_Background_Close_Pair.blend
```

The original was copied on 10 November 2026 to
`assets/baseline/RIS_Full_Background_Close_Pair.blend` and
`scenes/IAT_Lab.blend`. The initial copies are byte-for-byte identical to the
selected file. `iat-lab.json` records its SHA-256 and size.

Blender 5.2.3 LTS loaded the model with factory startup and automatic script
execution disabled. Inspection did not save or modify either copy. Four scenes,
two Geometry Nodes groups and seven embedded text blocks were found. Text
exports preserve Blender's UTF-8 text representation and have individual hashes.

The model is the historical full-lab presentation scene. Its embedded results,
older plants and background are not substitutes for the surrounding project's
later final-paper study inputs. This repository provides the model and tooling
for subsequent lab-design improvements, not a fresh validation of those results.

The source archive's rights note described collaborative research data and
separate third-party components. Only the selected `.blend` and its own embedded
records are included here; the surrounding solver, studies and measurements
have not been imported into this repository.
