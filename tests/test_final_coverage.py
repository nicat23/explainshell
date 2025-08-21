import unittest
from explainshell.util import propertycache


class TestFinalCoverage(unittest.TestCase):
    def test_propertycache_descriptor(self):
        # Test propertycache as descriptor with type parameter
        class TestClass:
            @propertycache
            def cached_prop(self):
                return "cached_value"

        obj = TestClass()
        descriptor = TestClass.__dict__["cached_prop"]

        # Test __get__ with type parameter
        result = descriptor.__get__(obj, TestClass)
        self.assertEqual(result, "cached_value")

        # Test that value is cached
        self.assertEqual(obj.cached_prop, "cached_value")

    def test_propertycache_cachevalue(self):
        # Test propertycache cachevalue method
        def dummy_func(self):
            return "test"

        cache = propertycache(dummy_func)

        class TestObj:
            pass

        obj = TestObj()
        cache.cachevalue(obj, "cached")
        self.assertEqual(getattr(obj, dummy_func.__name__), "cached")
