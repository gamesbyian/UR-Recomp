#include "modern_challenge_tour_context.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto gold = begin_modern_challenge_tour_context(
        ExecutionMode::Modern,
        true,
        false,
        4,
        2,
        0,
        ModernChallengeTier::Gold);
    assert(gold);
    assert(gold->selected_generation == 2);
    assert(modern_challenge_tour_context_matches(
        *gold, ExecutionMode::Modern, 4, 2, 0));
    assert(!modern_challenge_tour_context_matches(
        *gold, ExecutionMode::Modern, 4, 2, 1));
    assert(!modern_challenge_tour_context_matches(
        *gold, ExecutionMode::Authentic, 4, 2, 0));

    const auto generation = modern_challenge_generation_plan(*gold);
    assert(generation);
    assert(generation->rider_index == 4);
    assert(generation->tour_row == 2);
    assert(generation->expected_persisted_medal == 0);
    assert(generation->selected_generation == 2);

    // Selection/failure alone never creates persistent completion authority.
    auto award = modern_challenge_tour_award_override(
        *gold, false, false);
    assert(!award);
    award = modern_challenge_tour_award_override(
        *gold, true, false);
    assert(!award);

    // Once the selected Gold tier is legitimately completed at the stock
    // award boundary, the same context asks stock to perform 2 -> 3.
    award = modern_challenge_tour_award_override(
        *gold, true, true);
    assert(award);
    assert(award->expected_persisted_medal == 0);
    assert(award->effective_previous_medal == 2);
    assert(award->expected_stock_result == 3);

    // Lower-tier replay from an already-Gold profile controls generation but
    // creates no new persistent medal authority.
    auto bronze_replay = begin_modern_challenge_tour_context(
        ExecutionMode::Modern,
        true,
        false,
        1,
        5,
        3,
        ModernChallengeTier::Bronze);
    assert(bronze_replay);
    assert(bronze_replay->selected_generation == 0);
    assert(!modern_challenge_tour_award_override(
        *bronze_replay, true, true));

    // Hunter remains stock Gold-only discovery content, not an ordinary
    // direct-tier context.
    assert(!begin_modern_challenge_tour_context(
        ExecutionMode::Modern,
        true,
        true,
        0,
        8,
        0,
        ModernChallengeTier::Gold));

    assert(!begin_modern_challenge_tour_context(
        ExecutionMode::Authentic,
        true,
        false,
        0,
        0,
        0,
        ModernChallengeTier::Gold));
    assert(!begin_modern_challenge_tour_context(
        ExecutionMode::Modern,
        false,
        false,
        0,
        0,
        0,
        ModernChallengeTier::Gold));

    return 0;
}
