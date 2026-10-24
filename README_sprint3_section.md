## Sprint 3: Team Z PII Redactor

Redacts PII for Team Z's entities: `PHONE_NUMBER`, `LOCATION`, `PERSON`, `UK_NHS`, `UK_NINO`.
It calls `anonymize_text()` from `pii_scan.py` and swaps each PII span for a tag like `<PERSON>`.

### Setup
```
pip install -r requirements.txt
```
The first run downloads the spaCy model (`en_core_web_lg`), so give it a minute.

### Run it
```
# redact some text (all five entities by default)
python pii_redactor.py --text "Maria Garcia called 336-555-0123 from London."

# pick entities and show counts
python pii_redactor.py -t "John called 336-555-0123" -e PHONE_NUMBER --summary

# redact a whole file line by line
python pii_redactor.py --input notes.txt --output notes_redacted.txt
```

### Run the tests
```
python -m unittest test_sprint3_team_z -v
```

### Notes
- Empty or missing entity list means all five Team Z entities.
- Unsupported entities and bad input give a clear error message instead of crashing.
- The AI prompt we used is in `sprint3_prompt_team_z.txt`.