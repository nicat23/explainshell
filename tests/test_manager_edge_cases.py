import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from explainshell import manager, errors, store


class TestManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for manager.py"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_with_invalid_paths(self):
        """Test manager behavior with invalid file paths"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mgr = manager.manager("localhost", "testdb", ["/nonexistent/file.gz"])
            
            with patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
                mock_manpage_class.side_effect = FileNotFoundError("File not found")
                
                try:
                    added, exists = mgr.run()
                    self.assertEqual(added, [])
                    self.assertEqual(exists, [])
                except FileNotFoundError:
                    # Expected behavior for invalid paths
                    pass

    def test_manager_with_keyboard_interrupt(self):
        """Test manager handling of KeyboardInterrupt"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"])
            
            with patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
                mock_manpage_class.side_effect = KeyboardInterrupt()
                
                with self.assertRaises(KeyboardInterrupt):
                    mgr.run()

    def test_manager_with_value_error(self):
        """Test manager handling of ValueError during processing"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"])
            
            with patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
                mock_manpage_class.side_effect = ValueError("Invalid value")
                
                added, exists = mgr.run()
                
                self.assertEqual(added, [])
                self.assertEqual(exists, [])

    def test_manager_with_generic_exception(self):
        """Test manager handling of generic exceptions"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"])
            
            with patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
                mock_manpage_class.side_effect = RuntimeError("Generic error")
                
                with self.assertRaises(RuntimeError):
                    mgr.run()

    def test_findmulticommands_no_potential_commands(self):
        """Test findmulticommands when no potential multicommands exist"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # Only simple commands, no hyphens
            mock_store_instance.names.return_value = [
                ("id1", "ls"),
                ("id2", "cat"),
                ("id3", "grep")
            ]
            mock_store_instance.mappings.return_value = []
            
            mgr = manager.manager("localhost", "testdb", [])
            mappings, multicommands = mgr.findmulticommands()
            
            self.assertEqual(mappings, [])
            self.assertEqual(multicommands, {})

    def test_findmulticommands_existing_mappings(self):
        """Test findmulticommands when mappings already exist"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase")
            ]
            # Mapping already exists
            mock_store_instance.mappings.return_value = [("git rebase", "id2")]
            
            mgr = manager.manager("localhost", "testdb", [])
            mappings, multicommands = mgr.findmulticommands()
            
            self.assertEqual(mappings, [])
            self.assertEqual(multicommands, {})

    def test_findmulticommands_no_parent_command(self):
        """Test findmulticommands when parent command doesn't exist"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # git-rebase exists but git doesn't
            mock_store_instance.names.return_value = [
                ("id1", "git-rebase"),
                ("id2", "other-command")
            ]
            mock_store_instance.mappings.return_value = []
            
            mgr = manager.manager("localhost", "testdb", [])
            mappings, multicommands = mgr.findmulticommands()
            
            self.assertEqual(mappings, [])
            self.assertEqual(multicommands, {})

    def test_process_with_no_paragraphs(self):
        """Test process method when manpage has no paragraphs"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer:
            
            mgr = manager.manager("localhost", "testdb", [])
            
            mock_manpage = Mock()
            mock_manpage.name = "test"
            mock_manpage.paragraphs = []  # No paragraphs
            mock_manpage.read = Mock()
            mock_manpage.parse = Mock()
            
            ctx = mgr.ctx(mock_manpage)
            
            with self.assertRaises(AssertionError):
                mgr.process(ctx)

    def test_process_with_no_options_extracted(self):
        """Test process method when no options are extracted"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer, \
             patch('explainshell.manager.options.extract') as mock_extract:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mgr = manager.manager("localhost", "testdb", [])
            
            mock_manpage = Mock()
            mock_manpage.name = "test"
            mock_manpage.paragraphs = [Mock(), Mock()]  # Has paragraphs
            mock_manpage.options = []  # No options after extraction
            mock_manpage.read = Mock()
            mock_manpage.parse = Mock()
            mock_manpage.shortpath = "test.1.gz"
            mock_manpage.synopsis = "test synopsis"
            mock_manpage.aliases = [("test", 10)]
            
            ctx = mgr.ctx(mock_manpage)
            ctx.classifier = Mock()
            ctx.classifier.classify = Mock(return_value=[])
            
            mock_store_instance.addmanpage.return_value = mock_manpage
            
            result = mgr.process(ctx)
            
            # Should still process successfully even without options
            self.assertEqual(result, mock_manpage)

    def test_edit_with_empty_manpage(self):
        """Test edit method with empty manpage"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.fixer.runner') as mock_fixer:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            mgr = manager.manager("localhost", "testdb", [])
            
            mock_manpage = Mock()
            mock_manpage.name = "test"
            mock_manpage.paragraphs = []
            
            mock_store_instance.updatemanpage.return_value = mock_manpage
            
            result = mgr.edit(mock_manpage)
            
            self.assertEqual(result, mock_manpage)

    def test_manager_ctx_with_none_values(self):
        """Test managerctx with None values"""
        mock_manpage = Mock()
        mock_manpage.name = "test"
        ctx = manager.managerctx(None, None, mock_manpage)
        
        self.assertIsNone(ctx.classifier)
        self.assertIsNone(ctx.store)
        self.assertEqual(ctx.name, "test")

    def test_run_with_updated_manpage_no_overwrite(self):
        """Test run method with updated manpage and overwrite=False"""
        with patch('explainshell.manager.store.store') as mock_store_class, \
             patch('explainshell.manager.classifier.classifier') as mock_classifier_class, \
             patch('explainshell.manager.manpage.manpage') as mock_manpage_class:
            
            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            
            # Mock existing updated manpage
            existing_mp = Mock()
            existing_mp.source = "test.1.gz"
            existing_mp.updated = True  # Already updated
            mock_store_instance.findmanpage.return_value = [existing_mp]
            
            # Mock new manpage
            new_mp = Mock()
            new_mp.name = "test"
            new_mp.shortpath = "test.1.gz"
            mock_manpage_class.return_value = new_mp
            
            mgr = manager.manager("localhost", "testdb", ["test.1.gz"], overwrite=True)
            added, exists = mgr.run()
            
            # Should not overwrite updated manpage even with overwrite=True
            self.assertEqual(len(added), 0)
            self.assertEqual(len(exists), 1)


if __name__ == '__main__':
    unittest.main()