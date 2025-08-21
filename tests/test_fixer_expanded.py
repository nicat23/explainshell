import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import contextlib

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell import fixer, store


class TestBaseFixer(unittest.TestCase):
    """Tests for basefixer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.base_fixer = fixer.basefixer(self.mock_mctx)

    def test_basefixer_init(self):
        """Test basefixer initialization"""
        self.assertEqual(self.base_fixer.mctx, self.mock_mctx)
        self.assertTrue(self.base_fixer.run)
        self.assertIsNotNone(self.base_fixer.logger)
        self.assertEqual(self.base_fixer.logger.name, "basefixer")

    def test_basefixer_default_methods(self):
        """Test that all default methods exist and do nothing"""
        # All these methods should exist and not raise exceptions
        self.base_fixer.pre_get_raw_manpage()
        self.base_fixer.pre_parse_manpage()
        self.base_fixer.post_parse_manpage()
        self.base_fixer.pre_classify()
        self.base_fixer.post_classify()
        self.base_fixer.post_option_extraction()
        self.base_fixer.pre_add_manpage()

    def test_basefixer_class_attributes(self):
        """Test basefixer class attributes"""
        self.assertEqual(fixer.basefixer.runbefore, [])
        self.assertFalse(fixer.basefixer.runlast)

    def test_basefixer_inheritance(self):
        """Test that custom fixer can inherit from basefixer"""
        class CustomFixer(fixer.basefixer):
            def post_parse_manpage(self):
                self.custom_called = True

        custom = CustomFixer(self.mock_mctx)
        custom.post_parse_manpage()
        self.assertTrue(custom.custom_called)


class TestRunner(unittest.TestCase):
    """Tests for runner class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.original_fixerscls = fixer.fixerscls[:]

    def tearDown(self):
        """Clean up after tests"""
        fixer.fixerscls = self.original_fixerscls

    def test_runner_init(self):
        """Test runner initialization"""
        # Create mock fixer classes
        mock_fixer_cls1 = Mock()
        mock_fixer_cls2 = Mock()
        mock_fixer1 = Mock()
        mock_fixer2 = Mock()
        mock_fixer_cls1.return_value = mock_fixer1
        mock_fixer_cls2.return_value = mock_fixer2
        
        fixer.fixerscls = [mock_fixer_cls1, mock_fixer_cls2]
        
        runner = fixer.runner(self.mock_mctx)
        
        self.assertEqual(runner.mctx, self.mock_mctx)
        self.assertEqual(len(runner.fixers), 2)
        mock_fixer_cls1.assert_called_once_with(self.mock_mctx)
        mock_fixer_cls2.assert_called_once_with(self.mock_mctx)

    def test_runner_disable(self):
        """Test runner disable method"""
        class TestFixer1(fixer.basefixer):
            pass
        
        class TestFixer2(fixer.basefixer):
            pass
        
        fixer.fixerscls = [TestFixer1, TestFixer2]
        runner = fixer.runner(self.mock_mctx)
        
        self.assertEqual(len(runner.fixers), 2)
        
        runner.disable("TestFixer1")
        self.assertEqual(len(runner.fixers), 1)
        self.assertIsInstance(runner.fixers[0], TestFixer2)

    def test_runner_disable_not_found(self):
        """Test runner disable with non-existent fixer"""
        fixer.fixerscls = []
        runner = fixer.runner(self.mock_mctx)
        
        with self.assertRaises(ValueError):
            runner.disable("NonExistentFixer")

    def test_runner_fixers_filter(self):
        """Test runner _fixers method filters by run attribute"""
        mock_fixer1 = Mock()
        mock_fixer1.run = True
        mock_fixer2 = Mock()
        mock_fixer2.run = False
        mock_fixer3 = Mock()
        mock_fixer3.run = True
        
        runner = fixer.runner(self.mock_mctx)
        runner.fixers = [mock_fixer1, mock_fixer2, mock_fixer3]
        
        active_fixers = list(runner._fixers())
        self.assertEqual(len(active_fixers), 2)
        self.assertIn(mock_fixer1, active_fixers)
        self.assertIn(mock_fixer3, active_fixers)
        self.assertNotIn(mock_fixer2, active_fixers)

    def test_runner_pre_get_raw_manpage(self):
        """Test runner pre_get_raw_manpage calls all active fixers"""
        mock_fixer1 = Mock()
        mock_fixer1.run = True
        mock_fixer2 = Mock()
        mock_fixer2.run = False
        
        runner = fixer.runner(self.mock_mctx)
        runner.fixers = [mock_fixer1, mock_fixer2]
        
        runner.pre_get_raw_manpage()
        
        mock_fixer1.pre_get_raw_manpage.assert_called_once()
        mock_fixer2.pre_get_raw_manpage.assert_not_called()

    def test_runner_all_methods(self):
        """Test all runner methods call corresponding fixer methods"""
        mock_fixer = Mock()
        mock_fixer.run = True
        
        runner = fixer.runner(self.mock_mctx)
        runner.fixers = [mock_fixer]
        
        # Test all methods
        runner.pre_get_raw_manpage()
        runner.pre_parse_manpage()
        runner.post_parse_manpage()
        runner.pre_classify()
        runner.post_classify()
        runner.post_option_extraction()
        runner.pre_add_manpage()
        
        # Verify all methods were called
        mock_fixer.pre_get_raw_manpage.assert_called_once()
        mock_fixer.pre_parse_manpage.assert_called_once()
        mock_fixer.post_parse_manpage.assert_called_once()
        mock_fixer.pre_classify.assert_called_once()
        mock_fixer.post_classify.assert_called_once()
        mock_fixer.post_option_extraction.assert_called_once()
        mock_fixer.pre_add_manpage.assert_called_once()


