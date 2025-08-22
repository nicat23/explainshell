import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch

from explainshell import manager, store


class TestManagerExpanded(unittest.TestCase):
    """Expanded test framework for manager.py"""

    def setUp(self):
        """Set up test environment"""
        self.test_db = "explainshell_test_expanded"
        self.temp_dir = tempfile.mkdtemp()
        self.mock_store = Mock(spec=store.store)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_manpage(self, name="test", source="test.1.gz"):
        """Create a mock manpage object"""
        mock_mp = Mock()
        mock_mp.name = name
        mock_mp.source = source
        mock_mp.shortpath = source
        mock_mp.synopsis = f"{name} - test synopsis"
        # Create mock paragraphs with cleantext method
        mock_paragraphs = []
        for i in range(5):
            p = Mock()
            p.cleantext.return_value = f"test paragraph {i}"
            p.is_option = True
            p.idx = i
            mock_paragraphs.append(p)
        mock_mp.paragraphs = mock_paragraphs
        mock_mp.aliases = [(name, 10)]
        mock_mp.options = []
        mock_mp.updated = False
        return mock_mp

    def test_manager_initialization(self):
        """Test manager initialization with various parameters"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ) as mock_classifier_class:

            mock_store_instance = Mock()
            mock_classifier_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_classifier_class.return_value = mock_classifier_instance

            # Test basic initialization
            mgr = manager.manager("localhost", "testdb", {"/path/to/file.gz"})

            self.assertEqual(mgr.paths, {"/path/to/file.gz"})
            self.assertFalse(mgr.overwrite)
            mock_store_class.assert_called_once_with("testdb", "localhost")
            mock_classifier_instance.train.assert_called_once()

    def test_edit_method(self):
        """Test edit method"""
        with patch(
            "explainshell.manager.store.store"
        ) as mock_store_class, patch(
            "explainshell.manager.classifier.classifier"
        ), patch(
            "explainshell.manager.fixer.runner"
        ) as mock_fixer:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()
            mock_manpage.options = []

            mock_store_instance.updatemanpage.return_value = mock_manpage

            result = mgr.edit(mock_manpage)

            self.assertEqual(result, mock_manpage)
            mock_store_instance.updatemanpage.assert_called_once_with(
                mock_manpage
            )


if __name__ == "__main__":
    unittest.main()
