"""
Convex Marketplace MCP Server
Built with FastMCP - bridges AI clients to Convex backend marketplace APIs
"""

import os
import sys
from pathlib import Path
from typing import Any

from convex import ConvexClient
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Initialize FastMCP server
mcp = FastMCP("convex-marketplace")

# Initialize Convex client
CONVEX_URL = os.getenv("CONVEX_URL")
if not CONVEX_URL:
    print("Error: CONVEX_URL environment variable is required", file=sys.stderr)
    sys.exit(1)

convex_client = ConvexClient(CONVEX_URL)


@mcp.tool()
async def find_products(query: str) -> str:
    """Search for products in the marketplace.
    
    Args:
        query: Search text to find products (1-200 characters, non-empty)
    """
    # Validate query
    if not query or not query.strip():
        return "Error: Search query cannot be empty"
    
    if len(query) < 1 or len(query) > 200:
        return "Error: Search query must be between 1 and 200 characters"
    
    try:
        # Call Convex marketplace.searchProducts function
        results = convex_client.query("marketplace:searchProducts", {"query": query})
        
        if not results:
            return f"No products found matching '{query}'"
        
        # Format results
        formatted_results = []
        for product in results:
            product_info = f"""
Product ID: {product.get('_id', 'N/A')}
Name: {product.get('name', 'N/A')}
Description: {product.get('description', 'N/A')}
Price: ${product.get('price', 'N/A')}
"""
            formatted_results.append(product_info.strip())
        
        return "\n\n---\n\n".join(formatted_results)
    
    except Exception as e:
        return f"Error searching products: {str(e)}"


@mcp.tool()
async def get_payment_link(id: str) -> str:
    """Generate a payment link for a specific product.
    
    Args:
        id: Product identifier (non-empty string)
    """
    # Validate id
    if not id or not id.strip():
        return "Error: Product ID cannot be empty"
    
    try:
        # Call Convex marketplace.generatePayment function
        payment_data = convex_client.mutation(
            "marketplace:generatePayment",
            {"id": id}
        )
        
        if not payment_data:
            return f"Error: Could not generate payment link for product {id}"
        
        # Format payment information
        payment_info = f"""
Payment Link Generated Successfully

Product ID: {payment_data.get('productId', id)}
Payment URL: {payment_data.get('paymentUrl', 'N/A')}
Amount: ${payment_data.get('amount', 'N/A')}
Currency: {payment_data.get('currency', 'USD')}
Expires: {payment_data.get('expiresAt', 'N/A')}

Instructions: Share this payment link with the customer to complete the purchase.
"""
        
        return payment_info.strip()
    
    except Exception as e:
        return f"Error generating payment link: {str(e)}"


@mcp.tool()
async def finalize_purchase(
    id: str,
    name: str,
    address: str,
    email: str
) -> str:
    """Finalize a purchase with customer details.
    
    Args:
        id: Product being purchased (non-empty string)
        name: Customer name (1-100 characters)
        address: Shipping address (5-500 characters)
        email: Customer email (valid email format)
    """
    # Validate inputs
    if not id or not id.strip():
        return "Error: Product ID cannot be empty"
    
    if not name or not name.strip():
        return "Error: Customer name cannot be empty"
    
    if len(name) < 1 or len(name) > 100:
        return "Error: Customer name must be between 1 and 100 characters"
    
    if not address or not address.strip():
        return "Error: Shipping address cannot be empty"
    
    if len(address) < 5 or len(address) > 500:
        return "Error: Shipping address must be between 5 and 500 characters"
    
    if not email or not email.strip():
        return "Error: Email cannot be empty"
    
    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Error: Invalid email format"
    
    try:
        # Call Convex marketplace.confirmSale function
        confirmation = convex_client.mutation(
            "marketplace:confirmSale",
            {
                "id": id,
                "name": name,
                "address": address,
                "email": email
            }
        )
        
        if not confirmation:
            return "Error: Could not finalize purchase"
        
        # Format confirmation
        confirmation_info = f"""
Purchase Confirmed Successfully! 🎉

Order ID: {confirmation.get('orderId', 'N/A')}
Product ID: {confirmation.get('productId', id)}
Customer: {name}
Email: {email}
Shipping Address: {address}
Status: {confirmation.get('status', 'Confirmed')}
Estimated Delivery: {confirmation.get('estimatedDelivery', 'N/A')}

A confirmation email has been sent to {email}.
"""
        
        return confirmation_info.strip()
    
    except Exception as e:
        return f"Error finalizing purchase: {str(e)}"


def main():
    """Initialize and run the MCP server."""
    # Run the server with stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
