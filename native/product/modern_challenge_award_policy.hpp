#pragma once

#include "modern_challenge_commit_policy.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

struct ModernChallengeStockAwardOverride {
    std::uint8_t expected_persisted_medal = 0;
    std::uint8_t effective_previous_medal = 0;
    std::uint8_t expected_stock_result = 0;
};

constexpr std::optional<ModernChallengeStockAwardOverride>
modern_challenge_stock_award_override(
    const ModernChallengeCommitPlan& plan,
    ModernChallengeTier selected_tier) noexcept {
    if (plan.status != ModernChallengeCommitStatus::CommitRequired ||
        !valid_modern_challenge_tier(selected_tier)) {
        return std::nullopt;
    }

    const auto selected_value =
        challenge_tier_medal_value(selected_tier);
    if (selected_value == 0 || selected_value > 3 ||
        plan.resulting_medal != selected_value ||
        plan.expected_previous_medal >= selected_value) {
        return std::nullopt;
    }

    return ModernChallengeStockAwardOverride{
        plan.expected_previous_medal,
        static_cast<std::uint8_t>(selected_value - 1u),
        selected_value,
    };
}

constexpr bool modern_challenge_stock_award_precondition_matches(
    const ModernChallengeStockAwardOverride& override_plan,
    std::uint8_t current_persisted_medal) noexcept {
    return valid_stock_medal_value(current_persisted_medal) &&
           current_persisted_medal ==
               override_plan.expected_persisted_medal;
}

}  // namespace ur::product
