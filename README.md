# Marketplace Vision System

A hierarchical computer vision system for detecting and classifying items commonly sold on marketplace platforms.

## Overview

This project implements a two-tier detection pipeline:
- **Tier 1**: Broad category classification (electronics, furniture, clothing, vehicles, etc.)
- **Tier 2**: Specific attribute extraction (brand, model, condition, style, etc.)

## Installation

```bash
pip install -r requirements.txt
```

## Project Structure

```
01-project/
├── data/                    # Dataset storage
│   ├── raw/                # Original images
│   ├── processed/          # Preprocessed images
│   └── annotations/        # Labels and metadata
├── models/                  # Model storage
│   ├── tier1/              # Category detection models
│   ├── tier2/              # Specialized models
│   └── checkpoints/        # Saved weights
├── src/                     # Source code
│   ├── preprocessing.py    # Image preprocessing
│   ├── tier1_detector.py   # Category detection
│   ├── tier2_detectors/    # Specialized detectors
│   ├── pipeline.py         # End-to-end pipeline
│   └── utils.py           # Helper functions
├── notebooks/               # Jupyter notebooks
└── tests/                   # Unit tests
```

## Quick Start

### Option 1: Webcam Interface (Easiest!) - **ENHANCED**

```bash
python app.py
```

Opens a web interface with:
- **Flash/torch control** - Toggle camera flash on/off (NEW!)
- **Universal category analysis** - Detailed analysis for ALL product types (NEW!)
- **Multi-angle capture** - Take 2-4 photos from different angles for better accuracy
- **Live webcam feed** with gallery view
- **Image rotation controls** (0°, 90°, 180°, 270°) - rotates actual image, not just display
- **Detail level selector** (Quick/Normal/Detailed) for marketplace listings
- **Small feature detection** - finds scratches, text, model numbers, damage
- **Instant results** with comprehensive analysis
- **Cross-angle verification** - combines multiple views for better brand/wear detection

See:
- [`LATEST_FEATURES.md`](LATEST_FEATURES.md) - Flash control & universal analysis (NEW!)
- [`MULTI_IMAGE_GUIDE.md`](MULTI_IMAGE_GUIDE.md) - Multi-angle capture
- [`WEBCAM_GUIDE.md`](WEBCAM_GUIDE.md) - Basic webcam usage
- [`ENHANCED_FEATURES_GUIDE.md`](ENHANCED_FEATURES_GUIDE.md) - Rotation and detail analysis

### Option 2: Command Line - CLIP (Free, runs locally)

```bash
pip install -r requirements.txt
python demo.py
```

### Option 3: Command Line - OpenAI Vision API (90-95% accuracy, recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key (get from https://platform.openai.com/api-keys)
set OPENAI_API_KEY=sk-your-key-here

# Run with your image
python demo_openai.py path/to/your/image.jpg
```

**OpenAI Vision provides superior accuracy!** See [`OPENAI_VISION_GUIDE.md`](OPENAI_VISION_GUIDE.md) for details.

### Python API

```python
# Using CLIP (default)
from src.pipeline import MarketplaceDetectionPipeline
pipeline = MarketplaceDetectionPipeline()
result = pipeline.predict("path/to/image.jpg")

# Using OpenAI Vision (better accuracy)
from src.openai_detector import create_openai_category_detector
detector = create_openai_category_detector()
result = detector.predict("path/to/image.jpg")
```

## Features

### Two Detection Backends:

**CLIP (Default)**
- Zero-shot classification - no training needed
- Runs locally (free)
- 60-80% accuracy
- Fast inference

**OpenAI Vision API (Recommended)**
- 90-95% accuracy
- Brand & model detection
- Detailed reasoning
- ~$0.01-0.02 per image

### System Features:
- Hierarchical detection for better accuracy
- Extensible architecture for new categories
- Confidence scoring and uncertainty handling
- Batch processing support

Project for 01 summit hackathon.