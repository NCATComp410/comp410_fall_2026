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

## Test Results (Sprint-3, Operation Eclipse)

Our application redacts PII by calling `anonymize_text()` from `pii_scan.py`. The examples
below are real output from that function for our assigned entities: `CREDIT_CARD`,
`CRYPTO`, `DATE_TIME`, `EMAIL_ADDRESS` and `MEDICAL_LICENSE`. Each piece of PII is
replaced with its entity type, and all other text is left unchanged.

### Automated test summary

```bash
python -m pytest test_sprint3_operation_eclipse.py test_team_operation_eclipse.py -v
```

| Test file | What it covers | Result |
| --- | --- | --- |
| `test_sprint3_operation_eclipse.py` | Sprint-3: normal inputs and multiple PII occurrences | 12 passed |
| `test_team_operation_eclipse.py` | Sprint-1/2: detection of each entity (positive and negative cases) | 6 passed |
| **Total** | | **18 passed, 0 failed** |

### Normal inputs (one entity at a time)

| Entity | Original text | Anonymized output |
| --- | --- | --- |
| CREDIT_CARD | `My card number is 4111 1111 1111 1111.` | `My card number is <CREDIT_CARD>.` |
| CRYPTO (Bitcoin) | `Send the refund to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa please.` | `Send the refund to <CRYPTO> please.` |
| CRYPTO (Ethereum) | `My ETH wallet is 0x52908400098527886E0F7030069857D2E4169EE7` | `My ETH wallet is <CRYPTO>` |
| DATE_TIME | `The appointment is on October 15, 2026 at 3:30 PM.` | `The appointment is on <DATE_TIME> at <DATE_TIME>.` |
| EMAIL_ADDRESS | `Email me at jordan_lee@dept.ncat.edu with questions.` | `Email me at <EMAIL_ADDRESS> with questions.` |
| MEDICAL_LICENSE | `Medical license number: AB1000001` | `Medical license number: <MEDICAL_LICENSE>` |

### Multiple occurrences and mixed entity types

| Case | Entities requested | Original text | Anonymized output |
| --- | --- | --- | --- |
| Three emails | EMAIL_ADDRESS | `CC a@b.com, c@d.org and e@f.net` | `CC <EMAIL_ADDRESS>, <EMAIL_ADDRESS> and <EMAIL_ADDRESS>` |
| Three cards (Visa, Mastercard, Amex) | CREDIT_CARD | `Cards on file: 4111111111111111, 5555555555554444 and 378282246310005.` | `Cards on file: <CREDIT_CARD>, <CREDIT_CARD> and <CREDIT_CARD>.` |
| All five types in one sentence | all five | `On 05/24/2003 Dr. Lee (license AB1000001) emailed jordan_lee@dept.ncat.edu about card 4111111111111111 and wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.` | `On <DATE_TIME> Dr. Lee (license <MEDICAL_LICENSE>) emailed <EMAIL_ADDRESS> about card <CREDIT_CARD> and wallet <CRYPTO>.` |
| Only the selected type is redacted | EMAIL_ADDRESS | `Email jordan_lee@dept.ncat.edu, card 4111111111111111` | `Email <EMAIL_ADDRESS>, card 4111111111111111` |

### No PII, empty input, and values that should not be redacted

| Case | Original text | Anonymized output |
| --- | --- | --- |
| No PII | `The quick brown fox jumps over the lazy dog.` | `The quick brown fox jumps over the lazy dog.` (unchanged) |
| Empty input | *(empty string)* | *(empty string)* |
| Invalid card number (fails the Luhn check) | `Card 4111111111111112` | `Card 4111111111111112` (unchanged) |
| Malformed email (no domain ending) | `Contact me at user@example` | `Contact me at user@example` (unchanged) |
| Invalid medical license (bad DEA checksum) | `Medical license number: AB1234567` | `Medical license number: AB1234567` (unchanged) |
| Wallet address too short | `Wallet 1BoatSLRHtKNngkdXEeobR` | `Wallet 1BoatSLRHtKNngkdXEeobR` (unchanged) |

### Issues found during testing

| Case | Original text | Anonymized output | Notes |
| --- | --- | --- | --- |
| Two dates close together | `Start 05/24/2003, end 06/01/2004.` | `Start <DATE_TIME>.` | spaCy reads this as one date range, so both dates and the word "end" become a single tag. No date leaks. |
| Two cards separated only by a space | `4111111111111111 4111111111111111` | `<CREDIT_CARD>` | Presidio's anonymizer merges same-type PII separated only by whitespace. With a comma between them, each card gets its own tag. No PII leaks. |
| Misspelled entity name | `a@b.com` with entity `EMAIL_ADRESS` | Error: `No matching recognizers were found to serve the request.` | Calling `anonymize_text()` directly with an unknown entity name raises an error, so the application needs to check entity names before calling it. |


