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
        valid_cases = [
            ("standard format", "My Italian driver's license is AB1234567C.", "AB1234567C"),
            ("context wording", "Licenza di guida: ab1234567c.", "ab1234567c"),
        ]
        for label, text, code in valid_cases:
            with self.subTest(case=label):
                results = analyze_text(text, ["IT_DRIVER_LICENSE"])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, "IT_DRIVER_LICENSE")
                start = text.lower().index(code.lower())
                self.assertEqual(
                    (results[0].start, results[0].end),
                    (start, start + len(code)),
                )

        invalid_cases = [
            "Patente: AB1234567",
            "Patente: A1234567C",
            "Patente: AB12345678",
            "Patente: AB1234567CC",
            "Patente: U1234567C",
            "Patente: U1BCDEFGH",
            "My favorite number is 1234567890.",
        ]
        for text in invalid_cases:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, ["IT_DRIVER_LICENSE"]), [])

    def test_it_fiscal_code(self):
        """Test IT_FISCAL_CODE functionality"""
        entity = ["IT_FISCAL_CODE"]
        valid_cases = (
            ("RSSMRA85T10A562S", "Fiscal code: RSSMRA85T10A562S"),
            ("BNCLGU80A01F205D", "Fiscal code: BNCLGU80A01F205D"),
        )
        for code, text in valid_cases:
            with self.subTest(code=code):
                results = analyze_text(text, entity)
                start = text.index(code)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, entity[0])
                self.assertEqual((results[0].start, results[0].end),
                                 (start, start + len(code)))

        invalid_text = "Fiscal code: RSSMRA85T10A562"
        self.assertEqual(analyze_text(invalid_text, entity), [])

    def test_it_identity_card(self):
        """Test IT_IDENTITY_CARD functionality"""
        # Positive test
        text = "My Italian identity card number is CA 1234567."
        results = analyze_text(text, ["IT_IDENTITY_CARD"])

        self.assertTrue(any(result.entity_type == "IT_IDENTITY_CARD" for result in results))

        # Negative test
        text = "My favorite number is 123456789."
        results = analyze_text(text, ["IT_IDENTITY_CARD"])

        self.assertFalse(any(result.entity_type == "IT_IDENTITY_CARD" for result in results))

    def test_it_passport(self):
        """Test IT_PASSPORT functionality"""
        positive_cases = [
            ("Passaporto: AB1234567", 12, 21),
            ("Documento: XZ0000001", 11, 20),
        ]
        for text, expected_start, expected_end in positive_cases:
            with self.subTest(text=text):
                results = analyze_text(text, ["IT_PASSPORT"])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, "IT_PASSPORT")
                self.assertEqual(results[0].start, expected_start)
                self.assertEqual(results[0].end, expected_end)

        invalid_cases = [
            "Passaporto: AB123456",
            "Passaporto: A12345678",
            "Passaporto: ABC1234567",
            "Passaporto: AB12345678",
            "Passaporto: AB12345X7",
        ]
        for text in invalid_cases:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, ["IT_PASSPORT"]), [])

    def test_it_vat_code(self):
        """Detect valid Italian VAT codes and reject invalid candidates."""
        from presidio_analyzer.predefined_recognizers import ItVatCodeRecognizer

        entity = ["IT_VAT_CODE"]
        valid_cases = (
            ("bare", "01333550323", "01333550323"),
            ("bare period", "01333550323.", "01333550323"),
            ("bare parentheses", "(01333550323)", "01333550323"),
            ("bare quotes", '"01333550323"', "01333550323"),
            ("bare whitespace", " \t01333550323\n", "01333550323"),
            ("linking word is", "VAT number is 01333550323.", "01333550323"),
            ("mixed-case linking word", "My VaT NuMbEr IS: 01333550323.", "01333550323"),
            ("linking word equals", "VAT code equals 01333550323.", "01333550323"),
            ("Italian linking word", "La partita IVA è 01333550323.", "01333550323"),
            ("linking separated value", "Partita IVA is 013 33550 323.", "013 33550 323"),
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

        text = "VAT number is 01333550323; partita iva equals 12345670017"
        results = analyze_text(text, entity)
        expected_spans = sorted(
            (text.index(code), text.index(code) + len(code))
            for code in ("01333550323", "12345670017")
        )
        actual_spans = sorted((result.start, result.end) for result in results)
        self.assertEqual(len(results), 2)
        self.assertEqual(actual_spans, expected_spans)
        self.assertTrue(all(result.entity_type == entity[0] for result in results))

        list_cases = (
            ("comma", "VAT number: 01333550323, 12345670017"),
            ("and", "VAT numbers: 01333550323 and 12345670017"),
            ("or", "VAT code: 01333550323 or 12345670017"),
            ("Italian conjunction", "Partita IVA: 01333550323 e 12345670017"),
            ("mixed case", "VAT codes: 01333550323, AND 12345670017"),
            ("ampersand", "VAT number: 01333550323 & 12345670017"),
            ("labeled prefix", "VAT number: IT01333550323, 12345670017"),
            ("formatted list", "Partita IVA: 013 33550 323, 12345670017"),
        )
        for label, text in list_cases:
            with self.subTest(case=label):
                results = analyze_text(text, entity)
                first = "01333550323"
                if label == "labeled prefix":
                    first = "IT01333550323"
                elif label == "formatted list":
                    first = "013 33550 323"
                expected = [(text.index(first), text.index(first) + len(first)),
                            (text.index("12345670017"), text.index("12345670017") + 11)]
                self.assertEqual(sorted((r.start, r.end) for r in results), expected)
                self.assertTrue(all(r.entity_type == entity[0] for r in results))

        text = "VAT numbers: 01333550323, 12345670017 and IT12345671007"
        results = analyze_text(text, entity)
        expected = [(text.index(code), text.index(code) + len(code))
                    for code in ("01333550323", "12345670017", "IT12345671007")]
        self.assertEqual(sorted((r.start, r.end) for r in results), expected)

        # A valid VAT must not give an unrelated field permission to match.
        boundary_cases = (
            "VAT number: 01333550323, Invoice ID: 12345670017",
            "VAT number: 01333550323 and Invoice ID: 12345670017",
            "VAT number: 01333550323; 12345670017",
            "VAT number: 01333550323. 12345670017",
            "VAT number: 01333550323\n12345670017",
            "VAT number: 01333550323, DE 12345670017",
            "VAT number: 01333550323 12345670017",
            "Supplier: IT01333550323, 12345670017",
        )
        for text in boundary_cases:
            with self.subTest(case=text):
                results = analyze_text(text, entity)
                first = "IT01333550323" if "IT01333550323" in text else "01333550323"
                # Adjacent digit groups are rejected as one overlong candidate.
                expected = [] if text.endswith("01333550323 12345670017") else [
                    (text.index(first), text.index(first) + len(first))]
                self.assertEqual([(r.start, r.end) for r in results], expected)

        # Isolate office/context checks using fixtures that pass the checksum.
        checksum = ItVatCodeRecognizer()
        for label, code in (
            ("office 000 fixture", "12345670009"),
            ("office 101 fixture", "12345671015"),
            ("invoice fixture", "12345670017"),
            ("zero company fixture", "00000000018"),
        ):
            with self.subTest(case=label):
                self.assertTrue(checksum.validate_result(code))

        text = "VAT number: IT01333550323; Invoice ID: 12345670017"
        results = analyze_text(text, entity)
        start = text.index("IT01333550323")
        self.assertEqual(len(results), 1)
        self.assertEqual((results[0].start, results[0].end), (start, start + 13))

        invalid_cases = (
            ("invoice linking word", "Invoice ID is 12345670017."),
            ("neighboring invoice field", "VAT number is unavailable; Invoice ID is 12345670017."),
            ("sentence boundary", "VAT number is unavailable. Invoice ID: 12345670017."),
            ("negated label", "VAT number is not provided; Invoice ID: 12345670017."),
            ("linking word fragment", "VAT number issue: 01333550323"),
            ("invalid office 000", "Partita IVA: 12345670009"),
            ("invalid office 101", "Partita IVA: 12345671015"),
            ("foreign valid-checksum identifier", "German VAT: DE 12345670017"),
            ("separated twelve digits", "Partita IVA: IT013 33550 323 0"),
            ("prefixed ten digits", "IT0133355032"),
            ("prefixed twelve digits", "IT013335503230"),
            ("unlabelled separated value", "013 33550 323"),
            ("bad checksum", "Partita IVA: 01333550324"),
            ("all zeros", "Partita IVA: 00000000000"),
            ("zero company with valid office", "Partita IVA: 00000000018"),
            ("punctuated bad checksum", "(01333550324)"),
            ("wrapped invoice", "(Invoice ID: 12345670017)"),
            ("unlabeled list", "01333550323, 12345670017"),
            ("embedded prefix", "XIT01333550323"),
            ("trailing letter", "IT01333550323X"),
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
