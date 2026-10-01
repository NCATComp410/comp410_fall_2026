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

    def test_crypto(self):
        """Test CRYPTO functionality"""


    def test_date_time(self):
        """Test DATE_TIME functionality"""
        positive_cases = [
            "My appointment is on October 15, 2026.",
            "My birthday is 05/24/2003.",
            "The meeting is at 3:30 PM.",
            "I will see you tomorrow.",
            "The event is next week."
        ]

        for text in positive_cases:
            results = analyze_text(text, ["DATE_TIME"])
            entities = [result.entity_type for result in results]
            self.assertIn("DATE_TIME", entities)

        negative_text = "I went to the grocery store to buy some fruit."
        results = analyze_text(negative_text, ["DATE_TIME"])
        entities = [result.entity_type for result in results]
        self.assertNotIn("DATE_TIME", entities)
    def test_email_address(self):
        """Test EMAIL_ADDRESS functionality"""

    def test_medical_license(self):
        """Test MEDICAL_LICENSE functionality"""


if __name__ == '__main__':
    unittest.main()
