#pragma once

#include "host_product_state.hpp"

#include <algorithm>
#include <cstdint>
#include <optional>

namespace ur::product {

enum class ModernChallengeTier : std::uint8_t {
    Bronze = 1,
    Silver = 2,
    Gold = 3,
};

enum class CanonicalChallengeOpponent : std::uint8_t {
    Bronsen = 0,
    Silvia = 1,
    Goldwyn = 2,
    AntiUni = 3,
};

constexpr bool valid_stock_medal_value(std::uint8_t value) noexcept {
    return value <= static_cast<std::uint8_t>(ModernChallengeTier::Gold);
}

constexpr std::uint8_t challenge_tier_medal_value(
    ModernChallengeTier tier) noexcept {
    return static_cast<std::uint8_t>(tier);
}

constexpr std::optional<ModernChallengeTier> stock_next_challenge_tier(
    std::uint8_t current_medal) noexcept {
    if (!valid_stock_medal_value(current_medal) ||
        current_medal >= challenge_tier_medal_value(
            ModernChallengeTier::Gold)) {
        return std::nullopt;
    }
    return static_cast<ModernChallengeTier>(
        static_cast<std::uint8_t>(current_medal + 1u));
}

constexpr bool modern_challenge_tier_selectable(
    ExecutionMode mode,
    bool tour_available,
    ModernChallengeTier requested) noexcept {
    const auto value = challenge_tier_medal_value(requested);
    return mode == ExecutionMode::Modern &&
           tour_available &&
           value >= challenge_tier_medal_value(ModernChallengeTier::Bronze) &&
           value <= challenge_tier_medal_value(ModernChallengeTier::Gold);
}

constexpr CanonicalChallengeOpponent canonical_challenge_opponent(
    ModernChallengeTier tier,
    bool hunter_tour) noexcept {
    if (hunter_tour) return CanonicalChallengeOpponent::AntiUni;
    switch (tier) {
    case ModernChallengeTier::Bronze:
        return CanonicalChallengeOpponent::Bronsen;
    case ModernChallengeTier::Silver:
        return CanonicalChallengeOpponent::Silvia;
    case ModernChallengeTier::Gold:
        return CanonicalChallengeOpponent::Goldwyn;
    }
    return CanonicalChallengeOpponent::Bronsen;
}

struct ModernChallengeCompletion {
    std::uint8_t previous_medal = 0;
    std::uint8_t resulting_medal = 0;
    bool changed = false;
};

constexpr ModernChallengeCompletion modern_challenge_completion(
    ExecutionMode mode,
    std::uint8_t current_medal,
    ModernChallengeTier selected,
    bool challenge_completed) noexcept {
    ModernChallengeCompletion out{
        current_medal,
        current_medal,
        false,
    };
    if (mode != ExecutionMode::Modern ||
        !valid_stock_medal_value(current_medal) ||
        !challenge_completed) {
        return out;
    }

    const auto selected_value = challenge_tier_medal_value(selected);
    if (selected_value > out.resulting_medal) {
        out.resulting_medal = selected_value;
        out.changed = true;
    }
    return out;
}

constexpr ModernChallengeCompletion authentic_stock_completion(
    std::uint8_t current_medal,
    bool stock_awarded_next_medal) noexcept {
    ModernChallengeCompletion out{
        current_medal,
        current_medal,
        false,
    };
    if (!valid_stock_medal_value(current_medal) ||
        !stock_awarded_next_medal ||
        current_medal >= challenge_tier_medal_value(
            ModernChallengeTier::Gold)) {
        return out;
    }
    out.resulting_medal =
        static_cast<std::uint8_t>(current_medal + 1u);
    out.changed = true;
    return out;
}

}  // namespace ur::product
