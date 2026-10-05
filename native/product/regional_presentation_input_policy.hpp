#pragma once

#include <cstdint>

#include "regional_presentation_secret.hpp"

namespace ur::product {

/*
 * Title-owned admission policy for the hidden regional secret.
 *
 * The retained title-transition evidence identifies stock menu state 0x84 as
 * the title-family surface and 0xD7 as the main menu. Restricting controller
 * recognition to 0x84 avoids stealing ordinary left/right/A menu navigation.
 */
constexpr bool regional_secret_title_surface(
    bool modern_mode,
    std::uint8_t current_menu,
    bool in_race,
    bool host_text_entry_active) noexcept {
    return modern_mode &&
           !in_race &&
           current_menu == 0x84u &&
           !host_text_entry_active;
}

constexpr RegionalSecretContext regional_secret_context(
    bool modern_mode,
    std::uint8_t current_menu,
    bool in_race,
    bool host_text_entry_active) noexcept {
    return {
        modern_mode,
        regional_secret_title_surface(
            modern_mode,
            current_menu,
            in_race,
            host_text_entry_active),
        host_text_entry_active,
    };
}

constexpr bool regional_secret_keyboard_character(int key, char& out) noexcept {
    // Product policy stays SDL-free. The host passes an ASCII-like key symbol
    // for ordinary letter keys after platform normalization.
    if (key >= 'a' && key <= 'z') {
        out = static_cast<char>(key);
        return true;
    }
    if (key >= 'A' && key <= 'Z') {
        out = static_cast<char>(key);
        return true;
    }
    return false;
}

}  // namespace ur::product
