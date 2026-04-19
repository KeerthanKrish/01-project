import { ThemedText } from '@/components/themed-text';
import { useScanImages } from '@/contexts/scan-images-context';
import { useThemeColor } from '@/hooks/use-theme-color';
import MOCK from '@/mock_data.json';
import { publishListing, type PublishListingPayload } from '@/services/api';
import { useLocalSearchParams, useRouter, type Href } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ProductDetails } from './scan-review';

const CONDITION_TO_GRADE: Record<string, string> = {
  'New':       'A',
  'Like new':  'A',
  'Good':      'B',
  'Fair':      'C',
  'Poor':      'D',
};

const SEVERITY_COLOR: Record<string, string> = {
  none: '#16a34a',
  minor: '#ca8a04',
  moderate: '#ea580c',
  severe: '#dc2626',
};
const SEVERITY_LABEL: Record<string, string> = {
  none: '✓ None',
  minor: '! Minor',
  moderate: '!! Moderate',
  severe: '!!! Severe',
};
const GRADE_COLOR: Record<string, string> = {
  A: 'green', B: 'orange', C: 'red', D: 'red',
};

const MOCK_PRICES = { quickSale: 185, fair: 240, max: 295 };
const MOCK_COMPS = [
  { title: 'Similar item — very good condition', price: '$249', platform: 'eBay', daysAgo: 2 },
  { title: 'Same model, minor wear', price: '$220', platform: 'Facebook', daysAgo: 5 },
  { title: 'Like new, with accessories', price: '$289', platform: 'eBay', daysAgo: 7 },
  { title: 'Good condition, no box', price: '$195', platform: 'Craigslist', daysAgo: 12 },
];

