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
        ]:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['PHONE_NUMBER'])
                self.assertFalse(any(
                    result.entity_type == 'PHONE_NUMBER' for result in results
                ))

    def test_location(self):
        """Test LOCATION functionality"""

    def test_person(self):
        """Verify PERSON detection for names and rejection of non-names."""
        # A standard full name should be returned as an exact PERSON span.
        standard_text = "Michael Jordan scored the winning basket."
        standard_results = analyze_text(standard_text, entity_list=['PERSON'])
        standard_matches = [
            result for result in standard_results
            if result.entity_type == 'PERSON'
        ]
        self.assertTrue(standard_matches, "No PERSON was detected for Michael Jordan")
        standard_match = standard_matches[0]
        self.assertEqual(
            standard_text[standard_match.start:standard_match.end],
            "Michael Jordan",
        )
        self.assertGreaterEqual(standard_match.score, 0.5)
        self.assertLessEqual(standard_match.score, 1.0)

        # A title provides useful context and may be included in the detected span.
        titled_text = "Dr. Gregory House reviewed the patient chart."
        titled_results = analyze_text(titled_text, entity_list=['PERSON'])
        titled_matches = [
            result for result in titled_results
            if result.entity_type == 'PERSON'
        ]
        self.assertTrue(
            titled_matches,
            "No PERSON was detected for the titled name Dr. Gregory House",
        )
        self.assertTrue(
            any(
                "Gregory House" in titled_text[result.start:result.end]
                for result in titled_matches
            ),
            "Detected PERSON does not contain Gregory House",
        )
        for result in titled_matches:
            self.assertGreaterEqual(result.score, 0.5)
            self.assertLessEqual(result.score, 1.0)

        # Capitalized days, locations, and common nouns should not create PERSON matches.
        negative_text = (
            "The project status meeting is on Monday morning at Central Park "
            "beside the Red Bicycle."
        )
        negative_results = analyze_text(negative_text, entity_list=['PERSON'])
        person_matches = [
            result for result in negative_results
            if result.entity_type == 'PERSON'
        ]
        self.assertEqual(
            len(person_matches),
            0,
            "False-positive PERSON detections: "
            + str([negative_text[result.start:result.end] for result in person_matches]),
        )

    def test_uk_nhs(self):
        """Test UK_NHS functionality"""
        positive_cases = [
            ("NHS number: 9434765919", "9434765919"),
            ("Patient identifier: 943 476 5919", "943 476 5919"),
            ("Medical record number: 943-476-5919", "943-476-5919"),
        ]

        for text, expected_value in positive_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['UK_NHS'])
                self.assertTrue(
                    any(
                        result.entity_type == 'UK_NHS'
                        and text[result.start:result.end] == expected_value
                        for result in results
                    ),
                    f"Expected UK_NHS match {expected_value!r} in: {text}",
                )

        negative_cases = [
            "NHS number: 9434765918",
            "NHS number: 943476591",
            "NHS number: 94347659190",
            "NHS number: 94-3476-5919",
            "The appointment is next Tuesday.",
        ]

        for text in negative_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['UK_NHS'])
                self.assertFalse(
                    any(result.entity_type == 'UK_NHS' for result in results),
                    f"Unexpected UK_NHS match in: {text}",
                )

    def test_uk_nino(self):
        """Test UK_NINO functionality"""
        # Positive test cases covering valid NINO formats (compact, spaced, lowercase)
        valid_cases = [
            ("AB123456C", "AB123456C"),
            ("AB 12 34 56 C", "AB 12 34 56 C"),
            ("ab123456c", "ab123456c"),
            ("jw 12 34 56 b", "jw 12 34 56 b"),
            ("JW123456B", "JW123456B"),
            ("ER 98 76 54 D", "ER 98 76 54 D"),
            ("AB-12-34-56-C", "AB-12-34-56-C"),
            ("AB123456", "AB123456"),
            ("My NINO is AB123456C.", "AB123456C"),
            ("National Insurance number is JW123456B.", "JW123456B"),
            ("Employee record: AB 12 34 56 C on file.", "AB 12 34 56 C"),
        ]

        for text, expected in valid_cases:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['UK_NINO'])
                detected = [
                    text[result.start:result.end].strip()
                    for result in results
                    if result.entity_type == 'UK_NINO'
                ]
                self.assertIn(
                    expected,
                    detected,
                    f"Expected UK_NINO '{expected}' to be detected in: {text}"
                )
                for result in results:
                    if result.entity_type == 'UK_NINO':
                        self.assertGreaterEqual(result.score, 0.0)
                        self.assertLessEqual(result.score, 1.0)

        # Contextual keyword boosting: compare contextual matches directly against baseline
        raw_text = "AB123456C"
        raw_results = [r for r in analyze_text(raw_text, entity_list=['UK_NINO']) if r.entity_type == 'UK_NINO']
        self.assertTrue(raw_results, "Expected baseline match for bare NINO")
        context_terms = [
            "NINO",
            "National Insurance",
            "NI Number",
            "HMRC",
            "payroll",
            "PAYE",
            "P60",
            "P45",
            "social security",
        ]
        for term in context_terms:
            with self.subTest(context_term=term):
                context_text = f"{term}: AB123456C"
                context_results = [
                    r for r in analyze_text(context_text, entity_list=['UK_NINO'])
                    if r.entity_type == 'UK_NINO'
                ]
                self.assertTrue(context_results, f"Expected match for contextual NINO: {term}")
                self.assertGreater(
                    context_results[0].score,
                    raw_results[0].score,
                    f"Expected contextual keyword '{term}' to boost confidence over the baseline"
                )

        # Negative test cases: invalid prefixes, suffixes, lengths, and non-NINO text
        invalid_cases = [
            "DB123456A",  # Invalid prefix: D cannot be first letter
            "FB123456A",  # Invalid prefix: F cannot be first letter
            "IB123456A",  # Invalid prefix: I cannot be first letter
            "QB123456A",  # Invalid prefix: Q cannot be first letter
            "UB123456A",  # Invalid prefix: U cannot be first letter
            "VB123456A",  # Invalid prefix: V cannot be first letter
            "AD123456A",  # Invalid prefix: D cannot be second letter
            "AF123456A",  # Invalid prefix: F cannot be second letter
            "AI123456A",  # Invalid prefix: I cannot be second letter
            "AQ123456A",  # Invalid prefix: Q cannot be second letter
            "AU123456A",  # Invalid prefix: U cannot be second letter
            "AV123456A",  # Invalid prefix: V cannot be second letter
            "AO123456A",  # Invalid prefix: O cannot be second letter
            "BG123456A",  # Disallowed administrative prefix
            "GB123456A",  # Disallowed administrative prefix
            "NK123456A",  # Disallowed administrative prefix
            "KN123456A",  # Disallowed administrative prefix
            "NT123456A",  # Disallowed administrative prefix
            "TN123456A",  # Disallowed administrative prefix
            "ZZ123456A",  # Disallowed administrative prefix
            "AB123456E",  # Invalid suffix: E is not A, B, C, or D
            "AB123456Z",  # Invalid suffix: Z is not A, B, C, or D
            "AB12345A",   # Invalid body: only 5 digits
            "AB1234567A",  # Invalid body: 7 digits
            "The meeting is at 10 AM.",  # Non-NINO text
            "Invoice number 123456",     # Non-NINO text
            "Order ref 987654321",       # Non-NINO text
        ]

        for sample in invalid_cases:
            with self.subTest(sample=sample):
                results = analyze_text(sample, entity_list=['UK_NINO'])
                self.assertFalse(
                    any(result.entity_type == 'UK_NINO' for result in results),
                    f"Did not expect UK_NINO to be detected in: {sample}"
                )


if __name__ == '__main__':
    unittest.main()
