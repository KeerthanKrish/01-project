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
import json
import requests

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

# Create jsons folder for comprehensive analysis outputs
JSONS_FOLDER = Path("jsons")
JSONS_FOLDER.mkdir(exist_ok=True)

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


def save_comprehensive_json(tier1_result, tier2_result, metadata, barcode_info=None):
    """
    Save comprehensive JSON file with ALL analysis details.
    
    Args:
        tier1_result: Tier 1 detection results
        tier2_result: Tier 2 detailed analysis results
        metadata: Additional metadata (images, settings, etc.)
        barcode_info: Barcode lookup results (if available)
        
    Returns:
        Path to saved JSON file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = JSONS_FOLDER / f"analysis_{timestamp}.json"
    
    # Build comprehensive output
    comprehensive_output = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": timestamp,
            "backend": metadata.get('backend', 'Unknown'),
            "detail_level": metadata.get('detail_level', 'normal'),
            "rotation_applied": metadata.get('rotation', 0),
            "images_analyzed": metadata.get('images_analyzed', 1),
            "saved_image_paths": metadata.get('saved_paths', [])
        },
        
        "tier1_category_detection": {
            "category": tier1_result.get('category', 'unknown'),
            "confidence": tier1_result.get('confidence', 0.0),
            "reasoning": tier1_result.get('reasoning', ''),
            "all_predictions": tier1_result.get('predictions', []),
            "processing_time_ms": tier1_result.get('processing_time_ms', 0)
        },
        
        "tier2_detailed_analysis": tier2_result if tier2_result else {},
        
        "barcode_lookup": barcode_info if barcode_info else {
            "found": False,
            "message": "No barcode/SKU detected in images"
        },
        
        "comprehensive_description": generate_comprehensive_description(tier1_result, tier2_result),
        
        "marketplace_listing_ready": {
            "title_suggestion": generate_title_suggestion(tier2_result),
            "condition_summary": generate_condition_summary(tier2_result),
            "key_selling_points": extract_selling_points(tier2_result),
            "buyer_concerns": extract_buyer_concerns(tier2_result),
            "estimated_grade": tier2_result.get('marketplace_assessment', {}).get('cosmetic_grade', 'Unknown') if tier2_result else 'Unknown'
        },
        
        "raw_data": {
            "tier1_complete": tier1_result,
            "tier2_complete": tier2_result
        }
    }
    
    # Save to file
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_output, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Comprehensive JSON saved: {json_filename}")
    return str(json_filename)


def generate_comprehensive_description(tier1_result, tier2_result):
    """Generate a comprehensive text description of the product."""
    if not tier2_result:
        return f"Category identified as {tier1_result.get('category', 'unknown')}. Detailed analysis not available."
    
    parts = []
    
    # Product identification
    brand = tier2_result.get('brand', 'Unknown brand')
    product_type = tier2_result.get('product_type', tier1_result.get('category', 'item'))
    parts.append(f"This is a {brand} {product_type}.")
    
    # Material and specifications
    material = tier2_result.get('material', '')
    color = tier2_result.get('color', '')
    size = tier2_result.get('size_or_dimensions', '')
    
    specs = []
    if material: specs.append(f"made of {material}")
    if color: specs.append(f"in {color}")
    if size: specs.append(f"sized {size}")
    
    if specs:
        parts.append(f"It is {', '.join(specs)}.")
    
    # Condition overview
    condition = tier2_result.get('condition', 'Unknown')
    overall_assessment = tier2_result.get('overall_wear_assessment', '')
    if overall_assessment:
        parts.append(f"Overall condition is {condition}. {overall_assessment}")
    else:
        parts.append(f"Overall condition is {condition}.")
    
    # Product-specific wear
    pswa = tier2_result.get('product_specific_wear_analysis', {})
    if pswa and isinstance(pswa, dict) and pswa.get('summary'):
        parts.append(pswa['summary'])
    
    # Functionality
    func = tier2_result.get('functionality_assessment', {})
    if func and isinstance(func, dict):
        if func.get('appears_functional'):
            parts.append("The item appears to be fully functional.")
            if func.get('reasoning'):
                parts.append(func['reasoning'])
        else:
            parts.append("There are functionality concerns with this item.")
            if func.get('concerns'):
                concerns = func['concerns']
                if isinstance(concerns, list):
                    parts.append(f"Concerns: {', '.join(concerns)}")
                else:
                    parts.append(f"Concerns: {concerns}")
    
    # Completeness
    ma = tier2_result.get('marketplace_assessment', {})
    if ma and isinstance(ma, dict):
        completeness = ma.get('completeness', '')
        if completeness:
            parts.append(f"Item is {completeness}.")
    
    return ' '.join(parts)


def generate_title_suggestion(tier2_result):
    """Generate a marketplace listing title."""
    if not tier2_result:
        return "Item for Sale"
    
    brand = tier2_result.get('brand', '')
    product_type = tier2_result.get('product_type', 'item')
    condition = tier2_result.get('condition', '')
    
    # Build title
    title_parts = []
    if brand and brand != 'No visible branding':
        title_parts.append(brand)
    title_parts.append(product_type.title())
    if condition:
        title_parts.append(f"({condition} Condition)")
    
    return ' '.join(title_parts)


def generate_condition_summary(tier2_result):
    """Generate a concise condition summary for listings."""
    if not tier2_result:
        return "Condition details not available"
    
    condition = tier2_result.get('condition', 'Unknown')
    ma = tier2_result.get('marketplace_assessment', {})
    grade = ma.get('cosmetic_grade', '') if isinstance(ma, dict) else ''
    
    summary_parts = [f"{condition} condition"]
    if grade:
        summary_parts.append(f"(Grade {grade})")
    
    # Add key issues if any
    gpd = tier2_result.get('general_physical_damage', {})
    issues = []
    
    # Handle both dict and list formats for general_physical_damage
    if isinstance(gpd, dict):
        for damage_type in ['scratches', 'dents', 'scuffs', 'discoloration', 'cracks_or_chips']:
            damage_value = gpd.get(damage_type)
            if damage_value and isinstance(damage_value, list) and len(damage_value) > 0:
                issues.append(damage_type)
    elif isinstance(gpd, list):
        # If it's a list, just note that damage exists
        if len(gpd) > 0:
            issues.append("wear")
    
    if issues:
        summary_parts.append(f"with some {', '.join(issues[:2])}")
    else:
        summary_parts.append("with minimal wear")
    
    return ' '.join(summary_parts) + '.'


def extract_selling_points(tier2_result):
    """Extract key selling points from analysis."""
    if not tier2_result:
        return []
    
    points = []
    
    # From marketplace assessment
    ma = tier2_result.get('marketplace_assessment', {})
    if isinstance(ma, dict) and ma.get('selling_points'):
        selling_points = ma['selling_points']
        if isinstance(selling_points, list):
            points.extend(selling_points)
    
    # Add functionality if confirmed
    func = tier2_result.get('functionality_assessment', {})
    if isinstance(func, dict) and func.get('appears_functional') and func.get('confidence', 0) > 0.7:
        points.append("Fully functional")
    
    # Add brand if present
    brand = tier2_result.get('brand', '')
    if brand and brand != 'No visible branding':
        points.append(f"Genuine {brand} brand")
    
    # Add completeness
    if isinstance(ma, dict) and ma.get('completeness') == 'complete':
        points.append("Complete with all parts")
    
    return points


def extract_buyer_concerns(tier2_result):
    """Extract concerns buyers should be aware of."""
    if not tier2_result:
        return []
    
    concerns = []
    
    # From marketplace assessment
    ma = tier2_result.get('marketplace_assessment', {})
    if isinstance(ma, dict) and ma.get('major_concerns'):
        major_concerns = ma['major_concerns']
        if isinstance(major_concerns, list):
            concerns.extend(major_concerns)
    
    # From functionality
    func = tier2_result.get('functionality_assessment', {})
    if isinstance(func, dict) and func.get('concerns'):
        func_concerns = func['concerns']
        if isinstance(func_concerns, list):
            concerns.extend(func_concerns)
    
    # From product-specific wear
    pswa = tier2_result.get('product_specific_wear_analysis', {})
    if isinstance(pswa, dict) and pswa.get('inspection_results'):
        inspection_results = pswa['inspection_results']
        if isinstance(inspection_results, list):
            for result in inspection_results:
                if isinstance(result, dict):
                    if result.get('affects_function') or result.get('severity') in ['severe', 'moderate']:
                        concern_text = f"{result.get('wear_point', 'Component')}: {result.get('details', 'wear detected')}"
                        concerns.append(concern_text)
    
    return concerns


def lookup_barcode(barcode_number):
    """
    Look up product information using barcode/UPC/EAN number.
    
    Args:
        barcode_number: The barcode/UPC/EAN number as string
        
    Returns:
        Dictionary with product information or None if not found
    """
    if not barcode_number or len(barcode_number) < 8:
        return None
    
    # Clean the barcode number
    barcode_clean = ''.join(c for c in barcode_number if c.isdigit())
    
    if not barcode_clean:
        return None
    
    print(f"🔍 Looking up barcode: {barcode_clean}")
    
    # Try multiple free barcode APIs
    
    # 1. Try UPCitemdb.com (free, no API key needed for basic lookups)
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode_clean}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items') and len(data['items']) > 0:
                item = data['items'][0]
                result = {
                    'source': 'UPCitemdb',
                    'barcode': barcode_clean,
                    'title': item.get('title', ''),
                    'brand': item.get('brand', ''),
                    'model': item.get('model', ''),
                    'description': item.get('description', ''),
                    'category': item.get('category', ''),
                    'manufacturer': item.get('manufacturer', ''),
                    'size': item.get('size', ''),
                    'color': item.get('color', ''),
                    'images': item.get('images', []),
                    'ean': item.get('ean', ''),
                    'asin': item.get('asin', ''),
                    'raw_data': item
                }
                print(f"✅ Barcode lookup successful: {result.get('title', 'Unknown')}")
                return result
    except Exception as e:
        print(f"⚠️ UPCitemdb lookup failed: {str(e)}")
    
    # 2. Try Open Food Facts (for food/beverage items)
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_clean}.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                result = {
                    'source': 'Open Food Facts',
                    'barcode': barcode_clean,
                    'title': product.get('product_name', ''),
                    'brand': product.get('brands', ''),
                    'description': product.get('generic_name', ''),
                    'category': product.get('categories', ''),
                    'manufacturer': product.get('manufacturing_places', ''),
                    'size': product.get('quantity', ''),
                    'images': [product.get('image_url', '')],
                    'ingredients': product.get('ingredients_text', ''),
                    'nutrition_grade': product.get('nutrition_grade_fr', ''),
                    'raw_data': product
                }
                print(f"✅ Barcode lookup successful (Food): {result.get('title', 'Unknown')}")
                return result
    except Exception as e:
        print(f"⚠️ Open Food Facts lookup failed: {str(e)}")
    
    print(f"❌ No barcode information found for: {barcode_clean}")
    return None


def extract_barcodes_from_tier2(tier2_result):
    """
    Extract potential barcode numbers from Tier 2 analysis results.
    
    Args:
        tier2_result: Tier 2 detection results
        
    Returns:
        List of potential barcode numbers
    """
    if not tier2_result:
        return []
    
    barcodes = []
    
    # Check visible_text_found for barcode patterns
    visible_text = tier2_result.get('visible_text_found', [])
    for text in visible_text:
        # Look for numeric sequences that could be barcodes
        # UPC: 12 digits, EAN: 13 digits, but can vary
        digits = ''.join(c for c in str(text) if c.isdigit())
        if 8 <= len(digits) <= 14:  # Common barcode lengths
            barcodes.append(digits)
    
    # Also check regular visible_text field
    visible_text_alt = tier2_result.get('visible_text', [])
    for text in visible_text_alt:
        digits = ''.join(c for c in str(text) if c.isdigit())
        if 8 <= len(digits) <= 14:
            barcodes.append(digits)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_barcodes = []
    for bc in barcodes:
        if bc not in seen:
            seen.add(bc)
            unique_barcodes.append(bc)
    
    return unique_barcodes


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
        
        # Check if item is suitable for marketplace resale
        # Only block if EXPLICITLY marked as False (not missing, not None, not error)
        is_marketplace_suitable = tier1_result.get('marketplace_suitable')
        
        # Handle various false-y values
        if is_marketplace_suitable is None or is_marketplace_suitable == "" or is_marketplace_suitable == "null":
            is_marketplace_suitable = True
            print(f"📝 Note: marketplace_suitable field missing/null, defaulting to True")
        elif isinstance(is_marketplace_suitable, str):
            # Handle string "false" or "true"
            is_marketplace_suitable = is_marketplace_suitable.lower() != "false"
        
        suitability_reasoning = tier1_result.get('suitability_reasoning', '')
        
        if is_marketplace_suitable is False or is_marketplace_suitable == 0:  # Explicitly False only
            print(f"⚠️ Item not suitable for marketplace: {suitability_reasoning}")
            
            # Format response without Tier 2 analysis
            response = {
                'success': True,
                'marketplace_suitable': False,
                'suitability_reasoning': suitability_reasoning,
                'saved_paths': saved_paths,
                'images_analyzed': len(processed_images),
                'tier1': tier1_result,
                'tier2': None,
                'backend': 'OpenAI Vision' if USE_OPENAI else 'CLIP',
                'message': 'Item not suitable for marketplace resale - Tier 2 analysis skipped'
            }
            
            # Still save a basic JSON file
            json_metadata = {
                'backend': 'OpenAI Vision' if USE_OPENAI else 'CLIP',
                'detail_level': detail_level,
                'rotation': rotation,
                'images_analyzed': len(processed_images),
                'saved_paths': saved_paths,
                'marketplace_suitable': False,
                'skip_reason': suitability_reasoning
            }
            json_path = save_comprehensive_json(tier1_result, None, json_metadata, None)
            response['json_saved_path'] = json_path
            
            return jsonify(response)
        
        print(f"✅ Item suitable for marketplace resale")
        
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
            
            # Check if Tier 2 had an error
            if tier2_result and tier2_result.get('error'):
                print(f"❌ Tier 2 analysis error: {tier2_result['error']}")
            else:
                print(f"✅ Tier 2 analysis completed successfully")
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
        
        # Try barcode/SKU lookup if found
        barcode_info = None
        if tier2_result:
            # Look for barcode in tier2 results
            barcode_found = tier2_result.get('barcode_sku_found')
            
            if barcode_found and barcode_found != 'null' and barcode_found != 'None':
                # Try direct lookup
                barcode_info = lookup_barcode(barcode_found)
            
            if not barcode_info:
                # Try extracting from visible text
                potential_barcodes = extract_barcodes_from_tier2(tier2_result)
                for barcode in potential_barcodes:
                    barcode_info = lookup_barcode(barcode)
                    if barcode_info:
                        break
        
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
        
        # Save comprehensive JSON file
        json_metadata = {
            'backend': 'OpenAI Vision' if USE_OPENAI else 'CLIP',
            'detail_level': detail_level,
            'rotation': rotation,
            'images_analyzed': len(processed_images),
            'saved_paths': saved_paths
        }
        json_path = save_comprehensive_json(tier1_result, tier2_result, json_metadata, barcode_info)
        response['json_saved_path'] = json_path
        
        if barcode_info:
            response['barcode_lookup'] = {
                'found': True,
                'barcode': barcode_info.get('barcode', ''),
                'title': barcode_info.get('title', ''),
                'brand': barcode_info.get('brand', '')
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
