"""
End-to-end marketplace item detection pipeline.
Combines Tier 1 category detection with Tier 2 specialized attribute extraction.
"""

import numpy as np
from PIL import Image
from typing import Dict, Any, Union, Optional, List
import warnings
import time

from .tier1_detector import CategoryDetector, create_category_detector
from .tier2_detectors.electronics import ElectronicsDetector, create_electronics_detector
from .preprocessing import ImagePreprocessor, create_preprocessor
from .utils import Timer, format_output, calculate_confidence_score, is_confident_prediction


class MarketplaceDetectionPipeline:
    """
    Complete detection pipeline for marketplace items.
    
    Workflow:
    1. Preprocess image (resize, normalize, quality check)
    2. Tier 1: Detect general category
    3. Tier 2: Route to specialized detector based on category
    4. Return structured output with all attributes
    """
    
    # Categories that have specialized Tier 2 detectors
    SPECIALIZED_CATEGORIES = {
        "electronics": "electronics",
        # Future categories can be added here
        # "furniture": "furniture",
        # "clothing and accessories": "clothing",
        # "vehicles and automotive": "vehicles"
    }
    
    def __init__(
        self,
        tier1_model: str = "openai/clip-vit-large-patch14",
        tier2_model: str = "openai/clip-vit-large-patch14",
        confidence_threshold: float = 0.5,
        enable_tier2: bool = True,
        enable_quality_check: bool = True
    ):
        """
        Initialize the detection pipeline.
        
        Args:
            tier1_model: Model for category detection
            tier2_model: Model for attribute detection
            confidence_threshold: Minimum confidence to proceed to Tier 2
            enable_tier2: Whether to run Tier 2 detection
            enable_quality_check: Whether to assess image quality
        """
        self.confidence_threshold = confidence_threshold
        self.enable_tier2 = enable_tier2
        self.enable_quality_check = enable_quality_check
        
        print("Initializing Marketplace Detection Pipeline...")
        
        # Initialize preprocessor
        self.preprocessor = create_preprocessor("clip")
        
        # Initialize Tier 1 detector
        print("\n[1/2] Loading Tier 1 detector...")
        self.tier1_detector = create_category_detector(model_name=tier1_model)
        
        # Initialize Tier 2 detectors
        print("\n[2/2] Loading Tier 2 detectors...")
        self.tier2_detectors = {}
        
        # Load electronics detector
        self.tier2_detectors['electronics'] = create_electronics_detector(model_name=tier2_model)
        
        print("\nPipeline ready!")
        print(f"- Tier 1 categories: {len(self.tier1_detector.get_categories())}")
        print(f"- Tier 2 specialized detectors: {len(self.tier2_detectors)}")
        print(f"- Confidence threshold: {self.confidence_threshold}")
    
    def _route_to_tier2(
        self,
        category: str,
        image: Image.Image
    ) -> Optional[Dict[str, Any]]:
        """
        Route to appropriate Tier 2 detector based on category.
        
        Args:
            category: Detected category from Tier 1
            image: PIL Image
            
        Returns:
            Tier 2 results or None if no specialized detector
        """
        # Check if category has a specialized detector
        detector_key = None
        for key_category, detector_name in self.SPECIALIZED_CATEGORIES.items():
            if key_category in category.lower():
                detector_key = detector_name
                break
        
        if detector_key and detector_key in self.tier2_detectors:
            detector = self.tier2_detectors[detector_key]
            return detector.predict(image, detect_all=True)
        else:
            return None
    
    def predict(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        return_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete detection pipeline on a single image.
        
        Args:
            image_input: Image path, PIL Image, or numpy array
            return_metadata: Whether to include detailed metadata
            
        Returns:
            Dictionary with complete detection results
        """
        with Timer("Full Pipeline") as pipeline_timer:
            # Load and preprocess image
            if isinstance(image_input, str):
                img = Image.open(image_input).convert('RGB')
                source = image_input
            elif isinstance(image_input, np.ndarray):
                img = Image.fromarray(image_input)
                source = "array"
            else:
                img = image_input
                source = "PIL Image"
            
            metadata = {
                "source": source,
                "image_size": img.size
            }
            
            # Quality assessment (optional)
            if self.enable_quality_check:
                img_array = np.array(img)
                quality = self.preprocessor.assess_quality(img)
                metadata["quality"] = quality
                
                # Warn if quality is poor
                if quality.get("overall_quality") == "poor":
                    warnings.warn("Image quality is poor, predictions may be unreliable")
            
            # Tier 1: Category Detection
            with Timer("Tier 1") as tier1_timer:
                tier1_result = self.tier1_detector.predict(
                    img,
                    top_k=3,
                    return_all_scores=False
                )
            
            detected_category = tier1_result["category"]
            tier1_confidence = tier1_result["confidence"]
            
            print(f"Tier 1: {detected_category} (confidence: {tier1_confidence:.2%})")
            
            # Tier 2: Specialized Detection
            tier2_result = {}
            if self.enable_tier2:
                # Check if confidence is high enough
                if is_confident_prediction(tier1_confidence, self.confidence_threshold):
                    with Timer("Tier 2") as tier2_timer:
                        tier2_result = self._route_to_tier2(detected_category, img)
                    
                    if tier2_result:
                        print(f"Tier 2: Detected {tier2_result.get('product_type', 'attributes')}")
                    else:
                        print(f"Tier 2: No specialized detector for '{detected_category}'")
                        tier2_result = {
                            "message": f"No specialized detector available for category '{detected_category}'"
                        }
                else:
                    print(f"Tier 2: Skipped (confidence {tier1_confidence:.2%} < {self.confidence_threshold:.2%})")
                    tier2_result = {
                        "message": f"Tier 1 confidence too low ({tier1_confidence:.2%})"
                    }
            
            # Calculate overall confidence
            if tier2_result and "overall_confidence" in tier2_result:
                overall_confidence = calculate_confidence_score(
                    tier1_confidence,
                    tier2_result["overall_confidence"]
                )
            else:
                overall_confidence = tier1_confidence
            
            # Add timing metadata
            if return_metadata:
                metadata["tier1_time_ms"] = tier1_timer.elapsed_ms
                if tier2_result and "processing_time_ms" in tier2_result:
                    metadata["tier2_time_ms"] = tier2_result.pop("processing_time_ms")
                # Calculate total time manually since we're still in context
                metadata["total_time_ms"] = (time.time() - pipeline_timer.start_time) * 1000
                metadata["overall_confidence"] = float(overall_confidence)
        
        # Format output
        output = format_output(tier1_result, tier2_result, metadata if return_metadata else None)
        
        # Calculate final elapsed time
        total_ms = (time.time() - pipeline_timer.start_time) * 1000
        print(f"Pipeline complete in {total_ms:.0f}ms")
        
        return output
    
    def predict_batch(
        self,
        image_inputs: List[Union[str, Image.Image, np.ndarray]],
        return_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Run detection pipeline on multiple images.
        
        Args:
            image_inputs: List of image paths, PIL Images, or numpy arrays
            return_metadata: Whether to include detailed metadata
            
        Returns:
            List of detection results
        """
        results = []
        
        print(f"\nProcessing {len(image_inputs)} images...")
        
        for i, img_input in enumerate(image_inputs, 1):
            print(f"\n--- Image {i}/{len(image_inputs)} ---")
            try:
                result = self.predict(img_input, return_metadata=return_metadata)
                results.append(result)
            except Exception as e:
                warnings.warn(f"Failed to process image {i}: {str(e)}")
                results.append({
                    "error": str(e),
                    "tier1": {},
                    "tier2": {},
                    "metadata": {}
                })
        
        return results
    
    def add_tier2_detector(
        self,
        category: str,
        detector,
        detector_key: Optional[str] = None
    ) -> None:
        """
        Add a new Tier 2 specialized detector.
        
        Args:
            category: Category name this detector handles
            detector: Detector instance
            detector_key: Key to store detector (defaults to category)
        """
        if detector_key is None:
            detector_key = category.lower().replace(" ", "_")
        
        self.tier2_detectors[detector_key] = detector
        self.SPECIALIZED_CATEGORIES[category] = detector_key
        
        print(f"Added Tier 2 detector for '{category}'")
    
    def get_supported_categories(self) -> Dict[str, bool]:
        """
        Get list of categories and whether they have Tier 2 support.
        
        Returns:
            Dictionary mapping category to has_tier2_support
        """
        categories = {}
        for cat in self.tier1_detector.get_categories():
            has_tier2 = any(
                spec_cat in cat.lower()
                for spec_cat in self.SPECIALIZED_CATEGORIES.keys()
            )
            categories[cat] = has_tier2
        
        return categories
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Update confidence threshold for Tier 2 routing.
        
        Args:
            threshold: New threshold value (0-1)
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        self.confidence_threshold = threshold
        print(f"Confidence threshold updated to {threshold}")


def create_pipeline(
    confidence_threshold: float = 0.5,
    enable_tier2: bool = True
) -> MarketplaceDetectionPipeline:
    """
    Factory function to create a detection pipeline.
    
    Args:
        confidence_threshold: Minimum confidence for Tier 2
        enable_tier2: Whether to enable Tier 2 detection
        
    Returns:
        Configured pipeline
    """
    return MarketplaceDetectionPipeline(
        confidence_threshold=confidence_threshold,
        enable_tier2=enable_tier2
    )


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("MARKETPLACE DETECTION PIPELINE")
    print("=" * 60)
    
    pipeline = create_pipeline()
    
    print("\n" + "=" * 60)
    print("Supported Categories:")
    print("=" * 60)
    
    categories = pipeline.get_supported_categories()
    for cat, has_tier2 in sorted(categories.items()):
        tier2_status = "✓ Tier 2 available" if has_tier2 else "○ Tier 1 only"
        print(f"  {cat:30} {tier2_status}")
    
    print("\n" + "=" * 60)
    print("Pipeline ready for predictions!")
    print("=" * 60)
    
    # To test with actual images:
    # result = pipeline.predict("path/to/image.jpg")
    # print(json.dumps(result, indent=2))
