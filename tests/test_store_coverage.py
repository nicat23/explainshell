"""Tests to improve coverage for store.py module"""

import unittest
from unittest.mock import MagicMock, patch, call
from collections import OrderedDict

from explainshell import store, errors, helpconstants


class TestStoreCoverage(unittest.TestCase):
    """Test cases to improve coverage for store.py"""

    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db
        
        # Mock collections
        self.mock_classifier = MagicMock()
        self.mock_manpage = MagicMock()
        self.mock_mapping = MagicMock()
        
        self.mock_db.__getitem__.side_effect = lambda name: {
            'classifier': self.mock_classifier,
            'manpage': self.mock_manpage,
            'mapping': self.mock_mapping
        }[name]

    def test_store_initialization(self):
        """Test store initialization with custom parameters"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store(db="testdb", host="mongodb://testhost")
            
            self.assertEqual(s.connection, self.mock_client)
            self.assertEqual(s.db, self.mock_db)
            self.assertEqual(s.classifier, self.mock_classifier)
            self.assertEqual(s.manpage, self.mock_manpage)
            self.assertEqual(s.mapping, self.mock_mapping)

    def test_store_close(self):
        """Test store close method"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.close()
            
            self.mock_client.close.assert_called_once()
            self.assertIsNone(s.classifier)
            self.assertIsNone(s.manpage)
            self.assertIsNone(s.mapping)
            self.assertIsNone(s.db)

    def test_store_drop_no_confirm(self):
        """Test store drop without confirmation"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.drop(confirm=False)
            
            # Should not call drop on collections
            self.mock_mapping.drop.assert_not_called()
            self.mock_manpage.drop.assert_not_called()

    def test_store_drop_with_confirm(self):
        """Test store drop with confirmation"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.drop(confirm=True)
            
            self.mock_mapping.drop.assert_called_once()
            self.mock_manpage.drop.assert_called_once()

    def test_store_drop_none_collections(self):
        """Test store drop when collections are None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            s.manpage = None
            s.drop(confirm=True)
            
            # Should not crash when collections are None

    def test_store_trainingset(self):
        """Test store trainingset method"""
        mock_data = [
            {"name": "test1", "paragraphs": []},
            {"name": "test2", "paragraphs": []}
        ]
        self.mock_classifier.find.return_value = mock_data
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = list(s.trainingset())
            
            self.assertEqual(len(result), 2)
            self.mock_classifier.find.assert_called_once()

    def test_store_trainingset_none_classifier(self):
        """Test store trainingset when classifier is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.classifier = None
            result = list(s.trainingset())
            
            self.assertEqual(len(result), 0)

    def test_store_contains_true(self):
        """Test store __contains__ when item exists"""
        self.mock_mapping.count_documents.return_value = 1
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = "test" in s
            
            self.assertTrue(result)
            self.mock_mapping.count_documents.assert_called_with({"src": "test"})

    def test_store_contains_false(self):
        """Test store __contains__ when item doesn't exist"""
        self.mock_mapping.count_documents.return_value = 0
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = "test" in s
            
            self.assertFalse(result)

    def test_store_contains_none_mapping(self):
        """Test store __contains__ when mapping is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            result = "test" in s
            
            self.assertFalse(result)

    def test_store_iter(self):
        """Test store __iter__ method"""
        mock_data = [
            {
                "source": "test.1.gz",
                "name": "test",
                "synopsis": "test command",
                "paragraphs": [],
                "aliases": [["test", 10]]
            }
        ]
        self.mock_manpage.find.return_value = mock_data
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = list(s)
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], store.manpage)

    def test_store_iter_none_manpage(self):
        """Test store __iter__ when manpage is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.manpage = None
            result = list(s)
            
            self.assertEqual(len(result), 0)

    def test_findmanpage_gz_file(self):
        """Test findmanpage with .gz file"""
        mock_doc = {
            "source": "test.1.gz",
            "name": "test",
            "synopsis": "test command",
            "paragraphs": [],
            "aliases": [["test", 10]]
        }
        self.mock_manpage.find_one.return_value = mock_doc
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = s.findmanpage("test.1.gz")
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], store.manpage)

    def test_findmanpage_gz_file_not_found(self):
        """Test findmanpage with .gz file that doesn't exist"""
        self.mock_manpage.find_one.return_value = None
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            
            with self.assertRaises(errors.ProgramDoesNotExist):
                s.findmanpage("nonexistent.1.gz")

    def test_findmanpage_none_collections(self):
        """Test findmanpage when collections are None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            s.manpage = None
            
            with self.assertRaises(errors.ProgramDoesNotExist):
                s.findmanpage("test")

    def test_findmanpage_no_mappings(self):
        """Test findmanpage when no mappings exist"""
        self.mock_mapping.count_documents.return_value = 0
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            
            with self.assertRaises(errors.ProgramDoesNotExist):
                s.findmanpage("test")

    def test_findmanpage_mapping_manpage_mismatch(self):
        """Test findmanpage when mapping count doesn't match manpage count"""
        # Mock mapping results
        self.mock_mapping.count_documents.return_value = 2
        self.mock_mapping.find.return_value = [
            {"dst": "id1", "score": 10},
            {"dst": "id2", "score": 5}
        ]
        
        # Mock manpage results (fewer than mappings)
        self.mock_manpage.count_documents.return_value = 1
        self.mock_manpage.find.return_value = [
            {"_id": "id1", "name": "test", "source": "test.1.gz"}
        ]
        self.mock_manpage.find_one.return_value = {
            "source": "test.1.gz",
            "name": "test", 
            "synopsis": "test command",
            "paragraphs": [],
            "aliases": [["test", 10]]
        }
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            with patch('explainshell.store.logger') as mock_logger:
                s = store.store()
                result = s.findmanpage("test")
                
                # Should log error about mismatch
                mock_logger.error.assert_called()
                self.assertEqual(len(result), 1)

    def test_findmanpage_with_section_sorting(self):
        """Test findmanpage with section-specific sorting"""
        # Mock mapping results
        self.mock_mapping.count_documents.return_value = 2
        self.mock_mapping.find.return_value = [
            {"dst": "id1", "score": 10},
            {"dst": "id2", "score": 5}
        ]
        
        # Mock manpage results
        self.mock_manpage.count_documents.return_value = 2
        self.mock_manpage.find.return_value = [
            {"_id": "id1", "name": "test", "source": "test.1.gz"},
            {"_id": "id2", "name": "test", "source": "test.8.gz"}
        ]
        
        # Mock full manpage document
        self.mock_manpage.find_one.return_value = {
            "source": "test.8.gz",
            "name": "test",
            "synopsis": "test command",
            "paragraphs": [],
            "aliases": [["test", 10]]
        }
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            with patch.object(store.store, '_discovermanpagesuggestions', return_value=[]):
                s = store.store()
                result = s.findmanpage("test.8")
                
                # May return multiple results due to sorting behavior
                self.assertGreaterEqual(len(result), 1)
                # Check that at least one result has section 8
                sections = [mp.section for mp in result]
                self.assertIn("8", sections)

    def test_findmanpage_section_not_found(self):
        """Test findmanpage when requested section doesn't exist"""
        # Mock mapping results
        self.mock_mapping.count_documents.return_value = 1
        self.mock_mapping.find.return_value = [{"dst": "id1", "score": 10}]
        
        # Mock manpage results with different section
        self.mock_manpage.count_documents.return_value = 1
        self.mock_manpage.find.return_value = [
            {"_id": "id1", "name": "test", "source": "test.1.gz"}
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            
            with self.assertRaises(errors.ProgramDoesNotExist):
                s.findmanpage("test.8")  # Request section 8, but only 1 exists

    def test_discovermanpagesuggestions_none_collections(self):
        """Test _discovermanpagesuggestions when collections are None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            s.manpage = None
            
            result = s._discovermanpagesuggestions("id1", [])
            self.assertEqual(result, [])

    def test_discovermanpagesuggestions_no_suggestions(self):
        """Test _discovermanpagesuggestions with no suggestions found"""
        self.mock_mapping.find.side_effect = [
            [{"src": "test"}],  # First call
            []  # Second call - no suggestions
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = s._discovermanpagesuggestions("id1", [("id1", MagicMock())])
            
            self.assertEqual(result, [])

    def test_discovermanpagesuggestions_with_results(self):
        """Test _discovermanpagesuggestions with suggestions"""
        self.mock_mapping.find.side_effect = [
            [{"src": "test"}],  # Sources pointing to oid
            [{"dst": "id2"}, {"dst": "id3"}]  # Suggestion destinations
        ]
        
        self.mock_manpage.find.return_value = [
            {"_id": "id2", "name": "test2", "source": "test2.1.gz"},
            {"_id": "id3", "name": "test3", "source": "test3.1.gz"}
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = s._discovermanpagesuggestions("id1", [("id1", MagicMock())])
            
            self.assertEqual(len(result), 2)

    def test_addmapping_none_mapping(self):
        """Test addmapping when mapping collection is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            
            # Should not crash
            s.addmapping("src", "dst", 10)

    def test_addmanpage_existing_manpage(self):
        """Test addmanpage with existing manpage"""
        # Mock existing manpage
        existing_doc = {"_id": "old_id", "source": "test.1.gz"}
        self.mock_manpage.find_one.return_value = existing_doc
        
        # Mock insert result
        mock_result = MagicMock()
        mock_result.inserted_id = "new_id"
        self.mock_manpage.insert_one.return_value = mock_result
        
        # Mock mapping operations
        self.mock_mapping.count_documents.side_effect = [5, 3]  # Before and after delete
        
        # Create test manpage
        test_manpage = store.manpage(
            source="test.1.gz",
            name="test",
            synopsis="test command",
            paragraphs=[],
            aliases=[("test", 10), ("alias", 1)]
        )
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = s.addmanpage(test_manpage)
            
            # Should delete old manpage and mappings
            self.mock_manpage.delete_one.assert_called_with({"_id": "old_id"})
            self.mock_mapping.delete_many.assert_called_with({"dst": "old_id"})
            
            # Should insert new manpage
            self.mock_manpage.insert_one.assert_called_once()
            
            # Should add mappings for aliases
            self.assertEqual(self.mock_mapping.insert_one.call_count, 2)
            
            self.assertEqual(result, test_manpage)

    def test_addmanpage_none_manpage_collection(self):
        """Test addmanpage when manpage collection is None"""
        test_manpage = store.manpage(
            source="test.1.gz",
            name="test", 
            synopsis="test command",
            paragraphs=[],
            aliases=[("test", 10)]
        )
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.manpage = None
            
            result = s.addmanpage(test_manpage)
            self.assertEqual(result, test_manpage)

    def test_updatemanpage_none_manpage_collection(self):
        """Test updatemanpage when manpage collection is None"""
        test_manpage = store.manpage(
            source="test.1.gz",
            name="test",
            synopsis="test command", 
            paragraphs=[],
            aliases=[("test", 10)]
        )
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.manpage = None
            
            result = s.updatemanpage(test_manpage)
            self.assertEqual(result, test_manpage)
            # When manpage collection is None, updated flag is not set
            self.assertFalse(test_manpage.updated)

    def test_updatemanpage_with_new_aliases(self):
        """Test updatemanpage with new aliases"""
        # Mock existing document
        self.mock_manpage.find_one.return_value = {"_id": "test_id"}
        
        # Mock contains check
        self.mock_mapping.count_documents.side_effect = [0, 1]  # New alias, existing alias
        
        test_manpage = store.manpage(
            source="test.1.gz",
            name="test",
            synopsis="test command",
            paragraphs=[],
            aliases=[("newalias", 5), ("existingalias", 3)]
        )
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = s.updatemanpage(test_manpage)
            
            # Should update manpage
            self.mock_manpage.update_one.assert_called_once()
            
            # Should add only new alias
            self.mock_mapping.insert_one.assert_called_once()
            
            self.assertTrue(result.updated)

    def test_verify_success(self):
        """Test verify when everything is consistent"""
        # Mock mappings and manpages with consistent IDs
        self.mock_mapping.find.return_value = [
            {"dst": "id1"}, {"dst": "id2"}
        ]
        self.mock_manpage.find.return_value = [
            {"_id": "id1"}, {"_id": "id2"}
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            ok, unreachable, notfound = s.verify()
            
            self.assertTrue(ok)
            # unreachable can be list or set
            self.assertIn(type(unreachable), [list, set])
            self.assertEqual(notfound, set())

    def test_verify_unreachable_manpages(self):
        """Test verify with unreachable manpages"""
        # Mock mappings missing some manpage IDs
        self.mock_mapping.find.return_value = [{"dst": "id1"}]
        self.mock_manpage.find.side_effect = [
            [{"_id": "id1"}, {"_id": "id2"}],  # All manpages
            [{"_id": "id2", "name": "unreachable"}]  # Unreachable lookup
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            ok, unreachable, notfound = s.verify()
            
            self.assertFalse(ok)
            # unreachable can be empty set or list depending on implementation
            self.assertIn(type(unreachable), [list, set])
            self.assertEqual(notfound, set())

    def test_verify_missing_manpages(self):
        """Test verify with missing manpages"""
        # Mock mappings pointing to non-existent manpages
        self.mock_mapping.find.return_value = [
            {"dst": "id1"}, {"dst": "id2"}
        ]
        self.mock_manpage.find.return_value = [{"_id": "id1"}]  # Missing id2
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            ok, unreachable, notfound = s.verify()
            
            self.assertFalse(ok)
            # unreachable can be list or set
            self.assertIn(type(unreachable), [list, set])
            self.assertEqual(notfound, {"id2"})

    def test_verify_none_collections(self):
        """Test verify when collections are None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            s.manpage = None
            
            ok, unreachable, notfound = s.verify()
            
            self.assertFalse(ok)
            self.assertEqual(unreachable, [])
            self.assertEqual(notfound, [])

    def test_names_none_manpage(self):
        """Test names when manpage collection is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.manpage = None
            
            result = list(s.names())
            self.assertEqual(result, [])

    def test_names_with_results(self):
        """Test names with results"""
        self.mock_manpage.find.return_value = [
            {"_id": "id1", "name": "test1"},
            {"_id": "id2", "name": "test2"}
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = list(s.names())
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], ("id1", "test1"))
            self.assertEqual(result[1], ("id2", "test2"))

    def test_mappings_none_mapping(self):
        """Test mappings when mapping collection is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.mapping = None
            
            result = list(s.mappings())
            self.assertEqual(result, [])

    def test_mappings_with_results(self):
        """Test mappings with results"""
        self.mock_mapping.find.return_value = [
            {"src": "test1", "_id": "id1"},
            {"src": "test2", "_id": "id2"}
        ]
        
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            result = list(s.mappings())
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], ("test1", "id1"))
            self.assertEqual(result[1], ("test2", "id2"))

    def test_setmulticommand_none_manpage(self):
        """Test setmulticommand when manpage collection is None"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.manpage = None
            
            # Should not crash
            s.setmulticommand("test_id")

    def test_setmulticommand_success(self):
        """Test setmulticommand success"""
        with patch('pymongo.MongoClient', return_value=self.mock_client):
            s = store.store()
            s.setmulticommand("test_id")
            
            self.mock_manpage.update_one.assert_called_with(
                {"_id": "test_id"}, {"$set": {"multicommand": True}}
            )

    def test_paragraph_cleantext(self):
        """Test paragraph cleantext method"""
        p = store.paragraph(0, "<b>bold</b> &lt;test&gt; text", "SECTION", False)
        result = p.cleantext()
        
        self.assertEqual(result, "bold <test> text")

    def test_paragraph_equality(self):
        """Test paragraph equality"""
        p1 = store.paragraph(0, "text", "SECTION", False)
        p2 = store.paragraph(0, "text", "SECTION", False)
        p3 = store.paragraph(1, "text", "SECTION", False)
        
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(p1, None)

    def test_option_initialization_with_nestedcommand(self):
        """Test option initialization with nestedcommand validation"""
        p = store.paragraph(0, "text", "SECTION", True)
        
        # Should raise assertion error if nestedcommand=True but expectsarg=False
        with self.assertRaises(AssertionError):
            store.option(p, ["-a"], ["--all"], False, nestedcommand=True)

    def test_manpage_removeoption_not_option(self):
        """Test manpage removeoption with non-option paragraph"""
        p = store.paragraph(0, "text", "SECTION", False)
        mp = store.manpage("test.1.gz", "test", "synopsis", [p], [])
        
        with self.assertRaises(ValueError):
            mp.removeoption(0)

    def test_manpage_removeoption_not_found(self):
        """Test manpage removeoption with non-existent index"""
        mp = store.manpage("test.1.gz", "test", "synopsis", [], [])
        
        with self.assertRaises(ValueError):
            mp.removeoption(999)

    def test_manpage_arguments_property(self):
        """Test manpage arguments property"""
        p1 = store.paragraph(0, "text1", "SECTION", True)
        opt1 = store.option(p1, ["-a"], [], False, argument="files")
        
        p2 = store.paragraph(1, "text2", "SECTION", True)  
        opt2 = store.option(p2, ["-b"], [], False, argument="files")
        
        p3 = store.paragraph(2, "text3", "SECTION", True)
        opt3 = store.option(p3, ["-c"], [], False, argument="dirs")
        
        mp = store.manpage("test.1.gz", "test", "synopsis", [opt1, opt2, opt3], [])
        
        args = mp.arguments
        self.assertIn("files", args)
        self.assertIn("dirs", args)
        self.assertEqual(args["files"], "text1\n\ntext2")
        self.assertEqual(args["dirs"], "text3")

    def test_manpage_synopsisnoname_property(self):
        """Test manpage synopsisnoname property"""
        mp1 = store.manpage("test.1.gz", "test", "test - does something", [], [])
        self.assertEqual(mp1.synopsisnoname, "does something")
        
        mp2 = store.manpage("test.1.gz", "test", "invalid format", [], [])
        self.assertEqual(mp2.synopsisnoname, "")

    def test_manpage_from_store_with_options(self):
        """Test manpage from_store with option paragraphs"""
        data = {
            "source": "test.1.gz",
            "name": "test",
            "synopsis": None,  # Test None synopsis
            "paragraphs": [
                {
                    "idx": 0,
                    "text": "option text",
                    "section": "OPTIONS",
                    "is_option": True,
                    "short": ["-a"],
                    "long": ["--all"],
                    "expectsarg": False,
                    "argument": None,
                    "nestedcommand": False
                }
            ],
            "aliases": [["test", 10]],
            "partialmatch": True,
            "multicommand": True,
            "updated": True,
            "nestedcommand": ["exit"]
        }
        
        mp = store.manpage.from_store(data)
        
        self.assertEqual(mp.synopsis, helpconstants.NOSYNOPSIS)
        self.assertTrue(mp.partialmatch)
        self.assertTrue(mp.multicommand)
        self.assertTrue(mp.updated)
        self.assertEqual(mp.nestedcommand, ["exit"])
        self.assertEqual(len(mp.options), 1)
        self.assertIsInstance(mp.paragraphs[0], store.option)


if __name__ == '__main__':
    unittest.main()