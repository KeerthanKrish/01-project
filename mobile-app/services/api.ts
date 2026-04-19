import Constants from 'expo-constants';
import { Platform } from 'react-native';

/** Strip scheme/port/path; keep hostname or IPv4. */
function normalizeDevHost(raw: string): string {
  return raw
    .trim()
    .replace(/^https?:\/\//, '')
    .split('/')[0]
    .split(':')[0];
}

function isPrivateOrLocalHost(host: string): boolean {
  const h = host.toLowerCase();
  if (h === 'localhost' || h === '127.0.0.1' || h === '10.0.2.2') return true;
  if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return false;
  const [a, b] = host.split('.').map(Number);
  if (a === 10) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  return false;
}

/** Tunnel / edge hosts point at Metro only — FastAPI is still on your LAN unless tunneled separately. */
function isLikelyMetroOnlyHost(host: string): boolean {
  const h = host.toLowerCase();
  return h.includes('exp.direct') || h.includes('ngrok') || h.endsWith('.exp.host');
}

/**
 * Machine that serves ports 8000/8001/8002 (same as Metro in typical dev).
 * - Set `EXPO_PUBLIC_API_HOST` if you use `expo start --tunnel` or a remote backend.
 * - Otherwise we reuse Expo's packager host when it looks like LAN/local.
 */
function apiDevHost(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_HOST;
  if (fromEnv?.trim()) return normalizeDevHost(fromEnv);

  const uri = Constants.expoConfig?.hostUri;
  if (uri) {
    const host = normalizeDevHost(uri);
    if (host && !isLikelyMetroOnlyHost(host) && isPrivateOrLocalHost(host)) return host;
    if (__DEV__ && host && isLikelyMetroOnlyHost(host)) {
      console.warn(
        '[api] Metro is on a tunnel host; FastAPI will not match. Set EXPO_PUBLIC_API_HOST to your Mac LAN IP (or tunnel the APIs).'
      );
    }
  }

  if (Platform.OS === 'android') return '10.0.2.2';
  // Physical iPhones cannot use 127.0.0.1 for a Mac-hosted API; keep LAN default from this repo.
  if (Platform.OS === 'ios') return '10.130.81.96';
  return '127.0.0.1';
}

const API_HOST = apiDevHost();
export const DETECTOR_BASE = `http://${API_HOST}:8000`;
export const ANALYZER_BASE = `http://${API_HOST}:8001`;
export const ESTIMATE_BASE = `http://${API_HOST}:8002`;

if (__DEV__) {
  console.log('[api] backends:', { API_HOST, DETECTOR_BASE, ANALYZER_BASE, ESTIMATE_BASE });
}

// ── Feature flags ─────────────────────────────────────────────────────────────
export const FLAGS = {
  /** Run POST /detect on each photo and gate "Continue" on the result. */
  objectDetection: true,
  /** Run POST /api/analyze when the user hits Continue. */
  productAnalysis: true,
  /** POST /estimate on "Get estimate" from review (requires pricing server). */
  pricingEstimate: true,
};
// ─────────────────────────────────────────────────────────────────────────────

// ── Types ─────────────────────────────────────────────────────────────────────

export type DetectionResult = {
  image_name: string;
  object_count: number;
  has_exactly_one_object: boolean;
  error: string | null;
};

/** Real API response shape from POST /api/analyze (cv-base-main) */
export type AnalysisResponse = {
  success: boolean;
  marketplace_suitable: boolean;
  suitability_reasoning: string;
  images_analyzed: number;
  analysis_timestamp: string;
  detail_level: string;

  /** Tier-1 category detection */
  tier1: {
    category: string;
    confidence: number;
    alternatives: { category: string; confidence: number }[];
    reasoning?: string;
  };

  /** Tier-2 detailed product analysis */
  tier2: {
    brand?: string;
    product_type?: string;
    material?: string;
    color?: string;
    condition?: string;
    visible_text_found?: string[];
    barcode_sku_found?: string | null;
    general_physical_damage?: {
      scratches?: string[];
      dents?: string[];
      scuffs?: string[];
      discoloration?: string[];
      cracks_or_chips?: string[];
      other_damage?: string[];
    };
    product_specific_wear_analysis?: {
      inspection_results?: {
        wear_point: string;
        status: string;
        details: string;
        severity: string;
        affects_function: boolean;
      }[];
    };
    marketplace_assessment?: {
      cosmetic_grade?: string;
      major_concerns?: string[];
      selling_points?: string[];
    };
  };

  /** Flat convenience product object (may be null if not marketplace-suitable) */
  product: {
    brand: string;
    type: string;
    material: string;
    color: string;
    condition: string;
    cosmetic_grade: string;
    functionality: boolean;
    overall_confidence: number;
  } | null;

  /** Denormalised category (mirrors tier1) */
  category: {
    name: string;
    confidence: number;
    alternatives: { category: string; confidence: number }[];
  };

  /** Marketplace listing copy */
  listing: {
    title?: string;
    description?: string;
    condition?: string;
    grade?: string;
    selling_points?: string[];
    buyer_concerns?: string[];
  };

  /** Search optimisation payload */
  search: {
    primary_query?: string;
    fallback_query?: string;
    keywords?: string[];
    filters?: Record<string, string | string[]>;
  };

  /** Barcode lookup result (if a barcode was detected) */
  barcode_lookup?: {
    found: boolean;
    barcode?: string;
    title?: string;
    brand?: string;
    source?: string;
  };

  /** Appended client-side: user review fields not in tier1/tier2 */
  review_inputs?: {
    damage_issues: string;
    included_with_item: string;
    purchase_year_or_age: string;
    original_price_usd: string;
    notes: string;
    size: string;
  };
};

/** Review form fields (matches ProductDetails in scan-review). */
export type ReviewFormFields = {
  title: string;
  brand: string;
  model: string;
  category: string;
  condition: string;
  material: string;
  color: string;
  size: string;
  includedWithItem: string;
  purchaseYearOrAge: string;
  damageIssues: string;
  originalPrice: string;
  notes: string;
};

/** Deep-merge user edits from the review screen into the /api/analyze payload. */
export function mergeReviewIntoAnalysis(
  base: AnalysisResponse,
  details: ReviewFormFields
): AnalysisResponse {
  const out = JSON.parse(JSON.stringify(base)) as AnalysisResponse;
  const t2 = out.tier2;
  if (details.title) {
    t2.product_type = details.title;
    out.listing = { ...out.listing, title: details.title };
    if (out.product) out.product.type = details.title;
  }
  if (details.brand) {
    t2.brand = details.brand;
    if (out.product) out.product.brand = details.brand;
  }
  if (details.model) {
    t2.barcode_sku_found = details.model;
  }
  if (details.category) {
    out.tier1.category = details.category;
    out.category = {
      name: details.category,
      confidence: out.category?.confidence ?? 0,
      alternatives: out.category?.alternatives ?? [],
    };
  }
  if (details.condition) {
    t2.condition = details.condition;
    out.listing = { ...out.listing, condition: details.condition };
    if (out.product) out.product.condition = details.condition;
  }
  if (details.material) {
    t2.material = details.material;
    if (out.product) out.product.material = details.material;
  }
  if (details.color) {
    t2.color = details.color;
    if (out.product) out.product.color = details.color;
  }

  out.review_inputs = {
    damage_issues: details.damageIssues,
    included_with_item: details.includedWithItem,
    purchase_year_or_age: details.purchaseYearOrAge,
    original_price_usd: details.originalPrice,
    notes: details.notes,
    size: details.size,
  };

  return out;
}

export type ExistingListing = {
  title: string;
  url: string;
  price: number;
  marketplace: string;
};

export type MarketResearch = {
  timestamp?: string;
  response_id?: string;
  model?: string;
  recommended_price: number;
  price_range: { min: number; max: number };
  existing_listings: ExistingListing[];
};

export type EstimateApiResponse = {
  analysis: AnalysisResponse & { market_research?: MarketResearch };
  market_research: MarketResearch;
};

// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /detect
 * Validates that a single image contains exactly one object.
 */
export async function detectImage(imageUri: string): Promise<DetectionResult | null> {
  const url = `${DETECTOR_BASE}/detect`;
  console.log('[detect] → POST', url, '| uri:', imageUri.slice(0, 60));
  try {
    const form = new FormData();
    const ext = imageUri.split('.').pop()?.toLowerCase() ?? 'jpg';
    const mime = ext === 'png' ? 'image/png' : ext === 'heic' ? 'image/heic' : 'image/jpeg';
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    form.append('file', { uri: imageUri, type: mime, name: `image.${ext}` } as any);

    const res = await fetch(url, { method: 'POST', body: form });
    console.log('[detect] ← status:', res.status);

    if (!res.ok) {
      console.log('[detect] non-ok response:', res.status, res.statusText);
      return null;
    }

    const data = (await res.json()) as DetectionResult;
    console.log('[detect] result:', JSON.stringify(data));
    return data;
  } catch (err) {
    console.log('[detect] fetch error:', err);
    return null;
  }
}

/**
 * POST /api/analyze
 * Sends images to the analyser and returns the full analysis response.
 *
 * Mirrors exactly:
 *   curl -X POST "http://localhost:8001/api/analyze" -F "images=@photo.jpg"
 */
export async function analyzeImages(imageUris: string[]): Promise<AnalysisResponse | null> {
  const url = `${ANALYZER_BASE}/api/analyze`;
  console.log('[analyze] → POST', url, `| ${imageUris.length} image(s)`);
  try {
    // React Native's FormData accepts { uri, type, name } as the file value —
    // identical to what the browser does with a File object from <input type="file">.
    const form = new FormData();
    imageUris.forEach((uri, i) => {
      // Detect MIME type from extension; default to jpeg.
      const ext = uri.split('.').pop()?.toLowerCase() ?? 'jpg';
      const mime = ext === 'png' ? 'image/png' : ext === 'heic' ? 'image/heic' : 'image/jpeg';
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      form.append('images', { uri, type: mime, name: `image_${i + 1}.${ext}` } as any);
    });

    const res = await fetch(url, { method: 'POST', body: form });
    console.log('[analyze] ← status:', res.status);

    const raw = await res.text();
    console.log('[analyze] raw response (first 1500):', raw.slice(0, 1500));

    if (!res.ok) {
      console.log('[analyze] non-ok:', res.status, res.statusText);
      return null;
    }

    let data: AnalysisResponse;
    try {
      data = JSON.parse(raw) as AnalysisResponse;
    } catch (e) {
      console.log('[analyze] JSON parse error:', e);
      return null;
    }
    console.log('[analyze] data:', data);
    return data;
  } catch (err) {
    console.log('[analyze] fetch error:', err);
    return null;
  }
}

/**
 * POST /estimate
 * Body: `{ analysis: AnalysisResponse }` — full analyze payload merged with review edits.
 */
export async function postEstimate(analysis: AnalysisResponse): Promise<EstimateApiResponse | null> {
  const url = `${ESTIMATE_BASE}/estimate`;
  console.log('[estimate] → POST', url);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ analysis }),
    });
    const raw = await res.text();
    console.log('[estimate] ← status:', res.status, raw.slice(0, 400));

    if (!res.ok) {
      console.log('[estimate] non-ok body:', raw);
      return null;
    }

    const data = JSON.parse(raw) as EstimateApiResponse;
    console.log('[estimate] data:', data);
    return data;
  } catch (err) {
    console.log('[estimate] fetch error:', err);
    return null;
  }
}