export default function EstimateScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { analysisResult, estimateResult, resetScanSession } = useScanImages();
  const params = useLocalSearchParams<{ details: string }>();
  const details: Partial<ProductDetails> = params.details ? JSON.parse(params.details) : {};
  const [userListingPrice, setUserListingPrice] = useState('');
  const userPriceNum = useMemo(() => {
    const n = parseFloat(userListingPrice.replace(/[^0-9.]/g, ''));
    return Number.isFinite(n) && n >= 0 ? n : null;
  }, [userListingPrice]);
  const hasPriceInput = userListingPrice.trim().length > 0;
  const [publishing, setPublishing] = useState(false);

  const isRealData = !!analysisResult;
  const mr = estimateResult?.market_research;
  const priceFromApi = mr && typeof mr.recommended_price === 'number';
  const displayPrices = priceFromApi
    ? { quickSale: mr.price_range.min, fair: mr.recommended_price, max: mr.price_range.max }
    : MOCK_PRICES;
  console.log('[estimate] using', isRealData ? 'real API data' : 'mock data', priceFromApi ? '| live pricing' : '');

  // ── Normalise API response OR mock into a common shape ──────────────────────
  type WearPoint = { wear_point: string; details: string; severity: string; affects_function: boolean };
  let ai: {
    brand: string; type: string; category: string; condition: string;
    material: string; color: string; size: string;
    confidence: number; wearSummary: string; imagesAnalyzed: number;
    functional: boolean; functionalReasoning: string;
    cosmeticGrade: string; majorConcerns: string[]; sellingPoints: string[];
    completeness: string; cleanliness: string;
    titleSuggestion: string; buyerConcerns: string[];
    wearPoints: WearPoint[];
    suitabilityWarning: string;
    searchQuery: string;
    barcodeBrand: string;
  };

  if (isRealData) {
    const r = analysisResult!;
    const t2 = r.tier2;
    const mp = r.listing;
    const prod = r.product;

    ai = {
      brand:               t2.brand ?? prod?.brand ?? '',
      type:                t2.product_type ?? prod?.type ?? '',
      category:            r.tier1.category,
      condition:           t2.condition ?? prod?.condition ?? '',
      material:            t2.material ?? prod?.material ?? '',
      color:               t2.color ?? prod?.color ?? '',
      size:                '—',
      confidence:          Math.round((prod?.overall_confidence ?? 0) * 100),
      wearSummary:         '',
      imagesAnalyzed:      r.images_analyzed,
      functional:          prod?.functionality ?? true,
      functionalReasoning: t2.product_specific_wear_analysis?.inspection_results?.[0]?.details ?? '',
      cosmeticGrade:       t2.marketplace_assessment?.cosmetic_grade ?? prod?.cosmetic_grade ?? '',
      majorConcerns:       t2.marketplace_assessment?.major_concerns ?? [],
      sellingPoints:       mp.selling_points ?? t2.marketplace_assessment?.selling_points ?? [],
      completeness:        '',
      cleanliness:         '',
      titleSuggestion:     mp.title ?? r.barcode_lookup?.title ?? `${t2.brand ?? ''} ${t2.product_type ?? ''}`.trim(),
      buyerConcerns:       mp.buyer_concerns ?? [],
      wearPoints:          t2.product_specific_wear_analysis?.inspection_results ?? [],
      suitabilityWarning:  r.marketplace_suitable ? '' : (r.suitability_reasoning ?? ''),
      searchQuery:         r.search.primary_query ?? r.search.fallback_query ?? '',
      barcodeBrand:        r.barcode_lookup?.brand ?? '',
    };
  } else {
    const t2 = MOCK.tier2_detailed_analysis;
    const mp = MOCK.marketplace_listing_ready;
    ai = {
      brand:               t2.brand,
      type:                t2.product_type,
      category:            t2.category,
      condition:           t2.condition,
      material:            t2.material,
      color:               t2.color,
      size:                t2.size_or_dimensions !== 'Not visible' ? t2.size_or_dimensions : '—',
      confidence:          Math.round(t2.overall_confidence * 100),
      wearSummary:         t2.overall_wear_assessment,
      imagesAnalyzed:      t2.angles_analyzed,
      functional:          t2.functionality_assessment.appears_functional,
      functionalReasoning: t2.functionality_assessment.reasoning,
      cosmeticGrade:       t2.marketplace_assessment.cosmetic_grade,
      majorConcerns:       t2.marketplace_assessment.major_concerns,
      sellingPoints:       mp.key_selling_points,
      completeness:        t2.marketplace_assessment.completeness,
      cleanliness:         t2.marketplace_assessment.cleanliness,
      titleSuggestion:     mp.title_suggestion,
      buyerConcerns:       mp.buyer_concerns,
      wearPoints:          t2.product_specific_wear_analysis.inspection_results_by_angle,
      suitabilityWarning:  '',
      searchQuery:         '',
      barcodeBrand:        '',
    };
  }

  // User-edited values take priority; AI-detected values are fallbacks
  const eff = {
    title:         details.title         || `${ai.brand} ${ai.type}`,
    brand:         details.brand         || ai.brand,
    model:         details.model         || '',
    category:      details.category      || ai.category,
    condition:     details.condition     || ai.condition,
    material:      details.material      || ai.material,
    color:         details.color         || ai.color,
    size:          details.size          || ai.size,
    includedWithItem: details.includedWithItem ?? '',
    purchaseYearOrAge: details.purchaseYearOrAge ?? '',
    damageIssues:  details.damageIssues ?? '',
    originalPrice: details.originalPrice || '',
    notes:         details.notes         || '',
  };

  const grade = CONDITION_TO_GRADE[eff.condition] ?? ai.cosmeticGrade;

  function buildPublishPayload(sellerPrice: number): PublishListingPayload {
    const productType = (details.title || ai.type || 'Item').trim();
    const brand = (eff.brand || ai.brand || 'Unknown').trim();
    const title =
      eff.title.trim() ||
      [brand, productType].filter(Boolean).join(' ').trim() ||
      'Listing';
    const descParts = [
      brand && productType && `${brand} ${productType}.`,
      eff.material && `${eff.material}.`,
      eff.color && `Color: ${eff.color}.`,
      eff.condition && `Condition: ${eff.condition}.`,
      eff.damageIssues?.trim(),
      eff.includedWithItem?.trim() && `Included: ${eff.includedWithItem.trim()}.`,
      eff.notes?.trim(),
    ].filter((p): p is string => Boolean(p && String(p).trim()));
    const description =
      descParts.join(' ').replace(/\s+/g, ' ').trim() || title;
    return {
      analysis: {
        listing: { title, description },
        tier2: { brand, product_type: productType },
      },
      sellerPrice,
    };
  }

  const bg = useThemeColor({}, 'background');
  const cardBg = useThemeColor({}, 'card');
  const borderColor = useThemeColor({ light: '#e2e8f0', dark: '#2d3748' }, 'icon');
  const textColor = useThemeColor({}, 'text');
  const mutedColor = useThemeColor({ light: '#64748b', dark: '#94a3b8' }, 'icon');

  const barAnim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(barAnim, {
      toValue: ai.confidence / 100,
      duration: 900,
      useNativeDriver: false,
    }).start();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [barAnim, ai.confidence]);


  return (
    <View style={[styles.root, { backgroundColor: bg }]}>
      <ScrollView
        style={styles.fill}
        contentContainerStyle={{ paddingBottom: 132 + insets.bottom }}
        showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={styles.headerTitle} numberOfLines={2}>{eff.title}</Text>
          <View style={styles.headerBadgeRow}>
            <Badge color='white' label={eff.category} />
            <Badge color='white' label={eff.condition} />
            <Badge label={`Grade ${grade}`} color={GRADE_COLOR[grade] ?? 'white'} />
          </View>
          <Text style={styles.headerSub}>
            Analyzed {ai.imagesAnalyzed} image{ai.imagesAnalyzed !== 1 ? 's' : ''}
          </Text>
        </View>

        {/* ── Suitability warning ── */}
        {!!ai.suitabilityWarning && (
          <View style={[styles.suitWarn, { borderColor: '#ea580c' }]}>
            <Text style={styles.suitWarnTitle}>⚠ Not recommended for marketplace</Text>
            <Text style={[styles.suitWarnBody, { color: textColor }]}>{ai.suitabilityWarning}</Text>
          </View>
        )}

        {/* ── Price range ── */}
        <Card bg={cardBg} border={borderColor}>
          <ThemedText type="subtitle">Estimated price range</ThemedText>
          <View style={styles.priceRow}>
            <PriceBox label="Quick sale" amount={Math.round(displayPrices.quickSale)} color={mutedColor} textColor={textColor} />
            <PriceBox label="Fair market" amount={Math.round(displayPrices.fair)} color="#007AFF" textColor={textColor} featured />
            <PriceBox label="Max value" amount={Math.round(displayPrices.max)} color={mutedColor} textColor={textColor} />
          </View>
          <Text style={[styles.hint, { color: mutedColor }]}>
            {priceFromApi
              ? 'Recommended price is from live market research. Range shows min–max from comparable listings.'
              : 'List at the fair market price for the best balance of speed and return.'}
          </Text>
          {userPriceNum !== null && (
            <Text style={[styles.userAskLine, { color: '#007AFF' }]}>
              Your listing price: ${userPriceNum % 1 === 0 ? userPriceNum : userPriceNum.toFixed(2)}
            </Text>
          )}
        </Card>

        {/* ── AI Confidence ── */}
        <Card bg={cardBg} border={borderColor}>
          <View style={styles.rowBetween}>
            <ThemedText type="subtitle">AI Confidence</ThemedText>
            <Text style={[styles.confPct, { color: '#007AFF' }]}>{ai.confidence}%</Text>
          </View>
          <View style={[styles.barTrack, { backgroundColor: borderColor }]}>
            <Animated.View style={[
              styles.barFill,
              { backgroundColor: '#007AFF', width: barAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }) },
            ]} />
          </View>
          {!!ai.wearSummary && <Text style={[styles.hint, { color: mutedColor }]}>{ai.wearSummary}</Text>}
          <View style={[styles.funcRow, { borderColor }]}>
            <Text style={[styles.funcLabel, { color: textColor }]}>Functional</Text>
            <Text style={{ color: ai.functional ? '#16a34a' : '#dc2626', fontWeight: '600' }}>
              {ai.functional ? '✓ Yes' : '✗ No'}
            </Text>
          </View>
          {!!ai.functionalReasoning && <Text style={[styles.hint, { color: mutedColor }]}>{ai.functionalReasoning}</Text>}
        </Card>

        {/* ── Condition Breakdown ── */}
        <Card bg={cardBg} border={borderColor}>
          <View style={styles.rowBetween}>
            <ThemedText type="subtitle">Condition report</ThemedText>
            <View style={[styles.gradeCircle, { borderColor: GRADE_COLOR[grade] ?? '#64748b' }]}>
              <Text style={[styles.gradeText, { color: GRADE_COLOR[grade] ?? '#64748b' }]}>{grade}</Text>
            </View>
          </View>
          {ai.wearPoints.map((w, i) => (
            <View key={`${w.wear_point}-${i}`} style={[styles.wearRow, { borderBottomColor: borderColor }]}>
              <View style={styles.fill}>
                <Text style={[styles.wearPoint, { color: textColor }]}>
                  {w.wear_point.charAt(0).toUpperCase() + w.wear_point.slice(1)}
                </Text>
                <Text style={[styles.wearDetail, { color: mutedColor }]}>{w.details}</Text>
              </View>
              <Text style={[styles.wearSeverity, { color: SEVERITY_COLOR[w.severity] ?? mutedColor }]}>
                {SEVERITY_LABEL[w.severity] ?? w.severity}
              </Text>
            </View>
          ))}
          {ai.majorConcerns.length > 0 && (
            <View style={[styles.concernBox, { backgroundColor: 'rgba(234,88,12,0.08)', borderColor: '#ea580c' }]}>
              <Text style={[styles.concernTitle, { color: '#ea580c' }]}>Major concerns</Text>
              {ai.majorConcerns.map((c) => (
                <Text key={c} style={[styles.concernItem, { color: textColor }]}>· {c}</Text>
              ))}
            </View>
          )}
        </Card>

        {/* ── Marketplace Prep ── */}
        <Card bg={cardBg} border={borderColor}>
          <ThemedText type="subtitle">Marketplace listing</ThemedText>
          <View style={[styles.titleBox, { backgroundColor: borderColor }]}>
            <Text style={[styles.titleBoxLabel, { color: mutedColor }]}>Suggested title</Text>
            <Text style={[styles.titleBoxValue, { color: textColor }]}>{details.title || ai.titleSuggestion}</Text>
          </View>
          {ai.sellingPoints.length > 0 && (
            <>
              <Text style={[styles.subhead, { color: mutedColor }]}>Selling points</Text>
              {ai.sellingPoints.map((p) => (
                <Text key={p} style={[styles.bullet, { color: textColor }]}>✓  {p}</Text>
              ))}
            </>
          )}
          {ai.buyerConcerns.length > 0 && (
            <>
              <Text style={[styles.subhead, { color: mutedColor }]}>Buyer concerns</Text>
              {ai.buyerConcerns.map((c) => (
                <Text key={c} style={[styles.bullet, { color: '#ea580c' }]}>⚠  {c}</Text>
              ))}
            </>
          )}
        </Card>

        {/* ── Item Details ── */}
        <Card bg={cardBg} border={borderColor}>
          <ThemedText type="subtitle">Item details</ThemedText>
          {[
            { label: 'Brand',        value: eff.brand || '—',    edited: !!details.brand },
            { label: 'Type',         value: eff.title || '—',    edited: !!details.title },
            { label: 'Model / SKU',  value: eff.model || '—',    edited: !!details.model },
            { label: 'Material',     value: eff.material || '—', edited: !!details.material },
            { label: 'Color',        value: eff.color || '—',    edited: !!details.color },
            { label: 'Size',         value: eff.size || '—',     edited: !!details.size },
            ...(eff.damageIssues ? [{ label: 'Damage & wear', value: eff.damageIssues, edited: !!details.damageIssues }] : []),
            ...(eff.includedWithItem ? [{ label: "What's included", value: eff.includedWithItem, edited: !!details.includedWithItem }] : []),
            ...(eff.purchaseYearOrAge ? [{ label: 'Purchase year / age', value: eff.purchaseYearOrAge, edited: !!details.purchaseYearOrAge }] : []),
            ...(ai.completeness ? [{ label: 'Completeness', value: ai.completeness, edited: false }] : []),
            ...(ai.cleanliness  ? [{ label: 'Cleanliness',  value: ai.cleanliness,  edited: false }] : []),
            ...(ai.barcodeBrand ? [{ label: 'Barcode brand', value: ai.barcodeBrand, edited: false }] : []),
            ...(ai.searchQuery  ? [{ label: 'Search query',  value: ai.searchQuery,  edited: false }] : []),
          ].map(({ label, value, edited }) => (
            <View key={label} style={[styles.detailRow, { borderBottomColor: borderColor }]}>
              <Text style={[styles.detailLabel, { color: mutedColor }]}>{label}</Text>
              <View style={styles.detailValueRow}>
                {edited && <Text style={styles.editedDot}>●</Text>}
                <Text style={[styles.detailValue, { color: textColor }]}>{value}</Text>
              </View>
            </View>
          ))}
        </Card>

        {/* ── Comparable Sales ── */}
        <Card bg={cardBg} border={borderColor}>
          <ThemedText type="subtitle">Recent comparable sales</ThemedText>
          {mr?.existing_listings?.length ? (
            mr.existing_listings.map((c, i) => {
              const hasUrl = Boolean(c.url?.trim());
              const Row = hasUrl ? Pressable : View;
              const rowProps = hasUrl
                ? {
                    onPress: () => {
                      Linking.openURL(c.url).catch(() => {});
                    },
                    accessibilityRole: 'link' as const,
                    accessibilityLabel: `Open listing: ${c.title}`,
                  }
                : {};
              return (
                <Row
                  key={`${c.url}-${i}`}
                  style={[styles.compRow, { borderBottomColor: borderColor }]}
                  {...rowProps}>
                  <View style={styles.fill}>
                    <Text
                      style={[styles.compTitle, { color: hasUrl ? '#007AFF' : textColor }]}
                      numberOfLines={2}>
                      {c.title}
                    </Text>
                    <Text style={[styles.compMeta, { color: mutedColor }]} numberOfLines={1}>
                      {c.marketplace}
                      {hasUrl ? ' · Open link' : ''}
                    </Text>
                  </View>
                  <Text style={[styles.compPrice, { color: '#16a34a' }]}>${Math.round(c.price)}</Text>
                </Row>
              );
            })
          ) : (
            MOCK_COMPS.map((c, i) => (
              <View key={i} style={[styles.compRow, { borderBottomColor: borderColor }]}>
                <View style={styles.fill}>
                  <Text style={[styles.compTitle, { color: textColor }]} numberOfLines={1}>{c.title}</Text>
                  <Text style={[styles.compMeta, { color: mutedColor }]}>{c.platform} · {c.daysAgo}d ago</Text>
                </View>
                <Text style={[styles.compPrice, { color: '#16a34a' }]}>{c.price}</Text>
              </View>
            ))
          )}
        </Card>

        <Text style={[styles.disclaimer, { color: mutedColor }]}>
          {priceFromApi
            ? 'Prices from your pricing service. Indicative only — verify before listing.'
            : isRealData
              ? 'AI analysis complete. Connect the /estimate service for live price ranges.'
              : 'Showing demo data — connect to the live API for real estimates.'}
        </Text>
      </ScrollView>

      {/* ── Bottom actions ── */}
      <View style={[styles.barWrap, { paddingBottom: Math.max(insets.bottom, 12), backgroundColor: bg, borderTopColor: borderColor }]}>
        <TextInput
          style={[styles.userPriceInpTop, { borderColor, color: textColor, backgroundColor: cardBg }]}
          placeholder="Your price ($)"
          placeholderTextColor={mutedColor}
          value={userListingPrice}
          onChangeText={setUserListingPrice}
          keyboardType="decimal-pad"
          returnKeyType="done"
        />
        <View style={styles.barActionsRow}>
          <Pressable
            style={({ pressed }) => [styles.btnSec, styles.barActionBtn, pressed && styles.pressed]}
            onPress={() => router.back()}>
            <ThemedText type="defaultSemiBold" style={styles.btnSecLbl}>Edit details</ThemedText>
          </Pressable>
          <Pressable
            style={({ pressed }) => [
              styles.barActionBtn,
              hasPriceInput ? styles.btnPub : styles.btnSec,
              (pressed || publishing) && styles.pressed,
              publishing && styles.btnPubDisabled,
            ]}
            disabled={publishing}
            onPress={async () => {
              if (hasPriceInput) {
                if (userPriceNum === null) {
                  Alert.alert('Invalid price', 'Enter a valid dollar amount.');
                  return;
                }
                setPublishing(true);
                try {
                  const payload = buildPublishPayload(userPriceNum);
                  const out = await publishListing(payload);
                  if (!out.ok) {
                    Alert.alert(
                      'Publish failed',
                      out.message || `Server returned ${out.status || 'error'}. Check Metro logs for [publish].`
                    );
                    return;
                  }
                  resetScanSession();
                  // Group (tabs) is not part of the URL — home is /
                  router.replace('/' as Href);
                } finally {
                  setPublishing(false);
                }
                return;
              }
              setUserListingPrice('');
            }}>
            {publishing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <ThemedText
                type="defaultSemiBold"
                style={hasPriceInput ? styles.btnPubLbl : styles.btnSecLbl}>
                {hasPriceInput ? 'Publish' : 'Cancel'}
              </ThemedText>
            )}
          </Pressable>
        </View>
      </View>
    </View>
  );
}