class TestRegister(unittest.TestCase):
    """Tests for register decorator"""

    def setUp(self):
        """Set up test fixtures"""
        self.original_fixerscls = fixer.fixerscls[:]

    def tearDown(self):
        """Clean up after tests"""
        fixer.fixerscls = self.original_fixerscls

    def test_register_adds_to_fixerscls(self):
        """Test register decorator adds class to fixerscls"""
        initial_count = len(fixer.fixerscls)
        
        @fixer.register
        class TestFixer(fixer.basefixer):
            pass
        
        self.assertEqual(len(fixer.fixerscls), initial_count + 1)
        self.assertIn(TestFixer, fixer.fixerscls)

    def test_register_returns_class(self):
        """Test register decorator returns the class"""
        @fixer.register
        class TestFixer(fixer.basefixer):
            pass
        
        self.assertEqual(TestFixer.__name__, "TestFixer")

    def test_register_runbefore_setup(self):
        """Test register sets up runbefore relationships"""
        class FirstFixer(fixer.basefixer):
            pass
        
        @fixer.register
        class SecondFixer(fixer.basefixer):
            runbefore = [FirstFixer]
        
        self.assertTrue(hasattr(FirstFixer, '_parents'))
        self.assertIn(SecondFixer, FirstFixer._parents)


