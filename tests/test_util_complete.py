import unittest
from explainshell.util import namesection


class TestUtilComplete(unittest.TestCase):
    def test_namesection_with_gz(self):
        # Test the assertion error for .gz files
        with self.assertRaises(AssertionError):
            namesection("test.1.gz")

    def test_peekable_iter(self):
        # Test the __iter__ method return (line 114)
        from explainshell.util import peekable

        it = peekable(iter([1, 2, 3]))
        self.assertIs(iter(it), it)
