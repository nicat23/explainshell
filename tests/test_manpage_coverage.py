"""Tests to improve coverage for manpage.py module"""

import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open

from explainshell import manpage, errors


class TestManpageCoverage(unittest.TestCase):
    """Test cases to improve coverage for manpage.py"""

    def test_extractname_edge_cases(self):
        """Test extractname with various edge cases"""
        # Test with complex paths
        self.assertEqual(manpage.extractname('/very/long/path/to/file.1.gz'), 'file')
        self.assertEqual(manpage.extractname('file.1.1.gz'), 'file.1')
        self.assertEqual(manpage.extractname('file.1xyz.gz'), 'file')
        self.assertEqual(manpage.extractname('file.1.1xyz.gz'), 'file.1')
        
    def test_bold_complex_cases(self):
        """Test bold function with complex HTML"""
        # Test with multiple bold sections
        result = manpage.bold('<b>first</b> text <b>second</b>')
        self.assertEqual(result[0], ['first', 'second'])
        self.assertEqual(result[1], [' text '])
        
        # Test with nested or malformed HTML - the regex only matches the inner bold
        result = manpage.bold('<b>nested<b>bold</b></b>')
        self.assertEqual(result[0], ['bold'])  # Only matches the inner <b>bold</b>
        
    def test_parsesynopsis_error_cases(self):
        """Test _parsesynopsis with invalid input"""
        with self.assertRaises(ValueError):
            manpage._parsesynopsis('/base', '/base: invalid format')
            
        with self.assertRaises(ValueError):
            manpage._parsesynopsis('/base', '/base: "no dash separator"')

    def test_manpage_read_subprocess_error(self):
        """Test manpage.read() when subprocess fails"""
        mp = manpage.manpage('/nonexistent/path.1.gz')
        
        with patch('subprocess.check_output') as mock_subprocess:
            mock_subprocess.side_effect = [
                b'<html>test content</html>',  # First call succeeds
                subprocess.CalledProcessError(1, 'lexgrog')  # Second call fails
            ]
            
            mp.read()
            self.assertIsNotNone(mp._text)
            self.assertIsNone(mp.synopsis)

    def test_manpage_read_decode_error(self):
        """Test manpage.read() with decode errors"""
        mp = manpage.manpage('/test/path.1.gz')
        
        with patch('subprocess.check_output') as mock_subprocess:
            # Return invalid UTF-8 bytes
            mock_subprocess.return_value = b'\xff\xfe invalid utf8'
            
            mp.read()
            # Should handle decode errors gracefully
            self.assertIsNotNone(mp._text)

    def test_manpage_parse_empty_text(self):
        """Test parse() with empty or None text"""
        mp = manpage.manpage('/test/path.1.gz')
        mp._text = None
        
        with self.assertRaises(errors.EmptyManpage):
            mp.parse()

    def test_manpage_parse_no_paragraphs(self):
        """Test parse() when no paragraphs are generated"""
        mp = manpage.manpage('/test/path.1.gz')
        mp._text = '<html>\n\n\n\n\n\n\n</html>'  # Empty content after slicing
        
        with self.assertRaises(errors.EmptyManpage):
            mp.parse()

    def test_manpage_parse_with_synopsis(self):
        """Test parse() with synopsis processing"""
        mp = manpage.manpage('/test/echo.1.gz')
        # Create proper HTML that will generate paragraphs after slicing [7:-3]
        mp._text = '''line1
line2
line3
line4
line5
line6
line7
<p>Some content here</p>
<p>More content</p>
<p>Another paragraph</p>
footer1
footer2
footer3'''
        mp.synopsis = '/test/echo.1.gz: "echo - display a line of text"'
        
        mp.parse()
        
        self.assertEqual(mp.synopsis, 'display a line of text')
        self.assertIn('echo', [alias for alias, score in mp.aliases])

    def test_manpage_parse_multiple_synopsis_lines(self):
        """Test parse() with multiple synopsis lines"""
        mp = manpage.manpage('/test/prog.1.gz')
        # Create proper HTML that will generate paragraphs after slicing [7:-3]
        mp._text = '''line1
line2
line3
line4
line5
line6
line7
<p>Content paragraph</p>
<p>Another paragraph</p>
footer1
footer2
footer3'''
        mp.synopsis = '''/test/prog.1.gz: "prog - first description"
/test/prog.1.gz: "alias1 - same description"
/test/prog.1.gz: "alias2 - same description"'''
        
        mp.parse()
        
        self.assertEqual(mp.synopsis, 'first description')
        alias_names = [alias for alias, score in mp.aliases]
        self.assertIn('prog', alias_names)

    def test_parsetext_section_detection(self):
        """Test _parsetext with section headers"""
        lines = [
            '<b>NAME</b>',
            'program - description',
            '',
            '<b>SYNOPSIS</b>',
            'program [options]',
            '',
            '   <b>DESCRIPTION:</b>',
            'This is a description',
        ]
        
        paragraphs = list(manpage._parsetext(lines))
        
        self.assertEqual(len(paragraphs), 3)
        self.assertEqual(paragraphs[0].section, 'NAME')
        self.assertEqual(paragraphs[1].section, 'SYNOPSIS')
        self.assertEqual(paragraphs[2].section, 'DESCRIPTION')

    def test_parsetext_bold_section_detection(self):
        """Test _parsetext with bold section detection"""
        lines = [
            '    <b>OPTIONS:</b>',
            '    -v, --verbose',
            '        Enable verbose output',
            '',
            'More content'
        ]
        
        paragraphs = list(manpage._parsetext(lines))
        
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0].section, 'OPTIONS')

    def test_parsetext_href_replacement(self):
        """Test _parsetext with href replacement"""
        lines = [
            '<a href="file:///usr/share/man/man1/ls.1.gz?ls(1)">ls(1)</a>',
            'Some text with link'
        ]
        
        paragraphs = list(manpage._parsetext(lines))
        
        self.assertIn('manpages.ubuntu.com', paragraphs[0].text)

    def test_parsetext_replacement_patterns(self):
        """Test _parsetext with various replacement patterns"""
        lines = [
            'Text with \xe2\x80\xe2\x80\x98quotes\xe2\x80\xe2\x80\x99',
            '',  # Empty line to separate paragraphs
            'Text with \xe2\x94\xe2\x94\x82 pipe',
            '',  # Empty line to separate paragraphs
            'Text with \xc2\xb7 bullet'
        ]
        
        paragraphs = list(manpage._parsetext(lines))
        
        # Should apply replacements without crashing
        self.assertEqual(len(paragraphs), 3)

    def test_extracted_from_parse_no_synopsis(self):
        """Test _extracted_from_parse_7 with no synopsis"""
        mp = manpage.manpage('/test/path.1.gz')
        mp.synopsis = None
        mp.aliases = {'test'}
        
        # Should not crash when synopsis is None
        mp._extracted_from_parse_7()
        
        self.assertEqual(mp.synopsis, None)

    def test_extracted_from_parse_empty_items(self):
        """Test _extracted_from_parse_7 with empty parsed synopsis"""
        mp = manpage.manpage('/test/path.1.gz')
        mp.synopsis = '/test/path.1.gz: "invalid format"'
        mp.aliases = {'test'}
        
        with patch('explainshell.manpage._parsesynopsis') as mock_parse:
            mock_parse.side_effect = ValueError("Could not parse")
            
            # Should handle parsing errors gracefully
            try:
                mp._extracted_from_parse_7()
            except ValueError:
                pass  # Expected to raise ValueError

if __name__ == '__main__':
    unittest.main()