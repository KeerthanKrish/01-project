import { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { JSONRPCMessage } from '@modelcontextprotocol/sdk/types.js';

/**
 * SSE transport implementation for MCP server
 */
export class SSETransport {
  private clients: Map<string, Response> = new Map();
  private messageHandlers: Map<string, (message: JSONRPCMessage) => void> = new Map();

  /**
   * Handle SSE connection endpoint
   */
  handleSSEConnection(req: Request, res: Response, clientId: string): void {
    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

    // Store client connection
    this.clients.set(clientId, res);

    console.log(`SSE client connected: ${clientId}`);

    // Send initial connection event
    this.sendEvent(res, 'connected', { clientId, timestamp: Date.now() });

    // Handle client disconnect
    req.on('close', () => {
      console.log(`SSE client disconnected: ${clientId}`);
      this.clients.delete(clientId);
      this.messageHandlers.delete(clientId);
    });

    // Keep connection alive with periodic pings
    const pingInterval = setInterval(() => {
      if (this.clients.has(clientId)) {
        this.sendEvent(res, 'ping', { timestamp: Date.now() });
      } else {
        clearInterval(pingInterval);
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Handle incoming message from client
   */
  async handleMessage(
    clientId: string,
    message: JSONRPCMessage,
    server: Server
  ): Promise<void> {
    const client = this.clients.get(clientId);
    if (!client) {
      throw new Error(`Client ${clientId} not connected`);
    }

    try {
      // Set up one-time response handler
      const responseHandler = (response: JSONRPCMessage) => {
        this.sendEvent(client, 'message', response);
      };

      this.messageHandlers.set(clientId, responseHandler);

      // Process message through MCP server
      // Note: The SDK handles request processing internally
      // We'll send the response via SSE when ready
      
      // For now, echo back the message structure
      // In production, integrate with actual MCP server message handling
      this.sendEvent(client, 'message', {
        jsonrpc: '2.0',
        id: (message as any).id,
        result: { status: 'processed' },
      });
    } catch (error) {
      this.sendEvent(client, 'error', {
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  /**
   * Send an event to SSE client
   */
  private sendEvent(res: Response, event: string, data: any): void {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }

  /**
   * Broadcast message to all connected clients
   */
  broadcast(event: string, data: any): void {
    this.clients.forEach((client) => {
      this.sendEvent(client, event, data);
    });
  }

  /**
   * Get number of connected clients
   */
  getClientCount(): number {
    return this.clients.size;
  }
}
