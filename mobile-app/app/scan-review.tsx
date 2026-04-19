import { ThemedText } from '@/components/themed-text';
import { useScanImages } from '@/contexts/scan-images-context';
import { useThemeColor } from '@/hooks/use-theme-color';
import type { AnalysisResponse } from '@/services/api';
import { FLAGS, mergeReviewIntoAnalysis, postEstimate } from '@/services/api';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export type ProductDetails = {
  title: string;
  brand: string;
  model: string;
  category: string;
  condition: string;
  material: string;
  color: string;
  size: string;
  /** Box, accessories, manuals — affects resale comps */
  includedWithItem: string;
  /** Purchase year or rough age (e.g. "2022" or "~2 years") */
  purchaseYearOrAge: string;
  /** Scratches, dents, issues — pre-filled from AI, user edits */
  damageIssues: string;
  originalPrice: string;
  notes: string;
};

const CONDITIONS = ['New', 'Like new', 'Good', 'Fair', 'Poor'];
const COLS = 3;
const GAP = 8;
const CARD_PAD = 16;
const SCREEN_PAD = 16;

const EMPTY: ProductDetails = {
  title: '',
  brand: '',
  model: '',
  category: '',
  condition: '',
  material: '',
  color: '',
  size: '',
  includedWithItem: '',
  purchaseYearOrAge: '',
  damageIssues: '',
  originalPrice: '',
  notes: '',
};

function formatPhysicalDamage(
  d: AnalysisResponse['tier2']['general_physical_damage'] | undefined
): string {
  if (!d) return '';
  const lines: string[] = [];
  const parts: [string, string[] | undefined][] = [
    ['Scratches', d.scratches],
    ['Dents', d.dents],
    ['Scuffs', d.scuffs],
    ['Discoloration', d.discoloration],
    ['Cracks or chips', d.cracks_or_chips],
    ['Other damage', d.other_damage],
  ];
  for (const [label, arr] of parts) {
    if (arr?.length) lines.push(`${label}: ${arr.join('; ')}`);
  }
  return lines.join('\n');
}

function seedDamageFromAnalysis(r: AnalysisResponse): string {
  const t2 = r.tier2;
  const chunks: string[] = [];
  const phys = formatPhysicalDamage(t2.general_physical_damage);
  if (phys) chunks.push(phys);
  for (const c of t2.marketplace_assessment?.major_concerns ?? []) {
    chunks.push(`• ${c}`);
  }
  for (const c of r.listing.buyer_concerns ?? []) {
    chunks.push(`• ${c}`);
  }
  for (const w of t2.product_specific_wear_analysis?.inspection_results ?? []) {
    chunks.push(`• ${w.wear_point}: ${w.details}`);
  }
  return [...new Set(chunks)].join('\n').trim();
}

function detailsFromAnalysis(r: AnalysisResponse): ProductDetails {
  const t2 = r.tier2;
  const prod = r.product;
  const rawCond = t2.condition ?? prod?.condition ?? '';
  const CONDITIONS_LIST = ['New', 'Like new', 'Good', 'Fair', 'Poor'];
  const condition = CONDITIONS_LIST.find(
    (c) => c.toLowerCase() === rawCond.toLowerCase()
  ) ?? rawCond;

  return {
    ...EMPTY,
    title:    t2.product_type ?? prod?.type ?? '',
    brand:    t2.brand ?? prod?.brand ?? r.barcode_lookup?.brand ?? '',
    model:    t2.barcode_sku_found ?? r.barcode_lookup?.barcode ?? '',
    category: r.tier1.category,
    condition,
    material: t2.material ?? prod?.material ?? '',
    color:    t2.color ?? prod?.color ?? '',
    damageIssues: seedDamageFromAnalysis(r),
  };
}

