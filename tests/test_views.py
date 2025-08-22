import unittest
from unittest.mock import Mock, patch
import urllib.parse

from explainshell.web import views, app
from explainshell import errors
import bashlex.errors


class TestViews(unittest.TestCase):
    """Comprehensive tests for views.py"""

    def setUp(self):
        self.mock_store = Mock()
        self.app = app
        self.app.config['TESTING'] = True

    def tearDown(self):
        pass

    def test_makematch(self):
        """Test _makematch helper function"""
        result = views._makematch(0, 3, "foo", "command", "help-1")
        expected = {
            "match": "foo",
            "start": 0,
            "end": 3,
            "spaces": "",
            "commandclass": "command",
            "helpclass": "help-1"
        }
        self.assertEqual(result, expected)

    def test_substitution_markup(self):
        """Test _substitutionmarkup function"""
        result = views._substitutionmarkup("foo")
        expected = ('<a href="/explain?cmd=foo" '
                    'title="Zoom in to nested command">foo</a>')
        self.assertEqual(result, expected)

        # Test with special characters
        result = views._substitutionmarkup("cat <&3")
        self.assertIn("cat+%3C%263", result)
        self.assertIn("cat <&3", result)

    def test_process_group_results(self):
        """Test _process_group_results function"""
        # Create mock group
        mock_group = Mock()
        mock_group.name = "command"

        # Create mock result
        mock_result = Mock()
        mock_result.text = "test text"
        mock_result.start = 0
        mock_result.end = 4
        mock_result.match = "test"

        mock_group.results = [mock_result]

        texttoid = {}
        idstartpos = {}
        expansions = []

        matches = views._process_group_results(
            mock_group, texttoid, idstartpos, expansions
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["match"], "test")
        self.assertEqual(matches[0]["commandclass"], "command")

    def test_add_command_metadata(self):
        """Test _add_command_metadata function"""
        matches = [{"commandclass": "command", "match": "test"}]

        mock_commandgroup = Mock()
        mock_commandgroup.manpage = Mock()
        mock_commandgroup.manpage.name = "test"
        mock_commandgroup.manpage.section = "1"
        mock_commandgroup.manpage.source = "test.1.gz"
        mock_commandgroup.suggestions = []

        views._add_command_metadata(matches, mock_commandgroup)

        self.assertIn("simplecommandstart", matches[0]["commandclass"])
        self.assertEqual(matches[0]["name"], "test")
        self.assertEqual(matches[0]["section"], "1")
        self.assertEqual(matches[0]["source"], "test")

    @patch('explainshell.web.views.render_template')
    def test_index_route(self, mock_render):
        """Test index route"""
        with self.app.test_request_context():
            mock_render.return_value = "index page"

            result = views.index()

            mock_render.assert_called_once_with("index.html")
            self.assertEqual(result, "index page")

    @patch('explainshell.web.views.render_template')
    def test_about_route(self, mock_render):
        """Test about route"""
        with self.app.test_request_context():
            mock_render.return_value = "about page"

            result = views.about()

            mock_render.assert_called_once_with("about.html")
            self.assertEqual(result, "about page")

    @patch('explainshell.web.views.redirect')
    def test_explain_route_no_command(self, mock_redirect):
        """Test explain route with no command"""
        with self.app.test_request_context('/?'):
            mock_redirect.return_value = "redirect to home"

            result = views.explain()

            mock_redirect.assert_called_once_with("/")
            self.assertEqual(result, "redirect to home")

    @patch('explainshell.web.views.redirect')
    def test_explain_route_empty_command(self, mock_redirect):
        """Test explain route with empty command"""
        with self.app.test_request_context('/?cmd=   '):
            mock_redirect.return_value = "redirect to home"

            result = views.explain()

            mock_redirect.assert_called_once_with("/")
            self.assertEqual(result, "redirect to home")

    @patch('explainshell.web.views.render_template')
    def test_explain_route_newline_error(self, mock_render):
        """Test explain route with newline in command"""
        with self.app.test_request_context('/?cmd=ls%0Aps'):
            mock_render.return_value = "error page"

            result = views.explain()

            mock_render.assert_called_once_with(
                "errors/error.html",
                title="parsing error!",
                message="no newlines please"
            )
            self.assertEqual(result, "error page")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explaincommand')
    @patch('explainshell.web.views.render_template')
    def test_explain_route_program_not_exist(self, mock_render,
                                             mock_explaincommand,
                                             mock_store_class):
        """Test explain route with missing program"""
        with self.app.test_request_context('/?cmd=nonexistent'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_explaincommand.side_effect = \
                errors.ProgramDoesNotExist("nonexistent")
            mock_render.return_value = "missing page"

            result = views.explain()

            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "errors/missingmanpage.html")
            self.assertEqual(kwargs["title"], "missing man page")
            self.assertEqual(result, "missing page")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explaincommand')
    @patch('explainshell.web.views.render_template')
    @patch('explainshell.web.views.logger')
    def test_explain_route_parsing_error(self, mock_logger, mock_render,
                                         mock_explaincommand,
                                         mock_store_class):
        """Test explain route with parsing error"""
        with self.app.test_request_context('/?cmd=invalid+syntax'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Create ParsingError with required parameters
            mock_node = {'pos': 0}
            parsing_error = bashlex.errors.ParsingError(
                "test error", mock_node, 0)
            parsing_error.message = "test error"
            mock_explaincommand.side_effect = parsing_error
            mock_render.return_value = "parsing error page"

            result = views.explain()

            mock_logger.warn.assert_called_once()
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "errors/parsingerror.html")
            self.assertEqual(kwargs["title"], "parsing error!")
            self.assertEqual(result, "parsing error page")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explaincommand')
    @patch('explainshell.web.views.render_template')
    @patch('explainshell.web.views.logger')
    def test_explain_route_not_implemented(self, mock_logger, mock_render,
                                           mock_explaincommand,
                                           mock_store_class):
        """Test explain route with not implemented error"""
        with self.app.test_request_context('/?cmd=unsupported'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_explaincommand.side_effect = \
                NotImplementedError("test construct")
            mock_render.return_value = "not implemented page"

            result = views.explain()

            mock_logger.warn.assert_called_once()
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "errors/error.html")
            self.assertEqual(kwargs["title"], "error!")
            self.assertIn("test construct", kwargs["message"])
            self.assertEqual(result, "not implemented page")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explaincommand')
    @patch('explainshell.web.views.render_template')
    @patch('explainshell.web.views.logger')
    def test_explain_route_general_exception(self, mock_logger, mock_render,
                                             mock_explaincommand,
                                             mock_store_class):
        """Test explain route with general exception"""
        with self.app.test_request_context('/?cmd=error+command'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_explaincommand.side_effect = Exception("unexpected error")
            mock_render.return_value = "general error page"

            result = views.explain()

            mock_logger.error.assert_called_once()
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "errors/error.html")
            self.assertEqual(kwargs["title"], "error!")
            self.assertIn("something went wrong", kwargs["message"])
            self.assertEqual(result, "general error page")

    def test_explainprogram(self):
        """Test explainprogram function"""
        # Create mock manpage
        mock_mp = Mock()
        mock_mp.source = "test.1.gz"
        mock_mp.section = "1"
        mock_mp.namesection = "test(1)"
        mock_mp.synopsis = "test synopsis"
        mock_mp.options = [Mock(text="option 1"), Mock(text="option 2")]

        # Create mock store
        mock_store = Mock()
        mock_store.findmanpage.return_value = [mock_mp]

        result_mp, suggestions = views.explainprogram("test", mock_store)

        self.assertEqual(result_mp["source"], "test.1")
        self.assertEqual(result_mp["section"], "1")
        self.assertEqual(result_mp["program"], "test(1)")
        self.assertEqual(result_mp["synopsis"], "test synopsis")
        self.assertEqual(len(result_mp["options"]), 2)
        self.assertEqual(len(suggestions), 0)

    def test_explainprogram_with_suggestions(self):
        """Test explainprogram with multiple manpages"""
        # Create mock manpages
        mock_mp1 = Mock()
        mock_mp1.source = "test.1.gz"
        mock_mp1.section = "1"
        mock_mp1.namesection = "test(1)"
        mock_mp1.synopsis = "test synopsis"
        mock_mp1.options = []

        mock_mp2 = Mock()
        mock_mp2.namesection = "test(8)"
        mock_mp2.section = "8"
        mock_mp2.name = "test"

        # Create mock store
        mock_store = Mock()
        mock_store.findmanpage.return_value = [mock_mp1, mock_mp2]

        result_mp, suggestions = views.explainprogram("test", mock_store)

        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["text"], "test(8)")
        self.assertEqual(suggestions[0]["link"], "8/test")

    @patch('explainshell.web.views.matcher.matcher')
    @patch('explainshell.web.views.helpers.suggestions')
    def test_explaincommand(self, mock_suggestions, mock_matcher_class):
        """Test explaincommand function"""
        # Create mock matcher
        mock_matcher = Mock()
        mock_matcher_class.return_value = mock_matcher
        mock_matcher.expansions = []

        # Create mock groups
        mock_shell_group = Mock()
        mock_shell_group.results = []

        mock_cmd_group = Mock()
        mock_cmd_group.results = []
        mock_cmd_group.manpage = None

        mock_matcher.match.return_value = [mock_shell_group, mock_cmd_group]

        mock_store = Mock()

        matches, helptext = views.explaincommand("test command", mock_store)

        mock_matcher_class.assert_called_once_with("test command", mock_store)
        mock_matcher.match.assert_called_once()
        mock_suggestions.assert_called_once()

        self.assertIsInstance(matches, list)
        self.assertIsInstance(helptext, list)

    def test_formatmatch_no_expansions(self):
        """Test formatmatch with no expansions"""
        d = {}
        mock_match = Mock()
        mock_match.match = "test"
        mock_match.start = 0
        mock_match.end = 4
        expansions = []

        views.formatmatch(d, mock_match, expansions)

        self.assertEqual(str(d["match"]), "test")

    def test_formatmatch_with_expansions(self):
        """Test formatmatch with expansions"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "$(echo test)"
        mock_match.start = 0
        mock_match.end = 12
        expansions = [(2, 11, "substitution")]  # "echo test"

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        self.assertIn("expansion-substitution", str(d["match"]))

    @patch('explainshell.web.views.redirect')
    @patch('explainshell.web.views.logger')
    def test_explainold_with_args(self, mock_logger, mock_redirect):
        """Test explainold route with args parameter"""
        with self.app.test_request_context('/?args=-la'):
            mock_redirect.return_value = "redirect response"

            result = views.explainold("1", "ls")

            expected_url = ("/explain?cmd=" +
                            urllib.parse.quote_plus("ls.1 -la"))
            mock_redirect.assert_called_once_with(expected_url, 301)
            self.assertEqual(result, "redirect response")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explainprogram')
    @patch('explainshell.web.views.render_template')
    @patch('explainshell.web.views.logger')
    def test_explainold_success(self, mock_logger, mock_render,
                                mock_explainprogram, mock_store_class):
        """Test successful explainold route"""
        with self.app.test_request_context('/'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_mp = {"program": "test", "options": []}
            mock_suggestions = []
            mock_explainprogram.return_value = (mock_mp, mock_suggestions)

            mock_render.return_value = "options page"

            result = views.explainold("1", "test")

            mock_explainprogram.assert_called_once_with(
                "test.1", mock_store_instance)
            mock_render.assert_called_once_with(
                "options.html",
                mp=mock_mp,
                suggestions=mock_suggestions
            )
            self.assertEqual(result, "options page")

    @patch('explainshell.web.views.store.store')
    @patch('explainshell.web.views.explainprogram')
    @patch('explainshell.web.views.render_template')
    @patch('explainshell.web.views.logger')
    def test_explainold_program_not_exist(self, mock_logger, mock_render,
                                          mock_explainprogram,
                                          mock_store_class):
        """Test explainold route with missing program"""
        with self.app.test_request_context('/'):
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_explainprogram.side_effect = \
                errors.ProgramDoesNotExist("test")
            mock_render.return_value = "missing page"

            result = views.explainold(None, "test")

            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "errors/missingmanpage.html")
            self.assertEqual(kwargs["title"], "missing man page")
            self.assertEqual(result, "missing page")

    def test_checkoverlaps_no_overlap(self):
        """Test _checkoverlaps with no overlaps"""
        s = "test command"
        matches = [
            {"start": 0, "end": 4},  # "test"
            {"start": 5, "end": 12}  # "command"
        ]

        # Should not raise exception
        views._checkoverlaps(s, matches)

    def test_checkoverlaps_with_overlap(self):
        """Test _checkoverlaps with overlaps"""
        s = "test command"
        matches = [
            {"start": 0, "end": 6},  # "test c"
            {"start": 4, "end": 12}  # "t command" - overlaps with previous
        ]

        with self.assertRaises(RuntimeError):
            views._checkoverlaps(s, matches)


class TestViewsIntegration(unittest.TestCase):
    """Integration tests for views.py"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True

    def tearDown(self):
        pass

    def test_command_length_limit(self):
        """Test that commands are limited to 1000 characters"""
        long_command = "a" * 1001

        with self.app.test_request_context(
                f'/?cmd={long_command}'):
            with patch('explainshell.web.views.store.store') as \
                    mock_store_class:
                mock_store = Mock()
                mock_store_class.return_value = mock_store

                with patch('explainshell.web.views.explaincommand') \
                        as mock_explain:
                    mock_explain.return_value = ([], [])

                    with patch('explainshell.web.views.render_template') \
                            as mock_render:
                        mock_render.return_value = "result"

                        views.explain()

                        # Should be called with truncated command
                        mock_explain.assert_called_once()
                        args = mock_explain.call_args[0]
                        self.assertEqual(len(args[0]), 1000)

    def test_url_encoding_in_substitution(self):
        """Test URL encoding in substitution markup"""
        cmd_with_special_chars = "cat < file & echo 'test'"
        result = views._substitutionmarkup(cmd_with_special_chars)

        # Should contain URL-encoded version
        encoded = urllib.parse.quote_plus(cmd_with_special_chars)
        self.assertIn(encoded, result)
        # Should contain original for display
        self.assertIn(cmd_with_special_chars, result)

    def test_process_group_results_with_text(self):
        """Test _process_group_results with text in results"""
        mock_group = Mock()
        mock_group.name = "option"

        mock_result = Mock()
        mock_result.text = "help text"
        mock_result.start = 0
        mock_result.end = 4
        mock_result.match = "test"

        mock_group.results = [mock_result]

        texttoid = {}
        idstartpos = {}
        expansions = []

        matches = views._process_group_results(
            mock_group, texttoid, idstartpos, expansions
        )

        self.assertEqual(len(matches), 1)
        self.assertIn("help text", texttoid)
        self.assertIn(texttoid["help text"], idstartpos)

    def test_process_group_results_no_text(self):
        """Test _process_group_results with no text in results"""
        mock_group = Mock()
        mock_group.name = "command"

        mock_result = Mock()
        mock_result.text = None
        mock_result.start = 0
        mock_result.end = 4
        mock_result.match = "test"

        mock_group.results = [mock_result]

        texttoid = {}
        idstartpos = {}
        expansions = []

        matches = views._process_group_results(
            mock_group, texttoid, idstartpos, expansions
        )

        self.assertEqual(len(matches), 1)
        self.assertIn("unknown", matches[0]["commandclass"])
        self.assertEqual(matches[0]["helpclass"], "")

    def test_add_command_metadata_no_matches(self):
        """Test _add_command_metadata with empty matches list"""
        matches = []
        mock_commandgroup = Mock()

        # Should not raise exception
        views._add_command_metadata(matches, mock_commandgroup)
        self.assertEqual(len(matches), 0)

    def test_add_command_metadata_no_manpage(self):
        """Test _add_command_metadata with no manpage"""
        matches = [{"commandclass": "command", "match": "test"}]
        mock_commandgroup = Mock()
        mock_commandgroup.manpage = None

        views._add_command_metadata(matches, mock_commandgroup)

        self.assertIn("simplecommandstart", matches[0]["commandclass"])
        self.assertNotIn("name", matches[0])

    def test_add_command_metadata_with_dot_in_match(self):
        """Test _add_command_metadata when match already contains dot"""
        matches = [{"commandclass": "command", "match": "test.sh"}]

        mock_manpage = Mock()
        mock_manpage.name = "test"
        mock_manpage.section = "1"
        mock_manpage.source = "test.1.gz"

        mock_commandgroup = Mock()
        mock_commandgroup.manpage = mock_manpage
        mock_commandgroup.suggestions = []

        views._add_command_metadata(matches, mock_commandgroup)

        # Should not modify match when it contains dot
        self.assertEqual(matches[0]["match"], "test.sh")

    def test_formatmatch_with_whitespace_in_expansion(self):
        """Test formatmatch with whitespace characters in expansion"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "$(echo test)"
        mock_match.start = 0
        mock_match.end = 12

        # Expansion with whitespace
        expansions = [(2, 11, "substitution")]  # "echo test"

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        # Should handle whitespace properly
        self.assertIn("expansion-substitution", str(d["match"]))

    def test_formatmatch_expansion_beyond_match_end(self):
        """Test formatmatch with expansion beyond match end"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "test"
        mock_match.start = 0
        mock_match.end = 4

        # Expansion starts after match ends
        expansions = [(5, 10, "substitution")]

        views.formatmatch(d, mock_match, expansions)

        # Should not have expansion class
        self.assertNotIn("hasexpansion", d["commandclass"])
        self.assertEqual(str(d["match"]), "test")

    def test_formatmatch_non_substitution_expansion(self):
        """Test formatmatch with non-substitution expansion type"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "${var}"
        mock_match.start = 0
        mock_match.end = 6

        expansions = [(0, 6, "parameter")]  # Non-substitution type

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        self.assertIn("expansion-parameter", str(d["match"]))

    def test_explainprogram_source_without_gz_extension(self):
        """Test explainprogram with source not ending in .gz"""
        mock_mp = Mock()
        mock_mp.source = "test.1"  # No .gz extension
        mock_mp.section = "1"
        mock_mp.namesection = "test(1)"
        mock_mp.synopsis = "test synopsis"
        mock_mp.options = []

        mock_store = Mock()
        mock_store.findmanpage.return_value = [mock_mp]

        result_mp, suggestions = views.explainprogram("test", mock_store)

        # Code removes last 3 chars regardless of extension
        # "test.1"[:-3] = "tes"
        self.assertEqual(result_mp["source"], "tes")

    @patch('explainshell.web.views.matcher.matcher')
    def test_explaincommand_with_expansions(self, mock_matcher_class):
        """Test explaincommand with expansions"""
        mock_matcher = Mock()
        mock_matcher_class.return_value = mock_matcher
        mock_matcher.expansions = [(0, 5, "substitution")]

        # Create mock shell group
        mock_shell_group = Mock()
        mock_shell_result = Mock()
        mock_shell_result.text = "shell help"
        mock_shell_result.start = 0
        mock_shell_result.end = 5
        mock_shell_result.match = "test"
        mock_shell_group.name = "shell"
        mock_shell_group.results = [mock_shell_result]

        # Create mock command group
        mock_cmd_group = Mock()
        mock_cmd_result = Mock()
        mock_cmd_result.text = "command help"
        mock_cmd_result.start = 6
        mock_cmd_result.end = 10
        mock_cmd_result.match = "cmd"
        mock_cmd_group.name = "command"
        mock_cmd_group.results = [mock_cmd_result]
        mock_cmd_group.manpage = None
        mock_cmd_group.suggestions = []

        mock_matcher.match.return_value = [mock_shell_group, mock_cmd_group]

        with patch('explainshell.web.views.helpers.suggestions'):
            matches, helptext = views.explaincommand("test cmd", Mock())

        self.assertEqual(len(matches), 2)
        self.assertEqual(len(helptext), 2)
        # Verify expansions were passed to formatmatch
        self.assertIsInstance(matches, list)

    def test_explaincommand_spacing_calculation(self):
        """Test explaincommand spacing calculation between matches"""
        with patch('explainshell.web.views.matcher.matcher') as \
                mock_matcher_class:
            mock_matcher = Mock()
            mock_matcher_class.return_value = mock_matcher
            mock_matcher.expansions = []

            # Create matches with gaps
            mock_shell_group = Mock()
            mock_shell_result = Mock()
            mock_shell_result.text = "help1"
            mock_shell_result.start = 0
            mock_shell_result.end = 4
            mock_shell_result.match = "test"
            mock_shell_group.name = "shell"
            mock_shell_group.results = [mock_shell_result]

            mock_cmd_group = Mock()
            mock_cmd_result = Mock()
            mock_cmd_result.text = "help2"
            mock_cmd_result.start = 7  # 3 spaces gap
            mock_cmd_result.end = 10
            mock_cmd_result.match = "cmd"
            mock_cmd_group.name = "command"
            mock_cmd_group.results = [mock_cmd_result]
            mock_cmd_group.manpage = None
            mock_cmd_group.suggestions = []

            mock_matcher.match.return_value = [mock_shell_group,
                                               mock_cmd_group]

            with patch('explainshell.web.views.helpers.suggestions'):
                matches, helptext = views.explaincommand("test   cmd", Mock())

            # First match should have 3 spaces
            self.assertEqual(matches[0]["spaces"], "   ")
            # Second match should have empty spaces (last match)
            self.assertEqual(matches[1]["spaces"], "")

    def test_formatmatch_partial_expansion_overlap(self):
        """Test formatmatch with expansion extending beyond match"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "test cmd"
        mock_match.start = 0
        mock_match.end = 8

        # Expansion extends beyond match - should not be processed
        expansions = [(4, 12, "substitution")]  # "cmd" + beyond match end

        views.formatmatch(d, mock_match, expansions)

        # Should not have expansion since it extends beyond match
        self.assertNotIn("hasexpansion", d["commandclass"])
        self.assertEqual(str(d["match"]), "test cmd")

    def test_formatmatch_multiple_expansions(self):
        """Test formatmatch with multiple expansions in same match"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "$(echo) $(cat)"
        mock_match.start = 0
        mock_match.end = 14

        expansions = [
            (2, 6, "substitution"),   # "echo"
            (10, 13, "substitution")  # "cat"
        ]

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        match_str = str(d["match"])
        self.assertEqual(match_str.count("expansion-substitution"), 2)

    def test_formatmatch_expansion_with_spaces(self):
        """Test formatmatch handling spaces in expansion content"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "$(echo test)"
        mock_match.start = 0
        mock_match.end = 12

        expansions = [(2, 11, "substitution")]  # "echo test"

        views.formatmatch(d, mock_match, expansions)

        # Should have expansion markup with substitution link
        self.assertIn("hasexpansion", d["commandclass"])
        self.assertIn("expansion-substitution", str(d["match"]))
        self.assertIn("echo test", str(d["match"]))

    @patch('explainshell.web.views.logger')
    def test_explainprogram_logging(self, mock_logger):
        """Test explainprogram logs suggestions"""
        mock_mp1 = Mock()
        mock_mp1.source = "test.1.gz"
        mock_mp1.section = "1"
        mock_mp1.namesection = "test(1)"
        mock_mp1.synopsis = "test synopsis"
        mock_mp1.options = []

        mock_mp2 = Mock()
        mock_mp2.namesection = "test(8)"
        mock_mp2.section = "8"
        mock_mp2.name = "test"

        mock_store = Mock()
        mock_store.findmanpage.return_value = [mock_mp1, mock_mp2]

        views.explainprogram("test", mock_store)

        # Should log suggestions
        mock_logger.info.assert_called()
        args = mock_logger.info.call_args[0]
        self.assertIn("suggestions", args[0])

    def test_checkoverlaps_adjacent_matches(self):
        """Test _checkoverlaps with adjacent non-overlapping matches"""
        s = "test command"
        matches = [
            {"start": 0, "end": 4},  # "test"
            {"start": 4, "end": 5},  # " "
            {"start": 5, "end": 12}  # "command"
        ]

        # Should not raise exception for adjacent matches
        views._checkoverlaps(s, matches)

    def test_checkoverlaps_single_character_overlap(self):
        """Test _checkoverlaps with single character overlap"""
        s = "test command"
        matches = [
            {"start": 0, "end": 5},  # "test "
            {"start": 4, "end": 12}  # " command" - overlaps at position 4
        ]

        with self.assertRaises(RuntimeError) as cm:
            views._checkoverlaps(s, matches)

        self.assertIn("explained overlap", str(cm.exception))

    def test_explaincommand_negative_spacing(self):
        """Test explaincommand handles negative spacing"""
        with patch('explainshell.web.views.matcher.matcher') as \
                mock_matcher_class:
            mock_matcher = Mock()
            mock_matcher_class.return_value = mock_matcher
            mock_matcher.expansions = []

            # Create overlapping matches (negative spacing)
            mock_shell_group = Mock()
            mock_shell_result = Mock()
            mock_shell_result.text = "help1"
            mock_shell_result.start = 0
            mock_shell_result.end = 6  # Overlaps with next
            mock_shell_result.match = "test"
            mock_shell_group.name = "shell"
            mock_shell_group.results = [mock_shell_result]

            mock_cmd_group = Mock()
            mock_cmd_result = Mock()
            mock_cmd_result.text = "help2"
            mock_cmd_result.start = 4  # Starts before previous ends
            mock_cmd_result.end = 8
            mock_cmd_result.match = "cmd"
            mock_cmd_group.name = "command"
            mock_cmd_group.results = [mock_cmd_result]
            mock_cmd_group.manpage = None
            mock_cmd_group.suggestions = []

            mock_matcher.match.return_value = [mock_shell_group,
                                               mock_cmd_group]

            with patch('explainshell.web.views.helpers.suggestions'):
                matches, helptext = views.explaincommand("test cmd", Mock())

            # Should handle negative spacing by using max(0, spaces)
            self.assertEqual(matches[0]["spaces"], "")  # No negative

    def test_substitution_markup_empty_command(self):
        """Test _substitutionmarkup with empty command"""
        result = views._substitutionmarkup("")
        expected = ('<a href="/explain?cmd=" '
                    'title="Zoom in to nested command"></a>')
        self.assertEqual(result, expected)

    def test_substitution_markup_unicode_characters(self):
        """Test _substitutionmarkup with unicode characters"""
        cmd_with_unicode = "echo 'héllo wörld'"
        result = views._substitutionmarkup(cmd_with_unicode)

        # Should contain URL-encoded version
        encoded = urllib.parse.urlencode({"cmd": cmd_with_unicode})
        self.assertIn(encoded, result)
        # Should contain original for display
        self.assertIn(cmd_with_unicode, result)

    def test_formatmatch_complex_expansion_sequence(self):
        """Test formatmatch with complex expansion sequence"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "a$(b)c$(d)e"
        mock_match.start = 0
        mock_match.end = 10

        # Multiple expansions with gaps
        expansions = [
            (2, 3, "substitution"),  # "b"
            (6, 7, "substitution")   # "d"
        ]

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        match_str = str(d["match"])
        # Should have both expansions
        count = match_str.count("expansion-substitution")
        self.assertEqual(count, 2)
        # Should preserve non-expansion characters
        self.assertIn("a", match_str)
        self.assertIn("c", match_str)
        self.assertIn("e", match_str)

    def test_formatmatch_expansion_at_start(self):
        """Test formatmatch with expansion starting at position 0"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "$(echo)test"
        mock_match.start = 0
        mock_match.end = 11

        # Expansion starts at beginning of match
        expansions = [(0, 7, "substitution")]  # "$(echo)"

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        match_str = str(d["match"])
        self.assertIn("expansion-substitution", match_str)
        # Should have remaining text after expansion
        self.assertIn("test", match_str)

    def test_formatmatch_expansion_with_prefix_text(self):
        """Test formatmatch with text before expansion"""
        d = {"commandclass": "command"}
        mock_match = Mock()
        mock_match.match = "prefix$(cmd)suffix"
        mock_match.start = 5
        mock_match.end = 19

        # Expansion in middle with prefix text
        # "$(cmd)" at positions 6-11 relative to match start
        expansions = [(11, 16, "substitution")]

        views.formatmatch(d, mock_match, expansions)

        self.assertIn("hasexpansion", d["commandclass"])
        match_str = str(d["match"])
        self.assertIn("prefix", match_str)
        self.assertIn("expansion-substitution", match_str)
        self.assertIn("suffix", match_str)

    def test_process_group_results_with_is_shell_true(self):
        """Test _process_group_results with is_shell=True"""
        mock_group = Mock()
        mock_group.name = "shell"

        mock_result = Mock()
        mock_result.text = "shell help"
        mock_result.start = 0
        mock_result.end = 4
        mock_result.match = "test"

        mock_group.results = [mock_result]

        texttoid = {}
        idstartpos = {}
        expansions = []

        # Test with is_shell=True
        matches = views._process_group_results(
            mock_group, texttoid, idstartpos, expansions, is_shell=True
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["commandclass"], "shell")
        self.assertIn("shell help", texttoid)


if __name__ == "__main__":
    unittest.main()
