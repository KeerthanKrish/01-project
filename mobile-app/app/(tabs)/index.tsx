import { ThemedText } from '@/components/themed-text';
import { useThemeColor } from '@/hooks/use-theme-color';
import type { ConvexListing } from '@/services/api';
import { fetchListings } from '@/services/api';
import { useFocusEffect } from 'expo-router';
import { useCallback, useState, type ReactNode } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function formatListedAt(ms: number): string {
  try {
    return new Date(ms).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

function isSoldStatus(status: string): boolean {
  return status.trim().toLowerCase() === 'sold';
}

function DetailRow({
  label,
  value,
  textColor,
  mutedColor,
  multiline,
  mono,
}: {
  label: string;
  value: string;
  textColor: string;
  mutedColor: string;
  multiline?: boolean;
  mono?: boolean;
}) {
  return (
    <View style={styles.detailRow}>
      <Text style={[styles.detailLabel, { color: mutedColor }]}>{label}</Text>
      <Text
        style={[
          multiline ? styles.detailValueMultiline : styles.detailValue,
          { color: textColor },
          mono && {
            fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
            fontSize: 14,
            lineHeight: 20,
          },
        ]}
        selectable
        {...(multiline ? {} : { numberOfLines: 3 })}>
        {value}
      </Text>
    </View>
  );
}

function DrawerSection({
  title,
  children,
  titleColor,
}: {
  title: string;
  children: ReactNode;
  titleColor: string;
}) {
  return (
    <View style={styles.drawerSection}>
      <Text style={[styles.sectionHeading, { color: titleColor }]}>{title}</Text>
      {children}
    </View>
  );
}

function StatusPill({ status, textColor, borderColor }: { status: string; textColor: string; borderColor: string }) {
  return (
    <View style={[styles.statusPill, { borderColor }]}>
      <Text style={[styles.statusPillText, { color: textColor }]} numberOfLines={1}>
        {status}
      </Text>
    </View>
  );
}

function ListingDetailDrawer({
  visible,
  item,
  onClose,
  cardBg,
  borderColor,
  textColor,
  mutedColor,
  bottomInset,
  descriptionPanelBg,
  accentColor,
}: {
  visible: boolean;
  item: ConvexListing | null;
  onClose: () => void;
  cardBg: string;
  borderColor: string;
  textColor: string;
  mutedColor: string;
  bottomInset: number;
  descriptionPanelBg: string;
  accentColor: string;
}) {
  if (!item) return null;

  const priceStr = `$${item.price.toFixed(2)}`;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
      statusBarTranslucent>
      <View style={styles.modalRoot}>
        <Pressable style={styles.modalBackdrop} onPress={onClose} accessibilityLabel="Close drawer" />
        <View
          style={[
            styles.drawer,
            {
              backgroundColor: cardBg,
              borderTopColor: borderColor,
              paddingBottom: Math.max(bottomInset, 20) + 8,
            },
          ]}>
          <View style={[styles.drawerHandle, { backgroundColor: borderColor }]} />
          <Text style={[styles.drawerTitle, { color: textColor }]}>Listing details</Text>

          <View style={styles.drawerHero}>
            <Text style={[styles.drawerPrice, { color: accentColor }]}>{priceStr}</Text>
            <StatusPill status={item.status} textColor={textColor} borderColor={borderColor} />
          </View>

          <ScrollView
            style={styles.drawerScroll}
            contentContainerStyle={styles.drawerScrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled">
            <DrawerSection title="Description" titleColor={textColor}>
              <View style={[styles.descriptionPanel, { backgroundColor: descriptionPanelBg, borderColor }]}>
                <Text style={[styles.descriptionBody, { color: textColor }]} selectable>
                  {item.description}
                </Text>
              </View>
            </DrawerSection>

            <View style={[styles.sectionRule, { backgroundColor: borderColor }]} />

            <DrawerSection title="Activity" titleColor={textColor}>
              <DetailRow
                label="Listed"
                value={formatListedAt(item._creationTime)}
                textColor={textColor}
                mutedColor={mutedColor}
              />
            </DrawerSection>

            <View style={[styles.sectionRule, { backgroundColor: borderColor }]} />

            <DrawerSection title="People" titleColor={textColor}>
              <DetailRow label="Seller" value={item.userId} textColor={textColor} mutedColor={mutedColor} />
              <DetailRow
                label="Buyer"
                value={item.buyerId ?? '—'}
                textColor={textColor}
                mutedColor={mutedColor}
              />
            </DrawerSection>

            <View style={[styles.sectionRule, { backgroundColor: borderColor }]} />

            <DrawerSection title="Reference" titleColor={textColor}>
              <DetailRow
                label="Listing ID"
                value={item._id}
                textColor={textColor}
                mutedColor={mutedColor}
                mono
                multiline
              />
            </DrawerSection>
          </ScrollView>
          <Pressable
            style={({ pressed }) => [styles.drawerCloseBtn, pressed && styles.pressed]}
            onPress={onClose}>
            <Text style={styles.drawerCloseLbl}>Done</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const bg = useThemeColor({}, 'background');
  const cardBg = useThemeColor({}, 'card');
  const borderColor = useThemeColor({ light: '#e2e8f0', dark: '#2d3748' }, 'icon');
  const textColor = useThemeColor({}, 'text');
  const mutedColor = useThemeColor({ light: '#64748b', dark: '#94a3b8' }, 'icon');
  const descriptionPanelBg = useThemeColor({ light: '#f1f5f9', dark: '#22262e' }, 'background');
  const accentColor = useThemeColor({}, 'tint');

  const [listings, setListings] = useState<ConvexListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ConvexListing | null>(null);

  const load = useCallback(async (isRefresh: boolean) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    const result = await fetchListings(50);
    if (result.ok) {
      setListings(result.listings);
    } else {
      setError(result.error);
      setListings([]);
    }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useFocusEffect(
    useCallback(() => {
      load(false);
    }, [load])
  );

  return (
    <View style={[styles.root, { backgroundColor: bg, paddingTop: insets.top + 12 }]}>
      <View style={styles.header}>
        <ThemedText type="title">Your products</ThemedText>
        <ThemedText style={[styles.subtitle, { color: mutedColor }]}>
          Tap a listing for full details
        </ThemedText>
      </View>

      {loading && listings.length === 0 ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={[styles.loadingLbl, { color: mutedColor }]}>Loading listings…</Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Text style={[styles.errTitle, { color: textColor }]}>Couldn’t load listings</Text>
          <Text style={[styles.errBody, { color: mutedColor }]}>{error}</Text>
          <Pressable
            style={({ pressed }) => [styles.retryBtn, pressed && styles.pressed]}
            onPress={() => load(false)}>
            <Text style={styles.retryLbl}>Retry</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          data={listings}
          keyExtractor={(item) => item._id}
          contentContainerStyle={[
            styles.listContent,
            { paddingBottom: 120 + insets.bottom },
            listings.length === 0 && styles.listEmpty,
          ]}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor="#007AFF" />
          }
          ListEmptyComponent={
            <Text style={[styles.empty, { color: mutedColor }]}>
              No listings yet. Scan an item and publish from the estimate screen.
            </Text>
          }
          renderItem={({ item }) => {
            const sold = isSoldStatus(item.status);
            return (
              <Pressable
                onPress={() => setSelected(item)}
                style={({ pressed }) => [
                  styles.card,
                  {
                    backgroundColor: cardBg,
                    borderColor,
                    opacity: pressed ? 0.92 : sold ? 0.78 : 1,
                  },
                ]}
                accessibilityRole="button"
                accessibilityLabel={
                  sold
                    ? `Sold: ${item.description}, ${item.price} dollars`
                    : `${item.description}, ${item.price} dollars`
                }>
                <View style={styles.cardInner}>
                  <Text
                    style={[
                      styles.cardTitle,
                      { color: textColor },
                      sold && styles.cardSoldStrike,
                    ]}
                    numberOfLines={2}>
                    {item.description}
                  </Text>
                  <Text
                    style={[
                      styles.cardPrice,
                      { color: sold ? mutedColor : accentColor },
                      sold && styles.cardSoldStrike,
                    ]}>
                    ${item.price.toFixed(2)}
                  </Text>
                </View>
              </Pressable>
            );
          }}
        />
      )}

      <ListingDetailDrawer
        visible={selected !== null}
        item={selected}
        onClose={() => setSelected(null)}
        cardBg={cardBg}
        borderColor={borderColor}
        textColor={textColor}
        mutedColor={mutedColor}
        bottomInset={insets.bottom}
        descriptionPanelBg={descriptionPanelBg}
        accentColor={accentColor}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { paddingHorizontal: 20, marginBottom: 12 },
  subtitle: { fontSize: 14, marginTop: 4 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, gap: 12 },
  loadingLbl: { fontSize: 14 },
  errTitle: { fontSize: 17, fontWeight: '600' },
  errBody: { fontSize: 14, textAlign: 'center' },
  retryBtn: {
    marginTop: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 999,
    backgroundColor: '#007AFF',
  },
  retryLbl: { color: '#fff', fontSize: 16, fontWeight: '600' },
  pressed: { opacity: 0.88 },
  listContent: { paddingHorizontal: 16 },
  listEmpty: { flexGrow: 1, justifyContent: 'center' },
  empty: { textAlign: 'center', fontSize: 15, lineHeight: 22, paddingHorizontal: 24 },
  card: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
  },
  cardInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 14,
    paddingVertical: 16,
    paddingHorizontal: 18,
  },
  cardTitle: { flex: 1, fontSize: 16, fontWeight: '600', lineHeight: 22 },
  cardPrice: { fontSize: 18, fontWeight: '700' },
  cardSoldStrike: { textDecorationLine: 'line-through' },
  modalRoot: { flex: 1, justifyContent: 'flex-end' },
  modalBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.45)' },
  drawer: {
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    maxHeight: '88%',
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  drawerHandle: {
    alignSelf: 'center',
    width: 36,
    height: 4,
    borderRadius: 2,
    marginBottom: 16,
    opacity: 0.5,
  },
  drawerTitle: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
  drawerHero: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 20,
  },
  drawerPrice: { fontSize: 28, fontWeight: '800', letterSpacing: -0.5 },
  statusPill: {
    flexShrink: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
    maxWidth: '48%',
  },
  statusPillText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
  drawerScroll: { maxHeight: 440 },
  drawerScrollContent: { paddingBottom: 8 },
  drawerSection: { gap: 10 },
  sectionHeading: { fontSize: 13, fontWeight: '700', letterSpacing: -0.2 },
  sectionRule: { height: StyleSheet.hairlineWidth, marginVertical: 18, opacity: 0.55 },
  descriptionPanel: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  descriptionBody: { fontSize: 16, lineHeight: 24 },
  detailRow: { gap: 4, marginBottom: 12 },
  detailLabel: { fontSize: 13, fontWeight: '500' },
  detailValue: { fontSize: 16, lineHeight: 22 },
  detailValueMultiline: { fontSize: 16, lineHeight: 22 },
  drawerCloseBtn: {
    marginTop: 8,
    paddingVertical: 14,
    borderRadius: 999,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  drawerCloseLbl: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
