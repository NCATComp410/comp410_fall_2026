"""PII Redactor for Team Z (Sprint 3).

Wraps anonymize_text() from pii_scan.py with input validation, friendly
errors, and a few extras (summary counts, file and batch processing).
Run `python pii_redactor.py --help` for the command line options.
"""
import argparse
import sys

from pii_scan import analyze_text, anonymize_text

# Team Z entities from Sprint 1 and Sprint 2
SUPPORTED_ENTITIES = ["PHONE_NUMBER", "LOCATION", "PERSON", "UK_NHS", "UK_NINO"]


class RedactorError(ValueError):
    """Raised when the text or entity list is not usable."""


def parse_entities(entities=None):
    """Turn user input into a clean list of supported entity names.

    Accepts None, a comma separated string, or a list. None or empty means
    all Team Z entities. (Without this guard an empty list would make
    Presidio look for every entity type, not just ours.)
    """
    if entities is None:
        return list(SUPPORTED_ENTITIES)
    if isinstance(entities, str):
        entities = entities.split(",")
    if not isinstance(entities, (list, tuple, set)):
        raise RedactorError("Entities must be a list or a comma separated string.")
    cleaned = []
    for item in entities:
        if not isinstance(item, str):
            raise RedactorError(f"Entity names must be text, got {item!r}.")
        name = item.strip().upper()
        if name and name not in cleaned:
            cleaned.append(name)
    if not cleaned:
        return list(SUPPORTED_ENTITIES)
    unsupported = [name for name in cleaned if name not in SUPPORTED_ENTITIES]
    if unsupported:
        raise RedactorError(
            f"Unsupported entity: {', '.join(unsupported)}. "
            f"Supported: {', '.join(SUPPORTED_ENTITIES)}.")
    return cleaned


def redact_text(text, entities=None):
    """Return text with the chosen PII replaced by tags like <PERSON>."""
    if not isinstance(text, str):
        raise RedactorError("Text must be a string.")
    entity_list = parse_entities(entities)
    if not text.strip():
        return text  # nothing to scan, keep the original
    return anonymize_text(text, entity_list)


def summarize(text, entities=None):
    """Count how many of each entity type were found in the text."""
    if not isinstance(text, str):
        raise RedactorError("Text must be a string.")
    entity_list = parse_entities(entities)
    counts = {}
    if text.strip():
        for result in analyze_text(text, entity_list):
            counts[result.entity_type] = counts.get(result.entity_type, 0) + 1
    return counts


def redact_lines(text, entities=None):
    """Batch mode: redact each line on its own, keeping blank lines."""
    return "\n".join(redact_text(line, entities) for line in text.split("\n"))


def redact_file(in_path, out_path, entities=None):
    """Read a text file, redact it line by line, write the result."""
    try:
        with open(in_path, encoding="utf-8") as handle:
            content = handle.read()
    except FileNotFoundError as exc:
        raise RedactorError(f"File not found: {in_path}") from exc
    except UnicodeDecodeError as exc:
        raise RedactorError(f"{in_path} is not a UTF-8 text file.") from exc
    redacted = redact_lines(content, entities)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(redacted)
    return redacted


def main(argv=None):
    parser = argparse.ArgumentParser(description="Redact Team Z PII from text.")
    parser.add_argument("-e", "--entities", default=None,
                        help="comma separated list, default all: "
                             + ",".join(SUPPORTED_ENTITIES))
    parser.add_argument("-t", "--text", help="text to redact")
    parser.add_argument("-i", "--input", help="input text file")
    parser.add_argument("-o", "--output", help="output file (with --input)")
    parser.add_argument("-s", "--summary", action="store_true",
                        help="also print how many of each entity were found")
    args = parser.parse_args(argv)
    try:
        if args.input:
            out = args.output or args.input + ".redacted"
            redact_file(args.input, out, args.entities)
            print(f"Wrote redacted file to {out}")
        elif args.text is not None:
            print(redact_text(args.text, args.entities))
            if args.summary:
                print("Found:", summarize(args.text, args.entities) or "nothing")
        else:
            parser.error("give --text or --input")
    except RedactorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())