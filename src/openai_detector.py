"""
OpenAI Vision API detector using GPT-4V for superior accuracy.
This provides much better detection than CLIP for marketplace items.
"""

import os
import base64
from typing import List, Dict, Any, Union, Optional
from PIL import Image
import io
import json
from openai import OpenAI
import warnings

from .utils import Timer


class OpenAIVisionDetector:
    """
    Uses OpenAI's GPT-4 Vision API for marketplace item detection.
    Much more accurate than CLIP, especially for brands and conditions.
    """
    
    DEFAULT_CATEGORIES = [
        "electronics",
        "furniture",
        "clothing and accessories",
        "vehicles and automotive",
        "home and garden",
        "sports and recreation",
        "books and media",
        "baby and kids items",
        "tools and hardware",
        "jewelry and watches",
        "musical instruments",
        "art and collectibles",
        "pet supplies",
        "office supplies",
        "health and beauty",
        "toys and games"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        categories: Optional[List[str]] = None
    ):
        """
        Initialize OpenAI Vision detector.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o, gpt-4-turbo, gpt-4o-mini)
            categories: List of categories to detect
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.categories = categories if categories else self.DEFAULT_CATEGORIES
        
        print(f"OpenAI Vision Detector initialized with {self.model}")
    
    def _encode_image(self, image: Image.Image, format: str = "JPEG") -> str:
        """
        Encode PIL Image to base64 string.
        
        Args:
            image: PIL Image
            format: Image format (JPEG, PNG)
            
        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def predict(
        self,
        image_input: Union[str, Image.Image],
        top_k: int = 3,
        return_reasoning: bool = False
    ) -> Dict[str, Any]:
        """
        Predict category for an image using GPT-4 Vision.
        
        Args:
            image_input: Image path or PIL Image
            top_k: Number of top predictions to return
            return_reasoning: Whether to include GPT-4's reasoning
            
        Returns:
            Dictionary with prediction results
        """
        with Timer("OpenAI Vision Category Detection") as timer:
            # Load and encode image
            if isinstance(image_input, str):
                img = Image.open(image_input).convert('RGB')
            else:
                img = image_input
            
            # Resize if too large (OpenAI has limits)
            max_size = 2000
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            image_base64 = self._encode_image(img)
            
            # Create prompt
            categories_str = ", ".join(self.categories)
            
            prompt = f"""Analyze this marketplace item image and classify it into ONE of these categories:

{categories_str}

Also determine if this item is suitable for resale on marketplace platforms.

NOT SUITABLE items include:
• Trash, garbage, or waste
• Perishable food or beverages
• Opened/consumed food items
• Hazardous materials
• Bodily fluids or medical waste
• Extremely damaged/broken items beyond repair
• Items with no resale value
• Contraband or illegal items

Respond in JSON format:
{{
    "category": "the most appropriate category",
    "confidence": 0.95,
    "alternatives": [
        {{"category": "second best match", "confidence": 0.03}},
        {{"category": "third best match", "confidence": 0.02}}
    ],
    "reasoning": "brief explanation of why you chose this category",
    "marketplace_suitable": true or false,
    "suitability_reasoning": "why this is or isn't suitable for marketplace resale"
}}

Be precise and confident in your classification. The confidence should be a number between 0 and 1."""
            
            # Call OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.1  # Low temperature for consistent results
                )
                
                # Parse response
                content = response.content[0].text if hasattr(response, 'content') else response.choices[0].message.content
                
                # Try to extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                # Ensure alternatives list exists
                if 'alternatives' not in result:
                    result['alternatives'] = []
                
                # Convert confidence to float
                result['confidence'] = float(result['confidence'])
                for alt in result['alternatives']:
                    alt['confidence'] = float(alt['confidence'])
                
                result['processing_time_ms'] = timer.elapsed_ms
                
                if not return_reasoning and 'reasoning' in result:
                    reasoning = result.pop('reasoning')
                
                return result
                
            except Exception as e:
                warnings.warn(f"OpenAI API error: {str(e)}")
                # Fallback response
                return {
                    "category": "unknown",
                    "confidence": 0.0,
                    "alternatives": [],
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms,
                    "marketplace_suitable": True,  # Default to suitable on error
                    "suitability_reasoning": "Unable to assess suitability due to API error"
                }


