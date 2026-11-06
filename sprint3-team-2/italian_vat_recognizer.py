"""Italian VAT detection with format, office-code, and context checks."""
import re

from presidio_analyzer import Pattern
from presidio_analyzer.predefined_recognizers import ItVatCodeRecognizer


class ItalianVatRecognizer(ItVatCodeRecognizer):
    """Keep Presidio's checksum check and add the issue's format requirements."""

    VAT_LABEL = (
        r"(?:partita[ \t]+iva|p[._]?[ \t]*iva|"
        r"vat[ \t]+(?:codes?|numbers?)|codice[ \t]+iva)"
    )
    # Only a short, known label-to-value phrase may precede an unprefixed code.
    CONTEXT_BEFORE = re.compile(
        rf"(?<!\w){VAT_LABEL}(?!\w)[ \t:#=\-]{{0,16}}"
        r"(?:(?:is|equals|è)[ \t:#=\-]{1,16})?$",
        re.IGNORECASE,
    )
    # Continue a labeled list only across commas or explicit conjunctions.
    LIST_SEPARATOR = re.compile(
        r"[ \t]*(?:,[ \t]*(?:(?:and|or|e|o|&)[ \t]+)?|"
        r"(?:and|or|e|o|&)[ \t]+)[ \t]*",
        re.IGNORECASE,
    )

    def __init__(self, supported_language="en"):
        """Match the original value, including its country prefix and separators."""
        super().__init__(
            supported_language=supported_language,
            name="ItalianVatRecognizer",
            patterns=[
                Pattern(
                    "Italian VAT",
                    r"(?i)(?<!\w)(?:IT[ \t]*)?"
                    r"[0-9](?:[ \t_]*[0-9]){10}(?!\w|[ \t_]*[0-9])",
                    0.1,
                )
            ],
            context=[
                "partita iva", "p.iva", "p_iva", "piva",
                "vat code", "vat number", "codice iva",
            ],
        )

    def validate_result(self, pattern_text):
        """Reject invalid components before using Presidio's Luhn validation."""
        number = re.sub(r"[ \t_]", "", pattern_text).upper()
        if number.startswith("IT"):
            number = number[2:]
        if re.fullmatch(r"[0-9]{11}", number) is None:
            return False
        if int(number[:7]) == 0:
            return False
        office = int(number[7:10])
        # Office rules: https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/it/iva.py
        if office not in range(1, 101) and office not in {120, 121, 888, 999}:
            return False
        return super().validate_result(number)

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        """Accept labeled lists without carrying context into unrelated fields."""
        results = super().analyze(
            text, entities, nlp_artifacts=nlp_artifacts, regex_flags=regex_flags
        )
        standalone = re.fullmatch(r"[^\w]*[0-9]{11}[^\w]*", text) is not None
        accepted = []
        labeled_end = None
        for result in sorted(results, key=lambda match: match.start):
            has_label = self.CONTEXT_BEFORE.search(text[:result.start]) is not None
            continues_list = (
                labeled_end is not None
                and self.LIST_SEPARATOR.fullmatch(text[labeled_end:result.start]) is not None
            )
            prefixed = text[result.start:result.end].upper().startswith("IT")
            if prefixed or standalone or has_label or continues_list:
                accepted.append(result)
            # A prefix alone must not establish context for unrelated numbers.
            labeled_end = result.end if has_label or continues_list else None
        return accepted
