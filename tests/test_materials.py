import json
import math
import unittest
from unittest.mock import patch

from iat_lab.materials import ALIASES, REFERENCE_HZ, catalog, load_catalog


class MaterialCatalogTests(unittest.TestCase):
    def test_itu_reference_values_at_lab_frequency(self):
        records = catalog()
        # Independent reference values stored in the original lab model at 23.8 GHz.
        for name, epsilon, sigma in [
            ("concrete", 5.24, 0.5513158441), ("metal", 1, 1e7),
            ("wood", 1.99, 0.1404471844), ("chipboard", 2.58, 0.2571519315),
            ("plywood", 2.71, 0.33), ("glass", 6.31, 0.2512405813),
        ]:
            record = records["itu_" + name]
            self.assertAlmostEqual(record["relative_permittivity"], epsilon, places=6)
            self.assertTrue(math.isclose(record["conductivity_s_m"], sigma, rel_tol=1e-6))

    def test_uncharacterized_absorber_is_not_an_itu_material(self):
        key = ALIASES["RF 4 absorber proxy"]
        self.assertEqual(catalog()[key]["model"], "custom")
        self.assertIn("uncharacterized", catalog()[key]["status"])
        self.assertIsNone(catalog()["iat_ideal_absorber"]["relative_permittivity"])

    def test_frozen_custom_priors_are_not_silently_extrapolated(self):
        for frequency in [0, float("nan"), 28e9]:
            with self.assertRaises(ValueError):
                catalog(frequency)

    def test_pot_loss_tangent_consistency(self):
        self.assertAlmostEqual(catalog(REFERENCE_HZ)["iat_polypropylene"]["loss_tangent"], 0.002, places=6)

    def test_explicit_custom_catalog_values_are_applied(self):
        payload = {"schema_version": 1, "frequency_hz": REFERENCE_HZ, "materials": catalog()}
        payload["materials"]["iat_leaf"]["relative_permittivity"] = 12.0
        with patch("iat_lab.materials.Path.read_text", return_value=json.dumps(payload)):
            result = load_catalog("test-catalog.json")
        self.assertEqual(result["iat_leaf"]["relative_permittivity"], 12.0)
        self.assertGreater(result["iat_leaf"]["loss_tangent"], catalog()["iat_leaf"]["loss_tangent"])

    def test_itu_label_cannot_hide_custom_dielectric_values(self):
        payload = {"schema_version": 1, "frequency_hz": REFERENCE_HZ, "materials": catalog()}
        payload["materials"]["itu_wood"]["relative_permittivity"] = 99
        with patch("iat_lab.materials.Path.read_text", return_value=json.dumps(payload)):
            with self.assertRaisesRegex(ValueError, "ITU values must match"):
                load_catalog("test-catalog.json")


if __name__ == "__main__":
    unittest.main()
