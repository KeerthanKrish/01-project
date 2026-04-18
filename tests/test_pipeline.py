"""
Unit tests for marketplace detection pipeline.
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.preprocessing import ImagePreprocessor, create_preprocessor
from src.utils import Timer, softmax, get_top_k_predictions, calculate_confidence_score


class TestImagePreprocessor:
    """Tests for image preprocessing."""
    
    def test_create_preprocessor(self):
        """Test preprocessor creation."""
        preprocessor = create_preprocessor("clip")
        assert preprocessor is not None
        assert preprocessor.target_size == (224, 224)
    
    def test_normalize_image(self):
        """Test image normalization."""
        preprocessor = create_preprocessor("clip")
        
        # Create a test image
        img_array = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        
        # Normalize
        normalized = preprocessor.normalize_image(img_array)
        
        # Check shape
        assert normalized.shape == (224, 224, 3)
        
        # Check value range (should be roughly [-2, 2] after ImageNet normalization)
        assert normalized.min() >= -3
        assert normalized.max() <= 3
    
    def test_resize_image(self):
        """Test image resizing."""
        preprocessor = create_preprocessor("clip", target_size=(256, 256))
        
        # Create test image
        img = Image.new('RGB', (512, 512), color='red')
        
        # Resize
        resized = preprocessor.resize_image(img)
        
        assert resized.size == (256, 256)
    
    def test_quality_assessment(self):
        """Test image quality assessment."""
        preprocessor = create_preprocessor("clip")
        
        # Create test image
        img = Image.new('RGB', (300, 300), color='blue')
        
        # Assess quality
        quality = preprocessor.assess_quality(img)
        
        # Check required keys
        assert 'blur_score' in quality
        assert 'blur_level' in quality
        assert 'brightness' in quality
        assert 'overall_quality' in quality


class TestUtils:
    """Tests for utility functions."""
    
    def test_timer(self):
        """Test timer context manager."""
        import time
        
        with Timer("Test") as timer:
            time.sleep(0.1)
        
        assert timer.elapsed_ms >= 100
        assert timer.elapsed_ms < 200
    
    def test_softmax(self):
        """Test softmax function."""
        x = np.array([1.0, 2.0, 3.0])
        probs = softmax(x)
        
        # Check sum to 1
        assert np.abs(probs.sum() - 1.0) < 1e-6
        
        # Check all positive
        assert np.all(probs > 0)
        
        # Check monotonic (larger input -> larger output)
        assert probs[0] < probs[1] < probs[2]
    
    def test_get_top_k_predictions(self):
        """Test top-k predictions."""
        probs = np.array([0.1, 0.5, 0.2, 0.2])
        labels = ['a', 'b', 'c', 'd']
        
        top_k = get_top_k_predictions(probs, labels, k=2)
        
        assert len(top_k) == 2
        assert top_k[0]['label'] == 'b'
        assert top_k[0]['confidence'] == 0.5
        assert top_k[1]['label'] in ['c', 'd']
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        # Geometric mean of 0.9 and 0.81 should be 0.9
        score = calculate_confidence_score(0.9, 0.9)
        assert np.abs(score - 0.9) < 1e-6
        
        # Geometric mean of 0.8 and 0.2 should be 0.4
        score = calculate_confidence_score(0.8, 0.2)
        assert np.abs(score - 0.4) < 1e-6
        
        # Single confidence
        score = calculate_confidence_score(0.7)
        assert score == 0.7


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_create_sample_image(self):
        """Test creating a sample image for testing."""
        # Create a simple test image
        img = Image.new('RGB', (300, 300), color='red')
        assert img.size == (300, 300)
        assert img.mode == 'RGB'


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
