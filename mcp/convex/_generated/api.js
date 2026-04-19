/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import { anyApi, componentsGeneric } from "convex/server";

/**
 * A utility for referencing Convex functions in your app's API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
const fullApiProxy = {
  marketplace: {
    searchProducts: { type: "query", name: "marketplace:searchProducts" },
    generatePayment: { type: "mutation", name: "marketplace:generatePayment" },
    confirmSale: { type: "mutation", name: "marketplace:confirmSale" },
  }
};

export const api = new Proxy(anyApi, {
  get(target, prop) {
    if (prop === 'marketplace') {
      return fullApiProxy.marketplace;
    }
    return target[prop];
  }
});

export const internal = anyApi;
export const components = componentsGeneric();
