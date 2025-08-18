import unittest


class TestManpageBasic(unittest.TestCase):
    def test_manpage_imports(self):
        # Test basic imports that don't require store
        try:
            from explainshell.manpage import paragraph
            self.assertTrue(callable(paragraph))
        except ImportError:
            self.skipTest("dependencies not available")

    def test_paragraph_creation(self):
        try:
            from explainshell.manpage import paragraph
            p = paragraph(1, "test text", "DESCRIPTION", True)
            self.assertEqual(p.idx, 1)
            self.assertEqual(p.text, "test text")
            self.assertEqual(p.section, "DESCRIPTION")
            self.assertTrue(p.is_option)
        except ImportError:
            self.skipTest("dependencies not available")