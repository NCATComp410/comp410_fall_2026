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
        positive_cases = [
            "https://example.com",
            "www.example.com",
            "My site is example.com",
            "The URL https://sub.example.com/path?q=1 is here",
        ]
        negative_cases = [
            "This is not a url: example",
            "Visit localhost on port 8000",
            "The secret code is ABC123",
        ]

        for text in positive_cases:
            with self.subTest(text=text):
                results = analyze_text(text, [])
                self.assertTrue(
                    any(getattr(result, 'entity_type', None) == 'URL' for result in results),
                    f"Expected a URL match in: {text!r}"
                )

        for text in negative_cases:
            with self.subTest(text=text):
                results = analyze_text(text, [])
                self.assertFalse(
                    any(getattr(result, 'entity_type', None) == 'URL' for result in results),
                    f"Did not expect a URL match in: {text!r}"
                )

    def test_us_bank_number(self):
        """Test US_BANK_NUMBER functionality"""

    def test_us_driver_license(self):
        """Test US_DRIVER_LICENSE functionality"""

    def test_us_itin(self):
        """Test US_ITIN functionality"""

    def test_us_passport(self):
        """Test US_PASSPORT functionality"""


if __name__ == '__main__':
    unittest.main()
