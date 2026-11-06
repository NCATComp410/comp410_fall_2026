"""Sprint 3 tests for the Team Z PII redactor."""
import os
import uuid
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
from unittest.mock import patch

from pii_redactor import (RedactorError, SUPPORTED_ENTITIES, parse_entities,
                          main, redact_file, redact_lines, redact_text, summarize)


class TestEntityParsing(unittest.TestCase):
    """Entity list handling"""
    def test_default_is_all_team_entities(self):
        self.assertEqual(parse_entities(None), SUPPORTED_ENTITIES)

    def test_empty_list_falls_back_to_team_entities(self):
        self.assertEqual(parse_entities([]), SUPPORTED_ENTITIES)

    def test_string_and_case_and_duplicates(self):
        self.assertEqual(parse_entities(" phone_number, PERSON ,person"),
                         ["PHONE_NUMBER", "PERSON"])

    def test_unsupported_entity(self):
        with self.assertRaises(RedactorError):
            parse_entities(["CREDIT_CARD"])

    def test_bad_types(self):
        with self.assertRaises(RedactorError):
            parse_entities(42)
        with self.assertRaises(RedactorError):
            parse_entities([1, 2])


class TestRedactText(unittest.TestCase):
    """Normal, mixed, and boundary inputs"""
    def test_phone_number(self):
        self.assertEqual(redact_text("Call 336-555-0123 now", ["PHONE_NUMBER"]),
                         "Call <PHONE_NUMBER> now")

    def test_multiple_occurrences(self):
        out = redact_text("Call +1 212-555-1234 or (415) 555-2671.", ["PHONE_NUMBER"])
        self.assertEqual(out.count("<PHONE_NUMBER>"), 2)

    def test_uk_nhs(self):
        out = redact_text("My NHS number is 401 023 2137", ["UK_NHS"])
        self.assertEqual(out, "My NHS number is <UK_NHS>")

    def test_uk_nino(self):
        out = redact_text("NI number AB123456C", ["UK_NINO"])
        self.assertIn("<UK_NINO>", out)
        self.assertNotIn("AB123456C", out)

    def test_person_and_location(self):
        out = redact_text("John Smith lives in London.", ["PERSON", "LOCATION"])
        self.assertIn("<PERSON>", out)
        self.assertIn("<LOCATION>", out)

    def test_mixed_entities(self):
        out = redact_text("Maria Garcia, NHS 943 476 5919, phone 336-555-0123.")
        self.assertIn("<PERSON>", out)
        self.assertIn("<UK_NHS>", out)
        self.assertIn("<PHONE_NUMBER>", out)

    def test_only_chosen_entities_are_redacted(self):
        out = redact_text("John called 336-555-0123", ["PHONE_NUMBER"])
        self.assertEqual(out, "John called <PHONE_NUMBER>")

    def test_no_pii_is_unchanged(self):
        text = "The meeting is at 3 pm in room 204."
        self.assertEqual(redact_text(text), text)

    def test_empty_and_whitespace(self):
        self.assertEqual(redact_text(""), "")
        self.assertEqual(redact_text("   "), "   ")

    def test_invalid_text_types(self):
        for bad in (None, 123, ["a"]):
            with self.assertRaises(RedactorError):
                redact_text(bad)

    def test_pii_only_input(self):
        self.assertEqual(redact_text("336-555-0123", ["PHONE_NUMBER"]),
                         "<PHONE_NUMBER>")


class TestExtras(unittest.TestCase):
    """Summary, batch, and file features"""
    def test_summary_counts(self):
        counts = summarize("Call 336-555-0123 or 212-555-0198", ["PHONE_NUMBER"])
        self.assertEqual(counts, {"PHONE_NUMBER": 2})

    def test_summary_no_pii(self):
        self.assertEqual(summarize("hello there"), {})

    def test_batch_lines_keep_blank_lines(self):
        out = redact_lines("336-555-0123\n\nhello", ["PHONE_NUMBER"])
        self.assertEqual(out, "<PHONE_NUMBER>\n\nhello")

    def test_file_round_trip(self):
        # Use unique paths next to this test file so no system temp location
        # or directory cleanup permissions are required.
        folder = os.path.dirname(os.path.abspath(__file__))
        suffix = uuid.uuid4().hex
        src = os.path.join(folder, f".sprint3-in-{suffix}.txt")
        dst = os.path.join(folder, f".sprint3-out-{suffix}.txt")
        try:
            with open(src, "w", encoding="utf-8") as handle:
                handle.write("Call 336-555-0123\nNo PII here")
            redact_file(src, dst, ["PHONE_NUMBER"])
            with open(dst, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "Call <PHONE_NUMBER>\nNo PII here")
        finally:
            for path in (src, dst):
                if os.path.exists(path):
                    os.remove(path)

    def test_missing_file(self):
        with self.assertRaises(RedactorError):
            redact_file("does_not_exist.txt", "out.txt")


class TestCommandLine(unittest.TestCase):
    """CLI success and user-facing error paths."""
    def test_text_input_and_summary(self):
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["--text", "hello", "--summary"]), 0)
        self.assertIn("hello", stdout.getvalue())
        self.assertIn("Found: nothing", stdout.getvalue())

    def test_unsupported_entity_is_reported(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["--text", "hello", "-e", "CREDIT_CARD"]), 1)
        self.assertIn("Unsupported entity", stderr.getvalue())

    def test_missing_file_is_reported(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["--input", "missing-sprint3-input.txt"]), 1)
        self.assertIn("File not found", stderr.getvalue())


