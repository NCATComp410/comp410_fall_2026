# comp410_fall_2026
Repo for COMP410 fall 2026 semester

## Team CodeClan - Sprint 3 PII Redactor

Branch: `sprint3-team-codeclan`. The app accepts an entity list and some text,
calls `anonymize_text()` from `pii_scan.py`, and returns the text with every
detected value replaced by `<ENTITY_TYPE>`. All other text is left unchanged.

Team CodeClan supports these entity types: `ABA_ROUTING_NUMBER`, `AU_ABN`,
`AU_ACN`, `AU_MEDICARE`, `AU_TFN`. If the entity list is blank, the app uses
these five. Pass `ALL` to scan for every entity that `pii_scan` supports.

| File | Purpose |
|------|---------|
| `codeclan_redactor.py` | Core logic: input validation, entity parsing, calls `anonymize_text()`, counts redactions |
| `codeclan_cli.py` | Command-line app (single text, files, batch, stdin) |
| `codeclan_web_app.py` | Flask web app and JSON API |
| `test_codeclan_sprint3.py` | Automated tests (normal, boundary, invalid and unusual input) |
| `team_codeclan_prompt.txt` | The AI prompt used to build the app, including our refinements |

### Setup

```bash
python -m pip install -r requirements.txt
```

The first run may download the spaCy `en_core_web_lg` model (about 400 MB).

### Web app

```bash
python codeclan_web_app.py
```

Open `http://localhost:5000` (in Codespaces, open port 5000 from the Ports tab).
Tick the entities to redact, paste text or upload a `.txt` file, and click
**Anonymize**. The result highlights each redaction and shows a count for each
entity type. **Load sample text** fills in an example, and **Download redacted .txt**
saves the output to a file.

JSON API:

```bash
curl -X POST localhost:5000/api/redact -H "Content-Type: application/json" \
     -d '{"text": "My TFN is 876 543 210", "entities": ["AU_TFN"]}'
```

### Command line

```bash
python codeclan_cli.py -e AU_TFN,AU_ABN "My TFN is 876 543 210 and ABN 51 824 753 556"
python codeclan_cli.py -f input.txt -o output.txt --summary
python codeclan_cli.py -f a.txt b.txt --out-dir redacted/
echo "Routing 021000021" | python codeclan_cli.py
python codeclan_cli.py --list-entities
```

Exit codes: `0` success, `1` invalid input (unknown entity, missing file, text too long),
`2` bad command-line usage.

### Tests

```bash
python -m pytest test_codeclan_sprint3.py -v
```

### Known limitations

These come from Presidio's recognizers (`pii_scan.py` is unchanged), and the tests pin them down:
- A TFN written with dashes (`876-543-210`) is not detected.
- A number with no space before it (`TFN876543210`) is not detected.
- For a Medicare number with an IRN suffix (`2123 45670 1/2`), the `/2` stays in the output.

### Team roles

| Role | Member(s) | Owns |
|------|-----------|------|
| Lead developer and integrator | Sapri Sise | Core module, web app, CLI, shared edge-case tests, AU_MEDICARE, final merge |
| ABA_ROUTING_NUMBER tester / web app QA | Kamryn & Caleb | ABA tests, web app review |
| AU_ACN tester / CLI QA | Jasmine & Ryan | ACN tests, CLI and batch review |
| AU_TFN tester / prompt engineer | Kailyn & Marcus | TFN tests, `team_codeclan_prompt.txt` refinement and bug log |
| AU_ABN tester / documentation | Jarren | ABN tests, README |

### Who did what

**Sapri Sise (lead developer)**
- Created the `sprint3-team-codeclan` branch
- Wrote `codeclan_redactor.py`, `codeclan_web_app.py` and `codeclan_cli.py` with AI help
- Wrote `test_codeclan_sprint3.py` (48 tests), found and fixed the 6 bugs logged in the prompt file
- Wrote `team_codeclan_prompt.txt` and the README instructions; did the final merge and push
- Sprint 2: AU_MEDICARE unit tests

**Kamryn & Caleb (ABA_ROUTING_NUMBER)**
- Sprint 2: ABA_ROUTING_NUMBER unit tests
- Sprint 3: review ABA test cases; QA the web app

**Jasmine & Ryan (AU_ACN)**
- Sprint 2: AU_ACN unit tests
- Sprint 3: review ACN test cases; QA the CLI and batch mode

**Kailyn & Marcus (AU_TFN)**
- Sprint 2: AU_TFN unit tests
- Sprint 3: review TFN test cases; review the prompt and its refinement log

**Jarren (AU_ABN)**
- Sprint 2: AU_ABN unit tests
- Sprint 3: review ABN test cases; review the README

Sprint 2 credits come from the comments and commits in `test_team_codeclan.py`.
