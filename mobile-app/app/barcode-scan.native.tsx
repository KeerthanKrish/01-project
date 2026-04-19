import { useScanImages } from '@/contexts/scan-images-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

type ScanState = 'scanning' | 'detected' | 'done';

export default function BarcodeScanScreen() {
  const router = useRouter();
  const { setBarcode } = useScanImages();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanState, setScanState] = useState<ScanState>('scanning');
  const [detected, setDetected] = useState<{ type: string; value: string } | null>(null);

  function handleBarcodeScanned({ type, data }: { type: string; data: string }) {
    if (scanState !== 'scanning') return;
    setScanState('detected');
    setDetected({ type, value: data });
  }

  function confirmScan() {
    if (!detected) return;
    setBarcode({ type: detected.type, value: detected.value });
    setScanState('done');
    router.back();
  }

  function rescan() {
    setDetected(null);
    setScanState('scanning');
  }

  if (!permission) {
    return <View style={[styles.centered, styles.bg]} />;
  }

  if (!permission.granted) {
    return (
      <View style={[styles.centered, styles.bg]}>
        <Text style={styles.whiteText}>Camera permission is required to scan barcodes.</Text>
        <Pressable style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnLbl}>Grant permission</Text>
        </Pressable>
        <Pressable style={[styles.btn, styles.btnOutline]} onPress={() => router.back()}>
          <Text style={[styles.btnLbl, styles.btnOutlineLbl]}>Go back</Text>
        </Pressable>
      </View>
    );
  }

  const isDetected = scanState === 'detected' || scanState === 'done';

  return (
    <View style={styles.root}>
      <CameraView
        style={StyleSheet.absoluteFill}
        facing="back"
        onBarcodeScanned={scanState === 'scanning' ? handleBarcodeScanned : undefined}
        barcodeScannerSettings={{
          barcodeTypes: [
            'qr', 'ean13', 'ean8', 'upc_a', 'upc_e',
            'code128', 'code39', 'code93', 'datamatrix', 'pdf417', 'aztec',
          ],
        }}
      />

      {/* Viewfinder frame — corners turn green when a barcode is locked */}
      <View style={styles.viewfinderContainer} pointerEvents="none">
        <View style={styles.viewfinder}>
          <View style={[styles.corner, styles.tl, isDetected && styles.cornerDetected]} />
          <View style={[styles.corner, styles.tr, isDetected && styles.cornerDetected]} />
          <View style={[styles.corner, styles.bl, isDetected && styles.cornerDetected]} />
          <View style={[styles.corner, styles.br, isDetected && styles.cornerDetected]} />
        </View>
      </View>

      {/* Top instruction */}
      <View style={styles.topHint}>
        <Text style={styles.hintText}>
          {isDetected ? 'Barcode detected — aim and capture' : 'Point camera at a barcode or QR code'}
        </Text>
      </View>

      {/* Bottom bar */}
      <View style={styles.bottomBar}>
        {isDetected ? (
          <>
            <View style={styles.detectedCard}>
              <Text style={styles.detectedType}>{detected?.type?.toUpperCase()}</Text>
              <Text style={styles.detectedValue} numberOfLines={3}>{detected?.value}</Text>
            </View>
            <View style={styles.btnRow}>
              <Pressable
                style={[styles.btn, styles.btnOutline]}
                onPress={rescan}
                disabled={scanState === 'done'}>
                <Text style={[styles.btnLbl, styles.btnOutlineLbl]}>Scan again</Text>
              </Pressable>
              <Pressable
                style={styles.btn}
                onPress={confirmScan}
                disabled={scanState === 'done'}>
                <Text style={styles.btnLbl}>Continue</Text>
              </Pressable>
            </View>
          </>
        ) : (
          <Pressable style={[styles.btn, styles.btnOutline, styles.cancelBtn]} onPress={() => router.back()}>
            <Text style={[styles.btnLbl, styles.btnOutlineLbl]}>Cancel</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const CORNER = 24;
const CORNER_W = 3;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#000' },
  bg: { backgroundColor: '#111' },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, padding: 24 },
  viewfinderContainer: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewfinder: {
    width: 240,
    height: 180,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: CORNER,
    height: CORNER,
    borderColor: '#fff',
  },
  cornerDetected: {
    borderColor: '#4ade80',
  },
  tl: { top: 0, left: 0, borderTopWidth: CORNER_W, borderLeftWidth: CORNER_W },
  tr: { top: 0, right: 0, borderTopWidth: CORNER_W, borderRightWidth: CORNER_W },
  bl: { bottom: 0, left: 0, borderBottomWidth: CORNER_W, borderLeftWidth: CORNER_W },
  br: { bottom: 0, right: 0, borderBottomWidth: CORNER_W, borderRightWidth: CORNER_W },
  topHint: {
    position: 'absolute',
    top: 80,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  hintText: {
    color: '#fff',
    fontSize: 15,
    textAlign: 'center',
    backgroundColor: 'rgba(0,0,0,0.45)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    overflow: 'hidden',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingBottom: 48,
    paddingTop: 20,
    gap: 16,
    alignItems: 'center',
  },
  detectedCard: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 14,
    paddingHorizontal: 20,
    paddingVertical: 14,
    width: '100%',
    gap: 4,
  },
  detectedType: {
    color: '#a0cfdd',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  detectedValue: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
  btnRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  btn: {
    flex: 1,
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.7)',
  },
  btnLbl: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  btnOutlineLbl: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 16,
  },
  cancelBtn: {
    flex: 0,
    paddingHorizontal: 24,
  },
  whiteText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
});
