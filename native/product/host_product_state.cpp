#include "host_product_state.hpp"

#include <map>
#include <sstream>

namespace ur::product {
namespace {

constexpr std::string_view kHeader = "UR-HOST-STATE/1";

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

    std::ostringstream out;
    out << kHeader << '\n';
    out << "profile=";
    if (state.active_profile_id) {
        out << *state.active_profile_id;
    }
    out << '\n';
    out << "pause_on_focus_loss=" << (state.settings.pause_on_focus_loss ? '1' : '0') << '\n';
    out << "vibration_enabled=" << (state.settings.vibration_enabled ? '1' : '0') << '\n';
    return out.str();
}

DecodeResult decode_host_product_state(std::string_view encoded) {
    std::istringstream in{std::string(encoded)};
    std::string line;
    if (!std::getline(in, line) || line != kHeader) {
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

    static constexpr std::string_view required[] = {
        "profile", "pause_on_focus_loss", "vibration_enabled"
    };
    if (fields.size() != 3) {
        return {std::nullopt, "unexpected host-state field set"};
    }
    for (const auto key : required) {
        if (fields.find(std::string(key)) == fields.end()) {
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

    return {state, {}};
}

}  // namespace ur::product
