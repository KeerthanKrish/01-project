"""
Universal Detailed Detector using OpenAI Vision API.
Provides comprehensive analysis for ALL marketplace categories.
"""

import os
import base64
from typing import List, Dict, Any, Union
from PIL import Image
import io
import json
import warnings

from openai import OpenAI
from src.utils import Timer


class UniversalDetailedDetector:
    """
    Universal detector that provides detailed analysis for ANY category.
    Adapts its analysis based on the detected category type.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize the universal detector.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64."""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def predict(
        self,
        image_input: Union[str, Image.Image],
        category: str = "unknown",
        detect_all: bool = True,
        detail_level: str = "normal"
    ) -> Dict[str, Any]:
        """
        Analyze any product type with comprehensive detail.
        
        Args:
            image_input: Path to image or PIL Image
            category: Product category (electronics, furniture, clothing, accessories, etc.)
            detect_all: Whether to perform comprehensive analysis
            detail_level: "quick", "normal", or "detailed"
            
        Returns:
            Dictionary with comprehensive product attributes
        """
        with Timer(f"Universal Detection ({category})") as timer:
            # Load image
            if isinstance(image_input, str):
                image = Image.open(image_input)
            else:
                image = image_input
            
            # Resize if too large
            if max(image.size) > 2000:
                image = image.copy()
                image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            
            encoded_image = self._encode_image(image)
            
            # Build category-specific prompt
            prompt = self._build_category_prompt(category, detail_level)
            
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
                                        "url": f"data:image/jpeg;base64,{encoded_image}",
                                        "detail": "high" if detail_level == "detailed" else "auto"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000 if detail_level == "detailed" else 1000,
                    temperature=0.1
                )
                
                # Parse response
                content_text = response.choices[0].message.content
                
                # Extract JSON
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content_text)
                
                # Convert confidence scores
                for key in result:
                    if key.endswith('_confidence'):
                        result[key] = float(result[key])
                
                result['processing_time_ms'] = timer.elapsed_ms
                result['detail_level_used'] = detail_level
                result['category'] = category
                
                return result
                
            except Exception as e:
                warnings.warn(f"OpenAI API error: {str(e)}")
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "overall_confidence": 0.0,
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms,
                    "category": category
                }
    
    def _build_category_prompt(self, category: str, detail_level: str) -> str:
        """Build category-specific analysis prompt with dynamic product-specific wear detection."""
        
        if detail_level == "detailed":
            prompt = f"""You are a PROFESSIONAL MARKETPLACE APPRAISER analyzing this {category} product for sale.

🔴 MANDATORY STEP 1: TEXT READING (DO THIS FIRST!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
READ EVERY PIECE OF VISIBLE TEXT on this product:
• Brand names (printed, embossed, etched, labeled)
• Model numbers or product codes
• Size labels or measurements
• Material descriptions
• Warning labels
• Any other text or numbers

THEN for each piece of text found:
1. Is it a brand name? → Use as brand identification
2. Is it a model/product name? → Use for specific product type
3. Is it a size/spec? → Include in details
4. Is it care instructions? → Note the material info

⚠️ CRITICAL: Text-based identification is MORE RELIABLE than visual guessing.
If you see "Stanley", "Hydro Flask", "YETI", etc. → That's the brand!

🔴 MANDATORY STEP 2: BRAND & PRODUCT IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After reading all text:
✓ Brand: Did you find a brand name in the text? → Use it with HIGH confidence
✓ Product Type: Be VERY SPECIFIC (e.g., "32oz insulated water bottle" not "bottle")
✓ No text but see a logo? → Describe and identify it
✓ Absolutely nothing? → State "No visible branding"

IGNORE: User-added stickers, price tags, inventory labels

🔴 MANDATORY STEP 3: DYNAMIC PRODUCT-SPECIFIC WEAR ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW that you know the SPECIFIC product (e.g., "water bottle", "wallet", "telescope"):

A) THINK: "What are the common failure points and wear patterns for THIS specific product?"

   Examples:
   • Water bottle → lid seal degradation, dent affecting vacuum seal, coating chips, threads stripped
   • Wallet → card slot stretching, fold crease cracking, snap wear, stitching separation at stress points
   • Telescope → lens scratches, focus mechanism stiffness, tripod mount wear, coating deterioration, mirror tarnish
   • Backpack → zipper teeth damage, strap attachment fraying, bottom panel wear, buckle cracks
   • Headphones → ear pad deterioration, headband cracks, cable fraying at strain relief, driver rattling
   • Glasses → nose pad wear, hinge looseness, arm temple tips degradation, lens coating scratches

B) CREATE a mental checklist of these PRODUCT-SPECIFIC wear items

C) INSPECT the product for EACH item on your checklist

D) ALSO check for general damage (scratches, dents, scuffs, discoloration, cracks)

⚠️ CRITICAL: This is a TWO-PART inspection:
   1. Product-specific failure points (what typically breaks on THIS item)
   2. General physical damage (scratches, dents, etc.)

🔴 MANDATORY STEP 4: THOROUGH DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For EACH issue found, document:
✓ What: Type of damage/wear
✓ Where: Exact location
✓ How bad: Severity (minor/moderate/severe)
✓ Impact: Does it affect functionality?

⚠️ Even if product looks "good", there are ALWAYS minor imperfections.
Look harder! Check edges, corners, high-touch areas, moving parts, seals, joints.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPOND IN THIS EXACT JSON FORMAT (FILL EVERY FIELD):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
    "brand": "BRAND NAME from text/logo (or 'No visible branding' if truly none)",
    "brand_confidence": 0.95,
    "brand_source": "where you found it (e.g., 'printed on front', 'embossed logo', 'no branding visible')",
    "stickers_present": ["any user stickers seen"],
    
    "product_type": "VERY SPECIFIC type (e.g., '32oz insulated stainless steel water bottle' not just 'water bottle')",
    "product_type_confidence": 0.90,
    
    "material": "primary material(s) - be specific",
    "color": "specific color(s)",
    "size_or_dimensions": "size info if visible",
    
    "condition": "overall condition (Excellent/Good/Fair/Poor)",
    "condition_confidence": 0.88,
    
    "visible_text_found": [
        "List EVERY piece of text you can read",
        "Include brand names, model numbers, size labels",
        "Even partial text or numbers"
    ],
    
    "product_specific_wear_analysis": {{
        "product_identified": "specific product name",
        "typical_wear_points_for_this_product": [
            "List what TYPICALLY wears/breaks on this specific product",
            "Think about how this product is used",
            "What parts get stressed? What degrades over time?",
            "Example: For wallet - card slots, fold crease, stitching",
            "Example: For telescope - lens scratches, focus mechanism, mount threads"
        ],
        "inspection_results": [
            {{
                "wear_point": "specific part/area checked (e.g., 'lid seal', 'card slots', 'focus knob')",
                "status": "excellent/good/fair/poor/not_visible",
                "details": "what you observed",
                "severity": "none/minor/moderate/severe",
                "affects_function": true/false
            }}
        ],
        "summary": "Overall assessment of product-specific wear"
    }},
    
    "general_physical_damage": {{
        "scratches": ["location and severity of ANY scratches - be thorough"],
        "dents": ["location and severity of ANY dents"],
        "scuffs": ["location and severity of ANY scuffs"],
        "discoloration": ["location and severity of ANY discoloration"],
        "cracks_or_chips": ["location and severity of ANY cracks/chips"],
        "other_damage": ["any other wear or damage"]
    }},
    
    "overall_wear_assessment": "Comprehensive description combining product-specific wear and general damage. What makes it used vs new?",
    
    "functionality_assessment": {{
        "appears_functional": true/false,
        "confidence": 0.85,
        "reasoning": "why you think it works or doesn't work",
        "concerns": ["any functionality concerns based on visible wear"]
    }},
    
    "marketplace_assessment": {{
        "completeness": "complete/missing parts/accessories",
        "cleanliness": "very clean/clean/needs cleaning/dirty",
        "cosmetic_grade": "A (like new) / B (good) / C (fair) / D (poor)",
        "major_concerns": ["significant issues buyers should know"],
        "selling_points": ["positive features for listing"]
    }},
    
    "overall_confidence": 0.90,
    "detailed_notes": "2-3 sentences summarizing condition, product-specific issues, and marketplace viability"
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CRITICAL REMINDERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. READ ALL TEXT FIRST - text = brand identification
2. Identify SPECIFIC product (not generic)
3. THINK about what typically wears on THIS product
4. CHECK for those product-specific wear points
5. ALSO check for general damage
6. Document EVERY flaw found
7. Fill EVERY field (no empty arrays)
8. Be SPECIFIC in all descriptions"""

        else:  # quick or normal
            prompt = f"""PROFESSIONAL {category.upper()} APPRAISAL - PRODUCT-SPECIFIC ANALYSIS

STEP 1 - READ ALL TEXT:
Look for brand names, model numbers, size labels, any text on the product.
Text = most reliable way to identify brand!

STEP 2 - IDENTIFY SPECIFIC PRODUCT:
Not just "{category}" - what EXACT product is this?
(e.g., "32oz insulated water bottle", "bifold leather wallet", "backpacking tent")

STEP 3 - DYNAMIC WEAR ANALYSIS:
Think: "What typically wears/breaks on THIS specific product?"
Then inspect for those specific issues PLUS general damage.

Examples:
• Water bottle → lid seal, coating chips, vacuum seal integrity
• Wallet → card slots, fold crease, stitching at corners
• Backpack → zippers, strap attachments, bottom wear
• Camera → lens condition, shutter mechanism, battery door

RESPOND IN JSON:
{{
    "brand": "brand from text/logo or 'No visible branding'",
    "brand_confidence": 0.90,
    "brand_source": "where found",
    
    "product_type": "SPECIFIC product (not generic)",
    "material": "material",
    "color": "color",
    
    "condition": "Excellent/Good/Fair/Poor",
    
    "visible_text_found": ["list ALL visible text"],
    
    "product_specific_wear_analysis": {{
        "product_identified": "specific product",
        "typical_wear_points": ["what typically wears on this product"],
        "inspection_results": [
            {{"wear_point": "part checked", "status": "condition", "details": "observations"}}
        ]
    }},
    
    "general_physical_damage": [
        "scratch on left side (minor)",
        "scuff on bottom (moderate)",
        "etc - list EVERY flaw"
    ],
    
    "functionality_assessment": {{
        "appears_functional": true/false,
        "concerns": ["any concerns"]
    }},
    
    "marketplace_assessment": {{
        "cosmetic_grade": "A/B/C/D",
        "major_concerns": ["issues"],
        "selling_points": ["positives"]
    }},
    
    "overall_confidence": 0.88
}}

CRITICAL: 
1. Identify SPECIFIC product
2. Think what wears on THAT product
3. Check for those specific issues
4. Also check general damage
5. Fill all fields!"""
        
        return prompt
    
    def predict_multi_angle(
        self,
        images: List[Image.Image],
        category: str = "unknown",
        detect_all: bool = True,
        detail_level: str = "normal"
    ) -> Dict[str, Any]:
        """
        Analyze product using multiple angles/images.
        
        Args:
            images: List of PIL Images (different angles)
            category: Product category
            detect_all: Whether to perform comprehensive analysis
            detail_level: "quick", "normal", or "detailed"
            
        Returns:
            Dictionary with comprehensive analysis from all angles
        """
        with Timer(f"Multi-Angle Universal Detection ({len(images)} images)") as timer:
            # Encode all images
            encoded_images = []
            for img in images:
                if max(img.size) > 2000:
                    img = img.copy()
                    img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                encoded_images.append(self._encode_image(img))
            
            # Build multi-angle prompt
            prompt = self._build_multi_angle_prompt(category, len(images), detail_level)
            
            # Build message content with all images
            content = [{"type": "text", "text": prompt}]
            for img_base64 in encoded_images:
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
                    messages=[{"role": "user", "content": content}],
                    max_tokens=2000 if detail_level == "detailed" else 1000,
                    temperature=0.1
                )
                
                content_text = response.choices[0].message.content
                
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content_text)
                
                for key in result:
                    if key.endswith('_confidence'):
                        result[key] = float(result[key])
                
                result['processing_time_ms'] = timer.elapsed_ms
                result['detail_level_used'] = detail_level
                result['angles_analyzed'] = len(images)
                result['category'] = category
                
                return result
                
            except Exception as e:
                warnings.warn(f"OpenAI API error: {str(e)}")
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "overall_confidence": 0.0,
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms,
                    "category": category
                }
    
    def _build_multi_angle_prompt(self, category: str, num_images: int, detail_level: str) -> str:
        """Build multi-angle analysis prompt with dynamic product-specific wear detection."""
        
        intro = f"""You are a PROFESSIONAL MARKETPLACE APPRAISER analyzing this {category} using {num_images} different images.

Use ALL {num_images} images together for the MOST ACCURATE assessment possible."""
        
        base_instructions = """

🔴 STEP 1: READ ALL TEXT FROM ALL IMAGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Go through EACH image and read EVERY piece of text:
• Brand names (any angle where it's visible)
• Model numbers or product codes
• Size labels
• Material descriptions
• Any other text

Compare text across images to confirm brand!

🔴 STEP 2: IDENTIFY SPECIFIC PRODUCT & BRAND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Is brand visible in multiple angles? → HIGH confidence
• Brand only in one image? → Note which image
• Use best-lit image for reading text
• Be VERY SPECIFIC about product type

🔴 STEP 3: DYNAMIC PRODUCT-SPECIFIC WEAR (Multi-Angle)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Now that you know the SPECIFIC product:

A) THINK: "What typically wears/breaks on THIS specific product?"
   
B) CHECK for those specific wear points across ALL angles:
   • Image 1: Can I see [specific wear point]? What's its condition?
   • Image 2: New angle shows [different wear point]?
   • Image 3+: Complete the inspection

C) ALSO check general damage from all angles:
   • Scratches visible in each image?
   • Dents from different perspectives?
   • Discoloration seen in any angle?

⚠️ USE ALL IMAGES: Each angle may reveal different issues!

"""
        
        if detail_level == "detailed":
            prompt = intro + base_instructions + f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPOND IN THIS JSON FORMAT (FILL EVERY FIELD):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
    "images_analyzed": {num_images},
    "angle_coverage": "describe what angles/views were provided",
    
    "brand": "BRAND NAME from text/logo across all images",
    "brand_confidence": 0.95,
    "brand_source": "which image(s) showed the brand and how",
    "stickers_present": ["user stickers from any image"],
    
    "product_type": "VERY SPECIFIC type",
    "product_type_confidence": 0.92,
    
    "material": "material",
    "color": "color",
    "size_or_dimensions": "size",
    
    "condition": "Excellent/Good/Fair/Poor",
    "condition_confidence": 0.90,
    
    "visible_text_found": [
        "ALL text from ALL images",
        "Note which image each text came from if helpful"
    ],
    
    "product_specific_wear_analysis": {{
        "product_identified": "specific product name",
        "typical_wear_points_for_this_product": [
            "List what TYPICALLY wears/breaks on this specific product",
            "Consider how this product is used",
            "What parts get stressed? What degrades over time?"
        ],
        "inspection_results_by_angle": [
            {{
                "wear_point": "specific part checked (e.g., 'lid seal', 'zipper')",
                "visible_in_images": [1, 2, 3],
                "status": "excellent/good/fair/poor",
                "details": "observations from all relevant angles",
                "severity": "none/minor/moderate/severe",
                "affects_function": true/false
            }}
        ],
        "multi_angle_benefits": "What did multiple angles reveal about product-specific wear?",
        "summary": "Overall assessment of product-specific wear using all angles"
    }},
    
    "general_physical_damage_by_angle": {{
        "image_1": ["damage visible in first image"],
        "image_2": ["damage visible in second image"],
        "image_3": ["damage visible in third image (if applicable)"],
        "combined_summary": ["ALL damage found across ALL angles with locations"]
    }},
    
    "overall_wear_assessment": "Complete condition description using all angles, combining product-specific and general damage",
    
    "functionality_assessment": {{
        "appears_functional": true/false,
        "confidence": 0.85,
        "reasoning": "why functional or not, based on visible wear from all angles",
        "concerns": ["any functionality concerns"]
    }},
    
    "recommended_additional_angles": ["if any critical views are missing for complete product-specific inspection"],
    
    "marketplace_assessment": {{
        "completeness": "complete/missing parts",
        "cleanliness": "rating",
        "cosmetic_grade": "A/B/C/D",
        "major_concerns": ["issues from all angles"],
        "selling_points": ["positives from all angles"]
    }},
    
    "overall_confidence": 0.92,
    "detailed_notes": "Comprehensive assessment using all {num_images} angles, focusing on product-specific wear and general condition"
}}

