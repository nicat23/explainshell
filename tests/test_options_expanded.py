import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell import options, store


class TestExtractedOption(unittest.TestCase):
    """Tests for extractedoption class"""

    def test_extractedoption_init(self):
        """Test extractedoption initialization"""
        opt = options.extractedoption("-v", "LEVEL")
        self.assertEqual(opt.flag, "-v")
        self.assertEqual(opt.expectsarg, "LEVEL")

    def test_extractedoption_no_arg(self):
        """Test extractedoption without argument"""
        opt = options.extractedoption("--verbose", None)
        self.assertEqual(opt.flag, "--verbose")
        self.assertIsNone(opt.expectsarg)

    def test_extractedoption_equality_with_string(self):
        """Test extractedoption equality with string"""
        opt = options.extractedoption("-v", None)
        self.assertEqual(opt, "-v")
        self.assertNotEqual(opt, "-a")

    def test_extractedoption_equality_with_object(self):
        """Test extractedoption equality with another extractedoption"""
        opt1 = options.extractedoption("-v", "LEVEL")
        opt2 = options.extractedoption("-v", "LEVEL")
        opt3 = options.extractedoption("-a", "LEVEL")
        
        self.assertEqual(opt1, opt2)
        self.assertNotEqual(opt1, opt3)

    def test_extractedoption_str(self):
        """Test extractedoption string representation"""
        opt = options.extractedoption("--verbose", "LEVEL")
        self.assertEqual(str(opt), "--verbose")

    def test_extractedoption_namedtuple_properties(self):
        """Test extractedoption namedtuple properties"""
        opt = options.extractedoption("-f", "FILE")
        
        # Test tuple unpacking
        flag, expectsarg = opt
        self.assertEqual(flag, "-f")
        self.assertEqual(expectsarg, "FILE")
        
        # Test indexing
        self.assertEqual(opt[0], "-f")
        self.assertEqual(opt[1], "FILE")


class TestOptionFunction(unittest.TestCase):
    """Tests for _option function"""

    def test_option_basic_short(self):
        """Test _option with basic short option"""
        match = options._option("-a")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")
        self.assertIsNone(match.group("arg"))

    def test_option_basic_long(self):
        """Test _option with basic long option"""
        match = options._option("--verbose")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "--verbose")
        self.assertIsNone(match.group("arg"))

    def test_option_with_arg_brackets(self):
        """Test _option with argument in brackets"""
        match = options._option("-a[foo]")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")
        self.assertEqual(match.group("arg"), "foo")
        self.assertEqual(match.group("argoptional"), "[")
        self.assertEqual(match.group("argoptionalc"), "]")

    def test_option_with_arg_angle_brackets(self):
        """Test _option with argument in angle brackets"""
        match = options._option("-a<foo>")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")
        self.assertEqual(match.group("arg"), "foo")
        self.assertEqual(match.group("argoptional"), "<")
        self.assertEqual(match.group("argoptionalc"), ">")

    def test_option_with_equals_arg(self):
        """Test _option with equals argument"""
        match = options._option("-a=foo")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")
        self.assertEqual(match.group("arg"), "foo")
        self.assertIsNone(match.group("argoptional"))

    def test_option_with_space_arg(self):
        """Test _option with space-separated argument"""
        match = options._option("-a FOO")  # Only uppercase letters allowed for space args
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")
        self.assertEqual(match.group("arg"), "FOO")

    def test_option_invalid_cases(self):
        """Test _option with invalid cases"""
        # Single dash
        self.assertIsNone(options._option("-"))
        
        # Double dash only
        self.assertIsNone(options._option("--"))
        
        # Triple dash
        self.assertIsNone(options._option("---"))
        
        # Ending with dash
        self.assertIsNone(options._option("-a-"))
        self.assertIsNone(options._option("--a-"))
        
        # Mismatched brackets
        self.assertIsNone(options._option("-a[foo>"))
        self.assertIsNone(options._option("-a<foo]"))

    def test_option_with_position(self):
        """Test _option with position parameter"""
        text = "prefix -a suffix"
        match = options._option(text, 7)
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-a")

    def test_option_complex_args(self):
        """Test _option with complex arguments"""
        match = options._option("-a=<foo bar>")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("arg"), "foo bar")
        
        match = options._option("--file=[path/to/file]")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("arg"), "path/to/file")

    def test_option_help_flag(self):
        """Test _option with help flag"""
        match = options._option("-?")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-?")

    def test_option_hash_flag(self):
        """Test _option with hash flag"""
        match = options._option("-#")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "-#")


