import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch

from explainshell import manager, errors


class TestManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for manager.py to increase coverage"""

    def setUp(self):
        self.test_db = "explainshell_test_comprehensive"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_manpage(self, name="test", source="test.1.gz"):
        """Create a mock manpage object"""
        mock_mp = Mock()
        mock_mp.name = name
        mock_mp.source = source
        mock_mp.shortpath = source
        mock_mp.synopsis = f"{name} - test synopsis"
        mock_mp.paragraphs = [Mock() for _ in range(3)]
        mock_mp.aliases = [(name, 10)]
        mock_mp.options = []
        mock_mp.updated = False
        return mock_mp

    def test_read_method_with_assertion_error(self):
        """Test _read method when paragraphs assertion fails"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.fixer.runner") as mock_fixer:

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()
            mock_manpage.read = Mock()
            mock_manpage.parse = Mock()
            mock_manpage.paragraphs = [Mock()]  # Only 1 paragraph
            # will fail assertion

            ctx = mgr.ctx(mock_manpage)
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance

            with self.assertRaises(AssertionError):
                mgr._read(ctx, mock_fixer_instance)

    def test_extract_method_no_options_warning(self):
        """Test _extract method when no options are found"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.options.extract"), \
             patch("explainshell.manager.logger") as mock_logger:

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()
            mock_manpage.options = []  # No options found

            ctx = mgr.ctx(mock_manpage)
            mock_fixer_instance = Mock()

            mgr._extract(ctx, mock_fixer_instance)

            mock_logger.warning.assert_called_once()
            self.assertIn(
                "couldn't find any options",
                mock_logger.warning.call_args[0][0]
            )

    def test_run_with_value_error(self):
        """Test run method handling ValueError"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class, \
             patch("explainshell.manager.logger") as mock_logger:

            mock_manpage_class.side_effect = ValueError("test error")

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})
            added, exists = mgr.run()

            self.assertEqual(added, [])
            self.assertEqual(exists, [])
            mock_logger.fatal.assert_called()

    def test_run_with_keyboard_interrupt(self):
        """Test run method handling KeyboardInterrupt"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class:

            mock_manpage_class.side_effect = KeyboardInterrupt()

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            with self.assertRaises(KeyboardInterrupt):
                mgr.run()

    def test_run_with_general_exception(self):
        """Test run method handling general exception"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class, \
             patch("explainshell.manager.logger") as mock_logger:

            mock_manpage_class.side_effect = RuntimeError("unexpected error")

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            with self.assertRaises(RuntimeError):
                mgr.run()

            # Should log fatal error once for general exception
            mock_logger.fatal.assert_called()

    def test_run_with_existing_updated_manpage(self):
        """Test run method with existing manpage that has updated=True"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Mock existing manpage with updated=True
            existing_mp = self._create_mock_manpage()
            existing_mp.updated = True
            existing_mp.source = "test.1.gz"
            mock_store_instance.findmanpage.return_value = [existing_mp]

            # Mock new manpage
            new_mp = self._create_mock_manpage()
            mock_manpage_class.return_value = new_mp

            mgr = manager.manager(
                "localhost", "testdb", {"test.1.gz"}, overwrite=True
            )
            added, exists = mgr.run()

            # Should not overwrite updated manpage even with overwrite=True
            self.assertEqual(len(added), 0)
            self.assertEqual(len(exists), 1)

    def test_findmulticommands_with_existing_mappings(self):
        """Test findmulticommands with existing mappings"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Mock store methods
            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase"),
            ]
            # Existing mapping should prevent new mapping creation
            mock_store_instance.mappings.return_value = [("git rebase", "id2")]

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            # Should not create mapping since it already exists
            self.assertEqual(len(mappings), 0)
            self.assertEqual(len(multicommands), 0)

    def test_findmulticommands_no_base_command(self):
        """Test findmulticommands when base command doesn't exist"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Mock store methods - no base "git" command
            mock_store_instance.names.return_value = [
                ("id1", "other"),
                ("id2", "git-rebase"),
            ]
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            # Should not create mapping since base command doesn't exist
            self.assertEqual(len(mappings), 0)
            self.assertEqual(len(multicommands), 0)

    def test_main_with_verify_failure(self):
        """Test main function with verify returning failure"""
        with patch("explainshell.manager.store.store") as mock_store_class:
            mock_store_instance = Mock()
            mock_store_instance.verify.return_value = (False, ["unreachable"],
                                                       ["notfound"])
            mock_store_class.return_value = mock_store_instance

            result = manager.main([], "testdb", "localhost", False, False,
                                  True)

            self.assertEqual(result, 1)

    @patch("explainshell.manager.os.path.isdir")
    @patch("explainshell.manager.os.path.abspath")
    def test_main_with_file_path(self, mock_abspath, mock_isdir):
        """Test main function with file path (not directory)"""
        mock_isdir.return_value = False
        mock_abspath.return_value = "/test/file.gz"

        with patch("explainshell.manager.manager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main(["/test/file.gz"], "testdb", "localhost", False,
                         False, False)

            mock_manager_class.assert_called_once()
            # Should be called with set containing the absolute path
            args = mock_manager_class.call_args[0]
            self.assertIn("/test/file.gz", args[2])

    def test_main_with_added_manpages_output(self):
        """Test main function output when manpages are added"""
        with patch("explainshell.manager.manager") as mock_manager_class, \
             patch("builtins.print") as mock_print:

            mock_manager_instance = Mock()
            added_mp = Mock()
            added_mp.source = "test.1.gz"
            mock_manager_instance.run.return_value = ([added_mp], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main([], "testdb", "localhost", False, False, False)

            mock_print.assert_called()
            # Should print success message
            print_calls = [
                call[0][0] for call in mock_print.call_args_list
            ]
            self.assertTrue(
                any("successfully added" in call for call in print_calls)
            )

    def test_main_with_existing_manpages_output(self):
        """Test main function output when manpages already exist"""
        with patch("explainshell.manager.manager") as mock_manager_class, \
             patch("builtins.print") as mock_print:

            mock_manager_instance = Mock()
            existing_mp = Mock()
            existing_mp.path = "/test/existing.1.gz"
            mock_manager_instance.run.return_value = ([], [existing_mp])
            mock_manager_class.return_value = mock_manager_instance

            manager.main([], "testdb", "localhost", False, False, False)

            mock_print.assert_called()
            # Should print existing manpages message
            print_calls = [
                call[0][0] for call in mock_print.call_args_list
            ]
            self.assertTrue(
                any("already existed" in call for call in print_calls)
            )

    def test_classify_method(self):
        """Test _classify method"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch(
                 "explainshell.manager.store.classifiermanpage"
             ) as mock_classifiermanpage:

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()

            ctx = mgr.ctx(mock_manpage)
            ctx.classifier = Mock()
            ctx.classifier.classify = Mock(return_value=iter([]))

            mock_fixer_instance = Mock()
            mock_classifiermanpage.return_value = Mock()

            mgr._classify(ctx, mock_fixer_instance)

            mock_classifiermanpage.assert_called_once_with(
                ctx.name, ctx.manpage.paragraphs
            )
            ctx.classifier.classify.assert_called_once()
            mock_fixer_instance.pre_classify.assert_called_once()
            mock_fixer_instance.post_classify.assert_called_once()

    def test_write_method(self):
        """Test _write method"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()

            ctx = mgr.ctx(mock_manpage)
            mock_fixer_instance = Mock()

            mock_store_instance.addmanpage.return_value = mock_manpage

            result = mgr._write(ctx, mock_fixer_instance)

            mock_fixer_instance.pre_add_manpage.assert_called_once()
            mock_store_instance.addmanpage.assert_called_once_with(
                ctx.manpage
            )
            self.assertEqual(result, mock_manpage)

    def test_update_method(self):
        """Test _update method"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()

            ctx = mgr.ctx(mock_manpage)
            mock_fixer_instance = Mock()

            mock_store_instance.updatemanpage.return_value = mock_manpage

            result = mgr._update(ctx, mock_fixer_instance)

            mock_fixer_instance.pre_add_manpage.assert_called_once()
            mock_store_instance.updatemanpage.assert_called_once_with(
                ctx.manpage
            )
            self.assertEqual(result, mock_manpage)

    def test_run_with_no_added_manpages_warning(self):
        """Test run method warning when no manpages are added"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class, \
             patch("explainshell.manager.logger") as mock_logger:

            # Mock manpage that fails to process (returns None)
            mock_manpage_instance = Mock()
            mock_manpage_instance.shortpath = "test.1.gz"
            mock_manpage_instance.name = "test"
            mock_manpage_class.return_value = mock_manpage_instance

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_store_instance.findmanpage.side_effect = \
                errors.ProgramDoesNotExist("test")

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            # Mock process to return None (failed processing)
            with patch.object(mgr, "process", return_value=None):
                added, exists = mgr.run()

            self.assertEqual(len(added), 0)
            mock_logger.warning.assert_called_with("no manpages added")

    def test_run_calls_findmulticommands_when_manpages_added(self):
        """Test that run calls findmulticommands when manpages are added"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_store_instance.findmanpage.side_effect = \
                errors.ProgramDoesNotExist("test")

            mock_manpage_instance = Mock()
            mock_manpage_instance.shortpath = "test.1.gz"
            mock_manpage_instance.name = "test"
            mock_manpage_class.return_value = mock_manpage_instance

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            # Mock store methods for findmulticommands
            mock_store_instance.names.return_value = []
            mock_store_instance.mappings.return_value = []

            # Mock process to return a manpage (successful processing)
            with patch.object(
                mgr, "process", return_value=mock_manpage_instance
            ):
                added, exists = mgr.run()

            self.assertEqual(len(added), 1)
            # Verify findmulticommands was called
            mock_store_instance.names.assert_called_once()
            mock_store_instance.mappings.assert_called_once()


