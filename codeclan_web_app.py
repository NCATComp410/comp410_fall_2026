"""Team CodeClan - PII redactor web app.

Run:  python codeclan_web_app.py   (then open http://localhost:5000, or the
forwarded port 5000 in Codespaces)

Features:
  * entity checkboxes for the team's entities plus a free-text field for others
  * paste text or upload a .txt file
  * redacted output with highlighted placeholders and a per-entity summary
  * download the redacted text as a file
  * JSON API: POST /api/redact {"text": "...", "entities": [...]}

Author: Kamryn & Caleb, Team CodeClan. See README "Who did what".
"""
import os

from flask import Flask, Response, jsonify, render_template_string, request
from markupsafe import Markup, escape

from codeclan_redactor import (MAX_TEXT_LENGTH, TEAM_ENTITIES, RedactorError,
                               redact)

app = Flask(__name__)
# Reject uploads/bodies far larger than the text limit (4 bytes per char max).
app.config["MAX_CONTENT_LENGTH"] = MAX_TEXT_LENGTH * 4 + 64 * 1024

SAMPLE_TEXT = (
    "Hi team, please pay the invoice to routing number 021000021.\n"
    "Supplier ABN: 51 824 753 556, company ACN 004 085 616.\n"
    "Employee TFN 876 543 210, Medicare card 2123 45670 1.\n"
    "The meeting is on Tuesday in room 204."
)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodeClan PII Redactor</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2em auto; padding: 0 1em; color: #222; }
  h1 { margin-bottom: .2em; } .sub { color: #666; margin-top: 0; }
  fieldset { border: 1px solid #ccc; border-radius: 6px; margin-bottom: 1em; }
  label.ent { display: inline-block; min-width: 260px; margin: .2em 0; }
  textarea, input[type=text] { width: 100%; box-sizing: border-box; font: inherit; padding: .4em; }
  pre { background: #f6f6f6; padding: 1em; white-space: pre-wrap; border-radius: 6px; }
  mark { background: #ffd54f; padding: 0 2px; border-radius: 3px; }
  .error { color: #b00020; font-weight: 600; } .ok { color: #1b5e20; }
  button { padding: .5em 1.2em; font: inherit; cursor: pointer; }
  table { border-collapse: collapse; } td, th { padding: .2em .8em; border-bottom: 1px solid #ddd; text-align: left; }
</style></head><body>
<h1>CodeClan PII Redactor</h1>
<p class="sub">COMP410 Sprint 3 &middot; powered by <code>pii_scan.anonymize_text()</code></p>
<form method="post" enctype="multipart/form-data">
  <fieldset><legend>Entities to redact</legend>
  {% for name, label in team_entities.items() %}
    <label class="ent"><input type="checkbox" name="entity" value="{{ name }}"
      {% if name in checked %}checked{% endif %}> {{ name }} <small>({{ label }})</small></label>
  {% endfor %}
  <p><label>Other entities (comma separated, or ALL)<br>
  <input type="text" name="extra" value="{{ extra }}" placeholder="e.g. EMAIL_ADDRESS, PERSON"></label></p>
  </fieldset>
  <p><label>Text to anonymize<br>
  <textarea name="text" rows="8">{{ text }}</textarea></label></p>
  <p><label>&hellip;or upload a UTF-8 .txt file: <input type="file" name="file" accept=".txt,text/plain"></label></p>
  <button type="submit" name="action" value="redact">Anonymize</button>
  <button type="submit" name="action" value="sample">Load sample text</button>
  <button type="submit" name="action" value="download">Download redacted .txt</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if result %}
  <h2>Result</h2>
  <pre>{{ highlighted }}</pre>
  {% if result.total %}
    <table><tr><th>Entity</th><th>Redacted</th></tr>
    {% for name, n in result.counts|dictsort %}<tr><td>{{ name }}</td><td>{{ n }}</td></tr>{% endfor %}
    </table>
  {% else %}<p class="ok">No PII found for the selected entities.</p>{% endif %}
{% endif %}
</body></html>"""


def _highlight(redacted: str, entities: list) -> Markup:
    """HTML-escape the output, then wrap each <ENTITY> placeholder in <mark>."""
    html = str(escape(redacted))
    for name in entities:
        token = str(escape(f"<{name}>"))
        html = html.replace(token, f"<mark>{token}</mark>")
    return Markup(html)


def _form_entities() -> list:
    return request.form.getlist("entity") + [request.form.get("extra", "")]


def _form_text() -> str:
    upload = request.files.get("file")
    if upload and upload.filename:
        data = upload.read()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RedactorError("Uploaded file is not UTF-8 text.") from exc
    return request.form.get("text", "")


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page: form + result."""
    ctx = {"team_entities": TEAM_ENTITIES, "checked": list(TEAM_ENTITIES),
           "extra": "", "text": "", "result": None, "highlighted": "", "error": None}
    if request.method == "GET":
        return render_template_string(PAGE, **ctx)

    action = request.form.get("action", "redact")
    ctx["checked"] = request.form.getlist("entity")
    ctx["extra"] = request.form.get("extra", "")
    if action == "sample":
        ctx.update(text=SAMPLE_TEXT, checked=list(TEAM_ENTITIES))
        return render_template_string(PAGE, **ctx)

    try:
        text = _form_text()
        ctx["text"] = text
        if not text.strip():
            raise RedactorError("Please enter some text or upload a file.")
        # Unticking every box must not silently fall back to the defaults.
        if not "".join(_form_entities()).strip():
            raise RedactorError("Select at least one entity (or type ALL).")
        result = redact(text, _form_entities())
    except RedactorError as exc:
        ctx["error"] = f"Error: {exc}"
        return render_template_string(PAGE, **ctx), 400

    if action == "download":
        return Response(result.redacted, mimetype="text/plain",
                        headers={"Content-Disposition": "attachment; filename=redacted.txt"})
    ctx.update(result=result, highlighted=_highlight(result.redacted, result.entities))
    return render_template_string(PAGE, **ctx)


@app.post("/api/redact")
def api_redact():
    """JSON API. Body: {"text": str, "entities": list|str (optional)}."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Request body must be a JSON object."), 400
    try:
        result = redact(payload.get("text"), payload.get("entities"))
    except RedactorError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(redacted=result.redacted, entities=result.entities,
                   counts=dict(result.counts), total=result.total)


@app.errorhandler(413)
def too_large(_exc):
    """Friendly message for oversized uploads."""
    return jsonify(error=f"Input too large (limit {MAX_TEXT_LENGTH:,} characters)."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
