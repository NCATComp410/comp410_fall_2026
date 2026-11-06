"""
PII Anonymizer Application for Team 2
=====================================

This application detects and anonymizes Personally Identifiable Information (PII)
from text using Microsoft Presidio. Team 2 is responsible for the following entity types:
- IN_AADHAAR: Indian Aadhaar number (12-digit format)
- IN_PAN: Indian Permanent Account Number (10-character format)
- IN_PASSPORT: Indian Passport number
- IN_VEHICLE_REGISTRATION: Indian Vehicle Registration number
- IN_VOTER: Indian Voter ID / EPIC number (3 letters + 7 digits)

The application accepts an entity list and text input, invokes anonymize_text() from pii_scan.py,
and returns the original text with any PII redacted.

Author: Team 2 - Noire Meyers, Dakarai Lanes, Michael Nearn, Jarred Mattison, Nolan Maske
"""

from pii_scan import anonymize_text


def main():
    """
    Main function to run the PII Anonymizer application.

    This function prompts the user for input and processes the text to remove PII.
    """
    print("=" * 60)
    print("PII Anonymizer - Team 2")
    print("=" * 60)
    print()

    # Define the entity list for Team 2
    ENTITY_LIST = [
        'IN_AADHAAR',
        'IN_PAN',
        'IN_PASSPORT',
        'IN_VEHICLE_REGISTRATION',
        'IN_VOTER'
    ]

    print(f"Entities to detect and anonymize: {ENTITY_LIST}")
    print()

    # Get text input from user
    try:
        text = input("Enter the text to anonymize (or type 'quit' to exit): ")

        if text.lower() == 'quit':
            print("Exiting application.")
            return

        if not text or not text.strip():
            print("Error: Empty input. Please enter some text.")
            return

    except EOFError:
        print("\nInput stream ended.")
        return
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return

    # Anonymize the text
    try:
        anonymized_text = anonymize_text(text, ENTITY_LIST)

        # Display results
        print()
        print("=" * 60)
        print("ANONYMIZATION RESULTS")
        print("=" * 60)
        print(f"Original Text:\n{text}")
        print()
        print(f"Anonymized Text:\n{anonymized_text}")
        print("=" * 60)

    except Exception as e:
        print(f"Error during anonymization: {e}")


if __name__ == '__main__':
    main()
