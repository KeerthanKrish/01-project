# Marketplace Item Detection System

**AI-powered product analysis for marketplace listings using GPT-4 Vision**

Automatically detect, analyze, and grade products for resale platforms with comprehensive condition assessments, product-specific wear detection, and barcode lookup.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

Or create a `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

### 3. Run the Web Interface

```bash
python app.py
```

Open http://localhost:5000 in your browser.

### 4. Or Use Standalone Detection

```bash
python detector.py product.jpg
python detector.py img1.jpg img2.jpg img3.jpg  # Multi-angle
```

Or use in Python:
```python
from detector import analyze_product

result = analyze_product("product.jpg", detail_level="detailed")
print(result['tier2']['brand'])
print(result['marketplace_listing']['title'])
```

---

## 🎯 What It Does

### Core Workflow

```
Images → Marketplace Filter → Category → Detailed Analysis → Barcode Lookup → JSON Outputs
                                                                                    ↓
                                                          Comprehensive Analysis (jsons/)
                                                          Search Optimization (search_jsons/)
```

1. **Marketplace Suitability Check** - Filters out unsuitable items (trash, food, hazardous materials)
2. **Tier 1: Category Detection** - Identifies the broad category (electronics, furniture, clothing, etc.)
3. **Tier 2: Detailed Analysis** - Comprehensive product assessment:
   - **Specific Product Identification** - Exact product type and brand
   - **General Damage Inspection** - Scratches, dents, scuffs, discoloration
   - **Product-Specific Wear Detection** - Dynamically identifies and checks typical wear points for that product
   - **Functionality Assessment** - Working condition and concerns
   - **Marketplace Grading** - A/B/C/D cosmetic grade and selling points
4. **Barcode Lookup** - Fetches additional product data from UPC/EAN if detected
5. **JSON Outputs** - Saves TWO files automatically:
   - **Comprehensive Analysis** (`jsons/analysis_TIMESTAMP.json`) - Full detailed report
   - **Search Payload** (`search_jsons/search_TIMESTAMP.json`) - Optimized for similarity search APIs

### Product-Specific Wear Detection

The system doesn't just look for generic damage - it **dynamically determines** what typically wears on each specific product and checks for those issues:

| Product | Typical Wear Points Checked |
|---------|---------------------------|
| Water Bottle | Lid seal degradation, coating chips, vacuum seal integrity, thread condition |
| Wallet | Card slot stretching, fold crease cracking, stitching separation, snap wear |
| Headphones | Ear pad deterioration, headband cracks, cable fraying at strain relief |
| Backpack | Zipper teeth damage, strap attachment fraying, bottom panel wear, buckle cracks |
| Camera | Lens scratches, shutter mechanism, battery door, sensor dust |
| Glasses | Nose pad wear, hinge looseness, arm temple tips, lens coating scratches |
| Telescope | Lens scratches, focus mechanism stiffness, mount wear, mirror tarnish |

**How it works:**
1. AI identifies the **specific** product (e.g., "32oz insulated water bottle")
2. AI thinks: "What typically breaks or wears on THIS product?"
3. AI inspects for those specific wear points
4. AI also checks for general damage (scratches, dents, etc.)

This provides **much more thorough** condition assessment than generic damage detection.

### Search Optimization Payloads

**Automatically generated for every analysis** - the system creates a second JSON file optimized for similarity-search APIs.

**What it does:**
- Extracts only high-signal attributes (brand, product type, material, color, features)
- Removes analysis metadata, confidence scores, reasoning text, wear details
- Converts technical descriptions into shopper-friendly search terms
- Generates multiple query formats for different search strategies

**Output includes:**
- `primary_query`: Most precise buyer-style search string
- `fallback_query`: Broader version with fewer constraints
- `keywords`: 3-8 high-signal terms for filtering
- `filters`: Structured fields when clearly available
- `excluded_fields`: Important fields that were omitted (with reasoning)

**Use cases:**
- Feed into Algolia, Elasticsearch, or Pinecone for similarity matching
- Find comparable listings on eBay, Poshmark, Mercari
- Price research and competitive analysis
- Automated cross-listing to multiple marketplaces

**Example transformation:**

*From comprehensive analysis:*
```json
{
  "brand": "Sony",
  "brand_confidence": 0.98,
  "product_type": "WH-1000XM4 over-ear wireless noise-canceling headphones",
  "material": "plastic and synthetic leather",
  "color": "black",
  "condition": "Good",
  "visible_text_found": ["Sony", "WH-1000XM4", "Made in China"],
  "product_specific_wear_analysis": {...},
  "general_physical_damage": {...}
}
```

*To search payload:*
```json
{
  "primary_query": "Sony WH-1000XM4 wireless noise canceling headphones black",
  "fallback_query": "Sony wireless noise canceling headphones",
  "keywords": ["Sony", "WH-1000XM4", "wireless", "noise-canceling", "over-ear", "headphones", "black"],
  "filters": {
    "brand": "Sony",
    "model": "WH-1000XM4",
    "category": "electronics",
    "color": "black"
  },
  "excluded_fields": ["condition", "wear_analysis", "confidence_scores"]
}
```

---

## 📦 Features

### Web Interface (`app.py`)
- **Live Webcam Capture** - Real-time video feed for taking photos
- **Drag-and-Drop Upload** - Upload existing product photos
- **Multi-Angle Analysis** - Capture/upload up to 20+ images for comprehensive assessment
- **Image Rotation** - 0°, 90°, 180°, 270° (rotates actual pixel data before analysis)
- **Detail Levels** - Quick, Normal, or Detailed analysis
- **Flash Control** - Turn camera torch on/off (mobile devices)
- **Live Results** - See analysis directly in the browser
- **Image Gallery** - Review captured images before analyzing

### Standalone Detector (`detector.py`)
- **Command-Line Interface** - Analyze images from terminal
- **Python API** - Integrate into your own projects
- **Batch Processing** - Analyze multiple products programmatically
- **Comprehensive JSON** - All analysis data saved automatically

---

## 🧠 How It Works (Technical)

### Technology Stack
- **AI Model**: OpenAI GPT-4o Vision (gpt-4o)
- **Backend**: Python, Flask
- **Frontend**: HTML, JavaScript, WebRTC
- **Image Processing**: Pillow (PIL)
- **External APIs**: UPCitemdb, Open Food Facts (barcode lookup)

### Detection Approach

#### Tier 1: Category Detection
Uses GPT-4 Vision with zero-shot classification to identify the product category from a predefined list:
- Electronics, Furniture, Clothing & Accessories, Vehicles & Automotive
- Home & Garden, Sports & Recreation, Books & Media, Baby & Kids Items
- Tools & Hardware, Jewelry & Watches, Musical Instruments, Art & Collectibles
- Pet Supplies, Office Supplies, Health & Beauty, Toys & Games

Also performs **marketplace suitability filtering** to catch unsuitable items (trash, food, hazardous materials) before detailed analysis.

#### Tier 2: Detailed Analysis
Uses GPT-4 Vision with comprehensive prompts to:

1. **Read ALL Text** (highest priority)
   - Brand names (printed, embossed, etched)
   - Model numbers and product codes
   - **Barcode/SKU numbers** (12-13 digits for UPC/EAN)
   - Size labels, material info, care instructions

2. **Identify Specific Product**
   - Not just category, but exact product type
   - Example: "bifold leather wallet" not just "wallet"
   - Example: "32oz insulated stainless steel water bottle" not just "bottle"

3. **Dynamic Product-Specific Wear Analysis**
   - AI determines: "What typically wears/breaks on THIS product?"
   - Creates mental checklist of product-specific wear points
   - Inspects each wear point systematically
   - Documents severity and functional impact

4. **General Damage Inspection**
   - Scratches (location, severity)
   - Dents and deformations
   - Scuffs and abrasions
   - Discoloration and stains
   - Cracks, chips, and breaks

5. **Functionality Assessment**
   - Does it appear to work?
   - What concerns exist based on visible damage?
   - Confidence level in functionality assessment

6. **Marketplace Grading**
   - Completeness (all parts present?)
   - Cleanliness level
   - Cosmetic grade (A/B/C/D)
   - Major concerns for buyers
   - Selling points for listings

#### Multi-Angle Enhancement
When analyzing multiple images:
- Each angle reveals different damage
- Brand/text visible from different perspectives
- More confident product identification
- More thorough wear point inspection
- Significantly improved accuracy

### Cost Optimization
- JPEG quality set to 85 (visually identical to 95, but 25-30% smaller)
- Images resized to max 2000px (API limit)
- Dynamic token scaling for multi-image requests
- Prevents JSON truncation while minimizing costs

---

## 📊 Output Format

### Two JSON Files Generated Per Analysis

1. **Comprehensive Analysis** (`jsons/analysis_TIMESTAMP.json`) - Full detailed report
2. **Search Payload** (`search_jsons/search_TIMESTAMP.json`) - Optimized for search APIs

### 1. Comprehensive Analysis JSON

Saved to `jsons/analysis_TIMESTAMP.json`:

```json
{
  "analysis_metadata": {
    "timestamp": "2026-04-18T14:30:00",
    "analysis_id": "20260418_143000",
    "images_analyzed": 3,
    "detail_level": "detailed"
  },
  
  "tier1_category_detection": {
    "category": "electronics",
    "confidence": 0.95,
    "marketplace_suitable": true,
    "suitability_reasoning": "Standard resalable product"
  },
  
  "tier2_detailed_analysis": {
    "brand": "Sony",
    "brand_confidence": 0.98,
    "brand_source": "printed on front and back",
    
    "product_type": "WH-1000XM4 over-ear wireless noise-canceling headphones",
    "material": "plastic and synthetic leather",
    "color": "black",
    "condition": "Good",
    
    "visible_text_found": [
      "Sony", "WH-1000XM4", "Made in China", "FCC ID: ..."
    ],
    "barcode_sku_found": "012345678905",
    
    "product_specific_wear_analysis": {
      "product_identified": "WH-1000XM4 headphones",
      "typical_wear_points_for_this_product": [
        "ear pad deterioration",
        "headband cushion wear",
        "hinge stress cracks",
        "cable port condition",
        "button functionality"
      ],
      "inspection_results": [
        {
          "wear_point": "ear pads",
          "status": "good",
          "details": "Synthetic leather shows minor creasing but no flaking",
          "severity": "minor",
          "affects_function": false
        },
        {
          "wear_point": "headband cushion",
          "status": "excellent",
          "details": "No visible wear or compression",
          "severity": "none",
          "affects_function": false
        }
      ],
      "summary": "Overall good condition with expected minor ear pad wear"
    },
    
    "general_physical_damage": {
      "scratches": ["small scratch on right ear cup (minor)"],
      "dents": [],
      "scuffs": ["light scuff on headband top (minor)"],
      "discoloration": [],
      "cracks_or_chips": []
    },
    
    "functionality_assessment": {
      "appears_functional": true,
      "confidence": 0.90,
      "reasoning": "All buttons visible and intact, no visible damage to drivers",
      "concerns": ["Cannot verify Bluetooth or noise cancellation from images"]
    },
    
    "marketplace_assessment": {
      "completeness": "complete (headphones only, no case or cable visible)",
      "cleanliness": "clean",
      "cosmetic_grade": "B",
      "major_concerns": ["Missing accessories (case, cable)"],
      "selling_points": ["Premium Sony brand", "Popular WH-1000XM4 model", "Good overall condition"]
    },
    
    "overall_confidence": 0.92
  },
  
  "barcode_lookup": {
    "found": true,
    "source": "UPCitemdb",
    "barcode": "012345678905",
    "title": "Sony WH-1000XM4 Wireless Noise Canceling Headphones",
    "brand": "Sony",
    "category": "Electronics > Audio > Headphones"
  },
  
  "marketplace_listing": {
    "title": "Sony WH-1000XM4 over-ear wireless noise-canceling headphones (Good Condition)",
    "description": "This is a Sony WH-1000XM4 over-ear wireless noise-canceling headphones. It is made of plastic and synthetic leather in black. Condition: Good. Overall good condition with expected minor ear pad wear.",
    "condition": "Good",
    "grade": "B",
    "selling_points": [
      "Premium Sony brand",
      "Popular WH-1000XM4 model",
      "Good overall condition"
    ],
    "buyer_concerns": [
      "Missing accessories (case, cable)"
    ]
  }
}
```

### 2. Search Optimization Payload JSON

Saved to `search_jsons/search_TIMESTAMP.json`:

```json
{
  "primary_query": "Sony WH-1000XM4 wireless noise canceling headphones black",
  "fallback_query": "Sony wireless noise canceling headphones",
  "keywords": [
    "Sony",
    "WH-1000XM4",
    "wireless",
    "noise-canceling",
    "over-ear",
    "headphones",
    "black",
    "bluetooth"
  ],
  "filters": {
    "brand": "Sony",
    "model": "WH-1000XM4",
    "category": "electronics",
    "subcategory": "audio",
    "product_type": "headphones",
    "features": ["wireless", "noise-canceling", "over-ear"],
    "color": "black",
    "material": "plastic"
  },
  "excluded_fields": [
    "condition (not relevant for new product search)",
    "confidence_scores (internal metadata)",
    "wear_analysis (condition-specific)",
    "marketplace_assessment (resale-specific)"
  ],
  "processing_time_ms": 1250,
  "generated_at": "2026-04-18T14:30:01",
  "source_analysis_id": "20260418_143000"
}
```

**Key differences:**
- No confidence scores or analysis metadata
- Shopper-friendly language ("noise canceling" not "noise-canceling functionality assessment")
- Multiple query formats for flexibility
- Structured filters for faceted search
- Links back to source analysis via `source_analysis_id`

---

## 🎨 Web Interface Features

### Webcam Mode
1. Allow camera access when prompted
2. Position product in frame
3. Adjust rotation if needed (0°/90°/180°/270°)
4. Use flash/torch if needed (mobile devices)
5. Click "Capture Image" to add to gallery
6. Capture multiple angles (recommended: 3-5 images)
7. Select detail level (Quick/Normal/Detailed)
8. Click "Analyze All Images" to start detection

### Upload Mode
1. Drag and drop images onto the "Upload Images" zone
2. Or click "Upload Images" to select files
3. Images added to the same gallery as webcam captures
4. Remove unwanted images by clicking the × button
5. Analyze as normal

### Results Display
- **Unsuitable Items**: Red warning banner with reason
- **Category**: Detected category with confidence
- **Brand & Product**: Specific identification
- **Condition**: Overall condition assessment
- **Damage Report**: Detailed physical damage breakdown
- **Product-Specific Wear**: Typical wear points inspection results
- **Barcode Data**: Additional product info if barcode found
- **Marketplace Info**: Ready-to-use listing data (title, description, grade)

---

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here    # Required
```

