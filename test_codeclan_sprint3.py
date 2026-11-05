"""Sprint 3 tests for the Team CodeClan PII redactor.

Covers normal input, multiple occurrences, mixed entity types, text with no
PII, boundary conditions, invalid input and unusual cases for the CLI, the
core module and the web app.

Author: Sapri Sise (shared cases); entity cases by each entity owner, Team CodeClan. See README "Who did what".
"""
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from codeclan_cli import run
from codeclan_redactor import (MAX_TEXT_LENGTH, TEAM_ENTITIES, RedactorError,
                               parse_entities, redact)
from codeclan_web_app import app
from pii_scan import anonymize_text

# One valid (checksum-correct) value per team entity, with the context
# sentence used in Sprint 1/2, and an invalid (bad checksum) variant.
VALID = {
    "ABA_ROUTING_NUMBER": ("My bank routing number is {}", "021000021", "021000022"),
    "AU_ABN": ("Our ABN is {}", "51 824 753 556", "51 824 753 557"),
    "AU_ACN": ("The company ACN is {}", "004 085 616", "004 085 617"),
    "AU_MEDICARE": ("My Medicare card number is {}", "2123 45670 1", "2123 45679 1"),
    "AU_TFN": ("My tax file number is {}", "876 543 210", "876 543 211"),
}


class TestEachEntity(unittest.TestCase):
    """Each team entity is redacted on its own, and bad checksums are not."""

    def test_valid_values_are_redacted(self):
        for entity, (template, good, _bad) in VALID.items():
            with self.subTest(entity=entity):
                result = redact(template.format(good), [entity])
                self.assertEqual(result.redacted, template.format(f"<{entity}>"))
                self.assertEqual(result.counts[entity], 1)

    def test_invalid_checksums_are_kept(self):
        for entity, (template, _good, bad) in VALID.items():
            with self.subTest(entity=entity):
                text = template.format(bad)
                self.assertEqual(redact(text, [entity]).redacted, text)

    def test_matches_anonymize_text_directly(self):
        """The app must produce exactly what pii_scan.anonymize_text() does."""
        for entity, (template, good, _bad) in VALID.items():
            text = template.format(good)
            self.assertEqual(redact(text, [entity]).redacted,
                             anonymize_text(text, [entity]))

    def test_only_requested_entity_is_redacted(self):
        text = "TFN 876 543 210 and ABN 51 824 753 556"
        result = redact(text, ["AU_ABN"])
        self.assertIn("876 543 210", result.redacted)
        self.assertNotIn("51 824 753 556", result.redacted)


class TestMixedAndMultiple(unittest.TestCase):
    """Several values and entity types in one text."""

    def test_multiple_occurrences_of_same_entity(self):
        text = "Old TFN 876 543 210, new TFN 123 456 782."
        result = redact(text, ["AU_TFN"])
        self.assertEqual(result.redacted, "Old TFN <AU_TFN>, new TFN <AU_TFN>.")
        self.assertEqual(result.counts["AU_TFN"], 2)

    def test_all_team_entities_mixed(self):
        text = ("Routing number 021000021. ABN 51 824 753 556. "
                "ACN 004 085 616. Medicare 2123 45670 1. TFN 876 543 210.")
        result = redact(text, list(TEAM_ENTITIES))
        for value in ("021000021", "51 824 753 556", "004 085 616",
                      "2123 45670 1", "876 543 210"):
            self.assertNotIn(value, result.redacted)
        self.assertEqual(result.total, 5)
        # surrounding words are preserved
        for word in ("Routing number", "ABN", "ACN", "Medicare", "TFN"):
            self.assertIn(word, result.redacted)

    def test_default_entity_list_is_team_entities(self):
        self.assertEqual(parse_entities(""), list(TEAM_ENTITIES))
        result = redact("My tax file number is 876 543 210", "")
        self.assertEqual(result.redacted, "My tax file number is <AU_TFN>")

    def test_multiline_text_preserved(self):
        text = "Line one\n  ABN: 51 824 753 556\n\tLine three\n"
        result = redact(text, ["AU_ABN"])
        self.assertEqual(result.redacted, "Line one\n  ABN: <AU_ABN>\n\tLine three\n")


