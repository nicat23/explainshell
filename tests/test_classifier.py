import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import explainshell modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explainshell.algo import classifier
from explainshell import store, config


class TestGetFeatures(unittest.TestCase):
    """Tests for get_features function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_paragraph = Mock()

    def test_get_features_basic(self):
        """Test get_features with basic paragraph"""
        self.mock_paragraph.cleantext.return_value = "-v verbose option"
        self.mock_paragraph.section = "OPTIONS"
        
        with patch('explainshell.algo.classifier.features') as mock_features:
            # Mock all feature functions
            mock_features.starts_with_hyphen.return_value = True
            mock_features.is_indented.return_value = False
            mock_features.par_length.return_value = 15
            mock_features.first_line_contains.return_value = False
            mock_features.first_line_length.return_value = 15
            mock_features.first_line_word_count.return_value = 3
            mock_features.is_good_section.return_value = True
            mock_features.word_count.return_value = 3
            
            features_dict = classifier.get_features(self.mock_paragraph)
            
            # Verify all expected features are present
            expected_keys = [
                "starts_with_hyphen", "is_indented", "par_length",
                "first_line_contains_=", "first_line_contains_--",
                "first_line_contains_[", "first_line_contains_|",
                "first_line_contains_,", "first_line_length",
                "first_line_word_count", "is_good_section", "word_count"
            ]
            
            for key in expected_keys:
                self.assertIn(key, features_dict)
            
            # Verify feature function calls
            mock_features.starts_with_hyphen.assert_called_once_with("-v verbose option")
            mock_features.is_indented.assert_called_once_with("-v verbose option")
            mock_features.par_length.assert_called_once_with("-v verbose option")
            mock_features.is_good_section.assert_called_once_with(self.mock_paragraph)

    def test_get_features_empty_text_assertion(self):
        """Test get_features with empty text raises assertion"""
        self.mock_paragraph.cleantext.return_value = ""
        
        with self.assertRaises(AssertionError):
            classifier.get_features(self.mock_paragraph)

    def test_get_features_none_text_assertion(self):
        """Test get_features with None text raises assertion"""
        self.mock_paragraph.cleantext.return_value = None
        
        with self.assertRaises(AssertionError):
            classifier.get_features(self.mock_paragraph)

    def test_get_features_special_characters(self):
        """Test get_features with special characters in text"""
        self.mock_paragraph.cleantext.return_value = "--verbose=value [option] | pipe, comma"
        self.mock_paragraph.section = "OPTIONS"
        
        with patch('explainshell.algo.classifier.features') as mock_features:
            mock_features.starts_with_hyphen.return_value = True
            mock_features.is_indented.return_value = True
            mock_features.par_length.return_value = 40
            mock_features.first_line_contains.side_effect = lambda text, char: char in text
            mock_features.first_line_length.return_value = 40
            mock_features.first_line_word_count.return_value = 5
            mock_features.is_good_section.return_value = True
            mock_features.word_count.return_value = 5
            
            features_dict = classifier.get_features(self.mock_paragraph)
            
            # Verify special character features
            self.assertTrue(features_dict["first_line_contains_="])
            self.assertTrue(features_dict["first_line_contains_--"])
            self.assertTrue(features_dict["first_line_contains_["])
            self.assertTrue(features_dict["first_line_contains_|"])
            self.assertTrue(features_dict["first_line_contains_,"])

    def test_get_features_all_feature_calls(self):
        """Test that get_features calls all expected feature functions"""
        self.mock_paragraph.cleantext.return_value = "test paragraph"
        self.mock_paragraph.section = "DESCRIPTION"
        
        with patch('explainshell.algo.classifier.features') as mock_features:
            # Set up return values
            mock_features.starts_with_hyphen.return_value = False
            mock_features.is_indented.return_value = True
            mock_features.par_length.return_value = 14
            mock_features.first_line_contains.return_value = False
            mock_features.first_line_length.return_value = 14
            mock_features.first_line_word_count.return_value = 2
            mock_features.is_good_section.return_value = False
            mock_features.word_count.return_value = 2
            
            classifier.get_features(self.mock_paragraph)
            
            # Verify all feature functions were called
            mock_features.starts_with_hyphen.assert_called_once()
            mock_features.is_indented.assert_called_once()
            mock_features.par_length.assert_called_once()
            mock_features.first_line_length.assert_called_once()
            mock_features.first_line_word_count.assert_called_once()
            mock_features.is_good_section.assert_called_once()
            mock_features.word_count.assert_called_once()
            
            # Verify first_line_contains called for each special character
            expected_chars = ["=", "--", "[", "|", ","]
            self.assertEqual(mock_features.first_line_contains.call_count, len(expected_chars))


class TestClassifier(unittest.TestCase):
    """Tests for classifier class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_store = Mock()
        self.classifier_obj = classifier.classifier(self.mock_store, "maxent")

    def test_classifier_init(self):
        """Test classifier initialization"""
        c = classifier.classifier(self.mock_store, "bayes", max_iter=10)
        self.assertEqual(c.store, self.mock_store)
        self.assertEqual(c.algo, "bayes")
        self.assertEqual(c.classifier_args, {"max_iter": 10})
        self.assertIsNone(c.classifier)

    def test_classifier_init_invalid_algo(self):
        """Test classifier with invalid algorithm"""
        c = classifier.classifier(self.mock_store, "invalid")
        
        # Mock empty training data to reach the ValueError
        self.mock_store.trainingset.return_value = []
        
        with self.assertRaises(ValueError):
            c.train()

    @patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier')
    @patch('explainshell.algo.classifier.get_features')
    def test_train_maxent(self, mock_get_features, mock_maxent):
        """Test training with maxent classifier"""
        # Create mock training data
        mock_pos_para = Mock()
        mock_pos_para.is_option = True
        mock_neg_para = Mock()
        mock_neg_para.is_option = False
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_pos_para, mock_neg_para]
        
        self.mock_store.trainingset.return_value = [mock_manpage]
        
        # Mock feature extraction
        mock_get_features.side_effect = [
            {"feature1": True}, {"feature2": False}
        ]
        
        # Mock classifier training
        mock_trained_classifier = Mock()
        mock_maxent.train.return_value = mock_trained_classifier
        
        self.classifier_obj.train()
        
        # Verify training was called
        mock_maxent.train.assert_called_once()
        self.assertEqual(self.classifier_obj.classifier, mock_trained_classifier)
        
        # Verify training data was processed
        self.mock_store.trainingset.assert_called_once()

    @patch('explainshell.algo.classifier.nltk.classify.NaiveBayesClassifier')
    @patch('explainshell.algo.classifier.get_features')
    def test_train_bayes(self, mock_get_features, mock_bayes):
        """Test training with naive bayes classifier"""
        c = classifier.classifier(self.mock_store, "bayes")
        
        # Create mock training data
        mock_para = Mock()
        mock_para.is_option = True
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_para]
        
        self.mock_store.trainingset.return_value = [mock_manpage]
        mock_get_features.return_value = {"feature": True}
        
        mock_trained_classifier = Mock()
        mock_bayes.train.return_value = mock_trained_classifier
        
        c.train()
        
        mock_bayes.train.assert_called_once()
        self.assertEqual(c.classifier, mock_trained_classifier)

    @patch('explainshell.algo.classifier.get_features')
    def test_train_data_splitting(self, mock_get_features):
        """Test that training data is properly split"""
        # Create multiple paragraphs for testing split
        pos_paras = [Mock(is_option=True) for _ in range(8)]
        neg_paras = [Mock(is_option=False) for _ in range(8)]
        all_paras = pos_paras + neg_paras
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = all_paras
        
        self.mock_store.trainingset.return_value = [mock_manpage]
        mock_get_features.return_value = {"feature": True}
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_maxent.train.return_value = Mock()
            
            self.classifier_obj.train()
            
            # Verify train was called with proper split (3/4 for training)
            args, kwargs = mock_maxent.train.call_args
            training_data = args[0]
            
            # Should have 6 positive + 6 negative = 12 training instances
            self.assertEqual(len(training_data), 12)
            
            # Verify testfeats has remaining data (2 positive + 2 negative = 4)
            self.assertEqual(len(self.classifier_obj.testfeats), 4)

    def test_train_already_trained(self):
        """Test that train() doesn't retrain if already trained"""
        mock_classifier = Mock()
        self.classifier_obj.classifier = mock_classifier
        
        self.classifier_obj.train()
        
        # Should not call trainingset if already trained
        self.mock_store.trainingset.assert_not_called()
        self.assertEqual(self.classifier_obj.classifier, mock_classifier)

    @patch('explainshell.algo.classifier.nltk.metrics')
    def test_evaluate(self, mock_metrics):
        """Test evaluate method"""
        # Set up trained classifier
        mock_classifier = Mock()
        mock_prob_dist = Mock()
        mock_prob_dist.max.return_value = True
        mock_classifier.prob_classify.return_value = mock_prob_dist
        
        self.classifier_obj.classifier = mock_classifier
        self.classifier_obj.testfeats = [
            ({"feature": True}, True),
            ({"feature": False}, False)
        ]
        
        # Mock metrics functions
        mock_metrics.precision.return_value = 0.8
        mock_metrics.recall.return_value = 0.9
        
        with patch('builtins.print') as mock_print:
            self.classifier_obj.evaluate()
            
            # Verify metrics were calculated
            self.assertEqual(mock_metrics.precision.call_count, 2)
            self.assertEqual(mock_metrics.recall.call_count, 2)
            
            # Verify results were printed
            self.assertTrue(mock_print.called)

    @patch('explainshell.algo.classifier.get_features')
    def test_classify(self, mock_get_features):
        """Test classify method"""
        # Set up trained classifier
        mock_classifier = Mock()
        mock_prob_dist = Mock()
        mock_prob_dist.max.return_value = True
        mock_prob_dist.prob.return_value = 0.9  # Above cutoff
        mock_classifier.prob_classify.return_value = mock_prob_dist
        
        self.classifier_obj.classifier = mock_classifier
        
        # Create mock manpage with paragraphs
        mock_para1 = Mock()
        mock_para1.is_option = False
        mock_para2 = Mock()
        mock_para2.is_option = False
        
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_para1, mock_para2]
        
        mock_get_features.return_value = {"feature": True}
        
        with patch.object(config, 'CLASSIFIER_CUTOFF', 0.8):
            results = list(self.classifier_obj.classify(mock_manpage))
            
            # Should yield results for paragraphs above cutoff
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], (0.9, mock_para1))
            self.assertEqual(results[1], (0.9, mock_para2))
            
            # Verify paragraphs were marked as options
            self.assertTrue(mock_para1.is_option)
            self.assertTrue(mock_para2.is_option)

    @patch('explainshell.algo.classifier.get_features')
    def test_classify_below_cutoff(self, mock_get_features):
        """Test classify with certainty below cutoff"""
        mock_classifier = Mock()
        mock_prob_dist = Mock()
        mock_prob_dist.max.return_value = True
        mock_prob_dist.prob.return_value = 0.5  # Below cutoff
        mock_classifier.prob_classify.return_value = mock_prob_dist
        
        self.classifier_obj.classifier = mock_classifier
        
        mock_para = Mock()
        mock_para.is_option = False
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_para]
        
        mock_get_features.return_value = {"feature": True}
        
        with patch.object(config, 'CLASSIFIER_CUTOFF', 0.8):
            results = list(self.classifier_obj.classify(mock_manpage))
            
            # Should not yield results below cutoff
            self.assertEqual(len(results), 0)
            self.assertFalse(mock_para.is_option)

    @patch('explainshell.algo.classifier.get_features')
    def test_classify_negative_classification(self, mock_get_features):
        """Test classify with negative classification"""
        mock_classifier = Mock()
        mock_prob_dist = Mock()
        mock_prob_dist.max.return_value = False  # Classified as not option
        mock_prob_dist.prob.return_value = 0.9
        mock_classifier.prob_classify.return_value = mock_prob_dist
        
        self.classifier_obj.classifier = mock_classifier
        
        mock_para = Mock()
        mock_para.is_option = False
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_para]
        
        mock_get_features.return_value = {"feature": False}
        
        results = list(self.classifier_obj.classify(mock_manpage))
        
        # Should not yield results for negative classification
        self.assertEqual(len(results), 0)
        self.assertFalse(mock_para.is_option)

    def test_classify_calls_train(self):
        """Test that classify calls train if not already trained"""
        mock_manpage = Mock()
        mock_manpage.paragraphs = []
        
        with patch.object(self.classifier_obj, 'train') as mock_train:
            list(self.classifier_obj.classify(mock_manpage))
            mock_train.assert_called_once()


