import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bankdata_pipeline.dataset import KEY_COLUMNS, extract_fields


class ExtractFieldsTests(unittest.TestCase):
    def test_parses_single_line_values(self):
        payload = [
            "Naam: Example BV",
            "IBAN: NL00ABNA0123456789",
            "BIC: ABNANL2A",
            "Omschrijving: Test",
            "SEPA Overboeking",
        ]
        result = extract_fields(payload)
        self.assertEqual(result["Naam"], "Example BV")
        self.assertEqual(result["IBAN"], "NL00ABNA0123456789")
        self.assertEqual(result["BIC"], "ABNANL2A")
        self.assertEqual(result["Omschrijving"], "Test")
        self.assertEqual(result["PaymentMethod"], "SEPA Overboeking")

    def test_supports_multi_line_values(self):
        payload = [
            "Omschrijving: Line 1",
            "Line 2",
            "Naam: Multi",
        ]
        result = extract_fields(payload)
        self.assertEqual(result["Omschrijving"], "Line 1 Line 2")
        self.assertEqual(result["Naam"], "Multi")

    def test_missing_keys_return_none(self):
        result = extract_fields([])
        for key in KEY_COLUMNS:
            self.assertIsNone(result[key])


if __name__ == "__main__":
    unittest.main()
