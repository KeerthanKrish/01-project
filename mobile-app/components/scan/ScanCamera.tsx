import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useScanImages } from '@/contexts/scan-images-context';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';

import { MAX_SCAN_IMAGES } from './scan-constants';
import { scanStyles } from './scan-styles';

/**
 * Web: pick up to 10 images via the browser file dialog.
 */
export default function ScanCamera() {
  const router = useRouter();
  const { images, setImages } = useScanImages();
  const [notice, setNotice] = useState<string | null>(null);

  const revokeIfBlob = useCallback((uri: string) => {
    if (uri.startsWith('blob:')) {
      try { URL.revokeObjectURL(uri); } catch { /* ignore */ }
    }
  }, []);

  const openFilePicker = useCallback(() => {
    setNotice(null);
    if (images.length >= MAX_SCAN_IMAGES) {
      setNotice(`Max ${MAX_SCAN_IMAGES} images. Remove one to add more.`);
      return;
    }
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = () => {
      const files = Array.from(input.files ?? []);
      setImages((prev) => {
        const room = MAX_SCAN_IMAGES - prev.length;
        if (room <= 0) return prev;
        const urls: string[] = [];
        for (const file of files) {
          if (urls.length >= room) break;
          urls.push(URL.createObjectURL(file));
        }
        return [...prev, ...urls];
      });
    };
    input.click();
  }, [images.length, setImages]);

  function removeAt(index: number) {
    setImages((prev) => {
      const uri = prev[index];
      if (uri) revokeIfBlob(uri);
      return prev.filter((_, i) => i !== index);
    });
  }

  const atLimit = images.length >= MAX_SCAN_IMAGES;

  return (
    <ScrollView
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={scanStyles.scrollContent}
      showsVerticalScrollIndicator={false}>
      <ThemedView style={scanStyles.inner}>
        <ThemedText type="title">Scan</ThemedText>
        <ThemedText style={scanStyles.subtitle}>
          Add up to {MAX_SCAN_IMAGES} photos (web uses file upload).
        </ThemedText>
        <ThemedText style={scanStyles.countLabel}>
          {images.length} / {MAX_SCAN_IMAGES}
        </ThemedText>

        {notice ? <ThemedText style={scanStyles.subtitle}>{notice}</ThemedText> : null}

        <Pressable
          style={({ pressed }) => [scanStyles.scanButton, pressed && scanStyles.scanButtonPressed]}
          onPress={openFilePicker}
          disabled={atLimit}>
          <ThemedText type="defaultSemiBold" style={scanStyles.scanButtonLabel}>
            Choose images
          </ThemedText>
        </Pressable>

        {images.length > 0 ? (
          <>
            <View style={scanStyles.previewWrap}>
              <ThemedText type="subtitle">Photos</ThemedText>
              <View style={scanStyles.thumbnailGrid}>
                {images.map((uri, index) => (
                  <View key={`${index}-${uri}`} style={scanStyles.thumbnailWrap}>
                    <Image source={{ uri }} style={scanStyles.thumbnail} contentFit="cover" />
                    <Pressable
                      onPress={() => removeAt(index)}
                      style={scanStyles.removeThumb}
                      accessibilityRole="button"
                      accessibilityLabel="Remove photo">
                      <ThemedText style={scanStyles.removeThumbLabel}>×</ThemedText>
                    </Pressable>
                  </View>
                ))}
              </View>
            </View>
            <Pressable
              style={({ pressed }) => [scanStyles.scanButton, pressed && scanStyles.scanButtonPressed]}
              onPress={() => router.push('/scan-review')}>
              <ThemedText type="defaultSemiBold" style={scanStyles.scanButtonLabel}>
                Continue
              </ThemedText>
            </Pressable>
          </>
        ) : null}
      </ThemedView>
    </ScrollView>
  );
}
