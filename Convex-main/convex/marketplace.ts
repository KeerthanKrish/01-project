import { mutation, query, type MutationCtx } from "./_generated/server";
import type { Doc, Id } from "./_generated/dataModel";
import { v } from "convex/values";

type AvailableListing = Doc<"listings"> & { status: "available" };

function isAvailableListing(doc: Doc<"listings">): doc is AvailableListing {
  return doc.status === "available";
}

const contactFields = v.object({
  name: v.string(),
  address: v.string(),
  email: v.string(),
});

const availableListingDoc = v.object({
  _id: v.id("listings"),
  _creationTime: v.number(),
  description: v.string(),
  price: v.number(),
  status: v.literal("available"),
  userId: v.id("users"),
  buyerId: v.optional(v.id("buyers")),
});

/**
 * **When to call:** After the user wants to browse or discover items they can
 * buy, or to narrow results by keywords (for example “search for blue shoes”).
 * Use this **before** `generatePayment` or `confirmSale` so you only act on
 * listings the user actually sees.
 *
 * **Behavior:** Returns only listings whose `status` is `'available'`. If
 * `searchText` is empty or whitespace, returns **all** available listings.
 * Otherwise runs full-text search on `description` (Convex search index),
 * still restricted to available items. Each row includes `userId` (app seller).
 *
 * **Do not use for:** Sold items, buyer records, or creating payments—use
 * `generatePayment` / `confirmSale` for purchase flow steps.
 */
export const searchProducts = query({
  args: { searchText: v.string() },
  returns: v.array(availableListingDoc),
  handler: async (ctx, args) => {
    const term = args.searchText.trim();
    const rows =
      term === ""
        ? await ctx.db
            .query("listings")
            .withIndex("by_status", (q) => q.eq("status", "available"))
            .collect()
        : await ctx.db
            .query("listings")
            .withSearchIndex("search_description", (q) =>
              q.search("description", term).eq("status", "available"),
            )
            .collect();
    return rows.filter(isAvailableListing);
  },
});

/**
 * **When to call:** When the user (or checkout flow) is ready to **pay** for a
 * specific listing and you need a URL to redirect them to or display—**after**
 * they chose a product (e.g. from `searchProducts`) and **before** you record
 * the sale in the database.
 *
 * **Behavior:** Verifies the listing exists and `status === 'available'`.
 * Does **not** change the database. Returns a **mock** `paymentUrl` string
 * (not a real payment processor). If the item is missing or not available,
 * throws an error—do not call `confirmSale` until availability is resolved.
 *
 * **Do not use for:** Marking an item sold or saving buyer info—that is
 * `confirmSale`. Do not use as a substitute for search or listing creation.
 */
export const generatePayment = mutation({
  args: { productId: v.id("listings") },
  returns: v.object({
    paymentUrl: v.string(),
  }),
  handler: async (ctx, args) => {
    const listing = await ctx.db.get(args.productId);
    if (!listing) {
      throw new Error("Listing not found");
    }
    if (listing.status !== "available") {
      throw new Error("Product is not available for purchase");
    }
    const paymentUrl = `https://payments.example.com/pay/${args.productId}?mock=true`;
    return { paymentUrl };
  },
});

/**
 * **When to call:** **After** a successful (mock) payment or when the user
 * confirms purchase and provides **name, address, and email**—this is the step
 * that **commits** the sale: creates the buyer and marks the listing sold in
 * **one atomic transaction**.
 *
 * **Behavior:** Requires the listing to exist and be `'available'`. Inserts a
 * `buyers` row with the given contact fields, sets the listing to `'sold'`,
 * and sets `buyerId` on the listing. If the listing is already sold or
 * missing, throws—call `searchProducts` or re-check availability first.
 *
 * **Do not use for:** Starting checkout or getting a payment link—use
 * `generatePayment` first. Do not use for read-only search—use
 * `searchProducts`.
 */
export const confirmSale = mutation({
  args: {
    productId: v.id("listings"),
    name: v.string(),
    address: v.string(),
    email: v.string(),
  },
  returns: v.object({
    buyerId: v.id("buyers"),
    listingId: v.id("listings"),
  }),
  handler: async (ctx, args) => {
    const listing = await ctx.db.get(args.productId);
    if (!listing) {
      throw new Error("Listing not found");
    }
    if (listing.status !== "available") {
      throw new Error("Product is not available");
    }
    const buyerId = await ctx.db.insert("buyers", {
      name: args.name,
      address: args.address,
      email: args.email,
    });
    await ctx.db.patch(args.productId, {
      status: "sold",
      buyerId,
    });
    return { buyerId, listingId: args.productId };
  },
});

async function getOrCreateUserId(
  ctx: MutationCtx,
  fields: { name: string; address: string; email: string },
): Promise<Id<"users">> {
  const existing = await ctx.db
    .query("users")
    .withIndex("by_email", (q) => q.eq("email", fields.email))
    .unique();
  if (existing) {
    return existing._id;
  }
  return await ctx.db.insert("users", fields);
}

/**
 * **When to call:** After MCP (or another tool) returns a JSON file of **buyer**
 * contacts to load into the **`buyers`** table—used for purchase-side data,
 * separate from app `users` / sellers.
 *
 * **How to pass JSON:** e.g.
 * `npx convex run marketplace:importBuyersFromMcpJson -- "$(cat buyers-mcp-import.json)"`
 *
 * **Behavior:** Inserts one `buyers` row per entry. Returns the new buyer ids.
 */
export const importBuyersFromMcpJson = mutation({
  args: {
    buyers: v.array(contactFields),
  },
  returns: v.object({
    buyerIds: v.array(v.id("buyers")),
  }),
  handler: async (ctx, args) => {
    const buyerIds: Id<"buyers">[] = [];
    for (const row of args.buyers) {
      buyerIds.push(
        await ctx.db.insert("buyers", {
          name: row.name,
          address: row.address,
          email: row.email,
        }),
      );
    }
    return { buyerIds };
  },
});

/**
 * **When to call:** After your **app** exports a JSON file where each item
 * pairs **listing** fields with the **owner user** (seller). This inserts into
 * the **`users`** table (deduped by email) and **`listings`** with `userId` set
 * in one mutation per record.
 *
 * **How to pass JSON:** e.g.
 * `npx convex run marketplace:importAppListingsAndUsersFromJson -- "$(cat app-marketplace-import.json)"`
 *
 * **Behavior:** For each record, finds or creates a `users` row by `email`,
 * then inserts `listings` with `userId` and optional `status` (default
 * `'available'`). Returns each `listingId` and `userId` used.
 */
export const importAppListingsAndUsersFromJson = mutation({
  args: {
    records: v.array(
      v.object({
        user: contactFields,
        listing: v.object({
          description: v.string(),
          price: v.number(),
          status: v.optional(
            v.union(v.literal("available"), v.literal("sold")),
          ),
        }),
      }),
    ),
  },
  returns: v.object({
    results: v.array(
      v.object({
        listingId: v.id("listings"),
        userId: v.id("users"),
      }),
    ),
  }),
  handler: async (ctx, args) => {
    const results: { listingId: Id<"listings">; userId: Id<"users"> }[] = [];
    for (const record of args.records) {
      const userId = await getOrCreateUserId(ctx, record.user);
      const listingId = await ctx.db.insert("listings", {
        description: record.listing.description,
        price: record.listing.price,
        status: record.listing.status ?? "available",
        userId,
      });
      results.push({ listingId, userId });
    }
    return { results };
  },
});
