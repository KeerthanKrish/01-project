"""
Tier 2 Electronics Detector - Brand and model recognition for electronic items.
"""

import torch
import numpy as np
from PIL import Image
from typing import Dict, Any, Union, Optional, List
from transformers import CLIPProcessor, CLIPModel
import warnings

from ..utils import Timer, get_top_k_predictions, get_model_cache


class ElectronicsDetector:
    """
    Specialized detector for electronics attributes.
    
    Detects:
    - Product type (smartphone, laptop, camera, headphones, etc.)
    - Brand (Apple, Samsung, Sony, etc.)
    - Condition (new, used, refurbished, damaged)
    - Color
    """
    
    # Electronics product types
    PRODUCT_TYPES = [
        "smartphone",
        "laptop computer",
        "desktop computer",
        "tablet",
        "camera",
        "headphones",
        "earbuds",
        "smartwatch",
        "gaming console",
        "television",
        "monitor",
        "keyboard",
        "mouse",
        "speaker",
        "router",
        "printer",
        "drone",
        "e-reader"
    ]
    
    # Major brands
    BRANDS = [
        "Apple",
        "Samsung",
        "Sony",
        "Microsoft",
        "Dell",
        "HP",
        "Lenovo",
        "Asus",
        "Acer",
        "LG",
        "Google",
        "OnePlus",
        "Huawei",
        "Xiaomi",
        "Canon",
        "Nikon",
        "Bose",
        "JBL",
        "Beats",
        "Logitech",
        "Razer",
        "Nintendo",
        "PlayStation",
        "Xbox",
        "Amazon",
        "GoPro",
        "DJI",
        "Generic/Unknown"
    ]
    
    # Condition states
    CONDITIONS = [
        "brand new in box",
        "like new",
        "good used condition",
        "fair condition with wear",
        "damaged or for parts"
    ]
    
    # Common colors
    COLORS = [
        "black",
        "white",
        "silver",
        "gray",
        "gold",
        "rose gold",
        "blue",
        "red",
        "green",
        "pink",
        "purple",
        "multicolor"
    ]
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-large-patch14",
        device: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize electronics detector.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run on ('cuda', 'cpu', or None for auto)
            use_cache: Whether to cache model in memory
        """
        self.model_name = model_name
        self.use_cache = use_cache
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Initializing ElectronicsDetector on {self.device}...")
        
        # Load model and processor
        self._load_model()
        
        print("ElectronicsDetector ready")
    
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
    
    def _classify_attribute(
        self,
        image: Image.Image,
        options: List[str],
        prompt_template: str = "a photo of a {} electronic device",
        top_k: int = 1
    ) -> Dict[str, Any]:
        """
        Classify a specific attribute using CLIP.
        
        Args:
            image: PIL Image
            options: List of possible values
            prompt_template: Template for text prompts
            top_k: Number of top predictions
            
        Returns:
            Dictionary with predictions
        """
        # Prepare text prompts
        text_prompts = [prompt_template.format(opt) for opt in options]
        
        with torch.no_grad():
            # Process inputs
            inputs = self.processor(
                text=text_prompts,
                images=image,
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
        
        # Get top predictions
        top_predictions = get_top_k_predictions(probs, options, k=top_k)
        
        return {
            "value": top_predictions[0]['label'],
            "confidence": top_predictions[0]['confidence'],
            "alternatives": top_predictions[1:] if len(top_predictions) > 1 else []
        }
    
    def detect_product_type(
        self,
        image: Image.Image,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Detect the type of electronic product.
        
        Args:
            image: PIL Image
            top_k: Number of top predictions
            
        Returns:
            Dictionary with product type predictions
        """
        return self._classify_attribute(
            image,
            self.PRODUCT_TYPES,
            prompt_template="a photo of a {}",
            top_k=top_k
        )
    
    def detect_brand(
        self,
        image: Image.Image,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Detect the brand of the electronic product.
        
        Args:
            image: PIL Image
            top_k: Number of top predictions
            
        Returns:
            Dictionary with brand predictions
        """
        return self._classify_attribute(
            image,
            self.BRANDS,
            prompt_template="a {} brand electronic product",
            top_k=top_k
        )
    
    def detect_condition(
        self,
        image: Image.Image,
        top_k: int = 2
    ) -> Dict[str, Any]:
        """
        Assess the condition of the product.
        
        Args:
            image: PIL Image
            top_k: Number of top predictions
            
        Returns:
            Dictionary with condition predictions
        """
        return self._classify_attribute(
            image,
            self.CONDITIONS,
            prompt_template="a product in {}",
            top_k=top_k
        )
    
    def detect_color(
        self,
        image: Image.Image,
        top_k: int = 2
    ) -> Dict[str, Any]:
        """
        Detect the primary color of the product.
        
        Args:
            image: PIL Image
            top_k: Number of top predictions
            
        Returns:
            Dictionary with color predictions
        """
        return self._classify_attribute(
            image,
            self.COLORS,
            prompt_template="a {} colored product",
            top_k=top_k
        )
    
    def predict(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        detect_all: bool = True
    ) -> Dict[str, Any]:
        """
        Predict all electronics attributes.
        
        Args:
            image_input: Image path, PIL Image, or numpy array
            detect_all: If True, detect all attributes; else just product type
            
        Returns:
            Dictionary with all detected attributes
        """
        with Timer("Electronics Detection") as timer:
            # Load image
            if isinstance(image_input, str):
                img = Image.open(image_input).convert('RGB')
            elif isinstance(image_input, np.ndarray):
                img = Image.fromarray(image_input)
            else:
                img = image_input
            
            # Detect product type (always)
            product_type_result = self.detect_product_type(img, top_k=3)
            
            result = {
                "product_type": product_type_result['value'],
                "product_type_confidence": product_type_result['confidence'],
                "product_type_alternatives": product_type_result['alternatives']
            }
            
            if detect_all:
                # Detect brand
                brand_result = self.detect_brand(img, top_k=3)
                result["brand"] = brand_result['value']
                result["brand_confidence"] = brand_result['confidence']
                result["brand_alternatives"] = brand_result['alternatives']
                
                # Detect condition
                condition_result = self.detect_condition(img, top_k=2)
                result["condition"] = condition_result['value']
                result["condition_confidence"] = condition_result['confidence']
                
                # Detect color
                color_result = self.detect_color(img, top_k=2)
                result["color"] = color_result['value']
                result["color_confidence"] = color_result['confidence']
                
                # Calculate overall confidence (average of all attributes)
                confidences = [
                    product_type_result['confidence'],
                    brand_result['confidence'],
                    condition_result['confidence'],
                    color_result['confidence']
                ]
                result["overall_confidence"] = float(np.mean(confidences))
            else:
                result["overall_confidence"] = product_type_result['confidence']
            
            result["processing_time_ms"] = timer.elapsed_ms
        
        return result
    
    def predict_batch(
        self,
        image_inputs: List[Union[str, Image.Image, np.ndarray]],
        detect_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Predict attributes for multiple images.
        
        Args:
            image_inputs: List of image paths, PIL Images, or numpy arrays
            detect_all: If True, detect all attributes
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        
        for img_input in image_inputs:
            try:
                result = self.predict(img_input, detect_all=detect_all)
                results.append(result)
            except Exception as e:
                warnings.warn(f"Failed to process image: {str(e)}")
                results.append({"error": str(e)})
        
        return results


def create_electronics_detector(
    model_name: str = "openai/clip-vit-large-patch14"
) -> ElectronicsDetector:
    """
    Factory function to create an electronics detector.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        Configured ElectronicsDetector
    """
    return ElectronicsDetector(model_name=model_name)


if __name__ == "__main__":
    # Example usage
    print("Initializing Electronics Detector...")
    detector = create_electronics_detector()
    
    print("\nDetector ready for predictions!")
    print(f"Product types: {len(detector.PRODUCT_TYPES)}")
    print(f"Brands: {len(detector.BRANDS)}")
    
    # To test with an actual image:
    # result = detector.predict("path/to/phone.jpg")
    # print(f"\nPrediction: {result}")
