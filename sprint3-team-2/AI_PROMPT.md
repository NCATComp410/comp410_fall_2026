# AI Prompt for PII Anonymizer Application - Team 2

## Overview

This document describes the AI prompt used to develop the PII Anonymizer application for Team 2. The application detects and anonymizes Personally Identifiable Information (PII) from text using Microsoft Presidio's `anonymize_text()` function.

---

## Initial Prompt (v1)

```
Create a Python application that can detect and anonymize personally identifiable information (PII) from text.

Requirements:
- Use the anonymize_text() function from pii_scan.py
- Accept an entity list as input
- Accept text to anonymize as input
- Return the original text with PII redacted

Team 2 entities to support:
- IN_AADHAAR: Indian Aadhaar number (12-digit format)
- IN_PAN: Indian Permanent Account Number (10-character format)
- IN_PASSPORT: Indian Passport number
- IN_VEHICLE_REGISTRATION: Indian Vehicle Registration number
- IN_VOTER: Indian Voter ID / EPIC number (3 letters + 7 digits)

Output should be the original text with any PII redacted.
```

---

## Refined Prompt (v2)

After initial testing revealed some edge cases, I refined the prompt to include more specific requirements:

```
Create a Python application that can detect and anonymize personally identifiable information (PII) from text using Microsoft Presidio.

The application must:
1. Accept an entity list as input (list of entity type strings like 'IN_VOTER', 'IN_AADHAAR', etc.)
2. Accept text to anonymize as input (string)
3. Invoke the anonymize_text() function from pii_scan.py
4. Return the original text with PII redacted

Team 2 is responsible for these entity types:
- IN_AADHAAR: Indian Aadhaar number (12-digit format, e.g., 123456789012)
- IN_PAN: Indian Permanent Account Number (10-character format like ABCDE1234F)
- IN_PASSPORT: Indian Passport number (e.g., MNO1234567)
- IN_VEHICLE_REGISTRATION: Indian Vehicle Registration number (e.g., KA01AB1234)
- IN_VOTER: Indian Voter ID / EPIC number (3 uppercase letters + 7 digits, e.g., ABC1234567)

The application should:
- Handle empty input gracefully without crashing
- Preserve non-PII text exactly as-is
- Detect multiple occurrences of the same entity type in a single text
- Handle mixed entity types in the same text
- Provide clear error messages for invalid inputs

Output format: A string containing the original text with PII replaced by <ENTITY_NAME> (e.g., <IN_VOTER>)
```

---

## Final Prompt (v3) - With Testing Requirements

After testing revealed the need for comprehensive test coverage, I added requirements for a test suite:

```
Create a Python application that can detect and anonymize personally identifiable information (PII) from text using Microsoft Presidio.

The application must:
1. Accept an entity list as input (list of entity type strings like 'IN_VOTER', 'IN_AADHAAR', etc.)
2. Accept text to anonymize as input (string)
3. Invoke the anonymize_text() function from pii_scan.py
4. Return the original text with PII redacted

Team 2 is responsible for these entity types:
- IN_AADHAAR: Indian Aadhaar number (12-digit format, e.g., 123456789012)
- IN_PAN: Indian Permanent Account Number (10-character format like ABCDE1234F)
- IN_PASSPORT: Indian Passport number (e.g., MNO1234567)
- IN_VEHICLE_REGISTRATION: Indian Vehicle Registration number (e.g., KA01AB1234)
- IN_VOTER: Indian Voter ID / EPIC number (3 uppercase letters + 7 digits, e.g., ABC1234567)

The application should:
- Handle empty input gracefully without crashing
- Preserve non-PII text exactly as-is
- Detect multiple occurrences of the same entity type in a single text
- Handle mixed entity types in the same text
- Provide clear error messages for invalid inputs

Output format: A string containing the original text with PII replaced by <ENTITY_NAME> (e.g., <IN_VOTER>)

Additionally, create a comprehensive test suite that covers:
1. Normal inputs with valid PII
2. Multiple occurrences of the same entity type
3. Mixed entity types in the same text
4. Text containing no PII
5. Empty input handling
6. Boundary conditions for each entity format (valid vs invalid)
7. Invalid/invalid-like inputs that should NOT be detected as false positives
8. Contextual detection (text with context improves confidence)
9. Preservation of non-PII text including special characters and unicode

Test the application and fix any bugs found during testing.
```

---

## Prompt Refinement Notes

### v1 → v2 Improvements:
- Added specific format examples for each entity type to improve AI understanding
- Clarified that the application should handle empty input gracefully
- Specified output format with `<ENTITY_NAME>` placeholder

### v2 → v3 Improvements:
- Added explicit testing requirements for comprehensive test coverage
- Requested boundary condition testing (valid vs invalid formats)
- Asked for false positive prevention testing
- Included unicode and special character handling in test requirements

---

## Implementation Notes

The application uses the existing `pii_scan.py` module which already has:
- `analyzer`: AnalyzerEngine configured with all recognizers including Team 2 entities
- `anonymizer`: AnonymizerEngine for redacting detected PII
- `anonymize_text()`: Main function that takes text and entity_list, returns anonymized text

The implementation is straightforward because the core logic already exists in pii_scan.py. The application primarily:
1. Defines the Team 2 entity list
2. Calls `anonymize_text()` with user input
3. Returns/displayed the result

---

## Testing Results

All tests passed successfully, including:
- Empty and whitespace-only inputs
- No PII in text
- Multiple occurrences of same entity type
- Mixed entity types
- Boundary conditions for all 5 entity types
- Invalid/invalid-like inputs correctly NOT detected
- Contextual detection working as expected
- Non-PII text preserved exactly

---

## Files Created

1. `pii_anonymizer.py` - Main application file
2. `test_pii_anonymizer.py` - Comprehensive test suite
