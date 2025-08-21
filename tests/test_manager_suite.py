import unittest
import sys
import os


def create_manager_test_suite():
    """Create a comprehensive test suite for manager.py"""
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
    from .test_comprehensive import TestComprehensive
    from .test_matcher import test_matcher
    from .test_views import TestViews, TestViewsIntegration
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Core functionality tests
    suite.addTest(loader.loadTestsFromTestCase(TestComprehensive))
    suite.addTest(loader.loadTestsFromTestCase(test_matcher))
    suite.addTest(loader.loadTestsFromTestCase(TestViews))
    suite.addTest(loader.loadTestsFromTestCase(TestViewsIntegration))
    
    # Manager-specific tests
    suite.addTest(loader.loadTestsFromTestCase(TestManagerExpanded))
    suite.addTest(loader.loadTestsFromTestCase(TestManagerIntegration))
    suite.addTest(loader.loadTestsFromTestCase(TestManagerEdgeCases))
    suite.addTest(loader.loadTestsFromTestCase(TestManagerPerformance))

    # Optional stress tests
    if "--include-stress" in sys.argv:
        suite.addTest(loader.loadTestsFromTestCase(TestManagerStress))

    return suite


def create_full_test_suite():
    """Create comprehensive test suite for entire explainshell package"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add manager test suite
    suite.addTest(create_manager_test_suite())
    
    # Add other test modules if they exist
    test_modules = [
        'test_comprehensive',
        'test_matcher',
        'test_views', 
        'test_options',
        'test_store',
        'test_util',
        'test_features',
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(f'{module_name}', fromlist=[module_name])
            suite.addTest(loader.loadTestsFromModule(module))
        except (ImportError, AttributeError):
            continue  # Skip missing modules
    
    return suite

def run_manager_tests():
    """Run all manager tests with detailed output"""
    suite = create_manager_test_suite()
    return _run_test_suite(suite, "Manager Test Suite")

def run_full_tests():
    """Run complete test suite with detailed output"""
    suite = create_full_test_suite()
    return _run_test_suite(suite, "Complete Test Suite")

def _run_test_suite(suite, suite_name):
    """Helper to run test suite with consistent output"""
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast="--failfast" in sys.argv,
        buffer="--buffer" in sys.argv,
    )

    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")
    
    result = runner.run(suite)

    # Print detailed summary
    print(f"\n{'='*60}")
    print(f"{suite_name} Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")

    if result.failures:
        print(f"\nFailures ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"  {i}. {test}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"  {i}. {test}")
    
    if result.skipped and hasattr(result, 'skipped'):
        print(f"\nSkipped ({len(result.skipped)}):")
        for i, (test, reason) in enumerate(result.skipped, 1):
            print(f"  {i}. {test} - {reason}")

    return result.wasSuccessful()


class TestManagerTestSuite(unittest.TestCase):
    """Meta-test to ensure all test modules can be imported and run"""

    def test_manager_test_suite_creation(self):
        """Test that the manager test suite can be created"""
        suite = create_manager_test_suite()
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertGreater(suite.countTestCases(), 0)

    def test_full_test_suite_creation(self):
        """Test that the full test suite can be created"""
        suite = create_full_test_suite()
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertGreater(suite.countTestCases(), 0)

    def test_manager_test_categories(self):
        """Test that all manager test categories are represented"""
        suite = create_manager_test_suite()
        total_tests = suite.countTestCases()
        self.assertGreater(total_tests, 0, "Manager test suite should contain tests")
        self.assertGreaterEqual(total_tests, 5, "Should have at least 5 test categories")

    def test_comprehensive_coverage(self):
        """Test that comprehensive test coverage is available"""
        full_suite = create_full_test_suite()
        manager_suite = create_manager_test_suite()
        
        full_count = full_suite.countTestCases()
        manager_count = manager_suite.countTestCases()
        
        # Full suite should have at least as many tests as manager suite
        self.assertGreaterEqual(full_count, manager_count)
        
    def test_test_discovery(self):
        """Test that test discovery works for available modules"""
        # Test that we can discover tests in the current package
        loader = unittest.TestLoader()
        discovered_suite = loader.discover('.', pattern='test_*.py')
        self.assertIsInstance(discovered_suite, unittest.TestSuite)
        
    def test_suite_execution_modes(self):
        """Test different execution modes work"""
        # Test basic suite creation
        basic_suite = create_manager_test_suite()
        self.assertGreater(basic_suite.countTestCases(), 0)
        
        # Test full suite creation  
        full_suite = create_full_test_suite()
        self.assertGreater(full_suite.countTestCases(), 0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "run-manager":
            # Run manager test suite only
            success = run_manager_tests()
            sys.exit(0 if success else 1)
        elif command == "run-full":
            # Run complete test suite
            success = run_full_tests()
            sys.exit(0 if success else 1)
        elif command == "run-suite":
            # Backward compatibility
            success = run_manager_tests()
            sys.exit(0 if success else 1)
        elif command == "help":
            print("Usage:")
            print("  python test_manager_suite.py run-manager  # Run manager tests only")
            print("  python test_manager_suite.py run-full     # Run all available tests")
            print("  python test_manager_suite.py run-suite    # Run manager tests (legacy)")
            print("  python test_manager_suite.py help         # Show this help")
            print("  python test_manager_suite.py              # Run meta-tests")
            print("\nOptions:")
            print("  --include-stress    # Include stress tests")
            print("  --failfast          # Stop on first failure")
            print("  --buffer            # Buffer stdout/stderr")
            sys.exit(0)
    
    # Run the meta-tests by default
    unittest.main()