function Card({ bg, border, children }: { bg: string; border: string; children: React.ReactNode }) {
  return (
    <View style={[styles.card, { backgroundColor: bg, borderColor: border }]}>
      {children}
    </View>
  );
}

function Badge({ label, color = '#007AFF' }: { label: string; color?: string }) {
  return (
    <View style={[styles.badge, { borderColor: color }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
    </View>
  );
}

function PriceBox({ label, amount, color, textColor, featured }: {
  label: string; amount: number; color: string; textColor: string; featured?: boolean;
}) {
  return (
    <View style={[styles.priceBox, featured && styles.priceBoxFeatured]}>
      <Text style={[styles.priceAmt, { color }]}>${amount}</Text>
      <Text style={[styles.priceLbl, { color: textColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  fill: { flex: 1 },

  // Header
  header: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 28,
    gap: 8,
  },
  headerEyebrow: { fontSize: 11, color: 'rgba(255,255,255,0.7)', letterSpacing: 1.2, textTransform: 'uppercase' },
  headerTitle: { fontSize: 26, fontWeight: '700', color: '#fff' },
  headerBadgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  headerSub: { fontSize: 12, color: 'rgba(255,255,255,0.65)', marginTop: 2 },

  // Badge
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 3,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  badgeText: { fontSize: 11, fontWeight: '600', color: '#fff' },

  // Card
  card: { marginHorizontal: 16, marginTop: 12, borderRadius: 16, padding: 16, borderWidth: 1, gap: 10 },

  // Price
  priceRow: { flexDirection: 'row', justifyContent: 'space-between' },
  priceBox: { flex: 1, alignItems: 'center', paddingVertical: 10 },
  priceBoxFeatured: { backgroundColor: 'rgba(0,122,255,0.08)', borderRadius: 12, borderWidth: 1.5, borderColor: '#007AFF' },
  priceAmt: { fontSize: 22, fontWeight: '700' },
  priceLbl: { fontSize: 12, marginTop: 3 },

  // Confidence
  rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  confPct: { fontSize: 22, fontWeight: '700' },
  barTrack: { height: 8, borderRadius: 4, overflow: 'hidden' },
  barFill: { height: 8, borderRadius: 4 },
  funcRow: { flexDirection: 'row', justifyContent: 'space-between', paddingTop: 8, borderTopWidth: StyleSheet.hairlineWidth },
  funcLabel: { fontSize: 14 },

  // Wear
  gradeCircle: {
    width: 38, height: 38, borderRadius: 19, borderWidth: 2,
    alignItems: 'center', justifyContent: 'center',
  },
  gradeText: { fontSize: 18, fontWeight: '800' },
  wearRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, gap: 10,
  },
  wearPoint: { fontSize: 14, fontWeight: '600' },
  wearDetail: { fontSize: 12, marginTop: 2, lineHeight: 17 },
  wearSeverity: { fontSize: 12, fontWeight: '600', marginTop: 2 },
  concernBox: { borderWidth: 1, borderRadius: 10, padding: 12, gap: 4 },
  concernTitle: { fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  concernItem: { fontSize: 13 },

  // Marketplace
  titleBox: { borderRadius: 10, padding: 12, gap: 4 },
  titleBoxLabel: { fontSize: 11, fontWeight: '600', letterSpacing: 0.5, textTransform: 'uppercase' },
  titleBoxValue: { fontSize: 14, lineHeight: 20 },
  subhead: { fontSize: 12, fontWeight: '600', letterSpacing: 0.3, textTransform: 'uppercase', marginTop: 4 },
  bullet: { fontSize: 14, lineHeight: 22 },

  // Details
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 9, borderBottomWidth: StyleSheet.hairlineWidth },
  detailLabel: { fontSize: 14 },
  detailValueRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1, justifyContent: 'flex-end' },
  detailValue: { fontSize: 14, fontWeight: '500', textAlign: 'right' },
  editedDot: { fontSize: 7, color: '#007AFF' },

  // Comps
  compRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, gap: 10 },
  compTitle: { fontSize: 14 },
  compMeta: { fontSize: 12, marginTop: 2 },
  compPrice: { fontSize: 16, fontWeight: '600' },

  suitWarn: {
    marginHorizontal: 16, marginTop: 12, borderRadius: 14, padding: 14,
    borderWidth: 1, backgroundColor: 'rgba(234,88,12,0.07)', gap: 6,
  },
  suitWarnTitle: { fontSize: 13, fontWeight: '700', color: '#ea580c' },
  suitWarnBody:  { fontSize: 13, lineHeight: 18 },

  hint: { fontSize: 13, lineHeight: 18 },
  userAskLine: { fontSize: 15, fontWeight: '600', marginTop: 6 },
  disclaimer: { fontSize: 11, lineHeight: 16, marginHorizontal: 16, marginTop: 16, marginBottom: 8, textAlign: 'center' },

  // Bottom bar
  barWrap: {
    position: 'absolute', left: 0, right: 0, bottom: 0,
    paddingHorizontal: 16, paddingTop: 12, gap: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  userPriceInpTop: {
    width: '100%',
    borderWidth: 1.5,
    borderRadius: 999,
    paddingVertical: 14,
    paddingHorizontal: 18,
    fontSize: 17,
    fontWeight: '500',
  },
  barActionsRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'stretch',
  },
  barActionBtn: { flex: 1 },
  btnSec: { paddingVertical: 12, borderRadius: 999, borderWidth: 1.5, borderColor: '#007AFF', alignItems: 'center', justifyContent: 'center' },
  btnSecLbl: { color: '#007AFF', fontSize: 15 },
  btnPub: {
    paddingVertical: 12,
    borderRadius: 999,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPubLbl: { color: '#fff', fontSize: 15 },
  btnPubDisabled: { opacity: 0.75 },
  pressed: { opacity: 0.88 },
});