class TestClassifierIntegration(unittest.TestCase):
    """Integration tests for classifier module"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.mock_store = Mock()

    def test_full_classification_workflow(self):
        """Test complete classification workflow"""
        # Create realistic training data
        option_para = Mock()
        option_para.is_option = True
        option_para.cleantext.return_value = "-v, --verbose  Enable verbose output"
        option_para.section = "OPTIONS"
        
        desc_para = Mock()
        desc_para.is_option = False
        desc_para.cleantext.return_value = "This program does something useful."
        desc_para.section = "DESCRIPTION"
        
        training_manpage = Mock()
        training_manpage.paragraphs = [option_para, desc_para] * 10  # Duplicate for training
        
        self.mock_store.trainingset.return_value = [training_manpage]
        
        # Create test manpage
        test_para = Mock()
        test_para.is_option = False
        test_para.cleantext.return_value = "-h, --help  Show help message"
        test_para.section = "OPTIONS"
        
        test_manpage = Mock()
        test_manpage.paragraphs = [test_para]
        
        # Test with maxent classifier
        c = classifier.classifier(self.mock_store, "maxent")
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_trained_classifier = Mock()
            mock_prob_dist = Mock()
            mock_prob_dist.max.return_value = True
            mock_prob_dist.prob.return_value = 0.95
            mock_trained_classifier.prob_classify.return_value = mock_prob_dist
            mock_maxent.train.return_value = mock_trained_classifier
            
            with patch.object(config, 'CLASSIFIER_CUTOFF', 0.8):
                results = list(c.classify(test_manpage))
                
                self.assertEqual(len(results), 1)
                certainty, paragraph = results[0]
                self.assertEqual(certainty, 0.95)
                self.assertEqual(paragraph, test_para)
                self.assertTrue(test_para.is_option)

    def test_classifier_with_empty_training_data(self):
        """Test classifier behavior with empty training data"""
        self.mock_store.trainingset.return_value = []
        
        c = classifier.classifier(self.mock_store, "maxent")
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_maxent.train.return_value = Mock()
            
            c.train()
            
            # Should still attempt to train with empty data
            mock_maxent.train.assert_called_once()
            args, kwargs = mock_maxent.train.call_args
            training_data = args[0]
            self.assertEqual(len(training_data), 0)

    def test_classifier_feature_extraction_integration(self):
        """Test integration between classifier and feature extraction"""
        # Create paragraph with realistic content
        para = Mock()
        para.cleantext.return_value = "    -v, --verbose\n        Enable verbose output mode"
        para.section = "OPTIONS"
        
        # Test actual feature extraction (not mocked)
        with patch('explainshell.algo.classifier.features') as mock_features:
            mock_features.starts_with_hyphen.return_value = False  # Indented
            mock_features.is_indented.return_value = True
            mock_features.par_length.return_value = 50
            mock_features.first_line_contains.return_value = False
            mock_features.first_line_length.return_value = 17
            mock_features.first_line_word_count.return_value = 2
            mock_features.is_good_section.return_value = True
            mock_features.word_count.return_value = 6
            
            features_dict = classifier.get_features(para)
            
            # Verify realistic feature values
            self.assertFalse(features_dict["starts_with_hyphen"])  # Indented option
            self.assertTrue(features_dict["is_indented"])
            self.assertTrue(features_dict["is_good_section"])
            self.assertEqual(features_dict["par_length"], 50)

    def test_classifier_args_passing(self):
        """Test that classifier arguments are properly passed"""
        classifier_args = {"max_iter": 100, "trace": 0}
        c = classifier.classifier(self.mock_store, "maxent", **classifier_args)
        
        self.mock_store.trainingset.return_value = []
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_maxent.train.return_value = Mock()
            
            c.train()
            
            # Verify classifier args were passed to train
            args, kwargs = mock_maxent.train.call_args
            self.assertEqual(kwargs, classifier_args)

    def test_evaluate_with_no_classifier(self):
        """Test evaluate method when classifier is None"""
        c = classifier.classifier(self.mock_store, "maxent")
        c.classifier = None
        c.testfeats = [({"feature": True}, True)]
        
        # Mock empty training data to avoid train() issues
        self.mock_store.trainingset.return_value = []
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_maxent.train.return_value = None
            
            with patch('explainshell.algo.classifier.nltk.metrics') as mock_metrics:
                mock_metrics.precision.return_value = 0.0
                mock_metrics.recall.return_value = 0.0
                
                with patch('builtins.print') as mock_print:
                    c.evaluate()
                    
                    # Should still run evaluation even with None classifier
                    self.assertTrue(mock_print.called)

    def test_classify_with_no_classifier(self):
        """Test classify method when classifier is None"""
        c = classifier.classifier(self.mock_store, "maxent")
        c.classifier = None
        
        mock_para = Mock()
        mock_para.cleantext.return_value = "test"
        mock_para.section = "OPTIONS"  # Add section for is_good_section
        mock_manpage = Mock()
        mock_manpage.paragraphs = [mock_para]
        
        self.mock_store.trainingset.return_value = []
        
        with patch('explainshell.algo.classifier.nltk.classify.maxent.MaxentClassifier') as mock_maxent:
            mock_maxent.train.return_value = None
            
            with patch('explainshell.algo.classifier.get_features') as mock_get_features:
                mock_get_features.return_value = {"feature": True}
                
                results = list(c.classify(mock_manpage))
                
                # Should return empty results when classifier is None
                self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()