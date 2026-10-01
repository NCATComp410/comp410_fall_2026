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

    def test_crypto(self):
        """Test CRYPTO functionality"""
        # Valid Bitcoin (legacy, base58) address - the well-known Bitcoin Genesis address
        btc_text = "Please send funds to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa today."
        btc_results = analyze_text(text=btc_text, entity_list=["CRYPTO"])
        self.assertTrue(
            any(r.entity_type == "CRYPTO" for r in btc_results),
            "Valid Bitcoin address was not detected as CRYPTO"
        )

        # Valid Ethereum address (0x + 40 hex characters)
        eth_address = "0x" + ("1234567890abcdef" * 3)[:40]
        eth_text = f"My ETH wallet is {eth_address} for the payout."
        eth_results = analyze_text(text=eth_text, entity_list=["CRYPTO"])
        self.assertTrue(
            any(r.entity_type == "CRYPTO" for r in eth_results),
            "Valid Ethereum address was not detected as CRYPTO"
        )

        # Valid Litecoin (bech32) address (ltc1 + 39-59 lowercase alphanumeric chars)
        ltc_address = "ltc1" + ("q" * 39)
        ltc_text = f"Litecoin payment address: {ltc_address}"
        ltc_results = analyze_text(text=ltc_text, entity_list=["CRYPTO"])
        self.assertTrue(
            any(r.entity_type == "CRYPTO" for r in ltc_results),
            "Valid Litecoin address was not detected as CRYPTO"
        )

        # --- Negative test cases: text with no valid crypto address should not match ---

        # Plain text with no crypto address at all
        plain_text = "The quick brown fox jumps over the lazy dog."
        plain_results = analyze_text(text=plain_text, entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in plain_results),
            "Plain text with no address incorrectly flagged as CRYPTO"
        )

        # Bitcoin-like string that is too short to be a valid address
        short_btc_text = "Wallet: 1BoatSLRHtKNn is way too short."
        short_btc_results = analyze_text(text=short_btc_text, entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in short_btc_results),
            "Too-short Bitcoin-like string incorrectly flagged as CRYPTO"
        )

        # Ethereum-like string missing required length after 0x prefix
        short_eth_text = "Address 0x1234567890abcdef is incomplete."
        short_eth_results = analyze_text(text=short_eth_text, entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in short_eth_results),
            "Too-short Ethereum-like string incorrectly flagged as CRYPTO"
        )

        # Base58 excludes 0, O, I, l - a wallet-shaped string containing them should not match
        invalid_chars_text = "1IllegalO0lCharsNotValidBase58Address123"
        invalid_chars_results = analyze_text(text=invalid_chars_text, entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in invalid_chars_results),
            "String with invalid base58 characters incorrectly flagged as CRYPTO"
        )

        # Unrelated PII (email) should not be flagged as CRYPTO
        email_text = "Contact us at test@example.com for more info."
        email_results = analyze_text(text=email_text, entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in email_results),
            "Email address incorrectly flagged as CRYPTO"
        )

        # Empty string should produce no results
        empty_results = analyze_text(text="", entity_list=["CRYPTO"])
        self.assertFalse(
            any(r.entity_type == "CRYPTO" for r in empty_results),
            "Empty string incorrectly flagged as CRYPTO"
        )

    def test_date_time(self):
        """Test DATE_TIME functionality"""

    def test_email_address(self):
        """Test EMAIL_ADDRESS functionality"""

    def test_medical_license(self):
        """Test MEDICAL_LICENSE functionality"""


if __name__ == '__main__':
    unittest.main()
