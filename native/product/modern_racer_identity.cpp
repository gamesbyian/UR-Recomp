#include "modern_racer_identity.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <string>

namespace ur::product {
namespace {

constexpr std::array<LegacyRacerPreset, 16> kLegacyPresets{{
    {0, "MIKE", "red"}, {1, "ANDREW", "blue"},
    {2, "MARTIN", "green"}, {3, "MELISSA", "yellow"},
    {4, "AMY", "orange"}, {5, "MALCOLM", "cyan"},
    {6, "MICHELLE", "lime"}, {7, "COLIN", "blue"},
    {8, "DAVE", "white"}, {9, "TONY", "black"},
    {10, "CAROL", "pink"}, {11, "CRAIG", "teal"},
    {12, "KEN", "purple"}, {13, "ROBBIE", "red"},
    {14, "ALICE", "green"}, {15, "STEVE", "blue"},
}};

constexpr std::array<std::string_view, 71> kForbiddenWords{{
    "shit","fuck","damn","bastard","cunt","arse","bottom","twat","butt",
    "wank","prick","licker","jism","jizz","face","crap","piss","penis",
    "head","bloody","hellfire","bitch","bum","cretin","poof","homo",
    "lesbian","dike","dyke","toss","ass","fudgepacker","come","gonad",
    "bugger","anal","breath","beaver","satan","sega","sonic","sperm",
    "shag","gleet","smeg","felch","clit","jerk","spew","barf","puke",
    "masturbate","handjob","blowjob","weener","pork","screw","genital",
    "scrotum","ball","cream","dildo","vibr","ringpiece","hardon","boner",
    "stiff","erection","knob","sphincter","rectum"
}};

std::string lower_ascii(std::string_view input) {
    std::string out(input);
    std::transform(out.begin(), out.end(), out.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return out;
}

}  // namespace

const std::array<LegacyRacerPreset, 16>& legacy_racer_presets() noexcept {
    return kLegacyPresets;
}

bool valid_racer_name(std::string_view name) noexcept {
    if (name.empty() || name.size() > 16) return false;
    bool has_visible_content = false;
    for (unsigned char ch : name) {
        if (ch < 0x20 || ch > 0x7e || ch == '=' || ch == '\n' || ch == '\r') {
            return false;
        }
        if (ch != ' ') has_visible_content = true;
    }
    return has_visible_content;
}

bool valid_racer_identity(const HostRacerIdentity& identity) noexcept {
    return identity.rider_index < kLegacyPresets.size() &&
           valid_racer_name(identity.name);
}

bool stock_forbidden_name_match(std::string_view name) noexcept {
    if (!valid_racer_name(name)) return false;
    const std::string lowered = lower_ascii(name);
    for (const auto word : kForbiddenWords) {
        if (lowered.find(word) != std::string::npos) return true;
    }
    return false;
}

std::optional<HostRacerIdentity> make_legacy_racer_identity(
    std::size_t preset_index) noexcept {
    if (preset_index >= kLegacyPresets.size()) return std::nullopt;
    const auto& preset = kLegacyPresets[preset_index];
    return HostRacerIdentity{std::string(preset.name), preset.rider_index};
}

}  // namespace ur::product