CRITICAL: 
1. Use ALL images for complete picture
2. Think about THIS product's typical wear points
3. Check for those specific issues across all angles
4. Document EVERY piece of text and EVERY flaw from ANY angle!"""
        
        else:  # normal or quick
            prompt = intro + """

🎯 QUICK MULTI-ANGLE CHECKLIST:
1. Read text from ALL images → Find brand
2. Identify SPECIFIC product (not generic)
3. Think: "What wears on THIS product?"
4. Inspect ALL angles for those specific wear points
5. Also check general damage from all angles
6. Combine findings → Complete assessment

RESPOND IN JSON:
{{
    "images_analyzed": """ + str(num_images) + """,
    "angle_coverage": "angles shown",
    
    "brand": "brand from text/logo",
    "brand_confidence": 0.90,
    "brand_source": "which image",
    
    "product_type": "SPECIFIC product type",
    "material": "material",
    "color": "color",
    
    "condition": "Excellent/Good/Fair/Poor",
    
    "visible_text_found": ["text from all images"],
    
    "product_specific_wear_analysis": {{
        "product_identified": "specific product",
        "typical_wear_points": ["what typically wears on this product"],
        "inspection_results": [
            {{"wear_point": "part", "status": "condition", "visible_in_images": [1,2]}}
        ]
    }},
    
    "general_physical_damage": [
        "damage from image 1",
        "damage from image 2",
        "etc - list ALL damage from ALL angles"
    ],
    
    "multi_angle_benefits": "what extra angles revealed",
    
    "functionality_assessment": {{
        "appears_functional": true/false,
        "concerns": ["any concerns"]
    }},
    
    "marketplace_assessment": {{
        "cosmetic_grade": "A/B/C/D",
        "major_concerns": ["issues"],
        "selling_points": ["positives"]
    }},
    
    "overall_confidence": 0.88
}}

CRITICAL: 
1. Identify SPECIFIC product
2. Think what wears on THAT product
3. Check for those issues in all angles
4. Document everything!"""
        
        return prompt
