"""Sprint-3 tests for Operation Eclipse: normal inputs and multiple PII occurrences.

These tests call anonymize_text() from pii_scan.py, which is the function our
application uses to redact PII. They cover our team's assigned entities:
CREDIT_CARD, CRYPTO, DATE_TIME, EMAIL_ADDRESS, MEDICAL_LICENSE.

Run with:  python -m pytest test_sprint3_operation_eclipse.py -v
"""
import unittest

from pii_scan import anonymize_text

TEAM_ENTITIES = ["CREDIT_CARD", "CRYPTO", "DATE_TIME", "EMAIL_ADDRESS", "MEDICAL_LICENSE"]

# Sample values that pass each recognizer's validation
CARD = "4111111111111111"            # passes the Luhn checksum
CARD_SPACED = "4111 1111 1111 1111"
CARD_DASHED = "4111-1111-1111-1111"
BTC = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
ETH = "0x52908400098527886E0F7030069857D2E4169EE7"
LTC = "ltc1" + "q" * 39
EMAIL = "jordan_lee@dept.ncat.edu"
LICENSE = "AB1000001"                # passes the DEA checksum


class TestNormalInputs(unittest.TestCase):
    """One piece of PII in an ordinary sentence is replaced and the rest is kept."""

    # (input text, entity, expected output)
    CASES = [
        (f"My card number is {CARD}.", "CREDIT_CARD",
         "My card number is <CREDIT_CARD>."),
        (f"Visa: {CARD_SPACED}", "CREDIT_CARD", "Visa: <CREDIT_CARD>"),
        (f"Charge {CARD_DASHED} today", "CREDIT_CARD", "Charge <CREDIT_CARD> today"),
        (f"Send the refund to {BTC} please.", "CRYPTO",
         "Send the refund to <CRYPTO> please."),
        (f"My ETH wallet is {ETH}", "CRYPTO", "My ETH wallet is <CRYPTO>"),
        (f"Litecoin address: {LTC}", "CRYPTO", "Litecoin address: <CRYPTO>"),
        ("My birthday is 05/24/2003.", "DATE_TIME", "My birthday is <DATE_TIME>."),
        ("My appointment is on October 15, 2026.", "DATE_TIME",
         "My appointment is on <DATE_TIME>."),
        ("The meeting is at 3:30 PM.", "DATE_TIME", "The meeting is at <DATE_TIME>."),
        (f"Email me at {EMAIL} with questions.", "EMAIL_ADDRESS",
         "Email me at <EMAIL_ADDRESS> with questions."),
        ("Contact alex.smith+alerts@example.com", "EMAIL_ADDRESS",
         "Contact <EMAIL_ADDRESS>"),
        (f"Medical license number: {LICENSE}", "MEDICAL_LICENSE",
         "Medical license number: <MEDICAL_LICENSE>"),
        (f"DEA certificate number: {LICENSE} is active.", "MEDICAL_LICENSE",
         "DEA certificate number: <MEDICAL_LICENSE> is active."),
    ]

    def test_each_entity_alone(self):
        """Each entity is redacted when it is the only one requested."""
        for text, entity, expected in self.CASES:
            with self.subTest(entity=entity, text=text):
                self.assertEqual(anonymize_text(text, [entity]), expected)

    def test_each_entity_with_full_team_list(self):
        """Requesting all five team entities gives the same result for single-PII text."""
        for text, entity, expected in self.CASES:
            if entity == "DATE_TIME":
                continue  # covered above; date words can overlap other types
            with self.subTest(entity=entity, text=text):
                self.assertEqual(anonymize_text(text, TEAM_ENTITIES), expected)

    def test_original_value_is_removed(self):
        """The real PII value must not appear anywhere in the output."""
        values = [CARD, BTC, ETH, EMAIL, LICENSE]
        text = "Values: " + " | ".join(values)
        output = anonymize_text(text, TEAM_ENTITIES)
        for value in values:
            with self.subTest(value=value):
                self.assertNotIn(value, output)

    def test_only_requested_entity_is_redacted(self):
        """PII of a type that was not requested is left alone."""
        text = f"Email {EMAIL}, card {CARD}"
        self.assertEqual(anonymize_text(text, ["EMAIL_ADDRESS"]),
                         f"Email <EMAIL_ADDRESS>, card {CARD}")
        self.assertEqual(anonymize_text(text, ["CREDIT_CARD"]),
                         f"Email {EMAIL}, card <CREDIT_CARD>")


