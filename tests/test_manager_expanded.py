import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from explainshell import manager, store, errors, manpage, config


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
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_classifier_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_classifier_class.return_value = mock_classifier_instance
            
            # Test basic initialization
            mgr = manager.manager("localhost", "testdb", ["/path/to/file.gz"])
            
            self.assertEqual(mgr.paths, ["/path/to/file.gz"])
            self.assertFalse(mgr.overwrite)
            mock_store_class.assert_called_once_with("testdb", "localhost")
            mock_classifier_instance.train.assert_called_once()

    def test_manager_initialization_with_drop(self):
        """Test manager initialization with drop=True"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mgr = manager.manager("localhost", "testdb", [], drop=True)
            
            mock_store_instance.drop.assert_called_once_with(True)

    def test_managerctx_creation(self):
        """Test managerctx object creation"""
        mock_classifier = Mock()
        mock_store = Mock()
        mock_manpage = Mock()
        mock_manpage.name = "test"
        
        ctx = manager.managerctx(mock_classifier, mock_store, mock_manpage)
        
        self.assertEqual(ctx.classifier, mock_classifier)
        self.assertEqual(ctx.store, mock_store)
        self.assertEqual(ctx.manpage, mock_manpage)
        self.assertEqual(ctx.name, "test")
        self.assertIsNone(ctx.classifiermanpage)

    @patch('explainshell.manager.manpage.manpage')
    def test_run_with_empty_paths(self, mock_manpage_class):
        """Test run method with empty paths"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mgr = manager.manager("localhost", "testdb", [])
            added, exists = mgr.run()
            
            self.assertEqual(added, [])
            self.assertEqual(exists, [])

    @patch('explainshell.manager.manpage.manpage')
    def test_run_with_existing_manpage(self, mock_manpage_class):
        """Test run method when manpage already exists"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # Mock existing manpage
            existing_mp = self._create_mock_manpage()
            existing_mp.source = "test.1.gz"
            mock_store_instance.findmanpage.return_value = [existing_mp]
            
            # Mock new manpage
            new_mp = self._create_mock_manpage()
            mock_manpage_class.return_value = new_mp
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"], overwrite=False)
            added, exists = mgr.run()
            
            self.assertEqual(len(added), 0)
            self.assertEqual(len(exists), 1)

    @patch('explainshell.manager.manpage.manpage')
    def test_run_with_overwrite(self, mock_manpage_class):
        """Test run method with overwrite=True"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # Mock existing manpage that can be overwritten
            existing_mp = self._create_mock_manpage()
            existing_mp.updated = False
            existing_mp.source = "test.1.gz"
            existing_mp.aliases = []
            mock_store_instance.findmanpage.return_value = [existing_mp]
            
            # Mock new manpage
            new_mp = self._create_mock_manpage()
            mock_manpage_class.return_value = new_mp
            
            # Mock fixer runner
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"], overwrite=True)
            
            # Mock store.names() for findmulticommands
            mock_store_instance.names.return_value = []
            mock_store_instance.mappings.return_value = []
            
            # Mock the process method to return the manpage
            with patch.object(mgr, 'process', return_value=new_mp):
                added, exists = mgr.run()
            
            self.assertEqual(len(added), 1)
            self.assertEqual(len(exists), 0)

    def test_run_with_empty_manpage_error(self):
        """Test run method handling EmptyManpage error"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
            
            mock_manpage_class.side_effect = errors.EmptyManpage("test.1.gz")
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"])
            added, exists = mgr.run()
            
            self.assertEqual(added, [])
            self.assertEqual(exists, [])

    def test_findmulticommands_basic(self):
        """Test findmulticommands method"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # Mock store methods
            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase"),
                ("id3", "git-commit")
            ]
            mock_store_instance.mappings.return_value = [("git", "id1")]
            
            mgr = manager.manager("localhost", "testdb", [])
            mappings, multicommands = mgr.findmulticommands()
            
            # Should create mappings for git-rebase and git-commit
            expected_mappings = [("git rebase", "id2"), ("git commit", "id3")]
            self.assertEqual(len(mappings), 2)
            self.assertIn(("git rebase", "id2"), mappings)
            self.assertIn(("git commit", "id3"), mappings)

    def test_edit_method(self):
        """Test edit method"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance
            
            mgr = manager.manager("localhost", "testdb", [])
            mock_manpage = self._create_mock_manpage()
            
            # Mock updatemanpage to return the manpage
            mock_store_instance.updatemanpage.return_value = mock_manpage
            mock_manpage.options = []
            mock_manpage.aliases = []
            
            result = mgr.edit(mock_manpage)
            
            self.assertEqual(result, mock_manpage)
            mock_store_instance.updatemanpage.assert_called_once()

    def test_edit_method_with_paragraphs(self):
        """Test edit method with custom paragraphs"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance
            
            mgr = manager.manager("localhost", "testdb", [])
            mock_manpage = self._create_mock_manpage()
            custom_paragraphs = [Mock(), Mock()]
            
            mock_store_instance.updatemanpage.return_value = mock_manpage
            
            result = mgr.edit(mock_manpage, paragraphs=custom_paragraphs)
            
            self.assertEqual(mock_manpage.paragraphs, custom_paragraphs)
            mock_fixer_instance.disable.assert_called_once_with("paragraphjoiner")

    @patch('explainshell.manager.input')
    def test_main_with_verify(self, mock_input):
        """Test main function with verify option"""
        with patch('explainshell.manager.store.store') as mock_store_class:
            mock_store_instance = Mock()
            mock_store_instance.verify.return_value = (True, [], [])
            mock_store_class.return_value = mock_store_instance
            
            result = manager.main([], "testdb", "localhost", False, False, True)
            
            self.assertEqual(result, 0)
            mock_store_instance.verify.assert_called_once()

    @patch('explainshell.manager.input')
    def test_main_with_drop_confirmed(self, mock_input):
        """Test main function with drop option confirmed"""
        mock_input.return_value = "y"
        
        with patch('explainshell.manager.manager') as mock_manager_class, \
             patch('explainshell.manager.glob.glob') as mock_glob:
            
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance
            mock_glob.return_value = []
            
            manager.main([], "testdb", "localhost", False, True, False)
            
            mock_input.assert_called_once()
            mock_manager_class.assert_called_once()

    @patch('explainshell.manager.input')
    def test_main_with_drop_cancelled(self, mock_input):
        """Test main function with drop option cancelled"""
        mock_input.return_value = "n"
        
        with patch('explainshell.manager.manager') as mock_manager_class, \
             patch('explainshell.manager.glob.glob') as mock_glob:
            
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance
            mock_glob.return_value = []
            
            manager.main([], "testdb", "localhost", False, True, False)
            
            mock_input.assert_called_once()
            # Should still create manager but without drop
            mock_manager_class.assert_called_once()

    @patch('explainshell.manager.os.path.isdir')
    @patch('explainshell.manager.glob.glob')
    def test_main_with_directory_path(self, mock_glob, mock_isdir):
        """Test main function with directory path"""
        mock_isdir.return_value = True
        mock_glob.return_value = ["/test/file1.gz", "/test/file2.gz"]
        
        with patch('explainshell.manager.manager') as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance
            
            manager.main(["/test/dir"], "testdb", "localhost", False, False, False)
            
            mock_glob.assert_called_once()
            mock_manager_class.assert_called_once()

    def test_process_method_flow(self):
        """Test the complete process method flow"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer, \
             patch('explainshell.manager.options.extract') as mock_extract:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance
            
            mgr = manager.manager("localhost", "testdb", [])
            
            # Create mock context
            mock_manpage = self._create_mock_manpage()
            mock_manpage.read = Mock()
            mock_manpage.parse = Mock()
            
            ctx = mgr.ctx(mock_manpage)
            ctx.classifier = Mock()
            ctx.classifier.classify = Mock(return_value=[])
            
            mock_store_instance.addmanpage.return_value = mock_manpage
            
            result = mgr.process(ctx)
            
            # Verify the flow
            mock_manpage.read.assert_called_once()
            mock_manpage.parse.assert_called_once()
            mock_extract.assert_called_once()
            mock_store_instance.addmanpage.assert_called_once()
            self.assertEqual(result, mock_manpage)


class TestManagerIntegration(unittest.TestCase):
    """Integration tests for manager functionality"""
    
    def test_manager_with_real_file_structure(self):
        """Test manager with actual file structure (mocked dependencies)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a fake .gz file
            test_file = os.path.join(temp_dir, "test.1.gz")
            with open(test_file, 'wb') as f:
                f.write(b"fake gzip content")
            
            with patch('explainshell.manager.store.store') as mock_store_class, \
                 patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
                 patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
                
                mock_store_instance = Mock()
                mock_store_class.return_value = mock_store_instance
                def mock_findmanpage(name):
                    raise errors.ProgramDoesNotExist(name)
                mock_store_instance.findmanpage.side_effect = mock_findmanpage
                
                mock_manpage_instance = Mock()
                mock_manpage_instance.name = "test"
                mock_manpage_instance.shortpath = "test.1.gz"
                mock_manpage_instance.aliases = []
                mock_manpage_class.return_value = mock_manpage_instance
                
                mgr = manager.manager("localhost", "testdb", [test_file])
                
                # Mock store.names() for findmulticommands
                mock_store_instance.names.return_value = []
                mock_store_instance.mappings.return_value = []
                
                # Mock the process method
                with patch.object(mgr, 'process', return_value=mock_manpage_instance):
                    added, exists = mgr.run()
                
                self.assertEqual(len(added), 1)
                self.assertEqual(len(exists), 0)


if __name__ == '__main__':
    unittest.main()