"""Simple test web app for pii_scan.anonymize_text().

Run:  python pii_web_app.py   (then open the forwarded port 5000 in Codespaces)
"""
import os
from flask import Flask, render_template_string, request

from pii_scan import anonymize_text

app = Flask(__name__)

PAGE = """<!doctype html>
<title>PII Anonymizer</title>
<style>
  body { font-family: sans-serif; max-width: 800px; margin: 2em auto; }
  textarea, input[type=text] { width: 100%; box-sizing: border-box; }
  pre { background: #f4f4f4; padding: 1em; white-space: pre-wrap; }
  .error { color: #b00; }
</style>
<h1>PII Anonymizer</h1>
<form method="post">
  <p><label>Entities to search for (comma or space separated; blank = all)<br>
  <input type="text" name="entities" value="{{ entities }}"
         placeholder="PERSON, EMAIL_ADDRESS, PHONE_NUMBER"></label></p>
  <p><label>Text to anonymize<br>
  <textarea name="text" rows="8">{{ text }}</textarea></label></p>
  <button type="submit">Anonymize</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if result is not none %}<h2>Result</h2><pre>{{ result }}</pre>{% endif %}
"""


@app.route("/", methods=["GET", "POST"])
def index():
    entities = request.form.get("entities", "PERSON, EMAIL_ADDRESS, PHONE_NUMBER")
    text = request.form.get("text", "")
    result = error = None
    if request.method == "POST" and text.strip():
        entity_list = [e.strip().upper()
                       for e in entities.replace(",", " ").split() if e.strip()]
        try:
            result = anonymize_text(text, entity_list)
        except Exception as exc:  # e.g. unknown entity name
            error = f"Error: {exc}"
    return render_template_string(PAGE, entities=entities, text=text,
                                  result=result, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
