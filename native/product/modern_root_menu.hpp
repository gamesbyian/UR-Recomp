#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::product {

enum class ModernRootDestination : std::uint8_t {
    Play = 0,
    Practice = 1,
    Multiplayer = 2,
    Records = 3,
    Options = 4,
};

inline constexpr std::size_t kModernRootDestinationCount = 5;

struct ModernRootMenu {
    ModernRootDestination selected = ModernRootDestination::Play;
};

constexpr std::size_t modern_root_destination_index(
    ModernRootDestination destination) noexcept {
    return static_cast<std::size_t>(destination);
}

constexpr ModernRootDestination modern_root_destination_from_index(
    std::size_t index) noexcept {
    return static_cast<ModernRootDestination>(
        index % kModernRootDestinationCount);
}

constexpr ModernRootDestination modern_root_menu_selected(
    const ModernRootMenu& menu) noexcept {
    const auto index = modern_root_destination_index(menu.selected);
    return index < kModernRootDestinationCount
        ? menu.selected
        : ModernRootDestination::Play;
}

constexpr ModernRootMenu modern_root_menu_reset() noexcept {
    return {ModernRootDestination::Play};
}

constexpr ModernRootMenu modern_root_menu_move(
    ModernRootMenu menu,
    int delta) noexcept {
    menu.selected = modern_root_menu_selected(menu);
    if (delta == 0) return menu;

    const int count = static_cast<int>(kModernRootDestinationCount);
    int index = static_cast<int>(
        modern_root_destination_index(menu.selected));

    const int step = delta > 0 ? 1 : -1;
    index = (index + step + count) % count;
    menu.selected = modern_root_destination_from_index(
        static_cast<std::size_t>(index));
    return menu;
}

constexpr const char* modern_root_destination_label(
    ModernRootDestination destination) noexcept {
    switch (destination) {
    case ModernRootDestination::Play:
        return "PLAY";
    case ModernRootDestination::Practice:
        return "PRACTICE";
    case ModernRootDestination::Multiplayer:
        return "MULTIPLAYER";
    case ModernRootDestination::Records:
        return "RECORDS";
    case ModernRootDestination::Options:
        return "OPTIONS";
    default:
        return "PLAY";
    }
}

}  // namespace ur::product
