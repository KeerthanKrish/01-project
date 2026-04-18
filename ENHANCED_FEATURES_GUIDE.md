# Enhanced Webcam Interface - Feature Guide

## 🎯 New Features

### 1. **Image Rotation Control**
- **Real rotation** of the captured image (not just CSS)
- 4 rotation options: 0°, 90°, 180°, 270°
- Applied BEFORE sending to API for accurate detection
- Rotated images saved with rotation angle in filename

### 2. **Detail Level Analysis**
- **Quick**: Fast basic detection (~3s)
- **Normal**: Standard marketplace analysis (~5s)  
- **Detailed**: Comprehensive inspection for listings (~7-10s)

### 3. **Enhanced Detail Detection**
For marketplace listings, the system now detects:
- **Condition notes**: Specific wear and tear
- **Physical damage**: Scratches, dents, scuffs with locations
- **Visible text**: Model numbers, serial numbers, labels
- **Small features**: Buttons, ports, camera details
- **Value indicators**: Cosmetic grade, functional status

---

## 🔄 Rotation Feature

### Why This Matters
When taking photos of items, your camera orientation affects detection accuracy. For example:
- A phone held vertically needs 0° rotation
- A phone laid flat may need 90° rotation
- Upside-down items need 180° rotation

### How It Works

**UI Rotation (❌ Wrong way)**:
```javascript
// This only rotates the display, not the actual image
video.style.transform = 'rotate(90deg)';  // Visual only!
```

**Actual Rotation (✅ Our implementation)**:
```javascript
// This rotates the pixel data before sending to API
const rotatedCanvas = rotateCanvas(canvas, 90);  // Real rotation!
// Then send rotated image to backend
```

### Technical Implementation

1. **Capture original frame** from webcam
2. **Create new canvas** with swapped dimensions if 90°/270°
3. **Rotate pixel data** using canvas transforms
4. **Encode rotated image** to base64
5. **Send to API** with rotation parameter
6. **Backend applies** PIL rotation to Image object
7. **Save** with rotation angle in filename

### Usage Tips

**For upright items** (phones, bottles):
- Use **0°** if camera is aligned with item
- Use **90°** if camera is sideways relative to item

**For flat items** (books, tablets):
- Try different angles to find best orientation
- **180°** for upside-down captures

**For products with text**:
- Rotate so text is readable
- AI performs better with correctly oriented text

---

## 🔍 Detail Level Options

### Quick Analysis (~3 seconds)
**Best for:**
- Rapid scanning of multiple items
- Initial category identification
- When you just need basic info

**What you get:**
- Product type
- Brand
- Model (if obvious)
- Basic condition
- Color

**Cost:** ~$0.003/image (with gpt-4o-mini)

### Normal Analysis (~5 seconds) - **Default**
**Best for:**
- Standard marketplace listings
- Most use cases
- Balance of speed and detail

**What you get:**
- Everything in Quick, plus:
- Detailed condition assessment
- Visible defects and wear
- Condition notes
- Text/numbers on device
- Notable features

**Cost:** ~$0.01/image (with gpt-4o)

### Detailed Analysis (~7-10 seconds)
**Best for:**
- High-value items
- Items needing thorough inspection
- When condition details are critical
- Professional listings

**What you get:**
- Everything in Normal, plus:
- **Comprehensive damage report** with locations
- **Serial/model numbers** from stickers
- **All visible text** transcribed
- **Accessory inventory** (cables, cases, boxes)
- **Technical feature analysis**
- **Cosmetic grading** (A/B/C/D)
- **Value indicators** for pricing
- **Listing quality suggestions**

**Cost:** ~$0.015/image (with gpt-4o)

---

## 📋 Detailed Analysis Output

When using **Detailed** mode, you get extensive marketplace-ready information:

### Condition Assessment
```json
{
  "condition": "good used condition",
  "condition_notes": [
    "Minor scratches on back panel near camera",
    "Small scuff on bottom right corner",
    "Screen is pristine with no marks"
  ],
  "physical_damage": [
    "Light scratching on aluminum frame",
    "Tiny dent on top edge (2mm)",
    "Normal wear on charging port"
  ],
  "cosmetic_grade": "B",
  "condition_confidence": 0.87
}
```