class OpenAIElectronicsDetector:
    """
    Uses GPT-4 Vision for detailed electronics attribute detection.
    Much more accurate than CLIP for brand, model, and condition.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        """
        Initialize OpenAI electronics detector.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        print(f"OpenAI Electronics Detector initialized with {self.model}")
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode image to base64."""
        buffer = io.BytesIO()
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def predict(
        self,
        image_input: Union[str, Image.Image],
        detect_all: bool = True,
        detail_level: str = "normal"
    ) -> Dict[str, Any]:
        """
        Detect electronics attributes using GPT-4 Vision.
        
        Args:
            image_input: Image path or PIL Image
            detect_all: Whether to detect all attributes
            detail_level: "quick", "normal", or "detailed" analysis
            
        Returns:
            Dictionary with detected attributes
        """
        with Timer("OpenAI Electronics Detection") as timer:
            # Load and encode image
            if isinstance(image_input, str):
                img = Image.open(image_input).convert('RGB')
            else:
                img = image_input
            
            # Resize if too large
            max_size = 2000
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            image_base64 = self._encode_image(img)
            
            # Create prompt based on detail level
            if detail_level == "detailed":
                prompt = """Analyze this electronics product image in EXTREME DETAIL for a marketplace listing.

⚠️ CRITICAL PRIORITIES (Most Important):
1. **BRAND IDENTIFICATION** - This is the #1 priority. Look very carefully for:
   
   **GENUINE Brand Indicators (TRUST THESE):**
   - Manufacturer logos embossed/printed on device
   - Brand name on original product casing/body
   - Distinctive brand-specific design language (Apple's style, Samsung's look)
   - Official manufacturer markings
   - Brand text molded into the product
   
   **IGNORE These (NOT the brand):**
   - User-added stickers or decals
   - Aftermarket labels or customizations
   - Store price tags or inventory stickers
   - Personal customization stickers
   - Third-party accessory brands (if it's a phone case brand on a phone, report the PHONE brand)
   
   **Decision Process:**
   - Is this marking part of the original product design? → It's the brand
   - Is this a sticker that could be peeled off? → Ignore it, keep looking
   - Does the design language match a known brand? → Use that brand
   - Example: Headphones with Apple design language but a custom sticker → Brand is Apple (or the actual manufacturer)

2. **PRODUCT TYPE** - This is the #2 priority. Be very specific:
   - Don't just say "phone" - say "smartphone" or "flip phone"
   - Don't just say "computer" - say "laptop", "desktop tower", "all-in-one PC"
   - Don't just say "headphones" - say "over-ear headphones", "wireless earbuds", "gaming headset", "in-ear wired headphones"
   - Be as specific as possible about the exact device type

## PRODUCT-SPECIFIC WEAR DETECTION:

After identifying the product type, look for COMMON WEAR PATTERNS specific to that product:

**For HEADPHONES/EARBUDS:**
- Ear pad condition (cracking, peeling, flattening, discoloration)
- Headband padding wear (worn fabric, exposed foam, cracks)
- Headband hinge looseness or cracks
- Cable condition (fraying, exposed wires, kinks, discoloration)
- Jack/connector damage (bent, corroded, loose)
- Ear cup swivel joints (cracks, looseness)
- Cushion deterioration (synthetic leather peeling, foam exposed)
- Driver grills (dents, debris, damage)
- Adjustment mechanism wear
- Wireless charging case scratches (for earbuds)

**For SMARTPHONES:**
- Screen scratches (hairline, deep, spider cracks)
- Screen protector presence and condition
- Back panel scratches or cracks
- Camera lens scratches or cracks
- Frame dents or dings (corners especially)
- Port wear (Lightning/USB-C damage)
- Button functionality indicators
- Face/Touch ID area condition
- Charging port debris or damage

**For LAPTOPS:**
- Screen bezel cracks or chips
- Keyboard key wear (shiny keys, fading letters)
- Trackpad wear (discoloration, smoothness loss)
- Hinge condition (loose, cracked, stiff)
- Bottom case scratches or dents
- Port damage (USB, HDMI, charging)
- Screen backlight bleed visible
- Rubber feet missing or worn
- Palm rest wear/discoloration

**For TABLETS:**
- Screen condition and scratches
- Bezel chips or cracks
- Back panel dents or scratches
- Smart connector condition
- Camera lens condition
- Volume/power button wear
- Speaker grill damage

**For CAMERAS:**
- Lens scratches or fungus
- Sensor dust visibility
- Body grip rubber peeling
- LCD screen scratches
- Viewfinder condition
- Mount wear (lens mount, hot shoe)
- Battery compartment condition
- Rubber gasket deterioration

**For SMARTWATCHES:**
- Screen scratches (sapphire/glass)
- Band/strap wear (leather cracking, silicone tearing)
- Case scratches or dents
- Crown/button damage
- Sensor area scratches (heart rate)
- Charging connector corrosion

**For GAMING CONSOLES:**
- Controller stick drift indicators
- Button wear (rubber worn off)
- Case scratches or yellowing
- Port damage
- Fan noise/dust indicators
- Disc drive condition

## Complete Analysis Required:

3. **Model Identification**: Look for:
   - Model numbers on stickers or engravings
   - Text on device (e.g., "iPhone 14 Pro", "Galaxy S23")
   - Generation indicators
   - Capacity labels (64GB, 256GB, 512GB, etc.)

4. **Comprehensive Condition Assessment**:
   - Overall grade: NEW/Like New/Excellent/Good/Fair/Poor
   - Use the product-specific wear patterns above
   - Be thorough - check every common failure point for that product type
   - List ALL visible defects with precise locations

5. **Physical Details**:
   - Color/Finish (exact color and material)
   - Storage/Capacity visible on device
   - Accessories shown (cables, cases, boxes, chargers)
   - Serial/model numbers on stickers
   - ALL visible text and labels (excluding user-added stickers)

6. **Technical Features**:
   - Product-specific features (cameras, ports, buttons)
   - Special features relevant to device type

Respond in detailed JSON format:
{{
    "brand": "EXACT brand name from genuine markings - NOT from stickers",
    "brand_confidence": 0.95,
    "brand_reasoning": "How you identified the genuine brand (design, logo, NOT stickers)",
    "stickers_present": ["list any user-added stickers seen - these are NOT the brand"],
    
    "product_type": "SPECIFIC device type - be precise",
    "product_type_confidence": 0.95,
    "product_type_reasoning": "Why you classified it this way",
    
    "model": "specific model with generation",
    "model_confidence": 0.80,
    "storage_capacity": "if visible on device",
    
    "condition": "exact condition category",
    "condition_confidence": 0.85,
    "product_specific_wear": {{
        "category": "headphones/smartphone/laptop/etc",
        "common_wear_items_checked": ["list all the product-specific items you checked"],
        "issues_found": ["specific wear items found from the product-specific list above"]
    }},
    "condition_notes": ["general condition observations"],
    "physical_damage": ["all scratches, dents, marks with precise locations"],
    "missing_parts": ["if any parts appear missing"],
    
    "color": "exact color and finish",
    "color_confidence": 0.95,
    
    "visible_text": ["every piece of text visible on device - excluding stickers"],
    "serial_or_model_numbers": ["if visible on official labels or engravings"],
    "accessories_shown": ["cables, cases, boxes visible"],
    
    "technical_features": {{
        "relevant_to_product_type": ["features specific to this product"]
    }},
    
    "marketplace_value_indicators": {{
        "appears_functional": true/false,
        "cosmetic_grade": "A/B/C/D",
        "product_specific_concerns": ["issues specific to this product type"],
        "likely_issues": ["potential problems based on product-specific inspection"]
    }},
    
    "overall_confidence": 0.88,
    "detailed_analysis": "comprehensive marketplace analysis with product-specific wear assessment"
}}

CRITICAL REMINDERS:
1. IGNORE user stickers when identifying brand - look for genuine manufacturer markings
2. Apply product-specific wear detection - don't use generic inspection for all products
3. Be thorough with the product-specific checklist for that device type"""
            
            elif detail_level == "quick":
                prompt = """Quickly identify this electronics product with EMPHASIS on brand and product type:

🎯 PRIMARY OBJECTIVES:
1. **BRAND** (Most Important) - Look carefully for GENUINE brand indicators:
   - Manufacturer logos/text on the device itself
   - Design language (Apple style, Samsung look, etc.)
   - ⚠️ IGNORE user-added stickers - they are NOT the brand
   
2. **PRODUCT TYPE** (Most Important) - Be specific about exact device type

3. **Quick Condition** - Notable wear/damage

Respond in JSON:
{{
    "brand": "EXACT brand from genuine markings (NOT stickers)",
    "brand_confidence": 0.90,
    "brand_reasoning": "How identified (genuine logo/design, NOT stickers)",
    "stickers_ignored": ["any stickers seen that were ignored"],
    "product_type": "SPECIFIC device type",
    "product_type_confidence": 0.95,
    "model": "model if identifiable",
    "condition": "quick condition",
    "color": "color",
    "overall_confidence": 0.85,
    "reasoning": "Focus on genuine brand ID and specific product type"
}}

CRITICAL: Distinguish between genuine brand markings and user-added stickers!"""
            
            else:  # normal
                prompt = """Analyze this electronics product for a marketplace listing.

🎯 TOP PRIORITIES:
1. **BRAND IDENTIFICATION** - Most important! Look for:
   
   **Trust These (GENUINE brand):**
   - Manufacturer logos embossed or printed on device
   - Brand name on product body/casing
   - Distinctive design language
   - Official manufacturer markings
   
   **Ignore These (NOT the brand):**
   - User stickers or decals
   - Aftermarket labels
   - Store tags
   - Personal customizations
   
2. **PRODUCT TYPE** - Second most important! Be specific:
   - Not just "headphones" → "over-ear wireless headphones", "wireless earbuds", "wired in-ear headphones"
   - Not just "phone" → "smartphone", "flip phone"
   - Not just "laptop" → "laptop computer", "gaming laptop"

3. **PRODUCT-SPECIFIC CONDITION CHECK**:
   
   After identifying product type, check for COMMON WEAR specific to that product:
   
   **Headphones/Earbuds**: Ear pad wear, headband cracks, cable fraying, cushion peeling
   **Smartphones**: Screen scratches, back cracks, frame dents, port wear
   **Laptops**: Keyboard wear, hinge looseness, screen issues, trackpad condition
   **Tablets**: Screen condition, bezel chips, back dents
   **Cameras**: Lens scratches, body grip wear, sensor dust
   
   Use the appropriate checklist for the product type you identified!

4. **Additional Details**:
   - Model (if identifiable)
   - Color and finish
   - Visible text (official labels only)
   - Key features

Respond in JSON format:
{{
    "brand": "EXACT brand name from genuine markings",
    "brand_confidence": 0.90,
    "brand_reasoning": "How identified (genuine indicators, NOT stickers)",
    "stickers_present": ["any user stickers seen - these were ignored"],
    
    "product_type": "SPECIFIC device type",
    "product_type_confidence": 0.95,
    "product_type_reasoning": "Why this specific type",
    
    "model": "model name if identifiable",
    "model_confidence": 0.80,
    
    "condition": "detailed condition",
    "condition_confidence": 0.85,
    "product_specific_wear": {{
        "category": "product type identified",
        "specific_checks_performed": ["what product-specific items were checked"],
        "wear_found": ["specific wear items from product checklist"]
    }},
    "condition_notes": ["visible wear or defects using product-specific inspection"],
    
    "color": "exact color and finish",
    "color_confidence": 0.95,
    
    "visible_details": ["text, numbers on device - excluding user stickers"],
    "features": ["notable technical features"],
    
    "overall_confidence": 0.88,
    "reasoning": "Analysis with genuine brand ID and product-specific wear detection"
}}

REMEMBER: 
1. Ignore user stickers - find the genuine brand
2. Use product-specific wear detection - don't be generic!"""
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1500 if detail_level == "detailed" else 800,
                    temperature=0.1
                )
                
                # Parse response
                content = response.content[0].text if hasattr(response, 'content') else response.choices[0].message.content
                
                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                # Convert confidence scores to float
                for key in result:
                    if key.endswith('_confidence'):
                        result[key] = float(result[key])
                
                result['processing_time_ms'] = timer.elapsed_ms
                result['detail_level_used'] = detail_level
                
                return result
                
            except Exception as e:
                warnings.warn(f"OpenAI API error: {str(e)}")
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "color": "unknown",
                    "overall_confidence": 0.0,
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms
                }
    
    def predict_multi_angle(
        self,
        images: List[Image.Image],
        detect_all: bool = True,
        detail_level: str = "normal"
    ) -> Dict[str, Any]:
        """
        Detect electronics attributes using multiple angles/images.
        Provides more accurate detection by seeing product from different perspectives.
        
        Args:
            images: List of PIL Images (different angles of same product)
            detect_all: Whether to detect all attributes
            detail_level: "quick", "normal", or "detailed" analysis
            
        Returns:
            Dictionary with detected attributes from all angles
        """
        with Timer(f"OpenAI Multi-Angle Detection ({len(images)} images)") as timer:
            # Encode all images
            encoded_images = []
            for img in images:
                # Resize if too large
                if max(img.size) > 2000:
                    img = img.copy()
                    img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                
                encoded_images.append(self._encode_image(img))
            
            # Create enhanced multi-angle prompt
            angle_descriptions = ["front", "back", "side", "top", "bottom", "detail", "angle", "view"]
            angle_labels = [angle_descriptions[i % len(angle_descriptions)] for i in range(len(images))]
            
            if detail_level == "detailed":
                intro = f"""Analyze this electronics product using {len(images)} different images/angles for a marketplace listing.

You have {len(images)} images showing different perspectives of THE SAME PRODUCT. Use ALL images together for the most accurate analysis.

Image references: {', '.join([f'Image {i+1} ({label})' for i, label in enumerate(angle_labels)])}"""
            else:
                intro = f"""Analyze this electronics product using {len(images)} different angles/images.

You have {len(images)} images of the SAME PRODUCT. Combine information from all images for accurate detection."""
            
            # Use the appropriate single-image prompt but with multi-angle context
            if detail_level == "detailed":
                main_prompt = intro + """

⚠️ MULTI-ANGLE ANALYSIS STRATEGY:
- Compare across all images to identify brand/model consistently
- Use best-lit image for text reading
- Use multiple angles to assess overall condition
- Note which image shows each feature best

""" + """⚠️ CRITICAL PRIORITIES (Most Important):
1. **BRAND IDENTIFICATION** - This is the #1 priority. Check ALL images:
   
   **GENUINE Brand Indicators (TRUST THESE):**
   - Manufacturer logos embossed/printed on device (check all angles)
   - Brand name on original product casing/body
   - Distinctive brand-specific design language visible across images
   - Official manufacturer markings
   - Brand text molded into the product
   
   **IGNORE These (NOT the brand):**
   - User-added stickers or decals (often visible in only some angles)
   - Aftermarket labels or customizations
   - Store price tags or inventory stickers
   - Personal customization stickers
   
   **Multi-angle verification:**
   - Does the design language match across all angles? → Use that brand
   - Are stickers only in some images? → They're added, ignore them
   - Is the logo consistent? → It's genuine

2. **PRODUCT TYPE** - Be very specific using clues from all angles

## PRODUCT-SPECIFIC WEAR DETECTION (Check ALL images):

After identifying product type, use multiple angles to find ALL wear:

**For HEADPHONES/EARBUDS:**
- Ear pad condition (check both sides across images)
- Headband padding wear (visible in different angles)
- Cable condition (trace full length across images)
- Jack/connector damage
- Ear cup swivel joints (both sides)
- Cushion deterioration
- Driver grills condition
- Scuff marks (each angle reveals different areas)

**For SMARTPHONES:**
- Screen scratches (front image)
- Back panel condition (back image)
- Frame damage on all edges (multiple angles needed)
- Camera lens condition
- Port wear (bottom angle)
- Button condition (side angles)

**For LAPTOPS:**
- Screen/bezel (open view)
- Keyboard wear (top view)
- Hinge condition (side views)
- Bottom case (bottom view)
- Port damage (side views)

**For OTHER PRODUCTS:**
Apply appropriate product-specific checklist and use all angles to find every defect.

## COMPREHENSIVE MULTI-ANGLE INSPECTION:

Go through each image systematically:
- Image 1: What's visible? What condition indicators?
- Image 2: New angles? New wear patterns visible?
- Image 3+: Complete the condition picture

Combine findings from ALL images for final assessment.

Respond in detailed JSON format:
{{
    "images_analyzed": {len(images)},
    "angle_coverage": "what angles were provided (front/back/side/etc)",
    
    "brand": "EXACT brand from genuine markings across all images",
    "brand_confidence": 0.95,
    "brand_reasoning": "How identified using multiple angles (NOT from stickers)",
    "stickers_present": ["user stickers seen in any image - ignored"],
    
    "product_type": "SPECIFIC device type from all angles",
    "product_type_confidence": 0.98,
    "product_type_reasoning": "Why this type, using clues from multiple angles",
    
    "model": "specific model",
    "model_confidence": 0.85,
    
    "condition": "condition based on ALL angles",
    "condition_confidence": 0.90,
    "product_specific_wear": {{
        "category": "product type",
        "common_wear_items_checked": ["items checked across all angles"],
        "issues_found": ["specific wear from all images combined"],
        "issues_by_angle": {{
            "image_1": ["issues visible in first image"],
            "image_2": ["issues visible in second image"],
            "etc": ["..."]
        }}
    }},
    "condition_notes": ["comprehensive notes from all angles"],
    "physical_damage": ["all damage found across all images with locations"],
    
    "color": "color from best-lit image",
    "color_confidence": 0.95,
    
    "visible_text": ["text from all images combined"],
    "serial_or_model_numbers": ["from any image"],
    "accessories_shown": ["across all images"],
    
    "technical_features": {{
        "visible_across_angles": ["features confirmed from multiple views"]
    }},
    
    "multi_angle_benefits": "what the additional angles revealed",
    "recommended_additional_angles": ["if any critical angles are missing"],
    
    "marketplace_value_indicators": {{
        "appears_functional": true/false,
        "cosmetic_grade": "A/B/C/D from full inspection",
        "product_specific_concerns": ["based on complete multi-angle view"],
        "completeness": "are all important angles shown?"
    }},
    
    "overall_confidence": 0.92,
    "detailed_analysis": "comprehensive analysis using all {len(images)} images"
}}

CRITICAL:
1. Use ALL images together - don't just analyze one
2. Stickers visible in some angles? Ignore them
3. Check product-specific wear across ALL angles
4. Note what each angle contributed to the analysis"""
            
            else:
                # For quick/normal with multiple images, use simplified multi-angle prompt
                intro = f"""Analyze this electronics product using {len(images)} different images of the SAME product.

Use ALL images together for accurate brand, type, and condition assessment."""
                
                main_prompt = intro + """

🎯 PRIORITIES:
1. **BRAND** - Check all images for genuine markings (ignore user stickers)
2. **PRODUCT TYPE** - Be specific, use clues from all angles
3. **CONDITION** - Combine condition info from all angles
4. **PRODUCT-SPECIFIC WEAR** - Check appropriate items for this product type across all images

Respond in JSON:
{{
    "images_analyzed": {len(images)},
    "brand": "genuine brand across all images",
    "brand_confidence": 0.92,
    "brand_reasoning": "how identified from multiple angles",
    "stickers_present": ["any user stickers seen"],
    
    "product_type": "specific type",
    "product_type_confidence": 0.95,
    
    "model": "model if identifiable",
    "condition": "condition from all angles combined",
    "condition_confidence": 0.88,
    
    "product_specific_wear": {{
        "category": "product type",
        "issues_found": ["wear found across all angles"]
    }},
    
    "color": "color",
    "visible_details": ["text/markings from all images"],
    
    "overall_confidence": 0.90,
    "multi_angle_summary": "what the multiple angles revealed"
}}"""
            
            # Build message content with all images
            content = [{"type": "text", "text": main_prompt if detail_level != "detailed" else main_prompt}]
            
            for idx, img_base64 in enumerate(encoded_images):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}",
                        "detail": "high" if detail_level == "detailed" else "auto"
                    }
                })
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    max_tokens=2000 if detail_level == "detailed" else 1000,
                    temperature=0.1
                )
                
                # Parse response
                content_text = response.content[0].text if hasattr(response, 'content') else response.choices[0].message.content
                
                # Extract JSON
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content_text)
                
                # Convert confidence scores to float
                for key in result:
                    if key.endswith('_confidence'):
                        result[key] = float(result[key])
                
                result['processing_time_ms'] = timer.elapsed_ms
                result['detail_level_used'] = detail_level
                result['angles_analyzed'] = len(images)
                
                return result
                
            except Exception as e:
                warnings.warn(f"OpenAI API error: {str(e)}")
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "overall_confidence": 0.0,
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms
                }


# Factory functions
def create_openai_category_detector(
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> OpenAIVisionDetector:
    """Create OpenAI vision category detector."""
    return OpenAIVisionDetector(api_key=api_key, model=model)


def create_openai_electronics_detector(
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> OpenAIElectronicsDetector:
    """Create OpenAI electronics detector."""
    return OpenAIElectronicsDetector(api_key=api_key, model=model)


if __name__ == "__main__":
    print("OpenAI Vision Detector module loaded!")
    print("Set OPENAI_API_KEY environment variable to use this detector.")
