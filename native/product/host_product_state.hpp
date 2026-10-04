#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

#include "output_resolution_policy.hpp"

namespace ur::product {

enum class ExecutionMode : std::uint8_t {
    Authentic = 0,
    Modern = 1,
};

struct ProductPolicy {
    bool host_profiles;
    bool host_settings;
    bool modern_commands;
};

constexpr ProductPolicy policy_for(ExecutionMode mode) noexcept {
    return mode == ExecutionMode::Modern
        ? ProductPolicy{true, true, true}
        : ProductPolicy{false, false, false};
}

enum class HostDisplayMode : std::uint8_t {
    Windowed = 0,
    BorderlessFullscreen = 1,
    Fullscreen = 2,
};

enum class HostVSyncMode : std::uint8_t {
    Off = 0,
    On = 1,
    Adaptive = 2,
};

enum class HostPresentationFpsMode : std::uint8_t {
    Game = 0,
    Fps60 = 1,
    Fps90 = 2,
    Fps120 = 3,
    Fps144 = 4,
    Native = 5,
};

struct HostSettings {
    bool vibration_enabled = true;
    bool pause_on_focus_loss = true;
    HostDisplayMode display_mode = HostDisplayMode::Windowed;
    HostVSyncMode vsync_mode = HostVSyncMode::On;
    HostPresentationFpsMode presentation_fps_mode =
        HostPresentationFpsMode::Game;
    // Semantic output size only; monitor refresh remains a separate concern.
    HostOutputResolution output_resolution =
        HostOutputResolution::native();

    bool operator==(const HostSettings& other) const noexcept {
        return vibration_enabled == other.vibration_enabled &&
               pause_on_focus_loss == other.pause_on_focus_loss &&
               display_mode == other.display_mode &&
               vsync_mode == other.vsync_mode &&
               presentation_fps_mode == other.presentation_fps_mode &&
               output_resolution == other.output_resolution;
    }
};

struct HostProductState {
    static constexpr std::uint32_t schema_version = 6;

    std::optional<std::string> active_profile_id;
    HostSettings settings{};

    bool operator==(const HostProductState& other) const noexcept {
        return active_profile_id == other.active_profile_id && settings == other.settings;
    }
};

struct DecodeResult {
    std::optional<HostProductState> state;
    std::string error;

    explicit operator bool() const noexcept { return state.has_value(); }
};

bool is_valid_profile_id(std::string_view value) noexcept;
std::string encode_host_product_state(const HostProductState& state);
DecodeResult decode_host_product_state(std::string_view encoded);

}  // namespace ur::product
