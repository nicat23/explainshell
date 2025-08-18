import unittest
from explainshell.algo.features import first_line_contains, first_line_length, first_line_word_count, is_good_section


class TestFeaturesExtended(unittest.TestCase):
    def test_first_line_contains_true(self):
        result = first_line_contains("hello world\nsecond line", "world")
        self.assertTrue(result)

    def test_first_line_contains_false(self):
        result = first_line_contains("hello world\nsecond line", "missing")
        self.assertFalse(result)

    def test_first_line_length(self):
        result = first_line_length("test line")
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)

    def test_first_line_word_count(self):
        result = first_line_word_count("hello world test")
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)

    def test_first_line_word_count_short_words(self):
        result = first_line_word_count("a b c")  # Short words filtered out
        self.assertIsInstance(result, (int, float))

    def test_is_good_section_options(self):
        class MockParagraph:
            def __init__(self, section):
                self.section = section
        
        p = MockParagraph("OPTIONS")
        result = is_good_section(p)
        self.assertTrue(result)

    def test_is_good_section_description(self):
        class MockParagraph:
            def __init__(self, section):
                self.section = section
        
        p = MockParagraph("description")
        result = is_good_section(p)
        self.assertTrue(result)

    def test_is_good_section_bad(self):
        class MockParagraph:
            def __init__(self, section):
                self.section = section
        
        p = MockParagraph("AUTHOR")
        result = is_good_section(p)
        self.assertFalse(result)

    def test_is_good_section_none(self):
        class MockParagraph:
            def __init__(self, section):
                self.section = section
        
        p = MockParagraph(None)
        result = is_good_section(p)
        self.assertFalse(result)