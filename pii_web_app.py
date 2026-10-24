"""Team Z web app for the PII redactor (Sprint 3).

Uses redact_text() and summarize() from pii_redactor.py, which wrap
pii_scan.anonymize_text() and limit the app to Team Z's entities.

Run:  python pii_web_app.py   (then open the forwarded port 5000 in Codespaces)
"""
import os
from flask import Flask, render_template_string, request

from pii_redactor import (RedactorError, SUPPORTED_ENTITIES,
                          redact_lines, summarize)

app = Flask(__name__)

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
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if result is not none %}
  <h2>Result</h2><pre>{{ result }}</pre>
  <p class="hint">Found: {{ found }}</p>
{% endif %}
"""


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