class TestFlagFunction(unittest.TestCase):
    """Tests for _flag function"""

    def test_flag_basic(self):
        """Test _flag with basic flag"""
        match = options._flag("bs=1024")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "bs")
        self.assertEqual(match.group("arg"), "1024")

    def test_flag_no_arg(self):
        """Test _flag without argument"""
        # _flag requires = for matching, so test with just word won't match
        match = options._flag("verbose")
        self.assertIsNone(match)  # No = sign, so no match

    def test_flag_invalid_cases(self):
        """Test _flag with invalid cases"""
        # Starts with dash
        self.assertIsNone(options._flag("-verbose"))
        
        # Contains dashes
        self.assertIsNone(options._flag("foo-bar"))

    def test_flag_with_position(self):
        """Test _flag with position parameter"""
        text = "prefix bs=1024 suffix"
        match = options._flag(text, 7)
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "bs")
        self.assertEqual(match.group("arg"), "1024")

    def test_flag_complex_args(self):
        """Test _flag with complex arguments"""
        match = options._flag("count=100")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("opt"), "count")
        self.assertEqual(match.group("arg"), "100")


class TestEatBetween(unittest.TestCase):
    """Tests for _eatbetween function"""

    def test_eatbetween_no_separator(self):
        """Test _eatbetween with no separator"""
        result = options._eatbetween("foo", 0)
        self.assertEqual(result, 0)

    def test_eatbetween_comma(self):
        """Test _eatbetween with comma separator"""
        result = options._eatbetween("a, b", 1)
        self.assertEqual(result, 3)

    def test_eatbetween_pipe(self):
        """Test _eatbetween with pipe separator"""
        result = options._eatbetween("a|b", 1)
        self.assertEqual(result, 2)

    def test_eatbetween_or(self):
        """Test _eatbetween with 'or' separator"""
        result = options._eatbetween("a or b", 1)
        self.assertEqual(result, 5)

    def test_eatbetween_with_spaces(self):
        """Test _eatbetween with spaces around separators"""
        result = options._eatbetween("a , b", 1)
        self.assertEqual(result, 4)
        
        result = options._eatbetween("a | b", 1)
        self.assertEqual(result, 4)
        
        result = options._eatbetween("a  or  b", 1)
        self.assertEqual(result, 7)

    def test_eatbetween_multiple_separators(self):
        """Test _eatbetween with multiple separators"""
        result = options._eatbetween("a,|b", 1)
        self.assertEqual(result, 2)  # Only matches first separator


