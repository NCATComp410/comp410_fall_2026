"""Unit test file for team _2"""
import unittest
from pii_scan import analyze_text, anonymize_text, show_aggie_pride  # noqa


class TestTeam__2(unittest.TestCase):
    """Test team _2 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_in_aadhaar(self):
        """Test IN_AADHAAR functionality"""

    def test_in_pan(self):
        """Test IN_PAN functionality"""
        self.assertEqual(len(analyze_text("ABCPD1234E", entity_list=["IN_PAN"])), 1)
        for code in "ABCFGHLJPT":
            candidate = f"ABC{code}D1234E"
            with self.subTest(entity_code=code):
                results = analyze_text(candidate, entity_list=["IN_PAN"])
                self.assertEqual(len(results), 1)
                self.assertEqual(candidate[results[0].start:results[0].end], candidate)
    def test_in_pan_malformed(self):
        """Reject missing/extra characters, separators, and non-ASCII lookalikes."""
        candidates = (
            "", "ABCPD123E", "ABCPD12345E", "ABCP1234E", "ABCPDD1234E",
            "ABCPD1234", "ABCPD1234EF", "ABCPD 1234E", "ABC PD1234E",
            "ABCPD-1234E", "ABCPD1234\nE", "ABCPD１２３４E",
            "ABCPD١٢٣٤E", "ABCPD12A4E",
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.assertEqual(analyze_text(candidate, entity_list=["IN_PAN"]), [])

    def test_in_pan_false_positives(self):
        """Do not extract a PAN substring from a larger identifier."""
        candidates = (
            "XABCPD1234E", "ABCPD1234EX", "1ABCPD1234E", "ABCPD1234E1",
            "xABCPD1234E", "ABCPD1234Ex", "_ABCPD1234E", "ABCPD1234E_",
            "éABCPD1234E", "ABCPD1234Eé", "ABCPD1234EABCCD0000F",
            "Order number 1234567890", "Frying pan",
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.assertEqual(analyze_text(candidate, entity_list=["IN_PAN"]), [])

    def test_in_pan_integration(self):
        """Use the strict recognizer in all-entity scans and anonymization."""
        text = "PAN: ABCPD1234E"
        results = analyze_text(text, entity_list=[])
        pans = [result for result in results if result.entity_type == "IN_PAN"]
        self.assertEqual(len(pans), 1)
        self.assertEqual(text[pans[0].start:pans[0].end], "ABCPD1234E")
        self.assertEqual(anonymize_text(text, ["IN_PAN"]), "PAN: <IN_PAN>")
        for candidate in ("XABCPD1234E",):
            candidate_text = f"PAN: {candidate}"
            with self.subTest(candidate=candidate):
                results = analyze_text(candidate_text, entity_list=[])
                self.assertFalse(any(result.entity_type == "IN_PAN" for result in results))
                self.assertEqual(anonymize_text(candidate_text, ["IN_PAN"]), candidate_text)

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
        """Check registration detection in everyday vehicle records."""
        entity = ["IN_VEHICLE_REGISTRATION"]

        # Positive cases: different formats and surrounding contexts.
        examples = [
            ("Vehicle registration: MH01AB1234.", "MH01AB1234"),
            ("The number plate reads KA03MN4567.", "KA03MN4567"),
            ("VEHICLE REGISTRATION: MH01AB1234.", "MH01AB1234"),
            ("vehicle registration: KA03MN4567.", "KA03MN4567"),
        ]

        for text, expected in examples:
            with self.subTest(example=text):
                matches = analyze_text(text, entity_list=entity)

                self.assertEqual(len(matches), 1)
                match = matches[0]
                self.assertEqual(
                    match.entity_type,
                    "IN_VEHICLE_REGISTRATION",
                )
                self.assertEqual(
                    (match.start, match.end),
                    (text.index(expected),
                     text.index(expected) + len(expected)),
                )
                self.assertEqual(
                    text[match.start:match.end],
                    expected,
                )

        unsupported_formats = [
            "Registration number: MH 01 AB 1234.",
            "Vehicle number: KA-03-MN-4567.",
        ]
        for text in unsupported_formats:
            with self.subTest(unsupported_format=text):
                self.assertEqual(analyze_text(text, entity_list=entity), [])

        # Negative cases: ordinary text and incomplete identifiers.
        nonregistrations = [
            "The car is waiting near the main entrance.",
            "Vehicle registration: 12345678.",
            "Registration number: MH01AB.",
            "Number plate: ABCDE.",
        ]

        for text in nonregistrations:
            with self.subTest(negative=text):
                self.assertEqual(
                    analyze_text(text, entity_list=entity),
                    [],
                )

        # Multiple matches: detect both plates and their exact spans.
        text = (
            "Vehicle registration records list MH01AB1234 "
            "for the first car and KA03MN4567 for the second."
        )
        matches = analyze_text(text, entity_list=entity)

        self.assertEqual(len(matches), 2)
        self.assertEqual(
            {match.entity_type for match in matches},
            {"IN_VEHICLE_REGISTRATION"},
        )
        self.assertEqual(
            {(match.start, match.end) for match in matches},
            {
                (text.index(number), text.index(number) + len(number))
                for number in ("MH01AB1234", "KA03MN4567")
            },
        )

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
