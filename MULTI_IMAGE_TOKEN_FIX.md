# Fix: Multi-Image Analysis Stopping at Tier 1

**Date:** April 18, 2026  
**Issue:** With 14+ images, analysis would complete Tier 1 but skip Tier 2 entirely

## Root Cause Analysis

### The Problem Chain:

1. **Insufficient Token Limit** (Primary Issue)
   - `universal_detector.py` line 430 had:
   ```python
   max_tokens=2000 if detail_level == "detailed" else 1000
   ```
   - With 14 images, the AI needs to describe all angles
   - 1000 tokens (normal mode) or 2000 tokens (detailed mode) is insufficient
   - OpenAI truncates the response when it hits the token limit
   - Truncated JSON → JSON parsing fails → Exception thrown

2. **Silent Error Handling**
   - Exception handler returned a minimal object with an `error` field
   - UI checked `if (tier2 && !tier2.error)` before displaying Tier 2
   - Error existed but was never shown to user
   - **Result:** User only saw Tier 1, didn't know Tier 2 failed

3. **No Debugging Visibility**
   - No console logs showing what went wrong
   - No indication that token limit was exceeded
   - No way to diagnose the issue without reading code

## The Fix

### 1. Dynamic Token Scaling (`universal_detector.py`)

**BEFORE:**
```python
max_tokens=2000 if detail_level == "detailed" else 1000,
```

**AFTER:**
```python
# Scale max_tokens based on number of images
base_tokens = 3000 if detail_level == "detailed" else 2000
tokens_per_image = 150  # Extra tokens per additional image
max_tokens_calculated = base_tokens + (len(images) * tokens_per_image)
# Cap at OpenAI's limit
max_tokens_final = min(max_tokens_calculated, 4000)

print(f"🔧 Using {max_tokens_final} max tokens for {len(images)} images")
```

**Token Allocation Examples:**
- 1 image, normal mode: 2000 + (1 × 150) = 2150 tokens
- 5 images, normal mode: 2000 + (5 × 150) = 2750 tokens
- 14 images, normal mode: 2000 + (14 × 150) = 4000 tokens (capped)
- 14 images, detailed mode: 3000 + (14 × 150) = 4000 tokens (capped)

### 2. Enhanced Error Logging

**Added to `universal_detector.py`:**
```python
except Exception as e:
    error_msg = str(e)
    warnings.warn(f"OpenAI API error (multi-angle): {error_msg}")
    
    # Log more details for debugging
    print(f"❌ Multi-angle detection failed: {error_msg}")
    print(f"   - Number of images: {len(images)}")
    print(f"   - Detail level: {detail_level}")
    print(f"   - Category: {category}")
    
    return {
        "product_type": "unknown",
        "brand": "unknown",
        "condition": "unknown",
        "error": error_msg,
        "error_details": {
            "num_images": len(images),
            "detail_level": detail_level,
            "category": category
        },
        ...
    }
```

**Added to `app.py`:**
```python
# Check if Tier 2 had an error
if tier2_result and tier2_result.get('error'):
    print(f"❌ Tier 2 analysis error: {tier2_result['error']}")
else:
    print(f"✅ Tier 2 analysis completed successfully")
```

### 3. Minor Bug Fixes

- Fixed duplicate print statement on line 530 of `app.py`
- Added `🔧 Using X max tokens for Y images` log message

## Expected Behavior After Fix

### Terminal Output for 14 Images:
```
📸 Processing 14 image(s)...
  💾 Saved: images\capture_20260418_172122_1of14_r0.jpg
  ...
  💾 Saved: images\capture_20260418_172122_14of14_r0.jpg
🔍 Running Tier 1 detection...
✅ Item suitable for marketplace resale
🔍 Running Tier 2 detailed analysis for clothing and accessories with 14 angle(s)...
🔧 Using 4000 max tokens for 14 images
✅ Tier 2 analysis completed successfully
📄 Comprehensive JSON saved: jsons\analysis_20260418_172140.json
```

### If an Error Occurs (now visible):
```
🔍 Running Tier 2 detailed analysis for clothing and accessories with 14 angle(s)...
🔧 Using 4000 max tokens for 14 images
❌ Multi-angle detection failed: Expecting value: line 1 column 1 (char 0)
   - Number of images: 14
   - Detail level: normal
   - Category: clothing and accessories
❌ Tier 2 analysis error: Expecting value: line 1 column 1 (char 0)
```

## Testing Recommendations

1. **Test with varying image counts:**
   - 1 image (should work)
   - 5 images (should work)
   - 10 images (should work)
   - 14 images (should now work!)
   - 20 images (test upper limits)

2. **Test with different detail levels:**
   - Quick mode with many images
   - Normal mode with many images
   - Detailed mode with many images

3. **Monitor terminal output:**
   - Look for "🔧 Using X max tokens" message
   - Verify "✅ Tier 2 analysis completed successfully"
   - Check for any error messages

## Why This Issue Was Hard to Spot

1. **No error displayed to user** - UI silently failed
2. **Token limits are hidden** - OpenAI truncates silently
3. **Worked fine with few images** - Only manifested at scale
4. **JSON parsing errors are cryptic** - "Expecting value: line 1" doesn't hint at truncation

## Long-Term Improvements

Consider:
1. Add a warning in UI if > 10 images uploaded
2. Implement image count cap (e.g., max 15 images)
3. Add "Retry with fewer images" button if Tier 2 fails
4. Show token usage stats in JSON output for monitoring
5. Implement automatic image grouping for very large sets
