"""Unit test file for team _z"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__z(unittest.TestCase):
    """Test team _z PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_phone_number(self):
        """Test PHONE_NUMBER functionality"""
        examples = [
            ("Call me at +1 212-555-1234.", "+1 212-555-1234"),
            ("(415) 555-2671", "(415) 555-2671"),
            ("212.555.1234", "212.555.1234"),
            ("+44 20 7946 0958", "+44 20 7946 0958"),
            ("My phone number is 336-555-0123", "336-555-0123"),
            ("Reach me at +1 336 555 0123", "+1 336 555 0123"),
            ("Phone: 212-555-0198", "212-555-0198"),
            ("My number is 336.555.0123", "336.555.0123"),
        ]
        for text, phone_number in examples:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['PHONE_NUMBER'])
                detected = [
                    text[result.start:result.end]
                    for result in results
                    if result.entity_type == 'PHONE_NUMBER'
                ]
                self.assertIn(phone_number, detected)

        for text in [
            "Call me when you arrive.",
            "The room number is 42.",
            "The meeting is on 2026-10-01.",
            "Order number 12345",
            "My zip code is 27411",
            "Phone: 555-0123",
        ]:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['PHONE_NUMBER'])
                self.assertFalse(any(
                    result.entity_type == 'PHONE_NUMBER' for result in results
                ))

    def test_location(self):
        """Test LOCATION functionality"""

    def test_person(self):
        """Test PERSON functionality"""

    def test_uk_nhs(self):
        """Test UK_NHS functionality"""

    def test_uk_nino(self):
        """Test UK_NINO functionality"""


if __name__ == '__main__':
    unittest.main()
