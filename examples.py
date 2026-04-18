"""
Usage examples for the Marketplace Detection System.
Run this file to see various ways to use the system.
"""

import sys
sys.path.insert(0, '.')

from src.pipeline import create_pipeline
from src.tier1_detector import create_category_detector
from src.tier2_detectors.electronics import create_electronics_detector
from PIL import Image, ImageDraw, ImageFont
import json


def example_1_basic_usage():
    """Example 1: Basic single image detection"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage")
    print("="*70)
    
    # Create a test image
    img = Image.new('RGB', (400, 400), color=(70, 130, 180))
    draw = ImageDraw.Draw(img)
    draw.text((150, 180), "LAPTOP", fill='white')
    img.save("data/raw/example_laptop.jpg")
    
    # Initialize pipeline
    pipeline = create_pipeline()
    
    # Predict
    result = pipeline.predict("data/raw/example_laptop.jpg")
    
    # Display results
    print(f"\n✅ Category: {result['tier1']['category']}")
    print(f"✅ Confidence: {result['tier1']['confidence']:.2%}")
    
    if result['tier2']:
        print(f"✅ Tier 2 Results:")
        for key, value in result['tier2'].items():
            if not key.endswith('_alternatives') and key != 'processing_time_ms':
                print(f"   - {key}: {value}")


def example_2_tier1_only():
    """Example 2: Using Tier 1 detector standalone"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Tier 1 Only (Fast Category Detection)")
    print("="*70)
    
    # Create test images for different categories
    categories = [
        ("furniture", (139, 90, 43)),
        ("electronics", (50, 50, 200)),
        ("clothing", (200, 50, 50))
    ]
    
    detector = create_category_detector()
    
    for category, color in categories:
        # Create test image
        img = Image.new('RGB', (300, 300), color=color)
        img_path = f"data/raw/example_{category}.jpg"
        img.save(img_path)
        
        # Detect
        result = detector.predict(img_path, top_k=3)
        
        print(f"\n📁 {category.upper()}:")
        print(f"   Detected: {result['category']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Alternatives: {[alt['label'] for alt in result['alternatives']]}")


def example_3_electronics_deep_dive():
    """Example 3: Electronics detector deep dive"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Electronics Attribute Detection")
    print("="*70)
    
    # Create electronics test image
    img = Image.new('RGB', (400, 400), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 100, 350, 300], fill=(50, 50, 60), outline='white', width=3)
    draw.text((140, 180), "SMARTPHONE", fill='white')
    img.save("data/raw/example_phone.jpg")
    
    # Use electronics detector
    detector = create_electronics_detector()
    result = detector.predict("data/raw/example_phone.jpg", detect_all=True)
    
    print("\n📱 Electronics Detection Results:")
    print(f"   Product Type: {result['product_type']} ({result['product_type_confidence']:.2%})")
    print(f"   Brand: {result['brand']} ({result['brand_confidence']:.2%})")
    print(f"   Condition: {result['condition']} ({result['condition_confidence']:.2%})")
    print(f"   Color: {result['color']} ({result['color_confidence']:.2%})")
    print(f"   Overall Confidence: {result['overall_confidence']:.2%}")


def example_4_batch_processing():
    """Example 4: Batch processing multiple images"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Processing")
    print("="*70)
    
    # Create multiple test images
    image_paths = []
    categories = ["books", "toys", "sports", "furniture"]
    colors = [(100, 200, 100), (255, 200, 50), (200, 100, 50), (139, 90, 43)]
    
    for cat, color in zip(categories, colors):
        img = Image.new('RGB', (300, 300), color=color)
        path = f"data/raw/batch_{cat}.jpg"
        img.save(path)
        image_paths.append(path)
    
    # Process batch
    pipeline = create_pipeline()
    results = pipeline.predict_batch(image_paths, return_metadata=False)
    
    print(f"\n📦 Processed {len(results)} images:")
    for i, (path, result) in enumerate(zip(image_paths, results), 1):
        category = result['tier1']['category']
        confidence = result['tier1']['confidence']
        print(f"   {i}. {path.split('/')[-1]}: {category} ({confidence:.1%})")


