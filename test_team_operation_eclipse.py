"""Unit test file for team operation_eclipse"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam_operation_eclipse(unittest.TestCase):
    """Test team operation_eclipse PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_credit_card(self):
        """Test CREDIT_CARD functionality"""
        positive_examples = [
            "My card number is 4111111111111111.",
            "Visa: 4111 1111 1111 1111",
        ]

        for sample_text in positive_examples:
            results = analyze_text(sample_text, ['CREDIT_CARD'])
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            self.assertTrue(any(result.entity_type == 'CREDIT_CARD' for result in results))

        negative_examples = [
            "My phone number is 1234567890.",
            "The fallback code is 1234 5678 9012 3456.",
        ]

        for sample_text in negative_examples:
            results = analyze_text(sample_text, ['CREDIT_CARD'])
            self.assertEqual(results, [])

    def test_crypto(self):
        """Test CRYPTO functionality"""
        positive_cases = [
            "0x52908400098527886E0F7030069857D2E4169EE7",
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
            "ltc1" + "q" * 39,
        ]
        for address in positive_cases:
            with self.subTest(address=address):
                results = analyze_text(address, entity_list=['CRYPTO'])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].entity_type, 'CRYPTO')
                self.assertEqual(address[results[0].start:results[0].end], address)

        negative_cases = [
            "0x1234",
            "ABC123XYZ",
            "wallet address unavailable",
            "The quick brown fox jumps over the lazy dog.",
            "Wallet: 1BoatSLRHtKNngkdXEeobR",
            "Address 0x1234567890abcdef is incomplete.",
            "1IllegalO0lCharsNotValidBase58Address123",
            "Contact us at test@example.com for more info.",
            "",
            "Send funds to 1BoatSLRHtKNngkdXEeobR",
        ]
        for text in negative_cases:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, entity_list=['CRYPTO']), [])

    def test_date_time(self):
        """Test DATE_TIME functionality"""

    def test_email_address(self):
        """Test EMAIL_ADDRESS functionality"""
        email_text = (
            "Email: alex.smith+alerts@example.com; "
            "e-mail address: jordan_lee@dept.ncat.edu"
        )
        results = analyze_text(email_text, entity_list=['EMAIL_ADDRESS'])
        detected_addresses = {
            email_text[result.start:result.end]
            for result in results
            if result.entity_type == 'EMAIL_ADDRESS'
        }
        self.assertEqual(
            detected_addresses,
            {'alex.smith+alerts@example.com', 'jordan_lee@dept.ncat.edu'},
        )

        invalid_samples = [
            'Contact me at user@@example.com',
            'Contact me at @example.com',
            'Contact me at user@example',
            'This is ordinary text with no email address.',
            'Visit https://example.com/contact for details.',
        ]
        for sample in invalid_samples:
            with self.subTest(sample=sample):
                results = analyze_text(sample, entity_list=['EMAIL_ADDRESS'])
                self.assertFalse(
                    any(result.entity_type == 'EMAIL_ADDRESS' for result in results)
                )

    def test_medical_license(self):
        """Test MEDICAL_LICENSE functionality"""
        positive_examples = [
            "Medical license number: AB1000001",
            "DEA certificate number: AB1000001 is active.",
            "Physician license ID AB1000001 on file.",
        ]

        for sample_text in positive_examples:
            with self.subTest(sample_text=sample_text):
                results = analyze_text(sample_text, ['MEDICAL_LICENSE'])
                self.assertIsInstance(results, list)
                self.assertGreater(len(results), 0)
                self.assertTrue(any(result.entity_type == 'MEDICAL_LICENSE' for result in results))

        negative_examples = [
            "Medical license number: AB1234567",
            "The doctor claimed certificate AB9999999 but it is invalid.",
            "Contact us at test@example.com for more info.",
            "The quick brown fox jumps over the lazy dog.",
        ]

        for sample_text in negative_examples:
            with self.subTest(sample_text=sample_text):
                results = analyze_text(sample_text, ['MEDICAL_LICENSE'])
                self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
