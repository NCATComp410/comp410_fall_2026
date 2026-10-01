"""Unit test file for team _a"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__a(unittest.TestCase):
    """Test team _a PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_url(self):
        """Test URL functionality"""
        positive_cases = [
            "https://example.com",
            "www.example.com",
            "My site is example.com",
            "The URL https://sub.example.com/path?q=1 is here",
        ]
        negative_cases = [
            "This is not a url: example",
            "Visit localhost on port 8000",
            "The secret code is ABC123",
        ]

        for text in positive_cases:
            with self.subTest(text=text):
                results = analyze_text(text, [])
                self.assertTrue(
                    any(getattr(result, 'entity_type', None) == 'URL' for result in results),
                    f"Expected a URL match in: {text!r}"
                )

        for text in negative_cases:
            with self.subTest(text=text):
                results = analyze_text(text, [])
                self.assertFalse(
                    any(getattr(result, 'entity_type', None) == 'URL' for result in results),
                    f"Did not expect a URL match in: {text!r}"
                )

    def test_us_bank_number(self):
        """Test US_BANK_NUMBER functionality"""
        # --- POSITIVE TESTS (Should detect as US_BANK_NUMBER) ---

        # Valid 10-digit account number with context
        text_10deg = "My direct deposit bank account number is 1234567890"
        results_10deg = analyze_text(text_10deg, ['US_BANK_NUMBER'])
        self.assertEqual(len(results_10deg), 1)
        self.assertEqual(results_10deg[0].entity_type, 'US_BANK_NUMBER')

        # Valid 12-digit account number with routing/account context
        text_12deg = "Transfer funds to routing/account number 987654321012"
        results_12deg = analyze_text(text_12deg, ['US_BANK_NUMBER'])
        self.assertEqual(len(results_12deg), 1)
        self.assertEqual(results_12deg[0].entity_type, 'US_BANK_NUMBER')


        # --- NEGATIVE TESTS (Should NOT detect as US_BANK_NUMBER) ---

        # Plain text
        text_plain = "TEST normal text"
        results_plain = analyze_text(text_plain, ['US_BANK_NUMBER'])
        self.assertEqual(len(results_plain), 0)

        # Short number string
        text_short = "TEST short number 123"
        results_short = analyze_text(text_short, ['US_BANK_NUMBER'])
        self.assertEqual(len(results_short), 0)

        # Phone number not a bank account
        text_phone = "Call our customer service team at 800-555-0199"
        results_phone = analyze_text(text_phone, ['US_BANK_NUMBER'])
        self.assertEqual(len(results_phone), 0)

    def test_us_driver_license(self):
        """Test US_DRIVER_LICENSE functionality"""
        # Positive test: generic format
        text = "My driver license number is D1234567"
        results = analyze_text(text, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, 'US_DRIVER_LICENSE')
        self.assertEqual(text[results[0].start:results[0].end], 'D1234567')

        # Positive test: Florida format
        text_fl = "Her Florida driver license number is S123456789012"
        results_fl = analyze_text(text_fl, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_fl), 1)
        self.assertEqual(results_fl[0].entity_type, 'US_DRIVER_LICENSE')

        # Negative test: no license number in the text
        text_neg = "The weather is sunny and I went to the park today"
        results_neg = analyze_text(text_neg, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_neg), 0)

        # Negative test: short number that is not a license
        text_neg2 = "My order number is 12"
        results_neg2 = analyze_text(text_neg2, ['US_DRIVER_LICENSE'])
        self.assertEqual(len(results_neg2), 0)

    def test_us_itin(self):
        """Test US_ITIN functionality"""
        valid_cases = [
            ("ITIN: 900-50-1234", "900-50-1234"),
            ("Tax ID: 912-65-4321", "912-65-4321"),
            ("IRS number 923-70-1234", "923-70-1234"),
            ("My taxpayer ID is 934-88-5678", "934-88-5678"),
            ("ITIN 945-90-1234", "945-90-1234"),
            ("Tax ID 956-92-4321", "956-92-4321"),
            ("IRS ITIN: 967-94-1234", "967-94-1234"),
            ("ITIN 978-96-4321", "978-96-4321"),
            ("ITIN: 900501234", "900501234"),
        ]

        for text, expected_value in valid_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["US_ITIN"])
                self.assertTrue(
                    any(
                        match.entity_type == "US_ITIN"
                        and text[match.start:match.end] == expected_value
                        for match in matches
                    ),
                    f"Expected US_ITIN match {expected_value!r} in: {text}",
                )

        invalid_cases = [
            "ITIN: 900-49-1234",
            "ITIN: 900-66-1234",
            "ITIN: 900-69-1234",
            "ITIN: 900-89-1234",
            "ITIN: 900-93-1234",
            "ITIN: 800-50-1234",
            "ITIN: 900-5-1234",
            "SSN: 123-45-6789",
        ]

        for text in invalid_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["US_ITIN"])
                self.assertFalse(
                    any(match.entity_type == "US_ITIN" for match in matches),
                    f"Unexpected US_ITIN match found in: {text}",
                )

    def test_us_passport(self):
        """Test US_PASSPORT functionality"""
        valid_passports = [
            "Passport number: P12345678",
            "US passport ID is AB1234567",
            "Passport card no. 123456789",
        ]
        invalid_passports = [
            "Passport number: 12345678",
            "US passport ID is ABC12345",
            "Passport no. XX123456",
        ]

        for text in valid_passports:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['US_PASSPORT'])
                matches = [result for result in results if result.entity_type == 'US_PASSPORT']
                self.assertTrue(matches, f'Expected a US_PASSPORT match in: {text}')

        for text in invalid_passports:
            with self.subTest(text=text):
                results = analyze_text(text, entity_list=['US_PASSPORT'])
                matches = [result for result in results if result.entity_type == 'US_PASSPORT']
                self.assertFalse(matches, f'Expected no US_PASSPORT match in: {text}')


if __name__ == '__main__':
    unittest.main()