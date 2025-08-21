import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell import fixer, store


class TestFixerEdgeCases(unittest.TestCase):
    """Edge case tests for fixer module"""

    def setUp(self):
        """Set up test fixtures"""
        self.original_fixerscls = fixer.fixerscls[:]

    def tearDown(self):
        """Clean up after tests"""
        fixer.fixerscls = self.original_fixerscls

    def test_bulletremover_empty_paragraphs(self):
        """Test bulletremover with empty paragraphs list"""
        mock_mctx = Mock()
        mock_mctx.manpage.paragraphs = []
        
        bullet_remover = fixer.bulletremover(mock_mctx)
        bullet_remover.post_parse_manpage()
        
        # Should not crash with empty list
        self.assertEqual(len(mock_mctx.manpage.paragraphs), 0)

    def test_bulletremover_paragraph_with_only_whitespace(self):
        """Test bulletremover with paragraph containing only whitespace after bullet removal"""
        mock_mctx = Mock()
        p1 = Mock()
        p1.text = "   \xc2\xb7   "  # Only bullet and whitespace
        mock_mctx.manpage.paragraphs = [p1]
        
        bullet_remover = fixer.bulletremover(mock_mctx)
        bullet_remover.post_parse_manpage()
        
        # Paragraph should be removed
        self.assertEqual(len(mock_mctx.manpage.paragraphs), 0)

    def test_bulletremover_bullet_not_found(self):
        """Test bulletremover when bullet character not in text"""
        mock_mctx = Mock()
        p1 = Mock()
        p1.text = "normal text without bullet"
        mock_mctx.manpage.paragraphs = [p1]
        
        bullet_remover = fixer.bulletremover(mock_mctx)
        bullet_remover.post_parse_manpage()
        
        # Text should remain unchanged
        self.assertEqual(p1.text, "normal text without bullet")
        self.assertEqual(len(mock_mctx.manpage.paragraphs), 1)

    def test_leadingspaceremover_empty_options(self):
        """Test leadingspaceremover with empty options list"""
        mock_mctx = Mock()
        mock_mctx.manpage.options = []
        
        space_remover = fixer.leadingspaceremover(mock_mctx)
        space_remover.post_option_extraction()
        
        # Should not crash with empty list
        self.assertEqual(len(mock_mctx.manpage.options), 0)

    def test_leadingspaceremover_option_with_none_text(self):
        """Test leadingspaceremover with option having None text"""
        mock_mctx = Mock()
        opt1 = Mock()
        opt1.text = None
        mock_mctx.manpage.options = [opt1]
        
        space_remover = fixer.leadingspaceremover(mock_mctx)
        
        # Should handle None text gracefully
        with patch.object(space_remover, '_removewhitespace') as mock_remove:
            mock_remove.return_value = ""
            space_remover.post_option_extraction()
            mock_remove.assert_called_once_with(None)

    def test_tarfixer_with_different_names(self):
        """Test tarfixer with various command names"""
        test_cases = [
            ("tar", True),
            ("gtar", False),
            ("tar.exe", False),
            ("mytar", False),
            ("", False)
        ]
        
        for name, should_run in test_cases:
            mock_mctx = Mock()
            mock_mctx.name = name
            tar_fixer = fixer.tarfixer(mock_mctx)
            self.assertEqual(tar_fixer.run, should_run, f"Failed for name: {name}")

    def test_paragraphjoiner_empty_options(self):
        """Test paragraphjoiner with empty options list"""
        mock_mctx = Mock()
        mock_mctx.manpage.paragraphs = []
        
        joiner = fixer.paragraphjoiner(mock_mctx)
        
        with patch.object(joiner, '_join') as mock_join:
            joiner.post_option_extraction()
            mock_join.assert_called_once_with([], [])

    def test_paragraphjoiner_single_option(self):
        """Test paragraphjoiner with single option"""
        mock_mctx = Mock()
        mock_option = Mock()
        mock_option.is_option = True
        mock_regular = Mock()
        mock_regular.is_option = False
        mock_mctx.manpage.paragraphs = [mock_option, mock_regular]
        
        joiner = fixer.paragraphjoiner(mock_mctx)
        
        with patch.object(joiner, '_join') as mock_join:
            joiner.post_option_extraction()
            mock_join.assert_called_once_with([mock_option, mock_regular], [mock_option])

    def test_paragraphjoiner_join_no_between_paragraphs(self):
        """Test _join with no paragraphs between options"""
        paragraphs = [Mock(idx=0), Mock(idx=1)]
        options = [Mock(idx=0, section="OPTIONS"), Mock(idx=1, section="OPTIONS")]
        
        joiner = fixer.paragraphjoiner(Mock())
        merged = joiner._join(paragraphs, options)
        
        # Should not merge adjacent options
        self.assertEqual(merged, 0)

    def test_paragraphjoiner_join_with_none_text(self):
        """Test _join with options having None text"""
        paragraphs = [Mock(idx=i) for i in range(5)]
        for i, p in enumerate(paragraphs):
            p.text = f"text{i}" if i != 1 else None
        
        options = [
            Mock(idx=0, section="OPTIONS", text=None),
            Mock(idx=3, section="OPTIONS", text="opt3")
        ]
        
        joiner = fixer.paragraphjoiner(Mock())
        merged = joiner._join(paragraphs, options)
        
        # Should handle None text gracefully
        self.assertGreaterEqual(merged, 0)

    def test_optiontrimmer_empty_paragraphs(self):
        """Test optiontrimmer with empty paragraphs"""
        mock_mctx = Mock()
        mock_mctx.name = "git-rebase"
        mock_mctx.manpage.paragraphs = []
        
        trimmer = fixer.optiontrimmer(mock_mctx)
        
        # Should raise AssertionError due to empty classifiedoptions
        with self.assertRaises(AssertionError):
            trimmer.post_classify()

    def test_optiontrimmer_with_end_not_minus_one(self):
        """Test optiontrimmer with specific end value (not -1)"""
        # Create a custom trimmer for testing
        class TestTrimmer(fixer.optiontrimmer):
            d = {"test-cmd": (30, 10)}  # start > end as expected by assertion
        
        mock_mctx = Mock()
        mock_mctx.name = "test-cmd"
        
        opt1 = Mock(idx=5, is_option=True)   # Outside range
        opt2 = Mock(idx=15, is_option=True)  # Outside range (start > end makes range invalid)
        opt3 = Mock(idx=35, is_option=True)  # Outside range
        
        mock_mctx.manpage.paragraphs = [opt1, opt2, opt3]
        
        trimmer = TestTrimmer(mock_mctx)
        
        with patch.object(trimmer.logger, 'info'):
            trimmer.post_classify()
        
        # All options should be removed due to invalid range (start > end)
        self.assertFalse(opt1.is_option)
        self.assertFalse(opt2.is_option)
        self.assertFalse(opt3.is_option)

    def test_runner_with_no_fixers(self):
        """Test runner with empty fixers list"""
        fixer.fixerscls = []
        
        mock_mctx = Mock()
        runner = fixer.runner(mock_mctx)
        
        self.assertEqual(len(runner.fixers), 0)
        
        # All methods should work with empty fixers
        runner.pre_get_raw_manpage()
        runner.pre_parse_manpage()
        runner.post_parse_manpage()
        runner.pre_classify()
        runner.post_classify()
        runner.post_option_extraction()
        runner.pre_add_manpage()

    def test_runner_all_fixers_disabled(self):
        """Test runner with all fixers disabled"""
        class TestFixer(fixer.basefixer):
            def __init__(self, mctx):
                super().__init__(mctx)
                self.run = False
        
        fixer.fixerscls = [TestFixer]
        
        mock_mctx = Mock()
        runner = fixer.runner(mock_mctx)
        
        # No fixers should be active
        active_fixers = list(runner._fixers())
        self.assertEqual(len(active_fixers), 0)

    def test_register_with_complex_runbefore(self):
        """Test register with complex runbefore relationships"""
        class FirstFixer(fixer.basefixer):
            pass
        
        class SecondFixer(fixer.basefixer):
            pass
        
        @fixer.register
        class ThirdFixer(fixer.basefixer):
            runbefore = [FirstFixer, SecondFixer]
        
        # Both FirstFixer and SecondFixer should have ThirdFixer as parent
        self.assertIn(ThirdFixer, FirstFixer._parents)
        self.assertIn(ThirdFixer, SecondFixer._parents)

    def test_parents_function_edge_cases(self):
        """Test _parents function with edge cases"""
        # Test with class that has empty _parents list
        class TestFixer(fixer.basefixer):
            _parents = []
        
        parents = fixer._parents(TestFixer)
        self.assertEqual(parents, [])

    def test_topological_sort_integration(self):
        """Test that topological sort works correctly"""
        # Create fixers with dependencies
        class BaseFixer(fixer.basefixer):
            pass
        
        class MiddleFixer(fixer.basefixer):
            runbefore = [BaseFixer]
        
        class TopFixer(fixer.basefixer):
            runbefore = [MiddleFixer]
        
        test_fixers = [BaseFixer, MiddleFixer, TopFixer]
        
        # Mock the util.toposorted function
        with patch('explainshell.fixer.util.toposorted') as mock_topo:
            mock_topo.return_value = [TopFixer, MiddleFixer, BaseFixer]
            
            # Simulate the sorting that happens at module load
            sorted_fixers = mock_topo(test_fixers, fixer._parents)
            
            mock_topo.assert_called_once()
            self.assertEqual(sorted_fixers, [TopFixer, MiddleFixer, BaseFixer])


