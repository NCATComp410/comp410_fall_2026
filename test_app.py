import unittest
from app import process_anonymization, parse_entity_list, SUPPORTED_ENTITIES

class TestPIIAnonymizer(unittest.TestCase):

    def setUp(self):
        self.default_entities = list(SUPPORTED_ENTITIES)

    # --- Normal Functionality ---
    def test_single_entity_redaction(self):
        text = "Call me at 212-555-0199 tomorrow."
        redacted, _ = process_anonymization(text, ["PHONE_NUMBER"])
        self.assertNotIn("212-555-0199", redacted)
        self.assertIn("Call me at", redacted)

    def test_mixed_entities(self):
        text = "Email test@example.com or reach out via 212-555-0199."
        redacted, _ = process_anonymization(text, ["EMAIL_ADDRESS", "PHONE_NUMBER"])
        self.assertNotIn("test@example.com", redacted)
        self.assertNotIn("212-555-0199", redacted)

    def test_multiple_occurrences(self):
        text = "Primary: 212-555-0199, Secondary: 212-555-0188."
        redacted, _ = process_anonymization(text, ["PHONE_NUMBER"])
        self.assertNotIn("212-555-0199", redacted)
        self.assertNotIn("212-555-0188", redacted)

    # --- Edge Cases & Boundaries ---
    def test_no_pii_present(self):
        text = "This sentence contains strictly public text with no personal data."
        redacted, _ = process_anonymization(text, self.default_entities)
        self.assertEqual(redacted, text)

    def test_empty_string(self):
        redacted, _ = process_anonymization("", self.default_entities)
        self.assertEqual(redacted, "")

    def test_whitespace_and_newlines(self):
        text = "\n\n   \t  \n"
        redacted, _ = process_anonymization(text, self.default_entities)
        self.assertEqual(redacted, text)

    def test_pii_at_string_boundaries(self):
        text = "212-555-0199"
        redacted, _ = process_anonymization(text, ["PHONE_NUMBER"])
        self.assertNotIn("212-555-0199", redacted)

    # --- Entity Parsing & Validation ---
    def test_unsupported_entity_filtering(self):
        entities = parse_entity_list(["INVALID_ENTITY_TYPE", "PHONE_NUMBER"])
        self.assertIn("PHONE_NUMBER", entities)
        self.assertNotIn("INVALID_ENTITY_TYPE", entities)

    def test_case_insensitivity_and_formatting(self):
        entities = parse_entity_list(["phone_number,email_address"])
        self.assertIn("PHONE_NUMBER", entities)
        self.assertIn("EMAIL_ADDRESS", entities)

if __name__ == "__main__":
    unittest.main()
