# FastAPI Endpoint Details

## cv-base-main

Base: run `uvicorn api:app --reload --host 0.0.0.0 --port 8001`

### GET /
- Description: API info and endpoint map
- Params: none
- Body: none
- Response: JSON with name, version, status, endpoints

### GET /api/health
- Description: Health check and model status
- Params: none
- Body: none
- Response: JSON with status, detector, model, timestamp

### POST /api/analyze
- Description: Analyze one or more product images
- Content-Type: multipart/form-data
- Body:
  - images: one or more files (UploadFile), required
- Response: JSON with analysis summary, listing, and search payload

Example:
curl -X POST "http://localhost:8001/api/analyze" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg"

## num-object-detector-main

Base: run `uvicorn api:app --reload --host 0.0.0.0 --port 8000`

### GET /
- Description: API info and endpoint map
- Params: none
- Body: none
- Response: JSON with message, version, endpoints

### GET /health
- Description: Health check and OpenAI key presence
- Params: none
- Body: none
- Response: JSON with status, openai_configured

### POST /detect
- Description: Upload an image and count objects
- Content-Type: multipart/form-data
- Body:
  - file: image file (UploadFile), required
- Response: JSON (DetectionResult):
  - image_name: string
  - object_count: integer
  - has_exactly_one_object: boolean
  - error: string or null

Example:
curl -X POST "http://localhost:8000/detect" \
  -F "file=@image.jpg"
