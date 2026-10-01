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

    def test_in_vehicle_registration(self):
        """Test IN_VEHICLE_REGISTRATION functionality"""

    def test_in_voter(self):
        """Test IN_VOTER functionality"""


if __name__ == '__main__':
    unittest.main()
