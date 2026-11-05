"""
COMP410 Sprint 3 - PII Anonymizer Application
Wraps pii_scan.anonymize_text() to detect and redact sensitive entities.
"""

import argparse
import sys
from typing import List, Tuple
from pii_scan import anonymize_text

# Define entities supported by your team from Sprint 1 & Sprint 2
SUPPORTED_ENTITIES = {
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "US_SSN",
    "IP_ADDRESS",
}


def parse_entity_list(raw_entities: List[str]) -> List[str]:
    """Validates and normalizes the target entity list."""
    if not raw_entities:
        return list(SUPPORTED_ENTITIES)

    # Allow comma-separated strings (e.g., "EMAIL,PHONE") or multi-arg lists
    normalized = set()
    for item in raw_entities:
        for ent in item.split(","):
            cleaned = ent.strip().upper()
            if cleaned:
                normalized.add(cleaned)

    # Check for unsupported entities
    unsupported = normalized - SUPPORTED_ENTITIES
    if unsupported:
        sys.stderr.write(
            f"Warning: The following entities are not supported: {', '.join(unsupported)}\n"
        )

    active_entities = list(normalized.intersection(SUPPORTED_ENTITIES))
    return active_entities


def process_anonymization(text: str, entities: List[str]) -> Tuple[str, dict]:
    """
    Invokes pii_scan.anonymize_text() and compiles basic metadata metrics.
    """
    if not text:
        return "", {"original_length": 0, "redacted_length": 0}

    redacted_text = anonymize_text(text, entities=entities)

    stats = {
        "original_length": len(text),
        "redacted_length": len(redacted_text),
        "entities_targeted": entities,
    }
    return redacted_text, stats


def main():
    parser = argparse.ArgumentParser(
        description="Detect and redact Personally Identifiable Information (PII) from text."
    )
    parser.add_argument(
        "-t", "--text",
        type=str,
        help="Direct raw text string to redact."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to a text file containing content to redact."
    )
    parser.add_argument(
        "-e", "--entities",
        nargs="+",
        default=[],
        help=f"List of PII entities to target. Supported: {', '.join(sorted(SUPPORTED_ENTITIES))}",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display redaction statistics to stderr after output.",
    )

    args = parser.parse_args()

    # 1. Gather Input
    raw_text = ""
    if args.text is not None:
        raw_text = args.text
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as file_in:
                raw_text = file_in.read()
        except FileNotFoundError:
            sys.stderr.write(f"Error: File '{args.file}' not found.\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error reading file '{args.file}': {e}\n")
            sys.exit(1)
    elif not sys.stdin.isatty():
        # Read from pipeline or redirect
        raw_text = sys.stdin.read()
    else:
        # Interactive fallback
        print("Enter text to anonymize (Press Ctrl+D or Ctrl+Z on Windows when finished):")
        raw_text = sys.stdin.read()

    # 2. Parse and Validate Entities
    target_entities = parse_entity_list(args.entities)
    if not target_entities:
        sys.stderr.write("Error: No valid target entities specified.\n")
        sys.exit(1)

    # 3. Anonymize
    redacted, metrics = process_anonymization(raw_text, target_entities)

    # 4. Output
    print(redacted)

    if args.stats:
        sys.stderr.write("\n--- Redaction Metrics ---\n")
        sys.stderr.write(f"Active Entities: {', '.join(metrics['entities_targeted'])}\n")
        sys.stderr.write(f"Input Length:    {metrics['original_length']} chars\n")
        sys.stderr.write(f"Output Length:   {metrics['redacted_length']} chars\n")


if __name__ == "__main__":
    main()
