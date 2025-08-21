import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell import store, errors, helpconstants


class TestParagraph(unittest.TestCase):
    """Tests for paragraph class"""

    def test_paragraph_init(self):
        """Test paragraph initialization"""
        p = store.paragraph(1, "test text", "DESCRIPTION", True)
        self.assertEqual(p.idx, 1)
        self.assertEqual(p.text, "test text")
        self.assertEqual(p.section, "DESCRIPTION")
        self.assertTrue(p.is_option)

    def test_paragraph_cleantext(self):
        """Test paragraph cleantext method"""
        p = store.paragraph(1, "text with <b>tags</b> and &lt;symbols&gt;", "DESC", False)
        cleaned = p.cleantext()
        self.assertEqual(cleaned, "text with tags and <symbols>")

    def test_paragraph_cleantext_complex(self):
        """Test cleantext with complex HTML"""
        p = store.paragraph(1, "<div>test</div> &lt;arg&gt; <span>more</span>", "DESC", False)
        cleaned = p.cleantext()
        self.assertEqual(cleaned, "test <arg> more")

    def test_paragraph_from_store(self):
        """Test paragraph from_store class method"""
        data = {
            "idx": 2,
            "text": "stored text",
            "section": "OPTIONS",
            "is_option": True
        }
        p = store.paragraph.from_store(data)
        self.assertEqual(p.idx, 2)
        self.assertEqual(p.text, "stored text")
        self.assertEqual(p.section, "OPTIONS")
        self.assertTrue(p.is_option)

    def test_paragraph_from_store_missing_idx(self):
        """Test paragraph from_store with missing idx"""
        data = {
            "text": "stored text",
            "section": "OPTIONS",
            "is_option": True
        }
        p = store.paragraph.from_store(data)
        self.assertEqual(p.idx, 0)  # Default value

    def test_paragraph_to_store(self):
        """Test paragraph to_store method"""
        p = store.paragraph(3, "test text", "EXAMPLES", False)
        data = p.to_store()
        expected = {
            "idx": 3,
            "text": "test text",
            "section": "EXAMPLES",
            "is_option": False
        }
        self.assertEqual(data, expected)

    def test_paragraph_repr(self):
        """Test paragraph __repr__ method"""
        p = store.paragraph(1, "This is a long paragraph with multiple lines\nSecond line", "DESC", True)
        repr_str = repr(p)
        self.assertIn("paragraph 1", repr_str)
        self.assertIn("DESC", repr_str)
        self.assertIn("This is a long", repr_str)

    def test_paragraph_repr_short_text(self):
        """Test paragraph __repr__ with short text"""
        p = store.paragraph(2, "Short", "DESC", False)
        repr_str = repr(p)
        self.assertIn("paragraph 2", repr_str)
        self.assertIn("Shor", repr_str)  # Text is truncated in repr

    def test_paragraph_equality(self):
        """Test paragraph equality"""
        p1 = store.paragraph(1, "text", "DESC", True)
        p2 = store.paragraph(1, "text", "DESC", True)
        p3 = store.paragraph(2, "text", "DESC", True)
        
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(p1, None)