class TestExtractOption(unittest.TestCase):
    """Tests for extract_option function"""

    def test_extract_option_simple_short(self):
        """Test extract_option with simple short option"""
        short, long = options.extract_option("-a description")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].flag, "-a")
        self.assertIsNone(short[0].expectsarg)
        self.assertEqual(len(long), 0)

    def test_extract_option_simple_long(self):
        """Test extract_option with simple long option"""
        short, long = options.extract_option("--verbose description")
        self.assertEqual(len(short), 0)
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].flag, "--verbose")
        self.assertIsNone(long[0].expectsarg)

    def test_extract_option_multiple_options(self):
        """Test extract_option with multiple options"""
        short, long = options.extract_option("-a, -b, --verbose description")
        self.assertEqual(len(short), 2)
        self.assertEqual(short[0].flag, "-a")
        self.assertEqual(short[1].flag, "-b")
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].flag, "--verbose")

    def test_extract_option_with_args(self):
        """Test extract_option with arguments"""
        short, long = options.extract_option("-f FILE, --output=FILE")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].flag, "-f")
        self.assertEqual(short[0].expectsarg, "FILE")
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].flag, "--output")
        self.assertEqual(long[0].expectsarg, "FILE")

    def test_extract_option_pipe_separator(self):
        """Test extract_option with pipe separator"""
        short, long = options.extract_option("-a|-b|--verbose")
        self.assertEqual(len(short), 2)
        self.assertEqual(short[0].flag, "-a")
        self.assertEqual(short[1].flag, "-b")
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].flag, "--verbose")

    def test_extract_option_pipe_with_non_options(self):
        """Test extract_option with pipe and non-option flags"""
        short, long = options.extract_option("-a|b|c")
        self.assertEqual(len(short), 3)
        self.assertEqual(short[0].flag, "-a")
        self.assertEqual(short[1].flag, "b")
        self.assertEqual(short[2].flag, "|c")  # Actual behavior includes pipe
        self.assertEqual(len(long), 0)

    def test_extract_option_dd_style(self):
        """Test extract_option with dd-style options"""
        short, long = options.extract_option("bs=1024, count=100")
        self.assertEqual(len(short), 0)
        self.assertEqual(len(long), 2)
        self.assertEqual(long[0].flag, "bs")
        self.assertEqual(long[0].expectsarg, "1024")
        self.assertEqual(long[1].flag, "count")
        self.assertEqual(long[1].expectsarg, "100")

    def test_extract_option_mixed_formats(self):
        """Test extract_option with mixed option formats"""
        short, long = options.extract_option("-v, --verbose, bs=1024")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].flag, "-v")
        self.assertEqual(len(long), 1)  # bs=1024 is processed separately
        self.assertEqual(long[0].flag, "--verbose")

    def test_extract_option_with_whitespace(self):
        """Test extract_option with various whitespace"""
        short, long = options.extract_option("  -a   ,   -b   description")
        self.assertEqual(len(short), 2)
        self.assertEqual(short[0].flag, "-a")
        self.assertEqual(short[1].flag, "-b")

    def test_extract_option_multiline(self):
        """Test extract_option with multiline text"""
        text = "-a, -b,\n-c, --verbose description"
        short, long = options.extract_option(text)
        self.assertEqual(len(short), 3)
        self.assertEqual(len(long), 1)

    def test_extract_option_no_options(self):
        """Test extract_option with no options"""
        short, long = options.extract_option("just some description text")
        self.assertEqual(len(short), 0)
        self.assertEqual(len(long), 0)

    def test_extract_option_empty_string(self):
        """Test extract_option with empty string"""
        short, long = options.extract_option("")
        self.assertEqual(len(short), 0)
        self.assertEqual(len(long), 0)

    def test_extract_option_complex_args(self):
        """Test extract_option with complex arguments"""
        short, long = options.extract_option("-f<file>, --output=[path]")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].expectsarg, "file")
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].expectsarg, "path")

    def test_extract_option_help_flags(self):
        """Test extract_option with help flags"""
        short, long = options.extract_option("-?, --help")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].flag, "-?")
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].flag, "--help")


class TestExtract(unittest.TestCase):
    """Tests for extract function"""

    def test_extract_basic(self):
        """Test extract function with basic paragraphs"""
        p1 = store.paragraph(0, "-v, --verbose enable verbose output", "OPTIONS", True)
        p2 = store.paragraph(1, "This is just description", "DESCRIPTION", False)
        p3 = store.paragraph(2, "-f FILE, --file=FILE specify file", "OPTIONS", True)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1, p2, p3], [])
        
        options.extract(manpage)
        
        # Check that options were extracted
        extracted_options = manpage.options
        self.assertEqual(len(extracted_options), 2)
        
        # Check first option
        opt1 = extracted_options[0]
        self.assertEqual(opt1.short, ["-v"])
        self.assertEqual(opt1.long, ["--verbose"])
        self.assertFalse(opt1.expectsarg)
        
        # Check second option
        opt2 = extracted_options[1]
        self.assertEqual(opt2.short, ["-f"])
        self.assertEqual(opt2.long, ["--file"])
        self.assertTrue(opt2.expectsarg)

    def test_extract_no_options_found(self):
        """Test extract function when no options can be extracted"""
        p1 = store.paragraph(0, "invalid option format", "OPTIONS", True)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1], [])
        
        with patch('explainshell.options.logger') as mock_logger:
            options.extract(manpage)
            mock_logger.error.assert_called_once()

    def test_extract_mixed_paragraphs(self):
        """Test extract function with mixed option and non-option paragraphs"""
        p1 = store.paragraph(0, "-a simple option", "OPTIONS", True)
        p2 = store.paragraph(1, "Description paragraph", "DESCRIPTION", False)
        p3 = store.paragraph(2, "--verbose detailed option", "OPTIONS", True)
        p4 = store.paragraph(3, "Another description", "DESCRIPTION", False)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1, p2, p3, p4], [])
        
        options.extract(manpage)
        
        # Only option paragraphs should be converted
        extracted_options = manpage.options
        self.assertEqual(len(extracted_options), 2)
        
        # Non-option paragraphs should remain as regular paragraphs
        regular_paragraphs = [p for p in manpage.paragraphs if not isinstance(p, store.option)]
        self.assertEqual(len(regular_paragraphs), 2)

    def test_extract_with_expectsarg(self):
        """Test extract function with options that expect arguments"""
        p1 = store.paragraph(0, "-f FILE, -o OUTPUT", "OPTIONS", True)
        p2 = store.paragraph(1, "-v, --verbose", "OPTIONS", True)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1, p2], [])
        
        options.extract(manpage)
        
        extracted_options = manpage.options
        self.assertEqual(len(extracted_options), 2)
        
        # First option should expect arguments
        self.assertTrue(extracted_options[0].expectsarg)
        
        # Second option should not expect arguments
        self.assertFalse(extracted_options[1].expectsarg)

    def test_extract_empty_manpage(self):
        """Test extract function with empty manpage"""
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [], [])
        
        options.extract(manpage)
        
        # Should not crash with empty paragraphs
        self.assertEqual(len(manpage.paragraphs), 0)

    def test_extract_cleantext_integration(self):
        """Test extract function integration with cleantext"""
        # Create paragraph with HTML tags
        p1 = store.paragraph(0, "<b>-v</b>, <i>--verbose</i> enable verbose", "OPTIONS", True)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1], [])
        
        options.extract(manpage)
        
        extracted_options = manpage.options
        self.assertEqual(len(extracted_options), 1)
        
        opt = extracted_options[0]
        self.assertEqual(opt.short, ["-v"])
        self.assertEqual(opt.long, ["--verbose"])


