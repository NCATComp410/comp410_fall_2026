"""Tests for pii_scan"""
import unittest
import re
import os
from pii_scan import show_aggie_pride, analyze_text


class TestPIIScan(unittest.TestCase):
    """Tests for the pii_scan module"""
    def test_aggie_pride(self):
        """Test to make sure the Aggie Pride function works"""
        self.assertEqual('Aggie Pride - Worldwide', show_aggie_pride())

    def test_base_supported_entities(self):
        """Test to make sure the default supported entities are returned"""
        # read entities from team_entities.csv
        with open('team_entities.csv', encoding='utf-8') as f:
            entities = f.read().splitlines()
            # remove the header row
            entities = entities[1:]
        supported_entities = [entity.split(',')[0] for entity in entities]

        results = analyze_text('', [], show_supported=True)

        for entity in supported_entities:
            if entity:
                self.assertIn(entity, results)
            # Check to make sure recognizer actually loads the entity
                analyze_text('entity load test', entity_list=[entity])

    def test_starts_with_test(self):
        """Test to make sure all test methods start with test"""
        # In order to run as a test case the method name must start with test
        # This test checks to make sure all defines within test files start with test
        # This is a common mistake that can cause tests to be skipped
        for file in os.listdir('.'):
            if file.endswith('.py') and file.startswith('test_'):
                with open(file, encoding='utf-8') as f:
                    for line in f:
                        # make sure everything that looks like a method name starts with test
                        m = re.search(r'\s*def (\w+)', line)
                        if m:
                            err = 'Method name does not start with test: def '
                            err += m.group(1) + ' in ' + file
                            self.assertTrue(m.group(1).startswith('test'), err)

    def test_sample_entity_check(self):
        """Test to make sure a sample entity is correctly recognized"""
        sample_text = "My email is test@example.com"
        results = analyze_text(sample_text, entity_list=['EMAIL_ADDRESS'])
        # Results should be a list of RecognizerResults objects
        self.assertIsInstance(results, list)
        # Expect one result so check the the length of the results list
        self.assertEqual(len(results), 1)
        # Check for EMAIL entity, score, and string location
        for result in results:
            self.assertTrue(hasattr(result, 'score'))
            self.assertTrue(hasattr(result, 'start'))
            self.assertTrue(hasattr(result, 'end'))
            self.assertTrue(hasattr(result, 'entity_type'))
            # Check that email entity is correctly identified
            if result.entity_type == 'EMAIL_ADDRESS':
                self.assertEqual(sample_text[result.start:result.end], 'test@example.com')
                self.assertGreaterEqual(result.score, 0)
                self.assertLessEqual(result.score, 1)



