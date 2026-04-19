import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { ConvexBridge } from './convex-client.js';
import {
  findProductsSchema,
  getPaymentLinkSchema,
  finalizePurchaseSchema,
  FindProductsInput,
  GetPaymentLinkInput,
  FinalizePurchaseInput,
} from './schemas.js';
import { ZodError } from 'zod';

/**
 * MCP Server implementation with tool registration
 */
export class MCPServerInstance {
  private server: Server;
  private convexBridge: ConvexBridge;

  constructor(convexUrl: string) {
    this.convexBridge = new ConvexBridge(convexUrl);
    this.server = new Server(
      {
        name: 'convex-bridge-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.registerToolHandlers();
  }

  /**
   * Register all tool handlers with the MCP server
   */
  private registerToolHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'find_products',
          description:
            'Search for products in the catalog using a text query. Returns a list of matching products with details like name, description, price, and availability.',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query to find products (1-200 characters)',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'get_payment_link',
          description:
            'Generate a secure payment link for a specific product. Returns a payment URL that customers can use to complete their purchase.',
          inputSchema: {
            type: 'object',
            properties: {
              id: {
                type: 'string',
                description: 'Unique identifier of the product',
              },
            },
            required: ['id'],
          },
        },
        {
          name: 'finalize_purchase',
          description:
            'Complete a purchase transaction with customer details. Confirms the sale and processes the order with shipping information.',
          inputSchema: {
            type: 'object',
            properties: {
              id: {
                type: 'string',
                description: 'Unique identifier of the product being purchased',
              },
              name: {
                type: 'string',
                description: 'Customer full name (1-100 characters)',
              },
              address: {
                type: 'string',
                description: 'Shipping address (5-500 characters)',
              },
              email: {
                type: 'string',
                description: 'Customer email address for order confirmation',
              },
            },
            required: ['id', 'name', 'address', 'email'],
          },
        },
      ],
    }));

    // Handle tool execution
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        switch (request.params.name) {
          case 'find_products':
            return await this.handleFindProducts(request.params.arguments);

          case 'get_payment_link':
            return await this.handleGetPaymentLink(request.params.arguments);

          case 'finalize_purchase':
            return await this.handleFinalizePurchase(request.params.arguments);

          default:
            throw new Error(`Unknown tool: ${request.params.name}`);
        }
      } catch (error) {
        if (error instanceof ZodError) {
          return {
            content: [
              {
                type: 'text',
                text: `Validation error: ${error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ')}`,
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  /**
   * Handle find_products tool call
   */
  private async handleFindProducts(args: unknown) {
    const input = findProductsSchema.parse(args) as FindProductsInput;
    const result = await this.convexBridge.findProducts(input.query);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Handle get_payment_link tool call
   */
  private async handleGetPaymentLink(args: unknown) {
    const input = getPaymentLinkSchema.parse(args) as GetPaymentLinkInput;
    const result = await this.convexBridge.getPaymentLink(input.id);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Handle finalize_purchase tool call
   */
  private async handleFinalizePurchase(args: unknown) {
    const input = finalizePurchaseSchema.parse(args) as FinalizePurchaseInput;
    const result = await this.convexBridge.finalizePurchase(
      input.id,
      input.name,
      input.address,
      input.email
    );

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Get the underlying MCP server instance
   */
  getServer(): Server {
    return this.server;
  }

  /**
   * Connect with stdio transport (for testing)
   */
  async connectStdio(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}