class TestBulletRemover(unittest.TestCase):
    """Tests for bulletremover fixer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.mock_manpage = Mock()
        self.mock_mctx.manpage = self.mock_manpage
        self.bullet_remover = fixer.bulletremover(self.mock_mctx)

    def test_bulletremover_removes_bullets(self):
        """Test bulletremover removes bullet characters"""
        # Create paragraphs with bullet characters
        p1 = Mock()
        p1.text = "text with \xc2\xb7 bullet"
        p2 = Mock()
        p2.text = "normal text"
        p3 = Mock()
        p3.text = "\xc2\xb7"  # Only bullet, should be removed
        
        self.mock_manpage.paragraphs = [p1, p2, p3]
        
        self.bullet_remover.post_parse_manpage()
        
        # Check bullet was removed from p1
        self.assertEqual(p1.text, "text with  bullet")
        # p2 should be unchanged
        self.assertEqual(p2.text, "normal text")
        # p3 should be removed from list (empty after bullet removal)
        self.assertEqual(len(self.mock_manpage.paragraphs), 2)

    def test_bulletremover_no_bullets(self):
        """Test bulletremover with no bullets"""
        p1 = Mock()
        p1.text = "normal text"
        p2 = Mock()
        p2.text = "another text"
        
        self.mock_manpage.paragraphs = [p1, p2]
        
        self.bullet_remover.post_parse_manpage()
        
        # Nothing should change
        self.assertEqual(p1.text, "normal text")
        self.assertEqual(p2.text, "another text")
        self.assertEqual(len(self.mock_manpage.paragraphs), 2)

    def test_bulletremover_multiple_bullets(self):
        """Test bulletremover with multiple bullets in one paragraph"""
        p1 = Mock()
        p1.text = "text \xc2\xb7 with \xc2\xb7 multiple bullets"
        
        self.mock_manpage.paragraphs = [p1]
        
        self.bullet_remover.post_parse_manpage()
        
        # Only first bullet should be removed
        self.assertEqual(p1.text, "text  with \xc2\xb7 multiple bullets")


class TestLeadingSpaceRemover(unittest.TestCase):
    """Tests for leadingspaceremover fixer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.mock_manpage = Mock()
        self.mock_mctx.manpage = self.mock_manpage
        self.space_remover = fixer.leadingspaceremover(self.mock_mctx)

    def test_leadingspaceremover_removes_whitespace(self):
        """Test leadingspaceremover removes leading whitespace"""
        # Create mock options
        opt1 = Mock()
        opt1.text = "  line1\n    line2\n  line3"
        opt2 = Mock()
        opt2.text = "\t\tindented\n\t\t\tmore indented"
        
        self.mock_manpage.options = [opt1, opt2]
        
        self.space_remover.post_option_extraction()
        
        # Check whitespace was removed
        self.assertEqual(opt1.text, "line1\n  line2\nline3")
        self.assertEqual(opt2.text, "indented\n\tmore indented")

    def test_removewhitespace_method(self):
        """Test _removewhitespace method directly"""
        # Test cases from docstring
        result1 = self.space_remover._removewhitespace(' a\n  b ')
        self.assertEqual(result1, 'a\n b')
        
        result2 = self.space_remover._removewhitespace('\t a\n\t \tb')
        self.assertEqual(result2, 'a\n\tb')

    def test_removewhitespace_empty_string(self):
        """Test _removewhitespace with empty string"""
        result = self.space_remover._removewhitespace('')
        self.assertEqual(result, '')

    def test_removewhitespace_no_leading_space(self):
        """Test _removewhitespace with no leading space"""
        result = self.space_remover._removewhitespace('no leading space\nstill none')
        self.assertEqual(result, 'no leading space\nstill none')


class TestTarFixer(unittest.TestCase):
    """Tests for tarfixer"""

    def test_tarfixer_tar_command(self):
        """Test tarfixer runs for tar command"""
        mock_mctx = Mock()
        mock_mctx.name = "tar"
        mock_manpage = Mock()
        mock_mctx.manpage = mock_manpage
        
        tar_fixer = fixer.tarfixer(mock_mctx)
        
        self.assertTrue(tar_fixer.run)
        
        tar_fixer.pre_add_manpage()
        
        self.assertTrue(mock_manpage.partialmatch)

    def test_tarfixer_non_tar_command(self):
        """Test tarfixer doesn't run for non-tar commands"""
        mock_mctx = Mock()
        mock_mctx.name = "ls"
        
        tar_fixer = fixer.tarfixer(mock_mctx)
        
        self.assertFalse(tar_fixer.run)


