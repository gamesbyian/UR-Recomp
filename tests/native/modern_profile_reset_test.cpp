#include "modern_profile_reset.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto modern = ExecutionMode::Modern;
    const auto authentic = ExecutionMode::Authentic;

    constexpr std::uint32_t p1_left = 1u << 6;
    constexpr std::uint32_t p1_a = 1u << 8;
    constexpr std::uint32_t p1_l = 1u << 10;
    constexpr std::uint32_t p1_r = 1u << 11;
    constexpr std::uint32_t p2_l = 1u << (12 + 10);
    const std::uint32_t chordish =
        p1_left | p1_a | p1_l | p1_r | p2_l;

    assert(modern_profile_admin_filter_human_input(
               authentic, true, chordish) == chordish);
    assert(modern_profile_admin_filter_human_input(
               modern, false, chordish) == chordish);
    const auto filtered = modern_profile_admin_filter_human_input(
        modern, true, chordish);
    assert((filtered & p1_left) != 0);
    assert((filtered & p1_a) != 0);
    assert((filtered & p1_l) == 0);
    assert((filtered & p1_r) == 0);
    assert((filtered & p2_l) != 0);

    assert(!modern_profile_reset_confirming(
        modern_profile_reset_open(authentic, true, true)));
    assert(!modern_profile_reset_confirming(
        modern_profile_reset_open(modern, false, true)));
    assert(!modern_profile_reset_confirming(
        modern_profile_reset_open(modern, true, false)));

    auto state = modern_profile_reset_open(modern, true, true);
    assert(modern_profile_reset_confirming(state));

    const auto cancelled = modern_profile_reset_cancel(state);
    assert(!modern_profile_reset_confirming(cancelled));

    state = modern_profile_reset_open(modern, true, true);
    auto decision = modern_profile_reset_confirm(
        state, modern, true, true);
    assert(decision.action == ModernProfileResetAction::Execute);
    assert(!modern_profile_reset_confirming(decision.state));

    state = modern_profile_reset_open(modern, true, true);
    decision = modern_profile_reset_confirm(
        state, authentic, true, true);
    assert(decision.action == ModernProfileResetAction::None);

    state = modern_profile_reset_open(modern, true, true);
    decision = modern_profile_reset_confirm(
        state, modern, true, false);
    assert(decision.action == ModernProfileResetAction::None);

    decision = modern_profile_reset_confirm(
        {}, modern, true, true);
    assert(decision.action == ModernProfileResetAction::None);

    return 0;
}
