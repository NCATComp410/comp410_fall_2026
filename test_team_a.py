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

    def test_us_passport(self):
        """Test US_PASSPORT functionality"""
        valid_passports = [
            "Passport number: P12345678",
            "US passport ID is AB1234567",
            "Passport card no. 123456789",
        ]
        invalid_passports = [
            "Passport number: 12345678",
            "US passport ID is ABC12345",
            "Passport no. XX123456",
        ]

        for text in valid_passports:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['US_PASSPORT'])
                matches = [result for result in results if result.entity_type == 'US_PASSPORT']
                self.assertTrue(matches, f'Expected a US_PASSPORT match in: {text}')

        for text in invalid_passports:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['US_PASSPORT'])
                matches = [result for result in results if result.entity_type == 'US_PASSPORT']
                self.assertFalse(matches, f'Expected no US_PASSPORT match in: {text}')


if __name__ == '__main__':
    unittest.main()
