"""Sprint 3 unit and boundary tests for the Team 3 PII Redactor and Web App.

Covers normal inputs, multiple occurrences, mixed Team 3 entities, boundary
conditions (with emphasis on IT_VAT_CODE), text with no PII, empty/whitespace
inputs, invalid inputs, batch/file processing, CLI execution, and Flask routes.
"""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from pii_redactor import (
    RedactorError,
    SUPPORTED_ENTITIES,
    main,
    parse_entities,
    redact_file,
    redact_lines,
    redact_text,
    summarize,
)
from pii_web_app import app


class TestEntityParsing(unittest.TestCase):
    """Test entity list parsing, normalization, and validation."""

    def test_none_and_empty_default_to_team_3_entities(self):
        self.assertEqual(parse_entities(None), SUPPORTED_ENTITIES)
        self.assertEqual(parse_entities([]), SUPPORTED_ENTITIES)
        self.assertEqual(parse_entities(""), SUPPORTED_ENTITIES)
        self.assertEqual(parse_entities("   ,  "), SUPPORTED_ENTITIES)

    def test_comma_and_space_separated_case_insensitive_deduplicated(self):
        parsed = parse_entities(" it_vat_code, IT_FISCAL_CODE  it_vat_code , it_passport ")
        self.assertEqual(parsed, ["IT_VAT_CODE", "IT_FISCAL_CODE", "IT_PASSPORT"])

    def test_list_and_tuple_inputs(self):
        self.assertEqual(
            parse_entities(("it_driver_license", "IT_IDENTITY_CARD")),
            ["IT_DRIVER_LICENSE", "IT_IDENTITY_CARD"],
        )

    def test_unsupported_entity_raises_redactor_error(self):
        for unsupported in (["CREDIT_CARD"], "US_SSN", "IT_VAT_CODE, EMAIL_ADDRESS"):
            with self.subTest(unsupported=unsupported):
                with self.assertRaises(RedactorError):
                    parse_entities(unsupported)

    def test_invalid_entity_types_raise_redactor_error(self):
        for bad_input in (42, 3.14, {"a": 1}, [123], ["IT_VAT_CODE", None]):
            with self.subTest(bad_input=bad_input):
                with self.assertRaises(RedactorError):
                    parse_entities(bad_input)


