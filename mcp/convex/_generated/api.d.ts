/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

/**
 * Marketplace module
 */
export declare const marketplace: {
  searchProducts: FunctionReference<"query", "public", { query: string }, any>;
  generatePayment: FunctionReference<"mutation", "public", { id: string }, any>;
  confirmSale: FunctionReference<"mutation", "public", { id: string; name: string; address: string; email: string }, any>;
};

declare const fullApi: ApiFromModules<{
  marketplace: typeof marketplace;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
> & {
  marketplace: typeof marketplace;
};

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
