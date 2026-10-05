#pragma once

#include <cstdint>

#include "host_product_state.hpp"
#include "regional_presentation_secret.hpp"

namespace ur::product {

enum class RegionalPresentationUpdate : std::uint8_t {
    NoChange = 0,
    SaveRequired = 1,
};

/*
 * Narrow host-state adapter for the regional easter egg.
 *
 * It owns only recognition/session-local matcher state. A completed secret may
 * update HostProductState::regional_presentation and report SaveRequired.
 * Durable I/O remains the existing host-product store/platform adapter's job.
 */
class RegionalPresentationRuntime {
public:
    explicit RegionalPresentationRuntime(
        const HostProductState& state) noexcept {
        matcher_.set_current(state.regional_presentation);
    }

    RegionalPresentation current() const noexcept {
        return matcher_.current();
    }

    RegionalPresentationUpdate feed_text(
        HostProductState& state,
        char character,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    RegionalPresentationUpdate feed_controller(
        HostProductState& state,
        RegionalControllerAction action,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    void reset() noexcept { matcher_.reset(); }

private:
    void reconcile_external_state(const HostProductState& state) noexcept;
    RegionalPresentationUpdate apply_result(
        HostProductState& state,
        RegionalSecretResult result) noexcept;

    RegionalPresentationSecretMatcher matcher_{};
};

}  // namespace ur::product
