"""Final test to achieve 100% coverage for views.py"""

import unittest
from unittest.mock import MagicMock

from explainshell.web import views


class TestViewsFinalCoverage(unittest.TestCase):
    """Test to cover the final missing line in views.py"""

    def test_formatmatch_assert_expandedmatch(self):
        """Test formatmatch to ensure expandedmatch assertion is covered"""
        d = {"match": "", "commandclass": "command0"}
        m = MagicMock()
        m.start = 0
        m.end = 10
        m.match = "echo hello"
        expansions = [(5, 10, "parameter")]  # "hello" as parameter

        views.formatmatch(d, m, expansions)

        # The assertion should pass and expandedmatch should be populated
        self.assertNotEqual(str(d["match"]), "")
        self.assertIn("expansion-parameter", str(d["match"]))


if __name__ == '__main__':
    unittest.main()
