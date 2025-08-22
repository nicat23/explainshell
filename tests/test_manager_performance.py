import unittest
import time
from unittest.mock import Mock, patch
import tempfile

from explainshell import manager


class TestManagerPerformance(unittest.TestCase):
    """Performance and stress tests for manager.py"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_with_large_file_list(self):
        """Test manager performance with large number of files"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            # Create a large list of file paths
            large_file_list = [f"test{i}.1.gz" for i in range(100)]

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            start_time = time.time()
            mgr = manager.manager("localhost", "testdb", set(large_file_list))
            init_time = time.time() - start_time

            # Initialization should be fast even with many files
            self.assertEqual(len(mgr.paths), 100)
            self.assertLess(
                init_time, 1.0, "Manager initialization took too long"
            )

    def test_findmulticommands_with_many_commands(self):
        """Test findmulticommands performance with many commands"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Create many commands with potential multicommands
            names_data = []
            names_data = [(f"id{i}", f"cmd{i}") for i in range(50)] + \
                [(f"id{i + 50}", f"cmd{i}-sub") for i in range(50)]
            mock_store_instance.names.return_value = names_data
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())

            start_time = time.time()
            mappings, multicommands = mgr.findmulticommands()
            execution_time = time.time() - start_time

            # Should complete in reasonable time
            self.assertLess(
                execution_time, 2.0, "findmulticommands took too long"
            )
            self.assertEqual(len(mappings), 50)  # Should find 50 multicommands

    def test_run_with_concurrent_processing_simulation(self):
        """Test run method behavior under simulated concurrent load"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
            patch(
                "explainshell.manager.manpage.manpage"
            ) as mock_manpage_class,
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Simulate slow database operations
            def slow_findmanpage(name):
                time.sleep(0.01)  # 10ms delay
                from explainshell.errors import ProgramDoesNotExist

                raise ProgramDoesNotExist(name)

            mock_store_instance.findmanpage.side_effect = slow_findmanpage

            # Create multiple manpages
            file_list = [f"test{i}.1.gz" for i in range(10)]

            def create_mock_manpage(i, filename):
                mock_mp = Mock()
                mock_mp.name = f"test{i}"
                mock_mp.shortpath = filename
                mock_mp.aliases = []
                return mock_mp

            mock_manpages = [
                create_mock_manpage(i, filename)
                for i, filename in enumerate(file_list)
            ]

            mock_manpage_class.side_effect = mock_manpages

            mgr = manager.manager("localhost", "testdb", set(file_list))

            # Mock store.names() for findmulticommands
            mock_store_instance.names.return_value = []
            mock_store_instance.mappings.return_value = []

            # Mock the process method to return quickly
            def quick_process(ctx):
                return ctx.manpage

            with patch.object(mgr, "process", side_effect=quick_process):
                start_time = time.time()
                added, exists = mgr.run()
                execution_time = time.time() - start_time

                # Should process all files
                self.assertEqual(len(added), 10)
                self.assertEqual(len(exists), 0)

                # Should complete in reasonable time despite delays
                self.assertLess(
                    execution_time, 1.0, "Processing took too long"
                )

    def test_memory_usage_with_large_manpages(self):
        """Test memory efficiency with large manpage objects"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Create a manpage with many paragraphs
            mock_manpage = Mock()
            mock_manpage.name = "large_test"
            mock_manpage.paragraphs = [
                Mock() for _ in range(1000)
            ]  # Large number of paragraphs
            mock_manpage.options = [Mock() for _ in range(100)]  # Many options

            mgr = manager.manager("localhost", "testdb", set())
            ctx = mgr.ctx(mock_manpage)

            # Should handle large objects without issues
            self.assertEqual(ctx.name, "large_test")
            self.assertEqual(len(ctx.manpage.paragraphs), 1000)

    def test_repeated_operations_performance(self):
        """Test performance of repeated manager operations"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch("explainshell.manager.classifier.classifier"),
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            manager.manager("localhost", "testdb", set())

            # Create a mock manpage
            mock_manpage = Mock()
            mock_manpage.name = "test"
            # Create mock paragraphs with cleantext method

            def create_mock_paragraph(i):
                p = Mock()
                p.cleantext.return_value = f"test paragraph {i}"
                p.is_option = True
                p.idx = i
                return p

            mock_paragraphs = [create_mock_paragraph(i) for i in range(10)]
            mock_manpage.paragraphs = mock_paragraphs
            mock_manpage.options = []
            mock_manpage.aliases = []

            mock_store_instance.updatemanpage.return_value = mock_manpage

            # Perform repeated edit operations
            start_time = time.time()
            mgr = manager.manager("localhost", "testdb", set())
            results = [mgr.edit(mock_manpage) for _ in range(50)]
            execution_time = time.time() - start_time

            # Verify all operations completed
            self.assertEqual(len(results), 50)

            # Should complete repeated operations quickly
            self.assertLess(
                execution_time, 1.0, "Repeated operations took too long"
            )

    def test_manager_cleanup_performance(self):
        """Test manager cleanup and resource deallocation"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Create manager with many paths
            large_file_list = [f"test{i}.1.gz" for i in range(100)]
            mgr = manager.manager("localhost", "testdb", set(large_file_list))

            # Simulate cleanup
            start_time = time.time()
            del mgr
            cleanup_time = time.time() - start_time

            # Cleanup should be fast
            self.assertLess(cleanup_time, 0.1, "Cleanup took too long")

    def test_error_recovery_performance(self):
        """Test performance when recovering from errors"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
            patch(
                "explainshell.manager.manpage.manpage"
            ) as mock_manpage_class,
        ):

            # Create separate mock objects for successful and failing cases
            from explainshell.errors import EmptyManpage

            def create_success_mock(path):
                mock_mp = Mock()
                mock_mp.name = path.replace(".1.gz", "")
                mock_mp.shortpath = path
                mock_mp.aliases = []
                return mock_mp

            # Create mock responses for each file
            success_mocks = [
                create_success_mock(f"test{i}.1.gz") for i in range(5)
            ]
            fail_exceptions = [
                EmptyManpage(f"fail{i}.1.gz") for i in range(5)
            ]

            mock_responses = success_mocks + fail_exceptions
            mock_manpage_class.side_effect = mock_responses

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            def mock_findmanpage(name):
                from explainshell.errors import ProgramDoesNotExist

                raise ProgramDoesNotExist(name)

            mock_store_instance.findmanpage.side_effect = mock_findmanpage

            # Mix of good and bad files (order matches mock_responses)
            file_list = [f"test{i}.1.gz" for i in range(5)] + [
                f"fail{i}.1.gz" for i in range(5)
            ]

            mgr = manager.manager("localhost", "testdb", set(file_list))

            # Mock store.names() for findmulticommands
            mock_store_instance.names.return_value = []
            mock_store_instance.mappings.return_value = []

            with patch.object(mgr, "process", return_value=Mock()):
                start_time = time.time()
                added, exists = mgr.run()
                execution_time = time.time() - start_time

                # Should handle errors gracefully and continue
                self.assertEqual(len(added), 5)  # Only successful ones
                self.assertEqual(len(exists), 0)

                # Should not be significantly slower due to errors
                self.assertLess(
                    execution_time, 1.0, "Error recovery took too long"
                )


