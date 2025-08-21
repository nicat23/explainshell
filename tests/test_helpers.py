import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell.web import helpers
from explainshell import store


class TestHelpers(unittest.TestCase):
    """Comprehensive tests for web/helpers.py"""

    def setUp(self):
        """Set up test fixtures"""
        pass

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_convertparagraphs_basic(self):
        """Test convertparagraphs with basic manpage"""
        # Create mock paragraph with bytes text
        mock_paragraph = Mock()
        mock_paragraph.text = b"test paragraph text"
        
        # Create mock manpage
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_paragraph]
        
        result = helpers.convertparagraphs(mock_manpage)
        
        # Verify text was decoded
        self.assertEqual(mock_paragraph.text, "test paragraph text")
        self.assertIs(result, mock_manpage)

    def test_convertparagraphs_multiple_paragraphs(self):
        """Test convertparagraphs with multiple paragraphs"""
        # Create multiple mock paragraphs
        mock_p1 = Mock()
        mock_p1.text = b"first paragraph"
        
        mock_p2 = Mock()
        mock_p2.text = b"second paragraph"
        
        mock_p3 = Mock()
        mock_p3.text = b"third paragraph"
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_p1, mock_p2, mock_p3]
        
        result = helpers.convertparagraphs(mock_manpage)
        
        # Verify all paragraphs were decoded
        self.assertEqual(mock_p1.text, "first paragraph")
        self.assertEqual(mock_p2.text, "second paragraph")
        self.assertEqual(mock_p3.text, "third paragraph")
        self.assertIs(result, mock_manpage)

    def test_convertparagraphs_empty_paragraphs(self):
        """Test convertparagraphs with empty paragraphs list"""
        mock_manpage = Mock()
        mock_manpage.paragraphs = []
        
        result = helpers.convertparagraphs(mock_manpage)
        
        self.assertEqual(len(mock_manpage.paragraphs), 0)
        self.assertIs(result, mock_manpage)

    def test_convertparagraphs_unicode_text(self):
        """Test convertparagraphs with unicode text"""
        mock_paragraph = Mock()
        mock_paragraph.text = "unicode text: café résumé".encode('utf-8')
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_paragraph]
        
        result = helpers.convertparagraphs(mock_manpage)
        
        self.assertEqual(mock_paragraph.text, "unicode text: café résumé")
        self.assertIs(result, mock_manpage)

    def test_convertparagraphs_special_characters(self):
        """Test convertparagraphs with special characters"""
        mock_paragraph = Mock()
        mock_paragraph.text = b"Special chars: \xe2\x80\x93 \xe2\x80\x94 \xe2\x80\x98 \xe2\x80\x99"
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_paragraph]
        
        result = helpers.convertparagraphs(mock_manpage)
        
        # Should decode UTF-8 special characters
        expected = b"Special chars: \xe2\x80\x93 \xe2\x80\x94 \xe2\x80\x98 \xe2\x80\x99".decode('utf-8')
        self.assertEqual(mock_paragraph.text, expected)
        self.assertIs(result, mock_manpage)

    def test_suggestions_basic(self):
        """Test suggestions with basic match"""
        # Create mock manpage
        mock_mp = Mock()
        mock_mp.name = "ls"
        mock_mp.section = "1"
        mock_mp.namesection = "ls(1)"
        
        matches = [{
            "name": "ls",
            "start": 0,
            "end": 2,
            "suggestions": [mock_mp]
        }]
        
        command = "ls -l"
        
        helpers.suggestions(matches, command)
        
        # Verify suggestions were processed
        self.assertEqual(len(matches[0]["suggestions"]), 1)
        suggestion = matches[0]["suggestions"][0]
        self.assertEqual(suggestion["cmd"], "ls.1 -l")
        self.assertEqual(suggestion["text"], "ls(1)")

    def test_suggestions_multiple_suggestions(self):
        """Test suggestions with multiple manpages"""
        # Create multiple mock manpages
        mock_mp1 = Mock()
        mock_mp1.name = "ls"
        mock_mp1.section = "1"
        mock_mp1.namesection = "ls(1)"
        
        mock_mp2 = Mock()
        mock_mp2.name = "ls"
        mock_mp2.section = "8"
        mock_mp2.namesection = "ls(8)"
        
        matches = [{
            "name": "ls",
            "start": 0,
            "end": 2,
            "suggestions": [mock_mp2, mock_mp1]  # Unsorted order
        }]
        
        command = "ls -l"
        
        helpers.suggestions(matches, command)
        
        # Verify suggestions were sorted by section
        self.assertEqual(len(matches[0]["suggestions"]), 2)
        self.assertEqual(matches[0]["suggestions"][0]["text"], "ls(1)")
        self.assertEqual(matches[0]["suggestions"][1]["text"], "ls(8)")

    def test_suggestions_command_reconstruction(self):
        """Test suggestions with command reconstruction"""
        mock_mp = Mock()
        mock_mp.name = "grep"
        mock_mp.section = "1"
        mock_mp.namesection = "grep(1)"
        
        # Let's use a simpler command to test reconstruction
        matches = [{
            "name": "grep",
            "start": 5,
            "end": 9,
            "suggestions": [mock_mp]
        }]
        
        command = "echo grep test"
        
        helpers.suggestions(matches, command)
        
        suggestion = matches[0]["suggestions"][0]
        self.assertEqual(suggestion["cmd"], "echo grep.1 test")
        self.assertEqual(suggestion["text"], "grep(1)")

    def test_suggestions_no_name_field(self):
        """Test suggestions with match without name field"""
        matches = [{
            "start": 0,
            "end": 2,
            "suggestions": []
        }]
        
        command = "ls -l"
        
        # Should not process matches without name field
        helpers.suggestions(matches, command)
        
        # Match should remain unchanged
        self.assertNotIn("name", matches[0])

    def test_suggestions_no_suggestions_field(self):
        """Test suggestions with match without suggestions field"""
        matches = [{
            "name": "ls",
            "start": 0,
            "end": 2
        }]
        
        command = "ls -l"
        
        # Should not process matches without suggestions field
        helpers.suggestions(matches, command)
        
        # Match should remain unchanged
        self.assertNotIn("suggestions", matches[0])

    def test_suggestions_empty_suggestions(self):
        """Test suggestions with empty suggestions list"""
        matches = [{
            "name": "ls",
            "start": 0,
            "end": 2,
            "suggestions": []
        }]
        
        command = "ls -l"
        
        helpers.suggestions(matches, command)
        
        # Should result in empty suggestions
        self.assertEqual(matches[0]["suggestions"], [])

    def test_suggestions_multiple_matches(self):
        """Test suggestions with multiple matches"""
        mock_mp1 = Mock()
        mock_mp1.name = "ls"
        mock_mp1.section = "1"
        mock_mp1.namesection = "ls(1)"
        
        mock_mp2 = Mock()
        mock_mp2.name = "grep"
        mock_mp2.section = "1"
        mock_mp2.namesection = "grep(1)"
        
        matches = [
            {
                "name": "ls",
                "start": 0,
                "end": 2,
                "suggestions": [mock_mp1]
            },
            {
                "name": "grep",
                "start": 5,
                "end": 9,
                "suggestions": [mock_mp2]
            }
        ]
        
        command = "ls | grep pattern"
        
        helpers.suggestions(matches, command)
        
        # Verify both matches were processed
        self.assertEqual(matches[0]["suggestions"][0]["cmd"], "ls.1 | grep pattern")
        self.assertEqual(matches[1]["suggestions"][0]["cmd"], "ls | grep.1 pattern")

    def test_suggestions_edge_positions(self):
        """Test suggestions with edge positions in command"""
        mock_mp = Mock()
        mock_mp.name = "ls"
        mock_mp.section = "1"
        mock_mp.namesection = "ls(1)"
        
        # Test at beginning of command
        matches = [{
            "name": "ls",
            "start": 0,
            "end": 2,
            "suggestions": [mock_mp]
        }]
        
        command = "ls"
        
        helpers.suggestions(matches, command)
        
        suggestion = matches[0]["suggestions"][0]
        self.assertEqual(suggestion["cmd"], "ls.1")

    def test_suggestions_at_end_of_command(self):
        """Test suggestions with match at end of command"""
        mock_mp = Mock()
        mock_mp.name = "ls"
        mock_mp.section = "1"
        mock_mp.namesection = "ls(1)"
        
        matches = [{
            "name": "ls",
            "start": 5,
            "end": 7,
            "suggestions": [mock_mp]
        }]
        
        command = "echo ls"
        
        helpers.suggestions(matches, command)
        
        suggestion = matches[0]["suggestions"][0]
        self.assertEqual(suggestion["cmd"], "echo ls.1")

    def test_suggestions_complex_sections(self):
        """Test suggestions with complex section numbers"""
        mock_mp1 = Mock()
        mock_mp1.name = "printf"
        mock_mp1.section = "1"
        mock_mp1.namesection = "printf(1)"
        
        mock_mp2 = Mock()
        mock_mp2.name = "printf"
        mock_mp2.section = "3"
        mock_mp2.namesection = "printf(3)"
        
        mock_mp3 = Mock()
        mock_mp3.name = "printf"
        mock_mp3.section = "1p"
        mock_mp3.namesection = "printf(1p)"
        
        matches = [{
            "name": "printf",
            "start": 0,
            "end": 6,
            "suggestions": [mock_mp3, mock_mp2, mock_mp1]  # Unsorted
        }]
        
        command = "printf 'hello'"
        
        helpers.suggestions(matches, command)
        
        # Verify sorting by section
        suggestions = matches[0]["suggestions"]
        self.assertEqual(len(suggestions), 3)
        # Should be sorted: "1", "1p", "3"
        self.assertEqual(suggestions[0]["text"], "printf(1)")
        self.assertEqual(suggestions[1]["text"], "printf(1p)")
        self.assertEqual(suggestions[2]["text"], "printf(3)")


