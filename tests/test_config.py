import unittest
import explainshell.config as config


class TestConfig(unittest.TestCase):
    def test_config_has_mongo_uri(self):
        self.assertTrue(hasattr(config, 'MONGO_URI'))

    def test_config_has_debug(self):
        self.assertTrue(hasattr(config, 'DEBUG'))

    def test_config_has_manpage_dir(self):
        self.assertTrue(hasattr(config, 'MANPAGEDIR'))

    def test_mongo_uri_is_string(self):
        self.assertIsInstance(config.MONGO_URI, str)

    def test_debug_is_boolean(self):
        self.assertIsInstance(config.DEBUG, bool)

    def test_manpage_dir_is_string(self):
        self.assertIsInstance(config.MANPAGEDIR, str)