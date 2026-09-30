"""Unit test file for team codeclan"""
import unittest
from pii_scan import analyze_text, show_aggie_pride  # noqa


class TestTeam_codeclan(unittest.TestCase):
    """Test team codeclan PII functions"""
    def test_show_aggie_pride(self):
        """Test to make sure Aggie Pride is shown correctly"""
        self.assertEqual(show_aggie_pride(), "Aggie Pride - Worldwide")

    def test_aba_routing_number(self): # Kamryn & Caleb
        """Test ABA_ROUTING_NUMBER functionality"""
        # positive test case - valid routing number
        text = "My bank routing number is 021000021"
        results = analyze_text(text, ['ABA_ROUTING_NUMBER'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, 'ABA_ROUTING_NUMBER')
        self.assertEqual(text[results[0].start:results[0].end], '021000021')

        # negative test case - last digit changed so checksum fails
        results = analyze_text("My bank routing number is 021000022", ['ABA_ROUTING_NUMBER'])
        self.assertEqual(len(results), 0)

    def test_au_abn(self):
       """Test AU_ABN functionality"""
       # positive test case - valid ABN
       text = "Our ABN is 51 824 753 556"
       results = analyze_text(text, ['AU_ABN'])
       self.assertEqual(len(results), 1)
       self.assertEqual(results[0].entity_type, 'AU_ABN')
       self.assertEqual(text[results[0].start:results[0].end], '51 824 753 556')

       # negative test case - invalid check digits
       results = analyze_text("Our ABN is 51 824 753 557", ['AU_ABN'])
       self.assertEqual(len(results), 0)

    def test_au_acn(self): # Jasmine & Ryan
        """Test AU_ACN functionality"""
        text = "The company ACN is 004 085 616"
        results = analyze_text(text, ['AU_ACN'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, 'AU_ACN')
        self.assertEqual(text[results[0].start:results[0].end], '004 085 616')

        results = analyze_text("The company ACN is 004 085 617", ['AU_ACN'])
        self.assertEqual(len(results), 0)

    def test_au_medicare(self): # Sapri
        """Test AU_MEDICARE functionality"""

    def test_au_tfn(self): # Kailyn & Marcus
        """Test AU_TFN functionality"""


if __name__ == '__main__':
    unittest.main()
