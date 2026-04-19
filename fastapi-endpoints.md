# FastAPI Endpoints

## cv-base-main

- GET / - API info and endpoint map
- GET /api/health - Health check and model status
- POST /api/analyze - Analyze one or more product images
- GET /api/analysis/{analysis_id} - Fetch saved analysis by ID
- GET /api/search/{analysis_id} - Fetch saved search payload by ID
- GET /api/analyses - List recent analyses (default limit 20)

## num-object-detector-main

- GET / - API info and endpoint map
- GET /health - Health check and OpenAI key presence
- POST /detect - Upload an image and count objects
