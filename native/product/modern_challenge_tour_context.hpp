#pragma once

#include "modern_challenge_award_policy.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

struct ModernChallengeTourContext {
    bool active = false;
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t persisted_medal_before_tour = 0;
    ModernChallengeTier selected_tier = ModernChallengeTier::Bronze;
    std::uint8_t selected_generation = 0;
};

constexpr std::optional<ModernChallengeTourContext>
begin_modern_challenge_tour_context(
    ExecutionMode mode,
    bool tour_available,
    bool hunter_tour,
    std::uint8_t rider_index,
    std::uint8_t tour_row,
    std::uint8_t persisted_medal,
    ModernChallengeTier selected_tier) noexcept {
    if (mode != ExecutionMode::Modern ||
        !tour_available ||
        hunter_tour ||
        rider_index >= 16 ||
        tour_row >= 8 ||
        !valid_stock_medal_value(persisted_medal) ||
        !modern_challenge_tier_selectable(
            mode, tour_available, selected_tier, false)) {
        return std::nullopt;
    }

    const auto generation = challenge_tier_generation(selected_tier);
    if (!generation) return std::nullopt;

    return ModernChallengeTourContext{
        true,
        rider_index,
        tour_row,
        persisted_medal,
        selected_tier,
        *generation,
    };
}

constexpr bool modern_challenge_tour_context_matches(
    const ModernChallengeTourContext& context,
    ExecutionMode mode,
    std::uint8_t rider_index,
    std::uint8_t tour_row,
    std::uint8_t persisted_medal) noexcept {
    return context.active &&
           mode == ExecutionMode::Modern &&
           rider_index == context.rider_index &&
           tour_row == context.tour_row &&
           persisted_medal == context.persisted_medal_before_tour &&
           valid_stock_medal_value(persisted_medal) &&
           valid_modern_challenge_tier(context.selected_tier) &&
           challenge_tier_generation(context.selected_tier) ==
               std::optional<std::uint8_t>{context.selected_generation};
}

struct ModernChallengeGenerationPlan {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t expected_persisted_medal = 0;
    std::uint8_t selected_generation = 0;
};

constexpr std::optional<ModernChallengeGenerationPlan>
modern_challenge_generation_plan(
    const ModernChallengeTourContext& context) noexcept {
    if (!context.active) return std::nullopt;
    return ModernChallengeGenerationPlan{
        context.rider_index,
        context.tour_row,
        context.persisted_medal_before_tour,
        context.selected_generation,
    };
}

constexpr ModernChallengeCommitPlan modern_challenge_tour_commit_plan(
    const ModernChallengeTourContext& context,
    bool completed_selected_tier,
    bool stock_tour_award_boundary_reached) noexcept {
    if (!context.active) return {};
    return plan_modern_challenge_commit(
        ExecutionMode::Modern,
        context.persisted_medal_before_tour,
        context.selected_tier,
        completed_selected_tier,
        stock_tour_award_boundary_reached);
}

constexpr std::optional<ModernChallengeStockAwardOverride>
modern_challenge_tour_award_override(
    const ModernChallengeTourContext& context,
    bool completed_selected_tier,
    bool stock_tour_award_boundary_reached) noexcept {
    const auto commit = modern_challenge_tour_commit_plan(
        context,
        completed_selected_tier,
        stock_tour_award_boundary_reached);
    return modern_challenge_stock_award_override(
        commit, context.selected_tier);
}

}  // namespace ur::product
