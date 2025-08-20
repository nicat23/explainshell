import unittest
from explainshell.algo.features import extract_first_line, starts_with_hyphen, is_indented, par_length, word_count, has_bold


class TestFeatures(unittest.TestCase):
    def test_extract_first_line_simple(self):
        result = extract_first_line("a b cd")
        self.assertEqual(result, "a b cd")

    def test_extract_first_line_with_spaces(self):
        result = extract_first_line("a b  cd")
        self.assertEqual(result, "a b")

    def test_starts_with_hyphen_true(self):
        result = starts_with_hyphen("-v")
        self.assertTrue(result)

    def test_starts_with_hyphen_false(self):
        result = starts_with_hyphen("verbose")
        self.assertFalse(result)

    def test_is_indented_true(self):
        result = is_indented("  indented text")
        self.assertTrue(result)

    def test_is_indented_false(self):
        result = is_indented("not indented")
        self.assertFalse(result)

    def test_par_length(self):
        result = par_length("test")
        self.assertIsInstance(result, float)

    def test_word_count(self):
        result = word_count("hello world test")
        self.assertEqual(result, 0)  # 3 words rounded to nearest 10 is 0
        
        result = word_count("one two three four five six seven eight nine ten eleven")
        self.assertEqual(result, 10)  # 11 words rounded to nearest 10 is 10

    def test_has_bold_true(self):
        result = has_bold("<b>bold</b> text")
        self.assertTrue(result)

    def test_has_bold_false(self):
        result = has_bold("plain text")
        self.assertFalse(result)