class TestOption(unittest.TestCase):
    """Tests for option class"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_paragraph = store.paragraph(1, "-v verbose option", "OPTIONS", True)

    def test_option_init_basic(self):
        """Test option initialization"""
        opt = store.option(self.base_paragraph, ["-v"], ["--verbose"], False)
        self.assertEqual(opt.idx, 1)
        self.assertEqual(opt.text, "-v verbose option")
        self.assertEqual(opt.section, "OPTIONS")
        self.assertTrue(opt.is_option)
        self.assertEqual(opt.short, ["-v"])
        self.assertEqual(opt.long, ["--verbose"])
        self.assertFalse(opt.expectsarg)
        self.assertIsNone(opt.argument)
        self.assertFalse(opt.nestedcommand)

    def test_option_init_with_argument(self):
        """Test option initialization with argument"""
        opt = store.option(self.base_paragraph, ["-f"], ["--file"], "FILE", "FILENAME")
        self.assertEqual(opt.expectsarg, "FILE")
        self.assertEqual(opt.argument, "FILENAME")

    def test_option_init_nested_command(self):
        """Test option initialization with nested command"""
        opt = store.option(self.base_paragraph, ["-e"], ["--exec"], True, nestedcommand=True)
        self.assertTrue(opt.expectsarg)
        self.assertTrue(opt.nestedcommand)

    def test_option_init_nested_command_assertion(self):
        """Test option nested command requires expectsarg"""
        with self.assertRaises(AssertionError):
            store.option(self.base_paragraph, ["-e"], [], False, nestedcommand=True)

    def test_option_opts_property(self):
        """Test option opts property"""
        opt = store.option(self.base_paragraph, ["-v", "-V"], ["--verbose"], False)
        expected_opts = ["-v", "-V", "--verbose"]
        self.assertEqual(opt.opts, expected_opts)

    def test_option_from_store(self):
        """Test option from_store class method"""
        data = {
            "idx": 2,
            "text": "-l list files",
            "section": "OPTIONS",
            "is_option": True,
            "short": ["-l"],
            "long": ["--list"],
            "expectsarg": False,
            "argument": None,
            "nestedcommand": False
        }
        opt = store.option.from_store(data)
        self.assertEqual(opt.idx, 2)
        self.assertEqual(opt.short, ["-l"])
        self.assertEqual(opt.long, ["--list"])
        self.assertFalse(opt.expectsarg)

    def test_option_from_store_with_nested(self):
        """Test option from_store with nested command"""
        data = {
            "idx": 3,
            "text": "-exec command",
            "section": "OPTIONS",
            "is_option": True,
            "short": ["-exec"],
            "long": [],
            "expectsarg": True,
            "argument": "COMMAND",
            "nestedcommand": True
        }
        opt = store.option.from_store(data)
        self.assertTrue(opt.nestedcommand)
        self.assertEqual(opt.argument, "COMMAND")

    def test_option_to_store(self):
        """Test option to_store method"""
        opt = store.option(self.base_paragraph, ["-v"], ["--verbose"], "LEVEL", "VERBOSITY")
        data = opt.to_store()
        
        self.assertTrue(data["is_option"])
        self.assertEqual(data["short"], ["-v"])
        self.assertEqual(data["long"], ["--verbose"])
        self.assertEqual(data["expectsarg"], "LEVEL")
        self.assertEqual(data["argument"], "VERBOSITY")
        self.assertFalse(data["nestedcommand"])

    def test_option_str(self):
        """Test option __str__ method"""
        opt = store.option(self.base_paragraph, ["-v", "-V"], ["--verbose"], False)
        str_repr = str(opt)
        self.assertEqual(str_repr, "(-v, -V, --verbose)")

    def test_option_repr(self):
        """Test option __repr__ method"""
        opt = store.option(self.base_paragraph, ["-v"], ["--verbose"], False)
        repr_str = repr(opt)
        self.assertIn("options for paragraph 1", repr_str)
        self.assertIn("(-v, --verbose)", repr_str)


class TestManpage(unittest.TestCase):
    """Tests for manpage class"""

    def setUp(self):
        """Set up test fixtures"""
        self.paragraphs = [
            store.paragraph(0, "Description text", "DESCRIPTION", False),
            store.option(
                store.paragraph(1, "-v verbose", "OPTIONS", True),
                ["-v"], ["--verbose"], False
            )
        ]
        self.aliases = [("ls", 10), ("list", 5)]

    def test_manpage_init(self):
        """Test manpage initialization"""
        mp = store.manpage(
            "ls.1.gz", "ls", "list directory contents",
            self.paragraphs, self.aliases
        )
        self.assertEqual(mp.source, "ls.1.gz")
        self.assertEqual(mp.name, "ls")
        self.assertEqual(mp.synopsis, "list directory contents")
        self.assertEqual(mp.paragraphs, self.paragraphs)
        self.assertEqual(mp.aliases, self.aliases)
        self.assertFalse(mp.partialmatch)
        self.assertFalse(mp.multicommand)
        self.assertFalse(mp.updated)
        self.assertFalse(mp.nestedcommand)

    def test_manpage_init_with_flags(self):
        """Test manpage initialization with flags"""
        mp = store.manpage(
            "git.1.gz", "git", "git synopsis", [], [],
            partialmatch=True, multicommand=True, updated=True, nestedcommand=True
        )
        self.assertTrue(mp.partialmatch)
        self.assertTrue(mp.multicommand)
        self.assertTrue(mp.updated)
        self.assertTrue(mp.nestedcommand)

    def test_manpage_removeoption(self):
        """Test manpage removeoption method"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        mp.removeoption(1)
        
        # Check that the option was converted to a regular paragraph
        p = mp.paragraphs[1]
        self.assertIsInstance(p, store.paragraph)
        self.assertNotIsInstance(p, store.option)
        self.assertFalse(p.is_option)

    def test_manpage_removeoption_not_option(self):
        """Test removeoption with non-option paragraph"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        with self.assertRaises(ValueError):
            mp.removeoption(0)  # First paragraph is not an option

    def test_manpage_removeoption_not_found(self):
        """Test removeoption with non-existent idx"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        with self.assertRaises(ValueError):
            mp.removeoption(99)

    def test_manpage_namesection_property(self):
        """Test manpage namesection property"""
        mp = store.manpage("ls.1.gz", "ls", "synopsis", [], [])
        with patch('explainshell.store.util.namesection') as mock_namesection:
            mock_namesection.return_value = ("ls", "1")
            self.assertEqual(mp.namesection, "ls(1)")
            mock_namesection.assert_called_once_with("ls.1")

    def test_manpage_section_property(self):
        """Test manpage section property"""
        mp = store.manpage("cat.1.gz", "cat", "synopsis", [], [])
        with patch('explainshell.store.util.namesection') as mock_namesection:
            mock_namesection.return_value = ("cat", "1")
            self.assertEqual(mp.section, "1")

    def test_manpage_options_property(self):
        """Test manpage options property"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        options = mp.options
        self.assertEqual(len(options), 1)
        self.assertIsInstance(options[0], store.option)

    def test_manpage_arguments_property(self):
        """Test manpage arguments property"""
        # Create options with arguments
        opt1 = store.option(
            store.paragraph(1, "file option", "OPTIONS", True),
            ["-f"], [], False, "FILE"
        )
        opt2 = store.option(
            store.paragraph(2, "another file option", "OPTIONS", True),
            ["-o"], [], False, "FILE"
        )
        opt3 = store.option(
            store.paragraph(3, "different option", "OPTIONS", True),
            ["-v"], [], False, "LEVEL"
        )
        
        paragraphs = [opt1, opt2, opt3]
        mp = store.manpage("test.1.gz", "test", "test", paragraphs, [])
        
        arguments = mp.arguments
        self.assertIn("FILE", arguments)
        self.assertIn("LEVEL", arguments)
        self.assertIn("file option\n\nanother file option", arguments["FILE"])
        self.assertIn("different option", arguments["LEVEL"])

    def test_manpage_synopsisnoname_property(self):
        """Test manpage synopsisnoname property"""
        mp = store.manpage("ls.1.gz", "ls", "ls - list directory contents", [], [])
        self.assertEqual(mp.synopsisnoname, "list directory contents")

    def test_manpage_synopsisnoname_no_match(self):
        """Test synopsisnoname with no match"""
        mp = store.manpage("test.1.gz", "test", "invalid synopsis format", [], [])
        self.assertEqual(mp.synopsisnoname, "")

    def test_manpage_find_option(self):
        """Test manpage find_option method"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        option = mp.find_option("-v")
        self.assertIsNotNone(option)
        self.assertIn("-v", option.opts)

    def test_manpage_find_option_not_found(self):
        """Test find_option with non-existent flag"""
        mp = store.manpage("test.1.gz", "test", "test", self.paragraphs, [])
        option = mp.find_option("-z")
        self.assertIsNone(option)

    def test_manpage_to_store(self):
        """Test manpage to_store method"""
        mp = store.manpage(
            "ls.1.gz", "ls", "synopsis", self.paragraphs, self.aliases,
            partialmatch=True, multicommand=True, updated=True, nestedcommand=True
        )
        data = mp.to_store()
        
        expected_keys = [
            "source", "name", "synopsis", "paragraphs", "aliases",
            "partialmatch", "multicommand", "updated", "nestedcommand"
        ]
        for key in expected_keys:
            self.assertIn(key, data)
        
        self.assertEqual(data["source"], "ls.1.gz")
        self.assertEqual(data["name"], "ls")
        self.assertTrue(data["partialmatch"])
        self.assertTrue(data["multicommand"])

    def test_manpage_from_store(self):
        """Test manpage from_store class method"""
        data = {
            "source": "cat.1.gz",
            "name": "cat",
            "synopsis": "concatenate files",
            "paragraphs": [
                {
                    "idx": 0,
                    "text": "description",
                    "section": "DESCRIPTION",
                    "is_option": False
                },
                {
                    "idx": 1,
                    "text": "-n number lines",
                    "section": "OPTIONS",
                    "is_option": True,
                    "short": ["-n"],
                    "long": ["--number"],
                    "expectsarg": False,
                    "argument": None,
                    "nestedcommand": False
                }
            ],
            "aliases": [["cat", 10]],
            "partialmatch": True,
            "multicommand": False,
            "updated": True,
            "nestedcommand": False
        }
        
        mp = store.manpage.from_store(data)
        self.assertEqual(mp.name, "cat")
        self.assertEqual(mp.source, "cat.1.gz")
        self.assertEqual(len(mp.paragraphs), 2)
        self.assertIsInstance(mp.paragraphs[1], store.option)
        self.assertTrue(mp.partialmatch)
        self.assertTrue(mp.updated)

    def test_manpage_from_store_no_synopsis(self):
        """Test from_store with None synopsis"""
        data = {
            "source": "test.1.gz",
            "name": "test",
            "synopsis": None,
            "paragraphs": [],
            "aliases": []
        }
        
        mp = store.manpage.from_store(data)
        self.assertEqual(mp.synopsis, helpconstants.NOSYNOPSIS)

    def test_manpage_from_store_name_only(self):
        """Test from_store_name_only static method"""
        mp = store.manpage.from_store_name_only("ls", "ls.1.gz")
        self.assertEqual(mp.name, "ls")
        self.assertEqual(mp.source, "ls.1.gz")
        self.assertIsNone(mp.synopsis)
        self.assertEqual(mp.paragraphs, [])
        self.assertEqual(mp.aliases, [])

    def test_manpage_repr(self):
        """Test manpage __repr__ method"""
        mp = store.manpage("ls.1.gz", "ls", "synopsis", self.paragraphs, [])
        with patch('explainshell.store.util.namesection') as mock_namesection:
            mock_namesection.return_value = ("ls", "1")
            repr_str = repr(mp)
            self.assertIn("ls", repr_str)
            self.assertIn("1", repr_str)
            self.assertIn("1 options", repr_str)


