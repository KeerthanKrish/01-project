# MCP Convex Bridge

A production-ready Model Context Protocol (MCP) bridge server that connects AI agents to a Convex backend via Server-Sent Events (SSE) transport.

## Features

- ✅ **SSE Transport**: Real-time bidirectional communication using Server-Sent Events
- ✅ **Convex Integration**: Direct connection to Convex backend APIs
- ✅ **Type Safety**: Full TypeScript implementation with Zod validation
- ✅ **Authentication**: Bearer token middleware for secure access
- ✅ **MCP Tools**: Three production tools for product search, payments, and purchases
- ✅ **Error Handling**: Comprehensive error handling and validation
- ✅ **Health Monitoring**: Built-in health check endpoint

## Architecture

```
AI Agent → SSE Client → Express Server → MCP Server → Convex Backend
                            ↓
                    Bearer Auth Middleware
                            ↓
                    Zod Schema Validation
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your actual values
```

3. Set up Convex types (if you have a Convex project):
```bash
# This assumes you have convex/_generated/api.ts from your Convex project
# Copy or link the convex directory here
```

## Configuration

### Environment Variables

- `CONVEX_URL`: Your Convex deployment URL (required)
- `AUTH_TOKEN`: Bearer token for API authentication (required)
- `PORT`: Server port (default: 3000)
- `NODE_ENV`: Environment mode (development/production)

## Development

Start the development server with hot reload:
```bash
npm run dev
```

Type checking:
```bash
npm run type-check
```

Build for production:
```bash
npm run build
```

## Production

Build and start:
```bash
npm run build
npm start
```

## API Endpoints

### Public Endpoints

#### `GET /health`
Health check endpoint (no authentication required)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "clients": 2,
  "version": "1.0.0"
}
```

### Authenticated Endpoints

All endpoints below require `Authorization: Bearer <token>` header.

#### `GET /sse?clientId=<uuid>`
Establish SSE connection for receiving server events.

**Query Parameters:**
- `clientId` (optional): Client identifier (auto-generated if not provided)

**Events Sent:**
- `connected`: Initial connection confirmation
- `message`: JSONRPC response messages
- `ping`: Keep-alive pings (every 30s)
- `error`: Error notifications

#### `POST /messages?clientId=<uuid>`
Send JSONRPC messages to invoke MCP tools.

**Query Parameters:**
- `clientId` (required): Client identifier from SSE connection

**Request Body:** JSONRPC 2.0 message format

## MCP Tools

### 1. find_products

Search for products using text query.

**Input:**
```json
{
  "query": "laptop"
}
```

**Validation:**
- `query`: 1-200 characters

**Convex Call:** `api.products.searchProducts`

---

### 2. get_payment_link

Generate payment link for a product.

**Input:**
```json
{
  "id": "product-123"
}
```

**Validation:**
- `id`: non-empty string

**Convex Call:** `api.products.generatePayment`

---

### 3. finalize_purchase

Complete purchase with customer details.

**Input:**
```json
{
  "id": "product-123",
  "name": "John Doe",
  "address": "123 Main St, City, State 12345",
  "email": "john@example.com"
}
```

**Validation:**
- `id`: non-empty string
- `name`: 1-100 characters
- `address`: 5-500 characters
- `email`: valid email format

**Convex Call:** `api.products.confirmSale`

## Usage Example

### 1. Connect via SSE
```javascript
const eventSource = new EventSource(
  'http://localhost:3000/sse?clientId=my-client',
  {
    headers: {
      'Authorization': 'Bearer your-token-here'
    }
  }
);

eventSource.addEventListener('message', (event) => {
  const response = JSON.parse(event.data);
  console.log('Received:', response);
});
```

### 2. Send Tool Request
```javascript
const response = await fetch(
  'http://localhost:3000/messages?clientId=my-client',
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer your-token-here',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: 'find_products',
        arguments: {
          query: 'laptop'
        }
      }
    })
  }
);
```

## Security

- **Authentication**: All MCP endpoints require valid Bearer token
- **Validation**: Zod schemas validate all tool inputs before execution
- **Error Handling**: Errors are sanitized in production mode
- **CORS**: Configure CORS headers as needed for your deployment

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid Authorization header. Expected: Bearer <token>"
}
```

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Validation error: query: Query cannot be empty"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "Failed to search products: Connection timeout"
}
```

## Project Structure

```
mcp/
├── src/
│   ├── index.ts           # Main application entry
│   ├── mcp-server.ts      # MCP server implementation
│   ├── sse-transport.ts   # SSE transport layer
│   ├── convex-client.ts   # Convex backend wrapper
│   ├── schemas.ts         # Zod validation schemas
│   └── middleware.ts      # Express middleware
├── convex/                # Convex API types (from your project)
├── .env.example           # Environment template
├── package.json
├── tsconfig.json
└── README.md
```

## Contributing

1. Follow TypeScript strict mode conventions
2. Add Zod schemas for all new tool inputs
3. Update README for new tools or endpoints
4. Test with both development and production builds

## License

MIT