class TestNoPiiAndBoundaries(unittest.TestCase):
    """Text with no PII, empty input and edge positions."""

    def test_no_pii_text_unchanged(self):
        text = "The quarterly meeting is in room 204 at 3pm. Bring 12 copies."
        result = redact(text, list(TEAM_ENTITIES))
        self.assertEqual(result.redacted, text)
        self.assertEqual(result.total, 0)
        self.assertEqual(result.summary(), "No PII found.")

    def test_empty_and_whitespace_text(self):
        for text in ("", "   ", "\n\t\n"):
            with self.subTest(text=repr(text)):
                result = redact(text, ["AU_TFN"])
                self.assertEqual(result.redacted, text)
                self.assertEqual(result.total, 0)

    def test_pii_is_entire_text(self):
        self.assertEqual(redact("021000021", ["ABA_ROUTING_NUMBER"]).redacted,
                         "<ABA_ROUTING_NUMBER>")

    def test_pii_at_start_and_end_with_punctuation(self):
        text = "51 824 753 556 is the ABN; the TFN is (876 543 210)."
        result = redact(text, ["AU_ABN", "AU_TFN"])
        self.assertEqual(result.redacted, "<AU_ABN> is the ABN; the TFN is (<AU_TFN>).")

    def test_digits_embedded_in_longer_number_not_redacted(self):
        text = "Order id 9021000021999 shipped."
        self.assertEqual(redact(text, ["ABA_ROUTING_NUMBER"]).redacted, text)

    def test_unicode_text_preserved(self):
        text = "Café receipt — ABN 51 824 753 556 ✓ 日本"
        self.assertEqual(redact(text, ["AU_ABN"]).redacted,
                         "Café receipt — ABN <AU_ABN> ✓ 日本")

    def test_existing_placeholder_not_counted(self):
        text = "Template: <AU_TFN>. Real TFN 876 543 210."
        result = redact(text, ["AU_TFN"])
        self.assertEqual(result.redacted, "Template: <AU_TFN>. Real TFN <AU_TFN>.")
        self.assertEqual(result.counts["AU_TFN"], 1)

    def test_text_at_length_limit(self):
        text = "a" * MAX_TEXT_LENGTH
        self.assertEqual(redact(text, ["AU_TFN"]).redacted, text)
        with self.assertRaises(RedactorError):
            redact(text + "a", ["AU_TFN"])

    def test_bytes_input(self):
        self.assertEqual(redact(b"TFN 876 543 210", ["AU_TFN"]).redacted, "TFN <AU_TFN>")
        with self.assertRaises(RedactorError):
            redact(b"\xff\xfe bad", ["AU_TFN"])


class TestFormatsAndKnownLimits(unittest.TestCase):
    """Alternative number formats, plus documented limits of pii_scan."""

    def test_unspaced_and_dashed_formats_detected(self):
        cases = {
            "TFN 876543210": ("AU_TFN", "TFN <AU_TFN>"),
            "ABN 51824753556": ("AU_ABN", "ABN <AU_ABN>"),
            "ACN 004085616": ("AU_ACN", "ACN <AU_ACN>"),
            "Medicare 2123456701": ("AU_MEDICARE", "Medicare <AU_MEDICARE>"),
            "Routing 0210-0002-1": ("ABA_ROUTING_NUMBER", "Routing <ABA_ROUTING_NUMBER>"),
        }
        for text, (entity, expected) in cases.items():
            with self.subTest(text=text):
                self.assertEqual(redact(text, [entity]).redacted, expected)

    def test_blank_list_does_not_redact_other_teams_entities(self):
        """Bug found: anonymize_text(text, []) scans ALL entities, so names
        and dates were redacted. Our blank list means team entities only."""
        text = "Meet John on March 3 2026 in room 204."
        self.assertNotEqual(anonymize_text(text, []), text)  # raw behaviour
        self.assertEqual(redact(text, "").redacted, text)    # our fix

    def test_known_limits_of_presidio_recognizers(self):
        """Documented limits: Presidio does not match these formats.
        If a future Presidio version starts matching them, update the README."""
        for text, entity in (("TFN 876-543-210", "AU_TFN"),
                             ("TFN876543210", "AU_TFN")):
            with self.subTest(text=text):
                self.assertEqual(redact(text, [entity]).redacted, text)
        # Medicare IRN suffix (/2) is left after the redacted card number.
        self.assertEqual(redact("Medicare 2123 45670 1/2", ["AU_MEDICARE"]).redacted,
                         "Medicare <AU_MEDICARE>/2")