class TestMultipleOccurrences(unittest.TestCase):
    """Several pieces of PII in one text, of the same type and of mixed types."""

    def test_multiple_same_type(self):
        """Every occurrence of the same entity type is redacted."""
        cases = [
            ("Cards on file: 4111111111111111, 5555555555554444 and 378282246310005.",
             ["CREDIT_CARD"],
             "Cards on file: <CREDIT_CARD>, <CREDIT_CARD> and <CREDIT_CARD>."),
            (f"Wallets: {BTC} and {ETH}", ["CRYPTO"],
             "Wallets: <CRYPTO> and <CRYPTO>"),
            ("CC a@b.com, c@d.org and e@f.net", ["EMAIL_ADDRESS"],
             "CC <EMAIL_ADDRESS>, <EMAIL_ADDRESS> and <EMAIL_ADDRESS>"),
            (f"Licenses {LICENSE} and {LICENSE} match.", ["MEDICAL_LICENSE"],
             "Licenses <MEDICAL_LICENSE> and <MEDICAL_LICENSE> match."),
            ("Hired on 05/24/2003. Promoted on 06/01/2004.", ["DATE_TIME"],
             "Hired on <DATE_TIME>. Promoted on <DATE_TIME>."),
            ("I was born on 05/24/2003 and graduated on May 10, 2025.", ["DATE_TIME"],
             "I was born on <DATE_TIME> and graduated on <DATE_TIME>."),
        ]
        for text, entities, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(anonymize_text(text, entities), expected)

    def test_close_dates_merge_into_one_tag(self):
        """Found while testing: spaCy reads '05/24/2003, end 06/01/2004' as ONE date
        range, so both dates (and the word 'end') become a single <DATE_TIME> tag.
        No date leaks, so we record the behaviour instead of treating it as a failure."""
        output = anonymize_text("Start 05/24/2003, end 06/01/2004.", ["DATE_TIME"])
        self.assertEqual(output, "Start <DATE_TIME>.")
        self.assertNotIn("2003", output)
        self.assertNotIn("2004", output)

    def test_space_separated_cards_merge_into_one_tag(self):
        """Found while testing: Presidio's anonymizer merges same-type PII separated
        only by whitespace, so two cards become one tag. Nothing leaks."""
        output = anonymize_text(f"{CARD} {CARD}", ["CREDIT_CARD"])
        self.assertEqual(output, "<CREDIT_CARD>")
        self.assertEqual(anonymize_text(f"{CARD}, {CARD}", ["CREDIT_CARD"]),
                         "<CREDIT_CARD>, <CREDIT_CARD>")

    def test_same_value_repeated(self):
        """The same value appearing twice is redacted both times."""
        text = f"{EMAIL} wrote to {EMAIL}"
        self.assertEqual(anonymize_text(text, ["EMAIL_ADDRESS"]),
                         "<EMAIL_ADDRESS> wrote to <EMAIL_ADDRESS>")

    def test_all_five_entities_mixed(self):
        """One sentence containing every team entity."""
        text = (f"On 05/24/2003 Dr. Lee (license {LICENSE}) emailed {EMAIL} "
                f"about card {CARD} and wallet {BTC}.")
        expected = ("On <DATE_TIME> Dr. Lee (license <MEDICAL_LICENSE>) emailed "
                    "<EMAIL_ADDRESS> about card <CREDIT_CARD> and wallet <CRYPTO>.")
        self.assertEqual(anonymize_text(text, TEAM_ENTITIES), expected)

    def test_mixed_with_repeats(self):
        """Multiple occurrences of several types in one text."""
        text = (f"Card {CARD} and {CARD_DASHED}; email a@b.com and c@d.org; "
                f"wallets {BTC} and {ETH}.")
        expected = ("Card <CREDIT_CARD> and <CREDIT_CARD>; email <EMAIL_ADDRESS> "
                    "and <EMAIL_ADDRESS>; wallets <CRYPTO> and <CRYPTO>.")
        self.assertEqual(anonymize_text(text, TEAM_ENTITIES), expected)
        self.assertEqual(anonymize_text(text, TEAM_ENTITIES).count("<"), 6)

    def test_multiline_text(self):
        """PII spread across lines is redacted and the line breaks are kept."""
        text = (f"Name: Pat\nEmail: {EMAIL}\n\nCard: {CARD}\n"
                f"License: {LICENSE}\n")
        expected = ("Name: Pat\nEmail: <EMAIL_ADDRESS>\n\nCard: <CREDIT_CARD>\n"
                    "License: <MEDICAL_LICENSE>\n")
        self.assertEqual(
            anonymize_text(text, ["EMAIL_ADDRESS", "CREDIT_CARD", "MEDICAL_LICENSE"]),
            expected)

    def test_non_pii_text_preserved(self):
        """Removing the placeholders gives back exactly the non-PII text."""
        text = f"Hello! Pay with {CARD} or {BTC}, then email {EMAIL}. Thanks :)"
        output = anonymize_text(text, ["CREDIT_CARD", "CRYPTO", "EMAIL_ADDRESS"])
        stripped = (output.replace("<CREDIT_CARD>", "").replace("<CRYPTO>", "")
                    .replace("<EMAIL_ADDRESS>", ""))
        self.assertEqual(stripped, "Hello! Pay with  or , then email . Thanks :)")


if __name__ == "__main__":
    unittest.main()
