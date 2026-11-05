"""A small web interface for the PII anonymizer."""
from email.parser import BytesParser
from email.policy import default as email_policy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from urllib.parse import parse_qs

from pii_scan import analyze_text, anonymize_text


SUPPORTED_ENTITIES = set(analyze_text("", [], show_supported=True))
MAX_REQUEST_SIZE = 1_000_000
ALLOWED_UPLOAD_EXTENSIONS = (".txt", ".csv", ".log", ".md")


class UploadError(ValueError):
    """Raised when an uploaded file can't be used; the message is shown to the user."""


def parse_multipart(content_type: str, body: bytes) -> tuple[dict, tuple | None]:
    """Split a multipart/form-data body into text fields and one optional file.

    Returns (fields, upload) where fields maps names to strings and upload
    is (filename, file_bytes) or None when no file was chosen.
    """
    message = BytesParser(policy=email_policy).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + body
    )
    fields, upload = {}, None
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        payload = part.get_payload(decode=True) or b""
        filename = part.get_filename()
        if filename is not None:
            if filename:
                upload = (filename, payload)
        elif name:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, upload


def read_upload(filename: str, data: bytes) -> str:
    """Validate an uploaded file and return its text."""
    if not filename.lower().endswith(ALLOWED_UPLOAD_EXTENSIONS):
        allowed = ", ".join(ALLOWED_UPLOAD_EXTENSIONS)
        raise UploadError(f"Unsupported file type. Upload one of: {allowed}.")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UploadError("The uploaded file must be UTF-8 text.") from exc


def parse_entities(raw_entities: str) -> list[str]:
    """Parse comma- or newline-separated entity names."""
    return list(dict.fromkeys(
        entity.strip()
        for line in raw_entities.splitlines()
        for entity in line.split(",")
        if entity.strip()
    ))


def render_page(entities: str = "", text: str = "", result: str = "",
                error: str = "") -> str:
    """Render the input form and any result or validation error."""
    result_section = (
        f'<section aria-labelledby="result-heading"><h2 id="result-heading">'
        f'Redacted text</h2><pre>{escape(result)}</pre>'
        f'<form method="post" action="/download">'
        f'<input type="hidden" name="result" value="{escape(result)}">'
        f'<button type="submit">Download as .txt</button></form></section>'
        if result else ""
    )
    error_section = f'<p class="error" role="alert">{escape(error)}</p>' if error else ""
    supported = ", ".join(sorted(SUPPORTED_ENTITIES))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PII Text Anonymizer</title>
  <style>
    body {{ font: 16px system-ui, sans-serif; line-height: 1.5; margin: 2rem auto;
           max-width: 52rem; padding: 0 1rem; color: #202124; }}
    label {{ display: block; font-weight: 600; margin-top: 1rem; }}
    textarea {{ box-sizing: border-box; display: block; font: inherit; margin-top: .35rem;
                min-height: 5rem; padding: .6rem; width: 100%; }}
    #text {{ min-height: 12rem; }}
    button {{ background: #1457a6; border: 0; border-radius: .25rem; color: white;
              cursor: pointer; font: inherit; margin-top: 1rem; padding: .65rem 1rem; }}
    pre {{ background: #f3f4f6; overflow-wrap: anywhere; padding: 1rem;
           white-space: pre-wrap; }}
    .error {{ color: #a11212; }}
    details {{ margin-top: 1rem; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <main>
    <h1>PII Text Anonymizer</h1>
    <p>Enter entity types (comma- or newline-separated) and the text to scan.
       Matches are replaced with their type, such as <code>&lt;EMAIL_ADDRESS&gt;</code>.</p>
    {error_section}
    <form method="post" enctype="multipart/form-data">
      <label for="entities">Entity types</label>
      <textarea id="entities" name="entities" required
                placeholder="EMAIL_ADDRESS, PHONE_NUMBER">{escape(entities)}</textarea>
      <label for="text">Text to anonymize</label>
      <textarea id="text" name="text">{escape(text)}</textarea>
      <label for="file">Or upload a text file (.txt, .csv, .log, .md)</label>
      <input id="file" name="file" type="file" accept=".txt,.csv,.log,.md">
      <button type="submit">Anonymize text</button>
    </form>
    {result_section}
    <details>
      <summary>Supported entity types</summary>
      <p>{escape(supported)}</p>
    </details>
  </main>
</body>
</html>"""


class AnonymizerHandler(BaseHTTPRequestHandler):
    """Handle the anonymization form."""

    def do_GET(self):
        body = render_page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_type = self.headers.get_content_type()
        if content_type not in ("application/x-www-form-urlencoded", "multipart/form-data"):
            self.send_error(400, "Expected form data.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid content length.")
            return
        if content_length < 0 or content_length > MAX_REQUEST_SIZE:
            self.send_error(413, "Form submission is too large.")
            return

        body = self.rfile.read(content_length)
        if content_type == "multipart/form-data":
            fields, upload = parse_multipart(self.headers.get("Content-Type"), body)
        else:
            parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
            fields = {name: values[0] for name, values in parsed.items()}
            upload = None

        if self.path == "/download":
            self._send_download(fields.get("result", ""))
            return

        raw_entities = fields.get("entities", "")
        text = fields.get("text", "")
        if upload:
            try:
                text = read_upload(*upload)
            except UploadError as exc:
                self._send_page(raw_entities, text, error=str(exc))
                return
        entities = parse_entities(raw_entities)

        if not entities:
            self._send_page(raw_entities, text, error="Enter at least one entity type.")
            return
        unsupported = [entity for entity in entities if entity not in SUPPORTED_ENTITIES]
        if unsupported:
            names = ", ".join(unsupported)
            self._send_page(
                raw_entities,
                text,
                error=f"Unsupported entity type(s): {names}. See the supported list below.",
            )
            return
        if not text.strip():
            self._send_page(raw_entities, text,
                            error="Enter text to anonymize or upload a file.")
            return

        result = anonymize_text(text, entities)
        self._send_page(raw_entities, text, result=result)

    def _send_page(self, entities: str = "", text: str = "", result: str = "",
                   error: str = ""):
        body = render_page(entities, text, result, error).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_download(self, result: str):
        """Send the redacted text as a downloadable redacted.txt file."""
        body = result.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="redacted.txt"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), AnonymizerHandler)
    print(f"PII anonymizer running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PII anonymizer.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
