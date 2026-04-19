import { StyleSheet } from 'react-native';

export const scanStyles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 24,
    gap: 12,
    justifyContent: 'flex-start',
  },
  scrollContent: {
    flexGrow: 1,

  },
  inner: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 100,
    paddingBottom: 120,
    gap: 12,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  subtitle: {
    opacity: 0.8,
  },
  scanButton: {
    marginTop: 8,
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 999,
    alignItems: 'center',
  },
  scanButtonPressed: {
    opacity: 0.85,
  },
  scanButtonDisabled: {
    opacity: 0.4,
  },
  scanButtonLabel: {
    color: '#fff',
  },
  secondaryButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#007AFF',
    borderRadius: 999,
  },
  secondaryButtonPressed: {
    opacity: 0.4,
  },
  secondaryButtonLabel: {
    color: '#007AFF',
    fontSize: 16,
  },
  buttonRow: {
    gap: 10,
  },
  buttonCol: {
    flexDirection: 'column',
    gap: 10,
  },
  countLabel: {
    marginTop: 4,
    opacity: 0.75,
    fontSize: 14,
  },
  thumbnailGrid: {
    marginTop: 12,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  thumbnailWrap: {
    position: 'relative',
  },
  thumbnail: {
    width: 76,
    height: 76,
    borderRadius: 10,
    backgroundColor: 'rgba(0,0,0,0.06)',
  },
  removeThumb: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.65)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeThumbLabel: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 16,
    fontWeight: '600',
  },
  cameraRoot: {
    flex: 1,
    backgroundColor: '#000',
  },
  cameraHint: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  hintOnDark: {
    color: '#fff',
    textShadowColor: 'rgba(0,0,0,0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  previewWrap: {
    marginTop: 8,
    gap: 8,
    flex: 1,
    minHeight: 120,
  },
  photosHeader: {
    gap: 4,
  },
  warnNote: {
    fontSize: 12,
    color: '#ca8a04',
  },
  detectBadge: {
    position: 'absolute',
    bottom: 4,
    left: 4,
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  detectBadgeLabel: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700' as const,
    lineHeight: 13,
  },
  previewImage: {
    width: '100%',
    minHeight: 200,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.06)',
  },
  barcodeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f4f8',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#b3d9e8',
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 10,
  },
  barcodeBadgeLeft: {
    flex: 1,
    gap: 2,
  },
  barcodeBadgeType: {
    fontSize: 10,
    fontWeight: '700' as const,
    letterSpacing: 1.1,
    color: '#007AFF',
  },
  barcodeBadgeValue: {
    fontSize: 14,
    fontWeight: '500' as const,
    color: '#1a202c',
  },
  barcodeRemove: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(0,0,0,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  barcodeRemoveLbl: {
    color: '#555',
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 18,
  },
});
