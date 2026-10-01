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

    def test_location(self):
        """Test LOCATION functionality"""

    def test_person(self):
        """Test PERSON functionality"""

    def test_uk_nhs(self):
        """Test UK_NHS functionality"""

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

    # Contextual keyword boosting: compare contextual match directly against baseline
    raw_text = "AB123456C"
    context_text = "My NINO is AB123456C."
    raw_results = [r for r in analyze_text(raw_text, entity_list=['UK_NINO']) if r.entity_type == 'UK_NINO']
    context_results = [r for r in analyze_text(context_text, entity_list=['UK_NINO']) if r.entity_type == 'UK_NINO']

    self.assertTrue(raw_results, "Expected baseline match for bare NINO")
    self.assertTrue(context_results, "Expected match for contextual NINO")
    self.assertGreater(
        context_results[0].score,
        raw_results[0].score,
        "Expected contextual keywords ('NINO') to boost confidence score over the baseline"
    )

    # Negative test cases: invalid prefixes, suffixes, lengths, and non-NINO text
    invalid_cases = [
        "DB123456A",  # Invalid prefix: D cannot be first letter
        "QB123456A",  # Invalid prefix: Q cannot be first letter
        "VB123456A",  # Invalid prefix: V cannot be first letter
        "AD123456A",  # Invalid prefix: D cannot be second letter
        "AQ123456A",  # Invalid prefix: Q cannot be second letter
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
