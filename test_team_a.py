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
        # Positive test: generic format
        text = "My driver license number is D1234567"
        results = analyze_text(text, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, 'US_DRIVER_LICENSE')

        # Positive test: Florida format
        text_fl = "Her Florida driver license number is S123456789012"
        results_fl = analyze_text(text_fl, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_fl), 1)
        self.assertEqual(results_fl[0].entity_type, 'US_DRIVER_LICENSE')

        # Negative test: no license number in the text
        text_neg = "The weather is sunny and I went to the park today"
        results_neg = analyze_text(text_neg, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_neg), 0)

        # Negative test: short number that is not a license
        text_neg2 = "My order number is 12"
        results_neg2 = analyze_text(text_neg2, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_neg2), 0)

    def test_us_itin(self):
        """Test US_ITIN functionality"""

    def test_us_passport(self):
        """Test US_PASSPORT functionality"""


if __name__ == '__main__':
    unittest.main()