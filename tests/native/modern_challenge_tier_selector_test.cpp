#include "modern_challenge_tier_selector.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, false, 0);
    assert(selector.count == 3);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Bronze);

    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, false, 1);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Silver);

    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, false, 2);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Gold);

    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, false, 3);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Gold);

    selector = navigate_modern_challenge_tier_selector(
        selector, UR_MODERN_HOST_NAV_RIGHT);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Bronze);
    selector = navigate_modern_challenge_tier_selector(
        selector, UR_MODERN_HOST_NAV_LEFT);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Gold);

    ModernChallengeTier confirmed = ModernChallengeTier::Bronze;
    assert(confirm_modern_challenge_tier(
        selector,
        ExecutionMode::Modern,
        true,
        false,
        UR_MODERN_HOST_NAV_CONFIRM,
        confirmed));
    assert(confirmed == ModernChallengeTier::Gold);

    // Hunter is one canonical Gold choice, not three invented variants.
    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, true, 0);
    assert(selector.count == 1);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Gold);
    selector = navigate_modern_challenge_tier_selector(
        selector, UR_MODERN_HOST_NAV_LEFT);
    assert(selected_modern_challenge_tier(selector) ==
           ModernChallengeTier::Gold);
    assert(confirm_modern_challenge_tier(
        selector,
        ExecutionMode::Modern,
        true,
        true,
        UR_MODERN_HOST_NAV_CONFIRM,
        confirmed));
    assert(confirmed == ModernChallengeTier::Gold);

    // No selector exists when Modern policy cannot offer the tour.
    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Authentic, true, false, 0);
    assert(selector.count == 0);
    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, false, false, 0);
    assert(selector.count == 0);
    selector = make_modern_challenge_tier_selector(
        ExecutionMode::Modern, true, false, 4);
    assert(selector.count == 0);

    return 0;
}
