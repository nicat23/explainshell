import unittest


class TestMatcherBasic(unittest.TestCase):
    def test_matcher_imports(self):
        # Test basic imports that don't require bashlex
        try:
            from explainshell.matcher import (
                matchresult,
                matchgroup,
                matchwordexpansion,
            )

            self.assertTrue(callable(matchresult))
            self.assertTrue(callable(matchgroup))
            self.assertTrue(callable(matchwordexpansion))
        except ImportError:
            self.skipTest("bashlex not available")

    def test_matchresult_creation(self):
        try:
            from explainshell.matcher import matchresult

            mr = matchresult(0, 5, "test", None)
            self.assertEqual(mr.start, 0)
            self.assertEqual(mr.end, 5)
            self.assertEqual(mr.text, "test")
        except ImportError:
            self.skipTest("bashlex not available")
