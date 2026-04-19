import 'dotenv/config';
import express, { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { MCPServerInstance } from './mcp-server.js';
import { SSETransport } from './sse-transport.js';
import { authMiddleware, errorHandler } from './middleware.js';
import { JSONRPCMessage } from '@modelcontextprotocol/sdk/types.js';

/**
 * Main application entry point
 */
class MCPBridgeApp {
  private app: express.Application;
  private mcpServer: MCPServerInstance;
  private sseTransport: SSETransport;
  private port: number;

  constructor() {
    this.validateEnvironment();

    this.app = express();
    this.port = parseInt(process.env.PORT || '3000', 10);
    this.mcpServer = new MCPServerInstance(process.env.CONVEX_URL!);
    this.sseTransport = new SSETransport();

    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  /**
   * Validate required environment variables
   */
  private validateEnvironment(): void {
    const required = ['CONVEX_URL', 'AUTH_TOKEN'];
    const missing = required.filter((key) => !process.env[key]);

    if (missing.length > 0) {
      throw new Error(
        `Missing required environment variables: ${missing.join(', ')}\n` +
          'Please copy .env.example to .env and configure all values.'
      );
    }
  }

  /**
   * Setup Express middleware
   */
  private setupMiddleware(): void {
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Logging middleware
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
      next();
    });
  }

  /**
   * Setup application routes
   */
  private setupRoutes(): void {
    // Health check endpoint (no auth required)
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        clients: this.sseTransport.getClientCount(),
        version: '1.0.0',
      });
    });

    // Apply authentication to all MCP endpoints
    this.app.use('/sse', authMiddleware);
    this.app.use('/messages', authMiddleware);

    // SSE endpoint - establish event stream
    this.app.get('/sse', (req: Request, res: Response) => {
      const clientId = req.query.clientId as string || uuidv4();
      this.sseTransport.handleSSEConnection(req, res, clientId);
    });

    // Messages endpoint - receive JSONRPC messages
    this.app.post('/messages', async (req: Request, res: Response) => {
      try {
        const clientId = req.query.clientId as string;
        if (!clientId) {
          res.status(400).json({
            error: 'Bad Request',
            message: 'clientId query parameter is required',
          });
          return;
        }

        const message: JSONRPCMessage = req.body;
        if (!message.jsonrpc || message.jsonrpc !== '2.0') {
          res.status(400).json({
            error: 'Bad Request',
            message: 'Invalid JSONRPC message format',
          });
          return;
        }

        await this.sseTransport.handleMessage(
          clientId,
          message,
          this.mcpServer.getServer()
        );

        res.json({ status: 'accepted' });
      } catch (error) {
        console.error('Error handling message:', error);
        res.status(500).json({
          error: 'Internal Server Error',
          message: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    });

    // 404 handler
    this.app.use((req: Request, res: Response) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.path} not found`,
      });
    });
  }

  /**
   * Setup error handling
   */
  private setupErrorHandling(): void {
    this.app.use(errorHandler);

    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      process.exit(1);
    });
  }

  /**
   * Start the server
   */
  start(): void {
    this.app.listen(this.port, () => {
      console.log(`
╔════════════════════════════════════════════╗
║   MCP Convex Bridge Server                 ║
╠════════════════════════════════════════════╣
║   Status: Running                          ║
║   Port: ${this.port}                            ║
║   Convex: ${process.env.CONVEX_URL?.substring(0, 30)}...  ║
║                                            ║
║   Endpoints:                               ║
║   - GET  /health    (public)               ║
║   - GET  /sse       (auth required)        ║
║   - POST /messages  (auth required)        ║
║                                            ║
║   Tools Available:                         ║
║   - find_products                          ║
║   - get_payment_link                       ║
║   - finalize_purchase                      ║
╚════════════════════════════════════════════╝
      `);
    });
  }
}

// Start the application
try {
  const app = new MCPBridgeApp();
  app.start();
} catch (error) {
  console.error('Failed to start application:', error);
  process.exit(1);
}
