"""PII Redactor for Team 3 (Sprint 3).

Wraps anonymize_text() and analyze_text() from pii_scan.py with input
validation, Team 3 entity filtering, overlap-resolved detection summaries,
and batch/file redaction utilities.

Supported Team 3 entities (Sprint 1 & Sprint 2):
- IT_DRIVER_LICENSE
- IT_FISCAL_CODE
- IT_IDENTITY_CARD
- IT_PASSPORT
- IT_VAT_CODE

Run `python pii_redactor.py --help` for command-line usage.
"""
import argparse
import re
import sys

from pii_scan import analyze_text, anonymize_text

# Team 3 entities assigned in Sprint 1 and Sprint 2
SUPPORTED_ENTITIES = [
    "IT_DRIVER_LICENSE",
    "IT_FISCAL_CODE",
    "IT_IDENTITY_CARD",
    "IT_PASSPORT",
    "IT_VAT_CODE",
]


class RedactorError(ValueError):
    """Raised when the text, entity list, or file input is invalid."""


def parse_entities(entities=None) -> list[str]:
    """Validate and normalize user-supplied entities into a list of Team 3 entity names.

    Accepts None, a comma/space-separated string, or an iterable of strings.
    When None or empty, defaults to all five Team 3 entities so Presidio does
    not scan for unrelated global entity types.
    """
    if entities is None:
        return list(SUPPORTED_ENTITIES)
    if isinstance(entities, str):
        tokens = [tok for tok in re.split(r"[\s,]+", entities.strip()) if tok]
    elif isinstance(entities, (list, tuple, set)):
        tokens = list(entities)
    else:
        raise RedactorError(
            "Entities must be a list of strings or a comma/space-separated string."
        )

    cleaned = []
    for item in tokens:
        if not isinstance(item, str):
            raise RedactorError(f"Entity names must be strings, got {type(item).__name__}.")
        for part in re.split(r"[\s,]+", item.strip()):
            if not part:
                continue
            name = part.upper()
            if name not in cleaned:
                cleaned.append(name)

    if not cleaned:
        return list(SUPPORTED_ENTITIES)

    unsupported = [name for name in cleaned if name not in SUPPORTED_ENTITIES]
    if unsupported:
        raise RedactorError(
            f"Unsupported entity type(s): {', '.join(unsupported)}. "
            f"Team 3 supports: {', '.join(SUPPORTED_ENTITIES)}."
        )
    return cleaned


def _resolve_overlaps(results):
    """Deduplicate overlapping analyzer spans using Presidio's priority rules.

    When two recognizers match overlapping character spans (for example,
    IT_PASSPORT with context boost vs. low-confidence IT_IDENTITY_CARD on a
    9-character code), keep the highest-scoring (and longest) span so summary
    counts match the actual tags produced by anonymize_text().
    """
    accepted = []
    ordered = sorted(
        results,
        key=lambda r: (-getattr(r, "score", 0.0), -(r.end - r.start), r.start),
    )
    for candidate in ordered:
        if not any(
            candidate.start < kept.end and kept.start < candidate.end
            for kept in accepted
        ):
            accepted.append(candidate)
    return sorted(accepted, key=lambda r: r.start)


def redact_text(text: str, entities=None) -> str:
    """Anonymize supported Team 3 PII entities in text using pii_scan.anonymize_text().

    Replaces each detected PII span with <ENTITY_TYPE> while preserving all
    non-PII text and multi-line context boundaries.
    """
    if not isinstance(text, str):
        raise RedactorError("Input text must be a string.")
    entity_list = parse_entities(entities)
    if not text.strip():
        return text
    return anonymize_text(text, entity_list)


def redact_lines(text: str, entities=None) -> str:
    """Batch mode: anonymize each line independently while preserving blank lines.

    Useful when each line represents a separate record (such as a list of
    standalone 11-digit IT_VAT_CODE values).
    """
    if not isinstance(text, str):
        raise RedactorError("Input text must be a string.")
    entity_list = parse_entities(entities)
    return "\n".join(redact_text(line, entity_list) for line in text.split("\n"))