class TestItVatCodeAnonymization(unittest.TestCase):
    """Test IT_VAT_CODE detection and anonymization across valid, list, boundary, and invalid cases."""

    def test_valid_single_it_vat_codes_are_redacted(self):
        valid_cases = (
            ("bare", "01333550323", "<IT_VAT_CODE>"),
            ("bare period", "01333550323.", "<IT_VAT_CODE>."),
            ("bare parentheses", "(01333550323)", "(<IT_VAT_CODE>)"),
            ("bare quotes", "'\"01333550323'\"", "'\"<IT_VAT_CODE>'\""),
            ("bare whitespace", " \t01333550323\n", " \t<IT_VAT_CODE>\n"),
            ("linking word is", "VAT number is 01333550323.", "VAT number is <IT_VAT_CODE>."),
            ("mixed-case linking word", "My VaT NumBEr IS 01333550323.", "My VaT NumBEr IS <IT_VAT_CODE>."),
            ("linking word equals", "VAT code equals 01333550323.", "VAT code equals <IT_VAT_CODE>."),
            ("Italian linking word", "La partita IVA è 01333550323", "La partita IVA è <IT_VAT_CODE>"),
            ("linking separated value", "Partita IVA is 013 33550 323.", "Partita IVA is <IT_VAT_CODE>."),
            ("attached prefix", "Supplier: IT01333550323.", "Supplier: <IT_VAT_CODE>."),
            ("lowercase prefix", "Supplier: it01333550323.", "Supplier: <IT_VAT_CODE>."),
            ("underscore context", "P_IVA: 01333550323", "P_IVA: <IT_VAT_CODE>"),
            ("VAT code context", "VaT CoDe: 01333550323", "VaT CoDe: <IT_VAT_CODE>"),
            ("whitespace separator", "Partita IVA: 013 33550 323", "Partita IVA: <IT_VAT_CODE>"),
            ("office 100", "IT12345671007", "<IT_VAT_CODE>"),
            ("office 120", "IT12345671205", "<IT_VAT_CODE>"),
            ("office 121", "IT12345671213", "<IT_VAT_CODE>"),
            ("special office 888", "IT12345678887", "<IT_VAT_CODE>"),
            ("special office 999", "IT12345679992", "<IT_VAT_CODE>"),
            ("Italian context", "Partita IVA: 12345670017", "Partita IVA: <IT_VAT_CODE>"),
            ("mixed-case context", "p.IVA: 01333550323", "p.IVA: <IT_VAT_CODE>"),
            ("separated country code", "VAT number IT 12345670017", "VAT number <IT_VAT_CODE>"),
            ("underscore separator", "codice IVA: 01333550_323", "codice IVA: <IT_VAT_CODE>"),
        )
        for label, text, expected in valid_cases:
            with self.subTest(case=label):
                self.assertEqual(redact_text(text, ["IT_VAT_CODE"]), expected)

    def test_multiple_occurrences_and_labeled_vat_lists(self):
        list_cases = (
            (
                "two labeled clauses",
                "VAT number is 01333550323; partita iva equals 12345670017",
                "VAT number is <IT_VAT_CODE>; partita iva equals <IT_VAT_CODE>",
                2,
            ),
            (
                "comma list",
                "VAT number: 01333550323, 12345670017",
                "VAT number: <IT_VAT_CODE>, <IT_VAT_CODE>",
                2,
            ),
            (
                "and conjunction",
                "VAT numbers: 01333550323 and 12345670017",
                "VAT numbers: <IT_VAT_CODE> and <IT_VAT_CODE>",
                2,
            ),
            (
                "or conjunction",
                "VAT code: 01333550323 or 12345670017",
                "VAT code: <IT_VAT_CODE> or <IT_VAT_CODE>",
                2,
            ),
            (
                "Italian conjunction",
                "Partita IVA: 01333550323 e 12345670017",
                "Partita IVA: <IT_VAT_CODE> e <IT_VAT_CODE>",
                2,
            ),
            (
                "mixed case comma and",
                "VAT codes: 01333550323, AND 12345670017",
                "VAT codes: <IT_VAT_CODE>, AND <IT_VAT_CODE>",
                2,
            ),
            (
                "ampersand",
                "VAT number: 01333550323 & 12345670017",
                "VAT number: <IT_VAT_CODE> & <IT_VAT_CODE>",
                2,
            ),
            (
                "labeled prefix list",
                "VAT number: IT01333550323, 12345670017",
                "VAT number: <IT_VAT_CODE>, <IT_VAT_CODE>",
                2,
            ),
            (
                "formatted list",
                "Partita IVA: 013 33550 323, 12345670017",
                "Partita IVA: <IT_VAT_CODE>, <IT_VAT_CODE>",
                2,
            ),
            (
                "three-item list",
                "VAT numbers: 01333550323, 12345670017 and IT12345671007",
                "VAT numbers: <IT_VAT_CODE>, <IT_VAT_CODE> and <IT_VAT_CODE>",
                3,
            ),
        )
        for label, text, expected, expected_count in list_cases:
            with self.subTest(case=label):
                self.assertEqual(redact_text(text, ["IT_VAT_CODE"]), expected)
                self.assertEqual(
                    summarize(text, ["IT_VAT_CODE"]), {"IT_VAT_CODE": expected_count}
                )

    def test_vat_boundary_cases_preserve_unrelated_numbers(self):
        boundary_cases = (
            (
                "comma invoice id",
                "VAT number: 01333550323, Invoice ID: 12345670017",
                "VAT number: <IT_VAT_CODE>, Invoice ID: 12345670017",
            ),
            (
                "and invoice id",
                "VAT number: 01333550323 and Invoice ID: 12345670017",
                "VAT number: <IT_VAT_CODE> and Invoice ID: 12345670017",
            ),
            (
                "semicolon unlabeled",
                "VAT number: 01333550323; 12345670017",
                "VAT number: <IT_VAT_CODE>; 12345670017",
            ),
            (
                "period unlabeled",
                "VAT number: 01333550323. 12345670017",
                "VAT number: <IT_VAT_CODE>. 12345670017",
            ),
            (
                "newline unlabeled",
                "VAT number: 01333550323\n12345670017",
                "VAT number: <IT_VAT_CODE>\n12345670017",
            ),
            (
                "foreign prefix after comma",
                "VAT number: 01333550323, DE 12345670017",
                "VAT number: <IT_VAT_CODE>, DE 12345670017",
            ),
            (
                "adjacent overlong digit groups rejected",
                "VAT number: 01333550323 12345670017",
                "VAT number: 01333550323 12345670017",
            ),
            (
                "unlabeled prefix does not establish list context",
                "Supplier: IT01333550323, 12345670017",
                "Supplier: <IT_VAT_CODE>, 12345670017",
            ),
            (
                "labeled prefix with semicolon invoice id",
                "VAT number: IT01333550323; Invoice ID: 12345670017",
                "VAT number: <IT_VAT_CODE>; Invoice ID: 12345670017",
            ),
        )
        for label, text, expected in boundary_cases:
            with self.subTest(case=label):
                self.assertEqual(redact_text(text, ["IT_VAT_CODE"]), expected)

    def test_invalid_vat_candidates_are_not_redacted(self):
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
                self.assertEqual(redact_text(text, ["IT_VAT_CODE"]), text)
                self.assertEqual(summarize(text, ["IT_VAT_CODE"]), {})


