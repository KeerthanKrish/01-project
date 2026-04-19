import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { Pressable, StyleSheet, Text, useColorScheme, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const TAB_ICONS: Record<string, { name: React.ComponentProps<typeof IconSymbol>['name']; label: string }> = {
  index: { name: 'house.fill', label: 'Home' },
  scan: { name: 'plus.circle.fill', label: 'Sell' },
};

export function FloatingTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const scheme = useColorScheme() ?? 'light';
  const colors = Colors[scheme];

  return (
    <View style={[styles.wrapper, { bottom: Math.max(insets.bottom, 16) + 8 }]} pointerEvents="box-none">
      <View style={[styles.pill, { backgroundColor: colors.card }]}>
        {state.routes.map((route, index) => {
          const isFocused = state.index === index;
          const { options } = descriptors[route.key];
          const icon = TAB_ICONS[route.name];

          function onPress() {
            const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          }

          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              accessibilityRole="button"
              accessibilityState={isFocused ? { selected: true } : {}}
              accessibilityLabel={options.tabBarAccessibilityLabel ?? icon?.label}
              style={[
                styles.tabItem,
                isFocused && { backgroundColor: scheme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(10,126,164,0.08)' },
              ]}>
              <IconSymbol
                size={24}
                name={icon?.name ?? 'house.fill'}
                color={isFocused ? colors.tint : colors.icon}
              />
              <Text style={[styles.label, { color: isFocused ? colors.tint : colors.icon }]}>
                {icon?.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
    pointerEvents: 'box-none',
  },
  pill: {
    flexDirection: 'row',
    borderRadius: 40,
    paddingVertical: 3,
    paddingHorizontal: 3,
    width: '60%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 10,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    paddingVertical: 7,
    borderRadius: 28,
  },
  label: {
    fontSize: 10,
    fontWeight: '500',
  },
});
