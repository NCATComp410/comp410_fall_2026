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
        entity = ["IN_PASSPORT"]
        valid_cases = [
            ("Passport: A1234567", "A1234567"),
            ("My passport number is B7654321.", "B7654321"),
            ("Indian passport B7654321", "B7654321"),
            ("A1234567", "A1234567"),
        ]
        for text, expected_value in valid_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, entity[0])
                start = text.index(expected_value)
                self.assertEqual((results[0].start, results[0].end),
                                 (start, start + len(expected_value)))
                self.assertEqual(text[results[0].start:results[0].end],
                                 expected_value)

        text = "Primary passport: A1234567; backup passport: B7654321."
        results = analyze_text(text, entity)
        expected_spans = sorted(
            (text.index(value), text.index(value) + len(value))
            for value in ("A1234567", "B7654321")
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.entity_type == entity[0]
                            for result in results))
        self.assertEqual(sorted((result.start, result.end)
                                for result in results), expected_spans)
        self.assertCountEqual(
            [text[result.start:result.end] for result in results],
            ["A1234567", "B7654321"],
        )

        invalid_cases = [
            "Passport: A123456",       # too few digits
            "Passport: A12345678",     # too many digits
            "Passport: AB1234567",     # too many letters
            "Passport: 12345678",      # missing leading letter
            "Passport: A12345B7",      # non-digit within number
            "My passport number is not available.",
        ]
        for text in invalid_cases:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, entity), [])

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