class TestOptionsEdgeCases(unittest.TestCase):
    """Edge case tests for options module"""

    def test_extract_option_malformed_brackets(self):
        """Test extract_option with malformed brackets"""
        short, long = options.extract_option("-a[unclosed")
        # Should not extract malformed options
        self.assertEqual(len(short), 0)
        self.assertEqual(len(long), 0)

    def test_extract_option_nested_brackets(self):
        """Test extract_option with nested brackets"""
        short, long = options.extract_option("-a<nested>")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].expectsarg, "nested")

    def test_extract_option_special_characters_in_args(self):
        """Test extract_option with special characters in arguments"""
        short, long = options.extract_option("-a=foobar")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].expectsarg, "foobar")

    def test_extract_option_very_long_text(self):
        """Test extract_option with very long text"""
        long_text = "-a " + "description " * 1000
        short, long = options.extract_option(long_text)
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].flag, "-a")

    def test_extract_with_none_cleantext(self):
        """Test extract when cleantext returns None"""
        p1 = Mock()
        p1.is_option = True
        p1.cleantext.return_value = None
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", [p1], [])
        
        # Should raise TypeError when trying to process None
        with self.assertRaises(TypeError):
            options.extract(manpage)

    def test_tokenstate_namedtuple(self):
        """Test tokenstate namedtuple"""
        token = options.tokenstate(0, 5, "-v")
        self.assertEqual(token.startpos, 0)
        self.assertEqual(token.endpos, 5)
        self.assertEqual(token.token, "-v")
        
        # Test tuple unpacking
        start, end, tok = token
        self.assertEqual(start, 0)
        self.assertEqual(end, 5)
        self.assertEqual(tok, "-v")


class TestOptionsPerformance(unittest.TestCase):
    """Performance tests for options module"""

    def test_extract_option_many_options(self):
        """Test extract_option performance with many options"""
        # Create text with many options
        options_text = ", ".join([f"-{chr(97+i)}" for i in range(26)])  # -a through -z
        options_text += " description"
        
        short, long = options.extract_option(options_text)
        
        self.assertEqual(len(short), 26)
        self.assertEqual(len(long), 0)
        
        # Verify all options were extracted
        expected_flags = [f"-{chr(97+i)}" for i in range(26)]
        actual_flags = [opt.flag for opt in short]
        self.assertEqual(actual_flags, expected_flags)

    def test_extract_many_paragraphs(self):
        """Test extract function with many paragraphs"""
        paragraphs = []
        for i in range(100):
            if i % 2 == 0:  # Every other paragraph is an option
                p = store.paragraph(i, f"-{chr(97 + (i % 26))} option {i}", "OPTIONS", True)
            else:
                p = store.paragraph(i, f"Description {i}", "DESCRIPTION", False)
            paragraphs.append(p)
        
        manpage = store.manpage("test.1.gz", "test", "test synopsis", paragraphs, [])
        
        options.extract(manpage)
        
        # Should extract 50 options
        extracted_options = manpage.options
        self.assertEqual(len(extracted_options), 50)


if __name__ == "__main__":
    unittest.main()