class TestManagerStress(unittest.TestCase):
    """Stress tests for manager.py"""

    def test_stress_manager_initialization(self):
        """Stress test manager initialization with extreme parameters"""
        with (
            patch("explainshell.manager.store.store"),
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            # Very large file list
            huge_file_list = [f"test{i}.1.gz" for i in range(1000)]

            mgr = manager.manager("localhost", "testdb", set(huge_file_list))
            self.assertEqual(len(mgr.paths), 1000)

    def test_stress_findmulticommands(self):
        """Stress test findmulticommands with extreme data"""
        with (
            patch("explainshell.manager.store.store") as mock_store_class,
            patch(
                "explainshell.manager.classifier.classifier"
            ),
        ):

            mock_store_instance = Mock()
            mock_store_class.return_value = mock_store_instance

            # Create extreme number of commands
            base_commands = [(f"id{i}", f"cmd{i}") for i in range(500)]
            sub_commands = [(f"id{i}_{j}", f"cmd{i}-sub{j}")
                            for i in range(500) for j in range(5)]
            names_data = base_commands + sub_commands
            mock_store_instance.names.return_value = names_data
            mock_store_instance.mappings.return_value = []

            mgr = manager.manager("localhost", "testdb", set())

            start_time = time.time()
            mappings, multicommands = mgr.findmulticommands()
            execution_time = time.time() - start_time

            # Should complete even with extreme data
            self.assertLess(
                execution_time, 10.0, "Stress test took too long"
            )
            self.assertEqual(len(mappings), 2500)  # 500 * 5 subcommands


if __name__ == "__main__":
    unittest.main()
