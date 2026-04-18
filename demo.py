"""
Demo script for marketplace detection system.

This script demonstrates how to use the detection pipeline
with example images.
"""

import sys
import os
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import create_pipeline
from PIL import Image, ImageDraw, ImageFont
import warnings

warnings.filterwarnings('ignore')


def create_sample_images():
    """
    Create sample synthetic images for demonstration.
    
    Returns:
        List of (image_path, expected_category) tuples
    """
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    samples = []
    
    # Create sample images with different colors representing categories
    categories = [
        ("electronics", (50, 50, 200)),      # Blue
        ("furniture", (139, 90, 43)),        # Brown
        ("clothing", (200, 50, 50)),         # Red
        ("books", (100, 200, 100)),          # Green
    ]
    
    for category, color in categories:
        img = Image.new('RGB', (400, 400), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add text label
        text = category.upper()
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((400 - text_width) // 2, (400 - text_height) // 2)
        draw.text(position, text, fill='white')
        
        # Save image
        img_path = data_dir / f"sample_{category}.jpg"
        img.save(img_path)
        samples.append((str(img_path), category))
        
        print(f"Created sample image: {img_path}")
    
    return samples


def demo_single_prediction(pipeline, image_path, expected_category=None):
    """
    Demonstrate single image prediction.
    
    Args:
        pipeline: Detection pipeline
        image_path: Path to image
        expected_category: Expected category (optional)
    """
    print("\n" + "="*70)
    print(f"Processing: {image_path}")
    print("="*70)
    
    result = pipeline.predict(image_path, return_metadata=True)
    
    # Display results
    print("\n📊 TIER 1 RESULTS:")
    print(f"  Category: {result['tier1']['category']}")
    print(f"  Confidence: {result['tier1']['confidence']:.2%}")
    
    if result['tier1'].get('alternatives'):
        print(f"  Alternatives:")
        for alt in result['tier1']['alternatives']:
            print(f"    - {alt['label']}: {alt['confidence']:.2%}")
    
    if result['tier2'] and 'product_type' in result['tier2']:
        print("\n🔍 TIER 2 RESULTS:")
        tier2 = result['tier2']
        if 'product_type' in tier2:
            print(f"  Product Type: {tier2['product_type']}")
        if 'brand' in tier2:
            print(f"  Brand: {tier2['brand']}")
        if 'condition' in tier2:
            print(f"  Condition: {tier2['condition']}")
        if 'color' in tier2:
            print(f"  Color: {tier2['color']}")
        if 'overall_confidence' in tier2:
            print(f"  Overall Confidence: {tier2['overall_confidence']:.2%}")
    
    if result.get('metadata'):
        print("\n⏱️  PERFORMANCE:")
        meta = result['metadata']
        if 'total_time_ms' in meta:
            print(f"  Total Time: {meta['total_time_ms']:.0f}ms")
        if 'overall_confidence' in meta:
            print(f"  Overall Confidence: {meta['overall_confidence']:.2%}")
    
    if expected_category:
        detected = result['tier1']['category']
        match = expected_category.lower() in detected.lower()
        status = "✓ CORRECT" if match else "✗ INCORRECT"
        print(f"\n{status} (expected: {expected_category})")
    
    return result


def demo_batch_prediction(pipeline, image_paths):
    """
    Demonstrate batch prediction.
    
    Args:
        pipeline: Detection pipeline
        image_paths: List of image paths
    """
    print("\n" + "="*70)
    print("BATCH PREDICTION DEMO")
    print("="*70)
    
    results = pipeline.predict_batch(image_paths, return_metadata=False)
    
    print("\n📋 BATCH RESULTS SUMMARY:")
    print("-"*70)
    
    for i, (img_path, result) in enumerate(zip(image_paths, results), 1):
        if 'error' in result:
            print(f"{i}. {Path(img_path).name}: ERROR - {result['error']}")
        else:
            category = result['tier1']['category']
            confidence = result['tier1']['confidence']
            print(f"{i}. {Path(img_path).name}: {category} ({confidence:.1%})")
    
    return results


def save_results_to_json(results, output_path):
    """Save results to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_path}")


def main():
    """Main demo function."""
    print("="*70)
    print("MARKETPLACE DETECTION SYSTEM - DEMO")
    print("="*70)
    
    # Check if running with sample images or custom images
    if len(sys.argv) > 1:
        # User provided image paths
        image_paths = sys.argv[1:]
        samples = [(path, None) for path in image_paths]
        print(f"\n📁 Using {len(samples)} provided image(s)")
    else:
        # Create sample images
        print("\n🎨 Creating sample synthetic images...")
        samples = create_sample_images()
        print(f"\n✓ Created {len(samples)} sample images")
    
    # Initialize pipeline
    print("\n🚀 Initializing detection pipeline...")
    try:
        pipeline = create_pipeline(
            confidence_threshold=0.3,  # Lower threshold for demo
            enable_tier2=True
        )
    except Exception as e:
        print(f"\n❌ Error initializing pipeline: {e}")
        print("\n💡 TIP: Make sure you have installed all requirements:")
        print("   pip install -r requirements.txt")
        return
    
    # Demo 1: Single predictions
    print("\n" + "="*70)
    print("DEMO 1: SINGLE IMAGE PREDICTIONS")
    print("="*70)
    
    all_results = []
    for img_path, expected in samples[:2]:  # Process first 2 images
        result = demo_single_prediction(pipeline, img_path, expected)
        all_results.append(result)
    
    # Demo 2: Batch prediction (if we have more images)
    if len(samples) > 2:
        batch_paths = [img_path for img_path, _ in samples]
        batch_results = demo_batch_prediction(pipeline, batch_paths)
    
    # Save results
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    save_results_to_json(all_results, output_dir / "demo_results.json")
    
    # Print summary
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\n📌 Next steps:")
    print("  1. Try with your own images: python demo.py path/to/image.jpg")
    print("  2. Explore the Jupyter notebooks in the notebooks/ folder")
    print("  3. Check the full pipeline in src/pipeline.py")
    print("  4. Add more Tier 2 detectors for other categories")
    
    print("\n✨ Thank you for trying the Marketplace Detection System!")


if __name__ == "__main__":
    main()
