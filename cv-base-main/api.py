"""
FastAPI REST API for Marketplace Item Detection
================================================

Provides REST API endpoints for product analysis.
Alternative to the Flask web interface (app.py).

Endpoints:
- POST /api/analyze - Analyze uploaded images
- GET /api/health - Health check

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8001

Then access API at: http://localhost:8001
API docs at: http://localhost:8001/docs
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from PIL import Image
import io
from datetime import datetime
from dotenv import load_dotenv
import os
import requests

from detector import MarketplaceDetector

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Marketplace Item Detection API",
    description="AI-powered product analysis for marketplace listings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (allows requests from web browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
print("Initializing detector...")
detector = MarketplaceDetector()
print("Detector ready!")

CONVEX_HTTP_URL = os.getenv("CONVEX_HTTP_URL")


def _save_analysis_to_convex(response_payload: dict) -> None:
    if not CONVEX_HTTP_URL:
        return

    try:
        tier2 = response_payload.get("tier2") or {}
        payload = {
            "analysisJson": response_payload,
            "category": response_payload.get("category", {}).get("name", ""),
            "brand": tier2.get("brand", ""),
            "productType": tier2.get("product_type", ""),
            "marketplaceSuitable": bool(response_payload.get("marketplace_suitable")),
            "createdAt": int(datetime.now().timestamp() * 1000),
        }

        res = requests.post(
            f"{CONVEX_HTTP_URL.rstrip('/')}/api/save-analysis",
            json=payload,
            timeout=10,
        )
        if not res.ok:
            print(f"⚠️ Convex analysis save failed: {res.status_code} {res.text}")
        else:
            print(f"✅ Convex analysis saved: {res.json().get('id', 'ok')}")
    except Exception as exc:
        print(f"⚠️ Convex save failed: {exc}")


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Marketplace Item Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "health": "GET /api/health",
            "docs": "GET /docs"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "detector": "initialized",
        "model": "gpt-4o",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/analyze")
async def analyze_images(
    images: List[UploadFile] = File(..., description="One or more product images")
):
    """
    Analyze product images and return comprehensive results.
    
    Args:
        images: List of uploaded image files (JPEG, PNG, etc.)
        
    Returns:
        JSON with complete analysis including:
        - marketplace_suitable: Is item appropriate for resale
        - tier1: Category detection
        - tier2: Detailed analysis (brand, condition, wear)
        - barcode_lookup: Product data from barcode (if found)
        - marketplace_listing: Ready-to-use listing data
        - search_payload: Optimized search query
        - file_paths: Paths to saved JSON files
        
    Example:
        curl -X POST "http://localhost:8001/api/analyze" \\
             -F "images=@product1.jpg" \\
             -F "images=@product2.jpg"
    """
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No images provided")
        
        print(f"📸 Received {len(images)} image(s) for analysis")
        
        # Load images from uploads
        pil_images = []
        for idx, upload_file in enumerate(images):
            # Read image bytes
            contents = await upload_file.read()
            
            # Validate it's an image
            try:
                image = Image.open(io.BytesIO(contents))
                pil_images.append(image)
                print(f"  ✅ Image {idx+1}: {upload_file.filename} ({image.size[0]}x{image.size[1]})")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image file '{upload_file.filename}': {str(e)}"
                )
        
        # Run detection (always uses detailed mode)
        print(f"🔍 Running detailed analysis on {len(pil_images)} image(s)...")
        result = detector.analyze_images(
            images=pil_images,
            detail_level="detailed",
            save_json=False
        )
        
        # Format response
        response = {
            "success": result['success'],
            "marketplace_suitable": result['marketplace_suitable'],
            "images_analyzed": result['images_analyzed'],
            "analysis_timestamp": datetime.now().isoformat(),
            "detail_level": "detailed",
            "suitability_reasoning": result.get('suitability_reasoning', ''),
            "tier1": result.get('tier1'),
            "tier2": result.get('tier2'),
            
            # Category detection (Tier 1)
            "category": {
                "name": result['tier1']['category'],
                "confidence": result['tier1']['confidence'],
                "alternatives": result['tier1'].get('alternatives', [])
            },
            
            # Detailed analysis (Tier 2)
            "product": None,
            
            # Barcode lookup
            "barcode": None,
            "barcode_lookup": result.get('barcode_lookup'),
            
            # Marketplace listing data
            "listing": result.get('marketplace_listing'),
            
            # Search optimization payload
            "search": result.get('search_payload')
        }
        
        # Add product details if suitable
        if result['marketplace_suitable'] and result['tier2']:
            response['product'] = {
                "brand": result['tier2'].get('brand', 'Unknown'),
                "type": result['tier2'].get('product_type', 'Unknown'),
                "material": result['tier2'].get('material', ''),
                "color": result['tier2'].get('color', ''),
                "condition": result['tier2'].get('condition', 'Unknown'),
                "cosmetic_grade": result['tier2'].get('marketplace_assessment', {}).get('cosmetic_grade', ''),
                "functionality": result['tier2'].get('functionality_assessment', {}).get('appears_functional', None),
                "overall_confidence": result['tier2'].get('overall_confidence', 0.0)
            }
        else:
            response['unsuitable_reason'] = result.get('suitability_reasoning', '')
        
        # Add barcode info if found
        if result.get('barcode_lookup'):
            response['barcode'] = {
                "found": result['barcode_lookup'].get('found', False),
                "number": result['barcode_lookup'].get('barcode', ''),
                "source": result['barcode_lookup'].get('source', ''),
                "title": result['barcode_lookup'].get('title', ''),
                "brand": result['barcode_lookup'].get('brand', '')
            }
        
        print(f"✅ Analysis complete: {response['category']['name']}")
        _save_analysis_to_convex(response)
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("MARKETPLACE DETECTION API")
    print("="*70)
    print("\nStarting FastAPI server...")
    print("   API: http://localhost:8001")
    print("   Docs: http://localhost:8001/docs")
    print("   ReDoc: http://localhost:8001/redoc")
    print("\nEndpoints:")
    print("   POST /api/analyze - Analyze images")
    print("   GET  /api/health - Health check")
    print("   GET  /api/health - Health check")
    print("\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