class TestEntityParsing(unittest.TestCase):
    """Entity-list normalization and invalid entity names."""

    def test_case_spacing_and_duplicates(self):
        self.assertEqual(parse_entities(" au_tfn, AU_ABN;au_tfn  aba_routing_number "),
                         ["AU_TFN", "AU_ABN", "ABA_ROUTING_NUMBER"])
        self.assertEqual(parse_entities(["au_acn", "AU_ACN"]), ["AU_ACN"])

    def test_blank_and_none_use_defaults(self):
        for raw in (None, "", "  , ,", [], [""]):
            with self.subTest(raw=raw):
                self.assertEqual(parse_entities(raw), list(TEAM_ENTITIES))

    def test_all_keyword(self):
        entities = parse_entities("all")
        self.assertIn("AU_TFN", entities)
        self.assertIn("EMAIL_ADDRESS", entities)

    def test_unknown_entity_with_suggestion(self):
        with self.assertRaises(RedactorError) as ctx:
            parse_entities("AU_TFM")
        self.assertIn("did you mean AU_TFN", str(ctx.exception))

    def test_unknown_entity_mixed_with_valid(self):
        with self.assertRaises(RedactorError) as ctx:
            parse_entities(["AU_TFN", "NOT_A_THING"])
        self.assertIn("NOT_A_THING", str(ctx.exception))

    def test_wrong_types(self):
        for raw in (42, [1, 2], ["AU_TFN", None]):
            with self.subTest(raw=raw):
                with self.assertRaises(RedactorError):
                    parse_entities(raw)
        for text in (None, 123, ["list"]):
            with self.subTest(text=text):
                with self.assertRaises(RedactorError):
                    redact(text, ["AU_TFN"])


