import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useScanImages } from '@/contexts/scan-images-context';
import type { DetectionResult } from '@/services/api';
import { analyzeImages, detectImage, FLAGS } from '@/services/api';
import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { MAX_SCAN_IMAGES } from './scan-constants';
import { scanStyles } from './scan-styles';

type DetectStatus = 'loading' | DetectionResult | 'failed';

const BADGE: Record<string, { label: string; bg: string }> = {
  ok:       { label: '✓', bg: '#16a34a' },
  multi:    { label: '⚠', bg: '#ca8a04' },
  none:     { label: '✗', bg: '#dc2626' },
  loading:  { label: '…', bg: '#64748b' },
  failed:   { label: '?', bg: '#94a3b8' },
};

function badgeKey(status: DetectStatus): keyof typeof BADGE {
  if (status === 'loading') return 'loading';
  if (status === 'failed')  return 'failed';
  if (status.error)         return 'failed';
  if (status.has_exactly_one_object) return 'ok';
  if (status.object_count === 0)     return 'none';
  return 'multi';
}

export default function ScanCamera() {
  const router = useRouter();
  const { images, setImages, barcode, setBarcode, setAnalysisResult } = useScanImages();
  const [permission, requestPermission] = ImagePicker.useCameraPermissions();
  const [opening, setOpening] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [detections, setDetections] = useState<Record<string, DetectStatus>>({});
  const [analyzing, setAnalyzing] = useState(false);

  // Run detection on a batch of newly added URIs
  const runDetect = useCallback((uris: string[]) => {
    if (!FLAGS.objectDetection) return;

    setDetections((prev) => {
      const next = { ...prev };
      for (const uri of uris) next[uri] = 'loading';
      return next;
    });

    for (const uri of uris) {
      detectImage(uri).then((result) => {
        setDetections((prev) => ({ ...prev, [uri]: result ?? 'failed' }));
      });
    }
  }, []);

  function mergePickedUris(uris: string[]) {
    const added: string[] = [];
    setImages((prev) => {
      const room = MAX_SCAN_IMAGES - prev.length;
      if (room <= 0) return prev;
      const slice = uris.slice(0, room);
      added.push(...slice);
      return [...prev, ...slice];
    });
    // Detect after next tick so `added` is populated
    setTimeout(() => { if (added.length) runDetect(added); }, 0);
  }

  function removeAt(index: number) {
    setImages((prev) => {
      const uri = prev[index];
      if (uri) setDetections((d) => { const n = { ...d }; delete n[uri]; return n; });
      return prev.filter((_, i) => i !== index);
    });
  }

  async function runLibraryPicker(maxPick: number) {
    if (maxPick <= 0) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.85,
      allowsMultipleSelection: true,
      selectionLimit: maxPick,
    });
    if (!result.canceled && result.assets?.length) {
      mergePickedUris(result.assets.map((a) => a.uri).filter(Boolean));
    }
  }

  async function openPhotoLibrary() {
    setNotice(null);
    const slotsLeft = MAX_SCAN_IMAGES - images.length;
    if (slotsLeft <= 0) { setNotice(`Max ${MAX_SCAN_IMAGES} photos. Remove one to add more.`); return; }
    setOpening(true);
    try { await runLibraryPicker(slotsLeft); } finally { setOpening(false); }
  }

  async function openCamera() {
    setNotice(null);
    const slotsLeft = MAX_SCAN_IMAGES - images.length;
    if (slotsLeft <= 0) { setNotice(`Max ${MAX_SCAN_IMAGES} photos. Remove one to add more.`); return; }
    if (permission && !permission.granted) {
      const updated = await requestPermission();
      if (!updated.granted) return;
    }
    setOpening(true);
    try {
      try {
        const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.85 });
        if (!result.canceled && result.assets[0]?.uri) {
          mergePickedUris([result.assets[0].uri]);
        }
      } catch {
        setNotice('Camera unavailable on simulator — picking from library instead.');
        await runLibraryPicker(slotsLeft);
      }
    } finally { setOpening(false); }
  }

  if (!permission) {
    return <ThemedView style={scanStyles.centered}><ActivityIndicator /></ThemedView>;
  }

  const atLimit = images.length >= MAX_SCAN_IMAGES;

  // Per-image status helpers
  const isLoading = (uri: string) => detections[uri] === 'loading';
  const isOk      = (uri: string) => {
    const s = detections[uri];
    return typeof s === 'object' && s !== null && s.has_exactly_one_object;
  };

  const anyLoading     = images.some(isLoading);
  const warningCount   = images.filter((uri) => {
    const s = detections[uri];
    if (!s || s === 'loading') return false;
    return s === 'failed' || (typeof s === 'object' && !s.has_exactly_one_object);
  }).length;
  const estimateBlocked = FLAGS.objectDetection && (anyLoading || images.some((uri) => !isOk(uri)));

  return (
    <>
    <ScrollView
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={scanStyles.scrollContent}
      showsVerticalScrollIndicator={false}>
      <ThemedView style={scanStyles.inner}>
        <ThemedText type="title">Scan</ThemedText>
        <ThemedText style={scanStyles.subtitle}>
          Add up to {MAX_SCAN_IMAGES} photos for a price estimate.
        </ThemedText>
        <ThemedText style={scanStyles.countLabel}>
          {images.length} / {MAX_SCAN_IMAGES}
        </ThemedText>

        {notice ? <ThemedText style={scanStyles.subtitle}>{notice}</ThemedText> : null}

        <View style={scanStyles.buttonRow}>
          <Pressable
            style={({ pressed }) => [scanStyles.scanButton, pressed && scanStyles.scanButtonPressed]}
            onPress={openCamera}
            disabled={opening || atLimit}>
            <ThemedText type="defaultSemiBold" style={scanStyles.scanButtonLabel}>
              {opening ? 'Working…' : 'Take photo'}
            </ThemedText>
          </Pressable>
          <View style={scanStyles.buttonCol}>
          <Pressable
            style={({ pressed }) => [scanStyles.secondaryButton, pressed && scanStyles.secondaryButtonPressed]}
            onPress={openPhotoLibrary}
            disabled={opening || atLimit}>
            <ThemedText type="defaultSemiBold" style={scanStyles.secondaryButtonLabel}>
              Add from library
            </ThemedText>
          </Pressable>
          <Pressable
            style={({ pressed }) => [scanStyles.secondaryButton, pressed && scanStyles.secondaryButtonPressed]}
            onPress={() => router.push('/barcode-scan')}
            disabled={opening}>
            <ThemedText type="defaultSemiBold" style={scanStyles.secondaryButtonLabel}>
              Scan barcode  ▦
            </ThemedText>
          </Pressable>
          </View>
        </View>

        {barcode && (
          <View style={scanStyles.barcodeBadge}>
            <View style={scanStyles.barcodeBadgeLeft}>
              <Text style={scanStyles.barcodeBadgeType}>{barcode.type.toUpperCase()}</Text>
              <Text style={scanStyles.barcodeBadgeValue} numberOfLines={2}>{barcode.value}</Text>
            </View>
            <Pressable onPress={() => setBarcode(null)} style={scanStyles.barcodeRemove}>
              <Text style={scanStyles.barcodeRemoveLbl}>×</Text>
            </Pressable>
          </View>
        )}

        {images.length > 0 && (
          <>
            <View style={scanStyles.previewWrap}>
              <View style={scanStyles.photosHeader}>
                <ThemedText type="subtitle">Photos</ThemedText>
                {warningCount > 0 && (
                  <Text style={scanStyles.warnNote}>
                    {warningCount} photo{warningCount > 1 ? 's' : ''} may not show a clear single item
                  </Text>
                )}
              </View>

              <View style={scanStyles.thumbnailGrid}>
                {images.map((uri, index) => {
                  const status = detections[uri];
                  const key = status ? badgeKey(status) : null;
                  const badge = key ? BADGE[key] : null;

                  return (
                    <View key={`${index}-${uri}`} style={scanStyles.thumbnailWrap}>
                      <Image source={{ uri }} style={scanStyles.thumbnail} contentFit="cover" />

                      {/* Detection badge — bottom-left */}
                      {badge && (
                        <View style={[scanStyles.detectBadge, { backgroundColor: badge.bg }]}>
                          {status === 'loading'
                            ? <ActivityIndicator size="small" color="#fff" style={{ transform: [{ scale: 0.5 }] }} />
                            : <Text style={scanStyles.detectBadgeLabel}>{badge.label}</Text>}
                        </View>
                      )}

                      {/* Remove button — top-right */}
                      <Pressable
                        onPress={() => removeAt(index)}
                        style={scanStyles.removeThumb}
                        accessibilityRole="button"
                        accessibilityLabel="Remove photo">
                        <ThemedText style={scanStyles.removeThumbLabel}>×</ThemedText>
                      </Pressable>
                    </View>
                  );
                })}
              </View>
            </View>

            <Pressable
              style={({ pressed }) => [
                scanStyles.scanButton,
                pressed && !estimateBlocked && scanStyles.scanButtonPressed,
                estimateBlocked && scanStyles.scanButtonDisabled,
              ]}
              onPress={async () => {
                setAnalyzing(true);
                try {
                  if (FLAGS.productAnalysis) {
                    const result = await analyzeImages(images);
                    setAnalysisResult(result);
                  } else {
                    setAnalysisResult(null);
                  }
                } finally {
                  setAnalyzing(false);
                  router.push('/scan-review');
                }
              }}
              disabled={estimateBlocked || analyzing}>
              <ThemedText type="defaultSemiBold" style={scanStyles.scanButtonLabel}>
                {anyLoading ? 'Checking photos…' : 'Continue'}
              </ThemedText>
            </Pressable>
          </>
        )}
      </ThemedView>
    </ScrollView>

    <Modal visible={analyzing} transparent animationType="fade">
      <View style={analyzeOverlay.backdrop}>
        <View style={analyzeOverlay.card}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={analyzeOverlay.label}>Analyzing photos…</Text>
          <Text style={analyzeOverlay.sub}>This may take a few seconds</Text>
        </View>
      </View>
    </Modal>
    </>
  );
}

const analyzeOverlay = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingVertical: 36,
    paddingHorizontal: 48,
    alignItems: 'center',
    gap: 12,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 12,
  },
  label: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111',
  },
  sub: {
    fontSize: 13,
    color: '#666',
  },
});
