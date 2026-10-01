"""Unit test file for team _1"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam__1(unittest.TestCase):
    """Test team _1 PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_es_nie(self):
        """Test ES_NIE functionality"""
        valid_cases = [
            ("NIE X1234567L", "X1234567L"),
            ("NIE Y1234567X", "Y1234567X"),
            ("NIE Z1234567R", "Z1234567R"),
            ("NIE x1234567l", "x1234567l"),
            ("número de identificación de extranjero X1234567L",
             "X1234567L"),
        ]

        for text, expected_value in valid_cases:
            results = analyze_text(text, entity_list=['ES_NIE'])
            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result.entity_type, 'ES_NIE')
            self.assertEqual(text[result.start:result.end], expected_value)

        multiple_ids = "NIE X0000000T and NIE Y0000000Z"
        results = analyze_text(multiple_ids, entity_list=['ES_NIE'])
        detected_values = [multiple_ids[result.start:result.end]
                           for result in results]
        self.assertCountEqual(detected_values, ['X0000000T', 'Y0000000Z'])

        invalid_cases = [
            "NIE X1234567A",
            "NIE A1234567L",
            "NIE 12345678Z",
            "NIE X1234567",
            "NIE X12345678L",
        ]

        for text in invalid_cases:
            self.assertEqual(analyze_text(text, entity_list=['ES_NIE']), [])

    def test_es_nif(self):
        """Test ES_NIF functionality"""
        positive_cases = [
            ("Mi NIF es 12345678Z", "12345678Z"),
            ("NIF: 87654321X", "87654321X"),
            ("Tax ID: 12345678Z", "12345678Z"),
            ("NIF: 87654321-X", "87654321-X"),
        ]

        for text, expected_value in positive_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["ES_NIF"])
                self.assertTrue(
                    any(
                        match.entity_type == "ES_NIF"
                        and text[match.start:match.end] == expected_value
                        for match in matches
                    ),
                    f"Expected ES_NIF match {expected_value!r} in: {text}",
                )

        negative_cases = [
            "NIF: 1234567Z",
            "NIF: 123456789Z",
            "The code is 12345678",
            "Order number: 12345678A",
            "Tax ID: 1234567A",
        ]

        for text in negative_cases:
            with self.subTest(text=text):
                matches = analyze_text(text, ["ES_NIF"])
                self.assertFalse(any(match.entity_type == "ES_NIF" for match in matches),
                                 f"Unexpected ES_NIF match found in: {text}")

    def test_fi_personal_identity_code(self):
        """Test FI_PERSONAL_IDENTITY_CODE functionality"""

    def test_iban_code(self):
        """Test IBAN_CODE functionality"""
        entity = ['IBAN_CODE']


        # Positive: valid IBANs from several countries
        valid_ibans = [
            'GB29NWBK60161331926819',       # example from issue #20
            'GB82WEST12345698765432',       # United Kingdom
            'DE89370400440532013000',       # Germany
            'FR1420041010050500013M02606',  # France (letter in BBAN)
            'NL91ABNA0417164300',           # Netherlands
        ]
        for iban in valid_ibans:
            # Mask all but country code and last 4 in failure messages
            masked = iban[:2] + '*' * (len(iban) - 6) + iban[-4:]
            with self.subTest(iban=masked):
                text = f'Please send the payment to {iban} by Friday.'
                result = analyze_text(text, entity)
                self.assertEqual(len(result), 1, masked)
                self.assertEqual(result[0].entity_type, 'IBAN_CODE')

        # Positive: IBAN written with spaces, location returned
        text = 'Pay to GB29 NWBK 6016 1331 9268 19 today'
        result = analyze_text(text, entity)
        self.assertEqual(len(result), 1)
        self.assertEqual(text[result[0].start:result[0].end],
                         'GB29 NWBK 6016 1331 9268 19')

        # Positive: exact location without spaces
        result = analyze_text('IBAN: GB29NWBK60161331926819', entity)
        self.assertEqual((result[0].start, result[0].end), (6, 28))

        # Positive: multiple IBANs in one document
        text = ('Primary: DE89370400440532013000. '
                'Backup: FR1420041010050500013M02606.')
        result = analyze_text(text, entity)
        found = sorted(text[r.start:r.end] for r in result)
        self.assertEqual(found, ['DE89370400440532013000',
                                 'FR1420041010050500013M02606'])

        # Positive: contextual term nearby
        text = 'My International Bank Account Number is NL91ABNA0417164300'
        result = analyze_text(text, entity)
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(result[0].score, 0.5)

        # Negative: invalid structure, length, or checksum
        invalid_texts = [
            'Send to GB29NWBK60161331926818',  # bad checksum (last digit)
            'Send to DE8937040044053201300',   # too short for Germany
            'Send to XX29NWBK60161331926819',  # not a real country code
        ]
        # Negative: common false positives
        invalid_texts += [
            'ISBN 978-0-306-40615-7 is on the reading list.',
            'Call me at 919-555-0123.',
            'Order number AB12345678 shipped on 2026-09-30.',
            'Meet me at the library at noon.',
        ]
        for text in invalid_texts:
            with self.subTest(text=text):
                self.assertEqual(analyze_text(text, entity), [])

        # Masking: anonymize_text hides the IBAN in output
        from pii_scan import anonymize_text  # local import avoids conflicts
        text = 'Pay GB29 NWBK 6016 1331 9268 19 today'
        masked = anonymize_text(text, entity)
        self.assertEqual(masked, 'Pay <IBAN_CODE> today')
        self.assertNotIn('NWBK', masked)

    def test_ip_address(self):
        """Test IP_ADDRESS functionality"""
        valid_cases = [
            ("Login failed for user from IP 203.0.113.42",
             "203.0.113.42", 0.95),
            ("Allow traffic from 198.51.100.0/24", "198.51.100.0/24", 0.6),
            ("Client connected via 2001:db8:85a3::8a2e:370:7334",
             "2001:db8:85a3::8a2e:370:7334", 0.6),
            ("ipv6 loopback is ::1", "::1", 0.95),
            ("Mapped address ::ffff:192.0.2.10", "::ffff:192.0.2.10", 0.6),
        ]

        for text, expected_value, expected_score in valid_cases:
            results = analyze_text(text, entity_list=['IP_ADDRESS'])
            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result.entity_type, 'IP_ADDRESS')
            self.assertEqual(text[result.start:result.end], expected_value)
            self.assertAlmostEqual(result.score, expected_score)

        invalid_cases = [
            "Octet out of range: 256.1.1.1",
            "Only three parts: 192.0.2",
            "Bad IPv6 2001:db8::1::2",
            "The meeting started at 12:30:45",
            "Visit example.com",
        ]

        for text in invalid_cases:
            self.assertEqual(analyze_text(text, entity_list=['IP_ADDRESS']), [])


if __name__ == '__main__':
    unittest.main()