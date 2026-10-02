"""Unit test file for team _2"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__2(unittest.TestCase):
    """Test team _2 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_in_aadhaar(self):
        """Test IN_AADHAAR functionality"""

    def test_in_pan(self):
        """Test IN_PAN functionality"""

    def test_in_passport(self):
        """Test IN_PASSPORT functionality"""

    def test_in_vehicle_registration(self):
        """Test IN_VEHICLE_REGISTRATION functionality"""

    def test_in_voter(self):
        """Test IN_VOTER functionality"""
        entity = ['IN_VOTER']
        valid_cases = [
            ('Voter ID: ABC1234567', 'ABC1234567'),
            ('EPIC: DEF2345678', 'DEF2345678'),
            ('Election Commission of India: GHI3456789', 'GHI3456789'),
        ]

        for text, expected_value in valid_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity)
                matches = [result for result in results
                           if result.entity_type == 'IN_VOTER']
                self.assertEqual(len(matches), 1)
                result = matches[0]
                self.assertEqual(text[result.start:result.end], expected_value)

        bare_id = 'JKL4567890'
        bare_results = analyze_text(bare_id, entity)
        contextual_text = f'Voter ID: {bare_id}'
        contextual_results = analyze_text(contextual_text, entity)
        self.assertEqual(len(bare_results), 1)
        self.assertEqual(len(contextual_results), 1)
        self.assertGreater(contextual_results[0].score, bare_results[0].score)

        invalid_cases = [
            'Voter ID: ABC123456',
            'Voter ID: ABC12345678',
            'EPIC: AB1234567',
            'Voter ID: ABCDE1234F',
        ]
        for text in invalid_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity)
                self.assertFalse(any(result.entity_type == 'IN_VOTER'
                                     for result in results))

        from pii_scan import anonymize_text
        text = 'Voter ID: MNO5678901'
        redacted = anonymize_text(text, entity)
        self.assertEqual(redacted, 'Voter ID: <IN_VOTER>')
        self.assertNotIn('MNO5678901', redacted)


if __name__ == '__main__':
    unittest.main()
