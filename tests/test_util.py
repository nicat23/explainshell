import unittest
from explainshell.util import (
    consecutive,
    groupcontinuous,
    toposorted,
    pairwise,
    peekable,
    namesection,
    propertycache,
)


class TestUtil(unittest.TestCase):
    def test_consecutive_empty(self):
        def even(x):
            return x % 2 == 0
        result = list(consecutive([], even))
        self.assertEqual(result, [])

    def test_consecutive_single(self):
        def even(x):
            return x % 2 == 0
        result = list(consecutive([1], even))
        self.assertEqual(result, [[1]])

    def test_consecutive_mixed(self):
        def even(x):
            return x % 2 == 0
        result = list(consecutive([1, 2, 4, 5], even))
        self.assertEqual(result, [[1], [2, 4], [5]])

    def test_groupcontinuous_simple(self):
        result = list(groupcontinuous([1, 2, 4, 5]))
        self.assertEqual(result, [[1, 2], [4, 5]])

    def test_groupcontinuous_with_key(self):
        result = list(groupcontinuous([1, 3, 5, 7], key=lambda x: x // 2))
        self.assertGreater(len(result), 0)

    def test_toposorted_simple(self):
        graph = [1, 2, 3]

        def parents(x):
            return []
        result = toposorted(graph, parents)
        self.assertEqual(len(result), 3)

    def test_toposorted_with_dependencies(self):
        graph = [1, 2, 3]

        def parents(x):
            return [x - 1] if x > 1 else []
        result = toposorted(graph, parents)
        self.assertEqual(result, [1, 2, 3])

    def test_pairwise(self):
        result = list(pairwise([1, 2, 3, 4]))
        self.assertEqual(result, [(1, 2), (2, 3), (3, 4)])

    def test_peekable_basic(self):
        it = peekable(iter([1, 2, 3]))
        self.assertEqual(it.peek(), 1)
        self.assertEqual(it.index, 0)
        self.assertEqual(next(it), 1)
        self.assertEqual(it.index, 1)

    def test_peekable_hasnext(self):
        it = peekable(iter([1]))
        self.assertTrue(it.hasnext())
        next(it)
        self.assertFalse(it.hasnext())

    def test_namesection(self):
        name, section = namesection("test.1")
        self.assertEqual(name, "test")
        self.assertEqual(section, "1")

    def test_propertycache(self):
        class TestClass:
            @propertycache
            def expensive_property(self):
                return "computed_value"

        obj = TestClass()
        result1 = obj.expensive_property
        result2 = obj.expensive_property
        self.assertEqual(result1, "computed_value")
        self.assertEqual(result2, "computed_value")
