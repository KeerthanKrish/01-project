"""
FastAPI REST API for Marketplace Item Detection
================================================

Provides REST API endpoints for product analysis.
Alternative to the Flask web interface (app.py).

Endpoints:
- POST /api/analyze - Analyze uploaded images
- GET /api/health - Health check
- GET /api/analysis/{analysis_id} - Get saved analysis by ID
- GET /api/search/{analysis_id} - Get search payload by ID

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8001

Then access API at: http://localhost:8001
API docs at: http://localhost:8001/docs
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
from PIL import Image
import io
import json
from datetime import datetime

from detector import MarketplaceDetector

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

# Folders for saved results
JSONS_FOLDER = Path("jsons")
SEARCH_JSONS_FOLDER = Path("search_jsons")


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
            "get_analysis": "GET /api/analysis/{analysis_id}",
            "get_search": "GET /api/search/{analysis_id}",
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
            save_json=True
        )
        
        # Format response
        response = {
            "success": result['success'],
            "marketplace_suitable": result['marketplace_suitable'],
            "images_analyzed": result['images_analyzed'],
            "analysis_timestamp": datetime.now().isoformat(),
            
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
            
            # Marketplace listing data
            "listing": result.get('marketplace_listing'),
            
            # Search optimization payload
            "search": result.get('search_payload'),
            
            # Saved file paths
            "files": {
                "comprehensive_analysis": result.get('json_saved_path'),
                "search_payload": result.get('search_json_path')
            }
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
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Retrieve a saved comprehensive analysis by ID.
    
    Args:
        analysis_id: Timestamp ID of the analysis (e.g., "20260418_143000")
        
    Returns:
        Complete analysis JSON
        
    Example:
        curl "http://localhost:8001/api/analysis/20260418_143000"
    """
    try:
        json_path = JSONS_FOLDER / f"analysis_{analysis_id}.json"
        
        if not json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Analysis '{analysis_id}' not found"
            )
        
        with open(json_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        return JSONResponse(content=analysis_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading analysis: {str(e)}"
        )


@app.get("/api/search/{analysis_id}")
async def get_search_payload(analysis_id: str):
    """
    Retrieve a saved search optimization payload by ID.
    
    Args:
        analysis_id: Timestamp ID of the analysis (e.g., "20260418_143000")
        
    Returns:
        Search optimization payload JSON
        
    Example:
        curl "http://localhost:8001/api/search/20260418_143000"
    """
    try:
        json_path = SEARCH_JSONS_FOLDER / f"search_{analysis_id}.json"
        
        if not json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Search payload '{analysis_id}' not found"
            )
        
        with open(json_path, 'r', encoding='utf-8') as f:
            search_data = json.load(f)
        
        return JSONResponse(content=search_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading search payload: {str(e)}"
        )


@app.get("/api/analyses")
async def list_analyses(limit: int = 20):
    """
    List recent analyses.
    
    Args:
        limit: Maximum number of results to return (default: 20)
        
    Returns:
        List of analysis IDs with metadata
        
    Example:
        curl "http://localhost:8001/api/analyses?limit=10"
    """
    try:
        # Get all analysis files
        analysis_files = sorted(
            JSONS_FOLDER.glob("analysis_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        analyses = []
        for file_path in analysis_files:
            # Extract timestamp from filename
            analysis_id = file_path.stem.replace("analysis_", "")
            
            # Load basic metadata
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analyses.append({
                    "analysis_id": analysis_id,
                    "timestamp": data.get("analysis_metadata", {}).get("timestamp"),
                    "category": data.get("tier1_category_detection", {}).get("category"),
                    "marketplace_suitable": data.get("tier1_category_detection", {}).get("marketplace_suitable"),
                    "images_analyzed": data.get("analysis_metadata", {}).get("images_analyzed", 1)
                })
            except Exception as e:
                print(f"⚠️ Error loading {file_path.name}: {e}")
                continue
        
        return {
            "count": len(analyses),
            "limit": limit,
            "analyses": analyses
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing analyses: {str(e)}"
        )


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
    print("   GET  /api/analysis/{id} - Get analysis by ID")
    print("   GET  /api/search/{id} - Get search payload by ID")
    print("   GET  /api/analyses - List recent analyses")
    print("\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
