#include "host_product_state.hpp"

#include <charconv>
#include <map>
#include <sstream>

namespace ur::product {
namespace {

constexpr std::string_view kHeaderV1 = "UR-HOST-STATE/1";
constexpr std::string_view kHeaderV2 = "UR-HOST-STATE/2";
constexpr std::string_view kHeaderV3 = "UR-HOST-STATE/3";
constexpr std::string_view kHeaderV4 = "UR-HOST-STATE/4";
constexpr std::string_view kHeaderV5 = "UR-HOST-STATE/5";
constexpr std::string_view kHeaderV6 = "UR-HOST-STATE/6";

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

bool parse_presentation_fps_mode(
    std::string_view text,
    HostPresentationFpsMode& out) noexcept {
    if (text == "game") {
        out = HostPresentationFpsMode::Game;
        return true;
    }
    if (text == "60") {
        out = HostPresentationFpsMode::Fps60;
        return true;
    }
    if (text == "90") {
        out = HostPresentationFpsMode::Fps90;
        return true;
    }
    if (text == "120") {
        out = HostPresentationFpsMode::Fps120;
        return true;
    }
    if (text == "144") {
        out = HostPresentationFpsMode::Fps144;
        return true;
    }
    if (text == "native") {
        out = HostPresentationFpsMode::Native;
        return true;
    }
    return false;
}

const char* presentation_fps_mode_name(
    HostPresentationFpsMode mode) noexcept {
    switch (mode) {
    case HostPresentationFpsMode::Game:
        return "game";
    case HostPresentationFpsMode::Fps60:
        return "60";
    case HostPresentationFpsMode::Fps90:
        return "90";
    case HostPresentationFpsMode::Fps120:
        return "120";
    case HostPresentationFpsMode::Fps144:
        return "144";
    case HostPresentationFpsMode::Native:
        return "native";
    }
    return nullptr;
}

bool parse_widescreen_mode(
    std::string_view text,
    HostWidescreenMode& out) noexcept {
    if (text == "original") {
        out = HostWidescreenMode::Original;
        return true;
    }
    if (text == "16x9") {
        out = HostWidescreenMode::Authentic16x9;
        return true;
    }
    return false;
}

const char* widescreen_mode_name(HostWidescreenMode mode) noexcept {
    switch (mode) {
    case HostWidescreenMode::Original:
        return "original";
    case HostWidescreenMode::Authentic16x9:
        return "16x9";
    }
    return nullptr;
}

bool parse_internal_render_scale(
    std::string_view text,
    HostInternalRenderScale& out) noexcept {
    if (text == "1x") {
        out = HostInternalRenderScale::X1;
        return true;
    }
    if (text == "2x") {
        out = HostInternalRenderScale::X2;
        return true;
    }
    if (text == "3x") {
        out = HostInternalRenderScale::X3;
        return true;
    }
    if (text == "4x") {
        out = HostInternalRenderScale::X4;
        return true;
    }
    return false;
}

const char* internal_render_scale_name(
    HostInternalRenderScale scale) noexcept {
    switch (scale) {
    case HostInternalRenderScale::X1:
        return "1x";
    case HostInternalRenderScale::X2:
        return "2x";
    case HostInternalRenderScale::X3:
        return "3x";
    case HostInternalRenderScale::X4:
        return "4x";
    }
    return nullptr;
}

bool parse_positive_int(std::string_view text, int& out) noexcept {
    if (text.empty()) return false;
    int value = 0;
    const char* begin = text.data();
    const char* end = begin + text.size();
    const auto parsed = std::from_chars(begin, end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end || value <= 0) {
        return false;
    }
    out = value;
    return true;
}

bool parse_output_resolution(
    std::string_view text,
    HostOutputResolution& out) noexcept {
    if (text == "native") {
        out = HostOutputResolution::native();
        return true;
    }
    const auto split = text.find('x');
    if (split == std::string_view::npos ||
        split == 0 ||
        split + 1 >= text.size() ||
        text.find('x', split + 1) != std::string_view::npos) {
        return false;
    }
    int width = 0;
    int height = 0;
    if (!parse_positive_int(text.substr(0, split), width) ||
        !parse_positive_int(text.substr(split + 1), height)) {
        return false;
    }
    out = HostOutputResolution::explicit_size(width, height);
    return true;
}

std::string output_resolution_name(
    const HostOutputResolution& resolution) {
    if (!valid_output_resolution(resolution)) {
        return {};
    }
    if (resolution.kind == HostOutputResolutionKind::Native) {
        return "native";
    }
    return std::to_string(resolution.width) + "x" +
           std::to_string(resolution.height);
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
    const char* presentation_fps =
        presentation_fps_mode_name(state.settings.presentation_fps_mode);
    const std::string output_resolution =
        output_resolution_name(state.settings.output_resolution);
    const char* widescreen =
        widescreen_mode_name(state.settings.widescreen_mode);
    const char* internal_render_scale =
        internal_render_scale_name(state.settings.internal_render_scale);
    if (!display_mode || !vsync_mode || !presentation_fps || !widescreen ||
        !internal_render_scale || output_resolution.empty()) {
        return {};
    }

    std::ostringstream out;
    out << kHeaderV6 << '\n';
    out << "profile=";
    if (state.active_profile_id) {
        out << *state.active_profile_id;
    }
    out << '\n';
    out << "pause_on_focus_loss=" << (state.settings.pause_on_focus_loss ? '1' : '0') << '\n';
    out << "vibration_enabled=" << (state.settings.vibration_enabled ? '1' : '0') << '\n';
    out << "display_mode=" << display_mode << '\n';
    out << "vsync=" << vsync_mode << '\n';
    out << "presentation_fps=" << presentation_fps << '\n';
    out << "output_resolution=" << output_resolution << '\n';
    out << "widescreen=" << widescreen << '\n';
    out << "internal_render_scale=" << internal_render_scale << '\n';
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
    const bool legacy_v4 = line == kHeaderV4;
    const bool legacy_v5 = line == kHeaderV5;
    if (!legacy_v1 && !legacy_v2 && !legacy_v3 && !legacy_v4 &&
        !legacy_v5 && line != kHeaderV6) {
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
    static constexpr std::string_view required_v3_v4[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled", "display_mode", "vsync"
    };
    static constexpr std::string_view required_v5[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled", "display_mode", "vsync",
        "presentation_fps"
    };
    static constexpr std::string_view required_v6_core[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled"
    };
    static constexpr std::string_view allowed_v6[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled",
        "display_mode", "vsync", "presentation_fps", "output_resolution",
        "widescreen", "internal_render_scale"
    };

    const bool current_v6 =
        !legacy_v1 && !legacy_v2 && !legacy_v3 && !legacy_v4 && !legacy_v5;
    const std::string_view* required = required_v6_core;
    std::size_t required_count = 3u;
    if (legacy_v1) {
        required = required_v1;
        required_count = 3u;
    } else if (legacy_v2) {
        required = required_v2;
        required_count = 4u;
    } else if (legacy_v3 || legacy_v4) {
        required = required_v3_v4;
        required_count = 5u;
    } else if (legacy_v5) {
        required = required_v5;
        required_count = 6u;
    }

    if (!current_v6 && fields.size() != required_count) {
        return {std::nullopt, "unexpected host-state field set"};
    }
    for (std::size_t i = 0; i < required_count; ++i) {
        if (fields.find(std::string(required[i])) == fields.end()) {
            return {std::nullopt, "missing host-state field"};
        }
    }

    if (current_v6) {
        for (const auto& field : fields) {
            bool known = false;
            for (const auto allowed : allowed_v6) {
                if (std::string_view{field.first} == allowed) {
                    known = true;
                    break;
                }
            }
            if (!known) {
                return {std::nullopt, "unexpected host-state field set"};
            }
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
    const auto display_mode = fields.find("display_mode");
    if (!legacy_v1 && display_mode != fields.end() &&
        !parse_display_mode(
            display_mode->second,
            state.settings.display_mode,
            !legacy_v2 && !legacy_v3)) {
        return {std::nullopt, "invalid host display mode"};
    }
    const auto vsync = fields.find("vsync");
    if (!legacy_v1 && !legacy_v2 && vsync != fields.end() &&
        !parse_vsync_mode(vsync->second, state.settings.vsync_mode)) {
        return {std::nullopt, "invalid host vsync mode"};
    }
    const auto presentation_fps = fields.find("presentation_fps");
    if (!legacy_v1 && !legacy_v2 && !legacy_v3 && !legacy_v4 &&
        presentation_fps != fields.end() &&
        !parse_presentation_fps_mode(
            presentation_fps->second,
            state.settings.presentation_fps_mode)) {
        return {std::nullopt, "invalid host presentation fps mode"};
    }
    const auto output_resolution = fields.find("output_resolution");
    if (!legacy_v1 && !legacy_v2 && !legacy_v3 && !legacy_v4 &&
        !legacy_v5 && output_resolution != fields.end() &&
        !parse_output_resolution(
            output_resolution->second,
            state.settings.output_resolution)) {
        return {std::nullopt, "invalid host output resolution"};
    }
    if (current_v6) {
        const auto widescreen = fields.find("widescreen");
        if (widescreen != fields.end() &&
            !parse_widescreen_mode(
                widescreen->second,
                state.settings.widescreen_mode)) {
            return {std::nullopt, "invalid host widescreen mode"};
        }
        const auto internal_render_scale =
            fields.find("internal_render_scale");
        if (internal_render_scale != fields.end() &&
            !parse_internal_render_scale(
                internal_render_scale->second,
                state.settings.internal_render_scale)) {
            return {std::nullopt, "invalid host internal render scale"};
        }
    }

    return {state, {}};
}

}  // namespace ur::product
