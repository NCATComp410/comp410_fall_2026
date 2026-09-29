"""Unit test file for team _3"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__3(unittest.TestCase):
    """Test team _3 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_it_driver_license(self):
        """Test IT_DRIVER_LICENSE functionality"""

    def test_it_fiscal_code(self):
        """Test IT_FISCAL_CODE functionality"""

    def test_it_identity_card(self):
        """Test IT_IDENTITY_CARD functionality"""

    def test_it_passport(self):
        """Test IT_PASSPORT functionality"""

    def test_it_vat_code(self):
        """Detect valid Italian VAT codes and reject invalid candidates."""
        entity = ["IT_VAT_CODE"]
        valid_cases = (
            ("bare", "01333550323", "01333550323"),
            ("Italian context", "Partita IVA: 12345670017", "12345670017"),
            ("mixed-case context", "p.IvA: 01333550323", "01333550323"),
            ("separated country code", "VAT number IT 12345670017", "12345670017"),
            ("separator", "codice IVA: 01333550_323", "01333550_323"),
        )
        for label, text, code in valid_cases:
            with self.subTest(case=label):
                results = analyze_text(text, entity)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, entity[0])
                start = text.index(code)
                self.assertEqual((results[0].start, results[0].end),
                                 (start, start + len(code)))

        text = "VAT number 01333550323; partita iva 12345670017"
        results = analyze_text(text, entity)
        expected_spans = sorted(
            (text.index(code), text.index(code) + len(code))
            for code in ("01333550323", "12345670017")
        )
        actual_spans = sorted((result.start, result.end) for result in results)
        self.assertEqual(len(results), 2)
        self.assertEqual(actual_spans, expected_spans)
        self.assertTrue(all(result.entity_type == entity[0] for result in results))

        invalid_cases = (
            ("bad checksum", "Partita IVA: 01333550324"),
            ("all zeros", "Partita IVA: 00000000000"),
            ("ten digits", "Partita IVA: 0133355032"),
            ("twelve digits", "Partita IVA: 013335503230"),
            ("foreign billing number", "German VAT: DE123456789"),
            ("random invoice reference", "Invoice ID: 12345670018"),
            ("no identifier", "The invoice has no VAT number."),
        )
        for label, text in invalid_cases:
            with self.subTest(case=label):
                self.assertEqual(len(analyze_text(text, entity)), 0)


if __name__ == '__main__':
    unittest.main()
