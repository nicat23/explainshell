import unittest
from explainshell.util import consecutive, groupcontinuous, pairwise


class TestEdgeCases(unittest.TestCase):
    def test_consecutive_all_true(self):
        result = list(consecutive([2, 4, 6], lambda x: x % 2 == 0))
        self.assertEqual(result, [[2, 4, 6]])

    def test_consecutive_all_false(self):
        result = list(consecutive([1, 3, 5], lambda x: x % 2 == 0))
        self.assertEqual(result, [[1], [3], [5]])

    def test_groupcontinuous_single_item(self):
        result = list(groupcontinuous([5]))
        self.assertEqual(result, [[5]])

    def test_groupcontinuous_empty(self):
        result = list(groupcontinuous([]))
        self.assertEqual(result, [])

    def test_pairwise_empty(self):
        result = list(pairwise([]))
        self.assertEqual(result, [])

    def test_pairwise_single_item(self):
        result = list(pairwise([1]))
        self.assertEqual(result, [])

    def test_pairwise_two_items(self):
        result = list(pairwise([1, 2]))
        self.assertEqual(result, [(1, 2)])
