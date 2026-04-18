"""
Utility functions for marketplace vision system.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np


def ensure_dir(directory: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory: Path to directory
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def save_json(data: Dict[Any, Any], filepath: str, indent: int = 2) -> None:
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path to output file
        indent: JSON indentation level
    """
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(filepath: str) -> Dict[Any, Any]:
    """
    Load JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
    
    def __str__(self):
        return f"{self.name} took {self.elapsed_ms:.2f}ms"


def softmax(x: np.ndarray) -> np.ndarray:
    """
    Compute softmax values for array.
    
    Args:
        x: Input array
        
    Returns:
        Softmax probabilities
    """
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum()


def get_top_k_predictions(
    probabilities: np.ndarray,
    labels: list,
    k: int = 3
) -> list:
    """
    Get top-k predictions with labels and scores.
    
    Args:
        probabilities: Array of probabilities
        labels: List of label names
        k: Number of top predictions to return
        
    Returns:
        List of dicts with 'label', 'confidence' keys
    """
    top_k_indices = np.argsort(probabilities)[-k:][::-1]
    
    predictions = []
    for idx in top_k_indices:
        predictions.append({
            'label': labels[idx],
            'confidence': float(probabilities[idx])
        })
    
    return predictions


def format_output(
    tier1_result: Dict[str, Any],
    tier2_result: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format detection results into standard output structure.
    
    Args:
        tier1_result: Category detection results
        tier2_result: Attribute detection results (optional)
        metadata: Additional metadata (optional)
        
    Returns:
        Formatted output dictionary
    """
    output = {
        "tier1": tier1_result,
        "tier2": tier2_result if tier2_result else {},
        "metadata": metadata if metadata else {}
    }
    
    return output


def calculate_confidence_score(
    tier1_confidence: float,
    tier2_confidence: Optional[float] = None
) -> float:
    """
    Calculate overall confidence score.
    
    Args:
        tier1_confidence: Tier 1 confidence
        tier2_confidence: Tier 2 confidence (optional)
        
    Returns:
        Combined confidence score
    """
    if tier2_confidence is None:
        return tier1_confidence
    
    # Geometric mean of confidences
    return np.sqrt(tier1_confidence * tier2_confidence)


def is_confident_prediction(
    confidence: float,
    threshold: float = 0.7
) -> bool:
    """
    Check if prediction confidence exceeds threshold.
    
    Args:
        confidence: Prediction confidence
        threshold: Confidence threshold
        
    Returns:
        True if confident
    """
    return confidence >= threshold


class ModelCache:
    """Simple model cache to avoid reloading."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str):
        """Get model from cache."""
        return self._cache.get(key)
    
    def set(self, key: str, model):
        """Store model in cache."""
        self._cache[key] = model
    
    def clear(self):
        """Clear all cached models."""
        self._cache.clear()


# Global model cache
_model_cache = ModelCache()


def get_model_cache() -> ModelCache:
    """Get global model cache instance."""
    return _model_cache


if __name__ == "__main__":
    print("Utility module loaded successfully!")
