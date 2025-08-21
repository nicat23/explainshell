"""Tests to improve coverage for web/views.py module"""

import unittest
from unittest.mock import MagicMock, patch

from explainshell.web import views
from explainshell import errors


class TestViewsCoverage(unittest.TestCase):
    """Test cases to improve coverage for web/views.py"""

    def test_checkoverlaps_with_overlap(self):
        """Test _checkoverlaps with overlapping matches"""
        s = "echo hello"
        matches = [
            {"start": 0, "end": 5},  # "echo "
            {"start": 3, "end": 8}   # "o hel" - overlaps with first
        ]
        
        with self.assertRaises(RuntimeError) as cm:
            views._checkoverlaps(s, matches)
        
        self.assertIn("explained overlap", str(cm.exception))

    def test_checkoverlaps_no_overlap(self):
        """Test _checkoverlaps with non-overlapping matches"""
        s = "echo hello"
        matches = [
            {"start": 0, "end": 4},   # "echo"
            {"start": 5, "end": 10}   # "hello"
        ]
        
        # Should not raise exception
        views._checkoverlaps(s, matches)

    def test_process_group_results_shell_group(self):
        """Test _process_group_results with shell group"""
        group = MagicMock()
        group.name = "shell"
        group.results = [
            MagicMock(start=0, end=4, text="help text", match="echo")
        ]
        
        texttoid = {}
        idstartpos = {}
        expansions = []
        
        with patch('explainshell.web.views.formatmatch') as mock_format:
            matches = views._process_group_results(
                group, texttoid, idstartpos, expansions, is_shell=True
            )
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["commandclass"], "shell")
        mock_format.assert_called_once()

    def test_process_group_results_unknown_command(self):
        """Test _process_group_results with unknown command"""
        group = MagicMock()
        group.name = "command0"
        group.results = [
            MagicMock(start=0, end=7, text=None, match="unknown")  # Unknown command
        ]
        
        texttoid = {}
        idstartpos = {}
        expansions = []
        
        with patch('explainshell.web.views.formatmatch') as mock_format:
            matches = views._process_group_results(
                group, texttoid, idstartpos, expansions
            )
        
        self.assertEqual(len(matches), 1)
        self.assertIn("unknown", matches[0]["commandclass"])
        self.assertEqual(matches[0]["helpclass"], "")

    def test_add_command_metadata_no_matches(self):
        """Test _add_command_metadata with empty matches"""
        matches = []
        commandgroup = MagicMock()
        
        # Should not crash with empty matches
        views._add_command_metadata(matches, commandgroup)
        
        self.assertEqual(len(matches), 0)

    def test_add_command_metadata_with_manpage(self):
        """Test _add_command_metadata with manpage"""
        matches = [{"commandclass": "command0", "match": "echo"}]
        commandgroup = MagicMock()
        commandgroup.manpage.name = "echo"
        commandgroup.manpage.section = "1"
        commandgroup.manpage.source = "echo.1.gz"
        commandgroup.suggestions = []
        
        views._add_command_metadata(matches, commandgroup)
        
        self.assertIn("simplecommandstart", matches[0]["commandclass"])
        self.assertEqual(matches[0]["name"], "echo")
        self.assertEqual(matches[0]["section"], "1")
        self.assertEqual(matches[0]["match"], "echo(1)")
        # Source removes last 5 characters (.1.gz)
        self.assertEqual(matches[0]["source"], "echo")

    def test_add_command_metadata_match_with_dot(self):
        """Test _add_command_metadata when match already contains dot"""
        matches = [{"commandclass": "command0", "match": "echo.1"}]
        commandgroup = MagicMock()
        commandgroup.manpage.name = "echo"
        commandgroup.manpage.section = "1"
        commandgroup.manpage.source = "echo.1.gz"
        commandgroup.suggestions = []
        
        views._add_command_metadata(matches, commandgroup)
        
        # Should not modify match when it already contains a dot
        self.assertEqual(matches[0]["match"], "echo.1")

    def test_formatmatch_no_expansions(self):
        """Test formatmatch with no expansions in match"""
        d = {"match": ""}
        m = MagicMock()
        m.start = 0
        m.end = 4
        m.match = "echo"
        expansions = []
        
        views.formatmatch(d, m, expansions)
        
        self.assertEqual(str(d["match"]), "echo")

    def test_formatmatch_with_expansions(self):
        """Test formatmatch with expansions in match"""
        d = {"match": "", "commandclass": "command0"}
        m = MagicMock()
        m.start = 0
        m.end = 12
        m.match = "echo $(date)"
        expansions = [(5, 11, "substitution")]  # $(date)
        
        with patch('explainshell.web.views._substitutionmarkup', return_value='<a>date</a>'):
            views.formatmatch(d, m, expansions)
        
        self.assertIn("hasexpansion", d["commandclass"])
        self.assertIn('<span class="expansion-substitution">', str(d["match"]))

    def test_formatmatch_expansion_with_spaces(self):
        """Test formatmatch with expansion containing spaces"""
        d = {"match": "", "commandclass": "command0"}
        m = MagicMock()
        m.start = 0
        m.end = 15
        m.match = "echo $( date )"
        expansions = [(5, 13, "substitution")]  # $( date )
        
        with patch('explainshell.web.views._substitutionmarkup', return_value='<a> date </a>'):
            views.formatmatch(d, m, expansions)
        
        # Should handle spaces in expansions
        self.assertIn("expansion-substitution", str(d["match"]))

    def test_formatmatch_non_substitution_expansion(self):
        """Test formatmatch with non-substitution expansion"""
        d = {"match": "", "commandclass": "command0"}
        m = MagicMock()
        m.start = 0
        m.end = 9  # Match the expansion end
        m.match = "echo $var"
        expansions = [(5, 9, "parameter")]  # $var
        
        views.formatmatch(d, m, expansions)
        
        self.assertIn("expansion-parameter", str(d["match"]))

    def test_formatmatch_expansion_at_end(self):
        """Test formatmatch with expansion at end of match"""
        d = {"match": "", "commandclass": "command0"}
        m = MagicMock()
        m.start = 0
        m.end = 9
        m.match = "echo $var"
        expansions = [(5, 9, "parameter")]  # $var at end
        
        views.formatmatch(d, m, expansions)
        
        # Should handle expansion at end correctly
        self.assertIn("expansion-parameter", str(d["match"]))

    def test_substitutionmarkup_simple(self):
        """Test _substitutionmarkup with simple command"""
        result = views._substitutionmarkup('ls')
        
        self.assertIn('href="/explain?cmd=ls"', result)
        self.assertIn('title="Zoom in to nested command"', result)
        self.assertIn('>ls</a>', result)

    def test_substitutionmarkup_complex(self):
        """Test _substitutionmarkup with complex command needing encoding"""
        result = views._substitutionmarkup('cat file | grep "test"')
        
        self.assertIn('href="/explain?', result)
        self.assertIn('cat+file', result)  # URL encoded
        self.assertIn('>cat file | grep "test"</a>', result)

    def test_explaincommand_spacing_calculation(self):
        """Test explaincommand spacing calculation between matches"""
        mock_store = MagicMock()
        mock_matcher = MagicMock()
        
        # Mock groups with matches that have gaps
        shell_group = MagicMock()
        shell_group.name = "shell"
        shell_group.results = []
        
        command_group = MagicMock()
        command_group.name = "command0"
        command_group.manpage = None
        command_group.results = [
            MagicMock(start=0, end=4, text="help1", match="echo"),
            MagicMock(start=6, end=11, text="help2", match="hello")  # 2 spaces gap
        ]
        
        mock_matcher.match.return_value = [shell_group, command_group]
        mock_matcher.expansions = []
        
        with patch('explainshell.matcher.matcher', return_value=mock_matcher):
            with patch('explainshell.web.views.formatmatch'):
                with patch('explainshell.web.helpers.suggestions'):
                    matches, helptext = views.explaincommand("echo  hello", mock_store)
        
        # Should calculate spacing correctly
        self.assertEqual(len(matches), 2)
        # Test that spacing calculation logic is executed
        self.assertIsInstance(matches, list)


if __name__ == '__main__':
    unittest.main()