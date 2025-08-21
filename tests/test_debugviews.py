import unittest
from unittest.mock import Mock, patch, MagicMock
import json

from explainshell.web import debugviews, app
from explainshell import store, manager


class TestDebugViews(unittest.TestCase):
    """Comprehensive tests for debugviews.py"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        
    def tearDown(self):
        pass

    @patch('explainshell.web.debugviews.store.store')
    @patch('explainshell.web.debugviews.render_template')
    def test_debug_route(self, mock_render, mock_store_class):
        """Test debug route functionality"""
        with self.app.test_request_context('/debug'):
            # Create mock store and manpages
            mock_store = Mock()
            mock_store_class.return_value = mock_store
            
            # Create mock manpages
            mock_mp1 = Mock()
            mock_mp1.name = "ls"
            mock_mp1.synopsis = "list directory contents"
            mock_mp1.options = [Mock(__str__=lambda x: "-l"), Mock(__str__=lambda x: "-a")]
            
            mock_mp2 = Mock()
            mock_mp2.name = "cat"
            mock_mp2.synopsis = None
            mock_mp2.options = [Mock(__str__=lambda x: "-n")]
            
            mock_store.__iter__ = Mock(return_value=iter([mock_mp1, mock_mp2]))
            
            mock_render.return_value = "debug page"
            
            result = debugviews.debug()
            
            # Verify store creation
            mock_store_class.assert_called_once_with("explainshell", unittest.mock.ANY)
            
            # Verify render_template call
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], "debug.html")
            
            # Check the data structure
            d = kwargs['d']
            self.assertIn('manpages', d)
            self.assertEqual(len(d['manpages']), 2)
            
            # Verify manpages are sorted by name
            names = [mp['name'] for mp in d['manpages']]
            self.assertEqual(names, sorted(names, key=str.lower))
            
            self.assertEqual(result, "debug page")

    @patch('explainshell.web.debugviews.store.store')
    @patch('explainshell.web.debugviews.render_template')
    def test_debug_route_long_synopsis(self, mock_render, mock_store_class):
        """Test debug route with long synopsis truncation"""
        with self.app.test_request_context('/debug'):
            mock_store = Mock()
            mock_store_class.return_value = mock_store
            
            # Create manpage with long synopsis
            mock_mp = Mock()
            mock_mp.name = "test"
            mock_mp.synopsis = "a" * 50  # 50 characters
            mock_mp.options = []
            
            mock_store.__iter__ = Mock(return_value=iter([mock_mp]))
            mock_render.return_value = "debug page"
            
            debugviews.debug()
            
            # Check synopsis truncation
            args, kwargs = mock_render.call_args
            d = kwargs['d']
            self.assertEqual(len(d['manpages'][0]['synopsis']), 20)

    def test_convertvalue_list(self):
        """Test _convertvalue with list input"""
        result = debugviews._convertvalue([" item1 ", " item2 "])
        self.assertEqual(result, ["item1", "item2"])

    def test_convertvalue_true_string(self):
        """Test _convertvalue with 'true' string"""
        result = debugviews._convertvalue("true")
        self.assertTrue(result)
        
        result = debugviews._convertvalue("TRUE")
        self.assertTrue(result)

    def test_convertvalue_regular_string(self):
        """Test _convertvalue with regular string"""
        result = debugviews._convertvalue("  test value  ")
        self.assertEqual(result, "test value")

    def test_convertvalue_empty_string(self):
        """Test _convertvalue with empty string"""
        result = debugviews._convertvalue("")
        self.assertFalse(result)

    def test_convertvalue_none(self):
        """Test _convertvalue with None"""
        # _convertvalue expects string input, None will cause AttributeError
        with self.assertRaises(AttributeError):
            debugviews._convertvalue(None)

    @patch('explainshell.web.debugviews.store.paragraph')
    @patch('explainshell.web.debugviews.store.option')
    def test_process_paragraphs_basic(self, mock_option, mock_paragraph):
        """Test _process_paragraphs with basic paragraph"""
        mock_paragraph.return_value = Mock()
        
        paragraphs_data = [{
            "idx": 0,
            "text": "test paragraph",
            "section": "DESCRIPTION",
            "is_option": False,
            "short": [],
            "long": [],
            "expectsarg": "",
            "nestedcommand": "",
            "argument": ""
        }]
        
        result = debugviews._process_paragraphs(paragraphs_data)
        
        mock_paragraph.assert_called_once_with(0, "test paragraph", "DESCRIPTION", False)
        mock_option.assert_not_called()
        self.assertEqual(len(result), 1)

    @patch('explainshell.web.debugviews.store.paragraph')
    @patch('explainshell.web.debugviews.store.option')
    def test_process_paragraphs_option(self, mock_option, mock_paragraph):
        """Test _process_paragraphs with option paragraph"""
        mock_p = Mock()
        mock_paragraph.return_value = mock_p
        mock_option.return_value = Mock()
        
        paragraphs_data = [{
            "idx": 1,
            "text": "-l option",
            "section": "OPTIONS",
            "is_option": True,
            "short": ["-l"],
            "long": ["--list"],
            "expectsarg": "true",
            "nestedcommand": "",
            "argument": "FORMAT"
        }]
        
        result = debugviews._process_paragraphs(paragraphs_data)
        
        mock_paragraph.assert_called_once_with(1, "-l option", "OPTIONS", True)
        mock_option.assert_called_once_with(
            mock_p, ["-l"], ["--list"], True, "FORMAT", False
        )
        self.assertEqual(len(result), 1)

    @patch('explainshell.web.debugviews.store.paragraph')
    @patch('explainshell.web.debugviews.logger')
    @patch('explainshell.web.debugviews.abort')
    def test_process_paragraphs_invalid_nestedcommand(self, mock_abort, mock_logger, mock_paragraph):
        """Test _process_paragraphs with invalid nestedcommand"""
        mock_paragraph.return_value = Mock()
        
        paragraphs_data = [{
            "idx": 0,
            "text": "test",
            "section": "TEST",
            "is_option": False,
            "short": [],
            "long": [],
            "expectsarg": "",
            "nestedcommand": 123,  # Invalid type - will cause AttributeError in _convertvalue
            "argument": ""
        }]
        
        # This will raise AttributeError before reaching the logger/abort
        with self.assertRaises(AttributeError):
            debugviews._process_paragraphs(paragraphs_data)

    @patch('explainshell.web.debugviews.store.paragraph')
    @patch('explainshell.web.debugviews.store.option')
    def test_process_paragraphs_nestedcommand_conversions(self, mock_option, mock_paragraph):
        """Test _process_paragraphs nestedcommand type conversions"""
        mock_p = Mock()
        mock_paragraph.return_value = mock_p
        mock_option.return_value = Mock()
        
        # Test list conversion
        paragraphs_data = [{
            "idx": 0,
            "text": "test",
            "section": "TEST",
            "is_option": True,
            "short": ["-t"],
            "long": [],
            "expectsarg": "",
            "nestedcommand": ["item"],  # List should become True
            "argument": ""
        }]
        
        debugviews._process_paragraphs(paragraphs_data)
        
        mock_option.assert_called_with(mock_p, ["-t"], [], False, None, True)

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews.render_template')
    @patch('explainshell.web.debugviews.helpers.convertparagraphs')
    def test_tag_get_request(self, mock_convert, mock_render, mock_manager_class):
        """Test tag route with GET request"""
        with self.app.test_request_context('/debug/tag/test.1'):
            # Setup mocks
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_manpage = Mock()
            mock_manpage.paragraphs = []
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            
            mock_render.return_value = "tagger page"
            
            result = debugviews.tag("test.1")
            
            # Verify manager creation
            mock_manager_class.assert_called_once_with(
                unittest.mock.ANY, "explainshell", [], False, False
            )
            
            # Verify manpage lookup
            mock_manager.store.findmanpage.assert_called_once_with("test.1")
            
            # Verify paragraph conversion
            mock_convert.assert_called_once_with(mock_manpage)
            
            # Verify template rendering
            mock_render.assert_called_once_with("tagger.html", m=mock_manpage)
            
            self.assertEqual(result, "tagger page")

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews.render_template')
    @patch('explainshell.web.debugviews.helpers.convertparagraphs')
    def test_tag_get_with_option_paragraphs(self, mock_convert, mock_render, mock_manager_class):
        """Test tag route GET with option paragraphs"""
        with self.app.test_request_context('/debug/tag/test.1'):
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            # Create option paragraph with list expectsarg
            mock_option = Mock(spec=store.option)
            mock_option.expectsarg = ["arg1", "arg2"]
            mock_option.nestedcommand = [True]
            
            mock_manpage = Mock()
            mock_manpage.paragraphs = [mock_option]
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            
            mock_render.return_value = "tagger page"
            
            debugviews.tag("test.1")
            
            # Verify expectsarg list is joined
            self.assertEqual(mock_option.expectsarg, "arg1, arg2")
            # Verify nestedcommand list is converted to bool
            self.assertTrue(mock_option.nestedcommand)

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews.redirect')
    @patch('explainshell.web.debugviews.url_for')
    @patch('explainshell.web.debugviews._process_paragraphs')
    def test_tag_post_success(self, mock_process, mock_url_for, mock_redirect, mock_manager_class):
        """Test tag route with successful POST request"""
        paragraphs_json = json.dumps([{
            "idx": 0,
            "text": "test",
            "section": "TEST",
            "is_option": False,
            "short": [],
            "long": [],
            "expectsarg": "",
            "nestedcommand": "",
            "argument": ""
        }])
        
        with self.app.test_request_context('/debug/tag/test.1', method='POST', 
                                         data={'paragraphs': paragraphs_json, 'nestedcommand': 'true'}):
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_manpage = Mock()
            mock_manpage.name = "test"
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            
            mock_processed_paragraphs = [Mock()]
            mock_process.return_value = mock_processed_paragraphs
            
            mock_edited_manpage = Mock()
            mock_edited_manpage.name = "test"
            mock_manager.edit.return_value = mock_edited_manpage
            
            mock_url_for.return_value = "/explain?cmd=test"
            mock_redirect.return_value = "redirect response"
            
            result = debugviews.tag("test.1")
            
            # Verify paragraph processing
            mock_process.assert_called_once()
            
            # Verify nestedcommand setting
            self.assertTrue(mock_manpage.nestedcommand)
            
            # Verify edit call
            mock_manager.edit.assert_called_once_with(mock_manpage, mock_processed_paragraphs)
            
            # Verify redirect
            mock_url_for.assert_called_once_with("explain", cmd="test")
            mock_redirect.assert_called_once_with("/explain?cmd=test")
            
            self.assertEqual(result, "redirect response")

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews.abort')
    @patch('explainshell.web.debugviews._process_paragraphs')
    def test_tag_post_edit_failure(self, mock_process, mock_abort, mock_manager_class):
        """Test tag route with POST request edit failure"""
        paragraphs_json = json.dumps([])
        
        with self.app.test_request_context('/debug/tag/test.1', method='POST', 
                                         data={'paragraphs': paragraphs_json}):
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_manpage = Mock()
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            
            mock_process.return_value = []
            mock_manager.edit.return_value = None  # Edit failure
            
            debugviews.tag("test.1")
            
            mock_abort.assert_called_once_with(503)

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews._process_paragraphs')
    def test_tag_post_nestedcommand_false(self, mock_process, mock_manager_class):
        """Test tag route POST with nestedcommand false"""
        paragraphs_json = json.dumps([])
        
        with self.app.test_request_context('/debug/tag/test.1', method='POST', 
                                         data={'paragraphs': paragraphs_json, 'nestedcommand': 'false'}):
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_manpage = Mock()
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            mock_manager.edit.return_value = mock_manpage
            
            mock_process.return_value = []
            
            with patch('explainshell.web.debugviews.redirect'):
                debugviews.tag("test.1")
            
            # Verify nestedcommand is set to False
            self.assertFalse(mock_manpage.nestedcommand)

    @patch('explainshell.web.debugviews.manager.manager')
    @patch('explainshell.web.debugviews._process_paragraphs')
    def test_tag_post_no_nestedcommand_param(self, mock_process, mock_manager_class):
        """Test tag route POST without nestedcommand parameter"""
        paragraphs_json = json.dumps([])
        
        with self.app.test_request_context('/debug/tag/test.1', method='POST', 
                                         data={'paragraphs': paragraphs_json}):
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_manpage = Mock()
            mock_manager.store.findmanpage.return_value = [mock_manpage]
            mock_manager.edit.return_value = mock_manpage
            
            mock_process.return_value = []
            
            with patch('explainshell.web.debugviews.redirect'):
                debugviews.tag("test.1")
            
            # Verify nestedcommand defaults to False
            self.assertFalse(mock_manpage.nestedcommand)


class TestDebugViewsIntegration(unittest.TestCase):
    """Integration tests for debugviews.py"""
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        
    def tearDown(self):
        pass

    def test_convertvalue_edge_cases(self):
        """Test _convertvalue with edge cases"""
        # Test whitespace-only string
        result = debugviews._convertvalue("   ")
        self.assertFalse(result)
        
        # Test mixed case true
        result = debugviews._convertvalue("True")
        self.assertTrue(result)
        
        # Test empty list
        result = debugviews._convertvalue([])
        self.assertEqual(result, [])

    @patch('explainshell.web.debugviews.store.paragraph')
    @patch('explainshell.web.debugviews.store.option')
    def test_process_paragraphs_complex_scenario(self, mock_option, mock_paragraph):
        """Test _process_paragraphs with complex mixed scenarios"""
        mock_p1 = Mock()
        mock_p2 = Mock()
        mock_paragraph.side_effect = [mock_p1, mock_p2]
        mock_option.return_value = Mock()
        
        paragraphs_data = [
            {
                "idx": 0,
                "text": "regular paragraph",
                "section": "DESCRIPTION",
                "is_option": False,
                "short": [],
                "long": [],
                "expectsarg": "",
                "nestedcommand": "  true  ",  # String with whitespace
                "argument": ""
            },
            {
                "idx": 1,
                "text": "-v option",
                "section": "OPTIONS",
                "is_option": True,
                "short": [" -v ", " -V "],  # With whitespace
                "long": [" --verbose "],
                "expectsarg": ["arg1", "arg2"],  # List
                "nestedcommand": [],  # Empty list
                "argument": "  LEVEL  "  # With whitespace
            }
        ]
        
        result = debugviews._process_paragraphs(paragraphs_data)
        
        # Verify both paragraphs processed
        self.assertEqual(len(result), 2)
        
        # Verify first paragraph (regular)
        mock_paragraph.assert_any_call(0, "regular paragraph", "DESCRIPTION", False)
        
        # Verify second paragraph (option)
        mock_paragraph.assert_any_call(1, "-v option", "OPTIONS", True)
        mock_option.assert_called_once_with(
            mock_p2, ["-v", "-V"], ["--verbose"], ["arg1", "arg2"], "  LEVEL  ", False
        )

    @patch('explainshell.web.debugviews.store.store')
    def test_debug_route_empty_store(self, mock_store_class):
        """Test debug route with empty store"""
        with self.app.test_request_context('/debug'):
            mock_store = Mock()
            mock_store_class.return_value = mock_store
            mock_store.__iter__ = Mock(return_value=iter([]))
            
            with patch('explainshell.web.debugviews.render_template') as mock_render:
                mock_render.return_value = "empty debug page"
                
                result = debugviews.debug()
                
                args, kwargs = mock_render.call_args
                d = kwargs['d']
                self.assertEqual(len(d['manpages']), 0)
                self.assertEqual(result, "empty debug page")


if __name__ == "__main__":
    unittest.main()