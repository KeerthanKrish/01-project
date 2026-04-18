"""
Image preprocessing pipeline for marketplace item detection.
Handles resizing, normalization, orientation correction, and quality checks.
"""

import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Tuple, Optional, Union
import warnings


class ImagePreprocessor:
    """
    Preprocesses images for marketplace item detection.
    
    Features:
    - Automatic EXIF orientation correction
    - Resizing with aspect ratio preservation
    - Normalization for model input
    - Quality assessment
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (384, 384),
        normalize: bool = True,
        min_dimension: int = 100,
        max_dimension: int = 4096,
        maintain_aspect_ratio: bool = False
    ):
        """
        Initialize the preprocessor.
        
        Args:
            target_size: Target size for resizing (height, width)
            normalize: Whether to normalize pixel values
            min_dimension: Minimum allowed dimension (filters low quality)
            max_dimension: Maximum allowed dimension (prevent memory issues)
            maintain_aspect_ratio: If True, pad to maintain aspect ratio
        """
        self.target_size = target_size
        self.normalize = normalize
        self.min_dimension = min_dimension
        self.max_dimension = max_dimension
        self.maintain_aspect_ratio = maintain_aspect_ratio
        
    def load_image(self, image_path: str) -> Image.Image:
        """
        Load image from file path with error handling.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object
        """
        try:
            img = Image.open(image_path)
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception as e:
            raise ValueError(f"Failed to load image from {image_path}: {str(e)}")
    
    def correct_orientation(self, img: Image.Image) -> Image.Image:
        """
        Correct image orientation based on EXIF data.
        
        Args:
            img: PIL Image
            
        Returns:
            Oriented image
        """
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            # If EXIF data is missing or corrupt, continue without rotation
            pass
        return img
    
    def validate_image(self, img: Image.Image) -> Tuple[bool, str]:
        """
        Check if image meets quality requirements.
        
        Args:
            img: PIL Image
            
        Returns:
            Tuple of (is_valid, message)
        """
        width, height = img.size
        
        # Check minimum dimensions
        if width < self.min_dimension or height < self.min_dimension:
            return False, f"Image too small: {width}x{height} (min: {self.min_dimension})"
        
        # Check maximum dimensions
        if width > self.max_dimension or height > self.max_dimension:
            return False, f"Image too large: {width}x{height} (max: {self.max_dimension})"
        
        # Check aspect ratio (flag extreme ratios)
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 4:
            warnings.warn(f"Extreme aspect ratio: {aspect_ratio:.2f}")
        
        return True, "Valid"
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to target size.
        
        Args:
            img: PIL Image
            
        Returns:
            Resized image
        """
        if self.maintain_aspect_ratio:
            # Resize maintaining aspect ratio and pad
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            
            # Create a white background
            new_img = Image.new('RGB', self.target_size, (255, 255, 255))
            
            # Calculate position to paste (center)
            paste_x = (self.target_size[0] - img.size[0]) // 2
            paste_y = (self.target_size[1] - img.size[1]) // 2
            
            new_img.paste(img, (paste_x, paste_y))
            return new_img
        else:
            # Direct resize (may distort aspect ratio)
            return img.resize(self.target_size, Image.Resampling.LANCZOS)
    
    def normalize_image(self, img_array: np.ndarray) -> np.ndarray:
        """
        Normalize image array for model input.
        
        Uses ImageNet mean and std for pretrained models.
        
        Args:
            img_array: Numpy array of shape (H, W, C) with values [0, 255]
            
        Returns:
            Normalized array with values roughly [-1, 1]
        """
        # Convert to float and scale to [0, 1]
        img_array = img_array.astype(np.float32) / 255.0
        
        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        
        img_array = (img_array - mean) / std
        
        return img_array
    
    def assess_quality(self, img: Image.Image) -> dict:
        """
        Assess image quality metrics.
        
        Args:
            img: PIL Image
            
        Returns:
            Dictionary with quality metrics
        """
        img_array = np.array(img)
        
        # Calculate blur using Laplacian variance
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Classify blur level
        if laplacian_var < 100:
            blur_level = "high"
        elif laplacian_var < 500:
            blur_level = "moderate"
        else:
            blur_level = "low"
        
        # Calculate brightness
        brightness = np.mean(img_array)
        
        # Classify brightness
        if brightness < 80:
            brightness_level = "dark"
        elif brightness > 180:
            brightness_level = "bright"
        else:
            brightness_level = "good"
        
        # Calculate contrast
        gray_std = np.std(gray)
        if gray_std < 30:
            contrast_level = "low"
        elif gray_std > 80:
            contrast_level = "high"
        else:
            contrast_level = "good"
        
        return {
            "blur_score": float(laplacian_var),
            "blur_level": blur_level,
            "brightness": float(brightness),
            "brightness_level": brightness_level,
            "contrast": float(gray_std),
            "contrast_level": contrast_level,
            "overall_quality": "good" if blur_level == "low" and brightness_level == "good" else "fair"
        }
    
    def preprocess(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        return_array: bool = True,
        assess_quality: bool = True
    ) -> Tuple[Union[np.ndarray, Image.Image], dict]:
        """
        Complete preprocessing pipeline.
        
        Args:
            image_input: Path to image, PIL Image, or numpy array
            return_array: If True, return numpy array; else return PIL Image
            assess_quality: If True, include quality assessment in metadata
            
        Returns:
            Tuple of (processed_image, metadata)
        """
        metadata = {}
        
        # Load image
        if isinstance(image_input, str):
            img = self.load_image(image_input)
            metadata['source'] = image_input
        elif isinstance(image_input, np.ndarray):
            img = Image.fromarray(image_input)
            metadata['source'] = 'array'
        else:
            img = image_input
            metadata['source'] = 'PIL Image'
        
        # Store original dimensions
        metadata['original_size'] = img.size
        
        # Correct orientation
        img = self.correct_orientation(img)
        
        # Validate image
        is_valid, message = self.validate_image(img)
        metadata['validation'] = {'valid': is_valid, 'message': message}
        
        if not is_valid:
            raise ValueError(f"Image validation failed: {message}")
        
        # Assess quality before resizing
        if assess_quality:
            metadata['quality'] = self.assess_quality(img)
        
        # Resize
        img = self.resize_image(img)
        metadata['processed_size'] = self.target_size
        
        # Convert to array if requested
        if return_array:
            img_array = np.array(img)
            
            # Normalize if requested
            if self.normalize:
                img_array = self.normalize_image(img_array)
                metadata['normalized'] = True
            else:
                metadata['normalized'] = False
            
            return img_array, metadata
        else:
            return img, metadata
    
    def preprocess_batch(
        self,
        image_inputs: list,
        return_array: bool = True,
        assess_quality: bool = False
    ) -> Tuple[list, list]:
        """
        Preprocess multiple images.
        
        Args:
            image_inputs: List of image paths, PIL Images, or numpy arrays
            return_array: If True, return numpy arrays
            assess_quality: If True, include quality assessment
            
        Returns:
            Tuple of (list of processed images, list of metadata dicts)
        """
        processed_images = []
        metadata_list = []
        
        for img_input in image_inputs:
            try:
                processed_img, metadata = self.preprocess(
                    img_input,
                    return_array=return_array,
                    assess_quality=assess_quality
                )
                processed_images.append(processed_img)
                metadata_list.append(metadata)
            except Exception as e:
                warnings.warn(f"Failed to preprocess image: {str(e)}")
                metadata_list.append({'error': str(e)})
        
        return processed_images, metadata_list


def create_preprocessor(
    model_type: str = "clip",
    target_size: Optional[Tuple[int, int]] = None
) -> ImagePreprocessor:
    """
    Factory function to create preprocessor for specific model type.
    
    Args:
        model_type: Type of model ('clip', 'resnet', 'efficientnet')
        target_size: Override default target size
        
    Returns:
        Configured ImagePreprocessor
    """
    # Default sizes for different models
    default_sizes = {
        'clip': (224, 224),
        'resnet': (224, 224),
        'efficientnet': (384, 384),
        'vit': (384, 384)
    }
    
    if target_size is None:
        target_size = default_sizes.get(model_type.lower(), (224, 224))
    
    return ImagePreprocessor(
        target_size=target_size,
        normalize=True,
        maintain_aspect_ratio=True
    )


if __name__ == "__main__":
    # Example usage
    preprocessor = create_preprocessor("clip")
    
    # Test with a sample image (you'll need to provide an actual image path)
    # img_array, metadata = preprocessor.preprocess("path/to/image.jpg")
    # print(f"Processed image shape: {img_array.shape}")
    # print(f"Metadata: {metadata}")
    
    print("Preprocessor module loaded successfully!")
    print(f"Default target size for CLIP: {preprocessor.target_size}")
