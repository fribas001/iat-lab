# Laboratory reference audit

On 10 November 2026, the owner supplied a local `01_RIS` archive for inspection.
It contains useful photographs, a room plan, model-derived schematics and older
geometry/material studies. This index records what was found; it does not
reclassify historical simulations or photo-based estimates as lab measurements.

## Published experimental layout reference

Hamed Radpour et al., *Reconfigurable Intelligent Surface for Industrial
Automation: mmWave Propagation Measurement, Simulation, and Control Algorithm
Requirements*, [arXiv:2402.04844v2](https://arxiv.org/abs/2402.04844v2), 2024.

The experiment provides a basis for some layouts used in this project:
**Figure 3** gives the testbed plan, **Figure 4** shows the apparatus with and
without direct-path blockage, and **Table I** specifies the single 127-element
RIS operating at 23.8 GHz. The arrangement combines a tripod-mounted horn,
RIS, absorber blocker and receiver on an XY positioning table.
[Read the experimental setup in the paper](https://arxiv.org/html/2402.04844v2#S4).

The repository combines that experimental reference with the supplied lab
photographs, room drawing and archived geometry. Its four-tile, 508-cell model
and plant configurations are project-specific extensions, not configurations
established by this single-RIS paper. The paper's layouts are a modeling
reference; measurement agreement is not implied by using them.

## Useful sources

Paths below are relative to the supplied archive. Four selected images are
copied under [assets/references](../assets/references/README.md), with source
paths, hashes and the original schematic captions. Other listed studies remain
external references.

| Source | Useful information | Interpretation |
| --- | --- | --- |
| `RIS_Journal_Revised_2026-10-07/deferred/original_figures/Lab_space.jpg` | Overall apparatus, blue absorber coverage, wooden scanner table and blocker, dark RIS backing | Photograph; useful for appearance and arrangement, not independent dimensions |
| `RIS_Case3_Photo_Shield_Tilt_2026-10-14/inputs/photo_high_resolution_plant_layout.jpg` | Plant pair, pots, support, scanner assembly and blocker | Photograph; exact experimental registration still needs confirmation |
| Same `inputs/` folder: `photo_no_plant_front.jpeg`, `photo_no_plant_side.jpeg`, `photo_horn_view.jpeg` | Complementary apparatus views | Useful for a later hardware-detail pass |
| `RIS_Journal_Revised_2026-10-07/deferred/original_figures/FB UG Raum U.046_page-0001l.jpg` | Dimensioned U.046 room plan, doorway and recess | Drawing evidence; dimensions are annotations, not quantities inferred from image pixels |
| `RIS_Model_Based_Schematics_2026-10-14/figures/03_Four_RIS_Case3.png` and `.svg` | Equal-scale model plan, saved route geometry, 508 cells and 2,300 receiver points | Derived from older saved meshes/configuration; use with `README_and_captions.txt` |
| `RIS_Photo_Geometry_Correction_2026-10-14/README.txt` | Scanner/table-height inconsistencies and alternative hypotheses | Diagnostic audit; neither proposed alternative is established as the measured layout |
| `RIS_Plant_Materials_2026-10-13/REPORT.txt` and `REPORT.html` | Prior leaf/wood/pot modeling choices and numerical controls | Historical assumptions and tests, not material characterization of this lab |

The earlier `RIS_Schematics_BW_2026-10-14` images are conceptual generated
illustrations. The later **Model_Based_Schematics** set is the better technical
reference: its authoring notes explicitly describe geometry extraction and
replace the earlier illustrations for technical use.

## What the plan supports

The drawing labels **341.0 cm** across the room, **518.5 cm** along one side,
**502.5 cm** along the other, and **H: 3.60 m**. Its upper edge shows a door/recess
arrangement, including a **98.0 cm** span. The working model uses the matching
nominal **3.41 × 5.185 × 3.60 m** rectangular envelope and a 0.98 m doorway.
The unequal side dimensions and recess detail mean this should remain described
as a simplified envelope, not an exact architectural reconstruction. The plan's
annotated 17.83 m² also differs from the simple rectangular model area.

No room or apparatus dimensions were changed during this audit. The saved
0.50 m support hypothesis, 0.96 m receiver plane and 1.44 m RIS center remain
model assumptions where already labeled; a photograph does not resolve the
scanner antenna phase center or the common height datum.

## Appearance and RF material evidence

The photographs support wood on the blocker/table, a dark RIS backing, blue
pyramidal absorbers and dark metal supports. The procedural preview finishes
use these cues. They do not identify the exact board construction, paint,
absorber formulation or optical calibration.

No absorber manufacturer/model or calibrated permittivity/conductivity was
identified in the inspected reference material. The source reflection audit
explicitly calls the board and absorber RF properties proxies. The
[radio-material qualification status](RADIO_MATERIALS.md) therefore remains
unchanged. The older material study is useful provenance for the leaf/pot
assumptions; it does not turn them into measured values.

## Repository inclusion

At the owner's explicit selection, the repository includes the lab overview
photo, plant-layout photo, U.046 room plan and model-derived four-RIS schematic.
Their image bytes are unchanged; [source notes and hashes](../assets/references/README.md)
identify each copy. Older study archives have not been imported. Original
reference images are kept separate from native [Cycles previews](PREVIEWS.md)
so their roles remain clear.