/** Convex HTTP site (publish + listings) */
export const CONVEX_SITE_BASE = 'https://spotted-swordfish-838.convex.site';

/** Convex HTTP action — publish listing to DB */
export const PUBLISH_LISTING_URL = `${CONVEX_SITE_BASE}/api/publish-listing`;

export type PublishListingPayload = {
  analysis: {
    listing: { title: string; description: string };
    tier2: { brand: string; product_type: string };
  };
  sellerPrice: number;
};

export type PublishListingResult =
  | { ok: true; data: unknown }
  | { ok: false; status: number; message: string };

/**
 * POST /api/publish-listing (Convex)
 */
export async function publishListing(
  payload: PublishListingPayload
): Promise<PublishListingResult> {
  console.log('[publish] → POST', PUBLISH_LISTING_URL);
  console.log('[publish] body:', JSON.stringify(payload));
  try {
    const res = await fetch(PUBLISH_LISTING_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const raw = await res.text();
    console.log('[publish] ← status:', res.status, raw.slice(0, 800));

    if (!res.ok) {
      let message = raw || res.statusText;
      try {
        const j = JSON.parse(raw) as { error?: string; message?: string };
        message = j.error ?? j.message ?? message;
      } catch {
        /* use raw */
      }
      return { ok: false, status: res.status, message };
    }

    let data: unknown = raw;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = raw;
    }
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.log('[publish] fetch error:', err);
    return { ok: false, status: 0, message };
  }
}