class TestAllTeam3EntitiesAndEdgeCases(unittest.TestCase):
    """Test all five Team 3 entities, mixed entities, empty/no-PII inputs, and error handling."""

    def test_it_driver_license_anonymization(self):
        self.assertEqual(
            redact_text("My Italian driver's license is AB1234567C.", ["IT_DRIVER_LICENSE"]),
            "My Italian driver's license is <IT_DRIVER_LICENSE>.",
        )
        self.assertEqual(
            redact_text("Patente: AB1234567", ["IT_DRIVER_LICENSE"]),
            "Patente: AB1234567",
        )

    def test_it_fiscal_code_anonymization(self):
        self.assertEqual(
            redact_text("Fiscal code: RSSMRA85T10A562S", ["IT_FISCAL_CODE"]),
            "Fiscal code: <IT_FISCAL_CODE>",
        )
        self.assertEqual(
            redact_text("Fiscal code: RSSMRA85T10A562", ["IT_FISCAL_CODE"]),
            "Fiscal code: RSSMRA85T10A562",
        )

    def test_it_identity_card_anonymization(self):
        self.assertEqual(
            redact_text("My Italian identity card number is CA 1234567.", ["IT_IDENTITY_CARD"]),
            "My Italian identity card number is <IT_IDENTITY_CARD>.",
        )

    def test_it_passport_anonymization(self):
        self.assertEqual(
            redact_text("Passaporto: AB1234567", ["IT_PASSPORT"]),
            "Passaporto: <IT_PASSPORT>",
        )

    def test_mixed_team_3_entities_all_redacted(self):
        text = (
            "Customer Fiscal Code: RSSMRA85T10A562S, Driver License: AB1234567C, "
            "Identity Card: CA 1234567, Passaporto: AB1234567, "
            "and Partita IVA: IT01333550323."
        )
        out = redact_text(text)
        self.assertIn("<IT_FISCAL_CODE>", out)
        self.assertIn("<IT_DRIVER_LICENSE>", out)
        self.assertIn("<IT_IDENTITY_CARD>", out)
        self.assertIn("<IT_PASSPORT>", out)
        self.assertIn("<IT_VAT_CODE>", out)
        counts = summarize(text)
        self.assertEqual(
            counts,
            {
                "IT_FISCAL_CODE": 1,
                "IT_DRIVER_LICENSE": 1,
                "IT_IDENTITY_CARD": 1,
                "IT_PASSPORT": 1,
                "IT_VAT_CODE": 1,
            },
        )

    def test_subset_entity_filtering_redacts_only_requested_entities(self):
        text = "Fiscal code: RSSMRA85T10A562S, Partita IVA: IT01333550323."
        out = redact_text(text, ["IT_VAT_CODE"])
        self.assertEqual(out, "Fiscal code: RSSMRA85T10A562S, Partita IVA: <IT_VAT_CODE>.")

    def test_no_pii_text_preserved(self):
        text = "Order #94820 shipped to Rome on Tuesday at 3:30 PM."
        self.assertEqual(redact_text(text), text)
        self.assertEqual(summarize(text), {})

    def test_empty_and_whitespace_inputs(self):
        for empty_text in ("", " ", "   \n\t  "):
            with self.subTest(empty_text=repr(empty_text)):
                self.assertEqual(redact_text(empty_text), empty_text)
                self.assertEqual(summarize(empty_text), {})

    def test_invalid_text_types_raise_redactor_error(self):
        for bad_text in (None, 123, ["Partita IVA: 01333550323"], {"text": "01333550323"}):
            with self.subTest(bad_text=bad_text):
                with self.assertRaises(RedactorError):
                    redact_text(bad_text)
                with self.assertRaises(RedactorError):
                     redact_lines(bad_text)
                with self.assertRaises(RedactorError):
                    summarize(bad_text)


