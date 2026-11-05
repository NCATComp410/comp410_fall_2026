"""Tests for the file upload and download enhancements in app.py.

Run:  python -m unittest test_file_upload -v
"""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import threading
import unittest
from urllib.parse import urlencode

import app

# One server for the whole file. Every def here must start with "test"
# (class rule in test_pii_scan.py), so there are no helper functions.
SERVER = ThreadingHTTPServer(("127.0.0.1", 0), app.AnonymizerHandler)
threading.Thread(target=SERVER.serve_forever, daemon=True).start()
PORT = SERVER.server_port

BOUNDARY = "----team1boundary"
MULTIPART = f"multipart/form-data; boundary={BOUNDARY}"
TEAM_1 = "ES_NIE, ES_NIF, FI_PERSONAL_IDENTITY_CODE, IBAN_CODE, IP_ADDRESS"


class TestFileUpload(unittest.TestCase):
    """Upload a file instead of pasting text, then download the result."""

    def test_upload_txt_file_is_redacted(self):
        """A .txt upload is read and every Team 1 entity in it is redacted."""
        file_text = "NIE X1234567L\nIBAN GB29NWBK60161331926819\nserver 10.0.0.1"
        body = (
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="entities"\r\n\r\n'
            f"{TEAM_1}\r\n"
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="text"\r\n\r\n'
            "\r\n"
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="file"; filename="notes.txt"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{file_text}\r\n"
            f"--{BOUNDARY}--\r\n"
        ).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", PORT)
        connection.request("POST", "/", body=body, headers={"Content-Type": MULTIPART})
        response = connection.getresponse()
        page = response.read().decode("utf-8")
        connection.close()

        self.assertEqual(response.status, 200)
        self.assertIn("NIE &lt;ES_NIE&gt;", page)
        self.assertIn("IBAN &lt;IBAN_CODE&gt;", page)
        self.assertIn("server &lt;IP_ADDRESS&gt;", page)
        self.assertNotIn("X1234567L</pre>", page)

    def test_multipart_without_file_uses_pasted_text(self):
        """Submitting the form with no file chosen still redacts the textarea."""
        body = (
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="entities"\r\n\r\n'
            "IP_ADDRESS\r\n"
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="text"\r\n\r\n'
            "ip 8.8.8.8\r\n"
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="file"; filename=""\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
            "\r\n"
            f"--{BOUNDARY}--\r\n"
        ).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", PORT)
        connection.request("POST", "/", body=body, headers={"Content-Type": MULTIPART})
        page = connection.getresponse().read().decode("utf-8")
        connection.close()
        self.assertIn("ip &lt;IP_ADDRESS&gt;", page)

    def test_bad_uploads_show_errors(self):
        """Wrong file types and non-UTF-8 files give a message, not a crash."""
        cases = [
            ("photo.png", b"not really an image", "Unsupported file type"),
            ("bad.txt", b"\xff\xfe\x00 not utf-8", "must be UTF-8 text"),
        ]
        for filename, data, message in cases:
            with self.subTest(filename=filename):
                body = (
                    f"--{BOUNDARY}\r\n"
                    'Content-Disposition: form-data; name="entities"\r\n\r\n'
                    "IP_ADDRESS\r\n"
                    f"--{BOUNDARY}\r\n"
                    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                    "Content-Type: application/octet-stream\r\n\r\n"
                ).encode("utf-8") + data + f"\r\n--{BOUNDARY}--\r\n".encode("utf-8")
                connection = HTTPConnection("127.0.0.1", PORT)
                connection.request("POST", "/", body=body,
                                   headers={"Content-Type": MULTIPART})
                response = connection.getresponse()
                page = response.read().decode("utf-8")
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertIn(message, page)

    def test_empty_upload_and_empty_text_shows_error(self):
        """An empty file with no pasted text asks the user for input."""
        body = (
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="entities"\r\n\r\n'
            "IP_ADDRESS\r\n"
            f"--{BOUNDARY}\r\n"
            'Content-Disposition: form-data; name="file"; filename="empty.txt"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            "\r\n"
            f"--{BOUNDARY}--\r\n"
        ).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", PORT)
        connection.request("POST", "/", body=body, headers={"Content-Type": MULTIPART})
        page = connection.getresponse().read().decode("utf-8")
        connection.close()
        self.assertIn("Enter text to anonymize or upload a file.", page)

    def test_download_returns_redacted_text_file(self):
        """The download button returns the result as redacted.txt."""
        result = "line one <IP_ADDRESS>\nline two <ES_NIE>"
        connection = HTTPConnection("127.0.0.1", PORT)
        connection.request("POST", "/download", body=urlencode({"result": result}),
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = connection.getresponse()
        data = response.read().decode("utf-8")
        connection.close()

        self.assertEqual(response.status, 200)
        self.assertEqual(data, result)
        self.assertIn('filename="redacted.txt"',
                      response.getheader("Content-Disposition"))

    def test_result_page_has_download_button_and_upload_field(self):
        """The page shows the upload field, and a download button with a result."""
        page = app.render_page(entities="IP_ADDRESS", text="x", result="<IP_ADDRESS>")
        self.assertIn('type="file"', page)
        self.assertIn('enctype="multipart/form-data"', page)
        self.assertIn('action="/download"', page)
        self.assertIn('value="&lt;IP_ADDRESS&gt;"', page)


if __name__ == "__main__":
    unittest.main()
