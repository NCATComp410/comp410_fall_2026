# comp410_fall_2026
Repo for COMP410 fall 2026 semester

## PII anonymizer web app

Install the project dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python app.py
```

In Codespaces, open port `8000` when prompted (or use the **Ports** tab). The
page accepts entity names separated by commas or newlines, along with text to
anonymize. Matches are replaced with `<ENTITY_TYPE>`. On first startup,
`pii_scan.py` may download the spaCy `en_core_web_lg` model if it is not already
installed. You can also upload a `.txt`, `.csv`, `.log`, or `.md` file instead of pasting
text. After redacting, click **Download** to save the result as `redacted.txt`.

## Running the tests

```bash
python -m unittest test_web_app test_file_upload test_team_1_anonymization -v
```