### Customization (in code)

#### Custom Categories
```python
detector = MarketplaceDetector(
    categories=["electronics", "furniture", "custom_category"]
)
```

#### Custom Model
```python
detector = MarketplaceDetector(
    model="gpt-4o-mini"  # Cheaper, slightly less accurate
)
```

#### Custom Output Folder
```python
detector = MarketplaceDetector(
    output_folder="my_analysis_results"
)
```

---

## 📂 Project Structure

```
01-project/
├── detector.py           # ⭐ Core detection engine (standalone, 45KB)
├── app.py               # ⭐ Flask web interface (6KB)
├── requirements.txt     # ⭐ Minimal dependencies (5 packages)
├── README.md           # ⭐ Comprehensive documentation
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore rules
│
├── templates/
│   └── webcam.html     # Web interface UI
│
├── images/             # Captured/uploaded images (auto-created, gitignored)
│   ├── .gitkeep
│   └── capture_*.jpg
│
├── jsons/              # Comprehensive analysis outputs (auto-created, gitignored)
│   ├── .gitkeep
│   └── analysis_*.json
│
└── search_jsons/       # Search optimization payloads (auto-created, gitignored)
    ├── .gitkeep
    └── search_*.json
```

---

## 🛠️ Development

### Adding Custom Analysis

