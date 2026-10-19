# comp410_fall_2026
Repo for COMP410 fall 2026 semester

## Run the web app

From the repository root, install the Python dependencies and start the Flask app:

```bash
python -m pip install -r requirements.txt
python pii_web_app.py
```

The app runs on port `5000`. Open `http://localhost:5000` in your browser, or open
port `5000` from the Codespaces Ports tab. On first run, the app may download the
spaCy `en_core_web_lg` model.
