# Radio-material supplement

The working model assigns canonical radio-material keys to its physical meshes.
Blender preview colors are separate from the electrical parameters. The
reproducible exporter writes explicit Sionna RT 2.2 material definitions, rather
than relying only on material-name recognition.

The editable catalog is [`config/radio_materials.json`](../config/radio_materials.json).
It records model type, frequency, permittivity, conductivity, thickness, loss
tangent, provenance and qualification status. The default carrier is **23.8 GHz**.
The original values remain available in the protected `.blend` and embedded
protocol; no new laboratory material measurements have been performed.

## Values at 23.8 GHz

Conductivity is in S/m; relative permittivity and loss tangent are dimensionless.
Numbers here are rounded; the JSON catalog retains full precision.

| Blender / catalog key | Typical use | Real relative permittivity | Conductivity | Loss tangent | Basis |
| --- | --- | ---: | ---: | ---: | --- |
| `itu_concrete` | Four walls, floor, ceiling | 5.24 | 0.551316 | 0.079463 | Generic ITU concrete class |
| `itu_metal` | Scanner rails, supports, pipes, frame, tripod | 1 | 10,000,000 | 7,552,565 | ITU conductive-metal model; the large loss tangent is not a low-loss-dielectric approximation |
| `itu_wood` | Wooden door; plant wood preview parts | 1.99 | 0.140447 | 0.053303 | Generic ITU wood class; plant wood remains RF-excluded |
| `itu_plywood` | Blocker board and scanner/table members originally labeled plywood | 2.71 | 0.33 | 0.091968 | Generic ITU plywood class |
| `itu_chipboard` | RIS backing board and originally labeled chipboard members | 2.58 | 0.257152 | 0.075277 | Generic ITU chipboard class |
| `itu_glass` | Light-fixture diffusers | 6.31 | 0.251241 | 0.030071 | Generic ITU glass class |
| `iat_absorber_proxy` | Wall and blocker RF-absorber meshes | 1.48 | 0.033206 | 0.016945 | **Uncharacterized archived proxy**, not measured RF-absorber data |
| `iat_leaf` | Both plants' leaf surfaces | 13.698127 | 18.465524 | 1.018110 | Archived fixed leaf prior, not a new species/moisture measurement |
| `iat_polypropylene` | Pots and saucers | 2.20 | 0.005826 | 0.002000 | Archived polypropylene assumption; real pot composition unconfirmed |
| `iat_ideal_absorber` | Optional replacement at export | N/A | N/A | N/A | Perfect-absorption limiting case, not a dielectric estimate |

The six ITU entries use the band of the frequency-dependent models containing
23.8 GHz. These generic classes come from
[ITU-R P.2040-4, Table 3](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.2040-4-202509-I!!PDF-E.pdf)
and are implemented by Sionna's `ITURadioMaterial`. Their assignment to a
particular lab object is a modelling choice; it does not identify the actual
wall mix, wood species, board grade, metal alloy or glass product.

The five leaf preview materials are named `iat_leaf_0` through `iat_leaf_4`.
Their `iat_radio_material` property maps them all to `iat_leaf`. Thus the
export can retain different preview colors without inventing different leaf
electrical properties.

## Frequency and dielectric convention

For the catalog's ITU bands, with frequency `f_GHz`:

```text
epsilon_real = a * f_GHz**b
sigma_S_per_m = c * f_GHz**d
epsilon_complex = epsilon_real - j * sigma / (2*pi*f_Hz*epsilon_0)
tan_delta = sigma / (2*pi*f_Hz*epsilon_0*epsilon_real)
```

