"""
Price Estimator API using OpenAI Responses API with Web Search.
Returns market research appended to the provided analysis JSON.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()

app = FastAPI(title="Price Estimator API", version="1.0.0")


class PriceEstimateRequest(BaseModel):
    analysis: Dict[str, Any] = Field(..., description="Full analysis JSON from /api/analyze")


class PriceEstimateResponse(BaseModel):
    analysis: Dict[str, Any]
    market_research: Dict[str, Any]


def build_query(analysis: Dict[str, Any]) -> str:
    tier2 = analysis.get('tier2') or analysis.get('tier2_detailed_analysis', {})
    brand = tier2.get('brand', 'Unknown')
    product_type = tier2.get('product_type', 'Unknown')
    condition = tier2.get('condition', 'Unknown')
    color = tier2.get('color', 'Unknown')
    material = tier2.get('material', 'Unknown')
    wear_assessment = tier2.get('overall_wear_assessment', '')

    product_description = f"{brand} {product_type}, {color}, {material}, condition: {condition}. {wear_assessment}"

    return f"""Give me a price estimate for this product, based on similar products and the condition of my product:

Product: {product_description}

Return ONLY a clean JSON with:
- recommended_price: single recommended price in USD
- price_range: object with "min" and "max" prices in USD
- existing_listings: array of objects, each containing "title", "url", "price" (in USD), and "marketplace"

Use web search to find similar currently available listings.

##IMPORTANT: Consider the condition of my product before recommending the price."""


def estimate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable not set")

    query = build_query(analysis)
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

    try:
        price_estimate = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from model: {exc}")

    return {
        "timestamp": datetime.now().isoformat(),
        "response_id": response.id,
        "model": response.model,
        "recommended_price": price_estimate["recommended_price"],
        "price_range": price_estimate["price_range"],
        "existing_listings": price_estimate["existing_listings"]
    }


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/estimate", response_model=PriceEstimateResponse)
def estimate(request: PriceEstimateRequest) -> PriceEstimateResponse:
    market_research = estimate_price(request.analysis)
    updated = dict(request.analysis)
    updated["market_research"] = market_research
    return PriceEstimateResponse(analysis=updated, market_research=market_research)


def run_cli(json_path: str) -> None:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as exc:
        print(f"ERROR loading file: {exc}")
        sys.exit(1)

    market_research = estimate_price(data)
    data["market_research"] = market_research

    print("Price estimate complete")
    print(json.dumps(market_research, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli(sys.argv[1])
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")