class TestWebApp(unittest.TestCase):
    """Exercise the Flask form and error handling without model variability."""
    def setUp(self):
        import pii_web_app
        self.module = pii_web_app
        self.client = pii_web_app.app.test_client()

    def test_get_page_lists_supported_entities(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"UK_NINO", response.data)

    def test_empty_text_gets_friendly_message(self):
        response = self.client.post("/", data={"text": "   ", "entities": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter some text", response.data)

    def test_valid_post_displays_redacted_text_and_counts(self):
        with patch.object(self.module, "redact_lines", return_value="Call <PHONE_NUMBER>"), \
             patch.object(self.module, "summarize", return_value={"PHONE_NUMBER": 1}):
            response = self.client.post("/", data={
                "text": "Call 336-555-0123", "entities": "PHONE_NUMBER"
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Call &lt;PHONE_NUMBER&gt;", response.data)
        self.assertIn(b"PHONE_NUMBER: 1", response.data)

    def test_invalid_entity_is_shown_as_friendly_error(self):
        response = self.client.post("/", data={
            "text": "hello", "entities": "CREDIT_CARD"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unsupported entity", response.data)


class TestWebFileUpload(unittest.TestCase):
    """File downloads use the real redactor; invalid files never reach it."""

    def setUp(self):
        import pii_web_app
        self.module = pii_web_app
        self.client = pii_web_app.app.test_client()

    def upload(self, content, filename="notes.txt", entities="PHONE_NUMBER"):
        response = self.client.post("/redact-file", data={
            "file": (BytesIO(content), filename), "entities": entities
        })
        # Close the test client's multipart body, which may itself use a temp file.
        response.request.environ["wsgi.input"].close()
        return response

    def test_download_redacts_selected_entities_and_preserves_utf8_and_lines(self):
        response = self.upload("Café: John called 336-555-0123.\r\n\r\nDone.\n".encode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(),
                         "Café: John called <PHONE_NUMBER>.\r\n\r\nDone.\n")
        self.assertIn("notes_redacted.txt", response.headers["Content-Disposition"])
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_blank_entities_use_team_defaults_and_accept_utf8_bom(self):
        response = self.upload(b"\xef\xbb\xbfCall 336-555-0123", entities="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"Call <PHONE_NUMBER>")

    def test_no_pii_is_unchanged(self):
        response = self.upload(b"hello\n\nworld\n", filename="NOTES.TXT")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"hello\n\nworld\n")

    def test_invalid_files_get_friendly_errors_without_redaction(self):
        cases = [(b"", "notes.txt", b"file is empty"),
                 (b" \r\n\t", "notes.txt", b"file is empty"),
                 (b"\xff\xfe", "notes.txt", b"UTF-8"),
                 (b"hello", "notes.pdf", b"upload a .txt file")]
        with patch.object(self.module, "redact_lines") as redact:
            for content, filename, message in cases:
                with self.subTest(filename=filename, content=content):
                    response = self.upload(content, filename)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(message, response.data)
            redact.assert_not_called()

    def test_missing_file(self):
        response = self.client.post("/redact-file", data={"entities": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Please choose a .txt file", response.data)

    def test_unsupported_entities_do_not_return_original_file(self):
        response = self.upload(b"Call 336-555-0123", entities="CREDIT_CARD")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Unsupported entity", response.data)
        self.assertNotIn(b"336-555-0123", response.data)
        self.assertNotIn("Content-Disposition", response.headers)

    def test_filename_cannot_supply_a_path_or_html(self):
        response = self.upload(b"hello", filename="../../<script>notes.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("scriptnotes_redacted.txt", response.headers["Content-Disposition"])
        self.assertNotIn("../", response.headers["Content-Disposition"])
        self.assertNotIn("<script>", response.headers["Content-Disposition"])

    def test_file_size_boundary(self):
        limit = self.module.MAX_FILE_BYTES
        with patch.object(self.module, "redact_lines", return_value="safe") as redact:
            response = self.upload(b"a" * limit)
            self.assertEqual(response.status_code, 200)
            redact.assert_called_once()
            redact.reset_mock()
            response = self.upload(b"a" * (limit + 1))
            self.assertEqual(response.status_code, 413)
            self.assertIn(b"Upload too large", response.data)
            redact.assert_not_called()

    def test_oversized_request_gets_friendly_error(self):
        response = self.upload(b"a" * self.module.app.config["MAX_CONTENT_LENGTH"])
        self.assertEqual(response.status_code, 413)
        self.assertIn(b"Upload too large", response.data)

    def test_large_upload_stream_stays_in_memory(self):
        # Werkzeug normally spools uploads larger than 500 KB to disk.
        with self.module.app.test_request_context("/redact-file", method="POST", data={
                "file": (BytesIO(b"a" * 600_000), "notes.txt")}):
            from flask import request
            self.assertIsInstance(request.files["file"].stream, BytesIO)


if __name__ == "__main__":
    unittest.main()
