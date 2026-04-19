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
});
