# Data Collection Guide

This guide explains how to gather marketplace images for testing and training the detection system.

## Quick Start

### Option 1: Use Existing Datasets (Recommended)

Download pre-labeled images from open datasets:

1. **Open Images V7** (https://storage.googleapis.com/openimages/web/index.html)
   - Download specific categories: electronics, furniture, clothing, vehicles
   - Use the OIDv4 toolkit for easy downloading

2. **ImageNet** (https://www.image-net.org/)
   - Download synsets for relevant categories
   - Good for general object categories

3. **Stanford Products Dataset** (https://cvgl.stanford.edu/projects/lifted_struct/)
   - 120k images of 23k products
   - Great for fine-grained recognition

4. **DeepFashion** (for clothing)
   - http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html
   - Specialized clothing dataset

5. **CompCars / Stanford Cars** (for vehicles)
   - http://mmlab.ie.cuhk.edu.hk/datasets/comp_cars/index.html
   - http://ai.stanford.edu/~jkrause/cars/car_dataset.html

### Option 2: Scrape from Marketplaces (Respect ToS)

**Important**: Always respect website Terms of Service and robots.txt

Common sources:
- eBay (public listings)
- Facebook Marketplace
- Craigslist
- Etsy
- Amazon (product images)

Example scraping approach:
```python
import requests
from bs4 import BeautifulSoup
import time

# Example (pseudo-code - adjust for actual site)
def scrape_listings(url, category):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    images = []
    for img in soup.find_all('img', class_='listing-image'):
        img_url = img.get('src')
        images.append(img_url)
    
    return images
```

### Option 3: Synthetic Images (For Testing)

Create synthetic test images using the demo script:

```bash
python demo.py
```

This generates sample images in `data/raw/`.

## Data Organization

Organize your collected data as follows:

```
data/
├── raw/                      # Original images
│   ├── electronics/
│   │   ├── phone_001.jpg
│   │   ├── laptop_002.jpg
│   │   └── ...
│   ├── furniture/
│   │   ├── chair_001.jpg
│   │   ├── table_002.jpg
│   │   └── ...
│   ├── clothing/
│   │   └── ...
│   └── vehicles/
│       └── ...
├── processed/                # Preprocessed images
└── annotations/              # Labels and metadata
    ├── labels.json
    └── metadata.json
```

## Annotation Format

Create a `labels.json` file with this structure:

```json
{
  "images": [
    {
      "id": "001",
      "filename": "electronics/phone_001.jpg",
      "category": "electronics",
      "attributes": {
        "product_type": "smartphone",
        "brand": "Apple",
        "model": "iPhone 14 Pro",
        "condition": "used",
        "color": "black"
      }
    },
    {
      "id": "002",
      "filename": "furniture/chair_001.jpg",
      "category": "furniture",
      "attributes": {
        "furniture_type": "chair",
        "style": "modern",
        "material": "wood"
      }
    }
  ]
}
```

## Sample Size Recommendations

For effective testing and training:

### Minimum (Quick Testing)
- 20-50 images per category
- Cover 5-10 major categories
- Total: 100-500 images

### Good (Model Validation)
- 100-200 images per category
- Cover 10-15 categories
- Total: 1,000-3,000 images

### Optimal (Fine-tuning)
- 500-1,000 images per category
- Cover all relevant categories
- Total: 5,000-20,000 images
- Include variation in:
  - Lighting conditions
  - Backgrounds
  - Angles and orientations
  - Item conditions
  - Image quality

## Data Quality Guidelines

### Good Images
✓ Clear and well-lit
✓ Item is prominent in frame
✓ Minimal clutter in background
✓ Multiple angles of same item
✓ Various lighting conditions
✓ Different image qualities (good and poor)

### Avoid
✗ Extremely blurry images
✗ Items too small in frame
✗ Multiple unrelated items (unless testing multi-object detection)
✗ Watermarked images (unless training on real marketplace data)

## Automated Collection Script

Here's a template script to help organize your data:

```python
import os
import json
from pathlib import Path
import shutil

def organize_dataset(source_dir, target_dir):
    """
    Organize downloaded images into category folders.
    
    Args:
        source_dir: Directory with downloaded images
        target_dir: Target directory (e.g., data/raw)
    """
    categories = [
        'electronics', 'furniture', 'clothing', 'vehicles',
        'home_and_garden', 'sports', 'books', 'toys'
    ]
    
    # Create category folders
    for category in categories:
        os.makedirs(os.path.join(target_dir, category), exist_ok=True)
    
    # Move images (you'll need to implement category detection)
    # This is a simplified example
    for img_file in Path(source_dir).glob('*.jpg'):
        # Detect category from filename or use model
        # category = detect_category(img_file)
        # shutil.copy(img_file, f"{target_dir}/{category}/{img_file.name}")
        pass

def create_annotation_template(data_dir, output_file):
    """Create annotation template from collected images."""
    annotations = {"images": []}
    
    for category_dir in Path(data_dir).iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        for img_file in category_dir.glob('*.jpg'):
            annotations["images"].append({
                "id": img_file.stem,
                "filename": f"{category}/{img_file.name}",
                "category": category,
                "attributes": {}  # Fill in manually or use model predictions
            })
    
    with open(output_file, 'w') as f:
        json.dump(annotations, f, indent=2)
    
    print(f"Created annotation template: {output_file}")
    print(f"Total images: {len(annotations['images'])}")

if __name__ == "__main__":
    # Example usage
    create_annotation_template("data/raw", "data/annotations/labels_template.json")
```

## Data Augmentation

Once you have a base dataset, augment it to increase variety:

```python
from albumentations import (
    Compose, RandomRotate90, Flip, Transpose,
    RandomBrightnessContrast, HueSaturationValue,
    GaussianBlur, MotionBlur
)
import cv2

def augment_images(image_dir, output_dir, num_augmentations=3):
    """Generate augmented versions of images."""
    
    transform = Compose([
        RandomRotate90(),
        Flip(),
        RandomBrightnessContrast(p=0.5),
        HueSaturationValue(p=0.3),
        GaussianBlur(p=0.3),
    ])
    
    for img_path in Path(image_dir).glob('*.jpg'):
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        for i in range(num_augmentations):
            augmented = transform(image=image)['image']
            output_path = output_dir / f"{img_path.stem}_aug_{i}.jpg"
            cv2.imwrite(str(output_path), cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR))
```

## Using Collected Data

### Testing the System

```python
from src.pipeline import create_pipeline

pipeline = create_pipeline()

# Test on your collected images
image_path = "data/raw/electronics/phone_001.jpg"
result = pipeline.predict(image_path)
print(result)
```

### Evaluation

```python
from src.tier1_detector import create_category_detector
import json

# Load ground truth
with open("data/annotations/labels.json") as f:
    annotations = json.load(f)

# Extract test images and labels
test_images = [f"data/raw/{img['filename']}" for img in annotations['images']]
true_labels = [img['category'] for img in annotations['images']]

# Evaluate
detector = create_category_detector()
metrics = detector.evaluate(test_images, true_labels, top_k=3)
print(f"Accuracy: {metrics['top_1_accuracy']:.2%}")
```

## Next Steps

1. Collect 100-500 images using one of the methods above
2. Organize them into category folders
3. Create annotations file
4. Run evaluation script
5. Identify failure cases
6. Collect more data for weak categories
7. Consider fine-tuning models on your data

## Resources

- **Label Studio**: https://labelstud.io/ (annotation tool)
- **CVAT**: https://cvat.org/ (computer vision annotation tool)
- **Roboflow**: https://roboflow.com/ (dataset management)
- **Kaggle Datasets**: https://www.kaggle.com/datasets (pre-labeled datasets)

## Legal Considerations

- Always respect website Terms of Service
- Check robots.txt before scraping
- Don't violate copyright - use only for research/personal use
- Consider using Creative Commons licensed images
- Cite data sources in your work
