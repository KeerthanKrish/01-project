"""
Tier 1 Category Detection using CLIP for zero-shot classification.
"""

import torch
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Union, Optional, Tuple
from transformers import CLIPProcessor, CLIPModel
import warnings

from .utils import Timer, get_top_k_predictions, get_model_cache
from .preprocessing import ImagePreprocessor, create_preprocessor


class CategoryDetector:
    """
    Tier 1 category detector using CLIP for zero-shot classification.
    
    Classifies marketplace items into broad categories without requiring training.
    """
    
    # Default marketplace categories
    DEFAULT_CATEGORIES = [
        "electronics",
        "furniture",
        "clothing and accessories",
        "vehicles and automotive",
        "home and garden",
        "sports and recreation",
        "books and media",
        "baby and kids items",
        "tools and hardware",
        "jewelry and watches",
        "musical instruments",
        "art and collectibles",
        "pet supplies",
        "office supplies",
        "health and beauty",
        "toys and games"
    ]
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-large-patch14",
        categories: Optional[List[str]] = None,
        device: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize category detector.
        
        Args:
            model_name: HuggingFace model identifier
            categories: List of category names (uses defaults if None)
            device: Device to run on ('cuda', 'cpu', or None for auto)
            use_cache: Whether to cache model in memory
        """
        self.model_name = model_name
        self.categories = categories if categories else self.DEFAULT_CATEGORIES
        self.use_cache = use_cache
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Initializing CategoryDetector on {self.device}...")
        
        # Load model and processor
        self._load_model()
        
        # Initialize preprocessor
        self.preprocessor = create_preprocessor("clip", target_size=(224, 224))
        
        print(f"CategoryDetector ready with {len(self.categories)} categories")
    
    def _load_model(self):
        """Load CLIP model and processor."""
        cache = get_model_cache()
        cache_key = f"clip_{self.model_name}"
        
        if self.use_cache and cache.get(cache_key):
            print("Loading model from cache...")
            cached = cache.get(cache_key)
            self.model = cached['model']
            self.processor = cached['processor']
        else:
            print(f"Loading {self.model_name}...")
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            if self.use_cache:
                cache.set(cache_key, {'model': self.model, 'processor': self.processor})
    
    def _prepare_text_prompts(self, categories: List[str]) -> List[str]:
        """
        Create text prompts for categories.
        
        Args:
            categories: List of category names
            
        Returns:
            List of formatted prompts
        """
        # Use template to improve zero-shot performance
        template = "a photo of {}"
        return [template.format(cat) for cat in categories]
    
    def predict(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        top_k: int = 3,
        return_all_scores: bool = False
    ) -> Dict[str, Any]:
        """
        Predict category for a single image.
        
        Args:
            image_input: Image path, PIL Image, or numpy array
            top_k: Number of top predictions to return
            return_all_scores: If True, return scores for all categories
            
        Returns:
            Dictionary with prediction results
        """
        with Timer("Category Detection") as timer:
            # Preprocess image
            if isinstance(image_input, str):
                img = Image.open(image_input).convert('RGB')
            elif isinstance(image_input, np.ndarray):
                img = Image.fromarray(image_input)
            else:
                img = image_input
            
            # Prepare inputs
            text_prompts = self._prepare_text_prompts(self.categories)
            
            with torch.no_grad():
                # Process inputs
                inputs = self.processor(
                    text=text_prompts,
                    images=img,
                    return_tensors="pt",
                    padding=True
                )
                
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Get model outputs
                outputs = self.model(**inputs)
                
                # Calculate similarity scores
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
        
        # Get top-k predictions
        top_predictions = get_top_k_predictions(probs, self.categories, k=top_k)
        
        # Format results
        result = {
            "category": top_predictions[0]['label'],
            "confidence": top_predictions[0]['confidence'],
            "alternatives": top_predictions[1:] if len(top_predictions) > 1 else [],
            "processing_time_ms": timer.elapsed_ms
        }
        
        if return_all_scores:
            result["all_scores"] = {
                cat: float(prob) for cat, prob in zip(self.categories, probs)
            }
        
        return result
    
    def predict_batch(
        self,
        image_inputs: List[Union[str, Image.Image, np.ndarray]],
        top_k: int = 3,
        batch_size: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Predict categories for multiple images.
        
        Args:
            image_inputs: List of image paths, PIL Images, or numpy arrays
            top_k: Number of top predictions to return per image
            batch_size: Number of images to process at once
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        
        # Process in batches
        for i in range(0, len(image_inputs), batch_size):
            batch = image_inputs[i:i+batch_size]
            
            with Timer(f"Batch {i//batch_size + 1}") as timer:
                # Load and prepare images
                images = []
                for img_input in batch:
                    if isinstance(img_input, str):
                        img = Image.open(img_input).convert('RGB')
                    elif isinstance(img_input, np.ndarray):
                        img = Image.fromarray(img_input)
                    else:
                        img = img_input
                    images.append(img)
                
                # Prepare text prompts
                text_prompts = self._prepare_text_prompts(self.categories)
                
                with torch.no_grad():
                    # Process inputs
                    inputs = self.processor(
                        text=text_prompts,
                        images=images,
                        return_tensors="pt",
                        padding=True
                    )
                    
                    # Move to device
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Get model outputs
                    outputs = self.model(**inputs)
                    
                    # Calculate similarity scores
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1).cpu().numpy()
                
                # Format results for each image in batch
                for prob_row in probs:
                    top_predictions = get_top_k_predictions(prob_row, self.categories, k=top_k)
                    
                    result = {
                        "category": top_predictions[0]['label'],
                        "confidence": top_predictions[0]['confidence'],
                        "alternatives": top_predictions[1:] if len(top_predictions) > 1 else []
                    }
                    results.append(result)
            
            print(f"Processed batch {i//batch_size + 1}: {timer}")
        
        return results
    
    def add_category(self, category: str) -> None:
        """
        Add a new category to the detector.
        
        Args:
            category: Category name to add
        """
        if category not in self.categories:
            self.categories.append(category)
            print(f"Added category: {category}")
        else:
            warnings.warn(f"Category '{category}' already exists")
    
    def remove_category(self, category: str) -> None:
        """
        Remove a category from the detector.
        
        Args:
            category: Category name to remove
        """
        if category in self.categories:
            self.categories.remove(category)
            print(f"Removed category: {category}")
        else:
            warnings.warn(f"Category '{category}' not found")
    
    def get_categories(self) -> List[str]:
        """Get list of current categories."""
        return self.categories.copy()
    
    def evaluate(
        self,
        test_images: List[str],
        ground_truth: List[str],
        top_k: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate detector on test set.
        
        Args:
            test_images: List of image paths
            ground_truth: List of true category labels
            top_k: Consider prediction correct if true label in top-k
            
        Returns:
            Dictionary with evaluation metrics
        """
        if len(test_images) != len(ground_truth):
            raise ValueError("Number of images and labels must match")
        
        print(f"Evaluating on {len(test_images)} images...")
        
        predictions = self.predict_batch(test_images, top_k=top_k)
        
        # Calculate accuracy
        correct = 0
        top_k_correct = 0
        
        for pred, true_label in zip(predictions, ground_truth):
            # Top-1 accuracy
            if pred['category'] == true_label:
                correct += 1
            
            # Top-k accuracy
            all_predicted = [pred['category']] + [alt['label'] for alt in pred['alternatives']]
            if true_label in all_predicted[:top_k]:
                top_k_correct += 1
        
        accuracy = correct / len(test_images)
        top_k_accuracy = top_k_correct / len(test_images)
        
        metrics = {
            "total_images": len(test_images),
            "top_1_accuracy": accuracy,
            f"top_{top_k}_accuracy": top_k_accuracy,
            "correct_predictions": correct,
            f"top_{top_k}_correct": top_k_correct
        }
        
        print(f"Top-1 Accuracy: {accuracy:.2%}")
        print(f"Top-{top_k} Accuracy: {top_k_accuracy:.2%}")
        
        return metrics


def create_category_detector(
    model_name: str = "openai/clip-vit-large-patch14",
    custom_categories: Optional[List[str]] = None
) -> CategoryDetector:
    """
    Factory function to create a category detector.
    
    Args:
        model_name: HuggingFace model identifier
        custom_categories: Custom category list (uses defaults if None)
        
    Returns:
        Configured CategoryDetector
    """
    return CategoryDetector(
        model_name=model_name,
        categories=custom_categories
    )


if __name__ == "__main__":
    # Example usage
    print("Initializing Category Detector...")
    detector = create_category_detector()
    
    print(f"\nAvailable categories: {detector.get_categories()}")
    print("\nDetector ready for predictions!")
    
    # To test with an actual image:
    # result = detector.predict("path/to/image.jpg")
    # print(f"\nPrediction: {result}")
