import unittest
import explainshell.helpconstants as helpconstants


class TestHelpConstants(unittest.TestCase):
    def test_has_constants(self):
        # Test that key constants exist
        self.assertTrue(hasattr(helpconstants, '_function'))
        self.assertTrue(hasattr(helpconstants, 'PIPELINES'))
        self.assertTrue(hasattr(helpconstants, 'REDIRECTION'))

    def test_constants_are_strings(self):
        self.assertIsInstance(helpconstants._function, str)
        self.assertIsInstance(helpconstants.PIPELINES, str)
        self.assertIsInstance(helpconstants.REDIRECTION, str)

    def test_constants_not_empty(self):
        self.assertGreater(len(helpconstants._function), 0)
        self.assertGreater(len(helpconstants.PIPELINES), 0)
        self.assertGreater(len(helpconstants.REDIRECTION), 0)

    def test_operators_dict(self):
        self.assertTrue(hasattr(helpconstants, 'OPERATORS'))
        self.assertIsInstance(helpconstants.OPERATORS, dict)

    def test_parameters_dict(self):
        self.assertTrue(hasattr(helpconstants, 'parameters'))
        self.assertIsInstance(helpconstants.parameters, dict)