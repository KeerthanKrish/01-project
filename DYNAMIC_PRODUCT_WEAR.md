# Dynamic Product-Specific Wear Detection

## Overview

The system now features **dynamic product-specific wear detection** that adapts to ANY product type, even uncommon ones like telescopes, musical instruments, or specialized equipment.

## How It Works

### The Pipeline

```
1. User uploads image(s)
   ↓
2. Tier 1: Identify category (e.g., "home goods", "accessories")
   ↓
3. Tier 2: Read all text → Identify SPECIFIC product (e.g., "insulated water bottle")
   ↓
4. Tier 2: AI thinks: "What typically wears/breaks on THIS specific product?"
   ↓
5. Tier 2: Create mental checklist of product-specific wear points
   ↓
6. Tier 2: Inspect for those specific issues
   ↓
7. Tier 2: ALSO check general damage (scratches, dents, etc.)
   ↓
8. Return comprehensive analysis
```

## Key Features

### 1. Dynamic Wear Point Generation

The AI doesn't use pre-programmed lists. Instead, it **dynamically determines** what typically wears on each product:

**Example - Water Bottle:**
```
AI thinks: "What typically wears on an insulated water bottle?"
→ Lid seal degradation
→ Coating chips/scratches
→ Dent affecting vacuum seal
→ Thread wear on cap
→ Bottom scratches from setting down
```

**Example - Wallet:**
```
AI thinks: "What typically wears on a bifold leather wallet?"
→ Card slot stretching
→ Fold crease cracking
→ Corner leather wear
→ Stitching separation at stress points
→ Snap/button wear
→ Interior lining condition
```

**Example - Telescope (uncommon item):**
```
AI thinks: "What typically wears on a telescope?"
→ Lens scratches or coating deterioration
→ Focus mechanism stiffness
→ Tripod mount thread wear
→ Mirror tarnishing (if reflector type)
→ Finder scope alignment
→ Tube dents affecting alignment
```

### 2. Product-Specific + General Damage

**TWO-PART INSPECTION:**

**Part 1: Product-Specific Wear**
- Based on how THIS product is used
- Focuses on failure points unique to the product
- Checks functional components
- Assesses wear that affects usability

**Part 2: General Physical Damage**
- Scratches, dents, scuffs (everywhere)
- Discoloration, cracks, chips
- Surface condition
- Cosmetic issues

### 3. Works for ANY Product

Even if the product isn't in any pre-defined list:

**Known categories:** Electronics, furniture, clothing, accessories, toys, home goods, sports equipment, books/media

**Unknown/uncommon items:** Telescope, musical instrument, power tool, camping gear, art supplies, etc.

The AI will:
1. Identify the specific product type
2. Think about its typical use case
3. Determine what parts experience stress
4. Create appropriate wear checklist
5. Inspect thoroughly

## JSON Structure

### Product-Specific Wear Analysis

```json
{
  "product_specific_wear_analysis": {
    "product_identified": "32oz insulated stainless steel water bottle",
    
    "typical_wear_points_for_this_product": [
      "Lid seal integrity (affects leak prevention)",
      "Vacuum seal/insulation (dents can compromise)",
      "Powder coat finish (chips/scratches)",
      "Thread condition on cap (affects sealing)",
      "Bottom scuffs from setting down"
    ],
    
    "inspection_results": [
      {
        "wear_point": "lid seal",
        "status": "good",
        "details": "Seal appears intact, no visible cracks or deformation",
        "severity": "none",
        "affects_function": false
      },
      {
        "wear_point": "bottom dent",
        "status": "fair",
        "details": "Small dent on bottom right, approximately 0.5 inch diameter",
        "severity": "minor",
        "affects_function": false
      },
      {
        "wear_point": "powder coat",
        "status": "good",
        "details": "Minor scratches around base, coating mostly intact",
        "severity": "minor",
        "affects_function": false
      }
    ],
    
    "summary": "Water bottle shows typical usage wear. Dent is cosmetic only and does not affect insulation or functionality. Lid seal in good condition ensures proper leak prevention."
  },
  
  "general_physical_damage": {
    "scratches": ["Light scratches around bottom edge (minor)"],
    "dents": ["Small dent bottom right, 0.5 inch (moderate cosmetic)"],
    "scuffs": ["Base shows normal scuff marks from use"],
    "discoloration": [],
    "cracks_or_chips": [],
    "other_damage": []
  },
  
  "functionality_assessment": {
    "appears_functional": true,
    "confidence": 0.90,
    "reasoning": "All functional components (lid, seal, insulation) appear intact. Dent is external only.",
    "concerns": []
  }
}
```