The sign above uses an `exp(+j*omega*t)` convention. Sionna accepts real relative
permittivity and conductivity; do not pass a negative imaginary part as a
conductivity. The built-in dielectric model assumes relative permeability 1.
Its optical display color does not determine its radio response.
[Sionna radio-material documentation](https://nvlabs.github.io/sionna/rt/api/radio_materials.html)

The current custom leaf, pot and absorber priors are frozen at 23.8 GHz. The
catalog API rejects other frequencies rather than silently extrapolating them.
Supporting another carrier requires an explicit frequency model or new
frequency-qualified custom data. ITU materials themselves retain their built-in
frequency dependence when loaded in Sionna.

## RF absorber: what is known and what is missing

The user identified the wall treatment as **RF absorber**, but its manufacturer,
model, composition and measured complex material properties are not yet known.
The archived `(1.48, 0.0332057 S/m)` pair closely matches the ITU ceiling-board
class at 23.8 GHz. It is retained only under the explicit custom name
`iat_absorber_proxy`; it is not relabeled as a measured foam material.

Commercial RF absorbers vary in loading, geometry and treatment. For example,
[ETS-Lindgren's EHP datasheet](https://media.ets-lindgren.com/wp-content/uploads/2026/01/datasheet-absorber-EHP_rev2.3.pdf)
describes carbon-impregnated urethane pyramids and specifies reflectivity
performance. That is an example of product-specific documentation, not an
identification of the lab's absorber. A reflectivity number alone does not
uniquely determine bulk permittivity, conductivity and effective thickness.

Two explicit export choices are available:

| Option | Interpretation |
| --- | --- |
| `--absorber-model archived-proxy` | Default. Uses the saved dielectric proxy and 0.1 m slab assumption. Preserves its provenance, without claiming physical absorber accuracy. |
| `--absorber-model ideal` | Uses Sionna `AbsorberRadioMaterial`. It casts a shadow and absorbs incident energy without generating reflected/scattered paths. Useful as an ideal comparison, not as a measured material. |

A characterized replacement should supply the product identity, frequency band,
complex permittivity or equivalent conductivity/loss, effective slab thickness,
and source/measurement conditions. If the absorber has magnetic loading, a
nonmagnetic `RadioMaterial` may not be sufficient. The proxy and ideal options
are hypotheses to compare, not an uncertainty interval proven to bound the lab.

## Thickness and surface geometry

Sionna's finite-slab material already accounts for the slab's internal effects
at a surface interaction. Its recommended wall representation is a single
surface with a material thickness. The exporter therefore selects the interior
faces of the four walls, floor and ceiling, retaining the door opening, and
derives their thickness from the edited geometry. It does not send both sides
of these room slabs as two independent transmission layers.
[Sionna slab-model definition](https://nvlabs.github.io/sionna/rt/api/radio_materials.html#sionna.rt.RadioMaterial)

Other detailed objects retain their original topology. Leaf and pot meshes are
tagged in the source as midsurfaces; the archived thicknesses are 0.0003 m and
0.003 m respectively. Other solids and absorber pyramids are not automatically
converted to a rigorously equivalent single-surface model. The supplied path
example therefore disables refraction. Prepare and validate those surfaces
before enabling transmission in a study.

For non-room objects, the catalog's `thickness_m` is the default. An explicit
object custom property `iat_slab_thickness_m` overrides it. This is an EM model
parameter, separate from a Geometry Nodes display size. Room-slab thickness is
computed from the actual control transform instead.

## Editing the material catalog

The canonical Blender materials also have [procedural optical finishes](PREVIEWS.md#procedural-surface-finishes)
for Cycles/Eevee previews. Wood grain, concrete mottling, color, optical roughness
and bump normals do not alter the catalog's permittivity, conductivity, scattering
coefficients or exported mesh. The exporter reads the radio key/catalog, not
the Principled BSDF's appearance.

1. Edit `config/radio_materials.json`, preserving the carrier and provenance fields.
2. Keep `model: "itu"` for standard ITU classes. Their electrical values are checked
   against the specified ITU type. For measured/custom values use `model: "custom"`.
3. Enter real permittivity (at least 1), nonnegative conductivity, positive
   thickness, status and source. Loss tangent is recalculated on load.
4. Assign the catalog key through a Blender material's `iat_radio_material`
   custom property. Existing canonical assignments are already set up.
5. Export again into a fresh directory. The CLI reads this catalog by default;
   `--materials path/to/catalog.json` selects another qualified catalog.

To synchronize the embedded catalog descriptions in a freshly built model,
rebuild to a new output file. An existing model's serialized material record is
informational; the selected export catalog is authoritative for RF parameters.

Soil, ties, veins and presentation guides have no newly invented RF parameters.
They remain excluded from RF export. A wood material on a visible plant part
does not override that object's exclusion. Adding any such object requires an
explicit inclusion choice and a supported catalog key; missing RF materials
cause export to fail rather than become an implicit default.
