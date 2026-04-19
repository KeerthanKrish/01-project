import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();
const DEMO_USER_ID = "demo_user";

http.route({
  path: "/api/save-analysis",
  method: "POST",
  handler: httpAction(async (ctx: any, req: any) => {
    try {
      const body = await req.json();
      const createdAt = typeof body.createdAt === "number" ? body.createdAt : Date.now();

      const result = await ctx.runMutation(internal.analysis.saveAnalysis, {
        userId: DEMO_USER_ID,
        analysisJson: JSON.stringify(body.analysisJson ?? body.analysis ?? {}),
        category: String(body.category ?? ""),
        brand: String(body.brand ?? ""),
        productType: String(body.productType ?? ""),
        marketplaceSuitable: Boolean(body.marketplaceSuitable),
        createdAt,
      });

      return new Response(JSON.stringify({ ok: true, id: result.id }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return new Response(JSON.stringify({ ok: false, error: message }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }
  }),
});

http.route({
  path: "/api/save-price-estimate",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    try {
      const body = await req.json();
      const createdAt = typeof body.createdAt === "number" ? body.createdAt : Date.now();

      const result = await ctx.runMutation(internal.analysis.savePriceEstimate, {
        userId: DEMO_USER_ID,
        analysisId: String(body.analysisId ?? ""),
        estimateJson: JSON.stringify(body.estimateJson ?? body.estimate ?? {}),
        category: String(body.category ?? ""),
        brand: String(body.brand ?? ""),
        productType: String(body.productType ?? ""),
        condition: String(body.condition ?? ""),
        color: String(body.color ?? ""),
        material: String(body.material ?? ""),
        imagesAnalyzed: Number(body.imagesAnalyzed ?? 0),
        marketplaceSuitable: Boolean(body.marketplaceSuitable),
        analysisTimestamp: String(body.analysisTimestamp ?? ""),
        title: String(body.title ?? ""),
        recommendedPrice: Number(body.recommendedPrice ?? 0),
        minPrice: Number(body.minPrice ?? 0),
        maxPrice: Number(body.maxPrice ?? 0),
        createdAt,
      });

      return new Response(JSON.stringify({ ok: true, id: result.id }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return new Response(JSON.stringify({ ok: false, error: message }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }
  }),
});

http.route({
  path: "/api/publish-listing",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    try {
      const body = await req.json();
      const analysis = body.analysisJson ?? body.analysis ?? {};
      const tier2 = analysis.tier2 ?? {};
      const listing = analysis.listing ?? {};
      const imageUrls =
        body.imageUrls ??
        listing.imageUrls ??
        analysis.imageUrls ??
        [];

      const sellerPrice = Number(body.sellerPrice ?? body.price ?? 0);
      const title = String(listing.title ?? "");
      const description = String(
        listing.description ??
          `${tier2.brand ?? ""} ${tier2.product_type ?? ""}`.trim(),
      );

      const result = await ctx.runMutation(
        internal.publish.createListingFromAnalysis,
        {
          description: description || title || "Listing",
          price: sellerPrice,
          imageUrls: Array.isArray(imageUrls)
            ? imageUrls.map((url) => String(url))
            : [],
        },
      );

      return new Response(JSON.stringify({ ok: true, ...result }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return new Response(JSON.stringify({ ok: false, error: message }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }
  }),
});

http.route({
  path: "/api/listings",
  method: "GET",
  handler: httpAction(async (ctx, req) => {
    try {
      const url = new URL(req.url);
      const limitParam = url.searchParams.get("limit");
      const limit = limitParam ? Number(limitParam) : undefined;

      const listings = await ctx.runQuery(internal.publish.listListings, {
        limit,
      });

      return new Response(JSON.stringify({ ok: true, listings }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return new Response(JSON.stringify({ ok: false, error: message }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }
  }),
});

export default http;
