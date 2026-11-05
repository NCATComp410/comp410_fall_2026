"""Team CodeClan - Sprint 3 PII redactor.

Core logic shared by the command-line tool (codeclan_cli.py) and the web app
(codeclan_web_app.py). All redaction goes through pii_scan.anonymize_text().

Team CodeClan supports these entity types (Sprint 1 / Sprint 2):
    ABA_ROUTING_NUMBER, AU_ABN, AU_ACN, AU_MEDICARE, AU_TFN
"""
from __future__ import annotations

import difflib
import re
from collections import Counter
from dataclasses import dataclass, field

from pii_scan import analyze_text, anonymize_text

# Entities this team is responsible for, with a short human-readable label.
TEAM_ENTITIES: dict[str, str] = {
    "ABA_ROUTING_NUMBER": "US ABA bank routing number",
    "AU_ABN": "Australian Business Number",
    "AU_ACN": "Australian Company Number",
    "AU_MEDICARE": "Australian Medicare card number",
    "AU_TFN": "Australian Tax File Number",
}

# Keyword that expands to every entity the analyzer supports.
ALL_KEYWORD = "ALL"

# spaCy's default limit is 1,000,000 characters; stay well under it so a
# request fails with a clear message instead of a spaCy stack trace.
MAX_TEXT_LENGTH = 100_000

_PLACEHOLDER_RE = re.compile(r"<([A-Z][A-Z0-9_]*)>")


class RedactorError(ValueError):
    """Raised for invalid user input (bad entity names, bad text, etc.)."""


@dataclass
class RedactionResult:
    """The outcome of a redaction request."""
    original: str
    redacted: str
    entities: list[str]
    counts: Counter = field(default_factory=Counter)

    @property
    def total(self) -> int:
        """Total number of PII values that were redacted."""
        return sum(self.counts.values())

    def summary(self) -> str:
        """One-line, human-readable summary of what was redacted."""
        if not self.total:
            return "No PII found."
        parts = [f"{name} x{n}" for name, n in sorted(self.counts.items())]
        return f"Redacted {self.total} item(s): " + ", ".join(parts)


def supported_entities() -> list[str]:
    """Every entity type the pii_scan analyzer can detect, sorted."""
    return sorted(set(analyze_text("", [], show_supported=True)))


def _split_names(text: str) -> list[str]:
    return text.replace(",", " ").replace(";", " ").split()


def _tokenize(raw) -> list[str]:
    """Turn a string or iterable of strings into a flat list of names."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return _split_names(raw)
    try:
        items = list(raw)
    except TypeError as exc:
        raise RedactorError("Entity list must be a string or a list of strings.") from exc
    tokens: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise RedactorError(f"Entity names must be strings, got {item!r}.")
        tokens.extend(_split_names(item))
    return tokens


def parse_entities(raw) -> list[str]:
    """Normalize an entity list supplied by the user.

    Accepts a string ("au_tfn, AU_ABN  aba_routing_number") or an iterable of
    strings. Names are upper-cased, de-duplicated (order preserved) and
    validated against the analyzer's supported entities.

    * Empty / blank input -> the team's default entities.
    * "ALL" -> every supported entity.

    :raises RedactorError: on an unknown entity name or a non-string value.
    """
    names = list(dict.fromkeys(t.upper() for t in _tokenize(raw)))
    if not names:
        return list(TEAM_ENTITIES)

    supported = supported_entities()
    if ALL_KEYWORD in names:
        return supported

    unknown = [n for n in names if n not in supported]
    if unknown:
        hints = []
        for name in unknown:
            close = difflib.get_close_matches(name, supported, n=1, cutoff=0.6)
            hints.append(f"{name} (did you mean {close[0]}?)" if close else name)
        raise RedactorError("Unknown entity type(s): " + ", ".join(hints)
                            + ". Use --list-entities to see valid names.")
    return names


def _validate_text(text) -> str:
    if text is None:
        raise RedactorError("No text was provided.")
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RedactorError("Text must be UTF-8 encoded.") from exc
    if not isinstance(text, str):
        raise RedactorError(f"Text must be a string, got {type(text).__name__}.")
    if len(text) > MAX_TEXT_LENGTH:
        raise RedactorError(f"Text is too long ({len(text):,} characters); "
                            f"the limit is {MAX_TEXT_LENGTH:,}.")
    return text


def _count_placeholders(text: str, entities: list[str]) -> Counter:
    wanted = set(entities)
    return Counter(m for m in _PLACEHOLDER_RE.findall(text) if m in wanted)


def redact(text, entities=None) -> RedactionResult:
    """Redact PII from ``text`` using pii_scan.anonymize_text().

    Every detected value is replaced by ``<ENTITY_TYPE>``; all other text is
    returned unchanged.

    :param text: the text to anonymize (str or UTF-8 bytes).
    :param entities: entity names (see parse_entities); blank = team defaults.
    :raises RedactorError: on invalid input.
    """
    text = _validate_text(text)
    entity_list = parse_entities(entities)

    # Nothing to scan: skip the NLP pipeline entirely.
    if not text.strip():
        return RedactionResult(text, text, entity_list)

    redacted = anonymize_text(text, entity_list)

    # Count placeholders that were *added*, so a literal "<AU_TFN>" already
    # present in the input is not reported as a redaction.
    counts = _count_placeholders(redacted, entity_list)
    counts.subtract(_count_placeholders(text, entity_list))
    counts = +counts  # drop zero / negative entries
    return RedactionResult(text, redacted, entity_list, counts)
