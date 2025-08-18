import unittest


class TestOptionsBasic(unittest.TestCase):
    def test_options_regex_patterns(self):
        # Test regex patterns that don't require store
        try:
            from explainshell.options import SHORTOPT, LONGOPT
            import re
            self.assertIsInstance(SHORTOPT, type(re.compile('')))
            self.assertIsInstance(LONGOPT, type(re.compile('')))
        except ImportError:
            self.skipTest("dependencies not available")

    def test_shortopt_pattern(self):
        try:
            from explainshell.options import SHORTOPT
            # Test basic short option matching
            match = SHORTOPT.match("-v")
            self.assertIsNotNone(match)
            match = SHORTOPT.match("--verbose")
            self.assertIsNone(match)
        except ImportError:
            self.skipTest("dependencies not available")

    def test_longopt_pattern(self):
        try:
            from explainshell.options import LONGOPT
            # Test basic long option matching
            match = LONGOPT.match("--verbose")
            self.assertIsNotNone(match)
            match = LONGOPT.match("-v")
            self.assertIsNone(match)
        except ImportError:
            self.skipTest("dependencies not available")