#include "host_product_state.hpp"

#include <map>
#include <sstream>

namespace ur::product {
namespace {

constexpr std::string_view kHeaderV1 = "UR-HOST-STATE/1";
constexpr std::string_view kHeaderV2 = "UR-HOST-STATE/2";
constexpr std::string_view kHeaderV3 = "UR-HOST-STATE/3";
constexpr std::string_view kHeaderV4 = "UR-HOST-STATE/4";

bool parse_display_mode(
    std::string_view text,
    HostDisplayMode& out,
    bool allow_fullscreen) noexcept {
    if (text == "windowed") {
        out = HostDisplayMode::Windowed;
        return true;
    }
    if (text == "borderless") {
        out = HostDisplayMode::BorderlessFullscreen;
        return true;
    }
    if (allow_fullscreen && text == "fullscreen") {
        out = HostDisplayMode::Fullscreen;
        return true;
    }
    return false;
}

const char* display_mode_name(HostDisplayMode mode) noexcept {
    switch (mode) {
    case HostDisplayMode::Windowed:
        return "windowed";
    case HostDisplayMode::BorderlessFullscreen:
        return "borderless";
    case HostDisplayMode::Fullscreen:
        return "fullscreen";
    }
    return nullptr;
}

bool parse_vsync_mode(
    std::string_view text,
    HostVSyncMode& out) noexcept {
    if (text == "off") {
        out = HostVSyncMode::Off;
        return true;
    }
    if (text == "on") {
        out = HostVSyncMode::On;
        return true;
    }
    if (text == "adaptive") {
        out = HostVSyncMode::Adaptive;
        return true;
    }
    return false;
}

const char* vsync_mode_name(HostVSyncMode mode) noexcept {
    switch (mode) {
    case HostVSyncMode::Off:
        return "off";
    case HostVSyncMode::On:
        return "on";
    case HostVSyncMode::Adaptive:
        return "adaptive";
    }
    return nullptr;
}

bool parse_bool(std::string_view text, bool& out) noexcept {
    if (text == "0") {
        out = false;
        return true;
    }
    if (text == "1") {
        out = true;
        return true;
    }
    return false;
}

}  // namespace

bool is_valid_profile_id(std::string_view value) noexcept {
    if (value.empty() || value.size() > 64) {
        return false;
    }
    for (const char ch : value) {
        const bool alpha_num = (ch >= 'a' && ch <= 'z') ||
                               (ch >= 'A' && ch <= 'Z') ||
                               (ch >= '0' && ch <= '9');
        if (!alpha_num && ch != '-' && ch != '_' && ch != '.') {
            return false;
        }
    }
    return true;
}

std::string encode_host_product_state(const HostProductState& state) {
    if (state.active_profile_id && !is_valid_profile_id(*state.active_profile_id)) {
        return {};
    }

    const char* display_mode = display_mode_name(state.settings.display_mode);
    const char* vsync_mode = vsync_mode_name(state.settings.vsync_mode);
    if (!display_mode || !vsync_mode) {
        return {};
    }

    std::ostringstream out;
    out << kHeaderV4 << '\n';
    out << "profile=";
    if (state.active_profile_id) {
        out << *state.active_profile_id;
    }
    out << '\n';
    out << "pause_on_focus_loss=" << (state.settings.pause_on_focus_loss ? '1' : '0') << '\n';
    out << "vibration_enabled=" << (state.settings.vibration_enabled ? '1' : '0') << '\n';
    out << "display_mode=" << display_mode << '\n';
    out << "vsync=" << vsync_mode << '\n';
    return out.str();
}

DecodeResult decode_host_product_state(std::string_view encoded) {
    std::istringstream in{std::string(encoded)};
    std::string line;
    if (!std::getline(in, line)) {
        return {std::nullopt, "unsupported or missing host-state header"};
    }
    const bool legacy_v1 = line == kHeaderV1;
    const bool legacy_v2 = line == kHeaderV2;
    const bool legacy_v3 = line == kHeaderV3;
    if (!legacy_v1 && !legacy_v2 && !legacy_v3 && line != kHeaderV4) {
        return {std::nullopt, "unsupported or missing host-state header"};
    }

    std::map<std::string, std::string> fields;
    while (std::getline(in, line)) {
        if (line.empty()) {
            continue;
        }
        const auto split = line.find('=');
        if (split == std::string::npos || split == 0) {
            return {std::nullopt, "malformed host-state field"};
        }
        const std::string key = line.substr(0, split);
        const std::string value = line.substr(split + 1);
        if (!fields.emplace(key, value).second) {
            return {std::nullopt, "duplicate host-state field"};
        }
    }

    static constexpr std::string_view required_v1[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled"
    };
    static constexpr std::string_view required_v2[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled", "display_mode"
    };
    static constexpr std::string_view required_v3[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled", "display_mode", "vsync"
    };

    const std::string_view* required = required_v3;
    std::size_t required_count = 5u;
    if (legacy_v1) {
        required = required_v1;
        required_count = 3u;
    } else if (legacy_v2) {
        required = required_v2;
        required_count = 4u;
    }

    if (fields.size() != required_count) {
        return {std::nullopt, "unexpected host-state field set"};
    }
    for (std::size_t i = 0; i < required_count; ++i) {
        if (fields.find(std::string(required[i])) == fields.end()) {
            return {std::nullopt, "missing host-state field"};
        }
    }

    HostProductState state;
    const std::string& profile = fields.at("profile");
    if (!profile.empty()) {
        if (!is_valid_profile_id(profile)) {
            return {std::nullopt, "invalid profile id"};
        }
        state.active_profile_id = profile;
    }

    if (!parse_bool(fields.at("pause_on_focus_loss"), state.settings.pause_on_focus_loss) ||
        !parse_bool(fields.at("vibration_enabled"), state.settings.vibration_enabled)) {
        return {std::nullopt, "host-state booleans must be 0 or 1"};
    }
    if (!legacy_v1 &&
        !parse_display_mode(
            fields.at("display_mode"),
            state.settings.display_mode,
            !legacy_v2 && !legacy_v3)) {
        return {std::nullopt, "invalid host display mode"};
    }
    if (!legacy_v1 && !legacy_v2 &&
        !parse_vsync_mode(fields.at("vsync"), state.settings.vsync_mode)) {
        return {std::nullopt, "invalid host vsync mode"};
    }

    return {state, {}};
}

}  // namespace ur::product
