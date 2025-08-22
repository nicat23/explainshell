"""Simple tests to improve coverage without complex mocking"""

import unittest
from unittest.mock import MagicMock, patch

from explainshell import manpage, matcher, store
from explainshell.web import views


class TestSimpleCoverage(unittest.TestCase):
    """Simple tests to improve coverage"""

    def test_manpage_extracted_from_parse_with_items(self):
        """Test _extracted_from_parse_7 with valid items"""
        mp = manpage.manpage('/test/prog.1.gz')
        mp.synopsis = '/test/prog.1.gz: "prog - description"'
        mp.aliases = {'prog'}

        with patch(
            'explainshell.manpage._parsesynopsis',
            return_value=('prog', 'description')
        ):
            mp._extracted_from_parse_7()

        self.assertEqual(mp.synopsis, 'description')
        # Just verify the method completed without error
        self.assertIsNotNone(mp.aliases)

    def test_matcher_visitredirect_simple(self):
        """Test visitredirect with simple output"""
        m = matcher.matcher("echo > file", MagicMock())
        node = MagicMock()
        node.pos = [5, 11]

        m.visitredirect(node, None, ">", "file", None)

        self.assertEqual(len(m.groups[0].results), 1)

    def test_store_verify_return_types(self):
        """Test store verify return types"""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_mapping = MagicMock()
        mock_manpage = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: {
            'classifier': MagicMock(),
            'manpage': mock_manpage,
            'mapping': mock_mapping
        }[name]

        mock_mapping.find.return_value = []
        mock_manpage.find.return_value = []

        with patch('pymongo.MongoClient', return_value=mock_client):
            s = store.store()
            ok, unreachable, notfound = s.verify()

            self.assertTrue(ok)
            # unreachable can be list or set depending on implementation
            self.assertIn(type(unreachable), [list, set])
            self.assertIsInstance(notfound, set)

    def test_views_source_calculation(self):
        """Test views source calculation"""
        matches = [{"commandclass": "command0", "match": "echo"}]
        commandgroup = MagicMock()
        commandgroup.manpage.name = "echo"
        commandgroup.manpage.section = "1"
        commandgroup.manpage.source = "echo.1.gz"
        commandgroup.suggestions = []

        views._add_command_metadata(matches, commandgroup)

        # Source removes last 5 characters (.1.gz -> 5 chars)
        self.assertEqual(matches[0]["source"], "echo")


if __name__ == '__main__':
    unittest.main()
