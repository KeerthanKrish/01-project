"""
Simple Price Estimator using OpenAI Responses API with Web Search
Appends market research data to product analysis JSON
"""

import json
import os
import sys
from datetime import datetime
from openai import OpenAI


def main():
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Get JSON file path
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = r"C:\Users\tarak\Documents\projects\o1_project\price_estimator_gpt\01-project\jsons\analysis_20260418_173528.json"
    
    # Load JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded: {json_path}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Build query from product data
    tier2 = data.get('tier2_detailed_analysis', {})
    brand = tier2.get('brand', 'Unknown')
    product_type = tier2.get('product_type', 'Unknown')
    condition = tier2.get('condition', 'Unknown')
    color = tier2.get('color', 'Unknown')
    material = tier2.get('material', 'Unknown')
    wear_assessment = tier2.get('overall_wear_assessment', '')
    
    # Build product description for the query
    product_description = f"{brand} {product_type}, {color}, {material}, condition: {condition}. {wear_assessment}"
    
    query = f"""Give me a price estimate for this product, based on similar products and the condition of my product:

Product: {product_description}

Return ONLY a clean JSON with:
- recommended_price: single recommended price in USD
- price_range: object with "min" and "max" prices in USD
- existing_listings: array of objects, each containing "title", "url", "price" (in USD), and "marketplace"

Use web search to find similar currently available listings.

##IMPORTANT: Consider the condition of my product before recommending the price."""
    
    print(f"Searching for: {brand} {product_type}")
    
    # Call OpenAI with web search and structured output
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.responses.create(
            model="gpt-4o",
            input=query,
            tools=[{"type": "web_search"}],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "price_estimate",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "recommended_price": {"type": "number"},
                            "price_range": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"}
                                },
                                "required": ["min", "max"],
                                "additionalProperties": False
                            },
                            "existing_listings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "url": {"type": "string"},
                                        "price": {"type": "number"},
                                        "marketplace": {"type": "string"}
                                    },
                                    "required": ["title", "url", "price", "marketplace"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["recommended_price", "price_range", "existing_listings"],
                        "additionalProperties": False
                    }
                }
            },
            store=True
        )
        
        print("Search complete!")
        
        # Parse the JSON response
        price_estimate = json.loads(response.output_text)
        
        # Append to JSON
        data['market_research'] = {
            "timestamp": datetime.now().isoformat(),
            "response_id": response.id,
            "model": response.model,
            "recommended_price": price_estimate["recommended_price"],
            "price_range": price_estimate["price_range"],
            "existing_listings": price_estimate["existing_listings"]
        }
        
        # Create new file path in json_with_prices folder
        file_name = os.path.basename(json_path)
        base_name = os.path.splitext(file_name)[0]
        output_dir = r"C:\Users\tarak\Documents\projects\o1_project\price_estimator_gpt\01-project\json_with_prices"
        new_json_path = os.path.join(output_dir, f"{base_name}_with_prices.json")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to new file
        with open(new_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Success! Created new file: {new_json_path}")
        print(f"\nPrice Estimate:")
        print(f"  Recommended: ${price_estimate['recommended_price']}")
        print(f"  Range: ${price_estimate['price_range']['min']} - ${price_estimate['price_range']['max']}")
        print(f"  Found {len(price_estimate['existing_listings'])} listings")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
