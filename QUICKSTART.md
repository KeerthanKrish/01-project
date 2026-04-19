# Quick Start Guide

## Object Detection API with GPT-4o-mini

### Prerequisites
- Python 3.7+
- OpenAI API key

### Installation

1. Create and activate virtual environment:
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

### Running the CLI Version

```bash
python object_detector.py
```

Enter the path to your image when prompted. Results will be saved to `detection_result.json`.

### Running the API Version

1. Start the server:
```bash
python api.py
```

2. The API will be running at `http://localhost:8000`

3. View interactive documentation at `http://localhost:8000/docs`

### Testing the API

Using the test client:
```bash
python test_api.py test_image.jpg
```

Using curl:
```bash
curl -X POST "http://localhost:8000/detect" -F "file=@test_image.jpg"
```

### Response Format

```json
{
  "image_name": "test_image.jpg",
  "object_count": 1,
  "has_exactly_one_object": true,
  "error": null
}
```

- `has_exactly_one_object` is `true` if exactly 1 object is detected
- `has_exactly_one_object` is `false` if 0 or more than 1 objects are detected

### Project Files

- `object_detector.py` - CLI version
- `api.py` - FastAPI REST API
- `test_api.py` - API test client
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `README.md` - Full documentation

### Troubleshooting

**Issue:** `command not found: pip`
**Solution:** Use `pip3` instead of `pip`, or `python3 -m pip`

**Issue:** API key error
**Solution:** Make sure OPENAI_API_KEY is set: `export OPENAI_API_KEY='your-key'`

**Issue:** Cannot connect to API
**Solution:** Make sure the server is running: `python api.py`
