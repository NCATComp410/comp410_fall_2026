# comp410_fall_2026
Repo for COMP410 fall 2026 semester

## PII web app

The PII Text Anonymizer is a Flask app that redacts selected entity types in
text or uploaded files. Use Python 3.10 or newer.

### Install

Open a terminal in the repository root. In a Codespace, Python is already
available. For a local machine, create and activate a virtual environment first
if desired.

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

The spaCy model is required by the PII recognizers. The scanner attempts to
download it automatically the first time it is needed, but installing it here
avoids waiting for that download when you first submit text.

### Run

Start the app from the repository root:

```bash
python pii_web_app.py
```

The app listens on port 5000. In Codespaces, open the **Ports** tab and open or
forward port 5000. Locally, visit <http://127.0.0.1:5000>. To use a different
port, set the `PORT` environment variable before starting the app.

### Use

1. Select one or more entity types: `CREDIT_CARD`, `CRYPTO`, `DATE_TIME`,
	`EMAIL_ADDRESS`, or `MEDICAL_LICENSE`.
2. Paste text into the input box or upload a `.txt`, `.doc`, `.docx`, `.csv`, or
	`.md` file. Uploads are limited to 10 MB. Text files must be UTF-8 encoded.
3. Select **Anonymize**. Matches for the selected entity types appear in the
	output box as `<ENTITY_TYPE>` (for example, `<EMAIL_ADDRESS>`).
4. Select **Clear input** to clear the typed text, selected file, and output.

If no entity types are selected, the text is returned without entity
redactions. The app does not save submitted text or uploaded files.

### Legacy Word files

Reading `.doc` files requires the `antiword` system utility. On Debian/Ubuntu
and Codespaces, install it with:

```bash
sudo apt-get update
sudo apt-get install antiword
```

`.docx` files do not require `antiword`; they are read using the `python-docx`
dependency installed by `requirements.txt`.
