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

    def test_email_address(self):
        """Test EMAIL_ADDRESS functionality"""
        email_text = (
            "Email: alex.smith+alerts@example.com; "
            "e-mail address: jordan_lee@dept.ncat.edu"
        )
        results = analyze_text(email_text, entity_list=['EMAIL_ADDRESS'])
        detected_addresses = {
            email_text[result.start:result.end]
            for result in results
            if result.entity_type == 'EMAIL_ADDRESS'
        }
        self.assertEqual(
            detected_addresses,
            {'alex.smith+alerts@example.com', 'jordan_lee@dept.ncat.edu'},
        )

        invalid_samples = [
            'Contact me at user@@example.com',
            'Contact me at @example.com',
            'Contact me at user@example',
            'This is ordinary text with no email address.',
            'Visit https://example.com/contact for details.',
        ]
        for sample in invalid_samples:
            with self.subTest(sample=sample):
                results = analyze_text(sample, entity_list=['EMAIL_ADDRESS'])
                self.assertFalse(
                    any(result.entity_type == 'EMAIL_ADDRESS' for result in results)
                )

    def test_medical_license(self):
        """Test MEDICAL_LICENSE functionality"""


if __name__ == '__main__':
    unittest.main()
