"""Validate an export with Sionna RT 2.2; optionally run an ordinary-path sanity trace.

This does not implement the archived RIS two-hop solver or reproduce its results.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import sionna.rt as rt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iat_lab.sionna import load_export

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
parser.add_argument("--trace", action="store_true")
args = parser.parse_args()
if rt.__version__ != "2.2.0":
    raise RuntimeError(f"Validation targets sionna-rt==2.2.0; found {rt.__version__}")
manifest = json.loads((args.directory / "manifest.json").read_text(encoding="utf-8"))
scene = load_export(args.directory)
assert len(scene.objects) == len(manifest["objects"])
for obj in scene.objects.values():
    material = obj.radio_material
    expected = manifest["material_instances"][material.name]
    if expected["model"] == "ideal_absorber":
        assert isinstance(material, rt.AbsorberRadioMaterial)
        continue
    np.testing.assert_allclose(np.array(material.relative_permittivity), expected["relative_permittivity"], rtol=2e-6)
    np.testing.assert_allclose(np.array(material.conductivity), expected["conductivity_s_m"], rtol=2e-6)
    np.testing.assert_allclose(np.array(material.thickness), expected["thickness_m"], rtol=2e-6)
print(f"PASS: Sionna {rt.__version__} loaded {len(scene.objects)} objects and verified materials at {manifest['frequency_hz'] / 1e9:g} GHz")
if args.trace:
    if any(position is None for position in manifest["anchors_m"].values()):
        raise ValueError("Enable both TX assembly and Target marker to run the trace example")
    # Isotropic antennas exercise geometry/material loading, not the measured horn pattern.
    scene.tx_array = rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                   horizontal_spacing=0.5, pattern="iso", polarization="V")
    scene.rx_array = rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                   horizontal_spacing=0.5, pattern="iso", polarization="V")
    scene.add(rt.Transmitter(name="tx", position=manifest["anchors_m"]["tx"], power_dbm=10))
    scene.add(rt.Receiver(name="target", position=manifest["anchors_m"]["target"]))
    paths = rt.PathSolver()(scene=scene, max_depth=2, samples_per_src=10000, seed=42,
                            los=True, specular_reflection=True, diffuse_reflection=False,
                            refraction=False, diffraction=False)
    assert all(np.isfinite(np.array(component)).all() for component in paths.a)
    print("PASS: finite ordinary-path sanity trace; delay array shape:", np.array(paths.tau).shape)
    print("Scope: isotropic antennas, no RIS scattering, no refraction; not a reproduction of archived results.")