class TestClassifierManpage(unittest.TestCase):
    """Tests for classifiermanpage class"""

    def test_classifiermanpage_init(self):
        """Test classifiermanpage initialization"""
        paragraphs = [store.paragraph(0, "test", "DESC", False)]
        cm = store.classifiermanpage("test", paragraphs)
        self.assertEqual(cm.name, "test")
        self.assertEqual(cm.paragraphs, paragraphs)

    def test_classifiermanpage_from_store(self):
        """Test classifiermanpage from_store"""
        data = {
            "name": "test",
            "paragraphs": [{
                "idx": 0,
                "text": "test paragraph",
                "section": "DESC",
                "is_option": False
            }]
        }
        
        cm = store.classifiermanpage.from_store(data)
        self.assertEqual(cm.name, "test")
        self.assertEqual(len(cm.paragraphs), 1)
        self.assertIsInstance(cm.paragraphs[0], store.paragraph)

    def test_classifiermanpage_to_store(self):
        """Test classifiermanpage to_store"""
        paragraphs = [store.paragraph(0, "test", "DESC", False)]
        cm = store.classifiermanpage("test", paragraphs)
        data = cm.to_store()
        
        self.assertEqual(data["name"], "test")
        self.assertEqual(len(data["paragraphs"]), 1)


