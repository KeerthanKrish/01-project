# Object Detector with GPT Vision

A Python application that uses OpenCV and OpenAI's GPT-4o-mini model to detect and count objects in images.

Available as both a CLI tool and a FastAPI REST API.

## Features

- Uses OpenCV to load images
- Leverages GPT-4o-mini (OpenAI's smallest and most efficient vision model) for object detection
- CLI version outputs results to a JSON file (`detection_result.json`)
- FastAPI version provides REST API endpoint for object detection
- Returns `true` if exactly 1 object is detected
- Returns `false` if 0 or more than 1 objects are detected

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

Alternatively, create a `.env` file (see `.env.example`) and load it using python-dotenv.

## Usage

### CLI Version

1. Activate the virtual environment (if not already activated):
```bash
source venv/bin/activate
```

2. Run the detector:
```bash
python object_detector.py
```

The script will prompt you to enter the path to an image file. You can provide:
- A relative path (e.g., `test_image.jpg`)
- An absolute path (e.g., `/Users/username/images/photo.jpg`)

### FastAPI Version

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

3. Start the FastAPI server:
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --reload
```

The API will be available at `http://localhost:8000`

4. Access the interactive API documentation at `http://localhost:8000/docs`

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check endpoint
- `POST /detect` - Upload an image and get object detection results

### Using the API

**Using the test client:**
```bash
python test_api.py test_image.jpg
```

**Using curl:**
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg"
```

**Using Python requests:**
```python
import requests

url = "http://localhost:8000/detect"
files = {"file": open("test_image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## Example Output

### CLI Version

Console output:
```
Enter the path to the image: test_image.jpg
Analyzing image: /Users/vishnu/Documents/projects/01-project-1/test_image.jpg
Detected 1 object(s) in the image
Result saved to detection_result.json
Has exactly one object: True
```

JSON file (`detection_result.json`):
```json
{
  "image_path": "/Users/vishnu/Documents/projects/01-project-1/test_image.jpg",
  "object_count": 1,
  "has_exactly_one_object": true
}
```

### API Version

Request:
```bash
curl -X POST "http://localhost:8000/detect" -F "file=@test_image.jpg"
```

Response (exactly 1 object):
```json
{
  "image_name": "test_image.jpg",
  "object_count": 1,
  "has_exactly_one_object": true,
  "error": null
}
```

Response (multiple objects):
```json
{
  "image_name": "multiple_objects.jpg",
  "object_count": 3,
  "has_exactly_one_object": false,
  "error": null
}
```

## Requirements

- Python 3.7+
- OpenCV
- FastAPI and Uvicorn (for API version)
- OpenAI API key with access to GPT-4o-mini
- Internet connection for API calls

## Output Format

### CLI Version
The script creates a `detection_result.json` file with the following structure:
```json
{
  "image_path": "path/to/image.jpg",
  "object_count": 1,
  "has_exactly_one_object": true
}
```

### API Version
The API endpoint returns a JSON response:
```json
{
  "image_name": "image.jpg",
  "object_count": 1,
  "has_exactly_one_object": true,
  "error": null
}
```

Fields:
- `image_path` / `image_name`: Path or name of the analyzed image
- `object_count`: Number of objects detected (integer)
- `has_exactly_one_object`: Boolean - `true` if exactly 1 object, `false` otherwise
- `error`: (optional) Error message if detection failed