class TestParagraphJoiner(unittest.TestCase):
    """Tests for paragraphjoiner fixer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.mock_manpage = Mock()
        self.mock_mctx.manpage = self.mock_manpage
        self.joiner = fixer.paragraphjoiner(self.mock_mctx)

    def test_paragraphjoiner_runbefore(self):
        """Test paragraphjoiner runbefore attribute"""
        self.assertEqual(fixer.paragraphjoiner.runbefore, [fixer.leadingspaceremover])

    def test_paragraphjoiner_maxdistance(self):
        """Test paragraphjoiner maxdistance attribute"""
        self.assertEqual(fixer.paragraphjoiner.maxdistance, 5)

    def test_paragraphjoiner_post_option_extraction(self):
        """Test paragraphjoiner post_option_extraction method"""
        # Create mock paragraphs and options
        mock_option1 = Mock()
        mock_option1.is_option = True
        mock_option2 = Mock()
        mock_option2.is_option = True
        mock_regular = Mock()
        mock_regular.is_option = False
        
        self.mock_manpage.paragraphs = [mock_option1, mock_regular, mock_option2]
        
        with patch.object(self.joiner, '_join') as mock_join:
            self.joiner.post_option_extraction()
            
            mock_join.assert_called_once_with(
                self.mock_manpage.paragraphs,
                [mock_option1, mock_option2]
            )

    def test_join_method_basic(self):
        """Test _join method with basic scenario"""
        # Create test paragraphs
        paragraphs = []
        for i in range(10):
            p = Mock()
            p.idx = i
            p.text = f"text{i}"
            p.section = "OPTIONS"
            paragraphs.append(p)
        
        # Create options at indices 0, 2, 5
        options = [
            Mock(idx=0, section="OPTIONS", text="opt0"),
            Mock(idx=2, section="OPTIONS", text="opt2"),
            Mock(idx=5, section="OPTIONS", text="opt5")
        ]
        
        merged = self.joiner._join(paragraphs, options)
        
        # Should merge paragraph 1 into option at index 0
        self.assertGreater(merged, 0)

    def test_join_different_sections(self):
        """Test _join doesn't merge options from different sections"""
        paragraphs = [Mock(idx=i, text=f"text{i}") for i in range(5)]
        
        options = [
            Mock(idx=0, section="OPTIONS", text="opt0"),
            Mock(idx=2, section="DESCRIPTION", text="opt2")
        ]
        
        merged = self.joiner._join(paragraphs, options)
        
        # Should not merge due to different sections
        self.assertEqual(merged, 0)

    def test_join_too_many_between(self):
        """Test _join doesn't merge when too many paragraphs between"""
        paragraphs = [Mock(idx=i, text=f"text{i}") for i in range(10)]
        
        options = [
            Mock(idx=0, section="OPTIONS", text="opt0"),
            Mock(idx=8, section="OPTIONS", text="opt8")  # Too far apart
        ]
        
        merged = self.joiner._join(paragraphs, options)
        
        # Should not merge due to distance
        self.assertEqual(merged, 0)


