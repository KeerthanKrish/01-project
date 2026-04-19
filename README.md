# 01-project Monorepo Overview

This repository is now a multi-service marketplace intelligence stack. It analyzes product photos, generates listing-ready metadata, estimates prices from live web listings, stores results in Convex, and exposes marketplace actions through an MCP server.

## What This Codebase Does

At a high level, the system supports this flow:

1. Analyze one or more product images with OpenAI Vision.
2. Produce structured output (category, product details, condition, listing text, search payload).
3. Optionally estimate a recommended price using web search.
4. Persist analysis and pricing data to Convex via HTTP actions.
5. Publish/search/buy marketplace listings through Convex and MCP tools.

## Repository Structure

- `cv-base-main`  
  Main product analysis service (Flask UI + FastAPI + core detector).
- `price-estimator`  
  Price estimation API/CLI that enriches analysis JSON with market research.
- `Convex-main`  
  Backend data model and APIs for analyses, estimates, and listings.
- `mcp-server-main`  
  FastMCP server exposing marketplace tools (`find_products`, `get_payment_link`, `finalize_purchase`).
- `num-object-detector-main`  
  Separate lightweight detector focused on one binary rule: "exactly one object present".
- `fastapi-endpoints.md`, `fastapi-endpoints-details.md`  
  Short endpoint notes.

## Service-by-Service Breakdown

### 1) `cv-base-main` (Core Analysis)

Primary purpose: generate rich listing intelligence from images.

Key components:
- `detector.py`: `MarketplaceDetector` class with OpenAI vision prompts.
- `app.py`: Flask web UI for webcam/upload workflows.
- `api.py`: FastAPI endpoint for programmatic image analysis.

Main API:
- `POST /api/analyze` (port `8001` by default)
- `GET /api/health`

Output shape includes:
- `marketplace_suitable`
- `tier1` category detection
- `tier2` detailed product and condition analysis
- `barcode_lookup`
- `listing` (listing-ready content)
- `search` (search-optimized payload)

Convex integration:
- If `CONVEX_HTTP_URL` is set, analysis is posted to Convex `/api/save-analysis`.

### 2) `price-estimator` (Market Pricing)

Primary purpose: append market-based pricing to an existing analysis payload.

Key file:
- `price_estimator.py`

Main API:
- `POST /estimate` (port `8002`)
- `GET /health`

Behavior:
- Builds a pricing prompt from `analysis.tier2`.
- Uses OpenAI Responses API + `web_search` tool.
- Returns strict JSON with:
  - `recommended_price`
  - `price_range` (`min`, `max`)
  - `existing_listings` (title, URL, price, marketplace)
- Optionally posts to Convex `/api/save-price-estimate` when `CONVEX_HTTP_URL` is configured.

CLI mode:
- `python price_estimator.py <analysis.json>`

### 3) `Convex-main` (Persistence + Marketplace Backend)

Primary purpose: store analysis/price records and power listing/purchase workflow.

Schema (`convex/schema.ts`) includes tables:
- `analyses`
- `priceEstimates`
- `users` (sellers)
- `buyers`
- `listings`

Important functions:
- `convex/analysis.ts`
  - `saveAnalysis` (internal mutation)
  - `savePriceEstimate` (internal mutation)
- `convex/publish.ts`
  - `createListingFromAnalysis`
  - `listListings`
- `convex/marketplace.ts`
  - `searchProducts`
  - `generatePayment` (mock payment URL)
  - `confirmSale`

HTTP actions (`convex/http.ts`):
- `POST /api/save-analysis`
- `POST /api/save-price-estimate`
- `POST /api/publish-listing`
- `GET /api/listings`

Note: current HTTP actions use demo identity defaults for some writes (`demo_user` / demo seller path).

### 4) `mcp-server-main` (MCP Bridge)

Primary purpose: expose marketplace operations to MCP-compatible clients (for example Claude Desktop).

Key file:
- `convex_marketplace.py`

Tools exposed:
- `find_products(query)`
- `get_payment_link(id)`
- `finalize_purchase(id, name, address, email)`

This server calls Convex functions via `ConvexClient` and requires `CONVEX_URL`.

### 5) `num-object-detector-main` (Secondary Utility)

Primary purpose: detect if an image has exactly one object.

Includes:
- CLI (`object_detector.py`)
- FastAPI service (`api.py`, default port `8000`)
- quick API test script (`test_api.py`)

This is separate from the richer marketplace analyzer and is useful for intake validation/simple CV checks.

## End-to-End Data Flow

Typical path in this repo:

1. Client sends product images to `cv-base-main/api.py`.
2. Detector returns structured analysis payload.
3. Analysis may be persisted to Convex (`/api/save-analysis`).
4. Analysis is sent to `price-estimator` for market research.
5. Price estimate may be persisted to Convex (`/api/save-price-estimate`).
6. Listing can be published via Convex HTTP (`/api/publish-listing`) and then searched/purchased through Convex or MCP tools.

## Quick Start (Run Everything Locally)

### Prerequisites

- Python 3.8+ (some modules may run on 3.7+ but 3.8+ is safer)
- Node.js for Convex backend
- OpenAI API key

### A) Start Convex backend

```bash
cd Convex-main
npm install
npm run dev
```

### B) Start core analyzer API

```bash
cd cv-base-main
pip install -r requirements.txt
# set OPENAI_API_KEY
# optional: set CONVEX_HTTP_URL to your Convex HTTP endpoint
python api.py
```

### C) Start price estimator API

```bash
cd price-estimator
pip install -r requirements.txt
# set OPENAI_API_KEY
# optional: set CONVEX_HTTP_URL
python price_estimator.py
```

### D) (Optional) Start MCP server

```bash
cd mcp-server-main
uv venv
uv pip install -r requirements.txt
# set CONVEX_URL
uv run convex_marketplace.py
```

## Environment Variables

Common vars used across services:

- `OPENAI_API_KEY` (required by analyzer/estimator)
- `CONVEX_HTTP_URL` (optional; for posting analysis/price data to Convex HTTP actions)
- `CONVEX_URL` (required by MCP server)
- `OPENAI_MODEL` (optional in some modules/examples)

## Current Limitations / Risks

- Payment generation is currently mock-based (`payments.example.com`).
- Several write paths rely on demo identity defaults.
- CORS is open in the analyzer API (`allow_origins=["*"]`) for development convenience.
- Multiple detector services exist with overlapping naming, which can confuse onboarding.
- No unified automated test suite at the repo root.

## Suggested Next Improvements

1. Unify shared contracts for analysis payload keys between services.
2. Add a root orchestration script (or Docker Compose) for one-command startup.
3. Replace demo IDs with authenticated user context.
4. Add integration tests for analysis -> estimate -> persist flow.
5. Add secret scanning and ensure `.env` files are never committed with real keys.