Edit `detector.py` to modify prompts or add new analysis fields:

```python
def _build_analysis_prompt(self, category: str, detail_level: str, ...):
    # Add custom instructions to the prompt
    prompt = f"""
    ... existing prompt ...
    
    ALSO ANALYZE:
    - Your custom analysis requirement
    - Another custom field
    """
    
    # Update JSON format
    json_format = """
    {
        ...
        "your_custom_field": "value",
        ...
    }
    """
```

### Running Programmatically

```python
from detector import MarketplaceDetector

detector = MarketplaceDetector()

# Analyze single image
result = detector.analyze_images("product.jpg")

# Analyze multiple images
result = detector.analyze_images([
    "front.jpg",
    "back.jpg",
    "damage.jpg"
], detail_level="detailed")

# Access results
print(result['tier1']['category'])
print(result['tier2']['brand'])
print(result['tier2']['product_specific_wear_analysis'])
print(result['marketplace_listing']['title'])

# JSON already saved to jsons/ folder
print(f"Saved to: {result['json_saved_path']}")
```

### Batch Processing

```python
from detector import MarketplaceDetector
from pathlib import Path

detector = MarketplaceDetector()

# Process all products in a folder
for product_folder in Path("products").iterdir():
    if product_folder.is_dir():
        images = list(product_folder.glob("*.jpg"))
        result = detector.analyze_images([str(img) for img in images])
        print(f"Processed {product_folder.name}: {result['tier2']['brand']}")
```

