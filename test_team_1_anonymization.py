import unittest

from pii_scan import anonymize_text


class TestTeam1Anonymization(unittest.TestCase):

    def check_anonymization(self, text, entity):
        result = anonymize_text(text, [entity])

        sensitive_value = text.split(":")[-1].strip()
        original_label = text.split(":")[0]

        self.assertIsInstance(result, str)
        self.assertTrue(
            result.strip(),
            "Anonymized result is empty"
        )
        self.assertNotEqual(
            result,
            text,
            f"{entity} was not anonymized"
        )
        self.assertIn(
            original_label,
            result,
            "Original text context was not preserved"
        )
        self.assertNotIn(
            sensitive_value,
            result,
            f"{entity} was not anonymized"
        )

    def test_es_nie_anonymization(self):
        self.check_anonymization(
            "NIE: X1234567L",
            "ES_NIE"
        )

    def test_es_nif_anonymization(self):
        self.check_anonymization(
            "NIF: 12345678Z",
            "ES_NIF"
        )

    def test_fi_personal_identity_code_anonymization(self):
        self.check_anonymization(
            "Finnish ID: 131052-308T",
            "FI_PERSONAL_IDENTITY_CODE"
        )

    def test_iban_anonymization(self):
        self.check_anonymization(
            "IBAN: FI2112345600000785",
            "IBAN_CODE"
        )

    def test_ip_address_anonymization(self):
        self.check_anonymization(
            "IP: 192.168.1.1",
            "IP_ADDRESS"
        )


if __name__ == "__main__":
    unittest.main()