### Visible Details
```json
{
  "visible_text": [
    "iPhone",
    "256GB",
    "Model A2890"
  ],
  "serial_or_model_numbers": [
    "A2890",
    "IMEI partially visible"
  ],
  "storage_capacity": "256GB visible on back"
}
```

### Technical Features
```json
{
  "technical_features": {
    "camera_count": "3 (triple camera system)",
    "port_type": "Lightning connector",
    "special_features": [
      "Face ID visible at top",
      "Wireless charging capable (glass back)",
      "Ceramic Shield front"
    ]
  }
}
```

### Marketplace Value Indicators
```json
{
  "marketplace_value_indicators": {
    "appears_functional": true,
    "cosmetic_grade": "B",
    "likely_issues": [
      "Minor cosmetic wear may affect resale value",
      "Should test all buttons and cameras before listing"
    ]
  },
  "age_indicators": "Design suggests iPhone 14 series (2022-2023)",
  "listing_quality": {
    "photo_clarity": "clear",
    "lighting": "good",
    "angles_shown": "single angle - recommend multiple"
  }
}
```

---

## 💡 Best Practices

### For Rotation

1. **Test orientation first**: Capture at 0°, check results, rotate if needed
2. **Look at text**: Text should be readable after rotation
3. **Check AI response**: If brand/model is wrong, try different rotation
4. **Use landscape**: Items wider than tall often need 90° rotation

### For Detail Level

1. **Start with Normal**: Good balance for most items
2. **Use Quick for**:
   - Bulk scanning (50+ items)
   - Cost-sensitive operations
   - Initial sorting/categorization

3. **Use Detailed for**:
   - Electronics >$200
   - Items with visible damage
   - Professional/commercial listings
   - When buyer will scrutinize details

### For Best Detection

**Lighting**:
- Natural light preferred
- Avoid harsh shadows
- Ensure even illumination
- No glare on screens/glass

**Camera Position**:
- Fill frame with item (80% coverage)
- Steady camera (use tripod if possible)
- Perpendicular to item surface
- All important features visible

**Item Preparation**:
- Clean item before photographing
- Remove protective films if transparent
- Position logos/text facing camera
- Show multiple angles (capture 3-4 times with rotation)

**Detail Enhancement**:
- For small text: Get close-up shots
- For damage: Capture specific areas
- For accessories: Include in frame
- For boxes: Show labeling clearly

---

## 📸 Workflow Examples

### Example 1: Smartphone Listing

```
Step 1: Position phone upright
Step 2: Select "Detailed" analysis
Step 3: Capture at 0° (front view)
        → Get: Model, screen condition, Face ID details

Step 4: Rotate phone, capture at 90° (back view)
        → Get: Camera info, back condition, Apple logo

Step 5: Rotate to 0°, capture ports
        → Get: Lightning port condition, speaker grills

Result: Complete listing with:
- Exact model (iPhone 14 Pro, 256GB)
- Condition grade (B - good used)
- All visible damage noted
- Feature confirmation
- Ready for marketplace posting
```

### Example 2: Laptop Inspection

```
Step 1: Open laptop, position screen visible
Step 2: Select "Normal" analysis
Step 3: Capture at 0°
        → Get: Screen condition, keyboard state

Step 4: Close laptop, capture top at 0°
        → Get: Exterior condition, brand logo

Step 5: Flip laptop, capture bottom at 180°
        → Get: Model sticker, serial number, specs

Result: Complete laptop profile for listing
```

### Example 3: Batch Processing (20 items)

```
Step 1: Set to "Quick" mode (save time/cost)
Step 2: Arrange items on table
Step 3: Capture each at 0°
Step 4: Review results, note items needing detail
Step 5: Re-scan flagged items with "Detailed"

Time saved: ~5 minutes
Cost saved: ~$0.20
```

---

## 🎨 UI Features

### Rotation Controls
- **Visual feedback**: Active button highlighted
- **Persistent selection**: Stays until you change it
- **Clear labeling**: Degree markers (0°, 90°, 180°, 270°)

