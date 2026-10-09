#include "modern_restart_key_release.hpp"

#include <cassert>
#include <cstdint>

using namespace ur::product;

int main() {
    constexpr std::uint32_t start = 0x1000u;
    constexpr std::uint32_t left = 0x0200u;
    auto state = ModernRestartKeyRelease{true};
    for (int frame = 0; frame < 12; ++frame) {
        const auto result = modern_restart_key_filter(
            state, true, start | left);
        assert(result.inputs == left);
        assert(result.state.awaiting_return_release);
        state = result.state;
    }
    // A guest frame with no Start sampled does not clear physical ownership.
    auto result = modern_restart_key_filter(state, true, 0u);
    assert(result.inputs == 0u && result.state.awaiting_return_release);
    result = modern_restart_key_filter(result.state, true, start);
    assert(result.inputs == 0u);
    // After actual key-up, a new legitimate Start press is permitted.
    result = modern_restart_key_filter(result.state, false, start);
    assert(result.inputs == 0u && result.state.awaiting_return_release);
    result = modern_restart_key_filter(result.state, false, 0u);
    assert(!result.state.awaiting_return_release);
    result = modern_restart_key_filter(result.state, false, start);
    assert(result.inputs == start);
    // The fix must never change unrelated words or unarmed sessions.
    assert(modern_restart_key_filter({}, true, start).inputs == start);
    assert(modern_restart_key_filter({true}, true, left).inputs == left);
    static_assert(modern_restart_key_filter({true}, true, start).inputs == 0u);
    static_assert(modern_restart_key_filter({true}, false, start).inputs == 0u);
}
