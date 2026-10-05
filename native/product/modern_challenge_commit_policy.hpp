#pragma once

#include "modern_challenge_tier_policy.hpp"

#include <cstdint>

namespace ur::product {

enum class ModernChallengeCommitStatus : std::uint8_t {
    NoChange = 0,
    CommitRequired = 1,
    Rejected = 2,
};

struct ModernChallengeCommitPlan {
    ModernChallengeCommitStatus status = ModernChallengeCommitStatus::Rejected;
    std::uint8_t expected_previous_medal = 0;
    std::uint8_t resulting_medal = 0;

    constexpr bool commit_required() const noexcept {
        return status == ModernChallengeCommitStatus::CommitRequired;
    }
};

constexpr ModernChallengeCommitPlan plan_modern_challenge_commit(
    ExecutionMode mode,
    std::uint8_t persisted_medal_before_tour,
    ModernChallengeTier selected_tier,
    bool completed_selected_tier,
    bool stock_tour_award_boundary_reached) noexcept {
    if (mode != ExecutionMode::Modern ||
        !valid_stock_medal_value(persisted_medal_before_tour) ||
        !valid_modern_challenge_tier(selected_tier)) {
        return {};
    }

    // Failure, cancellation, or an incomplete tour never owns a progression
    // commit, even if a selected tier was higher than the current medal.
    if (!completed_selected_tier || !stock_tour_award_boundary_reached) {
        return {
            ModernChallengeCommitStatus::NoChange,
            persisted_medal_before_tour,
            persisted_medal_before_tour,
        };
    }

    const auto completion = modern_challenge_completion(
        mode,
        persisted_medal_before_tour,
        selected_tier,
        true);
    if (!completion.changed) {
        return {
            ModernChallengeCommitStatus::NoChange,
            persisted_medal_before_tour,
            persisted_medal_before_tour,
        };
    }

    return {
        ModernChallengeCommitStatus::CommitRequired,
        persisted_medal_before_tour,
        completion.resulting_medal,
    };
}

constexpr bool modern_challenge_commit_context_matches(
    const ModernChallengeCommitPlan& plan,
    std::uint8_t current_persisted_medal) noexcept {
    return plan.status != ModernChallengeCommitStatus::Rejected &&
           valid_stock_medal_value(current_persisted_medal) &&
           current_persisted_medal == plan.expected_previous_medal;
}

}  // namespace ur::product
