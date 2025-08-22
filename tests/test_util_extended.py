import unittest
from explainshell.util import peekable


class TestUtilExtended(unittest.TestCase):
    def test_peekable_empty_iterator(self):
        it = peekable(iter([]))
        with self.assertRaises(StopIteration):
            it.peek()

    def test_peekable_multiple_peeks(self):
        it = peekable(iter([1, 2, 3]))
        self.assertEqual(it.peek(), 1)
        self.assertEqual(it.peek(), 1)  # Should return same value
        self.assertEqual(next(it), 1)
        self.assertEqual(it.peek(), 2)

    def test_peekable_next_after_peek(self):
        it = peekable(iter([1, 2]))
        it.peek()
        self.assertEqual(next(it), 1)
        self.assertEqual(next(it), 2)
        with self.assertRaises(StopIteration):
            next(it)

    def test_peekable_index_tracking(self):
        it = peekable(iter([1, 2, 3]))
        self.assertEqual(it.index, 0)
        it.peek()
        self.assertEqual(it.index, 0)  # Peek shouldn't advance index
        next(it)
        self.assertEqual(it.index, 1)

    def test_toposorted_cyclic_graph(self):
        from explainshell.util import toposorted

        graph = [1, 2]

        def parents(x):
            return [2] if x == 1 else [1]  # Cyclic dependency

        with self.assertRaises(ValueError):
            toposorted(graph, parents)
