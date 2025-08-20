import unittest
from explainshell.errors import ProgramDoesNotExist, EmptyManpage


class TestErrors(unittest.TestCase):
    def test_program_does_not_exist_creation(self):
        error = ProgramDoesNotExist("test_program")
        self.assertEqual(str(error), "test_program")
        self.assertIsInstance(error, Exception)

    def test_program_does_not_exist_empty(self):
        error = ProgramDoesNotExist("")
        self.assertEqual(str(error), "")

    def test_empty_manpage_creation(self):
        error = EmptyManpage("empty manpage")
        self.assertEqual(str(error), "empty manpage")
        self.assertIsInstance(error, Exception)

    def test_empty_manpage_empty(self):
        error = EmptyManpage("")
        self.assertEqual(str(error), "")
