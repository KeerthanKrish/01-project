import requests
import sys

def test_api(image_path, api_url="http://localhost:8000"):
    """
    Test the object detection API.
    
    Args:
        image_path: Path to the image file
        api_url: Base URL of the API (default: http://localhost:8000)
    """
    detect_url = f"{api_url}/detect"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(detect_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("Detection Result:")
            print(f"  Image: {result['image_name']}")
            print(f"  Object Count: {result['object_count']}")
            print(f"  Has Exactly One Object: {result['has_exactly_one_object']}")
            if result.get('error'):
                print(f"  Error: {result['error']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to API at {api_url}")
        print("Make sure the API server is running (python api.py)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        print("Example: python test_api.py test_image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_api(image_path)
