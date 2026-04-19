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
        
        print(f"Files saved:")
        print(f"  - Analysis: {result['files']['comprehensive_analysis']}")
        print(f"  - Search: {result['files']['search_payload']}")
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


def get_saved_analysis(analysis_id: str):
    """Retrieve a saved analysis by ID."""
    print(f"\n4️⃣ Retrieving analysis: {analysis_id}")
    
    response = requests.get(f"{API_URL}/api/analysis/{analysis_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found!")
        print(f"Timestamp: {result['analysis_metadata']['timestamp']}")
        print(f"Category: {result['tier1_category_detection']['category']}")
    else:
        print(f"❌ Not found: {response.status_code}")


def list_recent_analyses():
    """List recent analyses."""
    print(f"\n5️⃣ Listing recent analyses...")
    
    response = requests.get(f"{API_URL}/api/analyses?limit=5")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['count']} analyses:")
        
        for analysis in result['analyses']:
            print(f"  - {analysis['analysis_id']}: {analysis['category']} ({analysis['images_analyzed']} images)")
    else:
        print(f"❌ Error: {response.status_code}")


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

4. Get Analysis by ID:
    curl http://localhost:8001/api/analysis/20260418_143000

5. Get Search Payload by ID:
    curl http://localhost:8001/api/search/20260418_143000

6. List Recent Analyses:
    curl http://localhost:8001/api/analyses?limit=10

7. View API Documentation:
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
    
    # Example: get saved analysis
    # get_saved_analysis("20260418_143000")
    
    # Example: list recent
    # list_recent_analyses()
    
    print("\n💡 To run Python examples, uncomment the function calls at the bottom of this file.")
