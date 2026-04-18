"""
Demo script using OpenAI Vision API for much better accuracy.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, '.')

from src.openai_detector import create_openai_category_detector, create_openai_electronics_detector
from PIL import Image
import json


def main():
    print("="*70)
    print("MARKETPLACE DETECTION - OpenAI Vision API Demo")
    print("="*70)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ Error: OPENAI_API_KEY not set!")
        print("\nTo use OpenAI Vision API:")
        print("  1. Get an API key from: https://platform.openai.com/api-keys")
        print("  2. Set the environment variable:")
        print("     Windows: set OPENAI_API_KEY=your-key-here")
        print("     Linux/Mac: export OPENAI_API_KEY=your-key-here")
        print("  3. Or create a .env file with: OPENAI_API_KEY=your-key-here")
        return
    
    # Check if user provided image
    if len(sys.argv) < 2:
        print("\n📁 Usage: python demo_openai.py <image_path>")
        print("\nExample:")
        print("  python demo_openai.py path/to/your/phone.jpg")
        print("\nNote: This will use OpenAI API and incur costs (~$0.01-0.02 per image)")
        return
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"\n❌ Error: Image not found: {image_path}")
        return
    
    print(f"\n📸 Image: {image_path}")
    print("\n🚀 Initializing OpenAI detectors...")
    
    # Initialize detectors
    try:
        tier1_detector = create_openai_category_detector(model="gpt-4o")
        tier2_detector = create_openai_electronics_detector(model="gpt-4o")
    except Exception as e:
        print(f"\n❌ Error initializing detectors: {e}")
        return
    
    # Tier 1: Category Detection
    print("\n" + "="*70)
    print("TIER 1: Category Detection")
    print("="*70)
    
    try:
        tier1_result = tier1_detector.predict(
            image_path,
            top_k=3,
            return_reasoning=True
        )
        
        print(f"\n✅ Category: {tier1_result['category']}")
        print(f"✅ Confidence: {tier1_result['confidence']:.1%}")
        
        if tier1_result.get('reasoning'):
            print(f"\n💭 Reasoning: {tier1_result['reasoning']}")
        
        if tier1_result.get('alternatives'):
            print(f"\n📊 Alternatives:")
            for alt in tier1_result['alternatives']:
                print(f"   - {alt['category']}: {alt['confidence']:.1%}")
        
        print(f"\n⏱️  Processing time: {tier1_result['processing_time_ms']:.0f}ms")
        
    except Exception as e:
        print(f"\n❌ Tier 1 Error: {e}")
        return
    
    # Tier 2: Electronics Detection (if electronics category)
    if 'electronics' in tier1_result['category'].lower():
        print("\n" + "="*70)
        print("TIER 2: Electronics Attribute Detection")
        print("="*70)
        
        try:
            tier2_result = tier2_detector.predict(image_path, detect_all=True)
            
            print(f"\n📱 Product Type: {tier2_result.get('product_type', 'unknown')}")
            print(f"   Confidence: {tier2_result.get('product_type_confidence', 0):.1%}")
            
            print(f"\n🏷️  Brand: {tier2_result.get('brand', 'unknown')}")
            print(f"   Confidence: {tier2_result.get('brand_confidence', 0):.1%}")
            
            if tier2_result.get('model'):
                print(f"\n📋 Model: {tier2_result['model']}")
                print(f"   Confidence: {tier2_result.get('model_confidence', 0):.1%}")
            
            print(f"\n✨ Condition: {tier2_result.get('condition', 'unknown')}")
            print(f"   Confidence: {tier2_result.get('condition_confidence', 0):.1%}")
            
            print(f"\n🎨 Color: {tier2_result.get('color', 'unknown')}")
            print(f"   Confidence: {tier2_result.get('color_confidence', 0):.1%}")
            
            if tier2_result.get('features'):
                print(f"\n🔍 Features:")
                for feature in tier2_result['features']:
                    print(f"   - {feature}")
            
            if tier2_result.get('reasoning'):
                print(f"\n💭 Analysis: {tier2_result['reasoning']}")
            
            print(f"\n📊 Overall Confidence: {tier2_result.get('overall_confidence', 0):.1%}")
            print(f"⏱️  Processing time: {tier2_result['processing_time_ms']:.0f}ms")
            
            # Save results
            output_dir = Path("data/processed")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / "openai_result.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "tier1": tier1_result,
                    "tier2": tier2_result
                }, f, indent=2)
            
            print(f"\n💾 Results saved to: {output_file}")
            
        except Exception as e:
            print(f"\n❌ Tier 2 Error: {e}")
    
    else:
        print(f"\n⚠️  Not an electronics item, skipping Tier 2")
    
    print("\n" + "="*70)
    print("✅ DETECTION COMPLETE!")
    print("="*70)
    
    print("\n💡 Notes:")
    print("  - OpenAI Vision API is much more accurate than CLIP")
    print("  - Cost: ~$0.01-0.02 per image with gpt-4o")
    print("  - For bulk processing, consider gpt-4o-mini (cheaper, slightly less accurate)")


if __name__ == "__main__":
    main()
