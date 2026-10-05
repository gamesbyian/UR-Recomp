#pragma once

#include "modern_challenge_tier_policy.hpp"
#include "modern_host_navigation.h"

#include <array>
#include <cstddef>

namespace ur::product {

struct ModernChallengeTierSelector {
    std::array<ModernChallengeTier, 3> tiers{
        ModernChallengeTier::Bronze,
        ModernChallengeTier::Silver,
        ModernChallengeTier::Gold,
    };
    std::size_t count = 0;
    std::size_t selected = 0;
};

constexpr ModernChallengeTier default_modern_challenge_tier(
    std::uint8_t current_medal) noexcept {
    const auto next = stock_next_challenge_tier(current_medal);
    return next.value_or(ModernChallengeTier::Gold);
}

constexpr ModernChallengeTierSelector make_modern_challenge_tier_selector(
    ExecutionMode mode,
    bool tour_available,
    bool hunter_tour,
    std::uint8_t current_medal) noexcept {
    ModernChallengeTierSelector selector;
    if (mode != ExecutionMode::Modern || !tour_available ||
        !valid_stock_medal_value(current_medal)) {
        return selector;
    }

    if (hunter_tour) {
        selector.tiers[0] = ModernChallengeTier::Gold;
        selector.count = 1;
        return selector;
    }

    selector.count = 3;
    const auto preferred = default_modern_challenge_tier(current_medal);
    for (std::size_t i = 0; i < selector.count; ++i) {
        if (selector.tiers[i] == preferred) {
            selector.selected = i;
            break;
        }
    }
    return selector;
}

constexpr ModernChallengeTier selected_modern_challenge_tier(
    const ModernChallengeTierSelector& selector) noexcept {
    return selector.count == 0
        ? ModernChallengeTier::Bronze
        : selector.tiers[
              selector.selected < selector.count ? selector.selected : 0u];
}

constexpr ModernChallengeTierSelector navigate_modern_challenge_tier_selector(
    ModernChallengeTierSelector selector,
    UrModernHostNavigationAction action) noexcept {
    if (selector.count <= 1) return selector;

    const int delta =
        ur_modern_host_navigation_adjustment_delta(action);
    if (delta < 0) {
        selector.selected =
            selector.selected == 0
                ? selector.count - 1
                : selector.selected - 1;
    } else if (delta > 0) {
        selector.selected =
            (selector.selected + 1) % selector.count;
    }
    return selector;
}

constexpr bool confirm_modern_challenge_tier(
    const ModernChallengeTierSelector& selector,
    ExecutionMode mode,
    bool tour_available,
    bool hunter_tour,
    UrModernHostNavigationAction action,
    ModernChallengeTier& out) noexcept {
    if (!ur_modern_host_navigation_is_confirm(action) ||
        selector.count == 0) {
        return false;
    }
    const auto selected = selected_modern_challenge_tier(selector);
    if (!modern_challenge_tier_selectable(
            mode, tour_available, selected, hunter_tour)) {
        return false;
    }
    out = selected;
    return true;
}

}  // namespace ur::product
