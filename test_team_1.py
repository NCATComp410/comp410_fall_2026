"""Unit test file for team _1"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__1(unittest.TestCase):
    """Test team _1 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_es_nie(self):
        """Test ES_NIE functionality"""
        valid_cases = [
            ("NIE X1234567L", "X1234567L"),
            ("NIE Y1234567X", "Y1234567X"),
            ("NIE Z1234567R", "Z1234567R"),
            ("NIE x1234567l", "x1234567l"),
            ("número de identificación de extranjero X1234567L",
             "X1234567L"),
        ]

        for text, expected_value in valid_cases:
            results = analyze_text(text, entity_list=['ES_NIE'])
            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result.entity_type, 'ES_NIE')
            self.assertEqual(text[result.start:result.end], expected_value)

        multiple_ids = "NIE X0000000T and NIE Y0000000Z"
        results = analyze_text(multiple_ids, entity_list=['ES_NIE'])
        detected_values = [multiple_ids[result.start:result.end]
                           for result in results]
        self.assertCountEqual(detected_values, ['X0000000T', 'Y0000000Z'])

        invalid_cases = [
            "NIE X1234567A",
            "NIE A1234567L",
            "NIE 12345678Z",
            "NIE X1234567",
            "NIE X12345678L",
        ]

        for text in invalid_cases:
            self.assertEqual(analyze_text(text, entity_list=['ES_NIE']), [])

    def test_es_nif(self):
        """Test ES_NIF functionality"""

    def test_fi_personal_identity_code(self):
        """Test FI_PERSONAL_IDENTITY_CODE functionality"""

    def test_iban_code(self):
        """Test IBAN_CODE functionality"""

    def test_ip_address(self):
        """Test IP_ADDRESS functionality"""


if __name__ == '__main__':
    unittest.main()
