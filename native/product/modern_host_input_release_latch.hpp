#pragma once

#include <cstdint>

namespace ur::product {

// Release latch for the human P1 input word around host-owned surfaces.
//
// While a Modern surface owns human input, the whole word is withheld from the
// guest. A key or button that is still physically held when the surface closes
// (for example the Enter/Start press that dismisses the Welcome panel) must not
// reach the stock game as a fresh press on a later frame. Every bit held while
// the host owned input therefore stays withheld until that bit is released;
// bits pressed after the surface closed pass through unchanged.
//
// The latch never synthesizes input: it only ever clears bits of the word the
// player is currently holding.
struct ModernHostInputReleaseLatch {
    std::uint32_t held = 0u;
};

struct ModernHostInputFilterResult {
    ModernHostInputReleaseLatch latch;
    std::uint32_t inputs = 0u;
};

constexpr ModernHostInputFilterResult modern_host_input_filter(
    ModernHostInputReleaseLatch latch,
    bool host_owns_input,
    std::uint32_t inputs) noexcept {
    if (host_owns_input) {
        // Track exactly what is held now, so a bit pressed and released while
        // the host surface was open is not withheld after it closes.
        return {{inputs}, 0u};
    }
    latch.held &= inputs;
    return {latch, inputs & ~latch.held};
}

}  // namespace ur::product