class TestOptionTrimmer(unittest.TestCase):
    """Tests for optiontrimmer fixer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mctx = Mock()
        self.mock_manpage = Mock()
        self.mock_mctx.manpage = self.mock_manpage

    def test_optiontrimmer_git_rebase(self):
        """Test optiontrimmer for git-rebase"""
        self.mock_mctx.name = "git-rebase"
        trimmer = fixer.optiontrimmer(self.mock_mctx)
        
        self.assertTrue(trimmer.run)
        self.assertIn("git-rebase", fixer.optiontrimmer.d)

    def test_optiontrimmer_other_command(self):
        """Test optiontrimmer for other commands"""
        self.mock_mctx.name = "ls"
        trimmer = fixer.optiontrimmer(self.mock_mctx)
        
        self.assertFalse(trimmer.run)

    def test_optiontrimmer_post_classify(self):
        """Test optiontrimmer post_classify method"""
        self.mock_mctx.name = "git-rebase"
        trimmer = fixer.optiontrimmer(self.mock_mctx)
        
        # Create mock options
        opt1 = Mock(idx=40, is_option=True)  # Below start
        opt2 = Mock(idx=60, is_option=True)  # Within range
        opt3 = Mock(idx=80, is_option=True)  # Within range
        
        self.mock_manpage.paragraphs = [opt1, opt2, opt3]
        
        with patch.object(trimmer.logger, 'info'):
            trimmer.post_classify()
        
        # opt1 should be removed (below start=50)
        self.assertFalse(opt1.is_option)
        # opt2 and opt3 should remain
        self.assertTrue(opt2.is_option)
        self.assertTrue(opt3.is_option)


class TestParentsFunction(unittest.TestCase):
    """Tests for _parents function"""

    def test_parents_normal_class(self):
        """Test _parents with normal class"""
        class TestFixer(fixer.basefixer):
            pass
        
        # Mock fixerscls
        with patch.object(fixer, 'fixerscls', [TestFixer]):
            parents = fixer._parents(TestFixer)
            self.assertEqual(parents, [])

    def test_parents_with_runbefore(self):
        """Test _parents with runbefore attribute"""
        class FirstFixer(fixer.basefixer):
            pass
        
        class SecondFixer(fixer.basefixer):
            _parents = [FirstFixer]
        
        parents = fixer._parents(SecondFixer)
        self.assertEqual(parents, [FirstFixer])

    def test_parents_runlast(self):
        """Test _parents with runlast=True"""
        class TestFixer(fixer.basefixer):
            runlast = True
        
        class OtherFixer(fixer.basefixer):
            pass
        
        with patch.object(fixer, 'fixerscls', [TestFixer, OtherFixer]):
            parents = fixer._parents(TestFixer)
            self.assertEqual(parents, [OtherFixer])

    def test_parents_runlast_with_parents_error(self):
        """Test _parents raises error when runlast=True and has parents"""
        class TestFixer(fixer.basefixer):
            runlast = True
            _parents = [Mock()]
        
        with self.assertRaises(ValueError):
            fixer._parents(TestFixer)


class TestFixerIntegration(unittest.TestCase):
    """Integration tests for fixer module"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.original_fixerscls = fixer.fixerscls[:]

    def tearDown(self):
        """Clean up after integration tests"""
        fixer.fixerscls = self.original_fixerscls

    def test_full_fixer_workflow(self):
        """Test complete fixer workflow"""
        # Create a custom fixer for testing
        @fixer.register
        class TestWorkflowFixer(fixer.basefixer):
            def __init__(self, mctx):
                super().__init__(mctx)
                self.calls = []
            
            def pre_get_raw_manpage(self):
                self.calls.append('pre_get_raw_manpage')
            
            def post_parse_manpage(self):
                self.calls.append('post_parse_manpage')
            
            def post_option_extraction(self):
                self.calls.append('post_option_extraction')
        
        mock_mctx = Mock()
        mock_mctx.manpage.paragraphs = []  # Mock paragraphs for bulletremover
        mock_mctx.manpage.options = []     # Mock options for leadingspaceremover
        
        runner = fixer.runner(mock_mctx)
        
        # Find our test fixer
        test_fixer = None
        for f in runner.fixers:
            if isinstance(f, TestWorkflowFixer):
                test_fixer = f
                break
        
        self.assertIsNotNone(test_fixer)
        
        # Run workflow
        runner.pre_get_raw_manpage()
        runner.post_parse_manpage()
        runner.post_option_extraction()
        
        # Verify calls were made
        expected_calls = ['pre_get_raw_manpage', 'post_parse_manpage', 'post_option_extraction']
        self.assertEqual(test_fixer.calls, expected_calls)

    def test_fixer_ordering(self):
        """Test that fixers are properly ordered"""
        # The fixerscls should be topologically sorted
        self.assertIsInstance(fixer.fixerscls, list)
        
        # paragraphjoiner should come before leadingspaceremover (runbefore relationship)
        pj_index = None
        lsr_index = None
        
        for i, cls in enumerate(fixer.fixerscls):
            if cls.__name__ == 'paragraphjoiner':
                pj_index = i
            elif cls.__name__ == 'leadingspaceremover':
                lsr_index = i
        
        if pj_index is not None and lsr_index is not None:
            self.assertLess(pj_index, lsr_index)

    def test_real_fixers_exist(self):
        """Test that real fixers are registered"""
        fixer_names = [cls.__name__ for cls in fixer.fixerscls]
        
        expected_fixers = [
            'bulletremover',
            'leadingspaceremover', 
            'tarfixer',
            'paragraphjoiner',
            'optiontrimmer'
        ]
        
        for expected in expected_fixers:
            self.assertIn(expected, fixer_names)

    def test_fixer_disable_integration(self):
        """Test disabling fixers in integration scenario"""
        mock_mctx = Mock()
        runner = fixer.runner(mock_mctx)
        
        initial_count = len(runner.fixers)
        
        # Disable a real fixer
        runner.disable('bulletremover')
        
        self.assertEqual(len(runner.fixers), initial_count - 1)
        
        # Verify bulletremover is not in active fixers
        active_names = [f.__class__.__name__ for f in runner._fixers()]
        self.assertNotIn('bulletremover', active_names)


if __name__ == "__main__":
    unittest.main()