# Quick Start Guide

Get up and running with the Marketplace Detection System in minutes.

## Installation

### 1. Clone the repository
```bash
cd 01-project
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- PyTorch and torchvision
- Hugging Face Transformers (for CLIP)
- OpenCV and Pillow (for image processing)
- And other necessary packages

**Note**: Installation may take 5-10 minutes depending on your internet speed.

## Quick Demo

Run the demo script to see the system in action:

```bash
python demo.py
```

This will:
1. Create sample synthetic images
2. Run them through the detection pipeline
3. Show Tier 1 (category) and Tier 2 (attributes) results
4. Save results to `data/processed/demo_results.json`

## Using the System

### Option 1: Python API

```python
from src.pipeline import create_pipeline

# Initialize pipeline
pipeline = create_pipeline()

# Predict on a single image
result = pipeline.predict("path/to/image.jpg")

print(f"Category: {result['tier1']['category']}")
print(f"Confidence: {result['tier1']['confidence']:.2%}")

# For electronics, you'll also get:
if result['tier2']:
    print(f"Brand: {result['tier2'].get('brand')}")
    print(f"Product Type: {result['tier2'].get('product_type')}")
    print(f"Condition: {result['tier2'].get('condition')}")
```

### Option 2: Command Line

```bash
# Run on your own image
python demo.py path/to/your/image.jpg

# Run on multiple images
python demo.py image1.jpg image2.jpg image3.jpg
```

### Option 3: Jupyter Notebook

```bash
jupyter notebook notebooks/01_getting_started.ipynb
```

The notebook includes:
- Step-by-step walkthrough
- Interactive examples
- Customization options
- Batch processing examples

## System Architecture

```
Image Input
    ↓
[Preprocessing]
    ↓
[Tier 1: Category Detection]  ← CLIP zero-shot classification
    ↓
[Routing Logic]
    ↓
[Tier 2: Specialized Detectors]  ← Category-specific models
    ├─ Electronics Detector (brand, model, condition)
    ├─ Furniture Detector (coming soon)
    ├─ Clothing Detector (coming soon)
    └─ Vehicle Detector (coming soon)
    ↓
[Structured Output]
```

## Supported Categories

Currently, Tier 1 detects 16 categories:

✓ **With Tier 2 Support:**
- Electronics (brand, model, condition, color)

○ **Tier 1 Only:**
- Furniture
- Clothing and accessories
- Vehicles and automotive
- Home and garden
- Sports and recreation
- Books and media
- Baby and kids items
- Tools and hardware
- Jewelry and watches
- Musical instruments
- Art and collectibles
- Pet supplies
- Office supplies
- Health and beauty
- Toys and games

## Customization

### Adjust Confidence Threshold

```python
# Higher threshold = more conservative Tier 2 routing
pipeline.set_confidence_threshold(0.7)

# Lower threshold = more aggressive Tier 2 routing
pipeline.set_confidence_threshold(0.3)
```

### Add Custom Categories

```python
from src.tier1_detector import create_category_detector

detector = create_category_detector()
detector.add_category("vintage collectibles")
detector.add_category("handmade crafts")
```

### Process Batches

```python
image_paths = [
    "image1.jpg",
    "image2.jpg",
    "image3.jpg"
]

results = pipeline.predict_batch(image_paths)
for result in results:
    print(f"Category: {result['tier1']['category']}")
```

## Testing and Evaluation

### Run Unit Tests

```bash
pytest tests/test_pipeline.py -v
```

### Evaluate on Your Data

1. Collect test images (see `DATA_COLLECTION.md`)
2. Create annotations file at `data/annotations/labels.json`
3. Run evaluation:

```bash
python evaluate.py
```

This will generate:
- Accuracy metrics
- Per-category performance
- Confusion matrix
- Failure mode analysis
- Recommendations for improvement

## Common Issues

### Issue: "No module named 'torch'"
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### Issue: CUDA out of memory
**Solution**: System will automatically fall back to CPU. For faster inference, reduce batch size or use a smaller model.

### Issue: Low accuracy on your images
**Solutions**:
1. Collect more diverse training data
2. Check image quality (blur, lighting, framing)
3. Review categories - make sure they match what you're testing
4. Consider fine-tuning on your specific marketplace data

### Issue: Slow processing
**Solutions**:
1. Use GPU if available (CUDA)
2. Reduce image resolution in preprocessing
3. Use batch processing for multiple images
4. Consider model quantization for deployment

## Performance Benchmarks

On CPU (Intel i7):
- Tier 1 only: ~2-3 seconds per image
- Tier 1 + Tier 2: ~4-6 seconds per image

On GPU (NVIDIA RTX 3080):
- Tier 1 only: ~0.5 seconds per image
- Tier 1 + Tier 2: ~1-2 seconds per image

Batch processing (8 images):
- CPU: ~15-20 seconds total
- GPU: ~3-5 seconds total

## Next Steps

1. **Try it yourself**: Run `python demo.py`
2. **Explore code**: Check out `src/pipeline.py`
3. **Add data**: Follow `DATA_COLLECTION.md` to gather test images
4. **Evaluate**: Run `python evaluate.py` to measure performance
5. **Extend**: Implement Tier 2 detectors for new categories
6. **Fine-tune**: Train on marketplace-specific data for better accuracy

## Getting Help

- **Documentation**: Check `README.md` for full details
- **Data collection**: See `DATA_COLLECTION.md`
- **Examples**: Explore notebooks in `notebooks/`
- **Issues**: Common problems and solutions above

## Project Structure Reference

```
01-project/
├── demo.py                   # Quick demo script
├── evaluate.py              # Evaluation script
├── requirements.txt         # Dependencies
├── README.md               # Full documentation
├── QUICKSTART.md          # This file
├── DATA_COLLECTION.md     # Data gathering guide
├── src/                    # Source code
│   ├── pipeline.py         # Main pipeline
│   ├── tier1_detector.py   # Category detection
│   ├── tier2_detectors/    # Specialized detectors
│   ├── preprocessing.py    # Image preprocessing
│   └── utils.py           # Utilities
├── notebooks/              # Jupyter notebooks
├── tests/                  # Unit tests
└── data/                   # Data storage
    ├── raw/               # Original images
    ├── processed/         # Results and processed data
    └── annotations/       # Ground truth labels
```

Happy detecting! 🚀