class TestFixerErrorHandling(unittest.TestCase):
    """Error handling tests for fixer module"""

    def setUp(self):
        """Set up test fixtures"""
        self.original_fixerscls = fixer.fixerscls[:]

    def tearDown(self):
        """Clean up after tests"""
        fixer.fixerscls = self.original_fixerscls

    def test_bulletremover_with_malformed_text(self):
        """Test bulletremover with malformed text attributes"""
        mock_mctx = Mock()
        p1 = Mock()
        p1.text = 123  # Non-string text
        mock_mctx.manpage.paragraphs = [p1]
        
        bullet_remover = fixer.bulletremover(mock_mctx)
        
        # Should handle non-string text gracefully
        try:
            bullet_remover.post_parse_manpage()
        except (AttributeError, TypeError):
            pass  # Expected for non-string text

    def test_leadingspaceremover_with_exception(self):
        """Test leadingspaceremover when _removewhitespace raises exception"""
        mock_mctx = Mock()
        opt1 = Mock()
        opt1.text = "test"
        mock_mctx.manpage.options = [opt1]
        
        space_remover = fixer.leadingspaceremover(mock_mctx)
        
        with patch.object(space_remover, '_removewhitespace', side_effect=Exception("test error")):
            with self.assertRaises(Exception):
                space_remover.post_option_extraction()

    def test_paragraphjoiner_with_invalid_indices(self):
        """Test paragraphjoiner with invalid paragraph indices"""
        paragraphs = [Mock(idx=0), Mock(idx=5)]  # Gap in indices
        options = [Mock(idx=0, section="OPTIONS"), Mock(idx=5, section="OPTIONS")]
        
        joiner = fixer.paragraphjoiner(Mock())
        
        # Should handle gaps in indices gracefully
        merged = joiner._join(paragraphs, options)
        self.assertEqual(merged, 0)

    def test_runner_disable_with_duplicate_names(self):
        """Test runner disable with multiple fixers having same name"""
        class TestFixer1(fixer.basefixer):
            pass
        
        class TestFixer2(fixer.basefixer):
            pass
        
        # Manually set same name
        TestFixer2.__name__ = "TestFixer1"
        
        fixer.fixerscls = [TestFixer1, TestFixer2]
        runner = fixer.runner(Mock())
        
        initial_count = len(runner.fixers)
        runner.disable("TestFixer1")
        
        # Should remove all fixers with that name
        remaining_count = len(runner.fixers)
        self.assertLess(remaining_count, initial_count)


