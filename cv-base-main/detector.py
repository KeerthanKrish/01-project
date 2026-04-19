"""
Marketplace Item Detection Engine
==================================

Standalone detection system for marketplace product analysis.
Can be used independently or integrated into web applications.

Workflow:
1. Marketplace Suitability Check - Filter unsuitable items
2. Tier 1: Category Detection - Identify broad category
3. Tier 2: Detailed Analysis - Specific product, damage, wear
4. Barcode Lookup - Additional product data
5. JSON Output - Comprehensive results

Usage:
    from detector import MarketplaceDetector
    
    detector = MarketplaceDetector()
    result = detector.analyze_images(
        images=["path/to/image.jpg"],
        detail_level="normal"
    )
"""

import os
import base64
import time
import json
import warnings
import requests
from typing import List, Dict, Any, Union, Optional
from PIL import Image
import io
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# UTILITIES
# ============================================================================

class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
    
    def __str__(self):
        return f"{self.name} took {self.elapsed_ms:.2f}ms"


# ============================================================================
# MAIN DETECTOR CLASS
# ============================================================================

class MarketplaceDetector:
    """
    Complete marketplace item detection system.
    
    Features:
    - Marketplace suitability filtering
    - Category detection (Tier 1)
    - Detailed product analysis (Tier 2)
    - General damage inspection
    - Product-specific wear detection
    - Barcode/SKU lookup
    - Comprehensive JSON output
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
        categories: Optional[List[str]] = None,
        output_folder: str = "jsons"
    ):
        """
        Initialize the marketplace detector.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o recommended)
            categories: Custom category list (optional)
            output_folder: Folder to save JSON outputs
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
        self.output_folder = Path(output_folder)
        
        # Folder for optional search payload persistence
        self.search_folder = Path("search_jsons")
        
        print(f"✅ Marketplace Detector initialized with {self.model}")
    
    # ========================================================================
    # MAIN ANALYSIS METHOD
    # ========================================================================
    
    def analyze_images(
        self,
        images: Union[str, List[str], Image.Image, List[Image.Image]],
        detail_level: str = "detailed",
        save_json: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze one or more product images.
        
        Args:
            images: Single image path/PIL Image or list of paths/PIL Images
            detail_level: Always uses "detailed" (most thorough analysis)
            save_json: Whether to save comprehensive JSON output
            
        Returns:
            Dictionary with complete analysis results including:
            - marketplace_suitable: Is item appropriate for resale
            - tier1: Category detection results
            - tier2: Detailed analysis (product, damage, wear)
            - barcode_lookup: Additional product data if barcode found
            - marketplace_listing: Ready-to-use listing data
        """
        # Normalize inputs to list
        if not isinstance(images, list):
            images = [images]
        
        # Load all images
        pil_images = []
        for img in images:
            if isinstance(img, str):
                pil_images.append(Image.open(img))
            else:
                pil_images.append(img)
        
        print(f"📸 Analyzing {len(pil_images)} image(s)...")
        
        # Step 1: Category Detection + Marketplace Suitability
        print("🔍 Step 1: Category detection...")
        tier1_result = self._detect_category(pil_images[0])
        
        detected_category = tier1_result.get('category', 'unknown').lower()
        
        # Check marketplace suitability
        is_suitable = self._check_marketplace_suitability(tier1_result)
        
        if not is_suitable:
            reason = tier1_result.get('suitability_reasoning', 'Unsuitable for resale')
            print(f"⚠️  Item not suitable for marketplace: {reason}")
            
            result = {
                'success': True,
                'marketplace_suitable': False,
                'suitability_reasoning': reason,
                'tier1': tier1_result,
                'tier2': None,
                'barcode_lookup': None,
                'marketplace_listing': None
            }
            
            if save_json:
                json_path, _ = self._save_comprehensive_json(
                    tier1_result, None, 
                    {'images_analyzed': len(pil_images), 'detail_level': detail_level},
                    None
                )
                result['json_saved_path'] = str(json_path)
            
            return result
        
        print(f"✅ Item suitable for marketplace resale")
        
        # Step 2-5: Detailed Analysis (Specific Product + Damage + Wear)
        print(f"🔍 Steps 2-5: Detailed analysis for {detected_category}...")
        if len(pil_images) > 1:
            tier2_result = self._analyze_multi_angle(
                pil_images, detected_category, detail_level
            )
        else:
            tier2_result = self._analyze_single_image(
                pil_images[0], detected_category, detail_level
            )
        
        # Check for errors
        if tier2_result and tier2_result.get('error'):
            print(f"❌ Tier 2 analysis error: {tier2_result['error']}")
        else:
            print(f"✅ Tier 2 analysis completed successfully")
        
        # Step 6: Barcode Lookup
        barcode_info = self._lookup_barcode_from_results(tier2_result)
        
        # Format complete results
        result = {
            'success': True,
            'marketplace_suitable': True,
            'images_analyzed': len(pil_images),
            'tier1': tier1_result,
            'tier2': tier2_result,
            'barcode_lookup': barcode_info,
            'marketplace_listing': self._generate_marketplace_listing(tier1_result, tier2_result)
        }
        
        # Generate search optimization payload (always for suitable items)
        if save_json:
            json_path, timestamp = self._save_comprehensive_json(
                tier1_result, tier2_result,
                {'images_analyzed': len(pil_images), 'detail_level': detail_level},
                barcode_info
            )
            result['json_saved_path'] = str(json_path)
            print(f"📄 Analysis saved: {json_path}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        search_payload = self._generate_search_payload(
            tier1_result, tier2_result, timestamp
        )
        result['search_payload'] = search_payload
        
        if save_json:
            search_json_path = self._save_search_payload(search_payload, timestamp)
            result['search_json_path'] = str(search_json_path)
        
        return result
    
    # ========================================================================
    # TIER 1: CATEGORY DETECTION
    # ========================================================================
    
    def _detect_category(self, image: Image.Image) -> Dict[str, Any]:
        """
        Detect product category and marketplace suitability.
        
        Returns dict with:
        - category: Detected category
        - confidence: Confidence score
        - marketplace_suitable: Is item suitable for resale
        - suitability_reasoning: Why it is/isn't suitable
        """
        with Timer("Tier 1: Category Detection") as timer:
            # Resize if too large
            if max(image.size) > 2000:
                image = image.copy()
                image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            
            image_base64 = self._encode_image(image)
            
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
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON from markdown if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                # Ensure alternatives exist
                if 'alternatives' not in result:
                    result['alternatives'] = []
                
                # Convert confidence to float
                result['confidence'] = float(result['confidence'])
                for alt in result['alternatives']:
                    alt['confidence'] = float(alt['confidence'])
                
                result['processing_time_ms'] = timer.elapsed_ms
                
                return result
                
            except Exception as e:
                warnings.warn(f"Tier 1 error: {str(e)}")
                return {
                    "category": "unknown",
                    "confidence": 0.0,
                    "alternatives": [],
                    "error": str(e),
                    "processing_time_ms": timer.elapsed_ms,
                    "marketplace_suitable": True,
                    "suitability_reasoning": "Unable to assess due to error"
                }
    
    # ========================================================================
    # TIER 2: DETAILED ANALYSIS
    # ========================================================================
    
    def _analyze_single_image(
        self,
        image: Image.Image,
        category: str,
        detail_level: str
    ) -> Dict[str, Any]:
        """
        Tier 2: Analyze single image for:
        - Specific product identification
        - General damage (scratches, dents, scuffs)
        - Product-specific wear (dynamic based on product type)
        """
        with Timer(f"Tier 2: Single Image Analysis ({category})") as timer:
            # Resize if needed
            if max(image.size) > 2000:
                image = image.copy()
                image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            
            encoded_image = self._encode_image(image)
            prompt = self._build_analysis_prompt(category, detail_level, multi_angle=False)
            
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
                error_msg = str(e)
                warnings.warn(f"Tier 2 single-image error: {error_msg}")
                print(f"❌ Tier 2 analysis failed: {error_msg}")
                
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "overall_confidence": 0.0,
                    "error": error_msg,
                    "processing_time_ms": timer.elapsed_ms,
                    "category": category
                }
    
    def _analyze_multi_angle(
        self,
        images: List[Image.Image],
        category: str,
        detail_level: str
    ) -> Dict[str, Any]:
        """
        Tier 2: Analyze multiple images for more comprehensive assessment.
        """
        with Timer(f"Tier 2: Multi-Angle Analysis ({len(images)} images)") as timer:
            # Encode all images
            encoded_images = []
            for img in images:
                if max(img.size) > 2000:
                    img = img.copy()
                    img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                encoded_images.append(self._encode_image(img))
            
            prompt = self._build_analysis_prompt(category, detail_level, multi_angle=True, num_images=len(images))
            
            # Build message with all images
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
                # Dynamic token scaling based on image count
                base_tokens = 3000 if detail_level == "detailed" else 2000
                tokens_per_image = 150
                max_tokens = min(base_tokens + (len(images) * tokens_per_image), 4000)
                
                print(f"🔧 Using {max_tokens} max tokens for {len(images)} images")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=max_tokens,
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
                error_msg = str(e)
                warnings.warn(f"Tier 2 multi-angle error: {error_msg}")
                print(f"❌ Multi-angle analysis failed: {error_msg}")
                print(f"   - Images: {len(images)}, Detail: {detail_level}, Category: {category}")
                
                return {
                    "product_type": "unknown",
                    "brand": "unknown",
                    "condition": "unknown",
                    "overall_confidence": 0.0,
                    "error": error_msg,
                    "processing_time_ms": timer.elapsed_ms,
                    "category": category
                }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 with optimized quality (85 = 25% smaller, visually identical)."""
        buffer = io.BytesIO()
        
        # Convert to RGB if needed
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _check_marketplace_suitability(self, tier1_result: Dict[str, Any]) -> bool:
        """Check if item is suitable for marketplace resale."""
        is_suitable = tier1_result.get('marketplace_suitable')
        
        # Default to True if missing/null
        if is_suitable is None or is_suitable == "" or is_suitable == "null":
            return True
        elif isinstance(is_suitable, str):
            return is_suitable.lower() != "false"
        
        return is_suitable is not False and is_suitable != 0
    
    def _lookup_barcode_from_results(self, tier2_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and lookup barcode from Tier 2 results."""
        if not tier2_result:
            return None
        
        # Try direct barcode field
        barcode_found = tier2_result.get('barcode_sku_found')
        if barcode_found and barcode_found != 'null' and barcode_found != 'None':
            info = self._lookup_barcode(barcode_found)
            if info:
                return info
        
        # Try extracting from visible text
        barcodes = self._extract_barcodes(tier2_result)
        for barcode in barcodes:
            info = self._lookup_barcode(barcode)
            if info:
                return info
        
        return None
    
    def _lookup_barcode(self, barcode_number: str) -> Optional[Dict[str, Any]]:
        """Look up product info using barcode APIs."""
        if not barcode_number or len(barcode_number) < 8:
            return None
        
        barcode_clean = ''.join(c for c in barcode_number if c.isdigit())
        if not barcode_clean:
            return None
        
        print(f"🔍 Looking up barcode: {barcode_clean}")
        
        # Try UPCitemdb.com
        try:
            url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode_clean}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    item = data['items'][0]
                    result = {
                        'found': True,
                        'source': 'UPCitemdb',
                        'barcode': barcode_clean,
                        'title': item.get('title', ''),
                        'brand': item.get('brand', ''),
                        'model': item.get('model', ''),
                        'description': item.get('description', ''),
                        'category': item.get('category', '')
                    }
                    print(f"✅ Barcode found: {result['title']}")
                    return result
        except Exception as e:
            print(f"⚠️ UPCitemdb failed: {e}")
        
        # Try Open Food Facts
        try:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_clean}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1 and data.get('product'):
                    product = data['product']
                    result = {
                        'found': True,
                        'source': 'Open Food Facts',
                        'barcode': barcode_clean,
                        'title': product.get('product_name', ''),
                        'brand': product.get('brands', ''),
                        'category': product.get('categories', '')
                    }
                    print(f"✅ Barcode found: {result['title']}")
                    return result
        except Exception as e:
            print(f"⚠️ Open Food Facts failed: {e}")
        
        print(f"❌ No barcode info found for: {barcode_clean}")
        return None
    
    def _extract_barcodes(self, tier2_result: Dict[str, Any]) -> List[str]:
        """Extract potential barcode numbers from visible text."""
        if not tier2_result:
            return []
        
        barcodes = []
        visible_text = tier2_result.get('visible_text_found', [])
        
        for text in visible_text:
            digits = ''.join(c for c in str(text) if c.isdigit())
            if 8 <= len(digits) <= 14:
                barcodes.append(digits)
        
        # Remove duplicates
        return list(dict.fromkeys(barcodes))
    
    def _generate_search_payload(
        self,
        tier1_result: Dict[str, Any],
        tier2_result: Dict[str, Any],
        analysis_timestamp: str
    ) -> Dict[str, Any]:
        """
        Generate optimized search payload for similarity-search APIs.
        
        Uses OpenAI to transform the full analysis into a compact,
        high-signal search payload optimized for product matching.
        
        Args:
            tier1_result: Tier 1 category detection
            tier2_result: Tier 2 detailed analysis
            analysis_timestamp: Timestamp for linking back to original analysis
            
        Returns:
            Search-optimized payload with primary_query, fallback_query, keywords, filters
        """
        print("🔍 Generating search optimization payload...")
        
        with Timer("Search Payload Generation") as timer:
            # Build input JSON from analysis
            analysis_input = {
                "tier1_category_detection": tier1_result,
                "tier2_detailed_analysis": tier2_result
            }
            
            # Create prompt for search optimization
            prompt = """You are a shopping-search optimizer.

Input: a product-analysis JSON generated from images of one item.
Output: a compact JSON payload for a similarity-search API.

Extract only the attributes that improve retrieval of similar products:
- brand
- normalized product type
- material
- color
- model name if clearly present
- size/dimensions if present
- notable features like RFID, pop-up, low-top, leather

Do not use:
- confidence scores
- image analysis metadata
- reasoning text
- wear-point analysis details
- long descriptive sentences

Build:
1. primary_query: the most precise buyer-style search string
2. fallback_query: a broader version with fewer constraints
3. keywords: 3-8 high-signal terms
4. filters: structured fields when clearly available
5. excluded_fields: important fields you ignored

Guidelines:
- Omit uncertain fields instead of guessing.
- Rewrite technical descriptions into shopper language.
- Include condition only when the goal is used/resale matching.
- Keep queries short and high signal.
- Return valid JSON only.

Input JSON:
""" + json.dumps(analysis_input, indent=2)
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=800,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON from markdown if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                search_payload = json.loads(content)
                search_payload['processing_time_ms'] = timer.elapsed_ms
                search_payload['generated_at'] = datetime.now().isoformat()
                search_payload['source_analysis_id'] = analysis_timestamp
                
                print(f"✅ Search payload generated: {search_payload.get('primary_query', 'N/A')}")
                return search_payload
                
            except Exception as e:
                error_msg = str(e)
                warnings.warn(f"Search payload generation error: {error_msg}")
                print(f"❌ Search payload generation failed: {error_msg}")
                
                # Fallback - basic extraction
                return {
                    "error": error_msg,
                    "primary_query": f"{tier2_result.get('brand', '')} {tier2_result.get('product_type', '')}".strip(),
                    "fallback_query": tier1_result.get('category', 'item'),
                    "keywords": [],
                    "filters": {},
                    "excluded_fields": [],
                    "processing_time_ms": timer.elapsed_ms,
                    "generated_at": datetime.now().isoformat(),
                    "source_analysis_id": analysis_timestamp
                }
    
    def _save_search_payload(self, search_payload: Dict[str, Any], timestamp: str) -> Path:
        """
        Save search payload to search_jsons folder.
        
        Args:
            search_payload: Search optimization payload
            timestamp: Timestamp for filename
            
        Returns:
            Path to saved JSON file
        """
        self.search_folder.mkdir(parents=True, exist_ok=True)
        search_json_path = self.search_folder / f"search_{timestamp}.json"
        
        with open(search_json_path, 'w', encoding='utf-8') as f:
            json.dump(search_payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Search payload saved: {search_json_path}")
        return search_json_path
    
    # ========================================================================
    # PROMPT BUILDING
    # ========================================================================
    
    def _build_analysis_prompt(
        self,
        category: str,
        detail_level: str,
        multi_angle: bool = False,
        num_images: int = 1
    ) -> str:
        """
        Build comprehensive analysis prompt with:
        - Text reading (brand, barcode)
        - Specific product identification
        - General damage inspection
        - Product-specific wear analysis (dynamic)
        """
        if multi_angle:
            intro = f"""You are a PROFESSIONAL MARKETPLACE APPRAISER analyzing this {category} using {num_images} different images.

Use ALL {num_images} images together for the MOST ACCURATE assessment possible.

🔴 STEP 1: READ ALL TEXT FROM ALL IMAGES (INCLUDING BARCODES!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Go through EACH image and read EVERY piece of text:
• Brand names (any angle where it's visible)
• Model numbers or product codes
• **Barcode/UPC/EAN numbers (12-13 digits) - VERY IMPORTANT!**
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

⚠️ USE ALL IMAGES: Each angle may reveal different issues!"""
        else:
            intro = f"""You are a PROFESSIONAL MARKETPLACE APPRAISER analyzing this {category} product.

🔴 STEP 1: TEXT READING (DO THIS FIRST!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
READ EVERY PIECE OF VISIBLE TEXT:
• Brand names (printed, embossed, etched)
• Model numbers or product codes
• **Barcode/SKU/UPC numbers (12-13 digits) - CRITICAL!**
• Size labels, material info, any other text

🔴 STEP 2: IDENTIFY SPECIFIC PRODUCT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Be VERY SPECIFIC: Not just "{category}", but exact product type
Examples: "bifold leather wallet", "32oz insulated water bottle", "reflex telescope"

🔴 STEP 3: DYNAMIC PRODUCT-SPECIFIC WEAR ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW that you know the SPECIFIC product:

A) THINK: "What are the common failure points for THIS product?"
   (e.g., wallet → card slots, fold crease, stitching)
   
B) INSPECT for those specific wear points

C) ALSO check general damage (scratches, dents, scuffs)"""
        
        # JSON format based on detail level
        if detail_level == "detailed":
            json_format = """

RESPOND IN THIS EXACT JSON FORMAT:
{
    "brand": "brand name or 'No visible branding'",
    "brand_confidence": 0.95,
    "brand_source": "where found",
    
    "product_type": "VERY SPECIFIC type",
    "material": "material",
    "color": "color",
    "condition": "Excellent/Good/Fair/Poor",
    
    "visible_text_found": ["ALL text including barcodes"],
    "barcode_sku_found": "12-13 digit barcode or null",
    
    "product_specific_wear_analysis": {
        "product_identified": "specific product",
        "typical_wear_points_for_this_product": ["what typically wears"],
        "inspection_results": [
            {
                "wear_point": "specific part",
                "status": "excellent/good/fair/poor",
                "details": "observations",
                "severity": "none/minor/moderate/severe",
                "affects_function": true/false
            }
        ],
        "summary": "overall product-specific wear assessment"
    },
    
    "general_physical_damage": {
        "scratches": ["location and severity"],
        "dents": ["location and severity"],
        "scuffs": ["location and severity"],
        "discoloration": ["location and severity"],
        "cracks_or_chips": ["location and severity"],
        "other_damage": ["other wear"]
    },
    
    "overall_wear_assessment": "comprehensive condition description",
    
    "functionality_assessment": {
        "appears_functional": true/false,
        "confidence": 0.85,
        "reasoning": "why",
        "concerns": ["any concerns"]
    },
    
    "marketplace_assessment": {
        "completeness": "complete/missing parts",
        "cleanliness": "very clean/clean/needs cleaning",
        "cosmetic_grade": "A/B/C/D",
        "major_concerns": ["issues"],
        "selling_points": ["positives"]
    },
    
    "overall_confidence": 0.90,
    "detailed_notes": "summary"
}

CRITICAL: 
1. READ ALL TEXT FIRST
2. Identify SPECIFIC product
3. THINK what wears on THAT product
4. CHECK for those issues
5. Document EVERYTHING"""
        else:
            json_format = """

RESPOND IN JSON:
{
    "brand": "brand or 'No visible branding'",
    "brand_confidence": 0.90,
    "product_type": "SPECIFIC product",
    "material": "material",
    "color": "color",
    "condition": "Excellent/Good/Fair/Poor",
    
    "visible_text_found": ["all text including barcodes"],
    "barcode_sku_found": "barcode number or null",
    
    "product_specific_wear_analysis": {
        "product_identified": "specific product",
        "typical_wear_points": ["what typically wears"],
        "inspection_results": [
            {"wear_point": "part", "status": "condition", "details": "observations"}
        ]
    },
    
    "general_physical_damage": [
        "list ALL damage with locations"
    ],
    
    "functionality_assessment": {
        "appears_functional": true/false,
        "concerns": ["any concerns"]
    },
    
    "marketplace_assessment": {
        "cosmetic_grade": "A/B/C/D",
        "major_concerns": ["issues"],
        "selling_points": ["positives"]
    },
    
    "overall_confidence": 0.88
}

CRITICAL: Identify SPECIFIC product, think what wears on it, check those points + general damage!"""
        
        return intro + json_format
    
    # ========================================================================
    # OUTPUT FORMATTING
    # ========================================================================
    
    def _generate_marketplace_listing(
        self,
        tier1_result: Dict[str, Any],
        tier2_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate ready-to-use marketplace listing data."""
        if not tier2_result:
            return {
                "title": "Item for Sale",
                "description": f"Category: {tier1_result.get('category', 'Unknown')}",
                "condition": "Unknown",
                "selling_points": [],
                "buyer_concerns": []
            }
        
        # Title
        brand = tier2_result.get('brand', '')
        product_type = tier2_result.get('product_type', 'item')
        condition = tier2_result.get('condition', '')
        
        title_parts = []
        if brand and brand != 'No visible branding':
            title_parts.append(brand)
        title_parts.append(product_type.title())
        if condition:
            title_parts.append(f"({condition} Condition)")
        
        title = ' '.join(title_parts)
        
        # Description
        description_parts = []
        
        # Product info
        description_parts.append(f"This is a {brand} {product_type}.")
        
        material = tier2_result.get('material', '')
        color = tier2_result.get('color', '')
        if material or color:
            specs = []
            if material: specs.append(f"made of {material}")
            if color: specs.append(f"in {color}")
            description_parts.append(f"It is {', '.join(specs)}.")
        
        # Condition
        overall_wear = tier2_result.get('overall_wear_assessment', '')
        if overall_wear:
            description_parts.append(f"Condition: {condition}. {overall_wear}")
        
        description = ' '.join(description_parts)
        
        # Selling points
        selling_points = []
        ma = tier2_result.get('marketplace_assessment', {})
        if isinstance(ma, dict) and ma.get('selling_points'):
            selling_points = ma['selling_points'] if isinstance(ma['selling_points'], list) else []
        
        # Concerns
        concerns = []
        if isinstance(ma, dict) and ma.get('major_concerns'):
            concerns = ma['major_concerns'] if isinstance(ma['major_concerns'], list) else []
        
        return {
            "title": title,
            "description": description,
            "condition": condition,
            "grade": ma.get('cosmetic_grade', '') if isinstance(ma, dict) else '',
            "selling_points": selling_points,
            "buyer_concerns": concerns
        }
    
    def _save_comprehensive_json(
        self,
        tier1_result: Dict[str, Any],
        tier2_result: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
        barcode_info: Optional[Dict[str, Any]]
    ) -> tuple[Path, str]:
        """Save comprehensive JSON with all analysis details. Returns (path, timestamp)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder.mkdir(parents=True, exist_ok=True)
        json_path = self.output_folder / f"analysis_{timestamp}.json"
        
        output = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis_id": timestamp,
                "images_analyzed": metadata.get('images_analyzed', 1),
                "detail_level": metadata.get('detail_level', 'normal')
            },
            "tier1_category_detection": tier1_result,
            "tier2_detailed_analysis": tier2_result if tier2_result else {},
            "barcode_lookup": barcode_info if barcode_info else {"found": False},
            "marketplace_listing": self._generate_marketplace_listing(tier1_result, tier2_result)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return json_path, timestamp


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def analyze_product(
    images: Union[str, List[str]],
    api_key: Optional[str] = None,
    detail_level: str = "detailed",
    save_json: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for quick product analysis.
    
    Args:
        images: Single image path or list of image paths
        api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        detail_level: Always uses "detailed" (most thorough analysis)
        save_json: Whether to save JSON output
        
    Returns:
        Complete analysis results
        
    Example:
        result = analyze_product("product.jpg")
        print(result['tier2']['brand'])
        print(result['marketplace_listing']['title'])
    """
    detector = MarketplaceDetector(api_key=api_key)
    return detector.analyze_images(images, detail_level=detail_level, save_json=save_json)


# ============================================================================
# STANDALONE DEMO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("MARKETPLACE DETECTOR - Standalone Demo")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\nUsage: python detector.py <image_path> [image_path2 ...]")
        print("\nExample:")
        print("  python detector.py product.jpg")
        print("  python detector.py img1.jpg img2.jpg img3.jpg")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    
    print(f"\nAnalyzing {len(image_paths)} image(s)...")
    result = analyze_product(image_paths, detail_level="detailed", save_json=False)
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    if not result['marketplace_suitable']:
        print(f"\n⚠️  NOT SUITABLE FOR MARKETPLACE")
        print(f"Reason: {result['suitability_reasoning']}")
    else:
        print(f"\n📦 Category: {result['tier1']['category']}")
        
        if result['tier2']:
            print(f"🏷️  Brand: {result['tier2'].get('brand', 'Unknown')}")
            print(f"📝 Product: {result['tier2'].get('product_type', 'Unknown')}")
            print(f"⭐ Condition: {result['tier2'].get('condition', 'Unknown')}")
            
            listing = result['marketplace_listing']
            print(f"\n📋 Suggested Title: {listing['title']}")
            print(f"📄 Description: {listing['description']}")
        
        if result.get('json_saved_path'):
            print(f"\n💾 Full analysis saved to: {result['json_saved_path']}")
    
    print("\n" + "="*70)
