# Convex Marketplace MCP Server

MCP server that bridges Claude Desktop to your Convex marketplace backend using FastMCP.

## Features

Three MCP tools for marketplace operations:

1. **find_products** - Search for products
   - Input: `query` (string, 1-200 chars)
   - Calls: `marketplace:searchProducts`

2. **get_payment_link** - Generate payment URL
   - Input: `id` (product identifier)
   - Calls: `marketplace:generatePayment`

3. **finalize_purchase** - Complete order
   - Inputs: `id`, `name`, `address`, `email`
   - Calls: `marketplace:confirmSale`

## Setup

### 1. Install UV

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal.

### 2. Install Dependencies

```bash
# Create virtual environment
uv venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install packages
uv pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
CONVEX_URL=https://your-deployment.convex.cloud
```

### 4. Test the Server

```bash
uv run convex_marketplace.py
```

Press `Ctrl+C` to stop.

## Claude Desktop Configuration

Edit `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add:

```json
{
  "mcpServers": {
    "convex-marketplace": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\mcp_server_local",
        "run",
        "convex_marketplace.py"
      ],
      "env": {
        "CONVEX_URL": "https://your-deployment.convex.cloud"
      }
    }
  }
}
```

Replace paths and URL with your actual values.

Restart Claude Desktop completely (Quit, not just close).

## Testing

Try these prompts in Claude:

```
Find products matching "laptop"
```

```
Generate a payment link for product abc123
```

```
Complete a purchase for product xyz789 with:
- Name: John Doe
- Email: john@example.com
- Address: 123 Main St, Springfield, IL 62701
```

## Required Convex Functions

Your Convex backend must have these functions in the `marketplace` module:

### `searchProducts` (query)
```typescript
export const searchProducts = query({
  args: { query: v.string() },
  handler: async (ctx, { query }) => {
    // Return array of products
  }
});
```

### `generatePayment` (mutation)
```typescript
export const generatePayment = mutation({
  args: { id: v.string() },
  handler: async (ctx, { id }) => {
    // Return payment data with paymentUrl
  }
});
```

### `confirmSale` (mutation)
```typescript
export const confirmSale = mutation({
  args: {
    id: v.string(),
    name: v.string(),
    address: v.string(),
    email: v.string()
  },
  handler: async (ctx, args) => {
    // Return order confirmation
  }
});
```

## Troubleshooting

**Server not showing in Claude?**
- Check JSON syntax in config
- Verify absolute path
- Restart Claude completely
- Check logs: `%APPDATA%\Claude\logs\mcp.log`

**Connection errors?**
- Verify `CONVEX_URL` in `.env`
- Check Convex functions are deployed
- Test: `uv run convex_marketplace.py`

**Import errors?**
```bash
uv pip install --force-reinstall -r requirements.txt
```

## License

MIT
