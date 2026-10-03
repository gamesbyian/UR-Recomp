#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

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
};

struct HostSettings {
    bool vibration_enabled = true;
    bool pause_on_focus_loss = true;
    HostDisplayMode display_mode = HostDisplayMode::Windowed;

    bool operator==(const HostSettings& other) const noexcept {
        return vibration_enabled == other.vibration_enabled &&
               pause_on_focus_loss == other.pause_on_focus_loss &&
               display_mode == other.display_mode;
    }
};

struct HostProductState {
    static constexpr std::uint32_t schema_version = 2;

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
