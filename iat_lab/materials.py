"""Frequency-aware material catalog; no Blender or Sionna import required."""

import json
import math
import re
from pathlib import Path

EPSILON_0 = 8.8541878128e-12
REFERENCE_HZ = 23.8e9
ITU_SOURCE = "https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.2040-4-202509-I!!PDF-E.pdf"
SIONNA_SOURCE = "https://nvlabs.github.io/sionna/rt/api/radio_materials.html"

# P.2040-4 coefficients for the band containing this lab's 23.8 GHz carrier.
# epsilon' = a*f_GHz**b; sigma = c*f_GHz**d, in S/m.
ITU = {
    "concrete": (5.24, 0, 0.0462, 0.7822, 1, 100),
    "metal": (1, 0, 1e7, 0, 1, 100),
    "wood": (1.99, 0, 0.0047, 1.0718, 0.001, 100),
    "plywood": (2.71, 0, 0.33, 0, 1, 40),
    "chipboard": (2.58, 0, 0.0217, 0.78, 1, 100),
    "glass": (6.31, 0, 0.0036, 1.3394, 0.1, 100),
}

CUSTOM = {
    "iat_absorber_proxy": {
        "relative_permittivity": 1.4800000190734863,
        "conductivity_s_m": 0.03320573270320892,
        "thickness_m": 0.10000000149011612,
        "status": "uncharacterized_RF_absorber_archived_proxy",
        "note": "Archived ceiling-board-like proxy, NOT measured RF absorber properties. Manufacturer and product are unknown.",
        "source": "assets/baseline/RIS_Full_Background_Close_Pair.blend: RF 4 absorber proxy",
    },
    "iat_leaf": {
        "relative_permittivity": 13.698127404866636,
        "conductivity_s_m": 18.465524003889673,
        "thickness_m": 0.0003000000142492354,
        "status": "archived_prior_not_measured",
        "note": "Fixed leaf prior from the archived protocol, valid here only at 23.8 GHz; no species/moisture fit is claimed.",
        "source": "data/embedded/PROTOCOL.json: materials.leaf",
    },
    "iat_polypropylene": {
        "relative_permittivity": 2.200000047683716,
        "conductivity_s_m": 0.00582583574578166,
        "thickness_m": 0.003000000026077032,
        "status": "archived_polypropylene_assumption",
        "note": "Pot/saucer polypropylene assumption, not an identification or measurement of the real pot.",
        "source": "data/embedded/PROTOCOL.json: materials.pot",
    },
}

ALIASES = {
    "RF 0 chipboard": "itu_chipboard", "RF 1 plywood": "itu_plywood",
    "RF 2 concrete": "itu_concrete", "RF 3 metal": "itu_metal",
    "RF 4 absorber proxy": "iat_absorber_proxy", "RF 5 wood": "itu_wood",
    "RF 6 glass": "itu_glass", "Fixed_PP_pot_assumption": "iat_polypropylene",
    "Wood_visual_only": "itu_wood",
    **{f"Fixed_leaf_{i}": "iat_leaf" for i in range(5)},
}


def catalog(frequency_hz=REFERENCE_HZ):
    if not math.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("Frequency must be finite and positive")
    f = frequency_hz / 1e9
    records = {}
    for name, (a, b, c, d, lo, hi) in ITU.items():
        if not lo <= f <= hi:
            raise ValueError(f"{name}: catalog coefficients are only specified for {lo}..{hi} GHz")
        records[f"itu_{name}"] = {
            "model": "itu", "itu_type": name, "relative_permittivity": a * f**b,
            "conductivity_s_m": c * f**d, "coefficients_abcd": [a, b, c, d],
            "valid_frequency_ghz": [lo, hi], "thickness_m": 0.1,
            "status": "ITU_generic_class_not_a_lab_measurement", "source": ITU_SOURCE,
        }
    for name, entry in CUSTOM.items():
        if frequency_hz != REFERENCE_HZ:
            raise ValueError("Custom leaf, pot and absorber priors are defined only at 23.8 GHz")
        records[name] = {"model": "custom", **entry}
    for entry in records.values():
        entry.update(frequency_hz=frequency_hz, relative_permeability=1.0,
                     scattering_coefficient=0.0, xpd_coefficient=0.0)
        entry["loss_tangent"] = entry["conductivity_s_m"] / (
            2 * math.pi * frequency_hz * EPSILON_0 * entry["relative_permittivity"])
    records["iat_ideal_absorber"] = {
        "model": "ideal_absorber", "status": "ideal_limiting_case_not_dielectric_measurement",
        "relative_permittivity": None, "conductivity_s_m": None, "loss_tangent": None,
        "frequency_hz": frequency_hz, "source": SIONNA_SOURCE,
        "note": "Absorbs all incident energy. No transmission or reflected/scattered path; casts a radio shadow.",
    }
    return records


def write_catalog(path, frequency_hz=REFERENCE_HZ):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "frequency_hz": frequency_hz, "materials": catalog(frequency_hz),
               "excluded_uncharacterized": ["soil", "ties", "veins", "visual guides"],
               "absorber_product": "RF absorber; manufacturer/model not supplied"}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def load_catalog(path=None, frequency_hz=REFERENCE_HZ):
    if path is None:
        return catalog(frequency_hz)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("frequency_hz") != frequency_hz:
        raise ValueError("Material catalog schema/frequency does not match the export")
    records = data["materials"]
    for name, record in records.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) or not record.get("status") or not record.get("source"):
            raise ValueError("Every material needs a name, status and source")
        if record["model"] not in {"itu", "custom", "ideal_absorber"}:
            raise ValueError(f"Unsupported material model: {name}")
        if record.get("frequency_hz", frequency_hz) != frequency_hz:
            raise ValueError(f"Frequency qualification differs from catalog: {name}")
        if record["model"] == "ideal_absorber":
            continue
        for key, lower in [("relative_permittivity", 1), ("conductivity_s_m", 0), ("thickness_m", 0)]:
            value = record[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < lower:
                raise ValueError(f"Invalid {key} on {name}")
        if record["thickness_m"] <= 0:
            raise ValueError(f"Slab thickness must be positive: {name}")
        for key in ("scattering_coefficient", "xpd_coefficient"):
            if not 0 <= record.get(key, 0) <= 1:
                raise ValueError(f"Invalid {key} on {name}")
        if record["model"] == "itu":
            a, b, c, d, lo, hi = ITU[record["itu_type"]]
            f = frequency_hz / 1e9
            if not lo <= f <= hi:
                raise ValueError(f"Frequency outside qualified ITU band: {name}")
            reference = {"relative_permittivity": a * f**b, "conductivity_s_m": c * f**d}
            for key in ("relative_permittivity", "conductivity_s_m"):
                if not math.isclose(record[key], reference[key], rel_tol=1e-6):
                    raise ValueError(f"{name}: ITU values must match its model. Use model='custom' for measured overrides.")
        record["loss_tangent"] = record["conductivity_s_m"] / (
            2 * math.pi * frequency_hz * EPSILON_0 * record["relative_permittivity"])
    return records
