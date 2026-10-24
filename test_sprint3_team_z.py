"""Sprint 3 tests for the Team Z PII redactor."""
import os
import tempfile
import unittest

from pii_redactor import (RedactorError, SUPPORTED_ENTITIES, parse_entities,
                          redact_file, redact_lines, redact_text, summarize)


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
        with tempfile.TemporaryDirectory() as folder:
            src = os.path.join(folder, "in.txt")
            dst = os.path.join(folder, "out.txt")
            with open(src, "w", encoding="utf-8") as handle:
                handle.write("Call 336-555-0123\nNo PII here")
            redact_file(src, dst, ["PHONE_NUMBER"])
            with open(dst, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "Call <PHONE_NUMBER>\nNo PII here")

    def test_missing_file(self):
        with self.assertRaises(RedactorError):
            redact_file("does_not_exist.txt", "out.txt")


if __name__ == "__main__":
    unittest.main()