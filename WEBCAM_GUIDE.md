# Webcam Interface - Quick Start Guide

A modern web interface for real-time marketplace item detection using your webcam.

## Features

✨ **Live webcam feed**  
📸 **One-click capture and analysis**  
🎯 **Instant results display**  
💾 **Auto-save all captured images**  
🎨 **Clean, modern UI**  
🔄 **Continuous detection** (no need to restart)

## Setup

### 1. Make sure dependencies are installed

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set OpenAI API key for better accuracy

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here
```

If you don't set an API key, the app will use CLIP (free, local) instead.

### 3. Run the web app

```bash
python app.py
```

The app will:
- Start a local web server
- Automatically open your browser to http://localhost:5000
- Display the webcam interface

## Usage

1. **Allow webcam access** when prompted by your browser
2. **Position your item** in front of the webcam
3. **Click "Capture & Analyze"** button
4. **View results** on the right side:
   - Category (electronics, furniture, etc.)
   - Detailed attributes (brand, model, condition, color)
   - Confidence scores
   - AI reasoning (if using OpenAI)

All captured images are automatically saved to the `images/` folder with timestamps.

## Interface Overview

```
┌─────────────────────────────────────────────────┐
│  🎥 Marketplace Item Detector                   │
│  Point your webcam at an item and click capture │
├──────────────────┬──────────────────────────────┤
│                  │                              │
│  Live Webcam     │  Detection Results           │
│  Feed            │                              │
│  [●] Live        │  📦 Waiting for capture...   │
│                  │                              │
│                  │                              │
│  [Capture]       │                              │
│                  │                              │
└──────────────────┴──────────────────────────────┘
```

## Results Display

### Tier 1 - Category Detection
```
TIER 1: Category Detection
━━━━━━━━━━━━━━━━━━━━━━━━━
Category: electronics
Confidence: ███████████ 94.5%
💭 This is clearly an electronic device...
```

### Tier 2 - Detailed Analysis (for electronics)
```
TIER 2: Detailed Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━
Product Type: smartphone
Brand: Apple
Model: iPhone 14 Pro
Condition: like new
Color: space gray
💭 Identified as iPhone 14 Pro based on...
```

## Tips for Best Results

### Good Lighting
- Use natural light or bright room lighting
- Avoid shadows on the item
- Ensure item is clearly visible

### Camera Position
- Place item centered in frame
- Fill most of the frame with the item
- Keep camera steady

### Item Presentation
- Show the most distinctive angle
- For electronics: show front with screen/logo visible
- For furniture: show the main functional side
- For clothing: lay flat or on hanger

### Multiple Captures
- Try different angles for better accuracy
- Capture close-ups for detail detection
- All images are saved for later review

## Saved Images

Images are saved to: `images/capture_YYYYMMDD_HHMMSS.jpg`

Example:
- `images/capture_20260418_143022.jpg`
- `images/capture_20260418_143055.jpg`
- `images/capture_20260418_143127.jpg`

You can review these images later or use them for training/evaluation.

## Keyboard Shortcuts

- **Space**: Capture & Analyze (when button is focused)
- **Ctrl+C**: Stop the server (in terminal)

## Backend Options

### Using CLIP (Default if no API key)
- ✅ Free, runs locally
- ✅ No internet required
- ⚠️ 60-80% accuracy
- ⚠️ Limited brand detection

### Using OpenAI Vision (Recommended)
- ✅ 90-95% accuracy
- ✅ Detailed reasoning
- ✅ Model identification
- ⚠️ Requires internet
- ⚠️ ~$0.01 per capture

## Troubleshooting

### "Camera Error: Unable to access webcam"

**Solutions**:
1. Grant browser permission to access camera
2. Make sure no other app is using the webcam
3. Try a different browser (Chrome recommended)
4. Check Windows Privacy Settings:
   - Settings → Privacy → Camera
   - Enable camera access for apps

### "OpenAI API error"

**Solutions**:
1. Check your API key is correct
2. Verify you have API credits remaining
3. Check your internet connection
4. The app will fall back to CLIP automatically

### "Detection failed"

**Solutions**:
1. Try better lighting
2. Move item closer to camera
3. Ensure item is centered in frame
4. Try a different angle

### Slow processing

**Normal times**:
- CLIP: 2-4 seconds
- OpenAI: 3-6 seconds

If slower:
1. Check internet connection (for OpenAI)
2. Close other programs using GPU
3. Try using gpt-4o-mini model (faster)

### Browser not opening automatically

Manually open: http://localhost:5000

## Advanced Usage

### Change Port

Edit `app.py`, line with:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

Change `port=5000` to your desired port.

### Use on Network

Access from other devices on your network:
1. Find your computer's IP (e.g., 192.168.1.100)
2. Open http://YOUR_IP:5000 on other device
3. Make sure firewall allows port 5000

### Batch Capture Mode

Hold items up one after another and click capture multiple times.
All images are saved with unique timestamps.

## API Endpoints

If you want to integrate with other tools:

### POST /detect
```bash
curl -X POST http://localhost:5000/detect \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_image_data"}'
```

### GET /health
```bash
curl http://localhost:5000/health
```

## Stop the Server

Press **Ctrl+C** in the terminal to stop the web server.

## Next Steps

1. Test with various items around you
2. Compare results with different backends
3. Review saved images in `images/` folder
4. Use images for model training/evaluation
5. Share results with your team

## Support

For issues:
1. Check this guide first
2. Review error messages in terminal
3. Try different lighting/angles
4. Test with different items

Happy detecting! 🚀