class TestCli(unittest.TestCase):
    """Command-line interface."""

    def _run(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_text_argument(self):
        code, out, _ = self._run("-e", "au_tfn", "TFN 876 543 210")
        self.assertEqual((code, out.strip()), (0, "TFN <AU_TFN>"))

    def test_summary(self):
        code, _, err = self._run("-s", "TFN 876 543 210, ABN 51 824 753 556")
        self.assertEqual(code, 0)
        self.assertIn("AU_ABN x1", err)
        self.assertIn("AU_TFN x1", err)

    def test_unknown_entity_exit_code(self):
        code, _, err = self._run("-e", "BOGUS", "hello")
        self.assertEqual(code, 1)
        self.assertIn("Unknown entity", err)

    def test_missing_file(self):
        code, _, err = self._run("-f", "does_not_exist_12345.txt")
        self.assertEqual(code, 1)
        self.assertIn("File not found", err)

    def test_file_and_batch(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.txt").write_text("ACN 004 085 616", encoding="utf-8")
            (tmp / "b.txt").write_text("Nothing here", encoding="utf-8")
            (tmp / "bad.txt").write_bytes(b"\xff\xfe\x00")
            out_file = tmp / "single.txt"
            self.assertEqual(self._run("-f", str(tmp / "a.txt"), "-o", str(out_file))[0], 0)
            self.assertEqual(out_file.read_text(encoding="utf-8"), "ACN <AU_ACN>")

            code, _, _ = self._run("-f", str(tmp / "a.txt"), str(tmp / "b.txt"),
                                   "--out-dir", str(tmp / "out"))
            self.assertEqual(code, 0)
            self.assertEqual((tmp / "out" / "a_redacted.txt").read_text(encoding="utf-8"),
                             "ACN <AU_ACN>")
            self.assertEqual((tmp / "out" / "b_redacted.txt").read_text(encoding="utf-8"),
                             "Nothing here")

            code, _, err = self._run("-f", str(tmp / "bad.txt"))
            self.assertEqual(code, 1)
            self.assertIn("UTF-8", err)

    def test_usage_errors(self):
        for argv in (["text", "-f", "x.txt"], ["-f", "a.txt", "b.txt", "-o", "o.txt"]):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit) as ctx:
                    self._run(*argv)
                self.assertEqual(ctx.exception.code, 2)

    def test_empty_input_note(self):
        code, out, err = self._run("")
        self.assertEqual((code, out.strip()), (0, ""))
        self.assertIn("input is empty", err)

    def test_list_entities(self):
        code, out, _ = self._run("--list-entities")
        self.assertEqual(code, 0)
        self.assertIn("AU_MEDICARE", out)


class TestWebApp(unittest.TestCase):
    """Flask web app and JSON API."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"CodeClan PII Redactor", resp.data)

    def test_form_redaction_highlights_and_counts(self):
        resp = self.client.post("/", data={"entity": ["AU_TFN"], "extra": "",
                                           "text": "TFN 876 543 210", "action": "redact"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<mark>&lt;AU_TFN&gt;</mark>", resp.data)
        self.assertNotIn(b"876 543 210</pre>", resp.data)

    def test_form_escapes_html(self):
        resp = self.client.post("/", data={"entity": ["AU_TFN"],
                                           "text": "<script>alert(1)</script>"})
        self.assertNotIn(b"<script>alert(1)</script>", resp.data)

    def test_form_empty_text_and_bad_entity(self):
        resp = self.client.post("/", data={"text": "   "})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Please enter some text", resp.data)
        resp = self.client.post("/", data={"extra": "NOPE", "text": "hi"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Unknown entity", resp.data)

    def test_form_no_entities_selected(self):
        """Bug fix: unticking every box used to silently use the defaults."""
        resp = self.client.post("/", data={"extra": "", "text": "TFN 876 543 210"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Select at least one entity", resp.data)

    def test_file_upload_and_download(self):
        data = {"entity": ["AU_ABN"], "action": "download",
                "file": (io.BytesIO(b"ABN 51 824 753 556"), "in.txt")}
        resp = self.client.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp.headers["Content-Disposition"])
        self.assertEqual(resp.data, b"ABN <AU_ABN>")

    def test_oversized_upload_shows_page_error(self):
        data = {"file": (io.BytesIO(b"a" * 500_000), "big.txt")}
        resp = self.client.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 413)
        self.assertIn(b"Input too large", resp.data)
        self.assertIn(b"CodeClan PII Redactor", resp.data)  # a page, not raw JSON

    def test_non_utf8_upload(self):
        data = {"file": (io.BytesIO(b"\xff\xfe\x00"), "bin.txt")}
        resp = self.client.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 400)

    def test_api(self):
        resp = self.client.post("/api/redact", json={"text": "Medicare 2123 45670 1",
                                                     "entities": ["AU_MEDICARE"]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["redacted"], "Medicare <AU_MEDICARE>")
        self.assertEqual(resp.get_json()["counts"], {"AU_MEDICARE": 1})

    def test_api_invalid(self):
        self.assertEqual(self.client.post("/api/redact", data="nope").status_code, 400)
        self.assertEqual(self.client.post("/api/redact", json=["x"]).status_code, 400)
        self.assertEqual(self.client.post("/api/redact", json={"text": 5}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