def example_5_custom_configuration():
    """Example 5: Custom pipeline configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Configuration")
    print("="*70)
    
    # Create test image
    img = Image.new('RGB', (300, 300), color=(100, 100, 200))
    img.save("data/raw/example_config.jpg")
    
    # Configure pipeline with custom settings
    pipeline = create_pipeline(
        confidence_threshold=0.3,  # Lower threshold
        enable_tier2=True
    )
    
    print("\n⚙️  Pipeline Configuration:")
    print(f"   Confidence Threshold: {pipeline.confidence_threshold}")
    print(f"   Tier 2 Enabled: {pipeline.enable_tier2}")
    
    # Get supported categories
    categories = pipeline.get_supported_categories()
    tier2_count = sum(1 for has_tier2 in categories.values() if has_tier2)
    
    print(f"   Total Categories: {len(categories)}")
    print(f"   With Tier 2 Support: {tier2_count}")
    
    # Adjust threshold dynamically
    pipeline.set_confidence_threshold(0.7)
    print(f"\n✅ Updated threshold to: {pipeline.confidence_threshold}")


def example_6_error_handling():
    """Example 6: Error handling and edge cases"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70)
    
    pipeline = create_pipeline()
    
    # Test with non-existent image
    print("\n🔍 Testing with non-existent image:")
    try:
        result = pipeline.predict("nonexistent.jpg")
    except Exception as e:
        print(f"   ✅ Caught error: {type(e).__name__}")
    
    # Test with very small image
    print("\n🔍 Testing with very small image:")
    small_img = Image.new('RGB', (50, 50), color='blue')
    small_img.save("data/raw/tiny.jpg")
    try:
        result = pipeline.predict("data/raw/tiny.jpg")
        print(f"   ✅ Processed successfully (validation passed)")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def example_7_json_output():
    """Example 7: Working with JSON output"""
    print("\n" + "="*70)
    print("EXAMPLE 7: JSON Output and Serialization")
    print("="*70)
    
    # Create test image
    img = Image.new('RGB', (300, 300), color=(200, 100, 50))
    img.save("data/raw/example_json.jpg")
    
    # Get prediction
    pipeline = create_pipeline()
    result = pipeline.predict("data/raw/example_json.jpg", return_metadata=True)
    
    # Save to JSON
    output_file = "data/processed/example_output.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Load and display
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    print(f"\n📄 JSON Structure:")
    print(f"   - tier1: {list(loaded['tier1'].keys())}")
    print(f"   - tier2: {list(loaded['tier2'].keys()) if loaded['tier2'] else 'empty'}")
    print(f"   - metadata: {list(loaded['metadata'].keys())}")


def example_8_adding_categories():
    """Example 8: Adding custom categories"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Adding Custom Categories")
    print("="*70)
    
    detector = create_category_detector()
    
    print(f"\n📊 Original categories: {len(detector.get_categories())}")
    
    # Add custom categories
    custom_categories = [
        "vintage collectibles",
        "handmade crafts",
        "3D printed items"
    ]
    
    for category in custom_categories:
        detector.add_category(category)
    
    print(f"✅ Added {len(custom_categories)} custom categories")
    print(f"📊 Total categories now: {len(detector.get_categories())}")
    
    # Test with new categories
    img = Image.new('RGB', (300, 300), color=(180, 150, 120))
    img.save("data/raw/example_custom.jpg")
    
    result = detector.predict("data/raw/example_custom.jpg", top_k=5)
    print(f"\n🔍 Top 5 predictions:")
    print(f"   1. {result['category']} ({result['confidence']:.2%})")
    for i, alt in enumerate(result['alternatives'], 2):
        print(f"   {i}. {alt['label']} ({alt['confidence']:.2%})")


def main():
    """Run all examples"""
    print("="*70)
    print("MARKETPLACE DETECTION SYSTEM - USAGE EXAMPLES")
    print("="*70)
    print("\nRunning 8 examples to demonstrate various features...\n")
    
    try:
        example_1_basic_usage()
        example_2_tier1_only()
        example_3_electronics_deep_dive()
        example_4_batch_processing()
        example_5_custom_configuration()
        example_6_error_handling()
        example_7_json_output()
        example_8_adding_categories()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n📚 Next steps:")
        print("   1. Try these examples with your own images")
        print("   2. Explore the notebooks/ directory for interactive tutorials")
        print("   3. Read QUICKSTART.md for more detailed usage")
        print("   4. Check out demo.py for a complete demonstration")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\n💡 Make sure you have installed all requirements:")
        print("   pip install -r requirements.txt")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
