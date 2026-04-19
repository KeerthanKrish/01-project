import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';

/**
 * Convex client wrapper for backend operations
 */
export class ConvexBridge {
  private client: ConvexHttpClient;

  constructor(convexUrl: string) {
    if (!convexUrl) {
      throw new Error('CONVEX_URL environment variable is required');
    }
    this.client = new ConvexHttpClient(convexUrl);
  }

  /**
   * Search for products using Convex backend
   */
  async findProducts(query: string) {
    try {
      const result = await this.client.query(api.products.searchProducts, {
        query,
      });
      return result;
    } catch (error) {
      throw new Error(
        `Failed to search products: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Generate payment link for a product
   */
  async getPaymentLink(id: string) {
    try {
      const result = await this.client.mutation(api.products.generatePayment, {
        id,
      });
      return result;
    } catch (error) {
      throw new Error(
        `Failed to generate payment link: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Finalize a purchase with customer details
   */
  async finalizePurchase(
    id: string,
    name: string,
    address: string,
    email: string
  ) {
    try {
      const result = await this.client.mutation(api.products.confirmSale, {
        id,
        name,
        address,
        email,
      });
      return result;
    } catch (error) {
      throw new Error(
        `Failed to finalize purchase: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }
}