class TestManagerAdditionalCoverage(unittest.TestCase):
    """Additional tests to cover remaining missed statements"""

    def setUp(self):
        self.test_db = "explainshell_test_additional"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_manpage(self, name="test", source="test.1.gz"):
        """Create a mock manpage object"""
        mock_mp = Mock()
        mock_mp.name = name
        mock_mp.source = source
        mock_mp.shortpath = source
        mock_mp.synopsis = f"{name} - test synopsis"
        mock_mp.paragraphs = [Mock() for _ in range(3)]
        mock_mp.aliases = [(name, 10)]
        mock_mp.options = []
        mock_mp.updated = False
        return mock_mp

    def test_read_method_store_manpage_creation(self):
        """Test _read method store.manpage creation"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.store.manpage") as mock_store_manpage:

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = Mock()
            mock_manpage.read = Mock()
            mock_manpage.parse = Mock()
            mock_manpage.paragraphs = [Mock(), Mock(), Mock()]  # 3 paragraphs
            mock_manpage.shortpath = "test.1.gz"
            mock_manpage.name = "test"
            mock_manpage.synopsis = "test synopsis"
            mock_manpage.aliases = [("test", 10)]

            ctx = mgr.ctx(mock_manpage)
            mock_fixer_instance = Mock()
            mock_store_manpage.return_value = Mock()

            mgr._read(ctx, mock_fixer_instance)

            # Verify store.manpage was called with correct parameters
            mock_store_manpage.assert_called_once_with(
                mock_manpage.shortpath,
                mock_manpage.name,
                mock_manpage.synopsis,
                mock_manpage.paragraphs,
                list(mock_manpage.aliases)
            )

    def test_classify_method_list_consumption(self):
        """Test _classify method list() consumption of classifier results"""
        with patch("explainshell.manager.store.store"), \
             patch("explainshell.manager.classifier.classifier"), \
             patch(
                 "explainshell.manager.store.classifiermanpage"
             ) as mock_classifiermanpage:

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = self._create_mock_manpage()

            ctx = mgr.ctx(mock_manpage)
            ctx.classifier = Mock()
            # Return an iterator that yields results
            ctx.classifier.classify = Mock(
                return_value=iter(["result1", "result2"])
            )

            mock_fixer_instance = Mock()
            mock_classifiermanpage.return_value = Mock()

            mgr._classify(ctx, mock_fixer_instance)

            # Verify classify was called and results consumed
            ctx.classifier.classify.assert_called_once()

    def test_run_with_multiple_matching_manpages(self):
        """Test run method with multiple matching manpages in store"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Mock multiple existing manpages with same shortpath
            existing_mp1 = self._create_mock_manpage()
            existing_mp1.source = "test.1.gz"
            existing_mp2 = self._create_mock_manpage()
            existing_mp2.source = "other.1.gz"  # Different source
            mock_store_instance.findmanpage.return_value = [
                existing_mp1, existing_mp2
            ]

            # Mock new manpage
            new_mp = self._create_mock_manpage()
            new_mp.shortpath = "test.1.gz"
            new_mp.name = "test"
            mock_manpage_class.return_value = new_mp

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"},
                                  overwrite=False)
            added, exists = mgr.run()

            # Should find matching manpage and not overwrite
            self.assertEqual(len(added), 0)
            self.assertEqual(len(exists), 1)

    def test_run_with_assertion_error_in_mps_filtering(self):
        """Test run method assertion when multiple matching sources found"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.manpage.manpage") as \
             mock_manpage_class:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Mock multiple existing manpages with SAME source
            # (should trigger assertion)
            existing_mp1 = self._create_mock_manpage()
            existing_mp1.source = "test.1.gz"
            existing_mp2 = self._create_mock_manpage()
            existing_mp2.source = "test.1.gz"  # Same source -
            # violates assertion
            mock_store_instance.findmanpage.return_value = [
                existing_mp1, existing_mp2
            ]

            new_mp = self._create_mock_manpage()
            new_mp.shortpath = "test.1.gz"
            new_mp.name = "test"
            mock_manpage_class.return_value = new_mp

            mgr = manager.manager("localhost", "testdb", {"test.1.gz"})

            with self.assertRaises(AssertionError):
                mgr.run()

    def test_findmulticommands_mapping_insertion_logging(self):
        """Test findmulticommands mapping insertion with logging"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.logger") as mock_logger:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase"),
            ]
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            # Verify mapping was added and logged
            mock_store_instance.addmapping.assert_called_once_with(
                "git rebase", "id2", 1
            )
            mock_logger.info.assert_any_call(
                "inserting mapping (multicommand) %s -> %s",
                "git rebase", "id2"
            )

    def test_findmulticommands_multicommand_setting_logging(self):
        """Test findmulticommands multicommand setting with logging"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.logger") as mock_logger:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            mock_store_instance.names.return_value = [
                ("id1", "git"),
                ("id2", "git-rebase"),
            ]
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())
            mappings, multicommands = mgr.findmulticommands()

            # Verify multicommand was set and logged
            mock_store_instance.setmulticommand.assert_called_once_with("id1")
            mock_logger.info.assert_any_call("making %r a multicommand", "git")

    @patch("explainshell.manager.os.path.isdir")
    @patch("explainshell.manager.glob.glob")
    @patch("explainshell.manager.os.path.abspath")
    def test_main_directory_processing_with_glob(
        self, mock_abspath, mock_glob, mock_isdir
    ):
        """Test main function directory processing with glob expansion"""
        mock_isdir.return_value = True
        mock_glob.return_value = ["/test/file1.gz", "/test/file2.gz"]
        mock_abspath.side_effect = lambda x: f"/abs{x}"

        with patch("explainshell.manager.manager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main(["/test/dir"], "testdb", "localhost", False,
                         False, False)

            # Verify glob was called with correct path
            mock_glob.assert_called_once_with("/test/dir/*.gz")
            # Verify manager was created with absolute paths
            args = mock_manager_class.call_args[0]
            self.assertIn("/abs/test/file1.gz", args[2])
            self.assertIn("/abs/test/file2.gz", args[2])

    @patch("explainshell.manager.os.path.isdir")
    @patch("explainshell.manager.os.path.abspath")
    def test_main_file_processing_with_abspath(self, mock_abspath, mock_isdir):
        """Test main function file processing with abspath"""
        mock_isdir.return_value = False
        mock_abspath.return_value = "/abs/test/file.gz"

        with patch("explainshell.manager.manager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main(
                ["/test/file.gz"], "testdb", "localhost", False, False, False
            )

            # Verify abspath was called
            mock_abspath.assert_called_once_with("/test/file.gz")
            # Verify manager was created with absolute path
            args = mock_manager_class.call_args[0]
            self.assertIn("/abs/test/file.gz", args[2])

    def test_main_overwrite_flag_when_drop_confirmed(self):
        """Test main function sets overwrite=True when drop is confirmed"""
        with patch("explainshell.manager.input") as mock_input, \
             patch("explainshell.manager.manager") as mock_manager_class:

            mock_input.return_value = "y"
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main([], "testdb", "localhost", False, True, False)

            # Verify manager was created with overwrite=True when drop=True
            args = mock_manager_class.call_args[0]
            self.assertTrue(args[3])
            # overwrite should be True (4th positional arg)
            self.assertTrue(args[4])
            # drop should be True (5th positional arg)

    def test_main_preserve_overwrite_when_drop_cancelled(self):
        """Test main function preserves overwrite
        flag when drop is cancelled"""
        with patch("explainshell.manager.input") as mock_input, \
             patch("explainshell.manager.manager") as mock_manager_class:

            mock_input.return_value = "n"
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main(
                [], "testdb", "localhost", True, True, False
            )  # overwrite=True initially

            # Verify manager was created with original overwrite flag
            args = mock_manager_class.call_args[0]
            self.assertTrue(args[3])    # should preserve original True
            self.assertFalse(args[4])   # drop should be False


class TestManagerFinalCoverage(unittest.TestCase):
    """Final tests to cover any remaining edge cases"""

    def setUp(self):
        self.test_db = "explainshell_test_final"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_managerctx_all_attributes(self):
        """Test managerctx initialization with all attributes"""
        mock_classifier = Mock()
        mock_store = Mock()
        mock_manpage = Mock()
        mock_manpage.name = "test_command"

        ctx = manager.managerctx(mock_classifier, mock_store, mock_manpage)

        # Test all attributes are properly initialized
        self.assertEqual(ctx.classifier, mock_classifier)
        self.assertEqual(ctx.store, mock_store)
        self.assertEqual(ctx.manpage, mock_manpage)
        self.assertEqual(ctx.name, "test_command")
        self.assertIsNone(ctx.classifiermanpage)
        self.assertIsNone(ctx.optionsraw)
        self.assertIsNone(ctx.optionsextracted)
        self.assertIsNone(ctx.aliases)

    @patch("explainshell.manager.os.path.join")
    def test_main_glob_path_construction(self, mock_join):
        """Test main function glob path construction"""
        mock_join.return_value = "/test/dir/*.gz"

        with patch("explainshell.manager.os.path.isdir") as mock_isdir, \
             patch("explainshell.manager.glob.glob") as mock_glob, \
             patch("explainshell.manager.manager") as mock_manager_class:

            mock_isdir.return_value = True
            mock_glob.return_value = []
            mock_manager_instance = Mock()
            mock_manager_instance.run.return_value = ([], [])
            mock_manager_class.return_value = mock_manager_instance

            manager.main(["/test/dir"], "testdb", "localhost", False,
                         False, False)

            # Verify os.path.join was called to construct glob pattern
            mock_join.assert_called_once_with("/test/dir", "*.gz")
            mock_glob.assert_called_once_with("/test/dir/*.gz")

    def test_edit_method_without_paragraphs_calls_extract(self):
        """Test edit method calls _extract when no paragraphs provided"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch("explainshell.manager.classifier.classifier"), \
             patch("explainshell.manager.fixer.runner") as mock_fixer:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_fixer_instance = Mock()
            mock_fixer.return_value = mock_fixer_instance

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = Mock()
            mock_manpage.options = []
            mock_store_instance.updatemanpage.return_value = mock_manpage

            # Mock _extract method to verify it's called
            with patch.object(mgr, '_extract') as mock_extract:
                mgr.edit(mock_manpage)  # No paragraphs provided

                # Should call _extract when no paragraphs provided
                mock_extract.assert_called_once()
                # Should not disable paragraphjoiner
                mock_fixer_instance.disable.assert_not_called()

    def test_ctx_method_returns_managerctx(self):
        """Test ctx method returns properly initialized managerctx"""
        with patch("explainshell.manager.store.store") as mock_store_class, \
             patch(
                 "explainshell.manager.classifier.classifier"
             ) as mock_classifier_class:

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance
            mock_classifier_instance = Mock()
            mock_classifier_class.return_value = mock_classifier_instance

            mgr = manager.manager("localhost", "testdb", set())
            mock_manpage = Mock()
            mock_manpage.name = "test"

            ctx = mgr.ctx(mock_manpage)

            self.assertIsInstance(ctx, manager.managerctx)
            self.assertEqual(ctx.classifier, mock_classifier_instance)
            self.assertEqual(ctx.store, mock_store_instance)
            self.assertEqual(ctx.manpage, mock_manpage)
            self.assertEqual(ctx.name, "test")


if __name__ == "__main__":
    unittest.main()
