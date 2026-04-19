import cv2
import base64
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def encode_image_to_base64(image_path):
    """Read and encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def count_objects_with_gpt(image_path, api_key):
    """
    Use GPT-4o-mini Vision to count objects in an image.
    
    Args:
        image_path: Path to the image file
        api_key: OpenAI API key
        
    Returns:
        int: Number of objects detected, or None if detection fails
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Unable to read image from {image_path}")
        return None
    
    base64_image = encode_image_to_base64(image_path)
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Count the number of distinct objects in this image. Return ONLY a single number representing the count. Do not include any explanation or additional text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        
        count_str = response.choices[0].message.content.strip()
        count = int(count_str)
        return count
        
    except Exception as e:
        print(f"Error calling GPT API: {e}")
        return None

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    image_path = input("Enter the path to the image: ").strip()
    
    if not image_path:
        print("Error: No image path provided")
        return
    
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.getcwd(), image_path)
    
    print(f"Analyzing image: {image_path}")
    
    object_count = count_objects_with_gpt(image_path, api_key)
    
    if object_count is None:
        print("Failed to detect objects")
        result = {
            "image_path": image_path,
            "object_count": None,
            "has_exactly_one_object": False,
            "error": "Failed to detect objects"
        }
    else:
        print(f"Detected {object_count} object(s) in the image")
        result = {
            "image_path": image_path,
            "object_count": object_count,
            "has_exactly_one_object": object_count == 1
        }
    
    output_file = "detection_result.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Result saved to {output_file}")
    print(f"Has exactly one object: {result['has_exactly_one_object']}")

if __name__ == "__main__":
    main()
