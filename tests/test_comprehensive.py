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
        modules = ["config", "errors", "helpconstants"]
        
        def can_import_module(module):
            try:
                mod = __import__(f"explainshell.{module}", fromlist=[module])
                return mod is not None
            except ImportError:
                return False
        
        self.assertTrue(all(can_import_module(module) for module in modules),
                       "One or more basic modules failed to import")

    def test_util_module_complete(self):
        # Test all util functions are accessible
        from explainshell import util

        functions = [
            "consecutive",
            "groupcontinuous",
            "toposorted",
            "pairwise",
            "namesection",
        ]
        
        self.assertTrue(all(hasattr(util, func) and callable(getattr(util, func)) 
                           for func in functions),
                       "One or more util functions are missing or not callable")

    def test_features_module_complete(self):
        # Test all feature functions are accessible
        from explainshell.algo import features

        functions = [
            "extract_first_line",
            "starts_with_hyphen",
            "is_indented",
            "word_count",
            "has_bold",
        ]
        
        self.assertTrue(all(hasattr(features, func) and callable(getattr(features, func)) 
                           for func in functions),
                       "One or more feature functions are missing or not callable")

    def test_constants_accessibility(self):
        # Test that constants are accessible
        from explainshell import helpconstants

        constants = ["PIPELINES", "REDIRECTION", "OPERATORS", "parameters"]
        
        self.assertTrue(all(hasattr(helpconstants, const) for const in constants),
                       "One or more constants are missing from helpconstants")

    def test_error_classes_inheritance(self):
        # Test error class inheritance
        from explainshell.errors import ProgramDoesNotExist, EmptyManpage

        self.assertTrue(issubclass(ProgramDoesNotExist, Exception))
        self.assertTrue(issubclass(EmptyManpage, Exception))
