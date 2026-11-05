"""Team CodeClan - command-line PII redactor.

Examples:
    python codeclan_cli.py -e AU_TFN,AU_ABN "My TFN is 876 543 210"
    python codeclan_cli.py -f notes.txt -o notes_redacted.txt --summary
    python codeclan_cli.py -f a.txt b.txt c.txt --out-dir redacted/   (batch)
    echo "Routing 021000021" | python codeclan_cli.py
    python codeclan_cli.py --list-entities

Exit codes: 0 = success, 1 = invalid input, 2 = bad command-line usage.

Author: Jasmine & Ryan, Team CodeClan. See README "Who did what".
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codeclan_redactor import (ALL_KEYWORD, TEAM_ENTITIES, RedactorError,
                               redact, supported_entities)


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Redact PII from text using pii_scan.anonymize_text().")
    parser.add_argument("text", nargs="?",
                        help="text to anonymize (omit to use --file or stdin)")
    parser.add_argument("-e", "--entities", default="",
                        help="comma/space separated entity types; blank = team "
                             f"CodeClan defaults; '{ALL_KEYWORD}' = every entity")
    parser.add_argument("-f", "--file", nargs="+", type=Path, metavar="PATH",
                        help="read text from one or more UTF-8 files (batch mode)")
    parser.add_argument("-o", "--output", type=Path,
                        help="write the redacted text to this file (single input)")
    parser.add_argument("--out-dir", type=Path,
                        help="batch mode: write <name>_redacted<ext> files here")
    parser.add_argument("-s", "--summary", action="store_true",
                        help="print a count of redacted entities to stderr")
    parser.add_argument("--list-entities", action="store_true",
                        help="list supported entity types and exit")
    return parser


def _list_entities() -> None:
    print("Team CodeClan entities (default):")
    for name, label in TEAM_ENTITIES.items():
        print(f"  {name:<20} {label}")
    print("\nAll entities supported by pii_scan:")
    print("  " + ", ".join(supported_entities()))


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RedactorError(f"File not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise RedactorError(f"{path} is not a UTF-8 text file.") from exc
    except OSError as exc:
        raise RedactorError(f"Could not read {path}: {exc.strerror}") from exc


def _write_file(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise RedactorError(f"Could not write {path}: {exc.strerror}") from exc


def _collect_jobs(parser, args) -> list:
    """Return [(path_or_None, text), ...] from TEXT, --file, or stdin."""
    if args.text is not None and args.file:
        parser.error("give either TEXT or --file, not both")
    if args.output and args.file and len(args.file) > 1:
        parser.error("--output works with a single input; use --out-dir for batches")
    if args.file:
        return [(p, _read_file(p)) for p in args.file]
    if args.text is not None:
        return [(None, args.text)]
    if not sys.stdin.isatty():
        return [(None, sys.stdin.read())]
    parser.error("no input: pass TEXT, --file, or pipe text on stdin")
    return []  # unreachable: parser.error exits


def _emit(args, path, result, batch: bool) -> None:
    """Write one result to --out-dir, --output, or stdout."""
    if args.out_dir and path is not None:
        dest = args.out_dir / f"{path.stem}_redacted{path.suffix}"
        _write_file(dest, result.redacted)
        print(f"{path} -> {dest}", file=sys.stderr)
    elif args.output:
        _write_file(args.output, result.redacted)
    else:
        if batch:
            print(f"===== {path} =====")
        # keep the input's own trailing newline instead of adding a second one
        print(result.redacted, end="" if result.redacted.endswith("\n") else "\n")
    if args.summary:
        label = f"{path}: " if path is not None else ""
        print(label + result.summary(), file=sys.stderr)


def run(argv: list[str] | None = None) -> int:
    """Entry point; returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_entities:
        _list_entities()
        return 0
    try:
        jobs = _collect_jobs(parser, args)
        for path, text in jobs:
            if not text.strip():
                label = f"{path}: " if path is not None else ""
                print(f"Note: {label}input is empty - nothing to redact.", file=sys.stderr)
            _emit(args, path, redact(text, args.entities), batch=len(jobs) > 1)
    except RedactorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
