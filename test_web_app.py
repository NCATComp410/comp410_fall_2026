"""Tests for the PII anonymizer web form helpers."""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import threading
import unittest
from urllib.parse import urlencode

import app


class TestWebApp(unittest.TestCase):
    """Test entity parsing and safe page rendering."""

    def test_parse_entities_accepts_commas_and_newlines(self):
        self.assertEqual(
            app.parse_entities("EMAIL_ADDRESS, PHONE_NUMBER\nEMAIL_ADDRESS"),
            ["EMAIL_ADDRESS", "PHONE_NUMBER"],
        )

    def test_render_page_escapes_user_content(self):
        page = app.render_page(
            entities="<script>",
            text="<script>alert(1)</script>",
            result="<EMAIL_ADDRESS>",
            error="Invalid <entity>",
        )
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;EMAIL_ADDRESS&gt;", page)
        self.assertIn("Invalid &lt;entity&gt;", page)

    def test_post_anonymizes_text_and_returns_redacted_result(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.AnonymizerHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port)
            body = urlencode({
                "entities": "EMAIL_ADDRESS",
                "text": "Email: user@example.com",
            })
            connection.request(
                "POST",
                "/",
                body=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = connection.getresponse()
            page = response.read().decode("utf-8")
            connection.close()

            self.assertEqual(response.status, 200)
            self.assertIn("Email: &lt;EMAIL_ADDRESS&gt;", page)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
