"""Unit test file for team _3"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__3(unittest.TestCase):
    """Test team _3 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_it_driver_license(self):
        """Test IT_DRIVER_LICENSE functionality"""

    def test_it_fiscal_code(self):
        """Test IT_FISCAL_CODE functionality"""

    def test_it_identity_card(self):
        """Test IT_IDENTITY_CARD functionality"""

    def test_it_passport(self):
        """Test IT_PASSPORT functionality"""
        positive_cases = [
            ("Passaporto: AB1234567", 12, 21),
            ("Documento: XZ0000001", 11, 20),
        ]
        for text, expected_start, expected_end in positive_cases:
            with self.subTest(text=text):
                results = analyze_text(text, ["IT_PASSPORT"])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, "IT_PASSPORT")
                self.assertEqual(results[0].start, expected_start)
                self.assertEqual(results[0].end, expected_end)

        invalid_cases = [
            "AB123456",
            "A12345678",
            "ABC1234567",
            "AB12345678",
            "AB12345X7",
        ]
        for text in invalid_cases:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, ["IT_PASSPORT"]), [])

    def test_it_vat_code(self):
        """Test IT_VAT_CODE functionality"""


if __name__ == '__main__':
    unittest.main()
