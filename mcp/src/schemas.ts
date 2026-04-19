import { z } from 'zod';

/**
 * Zod schemas for strict validation of tool inputs
 */

export const findProductsSchema = z.object({
  query: z.string().min(1, 'Query cannot be empty').max(200, 'Query too long'),
});

export const getPaymentLinkSchema = z.object({
  id: z.string().min(1, 'Product ID is required'),
});

export const finalizePurchaseSchema = z.object({
  id: z.string().min(1, 'Product ID is required'),
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  address: z.string().min(5, 'Address is required').max(500, 'Address too long'),
  email: z.string().email('Invalid email format'),
});

export type FindProductsInput = z.infer<typeof findProductsSchema>;
export type GetPaymentLinkInput = z.infer<typeof getPaymentLinkSchema>;
export type FinalizePurchaseInput = z.infer<typeof finalizePurchaseSchema>;
