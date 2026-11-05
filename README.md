# Team 3 - Sprint 3: Italian PII Redactor
## Project Description

This application detects and anonymizes personally identifiable information (PII) in text using Microsoft Presidio.

Users can enter text, select which PII entity types to detect, and receive a redacted version of the original text. The application also provides a command-line interface and supports file processing.

## Supported PII Entities

Team 3 supports the following Italian PII entity types:

* IT_DRIVER_LICENSE – Italian driver’s license
* IT_FISCAL_CODE – Italian fiscal code
* IT_IDENTITY_CARD – Italian identity card
* IT_PASSPORT – Italian passport
* IT_VAT_CODE – Italian VAT code

## Requirements

* Python 3
* Dependencies listed in requirements.txt

## Installation

Clone the repository:

`git clone https://github.com/NCATComp410/comp410_fall_2026.git
cd comp410_fall_2026`

Install the required dependencies:

`python3 -m pip install -r requirements.txt`

## Running the Web Application

Start the Flask application:

`python3 pii_web_app.py`

If port 5000 is already in use, run:

`PORT=5001 python3 pii_web_app.py`

Open the application in your browser at http://127.0.0.1:5000 or http://127.0.0.1:5001, depending on the port used.

Enter text, select the desired entity types, and submit it to view the anonymized result.

## Command-Line Usage

Redact text directly:

`python3 pii_redactor.py -t "Patente di guida: U1B234567C"`

Select specific entity tyes:

`python3 pii_redactor.py -t "Example text" -e IT_PASSPORT,IT_FISCAL_CODE`

Redact a file and save the output:

`python3 pii_redactor.py -i input.txt -o output.txt`

Additional options include batch-line processing and detection summaries.

## Running Tests

Run the Team 3 test suite:

`python3 -m unittest -v test_sprint3_team_3.py`

The tests cover entity detection, anonymization, invalid inputs, boundary cases, multiple PII entities, file processing, command-line functionality, and web application routes.

# AI Development

The AI development prompt used for this project is documented in team_3_prompt.txt.
