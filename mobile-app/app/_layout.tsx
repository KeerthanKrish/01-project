import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';

import { ScanImagesProvider } from '@/contexts/scan-images-context';
import { useColorScheme } from '@/hooks/use-color-scheme';

export const unstable_settings = {
  anchor: '(tabs)',
};

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <ScanImagesProvider>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="scan-review" options={{ title: 'Review', headerBackTitle: 'Back' }} />
          <Stack.Screen name="estimate" options={{ title: 'Estimate', headerBackTitle: 'Back' }} />
          <Stack.Screen name="barcode-scan" options={{ title: 'Scan Barcode', headerShown: false }} />
        </Stack>
        <StatusBar style="auto" />
      </ThemeProvider>
    </ScanImagesProvider>
  );
}
