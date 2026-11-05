"""Flask interface for testing PII anonymization."""
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, render_template_string, request


ENTITY_TYPES = (
		"CREDIT_CARD",
		"CRYPTO",
		"DATE_TIME",
		"EMAIL_ADDRESS",
		"MEDICAL_LICENSE",
)
ALLOWED_EXTENSIONS = {".txt", ".doc", ".docx", ".csv", ".md"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

PAGE = """
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>PII Text Anonymizer</title>
	<style>
		:root {
			color-scheme: light;
			--ink: #202b2b;
			--muted: #62706d;
			--paper: #fffefa;
			--canvas: #edf3ee;
			--line: #cbd6ce;
			--green: #176b52;
			--green-dark: #10513f;
			--coral: #c65e49;
		}
		* { box-sizing: border-box; }
		body {
			margin: 0;
			min-height: 100vh;
			background: radial-gradient(ellipse at 92% 8%, #d4e5d7 0, transparent 34%), var(--canvas);
			color: var(--ink);
			font: 16px/1.5 Georgia, "Times New Roman", serif;
		}
		main { width: min(100% - 40px, 960px); margin: 48px auto; }
		header { margin-bottom: 30px; border-bottom: 1px solid var(--line); padding-bottom: 20px; }
		.eyebrow { color: var(--green); font: 700 12px/1.3 sans-serif; text-transform: uppercase; }
		h1 { margin: 7px 0 0; font-size: clamp(30px, 5vw, 46px); line-height: 1.08; }
		.workspace { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
		.field { min-width: 0; }
		label, legend { display: block; margin-bottom: 8px; font: 700 14px/1.4 sans-serif; }
		fieldset { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 0 0 20px; padding: 0; border: 0; }
		fieldset label { display: flex; gap: 7px; align-items: center; margin: 0; font-weight: 400; }
		input[type="checkbox"] { accent-color: var(--green); width: 16px; height: 16px; }
		textarea {
			display: block; width: 100%; min-height: 300px; resize: vertical; padding: 14px;
			border: 1px solid var(--line); border-radius: 4px; background: var(--paper);
			color: var(--ink); font: 14px/1.55 ui-monospace, SFMono-Regular, Consolas, monospace;
		}
		textarea:focus, input:focus-visible, button:focus-visible { outline: 3px solid #79ad95; outline-offset: 2px; }
		input[type="file"] { max-width: 100%; margin: 0 0 12px; font: 14px sans-serif; }
		.hint { margin: -4px 0 9px; color: var(--muted); font: 13px/1.4 sans-serif; }
		.actions { display: flex; gap: 10px; margin-top: 12px; }
		button { min-height: 42px; padding: 9px 16px; border: 1px solid var(--green); border-radius: 3px; cursor: pointer; font: 700 14px sans-serif; }
		.primary { background: var(--green); color: white; }
		.primary:hover { background: var(--green-dark); }
		.secondary { background: transparent; color: var(--ink); border-color: var(--line); }
		.secondary:hover { background: #e3ebe4; }
		.error { margin: 0 0 16px; padding: 10px 12px; border-left: 3px solid var(--coral); background: #fff0eb; color: #773a2d; font: 14px/1.45 sans-serif; }
		@media (max-width: 680px) {
			main { width: min(100% - 28px, 520px); margin: 28px auto; }
			.workspace { grid-template-columns: 1fr; gap: 24px; }
			textarea { min-height: 220px; }
		}
	</style>
</head>
<body>
	<main>
		<header>
			<div class="eyebrow">Text processing</div>
			<h1>PII Text Anonymizer</h1>
		</header>
		{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
		<form method="post" enctype="multipart/form-data">
			<fieldset>
				<legend>Entities to redact</legend>
				{% for entity in entity_types %}
				<label><input type="checkbox" name="entity_types" value="{{ entity }}" {% if entity in selected %}checked{% endif %}>{{ entity }}</label>
				{% endfor %}
			</fieldset>
			<div class="workspace">
				<section class="field">
					<label for="input-text">Text to anonymize</label>
					<input type="file" name="input_file" id="input-file" accept=".txt,.doc,.docx,.csv,.md">
					<p class="hint">Optional file: TXT, DOC, DOCX, CSV, or Markdown (10 MB max)</p>
					<textarea id="input-text" name="input_text" placeholder="Paste text here, or choose a file above...">{{ input_text }}</textarea>
					<div class="actions">
						<button type="submit" class="primary">Anonymize</button>
						<button type="button" class="secondary" id="clear-input">Clear input</button>
					</div>
				</section>
				<section class="field">
					<label for="output-text">Redacted text</label>
					<textarea id="output-text" readonly placeholder="Your anonymized text will appear here...">{{ output_text }}</textarea>
				</section>
			</div>
		</form>
	</main>
	<script>
		document.getElementById('clear-input').addEventListener('click', () => {
			document.getElementById('input-text').value = '';
			document.getElementById('input-file').value = '';
			document.getElementById('output-text').value = '';
		});
	</script>
</body>
</html>
"""


def _read_uploaded_file(upload):
		"""Extract text from one supported upload."""
		suffix = Path(upload.filename or "").suffix.lower()
		if suffix not in ALLOWED_EXTENSIONS:
				raise ValueError("Choose a .txt, .doc, .docx, .csv, or .md file.")

		content = upload.read(MAX_UPLOAD_BYTES + 1)
		if len(content) > MAX_UPLOAD_BYTES:
				raise ValueError("Files must be 10 MB or smaller.")

		if suffix == ".docx":
				from docx import Document

				document = Document(io.BytesIO(content))
				parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
				for table in document.tables:
						parts.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
				return "\n".join(parts)

		if suffix == ".doc":
				antiword = shutil.which("antiword")
				if not antiword:
						raise ValueError("Legacy .doc files need antiword. Install it with: sudo apt-get install antiword")
				with tempfile.TemporaryDirectory() as temp_dir:
						path = Path(temp_dir) / "upload.doc"
						path.write_bytes(content)
						try:
								result = subprocess.run(
										[antiword, str(path)], check=True, capture_output=True, timeout=30
								)
						except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
								raise ValueError("Could not read this .doc file.") from exc
				return result.stdout.decode("utf-8", errors="replace")

		try:
				return content.decode("utf-8-sig")
		except UnicodeDecodeError as exc:
				raise ValueError("Text uploads must use UTF-8 encoding.") from exc


@app.route("/", methods=["GET", "POST"])
def index():
		input_text = ""
		output_text = ""
		selected = []
		error = None

		if request.method == "POST":
				selected = [entity for entity in request.form.getlist("entity_types") if entity in ENTITY_TYPES]
				upload = request.files.get("input_file")
				try:
						input_text = _read_uploaded_file(upload) if upload and upload.filename else request.form.get("input_text", "")
						if not input_text.strip():
								raise ValueError("Enter text or choose a file to anonymize.")
						from pii_scan import anonymize_text

						output_text = anonymize_text(input_text, selected)
				except ValueError as exc:
						error = str(exc)
				except Exception:
						app.logger.exception("Text anonymization failed")
						error = "Anonymization failed. Check the server logs for details."

		return render_template_string(
				PAGE,
				entity_types=ENTITY_TYPES,
				selected=selected,
				input_text=input_text,
				output_text=output_text,
				error=error,
		)


@app.errorhandler(413)
def request_too_large(_error):
		return render_template_string(
				PAGE,
				entity_types=ENTITY_TYPES,
				selected=[],
				input_text="",
				output_text="",
				error="Request is too large. Text and uploaded files must be 10 MB or smaller.",
		), 413


if __name__ == "__main__":
		app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)

