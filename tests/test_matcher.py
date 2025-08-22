import unittest

from explainshell import matcher, errors
from . import helpers

s = helpers.mockstore()


class test_matcher(unittest.TestCase):
    """Simplified matcher tests focusing on core functionality"""

    def assertBasicMatch(self, command, expected_groups=2):
        """Helper to test basic command matching"""
        m = matcher.matcher(command, s)
        groups = m.match()
        self.assertEqual(len(groups), expected_groups)
        return groups

    def test_simple_command(self):
        """Test basic command matching"""
        groups = self.assertBasicMatch("bar")
        self.assertEqual(len(groups[1].results), 1)
        result = groups[1].results[0]
        self.assertEqual(result.start, 0)
        self.assertEqual(result.end, 3)
        self.assertEqual(result.match, "bar")

    def test_command_with_option(self):
        """Test command with simple option"""
        groups = self.assertBasicMatch("bar -a")
        self.assertEqual(len(groups[1].results), 2)

        # Check command
        cmd_result = groups[1].results[0]
        self.assertEqual(cmd_result.match, "bar")

        # Check option
        opt_result = groups[1].results[1]
        self.assertEqual(opt_result.match, "-a")

    def test_command_with_argument(self):
        """Test command with argument"""
        groups = self.assertBasicMatch("withargs file.txt")
        self.assertEqual(len(groups[1].results), 2)

        # Check command
        cmd_result = groups[1].results[0]
        self.assertEqual(cmd_result.match, "withargs")

        # Check argument
        arg_result = groups[1].results[1]
        self.assertEqual(arg_result.match, "file.txt")

    def test_unknown_command(self):
        """Test unknown command raises exception"""
        with self.assertRaises(errors.ProgramDoesNotExist):
            matcher.matcher("unknowncommand", s).match()

    def test_pipe_commands(self):
        """Test piped commands"""
        groups = self.assertBasicMatch("bar | baz", expected_groups=3)

        # Check shell group has pipe
        shell_results = groups[0].results
        self.assertTrue(any("|" in str(r.match) for r in shell_results))

        # Check both commands are present
        self.assertEqual(len(groups[1].results), 1)  # bar
        self.assertEqual(len(groups[2].results), 1)  # baz

    def test_redirect(self):
        """Test basic redirection"""
        groups = self.assertBasicMatch("bar > file.txt")

        # Should have shell group with redirect and command group
        shell_results = groups[0].results
        self.assertTrue(any(">" in str(r.match) for r in shell_results))

    def test_assignment(self):
        """Test variable assignment"""
        groups = self.assertBasicMatch("VAR=value bar")

        # Check assignment in shell group
        shell_results = groups[0].results
        self.assertTrue(
            any("VAR=value" in str(r.match) for r in shell_results)
        )

    def test_comment(self):
        """Test comment handling"""
        groups = self.assertBasicMatch("bar # comment")

        # Check comment in shell group
        shell_results = groups[0].results
        self.assertTrue(
            any("# comment" in str(r.match) for r in shell_results)
        )

    def test_semicolon_separator(self):
        """Test semicolon separated commands"""
        groups = self.assertBasicMatch("bar; baz", expected_groups=3)

        # Check semicolon in shell group
        shell_results = groups[0].results
        self.assertTrue(any(";" in str(r.match) for r in shell_results))

    def test_command_substitution_basic(self):
        """Test basic command substitution"""
        # Command substitution creates additional groups
        self.assertBasicMatch("bar $(echo test)", expected_groups=3)

        # Should have expansions
        m = matcher.matcher("bar $(echo test)", s)
        m.match()
        self.assertTrue(len(m.expansions) > 0)

    def test_function_definition(self):
        """Test function definition"""
        groups = self.assertBasicMatch("function test() { bar; }")

        # Should have shell results for function syntax
        shell_results = groups[0].results
        self.assertTrue(len(shell_results) > 0)

    def test_if_statement(self):
        """Test if statement"""
        groups = self.assertBasicMatch(
            "if bar; then baz; fi", expected_groups=3
        )

        # Check if keywords in shell group
        shell_results = groups[0].results
        shell_text = " ".join(str(r.match) for r in shell_results)
        self.assertIn("if", shell_text)

    def test_for_loop(self):
        """Test for loop"""
        groups = self.assertBasicMatch("for i in 1 2 3; do bar; done")

        # Check for keywords in shell group
        shell_results = groups[0].results
        shell_text = " ".join(str(r.match) for r in shell_results)
        self.assertIn("for", shell_text)

    def test_multiple_options(self):
        """Test command with multiple options"""
        groups = self.assertBasicMatch("bar -a -b arg")

        # Should have command and options
        self.assertTrue(len(groups[1].results) >= 3)

        # Check command is first
        self.assertEqual(groups[1].results[0].match, "bar")

    def test_long_option(self):
        """Test long option"""
        groups = self.assertBasicMatch("bar --help")

        # Check long option
        results = groups[1].results
        self.assertTrue(any("--help" in str(r.match) for r in results))


if __name__ == "__main__":
    unittest.main()
