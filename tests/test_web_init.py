import unittest


class TestWebInit(unittest.TestCase):
    def test_web_module_import(self):
        try:
            import explainshell.web
            self.assertIsNotNone(explainshell.web)
        except ImportError:
            self.skipTest("Flask not available")

    def test_web_has_app_instance(self):
        try:
            from explainshell.web import app
            self.assertIsNotNone(app)
        except ImportError:
            self.skipTest("Flask not available")