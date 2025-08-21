import unittest
import explainshell.algo


class TestAlgoInit(unittest.TestCase):
    def test_algo_module_exists(self):
        self.assertIsNotNone(explainshell.algo)

    def test_algo_has_submodules(self):
        # Test that the algo package can be imported
        import explainshell.algo.features

        self.assertIsNotNone(explainshell.algo.features)
