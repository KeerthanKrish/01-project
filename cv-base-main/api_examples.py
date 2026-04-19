"""
Example: How to Use the FastAPI Detection API
==============================================

This script demonstrates how to interact with the API endpoints.
"""

import requests
from pathlib import Path

# API base URL
API_URL = "http://localhost:8001"


def test_health():
    """Test the health check endpoint."""
    print("\n1️⃣ Testing health endpoint...")
    response = requests.get(f"{API_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def analyze_single_image(image_path: str):
    """Analyze a single product image."""
    print(f"\n2️⃣ Analyzing single image: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {'images': f}
        response = requests.post(f"{API_URL}/api/analyze", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Category: {result['category']['name']}")
        print(f"Marketplace Suitable: {result['marketplace_suitable']}")
        
        if result['product']:
            print(f"Brand: {result['product']['brand']}")
            print(f"Type: {result['product']['type']}")
            print(f"Condition: {result['product']['condition']}")
        
        if result.get('search'):
            print(f"Search query: {result['search'].get('primary_query', '')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())


def analyze_multiple_images(image_paths: list):
    """Analyze multiple product images (multi-angle)."""
    print(f"\n3️⃣ Analyzing {len(image_paths)} images...")
    
    files = [('images', open(path, 'rb')) for path in image_paths]
    response = requests.post(f"{API_URL}/api/analyze", files=files)
    
    # Close all files
    for _, f in files:
        f.close()
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Images analyzed: {result['images_analyzed']}")
        print(f"Category: {result['category']['name']} ({result['category']['confidence']:.2%})")
        
        if result.get('listing'):
            print(f"\nListing suggestion:")
            print(f"  Title: {result['listing']['title']}")
            print(f"  Grade: {result['listing']['grade']}")
        
        if result.get('search'):
            print(f"\nSearch query:")
            print(f"  Primary: {result['search']['primary_query']}")
            print(f"  Keywords: {', '.join(result['search']['keywords'][:5])}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())


# Example using curl (command-line):
CURL_EXAMPLES = """
================================================================================
📡 CURL EXAMPLES (Command-Line Usage)
================================================================================

1. Health Check:
    curl http://localhost:8001/api/health

2. Analyze Single Image:
    curl -X POST http://localhost:8001/api/analyze \\
        -F "images=@product.jpg"

3. Analyze Multiple Images:
    curl -X POST http://localhost:8001/api/analyze \\
        -F "images=@front.jpg" \\
        -F "images=@back.jpg" \\
        -F "images=@damage.jpg"

4. View API Documentation:
    Open in browser: http://localhost:8001/docs
   
================================================================================
"""


if __name__ == "__main__":
    print("="*80)
    print("🚀 FastAPI Detection API - Usage Examples")
    print("="*80)
    print("\n⚠️  Make sure the API server is running:")
    print("   python api.py")
    print("   OR: uvicorn api:app --reload")
    
    # Show curl examples
    print(CURL_EXAMPLES)
    
    # Python examples (uncomment to run)
    # test_health()
    
    # Example: analyze a single image
    # analyze_single_image("path/to/product.jpg")
    
    # Example: analyze multiple images
    # analyze_multiple_images(["front.jpg", "back.jpg", "damage.jpg"])
    
    print("\n💡 To run Python examples, uncomment the function calls at the bottom of this file.")
