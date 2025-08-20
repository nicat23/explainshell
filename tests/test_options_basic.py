import unittest


class TestOptionsBasic(unittest.TestCase):
    def test_options_regex_patterns(self):
        # Test regex patterns that don't require store
        try:
            from explainshell.options import opt_regex, opt2_regex
            import re

            self.assertIsInstance(opt_regex, type(re.compile("")))
            self.assertIsInstance(opt2_regex, type(re.compile("")))
        except ImportError:
            self.skipTest("dependencies not available")

    def test_opt_regex_pattern(self):
        try:
            from explainshell.options import opt_regex

            # Test basic option matching
            match = opt_regex.match("-v")
            self.assertIsNotNone(match)
            match = opt_regex.match("--verbose")
            self.assertIsNotNone(match)
        except ImportError:
            self.skipTest("dependencies not available")

    def test_opt2_regex_pattern(self):
        try:
            from explainshell.options import opt2_regex

            # Test basic flag matching (like dd options)
            match = opt2_regex.match("bs=1024")
            self.assertIsNotNone(match)
            match = opt2_regex.match("-v")
            self.assertIsNone(match)
        except ImportError:
            self.skipTest("dependencies not available")
