#pragma once

#include <cstdint>

namespace ur::product {

// The keyboard Enter that confirms host Restart is also the default mapped
// guest Start. Guest frames are frozen while the host Pause menu is visible,
// so the ordinary word-sampling release latch may never see that held edge.
// The SDL physical-key state, sampled independently of guest frame hold,
// keeps Start blocked until the confirming key is physically released.
struct ModernRestartKeyRelease {
    bool awaiting_return_release = false;
};

struct ModernRestartKeyFilterResult {
    ModernRestartKeyRelease state{};
    std::uint32_t inputs = 0;
};

constexpr ModernRestartKeyFilterResult modern_restart_key_filter(
    ModernRestartKeyRelease state,
    bool physical_return_held,
    std::uint32_t inputs) noexcept {
    if (!state.awaiting_return_release) return {state, inputs};
    // After SDL reports key-up, the framework's mapped word can still
    // contain the old Start level. Require both physical release AND a
    // sampled zero Start bit before permitting a subsequent new press.
    constexpr std::uint32_t kStart = 0x1000u;
    if (!physical_return_held && !(inputs & kStart))
        return {{false}, inputs};
    return {state, inputs & ~kStart};
}

}  // namespace ur::product
