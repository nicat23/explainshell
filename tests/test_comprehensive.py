import unittest
import sys
import os


class TestComprehensive(unittest.TestCase):
    def test_package_structure(self):
        # Test that main package can be imported
        import explainshell
        self.assertIsNotNone(explainshell)

    def test_all_basic_modules_importable(self):
        # Test basic module imports
        modules = ['config', 'errors', 'helpconstants']
        for module in modules:
            try:
                mod = __import__(f'explainshell.{module}', fromlist=[module])
                self.assertIsNotNone(mod)
            except ImportError as e:
                self.fail(f"Failed to import explainshell.{module}: {e}")

    def test_util_module_complete(self):
        # Test all util functions are accessible
        from explainshell import util
        functions = ['consecutive', 'groupcontinuous', 'toposorted', 'pairwise', 'namesection']
        for func_name in functions:
            self.assertTrue(hasattr(util, func_name))
            self.assertTrue(callable(getattr(util, func_name)))

    def test_features_module_complete(self):
        # Test all feature functions are accessible
        from explainshell.algo import features
        functions = ['extract_first_line', 'starts_with_hyphen', 'is_indented', 'word_count', 'has_bold']
        for func_name in functions:
            self.assertTrue(hasattr(features, func_name))
            self.assertTrue(callable(getattr(features, func_name)))

    def test_constants_accessibility(self):
        # Test that constants are accessible
        from explainshell import helpconstants
        constants = ['PIPELINES', 'REDIRECTION', 'OPERATORS', 'parameters']
        for const_name in constants:
            self.assertTrue(hasattr(helpconstants, const_name))

    def test_error_classes_inheritance(self):
        # Test error class inheritance
        from explainshell.errors import ProgramDoesNotExist, EmptyManpage
        self.assertTrue(issubclass(ProgramDoesNotExist, Exception))
        self.assertTrue(issubclass(EmptyManpage, Exception))