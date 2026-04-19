# FastAPI REST API Guide

## Quick Start

### 1. Start the API Server

```bash
python api.py
```

Or with auto-reload for development:
```bash
uvicorn api:app --reload
```

Server will start at: **http://localhost:8000**

### 2. View Interactive Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST `/api/analyze`
**Analyze product images**

Upload one or more images and get comprehensive analysis.

**Request:**
```bash
curl -X POST http://localhost:8000/api/analyze \
     -F "images=@product1.jpg" \
     -F "images=@product2.jpg"
```

**Response:**
```json
{
  "success": true,
  "marketplace_suitable": true,
  "images_analyzed": 2,
  "category": {
    "name": "electronics",
    "confidence": 0.95
  },
  "product": {
    "brand": "Sony",
    "type": "WH-1000XM4 headphones",
    "condition": "Good",
    "cosmetic_grade": "B"
  },
  "listing": {
    "title": "Sony WH-1000XM4 (Good Condition)",
    "description": "...",
    "grade": "B"
  },
  "search": {
    "primary_query": "Sony WH-1000XM4 wireless headphones",
    "keywords": ["Sony", "WH-1000XM4", "wireless", "headphones"]
  },
  "files": {
    "comprehensive_analysis": "jsons/analysis_20260418_143000.json",
    "search_payload": "search_jsons/search_20260418_143000.json"
  }
}
```

---

### GET `/api/health`
**Health check**

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "detector": "initialized",
  "model": "gpt-4o",
  "timestamp": "2026-04-18T14:30:00"
}
```

---

### GET `/api/analysis/{analysis_id}`
**Retrieve saved analysis**

```bash
curl http://localhost:8000/api/analysis/20260418_143000
```

**Response:** Full comprehensive analysis JSON

---

### GET `/api/search/{analysis_id}`
**Retrieve search payload**

```bash
curl http://localhost:8000/api/search/20260418_143000
```

**Response:** Search optimization payload JSON

---

### GET `/api/analyses?limit=20`
**List recent analyses**

```bash
curl http://localhost:8000/api/analyses?limit=10
```

**Response:**
```json
{
  "count": 10,
  "limit": 10,
  "analyses": [
    {
      "analysis_id": "20260418_143000",
      "timestamp": "2026-04-18T14:30:00",
      "category": "electronics",
      "marketplace_suitable": true,
      "images_analyzed": 3
    }
  ]
}
```

## Python Client Example

```python
import requests

# Analyze images
files = [
    ('images', open('front.jpg', 'rb')),
    ('images', open('back.jpg', 'rb'))
]
response = requests.post('http://localhost:8000/api/analyze', files=files)
result = response.json()

print(f"Category: {result['category']['name']}")
print(f"Brand: {result['product']['brand']}")
print(f"Condition: {result['product']['condition']}")
```

## Features

- ✅ **RESTful API** - Standard HTTP endpoints
- ✅ **Multi-image upload** - Analyze multiple angles
- ✅ **Detailed analysis** - Always uses most thorough mode
- ✅ **JSON responses** - Easy to integrate
- ✅ **Auto-save** - Saves comprehensive + search JSONs
- ✅ **Interactive docs** - Built-in Swagger UI
- ✅ **CORS enabled** - Can be called from web browsers
- ✅ **Error handling** - Proper HTTP status codes

## Differences from Flask App

| Feature | Flask App (`app.py`) | FastAPI (`api.py`) |
|---------|---------------------|-------------------|
| **Purpose** | Web interface with webcam | REST API for integration |
| **UI** | Full HTML/CSS/JS interface | API only (JSON responses) |
| **Input** | Webcam + drag-drop | HTTP multipart file upload |
| **Output** | HTML results page | JSON response |
| **Documentation** | Manual | Auto-generated (Swagger/ReDoc) |
| **Use Case** | End users | Developers/integrations |

## When to Use Each

**Use Flask App (`app.py`)** when:
- You want a ready-to-use web interface
- Users need webcam capture
- You want immediate visual results

**Use FastAPI (`api.py`)** when:
- Integrating into other applications
- Building mobile apps that call your API
- Batch processing multiple products
- Creating automated workflows
- Need programmatic access to results

## Port Configuration

- Flask App: `http://localhost:5000`
- FastAPI: `http://localhost:8000`

Both can run simultaneously on different ports!