// ── Listings (GET) ───────────────────────────────────────────────────────────

export type ConvexListing = {
  _id: string;
  _creationTime: number;
  description: string;
  price: number;
  status: string;
  userId: string;
  buyerId: string | null;
};

export type ListingsApiResult =
  | { ok: true; listings: ConvexListing[] }
  | { ok: false; error: string };

/**
 * GET /api/listings?limit=50
 */
export async function fetchListings(limit = 50): Promise<ListingsApiResult> {
  const url = `${CONVEX_SITE_BASE}/api/listings?limit=${limit}`;
  console.log('[listings] → GET', url);
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    const raw = await res.text();
    console.log('[listings] ←', res.status, raw.slice(0, 400));

    let parsed: unknown;
    try {
      parsed = raw ? JSON.parse(raw) : {};
    } catch {
      return { ok: false, error: 'Invalid JSON from server' };
    }

    const body = parsed as { ok?: boolean; listings?: ConvexListing[]; error?: string };

    if (!res.ok) {
      return { ok: false, error: body.error ?? res.statusText ?? `HTTP ${res.status}` };
    }

    if (body.ok === false) {
      return { ok: false, error: body.error ?? 'Unknown error' };
    }

    if (body.ok !== true || !Array.isArray(body.listings)) {
      return { ok: false, error: body.error ?? 'Malformed response: expected ok and listings[]' };
    }

    return { ok: true, listings: body.listings };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.log('[listings] fetch error:', err);
    return { ok: false, error: message };
  }
}
