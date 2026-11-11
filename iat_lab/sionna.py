"""Optional Sionna RT adapter. Importing this module does not load Sionna."""

import json
from pathlib import Path


def _frequency_independent():
    """A perfect absorber has no frequency-dependent dielectric parameters."""


def load_export(directory):
    """Load an exported scene and set its qualified carrier frequency.

    Sionna 2.2.0's Scene.frequency setter calls frequency_update on every
    material, while AbsorberRadioMaterial omits that method. Attach a no-op
    only to these loaded, frequency-independent instances. The installed
    library and its classes are not modified.
    """
    import sionna.rt as rt

    if rt.__version__ != "2.2.0":
        raise RuntimeError(f"This adapter is validated with sionna-rt==2.2.0; found {rt.__version__}")
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    scene = rt.load_scene(str((directory / "scene.xml").resolve()), merge_shapes=False)
    for material in scene.radio_materials.values():
        if isinstance(material, rt.AbsorberRadioMaterial) and not hasattr(material, "frequency_update"):
            material.frequency_update = _frequency_independent
    scene.frequency = manifest["frequency_hz"]
    return scene