class TestEnhancementsCliAndWebApp(unittest.TestCase):
    """Test batch line mode, file I/O, CLI interface, and Flask web application."""

    def test_batch_lines_mode_redacts_standalone_vat_per_line(self):
        batch_input = "01333550323\n\n12345670017\nNo PII on this line"
        expected = "<IT_VAT_CODE>\n\n<IT_VAT_CODE>\nNo PII on this line"
        self.assertEqual(redact_lines(batch_input, ["IT_VAT_CODE"]), expected)
        self.assertEqual(
            summarize(batch_input, ["IT_VAT_CODE"], line_by_line=True),
            {"IT_VAT_CODE": 2},
        )

    def test_file_redaction_and_missing_file_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_file = os.path.join(tmpdir, "sample.txt")
            out_file = os.path.join(tmpdir, "sample_redacted.txt")
            with open(in_file, "w", encoding="utf-8") as handle:
                handle.write("Partita IVA: 01333550323\nFiscal code: RSSMRA85T10A562S\n")

            result = redact_file(in_file, out_file, ["IT_VAT_CODE", "IT_FISCAL_CODE"])
            self.assertEqual(
                result,
                "Partita IVA: <IT_VAT_CODE>\nFiscal code: <IT_FISCAL_CODE>\n",
            )
            with open(out_file, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), result)

        with self.assertRaises(RedactorError):
            redact_file("nonexistent_input_file.txt", "out.txt")

    def test_cli_main_text_and_error_handling(self):
        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            code = main(["-t", "Partita IVA: 01333550323", "-e", "IT_VAT_CODE", "--summary"])
        self.assertEqual(code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("Partita IVA: <IT_VAT_CODE>", output)
        self.assertIn("IT_VAT_CODE: 1", output)

        stderr_buf = io.StringIO()
        with redirect_stderr(stderr_buf):
            err_code = main(["-t", "hello", "-e", "UNSUPPORTED_TYPE"])
        self.assertEqual(err_code, 1)
        self.assertIn("Unsupported entity", stderr_buf.getvalue())

    def test_flask_web_app_routes(self):
        client = app.test_client()

        # GET request renders page and supported Team 3 entities
        get_resp = client.get("/")
        self.assertEqual(get_resp.status_code, 200)
        page_html = get_resp.get_data(as_text=True)
        for ent in SUPPORTED_ENTITIES:
            self.assertIn(ent, page_html)

        # POST request with valid IT_VAT_CODE input
        post_resp = client.post(
            "/",
            data={
                "entities": "IT_VAT_CODE",
                "text": "VAT number: 01333550323, Invoice ID: 12345670017",
            },
        )
        self.assertEqual(post_resp.status_code, 200)
        post_html = post_resp.get_data(as_text=True)
        self.assertIn("VAT number: &lt;IT_VAT_CODE&gt;, Invoice ID: 12345670017", post_html)
        self.assertIn("IT_VAT_CODE: 1", post_html)

        # POST request with unsupported entity shows friendly error without crashing
        bad_resp = client.post(
            "/",
            data={"entities": "CREDIT_CARD", "text": "Partita IVA: 01333550323"},
        )
        self.assertEqual(bad_resp.status_code, 200)
        self.assertIn("Unsupported entity", bad_resp.get_data(as_text=True))

        # POST request with empty text shows prompt message
        empty_resp = client.post("/", data={"entities": "IT_VAT_CODE", "text": "   "})
        self.assertEqual(empty_resp.status_code, 200)
        self.assertIn("Please enter some text to anonymize.", empty_resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()