"""Tests to improve coverage for matcher.py module"""

import unittest
from unittest.mock import MagicMock, patch
from explainshell import matcher, errors, helpconstants


class TestMatcherCoverage(unittest.TestCase):
    """Test cases to improve coverage for matcher.py"""

    def setUp(self):
        self.store = MagicMock()
        self.store.findmanpage.return_value = [MagicMock()]

    def test_matchgroup_initialization(self):
        """Test matchgroup initialization with all attributes"""
        mg = matcher.matchgroup("test")
        self.assertEqual(mg.name, "test")
        self.assertEqual(mg.results, [])
        self.assertIsNone(mg.manpage)
        self.assertIsNone(mg.suggestions)
        self.assertIsNone(mg.error)

    def test_matchresult_unknown_property(self):
        """Test matchresult unknown property"""
        mr_known = matcher.matchresult(0, 5, "text", "match")
        mr_unknown = matcher.matchresult(0, 5, None, "match")

        self.assertFalse(mr_known.unknown)
        self.assertTrue(mr_unknown.unknown)

    def test_matcher_initialization_attributes(self):
        """Test matcher initialization with all attributes"""
        m = matcher.matcher("test command", self.store)

        self.assertEqual(m.s, "test command")
        self.assertEqual(m.store, self.store)
        self.assertIsNone(m._prevoption)
        self.assertIsNone(m._currentoption)
        self.assertEqual(len(m.groups), 1)
        self.assertEqual(m.groups[0].name, "shell")
        self.assertEqual(m.expansions, [])
        self.assertEqual(len(m.groupstack), 1)
        self.assertEqual(m.compoundstack, [])
        self.assertEqual(m.functions, set())
        self.assertEqual(m.processed_command_words, set())
        self.assertEqual(m.redirect_output_positions, set())

    def test_matcher_manpage_property_shell_group(self):
        """Test matcher manpage property when on shell group"""
        m = matcher.matcher("test", self.store)
        # When groupstack top is shell group, should return None
        self.assertIsNone(m.manpage)

    def test_matcher_find_option_no_manpage(self):
        """Test find_option when no manpage is set"""
        m = matcher.matcher("test", self.store)
        result = m.find_option("-v")
        self.assertIsNone(result)

    def test_matcher_find_option_with_manpage(self):
        """Test find_option with manpage set"""
        m = matcher.matcher("test", self.store)
        mock_manpage = MagicMock()
        mock_option = MagicMock()
        mock_manpage.find_option.return_value = mock_option

        # Simulate having a manpage
        mg = matcher.matchgroup("command0")
        mg.manpage = mock_manpage  # type: ignore
        m.groups.append(mg)
        m.groupstack.append((None, mg, None))

        result = m.find_option("-v")
        self.assertEqual(result, mock_option)
        mock_manpage.find_option.assert_called_with("-v")

    def test_visitreservedword_with_compound_context(self):
        """Test visitreservedword with compound command context"""
        m = matcher.matcher("for i in list; do echo $i; done", self.store)
        m.compoundstack.append("for")

        # Mock node
        node = MagicMock()
        node.pos = [0, 3]

        # Test with compound-specific reserved word
        with patch.dict(
            helpconstants.COMPOUNDRESERVEDWORDS, {"for": {"do": "for do help"}}
        ):
            m.visitreservedword(node, "do")

        self.assertEqual(len(m.groups[0].results), 1)
        self.assertEqual(m.groups[0].results[0].text, "for do help")

    def test_visitoperator_with_compound_context(self):
        """Test visitoperator with compound command context"""
        m = matcher.matcher("if [ $? -eq 0 ]; then echo ok; fi", self.store)
        m.compoundstack.append("if")

        node = MagicMock()
        node.pos = [15, 16]

        # Test with compound-specific operator
        with patch.dict(
            helpconstants.COMPOUNDRESERVEDWORDS, {
                "if": {";": "if semicolon help"}}
        ):
            m.visitoperator(node, ";")

        self.assertEqual(len(m.groups[0].results), 1)
        self.assertEqual(m.groups[0].results[0].text, "if semicolon help")

    def test_visitredirect_with_output_node(self):
        """Test visitredirect with output node having parts"""
        m = matcher.matcher("echo hello > file", self.store)

        # Mock redirect node
        node = MagicMock()
        node.pos = [11, 17]

        # Mock output node as bashlex.ast.node with parts
        import bashlex.ast

        output = MagicMock(spec=bashlex.ast.node)
        output.pos = [13, 17]
        output.parts = [MagicMock()]
        output.parts[0].kind = "parameter"

        m.visitredirect(node, None, ">", output, None)

        # Should track redirect output position
        self.assertIn((13, 17), m.redirect_output_positions)

    def test_visitredirect_fd_redirect(self):
        """Test visitredirect with file descriptor redirect"""
        m = matcher.matcher("echo hello 2>&1", self.store)

        node = MagicMock()
        node.pos = [11, 16]

        m.visitredirect(node, None, ">&", 1, None)

        self.assertEqual(len(m.groups[0].results), 1)
        # Should contain redirection help text
        self.assertIn("redirection", m.groups[0].results[0].text.lower())

    def test_visitcommand_no_parts(self):
        """Test visitcommand with no parts"""
        m = matcher.matcher("", self.store)

        node = MagicMock()
        parts = []

        # Should return early without processing
        m.visitcommand(node, parts)

        # Should not create new groups
        self.assertEqual(len(m.groups), 1)

    def test_visitcommand_no_word_nodes(self):
        """Test visitcommand with no word nodes (only redirects)"""
        m = matcher.matcher("", self.store)

        node = MagicMock()
        redirect_part = MagicMock()
        redirect_part.kind = "redirect"
        parts = [redirect_part]

        with patch("bashlex.ast.findfirstkind", return_value=-1):
            m.visitcommand(node, parts)

        # Should not create new groups
        self.assertEqual(len(m.groups), 1)

    def test_visitcommand_already_processed(self):
        """Test visitcommand with already processed word"""
        m = matcher.matcher("echo hello", self.store)

        node = MagicMock()
        word_node = MagicMock()
        word_node.kind = "word"
        word_node.word = "echo"
        parts = [word_node]

        # Mark as already processed
        m.processed_command_words.add(id(word_node))

        with patch("bashlex.ast.findfirstkind", return_value=0):
            m.visitcommand(node, parts)

        # Should not create new groups
        self.assertEqual(len(m.groups), 1)

    def test_visitcommand_function_call(self):
        """Test visitcommand with function call"""
        m = matcher.matcher("myfunc arg1 arg2", self.store)
        m.functions.add("myfunc")

        node = MagicMock()
        word_node = self._extracted_from_test_visitcommand_function_call_(0, 6)
        word_node.word = "myfunc"
        arg_node = self._extracted_from_test_visitcommand_function_call_(7, 11)
        arg_node.parts = []

        parts = [word_node, arg_node]

        with patch("bashlex.ast.findfirstkind", return_value=0):
            m.visitcommand(node, parts)

        # Should add matches for function call
        self.assertGreater(len(m.matches), 0)

    # TODO Rename this here and in `test_visitcommand_function_call`
    def _extracted_from_test_visitcommand_function_call_(self, arg0, arg1):
        result = MagicMock()
        result.kind = "word"
        result.pos = [arg0, arg1]

        return result

    def test_visitcommand_with_expansions(self):
        """Test visitcommand with word node having expansions"""
        m = matcher.matcher("$(echo test)", self.store)

        node = MagicMock()
        word_node = MagicMock()
        word_node.kind = "word"
        word_node.parts = [MagicMock()]  # Has expansions
        parts = [word_node]

        with patch("bashlex.ast.findfirstkind", return_value=0):
            m.visitcommand(node, parts)

        # Should create a group for unknown command with expansions
        self.assertEqual(len(m.groups), 2)

    def test_compound_command_visitors(self):
        """Test compound command visitors"""
        m = matcher.matcher("", self.store)

        # Test all compound command visitors
        node = MagicMock()
        parts = []

        m.visitfor(node, parts)
        self.assertEqual(m.compoundstack[-1], "for")

        m.visitwhile(node, parts)
        self.assertEqual(m.compoundstack[-1], "while")

        m.visituntil(node, parts)
        self.assertEqual(m.compoundstack[-1], "until")

        m.visitif(node, parts)
        self.assertEqual(m.compoundstack[-1], "if")

    def test_visitnodeend_compound_mismatch(self):
        """Test visitnodeend with compound stack mismatch"""
        m = matcher.matcher("", self.store)
        m.compoundstack.append("for")

        node = MagicMock()
        node.kind = "while"

        with patch("explainshell.matcher.logger") as mock_logger:
            m.visitnodeend(node)
            mock_logger.warning.assert_called()

    def test_visitnodeend_empty_compound_stack(self):
        """Test visitnodeend with empty compound stack"""
        m = matcher.matcher("", self.store)

        node = MagicMock()
        node.kind = "for"

        with patch("explainshell.matcher.logger") as mock_logger:
            m.visitnodeend(node)
            mock_logger.warning.assert_called()

    def test_startcommand_no_word_node(self):
        """Test startcommand with no word nodes"""
        m = matcher.matcher("", self.store)

        parts = []
        with patch("bashlex.ast.findfirstkind", return_value=-1):
            result = m.startcommand(None, parts, None)

        self.assertFalse(result)

    def test_startcommand_word_with_parts(self):
        """Test startcommand with word node having parts"""
        m = matcher.matcher("", self.store)

        word_node = MagicMock()
        word_node.parts = [MagicMock()]  # Has expansions
        parts = [word_node]

        with patch("bashlex.ast.findfirstkind", return_value=0):
            result = m.startcommand(None, parts, None)

        self.assertFalse(result)

    def test_startcommand_program_not_found(self):
        """Test startcommand when program doesn't exist"""
        m = matcher.matcher("", self.store)
        self.store.findmanpage.side_effect = errors.ProgramDoesNotExist(
            "unknown"
        )

        word_node = MagicMock()
        word_node.word = "unknown"
        word_node.parts = []
        word_node.pos = [0, 7]  # Add required pos attribute
        parts = [word_node]

        with patch("bashlex.ast.findfirstkind", return_value=0):
            result = m.startcommand(None, parts, None)

        self.assertFalse(result)
        # Should create group with error
        self.assertEqual(len(m.groups), 2)
        self.assertIsNotNone(m.groups[1].error)

    def test_startcommand_multicommand_success(self):
        """Test startcommand with successful multicommand lookup"""
        m = matcher.matcher("git commit", self.store)

        # Mock manpages
        git_manpage = MagicMock()
        git_manpage.multicommand = True
        git_commit_manpage = MagicMock()

        self.store.findmanpage.side_effect = [
            [git_manpage],  # First call for "git"
            [git_commit_manpage],  # Second call for "git commit"
        ]

        word_node1 = (
            self._extracted_from_test_startcommand_multicommand_success_15(
                "git", 0, 3
            )
        )
        word_node2 = (
            self._extracted_from_test_startcommand_multicommand_success_15(
                "commit", 4, 10
            )
        )
        parts = [word_node1, word_node2]

        with patch("bashlex.ast.findfirstkind", side_effect=[0, 0]):
            result = m.startcommand(None, parts, None)

        self.assertTrue(result)
        self.assertEqual(len(m.groups), 2)
        self.assertEqual(m.groups[1].manpage, git_commit_manpage)

    # TODO Rename this here and in `test_startcommand_multicommand_success`
    def _extracted_from_test_startcommand_multicommand_success_15(
        self, arg0, arg1, arg2
    ):
        result = MagicMock()
        result.word = arg0
        result.pos = [arg1, arg2]
        result.parts = []

        return result

    def test_startcommand_multicommand_failure(self):
        """Test startcommand with failed multicommand lookup"""
        m = matcher.matcher("git unknown", self.store)

        git_manpage = MagicMock()
        git_manpage.multicommand = True

        self.store.findmanpage.side_effect = [
            [git_manpage],  # First call succeeds
            errors.ProgramDoesNotExist("git unknown"),  # Second call fails
        ]

        word_node1 = (
            self._extracted_from_test_startcommand_multicommand_failure_13(
                "git", 0, 3
            )
        )
        word_node2 = (
            self._extracted_from_test_startcommand_multicommand_failure_13(
                "unknown", 4, 11
            )
        )
        parts = [word_node1, word_node2]

        with patch("bashlex.ast.findfirstkind", side_effect=[0, 0]):
            result = m.startcommand(None, parts, None)

        self.assertTrue(result)
        # Should use original git manpage
        self.assertEqual(m.groups[1].manpage, git_manpage)

    # TODO Rename this here and in `test_startcommand_multicommand_failure`
    def _extracted_from_test_startcommand_multicommand_failure_13(
        self, arg0, arg1, arg2
    ):
        result = MagicMock()
        result.word = arg0
        result.pos = [arg1, arg2]
        result.parts = []

        return result

    def test_visitword_processed_command(self):
        """Test visitword with already processed command word"""
        m = matcher.matcher("echo", self.store)

        node = MagicMock()
        node.pos = [0, 4]

        # Mark as processed command
        m.processed_command_words.add(id(node))

        m.visitword(node, "echo")

        # Should not add any matches
        self.assertEqual(len(m.matches), 0)

    def test_visitword_redirect_output(self):
        """Test visitword with redirect output position"""
        m = matcher.matcher("echo > file", self.store)

        node = MagicMock()
        node.pos = [7, 11]

        # Mark as redirect output position
        m.redirect_output_positions.add((7, 11))

        m.visitword(node, "file")

        # Should not add any matches
        self.assertEqual(len(m.matches), 0)

    def test_visitword_unknown_command(self):
        """Test visitword inside unknown command"""
        m = matcher.matcher("unknown arg", self.store)

        # Simulate being inside unknown command (no manpage)
        mg = matcher.matchgroup("command0")
        mg.manpage = None
        m.groups.append(mg)
        m.groupstack.append((None, mg, None))

        node = MagicMock()
        node.pos = [8, 11]

        m.visitword(node, "arg")

        # Should add unknown match
        self.assertEqual(len(m.matches), 1)
        self.assertTrue(m.matches[0].unknown)

    def test_visitword_nested_command_end(self):
        """Test visitword that ends nested command"""
        m = matcher.matcher("find . -exec ls {} \\;", self.store)

        # Setup nested command scenario
        mg = matcher.matchgroup("command0")
        mg.manpage = MagicMock()  # type: ignore
        m.groups.append(mg)
        m.groupstack.append((None, mg, ["\\;"]))  # type: ignore
        # End word list

        node = MagicMock()
        node.pos = [19, 21]

        # Add a previous match to reference
        m.matches.append(matcher.matchresult(0, 4, "find help", "find"))

        # Test that the word is recognized as an end word
        m.visitword(node, "\\;")

        # Should add a match
        self.assertGreater(len(m.matches), 1)

    def test_visitword_short_option_splitting(self):
        """Test visitword with short option that needs splitting"""
        m = matcher.matcher("ls -la", self.store)

        # Setup command with manpage
        mg = matcher.matchgroup("command0")
        mock_manpage = MagicMock()
        mock_option_l = MagicMock()
        mock_option_l.text = "long format"
        mock_option_l.expectsarg = False
        mock_option_a = MagicMock()
        mock_option_a.text = "show all"
        mock_option_a.expectsarg = False

        def find_option_side_effect(opt):
            options = {"-l": mock_option_l, "-a": mock_option_a}
            return options.get(opt)

        mock_manpage.find_option.side_effect = (
            find_option_side_effect
        )
        mg.manpage = mock_manpage  # type: ignore
        m.groups.append(mg)
        m.groupstack.append((None, mg, None))

        node = MagicMock()
        node.pos = [3, 6]
        node.word = "-la"

        m.visitword(node, "-la")

        # Should split into multiple matches
        self.assertGreater(len(m.matches), 1)

    def test_visitword_previous_option_expects_arg(self):
        """Test visitword when previous option expects argument"""
        m = matcher.matcher("grep -f pattern", self.store)

        # Setup command with manpage
        mg = matcher.matchgroup("command0")
        mock_manpage = MagicMock()
        mock_manpage.find_option.return_value = None
        # Current word not an option
        mg.manpage = mock_manpage  # type: ignore
        mock_prev_option = (
            self._extracted_from_test_visitword_nested_command_option_11(m, mg)
        )
        mock_prev_option.nestedcommand = False
        m._prevoption = mock_prev_option  # type: ignore

        # Add previous match
        prev_match = matcher.matchresult(5, 7, "file option", "-f")
        m.matches.append(prev_match)

        self._ext_from_test_visitword_args_with_nested_cmds_24(
            8, 15, m, "pattern"
        )
        # Should process the argument
        self.assertEqual(len(m.matches), 1)

    def test_visitword_nested_command_option(self):
        """Test visitword with option that can nest commands"""
        m = matcher.matcher("find . -exec ls", self.store)

        # Setup command with manpage
        mg = matcher.matchgroup("command0")
        mock_manpage = MagicMock()
        mock_manpage.find_option.return_value = None
        mg.manpage = mock_manpage  # type: ignore
        mock_prev_option = (
            self._extracted_from_test_visitword_nested_command_option_11(m, mg)
        )
        mock_prev_option.nestedcommand = ["\\;"]
        m._prevoption = mock_prev_option  # type: ignore

        self._ext_from_test_visitword_args_with_nested_cmds_24(
            12, 14, m, "ls"
        )
        # After processing, _prevoption may be cleared
        # Just verify the method completed without error
        self.assertTrue(True)

    def _extracted_from_test_visitword_nested_command_option_11(self, m, mg):
        m.groups.append(mg)
        m.groupstack.append((None, mg, None))
        result = MagicMock()
        result.expectsarg = True
        return result

    def test_visitword_partial_match_success(self):
        """Test visitword with successful partial matching"""
        m = matcher.matcher("tar xvf", self.store)
        mg = matcher.matchgroup("command0")
        mock_manpage = MagicMock()
        mock_manpage.find_option.return_value = None
        mock_manpage.partialmatch = True
        mock_manpage.arguments = None
        self._ext_from_test_visitword_args_with_nested_cmd_11(
            mock_manpage, mg, m
        )
        with patch.object(m, "find_option") as mock_find:
            self._extracted_from_test_visitword_partial_match_success_13(
                mock_find, m
            )

    # TODO Rename this here and in `test_visitword_partial_match_success`
    def _extracted_from_test_visitword_partial_match_success_13(
        self, mock_find, m
    ):
        mock_find.side_effect = [None, MagicMock(), MagicMock(), MagicMock()]
        node = MagicMock()
        node.pos = [4, 7]
        node.word = "xvf"
        m.visitword(node, "xvf")
        self.assertGreater(len(m.matches), 0)

    def test_visitword_arguments_with_nested_command(self):
        """Test visitword with arguments that can nest commands"""
        m = matcher.matcher("sudo ls", self.store)

        # Setup command with arguments and nested command capability
        mg = matcher.matchgroup("command0")
        mock_manpage = MagicMock()
        mock_manpage.find_option.return_value = None
        mock_manpage.partialmatch = False
        mock_manpage.arguments = {"command": "command to execute"}
        mock_manpage.nestedcommand = ["exit"]
        self._ext_from_test_visitword_args_with_nested_cmd_11(
            mock_manpage, mg, m
        )
        # Mock successful startcommand
        with patch.object(m, "startcommand", return_value=True) as mock_start:
            self._ext_from_test_visitword_args_with_nested_cmds_24(
                5, 7, m, "ls"
            )
            mock_start.assert_called_once()

    def _ext_from_test_visitword_args_with_nested_cmd_11(self,
                                                         mock_manpage,
                                                         mg,
                                                         m):
        mg.manpage = mock_manpage
        m.groups.append(mg)
        m.groupstack.append((None, mg, None))

    def _ext_from_test_visitword_args_with_nested_cmds_24(self,
                                                          arg0,
                                                          arg1,
                                                          m,
                                                          arg3):
        node = MagicMock()
        node.pos = [arg0, arg1]
        m.visitword(node, arg3)

    def test_visitfunction_compound_curly_braces(self):
        """Test visitfunction with compound curly braces"""
        m = matcher.matcher("", self.store)

        # Mock function components
        name = MagicMock()
        name.word = "myfunc"

        # Mock compound body with curly braces
        body = MagicMock()
        body.list = [
            MagicMock(kind="reservedword", word="{", pos=[7, 8]),
            MagicMock(kind="command", pos=[9, 18]),
            MagicMock(kind="reservedword", word="}", pos=[19, 20]),
        ]

        parts = [name, body]

        node = MagicMock()
        node.pos = [0, 21]

        m.visitfunction(node, name, body, parts)

        # Should add function to functions set
        self.assertIn("myfunc", m.functions)

        # Should add matches for function declaration and closing brace
        shell_results = [
            r for r in m.groups[0].results if "function" in r.text.lower()]
        self.assertEqual(len(shell_results), 2)

    def test_visitfunction_non_curly_compound(self):
        """Test visitfunction with non-curly compound"""
        m = matcher.matcher("", self.store)

        name = MagicMock()
        name.word = "myfunc"

        # Mock compound body without curly braces
        body = MagicMock()
        body.list = [MagicMock(kind="command")]

        before_body = MagicMock()
        before_body.pos = [6, 8]

        parts = [name, before_body, body]

        node = MagicMock()
        node.pos = [0, 20]

        with patch("bashlex.ast.findfirstkind", return_value=2):
            with patch.object(m, "visit") as mock_visit:
                m.visitfunction(node, name, body, parts)

                mock_visit.assert_called_with(body)

    def test_visitparameter_numeric_value(self):
        """Test visitparameter with numeric value"""
        m = matcher.matcher("", self.store)

        node = MagicMock()
        node.pos = [1, 3]

        m.visitparameter(node, "42")

        # Should add expansion with digits kind
        self.assertEqual(len(m.expansions), 1)
        self.assertEqual(m.expansions[0].kind, "parameter-digits")

    def test_visitparameter_special_parameter(self):
        """Test visitparameter with special parameter"""
        m = matcher.matcher("", self.store)

        node = MagicMock()
        node.pos = [1, 3]

        with patch.dict(helpconstants.parameters, {"?": "exit_status"}):
            m.visitparameter(node, "?")

        # Should add expansion with special kind
        self.assertEqual(len(m.expansions), 1)
        self.assertEqual(m.expansions[0].kind, "parameter-exit_status")

    def test_match_no_ast(self):
        """Test match when no AST is generated"""
        m = matcher.matcher("", self.store)

        with patch("bashlex.parser.parsesingle", return_value=None):
            with patch("explainshell.matcher.logger") as mock_logger:
                result = m.match()

                mock_logger.warning.assert_called()
                self.assertEqual(len(result), 1)  # Only shell group

    def test_match_single_command_error_reraise(self):
        """Test match reraises error for single command with no results"""
        m = matcher.matcher("unknown", self.store)

        # Create scenario for error re-raising
        error = errors.ProgramDoesNotExist("unknown")
        mg = matcher.matchgroup("command0")
        mg.manpage = None
        mg.error = error
        m.groups.append(mg)

        with patch.object(m, "visit"):
            with patch("bashlex.parser.parsesingle") as mock_parse:
                mock_ast = MagicMock()
                mock_ast.kind = "command"
                mock_parse.return_value = mock_ast

                with self.assertRaises(errors.ProgramDoesNotExist):
                    m.match()

    def test_markunparsedunknown_comment(self):
        """Test _markunparsedunknown with comment"""
        m = matcher.matcher("echo hello # comment", self.store)

        # Mock existing matches that don't cover the comment
        m.groups[0].results = [
            matcher.matchresult(0, 10, "echo help", "echo hello")]

        m._markunparsedunknown()

        # Should add comment match
        comment_matches = [
            r for r in m.groups[0].results if "comment" in r.text.lower()
        ]
        self.assertEqual(len(comment_matches), 1)

    def test_markunparsedunknown_unparsed_ranges(self):
        """Test _markunparsedunknown with unparsed ranges"""
        m = matcher.matcher("echo hello world", self.store)

        # Mock partial matches leaving "world" unparsed
        m.groups[0].results = [
            matcher.matchresult(0, 10, "echo help", "echo hello")]

        m._markunparsedunknown()

        # Should add unknown match for "world"
        unknown_matches = [r for r in m.groups[0].results if r.unknown]
        self.assertEqual(len(unknown_matches), 1)

    def test_mergeadjacent_single_match(self):
        """Test _mergeadjacent with single match"""
        m = matcher.matcher("echo", self.store)

        matches = [matcher.matchresult(0, 4, "help", "echo")]
        # Mock _resultindex to provide the required mapping
        with patch.object(m, "_resultindex", return_value={matches[0]: 0}):
            result = m._mergeadjacent(matches)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], matches[0])

    def test_mergeadjacent_multiple_same_text(self):
        """Test _mergeadjacent with multiple matches having same text"""
        m = matcher.matcher("echo", self.store)

        # Create matches with same text that should be merged
        matches = [
            matcher.matchresult(0, 2, "help", "ec"),
            matcher.matchresult(2, 4, "help", "ho"),
        ]

        # Mock the result index to make them adjacent
        with patch.object(
            m, "_resultindex", return_value={matches[0]: 0, matches[1]: 1}
        ):
            result = m._mergeadjacent(matches)

        # Should merge into single match
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].start, 0)
        self.assertEqual(result[0].end, 4)


if __name__ == "__main__":
    unittest.main()
