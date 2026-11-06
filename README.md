# comp410_fall_2026
Repo for COMP410 fall 2026 semester

## PII Anonymizer

A tool that finds Personally Identifiable Information (PII) in text and replaces it with a
placeholder showing what kind of data was removed. For example:

```
Input:  Email me at john.doe@example.com or call 919-555-1234.
Output: Email me at <EMAIL_ADDRESS> or call <PHONE_NUMBER>.
```

It comes in two forms:

- **`app.py`**, a command-line tool.
- **`gui.py`**, a desktop window that shows each step of the process.

Both are built on `pii_scan.py`, which uses [Microsoft Presidio](https://microsoft.github.io/presidio/)
and the spaCy `en_core_web_lg` language model to detect entities.

### Supported entities

| Entity          | Example                  |
|-----------------|--------------------------|
| `PHONE_NUMBER`  | `919-555-1234`           |
| `EMAIL_ADDRESS` | `john.doe@example.com`   |
| `CREDIT_CARD`   | `4111 1111 1111 1111`    |
| `US_SSN`        | `219-09-9999`            |
| `IP_ADDRESS`    | `192.168.1.10`           |

Detection is based on patterns and checksums, not just the format. Some numbers that look
right are rejected because they are known to be invalid. For example, `123-45-6789` is not
detected as an SSN.

### Setup

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

The first time you run either app, the spaCy `en_core_web_lg` model (about 400 MB) is
downloaded automatically. To download it ahead of time, run:

```bash
python -m spacy download en_core_web_lg
```

### Using the GUI

```bash
python gui.py
```

The window opens with sample text already loaded. The model takes a few seconds to load.
The status bar says **Ready** when it is done.

1. Type or paste text into the **Input** pane, or use **Open file…** or **Load sample**.
2. Check the entity types you want to redact.
3. Click **Anonymize ▶**.

The window then shows each step:

| Panel                | What it shows |
|----------------------|---------------|
| **1. Input**         | Your text, with each detected entity highlighted in its entity's color |
| **2. Detections**    | Every match: entity type, matched text, character span, confidence score, and the Presidio recognizer that found it |
| **3. Redacted output** | The text with every match replaced by `<ENTITY_TYPE>` |
| **4. Metrics**       | Number of entities found, input and output length, processing time |
| **Activity log**     | A timestamped record of each step (model loading, analysis, redaction) |

### Using the command line

```bash
# Redact a string
python app.py -t "Call me at 919-555-1234"

# Redact a file
python app.py -f notes.txt

# Redact from piped input
cat notes.txt | python app.py

# Redact only some entity types (names are not case-sensitive and can be comma-separated)
python app.py -e phone_number,email_address -t "..."

# Show metrics after the output (printed to stderr)
python app.py --stats -t "..."
```

If you run `python app.py` with no input, it asks you to type text. Finish with **Ctrl+Z**
then **Enter** on Windows, or **Ctrl+D** on macOS and Linux.

Unsupported entity names give a warning and are skipped. If none of the names you give are
supported, the app exits with an error.

### How it works

```
text ──► pii_scan.analyze_text()  ──► list of detections (type, span, score)
                                         │
                                         ▼
         pii_scan.anonymizer.anonymize() ──► text with <ENTITY_TYPE> placeholders
```

1. **Analyze:** Presidio's `AnalyzerEngine` runs pattern-based and NLP-based recognizers over
   the text. It only looks for the entity types you selected.
2. **Anonymize:** Presidio's `AnonymizerEngine` replaces each detected span with its entity
   type name.

### Running the tests

```bash
python -m unittest test_app -v
```

### Files

| File          | Purpose |
|---------------|---------|
| `app.py`      | Command-line interface and helper functions (`parse_entity_list`, `process_anonymization`) |
| `gui.py`      | Tkinter desktop interface |
| `pii_scan.py` | Presidio analyzer and anonymizer setup, including custom recognizers |
| `test_app.py` | Unit tests for `app.py` |
