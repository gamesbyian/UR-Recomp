#pragma once

#include <cstdint>

namespace ur::product {

/*
 * Stable semantic IDs for Modern host-owned UI text.
 *
 * IDs describe meaning, not English wording or screen position. New surfaces
 * should add IDs deliberately as their copy becomes product-stable rather than
 * moving every diagnostic/temporary string into this catalog at once.
 */
enum class ModernTextId : std::uint8_t {
    RootPlay = 0,
    RootPractice = 1,
    RootMultiplayer = 2,
    RootRecords = 3,
    RootOptions = 4,
};

constexpr const char* modern_text_key(ModernTextId id) noexcept {
    switch (id) {
    case ModernTextId::RootPlay:
        return "root.play";
    case ModernTextId::RootPractice:
        return "root.practice";
    case ModernTextId::RootMultiplayer:
        return "root.multiplayer";
    case ModernTextId::RootRecords:
        return "root.records";
    case ModernTextId::RootOptions:
        return "root.options";
    default:
        return "root.play";
    }
}

constexpr const char* modern_text_english(ModernTextId id) noexcept {
    switch (id) {
    case ModernTextId::RootPlay:
        return "PLAY";
    case ModernTextId::RootPractice:
        return "PRACTICE";
    case ModernTextId::RootMultiplayer:
        return "MULTIPLAYER";
    case ModernTextId::RootRecords:
        return "RECORDS";
    case ModernTextId::RootOptions:
        return "OPTIONS";
    default:
        return "PLAY";
    }
}

/*
 * A future locale pack may resolve modern_text_key(id) externally. English
 * remains the built-in fail-closed fallback so missing/invalid locale data
 * cannot remove navigation copy or create a new product-state dependency.
 */
constexpr const char* modern_text_default(ModernTextId id) noexcept {
    return modern_text_english(id);
}

}  // namespace ur::product
