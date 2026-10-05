#include "modern_challenge_commit_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(plan.status == ModernChallengeCommitStatus::CommitRequired);
    assert(plan.expected_previous_medal == 0);
    assert(plan.resulting_medal == 3);
    assert(plan.commit_required());
    assert(modern_challenge_commit_context_matches(plan, 0));
    assert(!modern_challenge_commit_context_matches(plan, 1));

    // A selected tier never grants progression until the stock tour-award
    // lifecycle boundary has actually been reached.
    plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        ModernChallengeTier::Gold,
        true,
        false);
    assert(plan.status == ModernChallengeCommitStatus::NoChange);
    assert(plan.resulting_medal == 0);

    plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        1,
        ModernChallengeTier::Gold,
        false,
        true);
    assert(plan.status == ModernChallengeCommitStatus::NoChange);
    assert(plan.resulting_medal == 1);

    // Lower/equal selected tiers do not reduce or rewrite completion.
    plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        3,
        ModernChallengeTier::Bronze,
        true,
        true);
    assert(plan.status == ModernChallengeCommitStatus::NoChange);
    assert(plan.resulting_medal == 3);

    // The commit policy is not an Authentic-mode medal writer.
    plan = plan_modern_challenge_commit(
        ExecutionMode::Authentic,
        0,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(plan.status == ModernChallengeCommitStatus::Rejected);

    plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        4,
        ModernChallengeTier::Gold,
        true,
        true);
    assert(plan.status == ModernChallengeCommitStatus::Rejected);

    plan = plan_modern_challenge_commit(
        ExecutionMode::Modern,
        0,
        static_cast<ModernChallengeTier>(4),
        true,
        true);
    assert(plan.status == ModernChallengeCommitStatus::Rejected);

    return 0;
}
