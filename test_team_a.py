"""Unit test file for team _a"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__a(unittest.TestCase):
    """Test team _a PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_url(self):
        """Test URL functionality"""

    def test_us_bank_number(self):
        """Test US_BANK_NUMBER functionality"""

    def test_us_driver_license(self):
        """Test US_DRIVER_LICENSE functionality"""

    def test_us_itin(self):
        """Test US_ITIN functionality"""
        valid_cases = [
            ("ITIN: 900-50-1234", "900-50-1234"),
            ("Tax ID: 912-65-4321", "912-65-4321"),
            ("IRS number 923-70-1234", "923-70-1234"),
            ("My taxpayer ID is 934-88-5678", "934-88-5678"),
            ("ITIN 945-90-1234", "945-90-1234"),
            ("Tax ID 956-92-4321", "956-92-4321"),
            ("IRS ITIN: 967-94-1234", "967-94-1234"),
            ("ITIN 978-96-4321", "978-96-4321"),
            ("ITIN: 900501234", "900501234"),
        ]

        for text, expected_value in valid_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["US_ITIN"])
                self.assertTrue(
                    any(
                        match.entity_type == "US_ITIN"
                        and text[match.start:match.end] == expected_value
                        for match in matches
                    ),
                    f"Expected US_ITIN match {expected_value!r} in: {text}",
                )

        invalid_cases = [
            "ITIN: 900-49-1234",
            "ITIN: 900-66-1234",
            "ITIN: 900-69-1234",
            "ITIN: 900-89-1234",
            "ITIN: 900-93-1234",
            "ITIN: 800-50-1234",
            "ITIN: 900-5-1234",
            "SSN: 123-45-6789",
        ]

        for text in invalid_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["US_ITIN"])
                self.assertFalse(
                    any(match.entity_type == "US_ITIN" for match in matches),
                    f"Unexpected US_ITIN match found in: {text}",
                )

    def test_us_passport(self):
        """Test US_PASSPORT functionality"""


if __name__ == '__main__':
    unittest.main()
