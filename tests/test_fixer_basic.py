import unittest


class TestFixerBasic(unittest.TestCase):
    def test_fixer_imports(self):
        # Test basic imports that don't require full dependencies
        try:
            import explainshell.fixer
            self.assertIsNotNone(explainshell.fixer)
        except ImportError:
            self.skipTest("dependencies not available")

    def test_fixer_has_functions(self):
        try:
            from explainshell.fixer import splitcommand, findcommands
            self.assertTrue(callable(splitcommand))
            self.assertTrue(callable(findcommands))
        except ImportError:
            self.skipTest("dependencies not available")