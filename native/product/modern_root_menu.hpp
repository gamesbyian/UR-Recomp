#pragma once

#include "modern_text_catalog.hpp"

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

constexpr ModernTextId modern_root_destination_text_id(
    ModernRootDestination destination) noexcept {
    switch (destination) {
    case ModernRootDestination::Play:
        return ModernTextId::RootPlay;
    case ModernRootDestination::Practice:
        return ModernTextId::RootPractice;
    case ModernRootDestination::Multiplayer:
        return ModernTextId::RootMultiplayer;
    case ModernRootDestination::Records:
        return ModernTextId::RootRecords;
    case ModernRootDestination::Options:
        return ModernTextId::RootOptions;
    default:
        return ModernTextId::RootPlay;
    }
}

constexpr const char* modern_root_destination_label(
    ModernRootDestination destination) noexcept {
    return modern_text_default(modern_root_destination_text_id(destination));
}

}  // namespace ur::product