export default function ScanReviewScreen() {
  const {
    images,
    barcode,
    analysisResult,
    setAnalysisResult,
    setEstimateResult,
    resetScanSession,
  } = useScanImages();
  const [estimateLoading, setEstimateLoading] = useState(false);
  const router = useRouter();
  const params = useLocalSearchParams<{ details?: string }>();
  const insets = useSafeAreaInsets();
  const { width: W } = useWindowDimensions();

  const tileSize = (W - SCREEN_PAD * 2 - CARD_PAD * 2 - GAP * (COLS - 1)) / COLS;

  const bg = useThemeColor({}, 'background');
  const cardBg = useThemeColor({}, 'card');
  const inputBg = useThemeColor({ light: '#f7f9fb', dark: '#0f1117' }, 'background');
  const borderColor = useThemeColor({ light: '#e2e8f0', dark: '#2d3748' }, 'icon');
  const textColor = useThemeColor({}, 'text');
  const mutedColor = useThemeColor({ light: '#64748b', dark: '#94a3b8' }, 'icon');
  const chipInactive = useThemeColor({ light: '#f0f4f8', dark: '#252932' }, 'background');

  const [details, setDetails] = useState<ProductDetails>(() => {
    // Priority 1: manually passed params (coming back from estimate "Edit details")
    if (params.details) {
      try { return { ...EMPTY, ...JSON.parse(params.details) }; }
      catch { /* fall through */ }
    }
    // Priority 2: pre-fill from AI analysis result
    if (analysisResult) {
      return detailsFromAnalysis(analysisResult);
    }
    return EMPTY;
  });

  useEffect(() => {
    if (images.length === 0) router.replace('/(tabs)/scan');
  }, [images.length, router]);

  if (images.length === 0) return null;

  function set(k: keyof ProductDetails, v: string) {
    setDetails((p) => ({ ...p, [k]: v }));
  }

  const inp = [styles.input, { backgroundColor: inputBg, borderColor, color: textColor }];

  const bottomH = 50 + 12 + Math.max(insets.bottom, 12);

  return (
    <View style={[styles.root, { backgroundColor: bg }]}>
      <KeyboardAvoidingView
        style={styles.fill}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={90}>
        <ScrollView
          style={styles.fill}
          contentContainerStyle={{ paddingBottom: bottomH + 16 }}
          keyboardShouldPersistTaps="handled"
          alwaysBounceVertical>

          {/* Photos */}
          <View style={[styles.card, { backgroundColor: cardBg, margin: SCREEN_PAD, marginBottom: 0 }]}>
            <ThemedText type="subtitle">
              {images.length} {images.length === 1 ? 'photo' : 'photos'}
            </ThemedText>
            <View style={styles.grid}>
              {images.map((uri, i) => (
                <Image
                  key={`${i}-${uri}`}
                  source={{ uri }}
                  style={{ width: tileSize, height: tileSize, borderRadius: 10 }}
                  contentFit="cover"
                />
              ))}
            </View>
          </View>

          {/* Barcode card */}
          {barcode && (
            <View style={[styles.card, styles.barcodeCard, { margin: SCREEN_PAD, marginTop: GAP, borderColor }]}>
              <Text style={[styles.barcodeType, { color: '#0a7ea4' }]}>{barcode.type.toUpperCase()}</Text>
              <Text style={[styles.barcodeValue, { color: textColor }]}>{barcode.value}</Text>
            </View>
          )}

          {/* Details form */}
          <View style={[styles.card, { backgroundColor: cardBg, margin: SCREEN_PAD, marginTop: GAP }]}>
            <ThemedText type="subtitle">Item details</ThemedText>
            {analysisResult ? (
              <View style={styles.aiBanner}>
                <Text style={styles.aiBannerText}>✦ Pre-filled by AI — review and edit as needed</Text>
              </View>
            ) : (
              <Text style={[styles.hint, { color: mutedColor }]}>
                Optional — more info = better estimate
              </Text>
            )}

            {/* Item name */}
            <Text style={[styles.lbl, { color: textColor }]}>Item name / type</Text>
            <TextInput
              style={inp} placeholder="e.g. Nike Low-Top Sneaker, iPhone 14 Pro…"
              placeholderTextColor={mutedColor} value={details.title}
              onChangeText={(v) => set('title', v)} returnKeyType="next" />

            {/* Brand | Model */}
            <View style={styles.row}>
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Brand</Text>
                <TextInput style={inp} placeholder="Nike, Apple…"
                  placeholderTextColor={mutedColor} value={details.brand}
                  onChangeText={(v) => set('brand', v)} returnKeyType="next" />
              </View>
              <View style={{ width: 10 }} />
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Model / SKU</Text>
                <TextInput style={inp} placeholder="Optional"
                  placeholderTextColor={mutedColor} value={details.model}
                  onChangeText={(v) => set('model', v)} returnKeyType="next" />
              </View>
            </View>

            {/* Category | Size */}
            <View style={styles.row}>
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Category</Text>
                <TextInput style={inp} placeholder="Clothing, Electronics…"
                  placeholderTextColor={mutedColor} value={details.category}
                  onChangeText={(v) => set('category', v)} returnKeyType="next" />
              </View>
              <View style={{ width: 10 }} />
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Size</Text>
                <TextInput style={inp} placeholder="e.g. UK 10, M, 15"
                  placeholderTextColor={mutedColor} value={details.size}
                  onChangeText={(v) => set('size', v)} returnKeyType="next" />
              </View>
            </View>

            {/* Material | Color */}
            <View style={styles.row}>
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Material</Text>
                <TextInput style={inp} placeholder="Leather, Plastic…"
                  placeholderTextColor={mutedColor} value={details.material}
                  onChangeText={(v) => set('material', v)} returnKeyType="next" />
              </View>
              <View style={{ width: 10 }} />
              <View style={styles.fill}>
                <Text style={[styles.lbl, { color: textColor }]}>Color</Text>
                <TextInput style={inp} placeholder="e.g. White / Black"
                  placeholderTextColor={mutedColor} value={details.color}
                  onChangeText={(v) => set('color', v)} returnKeyType="next" />
              </View>
            </View>

            {/* Condition chips */}
            <Text style={[styles.lbl, { color: textColor }]}>Condition</Text>
            <View style={styles.chipRow}>
              {CONDITIONS.map((c) => {
                const active = details.condition === c;
                return (
                  <Pressable
                    key={c}
                    onPress={() => set('condition', active ? '' : c)}
                    style={[styles.chip, { backgroundColor: active ? '#007AFF' : chipInactive }]}>
                    <Text style={[styles.chipLbl, { color: active ? '#fff' : textColor }]}>{c}</Text>
                  </Pressable>
                );
              })}
            </View>

            {/* Damage / wear — pricing-critical */}
            <Text style={[styles.lbl, { color: textColor }]}>Damage & wear</Text>
            <TextInput
              style={[inp, styles.textArea, styles.textAreaSm]}
              placeholder="Scratches, dents, missing parts, battery health…"
              placeholderTextColor={mutedColor}
              value={details.damageIssues}
              onChangeText={(v) => set('damageIssues', v)}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />

            {/* What's included */}
            <Text style={[styles.lbl, { color: textColor }]}>What's included</Text>
            <Text style={[styles.fieldHint, { color: mutedColor }]}>
              Box, charger, manuals, accessories — affects price
            </Text>
            <TextInput
              style={[inp, styles.textArea, styles.textAreaSm]}
              placeholder="e.g. Original box, charging cable, no manual"
              placeholderTextColor={mutedColor}
              value={details.includedWithItem}
              onChangeText={(v) => set('includedWithItem', v)}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />

            {/* Purchase year / age */}
            <Text style={[styles.lbl, { color: textColor }]}>Purchase year or age</Text>
            <TextInput
              style={inp}
              placeholder="e.g. 2022, or “~3 years old”"
              placeholderTextColor={mutedColor}
              value={details.purchaseYearOrAge}
              onChangeText={(v) => set('purchaseYearOrAge', v)}
              returnKeyType="next"
            />

            {/* Original price */}
            <Text style={[styles.lbl, { color: textColor }]}>Original price ($)</Text>
            <TextInput style={inp} placeholder="e.g. 180"
              placeholderTextColor={mutedColor} value={details.originalPrice}
              onChangeText={(v) => set('originalPrice', v)}
              keyboardType="decimal-pad" returnKeyType="next" />

            {/* Notes */}
            <Text style={[styles.lbl, { color: textColor }]}>Additional notes</Text>
            <Text style={[styles.fieldHint, { color: mutedColor }]}>
              Receipt, warranty, why you’re selling — optional
            </Text>
            <TextInput
              style={[inp, styles.textArea]}
              placeholder="Anything else the pricing step should know"
              placeholderTextColor={mutedColor} value={details.notes}
              onChangeText={(v) => set('notes', v)}
              multiline numberOfLines={4} textAlignVertical="top" />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Bottom bar */}
      <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 12), backgroundColor: bg, borderTopColor: borderColor }]}>
        <Pressable
          style={({ pressed }) => [styles.btnSec, pressed && styles.pressed]}
          onPress={() => {
            resetScanSession();
            router.replace('/(tabs)/scan');
          }}>
          <ThemedText type="defaultSemiBold" style={styles.btnSecLbl}>Scan again</ThemedText>
        </Pressable>
        <Pressable
          style={({ pressed }) => [
            styles.btnPri,
            pressed && !estimateLoading && styles.pressed,
            estimateLoading && styles.btnPriDisabled,
          ]}
          disabled={estimateLoading}
          onPress={async () => {
            if (!analysisResult) {
              Alert.alert('No analysis', 'Go back to scan and add photos, then tap Continue.');
              return;
            }
            const merged = mergeReviewIntoAnalysis(analysisResult, details);
            if (FLAGS.pricingEstimate) {
              setEstimateLoading(true);
              try {
                const result = await postEstimate(merged);
                if (!result) {
                  Alert.alert(
                    'Estimate failed',
                    'Could not reach the pricing server. Check it is running and ESTIMATE_BASE matches your network.'
                  );
                  return;
                }
                setEstimateResult(result);
                const nextAnalysis = result.analysis as AnalysisResponse;
                if (nextAnalysis) setAnalysisResult(nextAnalysis);
              } finally {
                setEstimateLoading(false);
              }
            } else {
              setEstimateResult(null);
            }
            router.push({ pathname: '/estimate', params: { details: JSON.stringify(details) } });
          }}>
          <ThemedText type="defaultSemiBold" style={styles.btnPriLbl}>
            {estimateLoading ? 'Getting estimate…' : 'Get estimate'}
          </ThemedText>
        </Pressable>
      </View>

      <Modal visible={estimateLoading} transparent animationType="fade">
        <View style={styles.estimateOverlay}>
          <View style={styles.estimateCard}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.estimateOverlayLbl}>Fetching price estimate…</Text>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  fill: { flex: 1 },
  card: { borderRadius: 16, padding: CARD_PAD },
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: GAP },
  row: { flexDirection: 'row', marginTop: 12 },
  lbl: { fontSize: 13, letterSpacing: 0.2, marginTop: 12, marginBottom: 4 },
  hint: { fontSize: 13, lineHeight: 18, marginBottom: 4 },
  aiBanner: {
    backgroundColor: 'rgba(0,122,255,0.08)',
    borderRadius: 8,
    paddingVertical: 7,
    paddingHorizontal: 10,
    marginBottom: 4,
  },
  aiBannerText: { fontSize: 12, color: '#007AFF', fontWeight: '600' as const },
  fieldHint: { fontSize: 12, lineHeight: 16, marginBottom: 6, marginTop: -4 },
  input: { borderWidth: 1, borderRadius: 10, paddingVertical: 10, paddingHorizontal: 12, fontSize: 15 },
  textArea: { minHeight: 90, paddingTop: 10 },
  textAreaSm: { minHeight: 72 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 6, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20 },
  chipLbl: { fontSize: 14 },
  bar: {
    position: 'absolute', left: 0, right: 0, bottom: 0,
    flexDirection: 'row', gap: 12, paddingHorizontal: 20, paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  btnPri: { flex: 1, backgroundColor: '#007AFF', paddingVertical: 14, borderRadius: 999, alignItems: 'center' },
  btnPriDisabled: { opacity: 0.65 },
  btnPriLbl: { color: '#fff' },
  estimateOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  estimateCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    paddingVertical: 28,
    paddingHorizontal: 32,
    alignItems: 'center',
    gap: 14,
  },
  estimateOverlayLbl: { fontSize: 15, fontWeight: '600', color: '#111' },
  btnSec: { flex: 1, paddingVertical: 12, borderRadius: 999, borderWidth: 1.5, borderColor: '#007AFF', alignItems: 'center' },
  btnSecLbl: { color: '#007AFF', fontSize: 16 },
  pressed: { opacity: 0.88 },
  barcodeCard: {
    borderWidth: 1,
    backgroundColor: '#edf7fb',
    gap: 4,
  },
  barcodeType: {
    fontSize: 10,
    fontWeight: '700' as const,
    letterSpacing: 1.1,
    color: '#007AFF',
  },
  barcodeValue: {
    fontSize: 15,
    fontWeight: '500' as const,
  },
});
