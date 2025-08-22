import unittest
from unittest.mock import Mock, patch

from explainshell import manager, errors


class TestManagerSimple(unittest.TestCase):
    """Simplified manager tests focusing on core functionality"""

    def test_manager_initialization_basic(self):
        """Test basic manager initialization"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ) as mock_classifier_class:

            mock_store_instance = Mock()
            mock_classifier_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_classifier_class.return_value = mock_classifier_instance

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            self.assertEqual(mgr.paths, {"test.1.gz"})
            self.assertFalse(mgr.overwrite)
            mock_classifier_instance.train.assert_called_once()

    def test_managerctx_creation_basic(self):
        """Test basic managerctx creation"""
        mock_classifier = Mock()
        mock_store = Mock()
        mock_manpage = Mock()
        mock_manpage.name = "test"

        ctx = manager.managerctx(mock_classifier, mock_store, mock_manpage)

        self.assertEqual(ctx.classifier, mock_classifier)
        self.assertEqual(ctx.store, mock_store)
        self.assertEqual(ctx.manpage, mock_manpage)
        self.assertEqual(ctx.name, "test")

    def test_run_empty_paths(self):
        """Test run with empty paths"""
        with patch(
            "explainshell.manager.store.store"
        ), patch(
            "explainshell.manager.classifier.classifier"
        ):

            mgr = manager.manager("localhost", "testdb", set())
            added, exists = mgr.run()

            self.assertEqual(added, [])
            self.assertEqual(exists, [])

    def test_findmulticommands_no_commands(self):
        """Test findmulticommands with no commands"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_store_instance.names.return_value = []
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            self.assertEqual(mappings, [])
            self.assertEqual(multicommands, {})

    def test_findmulticommands_simple_case(self):
        """Test findmulticommands with simple case"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase"),
            ]
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            self.assertEqual(len(mappings), 1)
            self.assertEqual(mappings[0], ("git rebase", "id2"))
            self.assertEqual(multicommands, {"git": "id1"})

    @patch("explainshell.manager.input")
    def test_main_verify_success(self, mock_input):
        """Test main function with verify option - success case"""
        with patch("explainshell.manager.store.store") as mock_store_class:
            mock_store_instance = Mock()
            mock_store_instance.verify.return_value = (
                True,
                [],
                [],
            )  # verify() returns tuple
            mock_store_class.return_value = mock_store_instance

            result = manager.main(
                [], "testdb", "localhost", False, False, True
            )

            self.assertEqual(result, 0)

    @patch("explainshell.manager.input")
    def test_main_verify_failure(self, mock_input):
        """Test main function with verify option - failure case"""
        with patch("explainshell.manager.store.store") as mock_store_class:
            mock_store_instance = Mock()
            mock_store_instance.verify.return_value = (
                False,
                [],
                [],
            )  # verify() returns tuple
            mock_store_class.return_value = mock_store_instance

            result = manager.main(
                [], "testdb", "localhost", False, False, True
            )

            self.assertEqual(result, 1)

    def test_manager_with_drop_flag(self):
        """Test manager initialization with drop flag"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            manager.manager("localhost", "testdb", set(), drop=True)

            mock_store_instance.drop.assert_called_once_with(True)

    def test_manager_with_overwrite_flag(self):
        """Test manager initialization with overwrite flag"""
        with patch(
            "explainshell.manager.store.store"
        ), patch(
            "explainshell.manager.classifier.classifier"
        ):

            mgr = manager.manager("localhost", "testdb", set(), overwrite=True)

            self.assertTrue(mgr.overwrite)

    def test_run_with_empty_manpage_exception(self):
        """Test run method handling EmptyManpage exception"""
        with patch(
            "explainshell.manager.store.store"
        ), patch(
            "explainshell.manager.classifier.classifier"
        ), patch(
            "explainshell.manager.manpage.manpage"
        ) as mock_manpage_class:

            mock_manpage_class.side_effect = errors.EmptyManpage("test.1.gz")

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})
            added, exists = mgr.run()

            self.assertEqual(added, [])
            self.assertEqual(exists, [])

    def test_run_with_keyboard_interrupt(self):
        """Test run method handling KeyboardInterrupt"""
        with patch(
            "explainshell.manager.store.store"
        ), patch(
            "explainshell.manager.classifier.classifier"
        ), patch(
            "explainshell.manager.manpage.manpage"
        ) as mock_manpage_class:

            mock_manpage_class.side_effect = KeyboardInterrupt()

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            with self.assertRaises(KeyboardInterrupt):
                mgr.run()


if __name__ == "__main__":
    unittest.main()
