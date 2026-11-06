"""Flask test-client coverage for the PII web app."""
import html
import io
import re
import sys
import types
import unittest
from unittest.mock import patch

from docx import Document

from pii_web_app import app


class TestPIIWebApp(unittest.TestCase):
    """Test web requests, output rendering, validation, and file handling."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @staticmethod
    def _textarea(response, element_id):
        page = response.get_data(as_text=True)
        match = re.search(
            rf'<textarea[^>]*id=["\']{re.escape(element_id)}["\'][^>]*>(.*?)</textarea>',
            page,
            re.DOTALL,
        )
        if not match:
            raise AssertionError(f"Response did not contain textarea #{element_id}")
        return html.unescape(match.group(1))

    @staticmethod
    def _error(response):
        match = re.search(
            r'<p[^>]*class=["\'][^"\']*\berror\b[^"\']*["\'][^>]*>(.*?)</p>',
            response.get_data(as_text=True),
            re.DOTALL,
        )
        return html.unescape(match.group(1).strip()) if match else None

    def _post_text(self, text, entities):
        return self.client.post("/", data={"input_text": text, "entity_types": entities})

    def _assert_redacted(self, text, entities, expected):
        response = self._post_text(text, entities)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._textarea(response, "output-text"), expected)
        self.assertIsNone(self._error(response))

    def test_get_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self._error(response))

    def test_credit_card(self):
        self._assert_redacted(
            "My card number is 4111 1111 1111 1111.",
            ["CREDIT_CARD"],
            "My card number is <CREDIT_CARD>.",
        )

    def test_crypto(self):
        self._assert_redacted(
            "Send the refund to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa please.",
            ["CRYPTO"],
            "Send the refund to <CRYPTO> please.",
        )

    def test_date_time(self):
        self._assert_redacted(
            "The appointment is on October 15, 2026 at 3:30 PM.",
            ["DATE_TIME"],
            "The appointment is on <DATE_TIME> at <DATE_TIME>.",
        )

    def test_email_address(self):
        self._assert_redacted(
            "Email me at jordan_lee@dept.ncat.edu with questions.",
            ["EMAIL_ADDRESS"],
            "Email me at <EMAIL_ADDRESS> with questions.",
        )

    def test_medical_license(self):
        self._assert_redacted(
            "Medical license number: AB1000001",
            ["MEDICAL_LICENSE"],
            "Medical license number: <MEDICAL_LICENSE>",
        )

    def test_multiple_occurrences_of_same_entity(self):
        self._assert_redacted(
            "CC a@b.com, c@d.org and e@f.net",
            ["EMAIL_ADDRESS"],
            "CC <EMAIL_ADDRESS>, <EMAIL_ADDRESS> and <EMAIL_ADDRESS>",
        )

    def test_mixed_entity_types(self):
        text = (
            "On 05/24/2003 Dr. Lee (license AB1000001) emailed "
            "jordan_lee@dept.ncat.edu about card 4111111111111111 and wallet "
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa."
        )
        expected = (
            "On <DATE_TIME> Dr. Lee (license <MEDICAL_LICENSE>) emailed "
            "<EMAIL_ADDRESS> about card <CREDIT_CARD> and wallet <CRYPTO>."
        )
        self._assert_redacted(text, [
            "CREDIT_CARD", "CRYPTO", "DATE_TIME", "EMAIL_ADDRESS", "MEDICAL_LICENSE"
        ], expected)

    def test_text_without_pii(self):
        text = "The quick brown fox jumps over the lazy dog."
        self._assert_redacted(text, ["EMAIL_ADDRESS", "CREDIT_CARD"], text)

    def test_empty_text_shows_error(self):
        response = self._post_text("", ["EMAIL_ADDRESS"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Enter text or choose a file to anonymize.")
        self.assertEqual(self._textarea(response, "output-text"), "")

    def test_whitespace_only_text_shows_error(self):
        response = self._post_text(" \t\n ", ["EMAIL_ADDRESS"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Enter text or choose a file to anonymize.")

    def test_whitespace_and_multiline_around_pii_are_preserved(self):
        text = "  First line: test@example.com\n\nLast line.  "
        self._assert_redacted(
            text,
            ["EMAIL_ADDRESS"],
            "  First line: <EMAIL_ADDRESS>\n\nLast line.  ",
        )

    def test_no_entities_selected_shows_error(self):
        response = self._post_text("Contact test@example.com.", [])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Select at least one entity to redact.")
        self.assertEqual(self._textarea(response, "output-text"), "")

    def test_unknown_entity_name_shows_error(self):
        response = self._post_text("Contact test@example.com.", ["NOT_A_REAL_ENTITY"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Unknown entity type: NOT_A_REAL_ENTITY.")
        self.assertEqual(self._textarea(response, "output-text"), "")

    def test_selected_checkbox_stays_checked_after_validation_error(self):
        response = self._post_text("", ["EMAIL_ADDRESS"])
        self.assertIn(b'name="entity_types" value="EMAIL_ADDRESS" checked', response.data)
        self.assertIn(b'name="entity_types" value="CREDIT_CARD" >', response.data)

    def _upload(self, filename, content, entities=("EMAIL_ADDRESS",)):
        return self.client.post(
            "/",
            data={
                "entity_types": list(entities),
                "input_file": (content, filename),
            },
            content_type="multipart/form-data",
        )

    def test_txt_upload(self):
        response = self._upload("contact.txt", io.BytesIO(b"Email: test@example.com."))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._textarea(response, "output-text"), "Email: <EMAIL_ADDRESS>.")
        self.assertIsNone(self._error(response))

    def test_md_upload(self):
        response = self._upload("contact.md", io.BytesIO(b"Email: test@example.com."))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._textarea(response, "output-text"), "Email: <EMAIL_ADDRESS>.")
        self.assertIsNone(self._error(response))

    def test_csv_upload_preserves_trailing_newline(self):
        response = self._upload("contact.csv", io.BytesIO(b"email\ntest@example.com\n"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._textarea(response, "output-text"), "email\n<EMAIL_ADDRESS>\n")
        self.assertIsNone(self._error(response))

    def test_docx_upload(self):
        document = Document()
        document.add_paragraph("Email: test@example.com.")
        content = io.BytesIO()
        document.save(content)
        content.seek(0)
        response = self._upload("contact.docx", content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._textarea(response, "output-text"), "Email: <EMAIL_ADDRESS>.")
        self.assertIsNone(self._error(response))

    def test_corrupt_docx_shows_error(self):
        response = self._upload("corrupt.docx", io.BytesIO(b"not a docx archive"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Could not read this .docx file.")

    def test_unsupported_file_type_shows_error(self):
        response = self._upload("contact.pdf", io.BytesIO(b"Email: test@example.com."))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self._error(response),
            "Choose a .txt, .doc, .docx, .csv, or .md file.",
        )

    def test_upload_over_10_mb_returns_413(self):
        response = self._upload("large.txt", io.BytesIO(b"a" * (10 * 1024 * 1024 + 1)))
        self.assertEqual(response.status_code, 413)
        self.assertIn("10 MB", response.get_data(as_text=True))

    def test_non_utf8_text_upload_shows_error(self):
        response = self._upload("invalid.txt", io.BytesIO(b"\xff\xfe"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._error(response), "Text uploads must use UTF-8 encoding.")

    def test_pii_at_start_and_end_of_text(self):
        self._assert_redacted(
            "test@example.com is first; test@example.org is last",
            ["EMAIL_ADDRESS"],
            "<EMAIL_ADDRESS> is first; <EMAIL_ADDRESS> is last",
        )

    def test_pii_boundaries_in_long_text(self):
        middle = "ordinary words " * 500
        text = "test@example.com " + middle + " test@example.org"
        expected = "<EMAIL_ADDRESS> " + middle + " <EMAIL_ADDRESS>"
        self._assert_redacted(text, ["EMAIL_ADDRESS"], expected)

    def test_luhn_invalid_16_digit_lookalike_is_not_redacted(self):
        text = "Card 4111111111111112"
        self._assert_redacted(text, ["CREDIT_CARD"], text)

    def test_backend_crash_shows_error(self):
        scanner = types.ModuleType("pii_scan")
        scanner.anonymize_text = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("simulated scanner failure")
        )
        with patch.dict(sys.modules, {"pii_scan": scanner}):
            response = self._post_text("Contact test@example.com.", ["EMAIL_ADDRESS"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self._error(response),
            "Anonymization failed. Check the server logs for details.",
        )
        self.assertEqual(self._textarea(response, "output-text"), "")


if __name__ == "__main__":
    unittest.main()
