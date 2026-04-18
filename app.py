"""
Flask web app for live marketplace item detection via webcam.
Enhanced with rotation controls and detailed product analysis.
"""

from flask import Flask, render_template, request, jsonify
import os
import base64
from PIL import Image
import io
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Try to import OpenAI detector first, fall back to CLIP
try:
    from src.openai_detector import create_openai_category_detector
    from src.universal_detector import UniversalDetailedDetector
    USE_OPENAI = True
    print("✅ Using OpenAI Vision API (better accuracy)")
except:
    USE_OPENAI = False

if not USE_OPENAI or not os.getenv("OPENAI_API_KEY"):
    print("⚠️  OpenAI API key not found, using CLIP")
    USE_OPENAI = False
    from src.tier1_detector import create_category_detector
    from src.tier2_detectors.electronics import create_electronics_detector

app = Flask(__name__)

# Create images folder if it doesn't exist
IMAGES_FOLDER = Path("images")
IMAGES_FOLDER.mkdir(exist_ok=True)

# Initialize detectors
print("🚀 Initializing detectors...")
if USE_OPENAI:
    tier1_detector = create_openai_category_detector()
    universal_detector = UniversalDetailedDetector()  # For ALL categories
else:
    tier1_detector = create_category_detector()
    tier2_detector = create_electronics_detector()  # CLIP fallback (electronics only)

print("✅ Detectors ready!")


@app.route('/')
def index():
    """Render the main webcam interface."""
    return render_template('webcam.html', use_openai=USE_OPENAI)


def apply_rotation(image: Image.Image, rotation: int) -> Image.Image:
    """
    Apply rotation to image.
    
    Args:
        image: PIL Image
        rotation: Rotation angle (0, 90, 180, 270)
        
    Returns:
        Rotated PIL Image
    """
    if rotation == 90:
        return image.transpose(Image.ROTATE_270)  # PIL rotates counter-clockwise
    elif rotation == 180:
        return image.transpose(Image.ROTATE_180)
    elif rotation == 270:
        return image.transpose(Image.ROTATE_90)
    return image


@app.route('/detect', methods=['POST'])
def detect():
    """Process captured image(s) and return detection results."""
    try:
        # Get data from request
        data = request.json
        images_data = data.get('images', [])  # Now accepts multiple images
        rotation = data.get('rotation', 0)
        detail_level = data.get('detail_level', 'normal')
        
        if not images_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        print(f"📸 Processing {len(images_data)} image(s)...")
        
        # Process all images
        processed_images = []
        saved_paths = []
        
        for idx, image_data in enumerate(images_data):
            # Remove data URL prefix
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply rotation if needed
            if rotation != 0:
                image = apply_rotation(image, rotation)
            
            # Save image with timestamp and index
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = IMAGES_FOLDER / f"capture_{timestamp}_{idx+1}of{len(images_data)}_r{rotation}.jpg"
            
            # Save at high quality
            image.save(image_path, "JPEG", quality=95)
            
            processed_images.append(image)
            saved_paths.append(str(image_path))
            print(f"  💾 Saved: {image_path}")
        
        # Tier 1: Category Detection (use first image)
        print("🔍 Running Tier 1 detection...")
        if USE_OPENAI:
            tier1_result = tier1_detector.predict(processed_images[0], return_reasoning=True)
        else:
            tier1_result = tier1_detector.predict(processed_images[0], top_k=3)
        
        detected_category = tier1_result.get('category', 'unknown').lower()
        
        # Tier 2: Detailed analysis for ALL categories
        tier2_result = None
        print(f"🔍 Running Tier 2 detailed analysis for {detected_category} with {len(processed_images)} angle(s)...")
        
        if USE_OPENAI:
            # Use universal detector for ALL categories (not just electronics)
            if len(processed_images) > 1:
                tier2_result = universal_detector.predict_multi_angle(
                    processed_images,
                    category=detected_category,
                    detect_all=True,
                    detail_level=detail_level
                )
            else:
                tier2_result = universal_detector.predict(
                    processed_images[0],
                    category=detected_category,
                    detect_all=True,
                    detail_level=detail_level
                )
        else:
            # CLIP fallback: only supports electronics
            if 'electronics' in detected_category:
                tier2_result = tier2_detector.predict(processed_images[0], detect_all=True)
                if len(processed_images) > 1:
                    tier2_result['note'] = f"Analyzed 1 of {len(processed_images)} images (CLIP doesn't support multi-angle)"
            else:
                tier2_result = {
                    'note': 'Detailed analysis only available for electronics with CLIP. Use OpenAI for all categories.',
                    'category': detected_category
                }
        
        # Format response
        response = {
            'success': True,
            'saved_paths': saved_paths,
            'images_analyzed': len(processed_images),
            'rotation_applied': rotation,
            'tier1': tier1_result,
            'tier2': tier2_result,
            'backend': 'OpenAI Vision' if USE_OPENAI else 'CLIP',
            'detail_level': detail_level
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'backend': 'OpenAI Vision' if USE_OPENAI else 'CLIP',
        'detectors_loaded': True
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎥 MARKETPLACE DETECTION - WEBCAM INTERFACE (ENHANCED)")
    print("="*70)
    print(f"\n📊 Backend: {'OpenAI Vision API' if USE_OPENAI else 'CLIP (local)'}")
    print(f"💾 Images saved to: {IMAGES_FOLDER.absolute()}")
    print("\n🌐 Opening web interface at: http://localhost:5000")
    print("\n✨ NEW Features:")
    print("   - 💡 Camera flash/torch control (mobile devices)")
    print("   - 🌐 Universal category analysis (ALL product types)")
    print("   - 📸 Multi-angle capture for better accuracy")
    print("\n✨ Core Features:")
    print("   - Live webcam feed with gallery")
    print("   - Image rotation controls (0°, 90°, 180°, 270°)")
    print("   - Detail level selector (Quick/Normal/Detailed)")
    print("   - Comprehensive product analysis")
    print("   - Auto-save captured images")
    print("\n⏹️  Press Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    # Open browser automatically
    import webbrowser
    import threading
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:5000')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)
