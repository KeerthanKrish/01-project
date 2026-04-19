import { internalMutation } from "./_generated/server";
import { v } from "convex/values";

export const saveAnalysis = internalMutation({
  args: {
    userId: v.string(),
    analysisJson: v.string(),
    category: v.string(),
    brand: v.string(),
    productType: v.string(),
    marketplaceSuitable: v.boolean(),
    createdAt: v.number(),
  },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("analyses", {
      userId: args.userId,
      analysisJson: args.analysisJson,
      category: args.category,
      brand: args.brand,
      productType: args.productType,
      marketplaceSuitable: args.marketplaceSuitable,
      createdAt: args.createdAt,
    });
    return { id };
  },
});

export const savePriceEstimate = internalMutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("priceEstimates", {
      userId: args.userId,
      analysisId: args.analysisId,
      estimateJson: args.estimateJson,
      category: args.category,
      brand: args.brand,
      productType: args.productType,
      condition: args.condition,
      color: args.color,
      material: args.material,
      imagesAnalyzed: args.imagesAnalyzed,
      marketplaceSuitable: args.marketplaceSuitable,
      analysisTimestamp: args.analysisTimestamp,
      title: args.title,
      recommendedPrice: args.recommendedPrice,
      minPrice: args.minPrice,
      maxPrice: args.maxPrice,
      createdAt: args.createdAt,
    });
    return { id };
  },
});