class TestStore(unittest.TestCase):
    """Tests for store class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_classifier = MagicMock()
        self.mock_manpage = MagicMock()
        self.mock_mapping = MagicMock()
        
        self.mock_client.__getitem__.return_value = self.mock_db
        self.mock_db.__getitem__.side_effect = lambda x: {
            "classifier": self.mock_classifier,
            "manpage": self.mock_manpage,
            "mapping": self.mock_mapping
        }[x]

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_init(self, mock_mongo_client):
        """Test store initialization"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store("testdb", "mongodb://localhost")
        
        mock_mongo_client.assert_called_once_with("mongodb://localhost")
        self.assertEqual(s.db, self.mock_db)
        self.assertEqual(s.classifier, self.mock_classifier)
        self.assertEqual(s.manpage, self.mock_manpage)
        self.assertEqual(s.mapping, self.mock_mapping)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_close(self, mock_mongo_client):
        """Test store close method"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store()
        s.close()
        
        self.mock_client.close.assert_called_once()
        self.assertIsNone(s.classifier)
        self.assertIsNone(s.manpage)
        self.assertIsNone(s.mapping)
        self.assertIsNone(s.db)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_drop(self, mock_mongo_client):
        """Test store drop method"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store()
        s.drop(confirm=True)
        
        self.mock_mapping.drop.assert_called_once()
        self.mock_manpage.drop.assert_called_once()

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_drop_no_confirm(self, mock_mongo_client):
        """Test store drop without confirmation"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store()
        s.drop(confirm=False)
        
        self.mock_mapping.drop.assert_not_called()
        self.mock_manpage.drop.assert_not_called()

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_trainingset(self, mock_mongo_client):
        """Test store trainingset method"""
        mock_mongo_client.return_value = self.mock_client
        
        mock_data = [{"name": "test", "paragraphs": []}]
        self.mock_classifier.find.return_value = mock_data
        
        s = store.store()
        training_data = list(s.trainingset())
        
        self.mock_classifier.find.assert_called_once()
        self.assertEqual(len(training_data), 1)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_contains(self, mock_mongo_client):
        """Test store __contains__ method"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_mapping.count_documents.return_value = 1
        
        s = store.store()
        result = "test" in s
        
        self.assertTrue(result)
        self.mock_mapping.count_documents.assert_called_once_with({"src": "test"})

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_contains_not_found(self, mock_mongo_client):
        """Test store __contains__ with non-existent item"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_mapping.count_documents.return_value = 0
        
        s = store.store()
        result = "nonexistent" in s
        
        self.assertFalse(result)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_iter(self, mock_mongo_client):
        """Test store __iter__ method"""
        mock_mongo_client.return_value = self.mock_client
        
        mock_data = [{
            "source": "ls.1.gz",
            "name": "ls",
            "synopsis": "list files",
            "paragraphs": [],
            "aliases": []
        }]
        self.mock_manpage.find.return_value = mock_data
        
        s = store.store()
        manpages = list(s)
        
        self.assertEqual(len(manpages), 1)
        self.assertIsInstance(manpages[0], store.manpage)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_addmapping(self, mock_mongo_client):
        """Test store addmapping method"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store()
        s.addmapping("ls", "objectid", 10)
        
        self.mock_mapping.insert_one.assert_called_once_with({
            "src": "ls",
            "dst": "objectid",
            "score": 10
        })

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_findmanpage_gz(self, mock_mongo_client):
        """Test findmanpage with .gz extension"""
        mock_mongo_client.return_value = self.mock_client
        
        mock_doc = {
            "source": "ls.1.gz",
            "name": "ls",
            "synopsis": "list files",
            "paragraphs": [],
            "aliases": []
        }
        self.mock_manpage.find_one.return_value = mock_doc
        
        s = store.store()
        result = s.findmanpage("ls.1.gz")
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], store.manpage)
        self.mock_manpage.find_one.assert_called_with({"source": "ls.1.gz"})

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_findmanpage_not_found(self, mock_mongo_client):
        """Test findmanpage with non-existent manpage"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_mapping.count_documents.return_value = 0
        
        s = store.store()
        with self.assertRaises(errors.ProgramDoesNotExist):
            s.findmanpage("nonexistent")

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_addmanpage(self, mock_mongo_client):
        """Test store addmanpage method"""
        mock_mongo_client.return_value = self.mock_client
        
        # Mock successful insertion
        mock_result = Mock()
        mock_result.inserted_id = "new_objectid"
        self.mock_manpage.insert_one.return_value = mock_result
        self.mock_manpage.find_one.return_value = None  # No existing manpage
        
        # Create test manpage
        mp = store.manpage(
            "test.1.gz", "test", "test synopsis", [],
            [("test", 10), ("alias", 5)]
        )
        
        s = store.store()
        result = s.addmanpage(mp)
        
        self.assertEqual(result, mp)
        self.mock_manpage.insert_one.assert_called_once()
        # Should add mappings for aliases
        self.assertEqual(self.mock_mapping.insert_one.call_count, 2)

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_updatemanpage(self, mock_mongo_client):
        """Test store updatemanpage method"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_manpage.find_one.return_value = {"_id": "existing_id"}
        self.mock_mapping.count_documents.return_value = 0  # Alias doesn't exist
        
        mp = store.manpage("test.1.gz", "test", "synopsis", [], [("test", 10)])
        
        s = store.store()
        result = s.updatemanpage(mp)
        
        self.assertTrue(result.updated)
        self.mock_manpage.update_one.assert_called_once()

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_verify(self, mock_mongo_client):
        """Test store verify method"""
        mock_mongo_client.return_value = self.mock_client
        
        # Mock data for verification
        self.mock_mapping.find.return_value = [{"dst": "id1"}, {"dst": "id2"}]
        self.mock_manpage.find.return_value = [{"_id": "id1"}, {"_id": "id2"}]
        
        s = store.store()
        ok, unreachable, notfound = s.verify()
        
        self.assertTrue(ok)
        self.assertEqual(list(unreachable), [])
        self.assertEqual(list(notfound), [])

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_verify_unreachable(self, mock_mongo_client):
        """Test store verify with unreachable manpages"""
        mock_mongo_client.return_value = self.mock_client
        
        # Mock unreachable manpage
        self.mock_mapping.find.return_value = [{"dst": "id1"}]
        self.mock_manpage.find.return_value = [{"_id": "id1"}, {"_id": "id2"}]
        self.mock_manpage.find_one.return_value = {"name": "unreachable"}
        
        s = store.store()
        ok, unreachable, notfound = s.verify()
        
        self.assertFalse(ok)
        self.assertEqual(unreachable, ["unreachable"])
        self.assertEqual(list(notfound), [])

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_names(self, mock_mongo_client):
        """Test store names method"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_manpage.find.return_value = [
            {"_id": "id1", "name": "ls"},
            {"_id": "id2", "name": "cat"}
        ]
        
        s = store.store()
        names = list(s.names())
        
        self.assertEqual(len(names), 2)
        self.assertEqual(names[0], ("id1", "ls"))
        self.assertEqual(names[1], ("id2", "cat"))

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_mappings(self, mock_mongo_client):
        """Test store mappings method"""
        mock_mongo_client.return_value = self.mock_client
        
        self.mock_mapping.find.return_value = [
            {"src": "ls", "_id": "mapping1"},
            {"src": "cat", "_id": "mapping2"}
        ]
        
        s = store.store()
        mappings = list(s.mappings())
        
        self.assertEqual(len(mappings), 2)
        self.assertEqual(mappings[0], ("ls", "mapping1"))
        self.assertEqual(mappings[1], ("cat", "mapping2"))

    @patch('explainshell.store.pymongo.MongoClient')
    def test_store_setmulticommand(self, mock_mongo_client):
        """Test store setmulticommand method"""
        mock_mongo_client.return_value = self.mock_client
        
        s = store.store()
        s.setmulticommand("manpage_id")
        
        self.mock_manpage.update_one.assert_called_once_with(
            {"_id": "manpage_id"},
            {"$set": {"multicommand": True}}
        )


class TestStoreIntegration(unittest.TestCase):
    """Integration tests for store module"""

    def test_paragraph_option_inheritance(self):
        """Test that option properly inherits from paragraph"""
        base_p = store.paragraph(1, "test text", "OPTIONS", True)
        opt = store.option(base_p, ["-v"], ["--verbose"], False)
        
        # Should inherit paragraph properties
        self.assertEqual(opt.idx, base_p.idx)
        self.assertEqual(opt.text, base_p.text)
        self.assertEqual(opt.section, base_p.section)
        self.assertEqual(opt.is_option, base_p.is_option)
        
        # Should have option-specific properties
        self.assertEqual(opt.short, ["-v"])
        self.assertEqual(opt.long, ["--verbose"])

    def test_manpage_complex_scenario(self):
        """Test manpage with complex paragraph structure"""
        paragraphs = [
            store.paragraph(0, "Description", "DESCRIPTION", False),
            store.option(
                store.paragraph(1, "-v verbose", "OPTIONS", True),
                ["-v"], ["--verbose"], False
            ),
            store.option(
                store.paragraph(2, "-f file", "OPTIONS", True),
                ["-f"], ["--file"], "FILE", "FILENAME"
            ),
            store.paragraph(3, "Examples", "EXAMPLES", False)
        ]
        
        mp = store.manpage("test.1.gz", "test", "test - a test program", paragraphs, [])
        
        # Test options property
        options = mp.options
        self.assertEqual(len(options), 2)
        
        # Test arguments property
        arguments = mp.arguments
        self.assertIn("FILENAME", arguments)
        
        # Test find_option
        verbose_opt = mp.find_option("--verbose")
        self.assertIsNotNone(verbose_opt)
        self.assertIn("--verbose", verbose_opt.opts)
        
        # Test synopsisnoname
        self.assertEqual(mp.synopsisnoname, "a test program")

    def test_store_data_consistency(self):
        """Test data consistency between to_store and from_store"""
        # Create complex manpage
        paragraphs = [
            store.paragraph(0, "Description", "DESCRIPTION", False),
            store.option(
                store.paragraph(1, "-v verbose", "OPTIONS", True),
                ["-v", "-V"], ["--verbose"], "LEVEL", "VERBOSITY", True
            )
        ]
        
        original_mp = store.manpage(
            "test.1.gz", "test", "test synopsis", paragraphs,
            [("test", 10), ("alias", 5)],
            partialmatch=True, multicommand=True, updated=True, nestedcommand=True
        )
        
        # Convert to store format and back
        store_data = original_mp.to_store()
        restored_mp = store.manpage.from_store(store_data)
        
        # Verify all properties are preserved
        self.assertEqual(original_mp.source, restored_mp.source)
        self.assertEqual(original_mp.name, restored_mp.name)
        self.assertEqual(original_mp.synopsis, restored_mp.synopsis)
        self.assertEqual(original_mp.partialmatch, restored_mp.partialmatch)
        self.assertEqual(original_mp.multicommand, restored_mp.multicommand)
        self.assertEqual(original_mp.updated, restored_mp.updated)
        self.assertEqual(original_mp.nestedcommand, restored_mp.nestedcommand)
        
        # Verify paragraphs
        self.assertEqual(len(original_mp.paragraphs), len(restored_mp.paragraphs))
        
        # Verify option is properly restored
        original_opt = original_mp.paragraphs[1]
        restored_opt = restored_mp.paragraphs[1]
        self.assertIsInstance(restored_opt, store.option)
        self.assertEqual(original_opt.short, restored_opt.short)
        self.assertEqual(original_opt.long, restored_opt.long)
        self.assertEqual(original_opt.expectsarg, restored_opt.expectsarg)
        self.assertEqual(original_opt.argument, restored_opt.argument)
        self.assertEqual(original_opt.nestedcommand, restored_opt.nestedcommand)


if __name__ == "__main__":
    unittest.main()