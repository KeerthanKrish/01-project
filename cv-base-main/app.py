"""
Flask Web Interface for Marketplace Item Detection
===================================================

Provides webcam interface for capturing and analyzing marketplace items.
Uses detector.py for all detection logic.

Run: python app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import os
import base64
from PIL import Image
import io
from datetime import datetime
from pathlib import Path
from detector import MarketplaceDetector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Create images folder
IMAGES_FOLDER = Path("images")
IMAGES_FOLDER.mkdir(exist_ok=True)

# Initialize detector
print("🚀 Initializing detector...")
detector = MarketplaceDetector(output_folder="jsons")
print("✅ Detector ready!")


@app.route('/')
def index():
    """Render the main webcam interface."""
    return render_template('webcam.html', use_openai=True)


@app.route('/detect', methods=['POST'])
def detect():
    """Process captured/uploaded images and return detection results."""
    try:
        # Get request data
        data = request.json
        images_data = data.get('images', [])
        rotation = data.get('rotation', 0)
        detail_level = data.get('detail_level', 'detailed')  # Always use detailed analysis
        
        if not images_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        print(f"📸 Processing {len(images_data)} image(s)...")
        
        # Process and save all images
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
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = IMAGES_FOLDER / f"capture_{timestamp}_{idx+1}of{len(images_data)}_r{rotation}.jpg"
            image.save(image_path, "JPEG", quality=85)
            
            processed_images.append(image)
            saved_paths.append(str(image_path))
            print(f"  💾 Saved: {image_path}")
        
        # Run detection using the detector module
        result = detector.analyze_images(
            images=processed_images,
            detail_level=detail_level,
            save_json=False
        )
        
        # Format response for web UI
        response = {
            'success': result['success'],
            'marketplace_suitable': result.get('marketplace_suitable', True),
            'suitability_reasoning': result.get('suitability_reasoning', ''),
            'saved_paths': saved_paths,
            'images_analyzed': result['images_analyzed'],
            'rotation_applied': rotation,
            'tier1': result['tier1'],
            'tier2': result['tier2'],
            'backend': 'OpenAI Vision',
            'detail_level': detail_level,
            'search_payload': result.get('search_payload')
        }
        
        # Add barcode info if found
        if result.get('barcode_lookup'):
            barcode = result['barcode_lookup']
            if barcode.get('found'):
                response['barcode_lookup'] = {
                    'found': True,
                    'barcode': barcode.get('barcode', ''),
                    'title': barcode.get('title', ''),
                    'brand': barcode.get('brand', '')
                }
        
        # Add message for unsuitable items
        if not result['marketplace_suitable']:
            response['message'] = 'Item not suitable for marketplace resale - Tier 2 analysis skipped'
        
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
        'backend': 'OpenAI Vision',
        'detectors_loaded': True
    })


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
        return image.transpose(Image.ROTATE_270)
    elif rotation == 180:
        return image.transpose(Image.ROTATE_180)
    elif rotation == 270:
        return image.transpose(Image.ROTATE_90)
    return image


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎥 MARKETPLACE DETECTION - WEB INTERFACE")
    print("="*70)
    print(f"\n📊 Backend: OpenAI Vision API")
    print(f"💾 Images saved to: {IMAGES_FOLDER.absolute()}")
    print("\n🌐 Opening web interface at: http://localhost:5000")
    print("\n✨ Features:")
    print("   - Live webcam capture OR drag-and-drop upload")
    print("   - Image rotation controls (0°, 90°, 180°, 270°)")
    print("   - Multi-angle analysis (up to 20+ images)")
    print("   - Detail levels (Quick/Normal/Detailed)")
    print("   - Flash/torch control (mobile devices)")
    print("   - Automatic barcode lookup")
    print("   - Product-specific wear detection")
    print("   - Comprehensive JSON output")
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
