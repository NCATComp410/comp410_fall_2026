"""Team 3 Web Application for PII Detection and Anonymization (Sprint 3).

Builds on the sprint3-team-null sample web application and integrates with
pii_redactor.py (which invokes anonymize_text() from pii_scan.py). Supports
Team 3's five Italian PII entities:
  IT_DRIVER_LICENSE, IT_FISCAL_CODE, IT_IDENTITY_CARD, IT_PASSPORT, IT_VAT_CODE

Run:
  python pii_web_app.py
Then open http://localhost:5000 (or forwarded port 5000 in GitHub Codespaces).
"""
import os
from flask import Flask, render_template_string, request

from pii_redactor import (
    RedactorError,
    SUPPORTED_ENTITIES,
    parse_entities,
    redact_lines,
    redact_text,
    summarize,
)

app = Flask(__name__)

DEFAULT_ENTITIES = ", ".join(SUPPORTED_ENTITIES)

EXAMPLE_MIXED = (
    "Vendor Partita IVA: 01333550323, 12345670017 and IT12345671007 (Invoice ID: 12345670017).\n"
    "Fiscal code: RSSMRA85T10A562S | Driver's license: AB1234567C.\n"
    "Italian identity card number is CA 1234567 | Passaporto: AB1234567."
)

EXAMPLE_VAT_BOUNDARY = (
    "VAT number is 01333550323; partita iva equals 12345670017.\n"
    "VAT number: 01333550323, Invoice ID: 12345670017.\n"
    "Supplier: IT01333550323, 12345670017 (unlabeled second code is ignored).\n"
    "Invalid checksum Partita IVA: 01333550324 and invalid office Partita IVA: 12345670009."
)

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Team 3 Italian PII Anonymizer</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      max-width: 860px;
      margin: 2em auto;
      padding: 0 1em;
      color: #1f2937;
      line-height: 1.5;
    }
    h1 { margin-bottom: 0.25em; }
    .subtitle { color: #4b5563; margin-top: 0; font-size: 0.95em; }
    .badges { margin: 0.75em 0 1.25em; }
    .badge {
      display: inline-block;
      background: #eef2ff;
      color: #3730a3;
      border: 1px solid #c7d2fe;
      border-radius: 4px;
      padding: 0.15em 0.5em;
      margin: 0.15em 0.25em 0.15em 0;
      font-family: monospace;
      font-size: 0.85em;
    }
    textarea, input[type=text] {
      width: 100%;
      box-sizing: border-box;
      padding: 0.6em;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-family: inherit;
      font-size: 0.95em;
    }
    textarea { font-family: monospace; }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5em;
      align-items: center;
      margin-top: 0.75em;
    }
    button {
      padding: 0.55em 1.1em;
      border-radius: 6px;
      border: 1px solid #2563eb;
      background: #2563eb;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }
    button.secondary {
      background: #f9fafb;
      color: #1f2937;
      border-color: #d1d5db;
      font-weight: 500;
    }
    .checkbox-label {
      font-size: 0.9em;
      color: #374151;
      margin-left: 0.5em;
    }
    pre {
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 1em;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .error {
      color: #991b1b;
      background: #fef2f2;
      border: 1px solid #fecaca;
      padding: 0.75em 1em;
      border-radius: 6px;
    }
    .summary {
      color: #065f46;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      padding: 0.6em 0.9em;
      border-radius: 6px;
      font-size: 0.92em;
    }
  </style>
</head>
<body>
  <h1>Team 3 — Italian PII Anonymizer</h1>
  <p class="subtitle">Detects and redacts Team 3 Italian PII entities using <code>anonymize_text()</code> from <code>pii_scan.py</code>.</p>
  <div class="badges">
    <strong>Supported entities:</strong>
    {% for ent in supported_list %}
      <span class="badge">{{ ent }}</span>
    {% endfor %}
  </div>

  <form method="post">
    <p>
      <label><strong>Entities to search for</strong> (comma or space separated; blank = all Team 3 entities)<br>
      <input type="text" name="entities" value="{{ entities }}"
             placeholder="{{ default_entities }}"></label>
    </p>
    <p>
      <label><strong>Text to anonymize</strong><br>
      <textarea name="text" rows="8" placeholder="Enter text containing Italian PII (e.g. Partita IVA: 01333550323)...">{{ text }}</textarea></label>
    </p>
    <p>
      <label class="checkbox-label">
        <input type="checkbox" name="batch_lines" value="1" {% if batch_lines %}checked{% endif %}>
        Batch mode: process each line as an independent standalone record
      </label>
    </p>
    <div class="controls">
      <button type="submit">Anonymize</button>
      <button type="submit" name="preset" value="mixed" class="secondary">Load Team 3 Mixed Example</button>
      <button type="submit" name="preset" value="vat" class="secondary">Load IT_VAT_CODE Boundary Example</button>
    </div>
  </form>

  {% if error %}
    <p class="error">{{ error }}</p>
  {% endif %}

  {% if result is not none %}
    <h2>Result</h2>
    <pre>{{ result }}</pre>
    <p class="summary"><strong>Detected entities ({{ active_entities }}):</strong> {{ found }}</p>
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    entities = request.form.get("entities", DEFAULT_ENTITIES)
    text = request.form.get("text", "")
    batch_lines = bool(request.form.get("batch_lines"))
    preset = request.form.get("preset")

    if preset == "mixed":
        entities = DEFAULT_ENTITIES
        text = EXAMPLE_MIXED
        batch_lines = False
    elif preset == "vat":
        entities = "IT_VAT_CODE"
        text = EXAMPLE_VAT_BOUNDARY
        batch_lines = False

    result = error = found = active_entities = None
    if request.method == "POST" and not preset:
        if not text.strip():
            error = "Please enter some text to anonymize."
        else:
            try:
                parsed = parse_entities(entities)
                active_entities = ", ".join(parsed)
                result = (
                    redact_lines(text, parsed)
                    if batch_lines
                    else redact_text(text, parsed)
                )
                counts = summarize(text, parsed, line_by_line=batch_lines)
                found = (
                    ", ".join(f"{name}: {count}" for name, count in counts.items())
                    or "No matching PII detected"
                )
            except RedactorError as exc:
                error = f"Error: {exc}"
            except Exception as exc:
                error = f"Error: {exc}"

    return render_template_string(
        PAGE,
        entities=entities,
        default_entities=DEFAULT_ENTITIES,
        supported_list=SUPPORTED_ENTITIES,
        text=text,
        batch_lines=batch_lines,
        result=result,
        error=error,
        found=found,
        active_entities=active_entities,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))