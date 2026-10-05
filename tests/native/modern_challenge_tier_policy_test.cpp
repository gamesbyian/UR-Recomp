#include "modern_challenge_tier_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    assert(challenge_tier_medal_value(ModernChallengeTier::Bronze) == 1);
    assert(challenge_tier_medal_value(ModernChallengeTier::Silver) == 2);
    assert(challenge_tier_medal_value(ModernChallengeTier::Gold) == 3);

    assert(stock_next_challenge_tier(0) == ModernChallengeTier::Bronze);
    assert(stock_next_challenge_tier(1) == ModernChallengeTier::Silver);
    assert(stock_next_challenge_tier(2) == ModernChallengeTier::Gold);
    assert(!stock_next_challenge_tier(3));
    assert(!stock_next_challenge_tier(4));

    for (const auto tier : {
             ModernChallengeTier::Bronze,
             ModernChallengeTier::Silver,
             ModernChallengeTier::Gold}) {
        assert(modern_challenge_tier_selectable(
            ExecutionMode::Modern, true, tier));
        assert(!modern_challenge_tier_selectable(
            ExecutionMode::Authentic, true, tier));
        assert(!modern_challenge_tier_selectable(
            ExecutionMode::Modern, false, tier));
    }

    assert(!modern_challenge_tier_selectable(
        ExecutionMode::Modern, true, ModernChallengeTier::Bronze, true));
    assert(!modern_challenge_tier_selectable(
        ExecutionMode::Modern, true, ModernChallengeTier::Silver, true));
    assert(modern_challenge_tier_selectable(
        ExecutionMode::Modern, true, ModernChallengeTier::Gold, true));

    assert(canonical_challenge_opponent(
               ModernChallengeTier::Bronze, false) ==
           CanonicalChallengeOpponent::Bronsen);
    assert(canonical_challenge_opponent(
               ModernChallengeTier::Silver, false) ==
           CanonicalChallengeOpponent::Silvia);
    assert(canonical_challenge_opponent(
               ModernChallengeTier::Gold, false) ==
           CanonicalChallengeOpponent::Goldwyn);
    for (const auto tier : {
             ModernChallengeTier::Bronze,
             ModernChallengeTier::Silver,
             ModernChallengeTier::Gold}) {
        assert(canonical_challenge_opponent(tier, true) ==
               CanonicalChallengeOpponent::AntiUni);
    }

    // Modern records the highest canonical tier actually completed. A direct
    // Gold completion therefore satisfies Bronze and Silver as well.
    auto result = modern_challenge_completion(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        true);
    assert(result.previous_medal == 0);
    assert(result.resulting_medal == 3);
    assert(result.changed);

    result = modern_challenge_completion(
        ExecutionMode::Modern,
        1,
        ModernChallengeTier::Silver,
        true);
    assert(result.resulting_medal == 2);
    assert(result.changed);

    // Replaying a lower/equal tier never reduces canonical completion.
    result = modern_challenge_completion(
        ExecutionMode::Modern,
        3,
        ModernChallengeTier::Bronze,
        true);
    assert(result.resulting_medal == 3);
    assert(!result.changed);

    // Failure never grants progression.
    result = modern_challenge_completion(
        ExecutionMode::Modern,
        1,
        ModernChallengeTier::Gold,
        false);
    assert(result.resulting_medal == 1);
    assert(!result.changed);

    // Authentic retains stock one-generation-at-a-time sequencing.
    result = authentic_stock_completion(0, true);
    assert(result.resulting_medal == 1);
    assert(result.changed);
    result = authentic_stock_completion(1, true);
    assert(result.resulting_medal == 2);
    result = authentic_stock_completion(2, true);
    assert(result.resulting_medal == 3);
    result = authentic_stock_completion(3, true);
    assert(result.resulting_medal == 3);
    assert(!result.changed);

    // Modern policy is inert when evaluated under Authentic mode.
    result = modern_challenge_completion(
        ExecutionMode::Authentic,
        0,
        ModernChallengeTier::Gold,
        true);
    assert(result.resulting_medal == 0);
    assert(!result.changed);

    return 0;
}