---

## 💡 Tips for Best Results

### Photography
- **Good Lighting**: Natural light or bright indoor lighting
- **Multiple Angles**: 3-5 images minimum (front, back, sides, damage areas)
- **Text Visibility**: Ensure brand names and barcodes are in focus
- **Close-ups**: Take separate close-up shots of damage or wear areas
- **Plain Background**: Solid color background helps AI focus on product

### Detail Levels
- **Quick**: Fast, basic analysis (~500 tokens, ~30 seconds)
- **Normal**: Balanced accuracy and speed (~1000 tokens, ~45 seconds)
- **Detailed**: Most thorough analysis (~2000+ tokens, ~60-90 seconds)

### Multi-Angle Tips
- Front view with brand visible
- Back view with any labels or barcodes
- Side views showing wear areas
- Top/bottom views if relevant
- Close-ups of specific damage

### Accuracy Tips
- Clean the product before photographing
- Remove personal stickers (system tries to ignore them, but better to remove)
- Include size reference if possible (ruler, coin)
- Capture barcodes clearly for automatic product lookup

---

## 📝 Requirements

See `requirements.txt`:

```
flask==3.0.0
pillow==10.2.0
openai==1.12.0
requests==2.31.0
python-dotenv==1.0.0
```

**System Requirements:**
- Python 3.8+
- Internet connection (for OpenAI API and barcode lookup)
- Webcam (optional, for web interface)

