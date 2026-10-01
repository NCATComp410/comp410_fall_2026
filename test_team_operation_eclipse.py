"""Unit test file for team operation_eclipse"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam_operation_eclipse(unittest.TestCase):
    """Test team operation_eclipse PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_credit_card(self):
        """Test CREDIT_CARD functionality"""
        positive_examples = [
            "My card number is 4111111111111111.",
            "Visa: 4111 1111 1111 1111",
        ]

        for sample_text in positive_examples:
            results = analyze_text(sample_text, ['CREDIT_CARD'])
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            self.assertTrue(any(result.entity_type == 'CREDIT_CARD' for result in results))

        negative_examples = [
            "My phone number is 1234567890.",
            "The fallback code is 1234 5678 9012 3456.",
        ]

        for sample_text in negative_examples:
            results = analyze_text(sample_text, ['CREDIT_CARD'])
            self.assertEqual(results, [])

    def test_crypto(self):
        """Test CRYPTO functionality"""

    def test_date_time(self):
        """Test DATE_TIME functionality"""

    def test_email_address(self):
        """Test EMAIL_ADDRESS functionality"""

    def test_medical_license(self):
        """Test MEDICAL_LICENSE functionality"""


if __name__ == '__main__':
    unittest.main()
