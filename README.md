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
installed.