---

## 🚨 Known Limitations

1. **Cannot Verify Functionality**: Can only assess if item *appears* functional based on visible damage
2. **Hidden Damage**: Cannot detect internal issues not visible in photos
3. **Barcode Reading**: May miss barcodes if blurry, obscured, or at bad angle
4. **Text Recognition**: Struggles with very small text or poor lighting
5. **Cost**: OpenAI API usage costs money (gpt-4o is ~$0.005/image typically)
6. **Internet Required**: Needs connection for OpenAI API and barcode lookup

---

## 🎓 Use Cases

- **Resellers**: Grade inventory for marketplace listings (eBay, Mercari, Poshmark, Facebook Marketplace)
- **Thrift Stores**: Quickly assess and price incoming inventory
- **Donation Centers**: Determine if items are worth accepting
- **Insurance**: Document item condition for claims
- **Estate Sales**: Catalog and assess large inventories
- **Personal**: Decide what's worth selling vs donating

---

## 🤝 Support

For issues or questions:
1. Check this README thoroughly
2. Review the JSON output for detailed analysis
3. Try "detailed" mode for better accuracy
4. Ensure good lighting and clear photos

---

## 📜 License

MIT License - feel free to use and modify as needed.

---

## 🎉 Credits

Built with:
- OpenAI GPT-4 Vision
- Flask web framework
- Pillow image processing
- UPCitemdb & Open Food Facts APIs

---

**Happy Analyzing!** 🚀
