"""Unit test file for team _1"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__1(unittest.TestCase):
    """Test team _1 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_es_nie(self):
        """Test ES_NIE functionality"""

    def test_es_nif(self):
        """Test ES_NIF functionality"""
        positive_cases = [
            ("Mi NIF es 12345678Z", "12345678Z"),
            ("NIF: 87654321X", "87654321X"),
            ("Tax ID: 12345678Z", "12345678Z"),
            ("NIF: 87654321-X", "87654321-X"),
        ]

        for text, expected_value in positive_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["ES_NIF"])
                self.assertTrue(
                    any(
                        match.entity_type == "ES_NIF"
                        and text[match.start:match.end] == expected_value
                        for match in matches
                    ),
                    f"Expected ES_NIF match {expected_value!r} in: {text}",
                )

        negative_cases = [
            "NIF: 1234567Z",
            "NIF: 123456789Z",
            "The code is 12345678",
            "Order number: 12345678A",
            "Tax ID: 1234567A",
        ]

        for text in negative_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["ES_NIF"])
                self.assertFalse(any(match.entity_type == "ES_NIF" for match in matches),
                                 f"Unexpected ES_NIF match found in: {text}")

    def test_fi_personal_identity_code(self):
        """Test FI_PERSONAL_IDENTITY_CODE functionality"""

    def test_iban_code(self):
        """Test IBAN_CODE functionality"""

    def test_ip_address(self):
        """Test IP_ADDRESS functionality"""


if __name__ == '__main__':
    unittest.main()
