import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  /** Purchase / MCP-sourced buyer records (checkout flow). */
  buyers: defineTable({
    name: v.string(),
    address: v.string(),
    email: v.string(),
  }).index("by_email", ["email"]),

  /** App-sourced user accounts (sellers); distinct from `buyers`. */
  users: defineTable({
    name: v.string(),
    address: v.string(),
    email: v.string(),
  }).index("by_email", ["email"]),

  listings: defineTable({
    description: v.string(),
    price: v.number(),
    status: v.union(v.literal("available"), v.literal("sold")),
    /** App user (seller) this listing belongs to. */
    userId: v.id("users"),
    buyerId: v.optional(v.id("buyers")),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"])
    .searchIndex("search_description", {
      searchField: "description",
      filterFields: ["status"],
    }),

  analyses: defineTable({
    userId: v.string(),
    analysisJson: v.string(),
    category: v.string(),
    brand: v.string(),
    productType: v.string(),
    marketplaceSuitable: v.boolean(),
    createdAt: v.number(),
  })
    .index("by_category", ["category"])
    .index("by_brand", ["brand"])
    .index("by_createdAt", ["createdAt"])
    .index("by_userId", ["userId"]),

  priceEstimates: defineTable({
    userId: v.string(),
    analysisId: v.string(),
    estimateJson: v.string(),
    category: v.string(),
    brand: v.string(),
    productType: v.string(),
    condition: v.string(),
    color: v.string(),
    material: v.string(),
    imagesAnalyzed: v.number(),
    marketplaceSuitable: v.boolean(),
    analysisTimestamp: v.string(),
    title: v.string(),
    recommendedPrice: v.number(),
    minPrice: v.number(),
    maxPrice: v.number(),
    createdAt: v.number(),
  })
    .index("by_analysisId", ["analysisId"])
    .index("by_createdAt", ["createdAt"])
    .index("by_userId", ["userId"]) 
    .index("by_category", ["category"]) 
    .index("by_brand", ["brand"]) 
    .index("by_productType", ["productType"]),
});
