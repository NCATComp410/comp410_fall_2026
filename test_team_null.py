"""Unit test file for team null"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam_null(unittest.TestCase):
    """Test team null PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_us_ssn(self):
        """Test US_SSN functionality"""
        valid_ssns = [
            "SSN 123-12-1234",
            "SSN 987654321",
            "SSN 123-45-6789 and 987-65-4321",
        ]
        invalid_ssns = [
            "SSN 1234-56-789",
            "SSN 123-45-67890",
            "SSN 12-345-6789",
            "SSN 000-00-0000",
        ]

        for sample in valid_ssns:
            with self.subTest(sample=sample):
                results = analyze_text(sample, entity_list=['US_SSN'])
                self.assertTrue(
                    any(result.entity_type == 'US_SSN' for result in results),
                    f"Expected US_SSN to be detected in: {sample}"
                )

        for sample in invalid_ssns:
            with self.subTest(sample=sample):
                results = analyze_text(sample, entity_list=['US_SSN'])
                self.assertFalse(
                    any(result.entity_type == 'US_SSN' for result in results),
                    f"Did not expect US_SSN to be detected in: {sample}"
                )


if __name__ == '__main__':
    unittest.main()
