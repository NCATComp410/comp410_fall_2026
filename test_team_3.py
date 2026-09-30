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
        from presidio_analyzer.predefined_recognizers import ItVatCodeRecognizer

        entity = ["IT_VAT_CODE"]
        valid_cases = (
            ("bare", "01333550323", "01333550323"),
            ("attached prefix", "Supplier: IT01333550323.", "IT01333550323"),
            ("lowercase prefix", "Supplier: it01333550323.", "it01333550323"),
            ("underscore context", "P_IVA: 01333550323", "01333550323"),
            ("VAT code context", "VaT CoDe: 01333550323", "01333550323"),
            ("whitespace separator", "Partita IVA: 013 33550 323", "013 33550 323"),
            ("office 100", "IT12345671007", "IT12345671007"),
            ("office 120", "IT12345671205", "IT12345671205"),
            ("office 121", "IT12345671213", "IT12345671213"),
            ("special office 888", "IT12345678887", "IT12345678887"),
            ("special office 999", "IT12345679992", "IT12345679992"),
            ("Italian context", "Partita IVA: 12345670017", "12345670017"),
            ("mixed-case context", "p.IvA: 01333550323", "01333550323"),
            ("separated country code", "VAT number IT 12345670017", "IT 12345670017"),
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

        # Isolate office/context checks using fixtures that pass the checksum.
        checksum = ItVatCodeRecognizer()
        for label, code in (
            ("office 000 fixture", "12345670009"),
            ("office 101 fixture", "12345671015"),
            ("invoice fixture", "12345670017"),
        ):
            with self.subTest(case=label):
                self.assertTrue(checksum.validate_result(code))

        text = "VAT number: IT01333550323; Invoice ID: 12345670017"
        results = analyze_text(text, entity)
        start = text.index("IT01333550323")
        self.assertEqual(len(results), 1)
        self.assertEqual((results[0].start, results[0].end), (start, start + 13))

        invalid_cases = (
            ("invalid office 000", "Partita IVA: 12345670009"),
            ("invalid office 101", "Partita IVA: 12345671015"),
            ("foreign valid-checksum identifier", "German VAT: DE 12345670017"),
            ("separated twelve digits", "Partita IVA: IT013 33550 323 0"),
            ("prefixed ten digits", "IT0133355032"),
            ("prefixed twelve digits", "IT013335503230"),
            ("unlabelled separated value", "013 33550 323"),
            ("bad checksum", "Partita IVA: 01333550324"),
            ("all zeros", "Partita IVA: 00000000000"),
            ("ten digits", "Partita IVA: 0133355032"),
            ("twelve digits", "Partita IVA: 013335503230"),
            ("foreign billing number", "German VAT: DE123456789"),
            ("random invoice reference", "Invoice ID: 12345670017"),
            ("no identifier", "The invoice has no VAT number."),
        )
        for label, text in invalid_cases:
            with self.subTest(case=label):
                self.assertEqual(len(analyze_text(text, entity)), 0)


if __name__ == '__main__':
    unittest.main()
