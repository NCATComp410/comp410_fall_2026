"""Tests for the Flask PII web app."""
import io
import sys
import types
import unittest
from unittest.mock import patch

from pii_web_app import app


class TestPIIWebApp(unittest.TestCase):
    """Exercise the web form without initializing the NLP model."""

    def test_selected_entities_are_anonymized(self):
        scanner = types.ModuleType("pii_scan")
        scanner.anonymize_text = lambda text, entities: f"{text} => <{','.join(entities)}>"
        with patch.dict(sys.modules, {"pii_scan": scanner}):
            response = app.test_client().post(
                "/",
                data={
                    "input_text": "mail me at test@example.com",
                    "entity_types": ["EMAIL_ADDRESS", "UNKNOWN"],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"mail me at test@example.com =&gt; &lt;EMAIL_ADDRESS&gt;", response.data)

    def test_text_file_upload_is_loaded(self):
        scanner = types.ModuleType("pii_scan")
        scanner.anonymize_text = lambda text, entities: f"<EMAIL_ADDRESS> {text}"
        with patch.dict(sys.modules, {"pii_scan": scanner}):
            response = app.test_client().post(
                "/",
                data={
                    "entity_types": "EMAIL_ADDRESS",
                    "input_file": (io.BytesIO(b"test@example.com"), "sample.txt"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"&lt;EMAIL_ADDRESS&gt; test@example.com", response.data)


if __name__ == "__main__":
    unittest.main()