import unittest
import doctest
import explainshell.util
import explainshell.algo.features


class TestDocstrings(unittest.TestCase):
    def test_util_doctests(self):
        # Run doctests for util module
        result = doctest.testmod(explainshell.util, verbose=False)
        self.assertEqual(result.failed, 0, f"Doctest failures in util: {result.failed}")

    def test_features_doctests(self):
        # Run doctests for features module
        result = doctest.testmod(explainshell.algo.features, verbose=False)
        self.assertEqual(result.failed, 0, f"Doctest failures in features: {result.failed}")