import { internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";

type DemoUser = {
  name: string;
  address: string;
  email: string;
};

const DEMO_USER: DemoUser = {
  name: "Demo Seller",
  address: "",
  email: "demo@seller.local",
};

export const createListingFromAnalysis = internalMutation({
  args: {
    description: v.string(),
    price: v.number(),
    imageUrls: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", DEMO_USER.email))
      .unique();

    const userId = existing
      ? existing._id
      : await ctx.db.insert("users", DEMO_USER);

    const listingId = await ctx.db.insert("listings", {
      description: args.description,
      price: args.price,
      imageUrls: args.imageUrls,
      status: "available",
      userId,
    });

    return { listingId, userId };
  },
});

export const listListings = internalQuery({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    return await ctx.db.query("listings").order("desc").take(limit);
  },
});
