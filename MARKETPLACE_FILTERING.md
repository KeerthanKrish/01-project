# Marketplace Suitability Filtering

## Overview

The system now automatically filters out items that are not suitable for marketplace resale platforms. This prevents wasted processing on items that cannot or should not be sold online.

## How It Works

### 1. Tier 1 Marketability Check

After the initial category detection (Tier 1), the AI evaluates whether the item is appropriate for marketplace resale before proceeding to detailed analysis (Tier 2).

### 2. Items That Are Filtered Out

The following types of items are automatically identified as **not suitable for marketplace resale**:

- **Trash, garbage, or waste** - Discarded items with no value
- **Perishable food or beverages** - Fresh produce, drinks, meals
- **Opened/consumed food items** - Partially eaten food or opened packages
- **Hazardous materials** - Chemicals, toxic substances, dangerous goods
- **Bodily fluids or medical waste** - Health and safety concerns
- **Extremely damaged/broken items beyond repair** - Items with no functional or aesthetic value
- **Items with no resale value** - Worthless or unsellable objects
- **Contraband or illegal items** - Items that cannot be legally sold

### 3. Processing Flow

```
Image Capture
    ↓
Tier 1: Category Detection + Marketability Check
    ↓
├─ NOT SUITABLE → Skip Tier 2, show warning to user
└─ SUITABLE → Continue to Tier 2 detailed analysis
```

## User Interface

When an item is deemed not suitable:

### Red Warning Banner
- Large "⛔ Not Suitable for Marketplace Resale" message
- Clear explanation of why the item was rejected
- Note that detailed condition analysis was skipped

### Information Included
- Basic category detection (what the AI saw)
- Specific suitability reasoning
- Saved image paths (if captured)
- Basic JSON file (no Tier 2 data)

## Example Scenarios

### Scenario 1: Trash
```
User captures: Empty pizza box with food residue
Result: "Not suitable - This appears to be food waste/garbage with no resale value"
```

### Scenario 2: Perishable Food
```
User captures: Fresh apple
Result: "Not suitable - This is a perishable food item that cannot be sold on online marketplaces"
```

### Scenario 3: Broken Beyond Repair
```
User captures: Shattered glass, completely destroyed electronics
Result: "Not suitable - Item is too damaged to have any resale value"
```

### Scenario 4: Resellable Item (Normal Flow)
```
User captures: Used laptop with minor scratches
Result: ✅ Proceeds to full Tier 2 analysis with brand, model, condition details
```

## Technical Details

### API Response Structure (Not Suitable)

```json
{
  "success": true,
  "marketplace_suitable": false,
  "suitability_reasoning": "This appears to be food waste with no resale value",
  "saved_paths": ["images/capture_20260418_123456_1.jpg"],
  "images_analyzed": 1,
  "tier1": {
    "category": "unknown",
    "confidence": 0.95,
    "marketplace_suitable": false,
    "suitability_reasoning": "..."
  },
  "tier2": null,
  "message": "Item not suitable for marketplace resale - Tier 2 analysis skipped",
  "json_saved_path": "jsons/analysis_20260418_123456.json"
}
```

### Saved JSON File (Not Suitable)

A basic JSON file is still created for record-keeping, but without Tier 2 data:

```json
{
  "analysis_id": "analysis_20260418_123456",
  "timestamp": "2026-04-18T12:34:56.123456",
  "metadata": {
    "backend": "OpenAI Vision",
    "images_analyzed": 1,
    "marketplace_suitable": false,
    "skip_reason": "This appears to be trash/waste..."
  },
  "tier1_category_detection": {
    "category": "unknown",
    "confidence": 0.95,
    "marketplace_suitable": false
  },
  "tier2_detailed_analysis": null
}
```

## Benefits

### 1. Efficiency
- Saves API calls for unsuitable items
- Reduces processing time
- Lowers costs

### 2. User Experience
- Clear feedback on why an item cannot be listed
- Prevents users from wasting time on non-sellable items
- Guides users toward appropriate items

### 3. Data Quality
- Cleaner dataset of actual marketplace items
- More accurate condition reports for valid items
- Better training data for future improvements

## Configuration

The marketability check is **always enabled** and runs automatically as part of Tier 1 detection. No configuration needed.

## Notes

- The check is performed by GPT-4 Vision using advanced image understanding
- Borderline cases (e.g., damaged but repairable items) are allowed to proceed
- Users can still capture images of unsuitable items - they just won't receive detailed analysis
- All images are saved regardless of marketability status
