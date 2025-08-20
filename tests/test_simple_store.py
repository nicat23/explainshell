import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Simple tests that don't require external dependencies
class TestSimpleStore(unittest.TestCase):
    def test_paragraph_creation(self):
        # Test basic paragraph creation without imports
        try:
            from explainshell.store import paragraph

            p = paragraph(1, "test text", "DESCRIPTION", True)
            self.assertEqual(p.idx, 1)
            self.assertEqual(p.text, "test text")
            self.assertEqual(p.section, "DESCRIPTION")
            self.assertTrue(p.is_option)
        except ImportError:
            self.skipTest("pymongo not available")

    def test_manpage_basic(self):
        try:
            from explainshell.store import manpage

            mp = manpage(
                "source", "name", "synopsis", [], [], False, False, False
            )
            self.assertEqual(mp.source, "source")
            self.assertEqual(mp.name, "name")
        except ImportError:
            self.skipTest("pymongo not available")
