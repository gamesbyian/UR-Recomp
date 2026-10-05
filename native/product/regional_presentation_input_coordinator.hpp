#pragma once

#include <array>
#include <cstdint>

#include "regional_presentation_runtime.hpp"

namespace ur::product {

struct RegionalInputDecision {
    bool consume = false;
    RegionalPresentationUpdate update = RegionalPresentationUpdate::NoChange;
};

class RegionalPresentationInputCoordinator {
public:
    explicit RegionalPresentationInputCoordinator(
        const HostProductState& state) noexcept
        : runtime_(state) {}

    RegionalPresentation current() const noexcept { return runtime_.current(); }

    RegionalInputDecision keyboard_key(
        HostProductState& state,
        int key,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    RegionalInputDecision controller_button(
        HostProductState& state,
        RegionalControllerAction action,
        bool pressed,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    void reset() noexcept;

private:
    static bool secret_letter(char ch) noexcept;
    static std::size_t action_index(RegionalControllerAction action) noexcept;

    RegionalPresentationRuntime runtime_;
    std::array<bool, 5> owned_controller_release_{};
};

}  // namespace ur::product
