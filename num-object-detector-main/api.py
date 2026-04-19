from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import cv2
import base64
import os
import numpy as np
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Object Detection API", version="1.0.0")

class DetectionResult(BaseModel):
    image_name: str
    object_count: int
    has_exactly_one_object: bool
    error: str = None

def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

def count_objects_with_gpt_base64(base64_image: str, api_key: str):
    """
    Use GPT-4o-mini Vision to count objects in an image.
    
    Args:
        image_path: Path to the image file
        api_key: OpenAI API key
        
    Returns:
        int: Number of objects detected, or None if detection fails
    """
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
                            "text": "Count the number of primary product objects in the foreground. Ignore background items, hands, furniture, shelves, or clutter. Treat accessories or packaging that belong to the product as part of the main product. Return ONLY a single number and nothing else."
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

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Object Detection API",
        "version": "1.0.0",
        "endpoints": {
            "/detect": "POST - Upload an image to detect objects",
            "/health": "GET - Check API health status"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "status": "healthy",
        "openai_configured": api_key is not None
    }

@app.post("/detect", response_model=DetectionResult)
async def detect_objects(file: UploadFile = File(...)):
    """
    Detect objects in an uploaded image.
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        
    Returns:
        DetectionResult with object count and boolean for exactly one object
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable not set"
        )
    
    content_type = file.content_type or ""
    if not content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    try:
        contents = await file.read()
        
        img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        
        base64_image = encode_image_bytes_to_base64(contents)
        object_count = count_objects_with_gpt_base64(base64_image, api_key)
        
        if object_count is None:
            return DetectionResult(
                image_name=file.filename,
                object_count=0,
                has_exactly_one_object=False,
                error="Failed to detect objects"
            )
        
        return DetectionResult(
            image_name=file.filename,
            object_count=object_count,
            has_exactly_one_object=object_count == 1
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