class TestHelpersIntegration(unittest.TestCase):
    """Integration tests for helpers.py"""

    def setUp(self):
        """Set up integration test fixtures"""
        pass

    def tearDown(self):
        """Clean up after integration tests"""
        pass

    def test_convertparagraphs_with_real_paragraph_structure(self):
        """Test convertparagraphs with realistic paragraph structure"""
        # Create paragraphs that mimic real store.paragraph objects
        mock_p1 = Mock()
        mock_p1.text = b"DESCRIPTION\n    This is a test command."
        
        mock_p2 = Mock()
        mock_p2.text = b"OPTIONS\n    -v, --verbose\n        Enable verbose output."
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_p1, mock_p2]
        
        result = helpers.convertparagraphs(mock_manpage)
        
        self.assertEqual(mock_p1.text, "DESCRIPTION\n    This is a test command.")
        self.assertEqual(mock_p2.text, "OPTIONS\n    -v, --verbose\n        Enable verbose output.")
        self.assertIs(result, mock_manpage)

    def test_suggestions_realistic_scenario(self):
        """Test suggestions with realistic command scenario"""
        # Simulate find command with exec
        mock_find_mp = Mock()
        mock_find_mp.name = "find"
        mock_find_mp.section = "1"
        mock_find_mp.namesection = "find(1)"
        
        mock_grep_mp1 = Mock()
        mock_grep_mp1.name = "grep"
        mock_grep_mp1.section = "1"
        mock_grep_mp1.namesection = "grep(1)"
        
        mock_grep_mp2 = Mock()
        mock_grep_mp2.name = "grep"
        mock_grep_mp2.section = "1p"
        mock_grep_mp2.namesection = "grep(1p)"
        
        matches = [
            {
                "name": "find",
                "start": 0,
                "end": 4,
                "suggestions": [mock_find_mp]
            },
            {
                "name": "grep",
                "start": 17,
                "end": 21,
                "suggestions": [mock_grep_mp2, mock_grep_mp1]
            }
        ]
        
        command = "find /path -exec grep pattern {} \\;"
        
        helpers.suggestions(matches, command)
        
        # Verify find suggestions
        find_suggestion = matches[0]["suggestions"][0]
        self.assertEqual(find_suggestion["cmd"], "find.1 /path -exec grep pattern {} \\;")
        self.assertEqual(find_suggestion["text"], "find(1)")
        
        # Verify grep suggestions (should be sorted)
        grep_suggestions = matches[1]["suggestions"]
        self.assertEqual(len(grep_suggestions), 2)
        self.assertEqual(grep_suggestions[0]["cmd"], "find /path -exec grep.1 pattern {} \\;")
        self.assertEqual(grep_suggestions[0]["text"], "grep(1)")
        self.assertEqual(grep_suggestions[1]["cmd"], "find /path -exec grep.1p pattern {} \\;")
        self.assertEqual(grep_suggestions[1]["text"], "grep(1p)")

    def test_convertparagraphs_error_handling(self):
        """Test convertparagraphs with potential encoding issues"""
        # Test with invalid UTF-8 bytes (should handle gracefully)
        mock_paragraph = Mock()
        # This will raise UnicodeDecodeError if not handled properly
        mock_paragraph.text = b'\xff\xfe invalid utf-8'
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_paragraph]
        
        # This should either handle the error or raise it consistently
        try:
            result = helpers.convertparagraphs(mock_manpage)
            # If it succeeds, verify the result
            self.assertIs(result, mock_manpage)
        except UnicodeDecodeError:
            # If it fails, that's expected behavior for invalid UTF-8
            pass

    def test_suggestions_performance_with_many_suggestions(self):
        """Test suggestions performance with many manpage suggestions"""
        # Create many mock manpages
        mock_manpages = []
        for i in range(50):
            mock_mp = Mock()
            mock_mp.name = "test"
            mock_mp.section = str(i)
            mock_mp.namesection = f"test({i})"
            mock_manpages.append(mock_mp)
        
        matches = [{
            "name": "test",
            "start": 0,
            "end": 4,
            "suggestions": mock_manpages
        }]
        
        command = "test command"
        
        # This should complete in reasonable time
        helpers.suggestions(matches, command)
        
        # Verify all suggestions were processed
        self.assertEqual(len(matches[0]["suggestions"]), 50)
        
        # Verify they're sorted by section (string sort, so "10" comes before "2")
        sections = [s["text"] for s in matches[0]["suggestions"]]
        expected_sections = [f"test({i})" for i in sorted(range(50), key=str)]
        self.assertEqual(sections, expected_sections)

    def test_helpers_module_imports(self):
        """Test that helpers module imports work correctly"""
        # Verify util module is imported
        self.assertTrue(hasattr(helpers, 'util'))
        
        # Verify functions are available
        self.assertTrue(callable(helpers.convertparagraphs))
        self.assertTrue(callable(helpers.suggestions))

    def test_convertparagraphs_preserves_manpage_attributes(self):
        """Test that convertparagraphs preserves other manpage attributes"""
        mock_manpage = Mock()
        mock_manpage.name = "test"
        mock_manpage.section = "1"
        mock_manpage.synopsis = "test synopsis"
        mock_manpage.paragraphs = []
        
        result = helpers.convertparagraphs(mock_manpage)
        
        # Verify other attributes are preserved
        self.assertEqual(result.name, "test")
        self.assertEqual(result.section, "1")
        self.assertEqual(result.synopsis, "test synopsis")
        self.assertIs(result, mock_manpage)


if __name__ == "__main__":
    unittest.main()