### Detail Level Controls
- **Color-coded**:
  - Quick: Gray (basic)
  - Normal: Green (recommended)
  - Detailed: Green (thorough)
- **Auto-defaults**: Normal mode selected by default

### Results Display
- **Tier 1 Card**: Always shown (category + confidence)
- **Tier 2 Card**: Shows when electronics detected
- **Detail Cards**: Extra info boxes for:
  - ⚠️ Condition notes (yellow background)
  - 🔍 Visible damage (yellow background)
  - 📝 Visible text (yellow background)
  - ✨ Features (yellow background)
- **Scrollable**: Results auto-scroll for long outputs

---

## ⚙️ Technical Details

### Image Quality
- **Capture resolution**: Up to 1920x1080
- **JPEG quality**: 95% (preserves fine details)
- **Format**: JPEG for compatibility
- **Storage**: Original resolution maintained

### Rotation Algorithm
```javascript
// 90° rotation
if (rotation === 90) {
    rotatedCanvas.width = originalHeight;
    rotatedCanvas.height = originalWidth;
    ctx.translate(rotatedCanvas.width/2, rotatedCanvas.height/2);
    ctx.rotate((90 * Math.PI) / 180);
    ctx.drawImage(canvas, -originalWidth/2, -originalHeight/2);
}
```

### Backend Processing
```python
def apply_rotation(image: Image.Image, rotation: int) -> Image.Image:
    if rotation == 90:
        return image.transpose(Image.ROTATE_270)  # PIL counter-clockwise
    elif rotation == 180:
        return image.transpose(Image.ROTATE_180)
    elif rotation == 270:
        return image.transpose(Image.ROTATE_90)
    return image
```

### Filename Convention
```
images/capture_20260418_143022_r90.jpg
                        ↑        ↑
                    timestamp   rotation
```

---

## 📊 Performance & Costs

### Processing Times
| Detail Level | CLIP | OpenAI Vision |
|--------------|------|---------------|
| Quick | 2-3s | 3-4s |
| Normal | 3-4s | 5-6s |
| Detailed | 4-5s | 8-12s |

### API Costs (OpenAI)
| Detail Level | gpt-4o | gpt-4o-mini |
|--------------|--------|-------------|
| Quick | ~$0.008 | ~$0.002 |
| Normal | ~$0.012 | ~$0.003 |
| Detailed | ~$0.020 | ~$0.005 |

### Recommendations
- **For 100 items with Normal**: ~$1.20 (gpt-4o) or ~$0.30 (gpt-4o-mini)
- **For 100 items with Detailed**: ~$2.00 (gpt-4o) or ~$0.50 (gpt-4o-mini)
- **Mixed approach**: Quick for initial scan, Detailed for valuable items

---

## 🚀 Quick Reference

### Keyboard Shortcuts
- **Space**: Trigger capture (when button focused)
- **Tab**: Navigate between controls
- **Arrow Keys**: Select rotation/detail options

### Common Issues

**"Image rotated wrong way"**
- Try opposite rotation (90° → 270°)
- Or use 180° + your rotation

**"Not detecting small text"**
- Use "Detailed" mode
- Get closer to item
- Ensure good lighting
- Text should be in focus

**"Condition detection inaccurate"**
- Use "Detailed" mode
- Better lighting to show scratches
- Multiple angles recommended
- Clean item first for fair assessment

---

## 💻 Development Notes

### Adding New Detail Levels
Edit `src/openai_detector.py`, add new prompt in `predict()` method:
```python
elif detail_level == "premium":
    prompt = """Your custom prompt here..."""
```

### Customizing Rotation
Edit `templates/webcam.html`, modify rotation options:
```html
<button class="rotation-btn" data-rotation="45">45°</button>
```

### Extending Results Display
Edit `displayResults()` function in HTML to show new fields.

---

**Pro Tip**: For professional listings, capture 4 images:
1. Front view (0°)
2. Back view (0° or 90°)
3. Side view (90°)
4. Detailed shot (close-up, 0°)

Then use "Detailed" analysis on the best shot for comprehensive listing data!