def summarize(text: str, entities=None, line_by_line: bool = False) -> dict[str, int]:
    """Count how many instances of each Team 3 PII entity were detected in text."""
    if not isinstance(text, str):
        raise RedactorError("Input text must be a string.")
    entity_list = parse_entities(entities)
    counts: dict[str, int] = {}
    if not text.strip():
        return counts

    segments = text.split("\n") if line_by_line else [text]
    for segment in segments:
        if not segment.strip():
            continue
        resolved = _resolve_overlaps(analyze_text(segment, entity_list))
        for result in resolved:
            counts[result.entity_type] = counts.get(result.entity_type, 0) + 1
    return counts


def redact_file(
    in_path: str,
    out_path: str,
    entities=None,
    line_by_line: bool = False,
) -> str:
    """Read a UTF-8 text file, redact Team 3 PII entities, and write the output file."""
    if not isinstance(in_path, str) or not in_path.strip():
        raise RedactorError("Input file path must be a non-empty string.")
    if not isinstance(out_path, str) or not out_path.strip():
        raise RedactorError("Output file path must be a non-empty string.")

    entity_list = parse_entities(entities)
    try:
        with open(in_path, encoding="utf-8") as handle:
            content = handle.read()
    except FileNotFoundError as exc:
        raise RedactorError(f"File not found: {in_path}") from exc
    except UnicodeDecodeError as exc:
        raise RedactorError(f"File is not valid UTF-8 text: {in_path}") from exc
    except OSError as exc:
        raise RedactorError(f"Could not read input file '{in_path}': {exc}") from exc

    redacted = (
        redact_lines(content, entity_list)
        if line_by_line
        else redact_text(content, entity_list)
    )
    try:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(redacted)
    except OSError as exc:
        raise RedactorError(f"Could not write output file '{out_path}': {exc}") from exc
    return redacted


def main(argv=None) -> int:
    """Command-line entry point for Team 3 PII Redactor."""
    parser = argparse.ArgumentParser(
        description="Detect and anonymize Team 3 Italian PII entities."
    )
    parser.add_argument(
        "-e",
        "--entities",
        default=None,
        help=(
            "Comma or space separated list of entities to redact "
            f"(default: all Team 3 entities: {', '.join(SUPPORTED_ENTITIES)})"
        ),
    )
    parser.add_argument("-t", "--text", help="Text string to anonymize.")
    parser.add_argument("-i", "--input", help="Path to UTF-8 input text file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output file when using --input (default: <input>.redacted).",
    )
    parser.add_argument(
        "-b",
        "--batch-lines",
        action="store_true",
        help="Process input line by line (each line treated as an independent record).",
    )
    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Print a summary count of detected PII entities.",
    )

    args = parser.parse_args(argv)
    if args.text is None and not args.input:
        parser.error("Provide either --text (-t) or --input (-i).")

    try:
        if args.input:
            out_path = args.output or f"{args.input}.redacted"
            with open(args.input, encoding="utf-8") as handle:
                raw_text = handle.read()
            redact_file(
                args.input,
                out_path,
                entities=args.entities,
                line_by_line=args.batch_lines,
            )
            print(f"Wrote anonymized output to {out_path}")
            if args.summary:
                counts = summarize(
                    raw_text, entities=args.entities, line_by_line=args.batch_lines
                )
                summary_str = (
                    ", ".join(f"{k}: {v}" for k, v in counts.items()) or "none"
                )
                print(f"Summary: {summary_str}")
        else:
            output = (
                redact_lines(args.text, args.entities)
                if args.batch_lines
                else redact_text(args.text, args.entities)
            )
            print(output)
            if args.summary:
                counts = summarize(
                    args.text, entities=args.entities, line_by_line=args.batch_lines
                )
                summary_str = (
                    ", ".join(f"{k}: {v}" for k, v in counts.items()) or "none"
                )
                print(f"Summary: {summary_str}")
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"Error: File is not valid UTF-8 text: {args.input}", file=sys.stderr)
        return 1
    except RedactorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())