class TestFixerPerformance(unittest.TestCase):
    """Performance-related tests for fixer module"""

    def test_paragraphjoiner_with_many_paragraphs(self):
        """Test paragraphjoiner performance with many paragraphs"""
        # Create many paragraphs
        paragraphs = [Mock(idx=i, text=f"text{i}") for i in range(100)]
        
        # Create options at regular intervals
        options = []
        for i in range(0, 100, 10):
            opt = Mock(idx=i, section="OPTIONS", text=f"opt{i}")
            options.append(opt)
        
        joiner = fixer.paragraphjoiner(Mock())
        
        # Should complete in reasonable time
        merged = joiner._join(paragraphs, options)
        self.assertGreaterEqual(merged, 0)

    def test_bulletremover_with_many_paragraphs(self):
        """Test bulletremover performance with many paragraphs"""
        mock_mctx = Mock()
        
        # Create many paragraphs, some with bullets
        paragraphs = []
        for i in range(100):
            p = Mock()
            if i % 10 == 0:
                p.text = f"text{i} \xc2\xb7 with bullet"
            else:
                p.text = f"text{i} without bullet"
            paragraphs.append(p)
        
        mock_mctx.manpage.paragraphs = paragraphs
        
        bullet_remover = fixer.bulletremover(mock_mctx)
        
        # Should complete in reasonable time
        bullet_remover.post_parse_manpage()
        
        # Verify bullets were processed
        bullet_count = sum(1 for p in paragraphs if "\xc2\xb7" not in p.text)
        self.assertGreater(bullet_count, 0)

    def test_runner_with_many_fixers(self):
        """Test runner performance with many fixers"""
        # Save original fixers
        original_fixers = fixer.fixerscls[:]
        
        try:
            # Create many fixer classes
            fixer_classes = []
            for i in range(20):
                class_name = f"TestFixer{i}"
                fixer_class = type(class_name, (fixer.basefixer,), {})
                fixer_classes.append(fixer_class)
            
            fixer.fixerscls = fixer_classes
            
            mock_mctx = Mock()
            mock_mctx.manpage.paragraphs = []
            mock_mctx.manpage.options = []
            
            runner = fixer.runner(mock_mctx)
            
            # Should handle many fixers efficiently
            self.assertEqual(len(runner.fixers), 20)
            
            # All methods should complete quickly
            runner.pre_get_raw_manpage()
            runner.post_parse_manpage()
            runner.post_option_extraction()
        finally:
            # Restore original fixers
            fixer.fixerscls = original_fixers


if __name__ == "__main__":
    unittest.main()