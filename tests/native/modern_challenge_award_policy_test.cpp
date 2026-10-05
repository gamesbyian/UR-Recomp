#include "modern_challenge_award_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        true,
        true);
    auto award = modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Gold);
    assert(award);
    assert(award->expected_persisted_medal == 0);
    assert(award->effective_previous_medal == 2);
    assert(award->expected_stock_result == 3);
    assert(modern_challenge_stock_award_precondition_matches(*award, 0));
    assert(!modern_challenge_stock_award_precondition_matches(*award, 1));

    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Silver,
        true,
        true);
    award = modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Silver);
    assert(award);
    assert(award->effective_previous_medal == 1);
    assert(award->expected_stock_result == 2);

    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Bronze,
        true,
        true);
    award = modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Bronze);
    assert(award);
    assert(award->effective_previous_medal == 0);
    assert(award->expected_stock_result == 1);

    // Existing Silver completing Gold still lets stock perform its natural
    // 2 -> 3 transaction. The hook contract does not invent a different
    // result, it only describes the stock input value that produces Gold.
    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        2,
        ModernChallengeTier::Gold,
        true,
        true);
    award = modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Gold);
    assert(award);
    assert(award->effective_previous_medal == 2);
    assert(award->expected_stock_result == 3);

    // No-change, failure, Authentic, stale or mismatched selected-tier plans
    // never authorize an award override.
    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        3,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(!modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Gold));

    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        false,
        true);
    assert(!modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Gold));

    commit = plan_modern_challenge_commit(
        ExecutionMode::Authentic,
        0,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(!modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Gold));

    commit = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(!modern_challenge_stock_award_override(
        commit, ModernChallengeTier::Silver));

    return 0;
}