## UI Display

### Product-Specific Wear Section (Orange/Yellow)

Shows:
- Product identified
- Typical wear points for THIS product
- Detailed inspection results per wear point:
  - Status (color-coded: green=excellent, blue=good, orange=fair, red=poor)
  - Details of observation
  - Severity rating
  - Functional impact (yes/no)
  - Which images showed it (multi-angle)
- Summary assessment

### General Damage Section (Red)

Shows:
- Scratches (with locations)
- Dents (with locations)
- Scuffs (with locations)
- Discoloration
- Cracks/chips
- Other damage

### Functionality Section (Green/Red)

Shows:
- Functional status (✅ or ❌)
- Confidence level
- Reasoning
- Specific concerns

## Examples by Product Type

### Water Bottle
**Typical Wear Points:**
- Lid seal condition
- Insulation integrity
- Coating condition
- Thread wear
- Base scratches

### Wallet
**Typical Wear Points:**
- Card slot stretching
- Fold crease condition
- Corner wear
- Stitching integrity
- Snap/button function

### Telescope
**Typical Wear Points:**
- Lens scratches/coating
- Focus mechanism
- Mount threads
- Mirror condition
- Tube alignment
- Finder scope

### Backpack
**Typical Wear Points:**
- Zipper teeth/slider
- Strap attachment points
- Bottom panel wear
- Buckle integrity
- Back padding
- Interior lining

### Headphones
**Typical Wear Points:**
- Ear pad deterioration
- Headband cracks
- Cable fraying
- Driver condition
- Adjustment mechanism
- Jack/connector

### Camera
**Typical Wear Points:**
- Lens element condition
- Shutter mechanism
- Battery door latch
- Viewfinder clarity
- Mount condition
- Mode dial function

## Prompt Engineering Key

### Critical Instructions to AI:

1. **"THINK: What typically wears/breaks on THIS specific product?"**
   - Forces the AI to be product-specific
   - Not just category-level

2. **"Create a mental checklist based on how this product is used"**
   - Considers usage patterns
   - Focuses on stress points

3. **"Check EACH item on your checklist"**
   - Ensures thoroughness
   - Structured inspection

4. **"Document: what/where/severity/function impact"**
   - Complete information
   - Actionable for buyers

## Benefits

### For Sellers:
- Complete condition documentation
- Professional-grade assessment
- Confidence in listing accuracy
- Reduce buyer disputes

### For Buyers:
- Know exactly what they're getting
- Understand product-specific issues
- Make informed purchase decisions
- Realistic expectations

### For the System:
- Works on ANY product
- No need to pre-program everything
- Scales infinitely
- Gets smarter over time

## Testing Examples

### Test 1: Water Bottle
**Input:** Multi-angle photos of water bottle  
**Expected:** Lid seal, coating, dent impact on insulation, thread condition

### Test 2: Wallet
**Input:** Photos of leather wallet  
**Expected:** Card slots, fold crease, stitching, snap, corner wear

### Test 3: Telescope (uncommon)
**Input:** Photos of telescope  
**Expected:** Lens condition, focus mechanism, mount threads, mirror (if visible), tube dents

### Test 4: Gaming Controller
**Input:** Photos of game controller  
**Expected:** Button responsiveness indicators, stick drift signs, trigger wear, grip condition, battery contacts

## Try It Now!

```bash
python app.py
```

Test with any product - the AI will:
1. Identify the specific product
2. Think about what wears on that product
3. Check for those specific issues
4. Also check general damage
5. Provide complete assessment

Works for **literally any product**, even ones never seen before!
