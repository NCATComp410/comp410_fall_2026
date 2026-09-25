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

    def test_uk_nino(self):
        """Test UK_NINO functionality"""


if __name__ == '__main__':
    unittest.main()
