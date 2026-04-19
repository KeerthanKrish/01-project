import { useScanImages } from '@/contexts/scan-images-context';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

export default function BarcodeScanScreen() {
  const router = useRouter();
  const { setBarcode } = useScanImages();
  const [value, setValue] = useState('');

  function submit() {
    const trimmed = value.trim();
    if (!trimmed) return;
    setBarcode({ type: 'manual', value: trimmed });
    router.back();
  }

  return (
    <View style={styles.root}>
      <Text style={styles.icon}>📷</Text>
      <Text style={styles.title}>Barcode scanner</Text>
      <Text style={styles.subtitle}>
        Live barcode scanning isn't supported on web. Enter the barcode value manually below.
      </Text>
      <TextInput
        style={styles.input}
        placeholder="Barcode value…"
        placeholderTextColor="#94a3b8"
        value={value}
        onChangeText={setValue}
        autoFocus
        returnKeyType="done"
        onSubmitEditing={submit}
      />
      <Pressable
        style={({ pressed }) => [styles.btn, !value.trim() && styles.btnDisabled, pressed && styles.pressed]}
        onPress={submit}
        disabled={!value.trim()}>
        <Text style={styles.btnLbl}>Save barcode</Text>
      </Pressable>
      <Pressable style={({ pressed }) => [styles.btnSec, pressed && styles.pressed]} onPress={() => router.back()}>
        <Text style={styles.btnSecLbl}>Cancel</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32, gap: 14, backgroundColor: '#f0f4f8' },
  icon: { fontSize: 48 },
  title: { fontSize: 22, fontWeight: '700', color: '#1a202c' },
  subtitle: { fontSize: 15, color: '#64748b', textAlign: 'center', lineHeight: 22 },
  input: {
    width: '100%', borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 12,
    paddingVertical: 12, paddingHorizontal: 14, fontSize: 16,
    backgroundColor: '#fff', color: '#1a202c',
  },
  btn: { width: '100%', backgroundColor: '#007AFF', paddingVertical: 14, borderRadius: 999, alignItems: 'center' },
  btnDisabled: { opacity: 0.45 },
  btnLbl: { color: '#fff', fontSize: 16, fontWeight: '600' },
  btnSec: { width: '100%', paddingVertical: 12, alignItems: 'center' },
  btnSecLbl: { color: '#007AFF', fontSize: 16 },
  pressed: { opacity: 0.8 },
});
