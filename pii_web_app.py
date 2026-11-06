"""Team Z web app for the PII redactor (Sprint 3).

Uses redact_text() and summarize() from pii_redactor.py, which wrap
pii_scan.anonymize_text() and limit the app to Team Z's entities.

Run:  python pii_web_app.py   (then open the forwarded port 5000 in Codespaces)
"""
import os
from io import BytesIO
from flask import Flask, Request, render_template_string, request, send_file
from werkzeug.utils import secure_filename

from pii_redactor import (RedactorError, SUPPORTED_ENTITIES,
                          redact_lines, summarize)

MAX_FILE_BYTES = 1024 * 1024


class MemoryUploadRequest(Request):
    """Keep uploaded PII in memory instead of spooling it to a temp file."""

    def _get_file_stream(self, total_content_length, content_type, filename=None,
                         content_length=None):
        return BytesIO()


app = Flask(__name__)
app.request_class = MemoryUploadRequest
# Allow multipart form overhead in addition to the 1 MiB file limit.
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES + 64 * 1024

DEFAULT_ENTITIES = ", ".join(SUPPORTED_ENTITIES)
EXAMPLE = ("Maria Garcia lives in London. Call her at 336-555-0123.\n"
           "NHS number: 401 023 2137, NI number: AB123456C.")

PAGE = """<!doctype html>
<title>Team Z PII Redactor</title>
<style>
  body { font-family: sans-serif; max-width: 800px; margin: 2em auto; }
  textarea, input[type=text] { width: 100%; box-sizing: border-box; }
  pre { background: #f4f4f4; padding: 1em; white-space: pre-wrap; }
  .error { color: #b00; }
  .hint { color: #555; font-size: 0.9em; }
</style>
<h1>Team Z PII Redactor</h1>
<p class="hint">Supported entities: {{ supported }}</p>
<form method="post">
  <p><label>Entities to redact (comma or space separated; blank = all of them)<br>
  <input type="text" name="entities" value="{{ entities }}"></label></p>
  <p><label>Text to redact (each line is handled on its own)<br>
  <textarea name="text" rows="8">{{ text }}</textarea></label></p>
  <button type="submit">Redact</button>
  <button type="submit" name="example" value="1">Load example</button>
</form>
<h2>Redact a text file</h2>
<p class="hint">Upload a UTF-8 .txt file up to 1 MiB (1,048,576 bytes).
The file is processed in memory and the redacted result downloads immediately.</p>
<form method="post" action="{{ url_for('redact_upload') }}" enctype="multipart/form-data">
  <p><label>Entities to redact (blank = all five)<br>
  <input type="text" name="entities" value="{{ entities }}"></label></p>
  <p><label>Text file <input type="file" name="file" accept=".txt" required></label></p>
  <button type="submit">Download redacted file</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if result is not none %}
  <h2>Result</h2><pre>{{ result }}</pre>
  <p class="hint">Found: {{ found }}</p>
{% endif %}
"""


@app.errorhandler(413)
def upload_too_large(exc):
    return render_template_string(
        PAGE, entities=DEFAULT_ENTITIES, text="", result=None, found=None,
        error="Upload too large. Choose a .txt file up to 1 MiB.",
        supported=", ".join(SUPPORTED_ENTITIES)), 413


@app.post("/redact-file")
def redact_upload():
    """Validate an uploaded text file and return only its redacted contents."""
    entities = request.form.get("entities", "")
    upload = request.files.get("file")
    try:
        if upload is None or not upload.filename:
            raise RedactorError("Please choose a .txt file to redact.")
        if not upload.filename.lower().endswith(".txt"):
            raise RedactorError("Please upload a .txt file.")
        content = upload.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            return upload_too_large(None)
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise RedactorError("The file must contain UTF-8 text.") from exc
        if not text.strip():
            raise RedactorError("The file is empty. Please choose a file containing text.")
        entity_list = entities.replace(",", " ").split()
        result = redact_lines(text, entity_list)
    except RedactorError as exc:
        return render_template_string(
            PAGE, entities=entities, text="", result=None, found=None,
            error=f"Error: {exc}", supported=", ".join(SUPPORTED_ENTITIES)), 400

    filename = secure_filename(upload.filename) or "upload.txt"
    stem = os.path.splitext(filename)[0] or "upload"
    response = send_file(BytesIO(result.encode("utf-8")),
                         mimetype="text/plain", as_attachment=True,
                         download_name=f"{stem}_redacted.txt")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    entities = request.form.get("entities", DEFAULT_ENTITIES)
    text = request.form.get("text", "")
    if request.form.get("example"):
        text, entities = EXAMPLE, DEFAULT_ENTITIES
    result = error = found = None
    if request.method == "POST" and text.strip() and not request.form.get("example"):
        entity_list = [e for e in entities.replace(",", " ").split() if e]
        try:
            result = redact_lines(text, entity_list)
            counts = summarize(text, entity_list)
            found = ", ".join(f"{name}: {n}" for name, n in counts.items()) or "nothing"
        except RedactorError as exc:
            error = f"Error: {exc}"
    elif request.method == "POST" and not text.strip() and not request.form.get("example"):
        error = "Please enter some text to redact."
    return render_template_string(PAGE, entities=entities, text=text, result=result,
                                  error=error, found=found,
                                  supported=", ".join(SUPPORTED_ENTITIES))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
