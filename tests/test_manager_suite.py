import unittest
import sys
import os


def create_manager_test_suite():
    """Create a comprehensive test suite for manager.py"""
    # Import test modules only when needed
    # Import test classes using relative imports
    from .test_manager_expanded import (
        TestManagerExpanded,
        TestManagerIntegration,
    )
    from .test_manager_edge_cases import TestManagerEdgeCases
    from .test_manager_performance import (
        TestManagerPerformance,
        TestManagerStress,
    )

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add expanded functionality tests
    suite.addTest(loader.loadTestsFromTestCase(TestManagerExpanded))
    suite.addTest(loader.loadTestsFromTestCase(TestManagerIntegration))

    # Add edge case tests
    suite.addTest(loader.loadTestsFromTestCase(TestManagerEdgeCases))

    # Add performance tests
    suite.addTest(loader.loadTestsFromTestCase(TestManagerPerformance))

    # Add stress tests (optional, can be skipped if too resource intensive)
    if "--include-stress" in sys.argv:
        suite.addTest(loader.loadTestsFromTestCase(TestManagerStress))

    return suite


def run_manager_tests():
    """Run all manager tests with detailed output"""
    suite = create_manager_test_suite()
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast="--failfast" in sys.argv,
    )

    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print("Manager Test Suite Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}"
    )

    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


class TestManagerTestSuite(unittest.TestCase):
    """Meta-test to ensure all manager test modules can be imported and run"""

    def test_all_manager_test_modules_importable(self):
        """Test that all manager test modules can be imported"""
        # Test that the suite creation works (which imports the modules)
        try:
            suite = create_manager_test_suite()
            self.assertIsInstance(suite, unittest.TestSuite)
        except ImportError as e:
            self.fail(f"Failed to import manager test modules: {e}")

    def test_manager_test_suite_creation(self):
        """Test that the manager test suite can be created"""
        suite = create_manager_test_suite()
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertGreater(suite.countTestCases(), 0)

    def test_manager_test_categories(self):
        """Test that all test categories are represented"""
        suite = create_manager_test_suite()

        # Verify suite has tests
        total_tests = suite.countTestCases()
        self.assertGreater(total_tests, 0, "Test suite should contain tests")

        # Verify minimum expected test count (basic sanity check)
        self.assertGreaterEqual(
            total_tests, 3, "Should have at least 3 test categories"
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run-suite":
        # Run the complete manager test suite
        success = run_manager_tests()
        sys.exit(0 if success else 1)
    else:
        # Run the meta-tests
        unittest.main()
