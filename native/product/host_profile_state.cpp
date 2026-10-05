#include "host_profile_state.hpp"

#include <charconv>
#include <cstring>
#include <limits>
#include <map>
#include <sstream>

namespace ur::product {
namespace {

constexpr std::string_view kHeaderV1 = "UR-HOST-PROFILE/1";
constexpr std::string_view kHeaderV2 = "UR-HOST-PROFILE/2";
constexpr std::string_view kHeaderV3 = "UR-HOST-PROFILE/3";
constexpr std::string_view kHeaderV4 = "UR-HOST-PROFILE/4";

int hex_value(char ch) noexcept {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return 10 + (ch - 'a');
    if (ch >= 'A' && ch <= 'F') return 10 + (ch - 'A');
    return -1;
}

std::string encode_sram(
    const std::array<std::uint8_t, kStockSramBytes>& bytes) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string out;
    out.resize(kStockSramBytes * 2);
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        out[i * 2] = digits[(bytes[i] >> 4) & 0x0f];
        out[i * 2 + 1] = digits[bytes[i] & 0x0f];
    }
    return out;
}

bool decode_sram(
    std::string_view text,
    std::optional<std::array<std::uint8_t, kStockSramBytes>>& out) noexcept {
    if (text.empty()) {
        out.reset();
        return true;
    }
    if (text.size() != kStockSramBytes * 2) return false;

    std::array<std::uint8_t, kStockSramBytes> bytes{};
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        const int high = hex_value(text[i * 2]);
        const int low = hex_value(text[i * 2 + 1]);
        if (high < 0 || low < 0) return false;
        bytes[i] = static_cast<std::uint8_t>((high << 4) | low);
    }
    out = bytes;
    return true;
}

template <typename T>
bool parse_unsigned(std::string_view text, T& out) noexcept {
    if (text.empty()) return false;
    unsigned long long value = 0;
    const char* begin = text.data();
    const char* end = begin + text.size();
    const auto parsed = std::from_chars(begin, end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end ||
        value > static_cast<unsigned long long>(
            std::numeric_limits<T>::max())) {
        return false;
    }
    out = static_cast<T>(value);
    return true;
}

std::string encode_tour_continuation(
    const std::optional<HostTourContinuation>& continuation) {
    if (!continuation) return {};
    if (!valid_tour_continuation(*continuation)) return {};

    std::ostringstream out;
    out << static_cast<unsigned>(continuation->rider_index) << ':'
        << static_cast<unsigned>(continuation->tour_row) << ':'
        << static_cast<unsigned>(continuation->medal_value) << ':';
    for (const auto flag : continuation->qualified) {
        out << static_cast<unsigned>(flag);
    }
    return out.str();
}

bool decode_tour_continuation(
    std::string_view text,
    std::optional<HostTourContinuation>& out) noexcept {
    if (text.empty()) {
        out.reset();
        return true;
    }

    const auto a = text.find(':');
    const auto b = a == std::string_view::npos
        ? std::string_view::npos : text.find(':', a + 1);
    const auto c = b == std::string_view::npos
        ? std::string_view::npos : text.find(':', b + 1);
    if (a == std::string_view::npos ||
        b == std::string_view::npos ||
        c == std::string_view::npos ||
        text.find(':', c + 1) != std::string_view::npos) {
        return false;
    }

    HostTourContinuation value;
    if (!parse_unsigned(text.substr(0, a), value.rider_index) ||
        !parse_unsigned(text.substr(a + 1, b - a - 1), value.tour_row) ||
        !parse_unsigned(text.substr(b + 1, c - b - 1), value.medal_value)) {
        return false;
    }

    const auto flags = text.substr(c + 1);
    if (flags.size() != kTourTrackCount) return false;
    for (std::size_t i = 0; i < flags.size(); ++i) {
        if (flags[i] != '0' && flags[i] != '1') return false;
        value.qualified[i] = static_cast<std::uint8_t>(flags[i] - '0');
    }
    if (!valid_tour_continuation(value)) return false;
    out = value;
    return true;
}

std::optional<CompletedRunGhostTarget> decode_ghost_target(
    std::string_view value) noexcept {
    if (value == "off") return CompletedRunGhostTarget::Off;
    if (value == "previous") return CompletedRunGhostTarget::Previous;
    if (value == "personal-best") return CompletedRunGhostTarget::PersonalBest;
    return std::nullopt;
}

std::string_view encode_ghost_target(
    CompletedRunGhostTarget target) noexcept {
    switch (target) {
    case CompletedRunGhostTarget::Off:
        return "off";
    case CompletedRunGhostTarget::Previous:
        return "previous";
    case CompletedRunGhostTarget::PersonalBest:
        return "personal-best";
    }
    return {};
}

}  // namespace

bool valid_tour_continuation(const HostTourContinuation& value) noexcept {
    if (value.rider_index >= 16 || value.tour_row >= 9 ||
        value.medal_value > 3) {
        return false;
    }

    unsigned completed = 0;
    for (const auto flag : value.qualified) {
        if (flag > 1) return false;
        completed += flag;
    }
    return completed > 0 && completed < kTourTrackCount;
}

std::optional<HostProfileState> make_default_host_profile_state(
    std::string_view profile_id) {
    if (!is_valid_profile_id(profile_id)) return std::nullopt;
    HostProfileState state;
    state.profile_id = std::string(profile_id);
    return state;
}

std::string encode_host_profile_state(const HostProfileState& state) {
    if (!is_valid_profile_id(state.profile_id)) return {};
    if (state.tour_continuation &&
        !valid_tour_continuation(*state.tour_continuation)) {
        return {};
    }

    std::ostringstream out;
    const auto ghost_target = encode_ghost_target(state.ghost_target);
    if (ghost_target.empty()) return {};

    out << kHeaderV4 << '\n';
    out << "profile=" << state.profile_id << '\n';
    out << "generation=" << state.autosave_generation << '\n';
    out << "stock_sram=";
    if (state.stock_sram) out << encode_sram(*state.stock_sram);
    out << '\n';
    out << "tour_resume=" << encode_tour_continuation(state.tour_continuation)
        << '\n';
    out << "ghost_target=" << ghost_target << '\n';
    out << "racer_name=";
    if (state.racer_identity) {
        if (!valid_racer_identity(*state.racer_identity)) return {};
        out << state.racer_identity->name;
    }
    out << '\n';
    out << "racer_index=";
    if (state.racer_identity) {
        out << static_cast<unsigned>(state.racer_identity->rider_index);
    }
    out << '\n';
    return out.str();
}

HostProfileDecodeResult decode_host_profile_state(std::string_view encoded) {
    std::istringstream in{std::string(encoded)};
    std::string line;
    if (!std::getline(in, line)) {
        return {std::nullopt, false, "unsupported or missing profile-state header"};
    }
    const bool legacy_v1 = line == kHeaderV1;
    const bool legacy_v2 = line == kHeaderV2;
    const bool legacy_v3 = line == kHeaderV3;
    const bool current_v4 = line == kHeaderV4;
    if (!legacy_v1 && !legacy_v2 && !legacy_v3 && !current_v4) {
        return {std::nullopt, false, "unsupported or missing profile-state header"};
    }

    std::map<std::string, std::string> fields;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        const auto split = line.find('=');
        if (split == std::string::npos || split == 0) {
            return {std::nullopt, false, "malformed profile-state field"};
        }
        const std::string key = line.substr(0, split);
        const std::string value = line.substr(split + 1);
        if (!fields.emplace(key, value).second) {
            return {std::nullopt, false, "duplicate profile-state field"};
        }
    }

    const std::size_t expected =
        legacy_v1 ? 3u : (legacy_v2 ? 4u : (legacy_v3 ? 5u : 7u));
    if (fields.size() != expected ||
        fields.find("profile") == fields.end() ||
        fields.find("generation") == fields.end() ||
        fields.find("stock_sram") == fields.end() ||
        (!legacy_v1 && fields.find("tour_resume") == fields.end()) ||
        ((legacy_v3 || current_v4) && fields.find("ghost_target") == fields.end()) ||
        (current_v4 && (fields.find("racer_name") == fields.end() ||
                        fields.find("racer_index") == fields.end()))) {
        return {std::nullopt, false, "unexpected profile-state field set"};
    }

    auto state = make_default_host_profile_state(fields["profile"]);
    if (!state) {
        return {std::nullopt, false, "invalid profile identifier"};
    }

    if (!parse_unsigned(fields["generation"], state->autosave_generation)) {
        return {std::nullopt, false, "invalid autosave generation"};
    }
    if (!decode_sram(fields["stock_sram"], state->stock_sram)) {
        return {std::nullopt, false, "invalid stock SRAM snapshot"};
    }
    if (!legacy_v1 &&
        !decode_tour_continuation(
            fields["tour_resume"], state->tour_continuation)) {
        return {std::nullopt, false, "invalid tour continuation"};
    }
    if (legacy_v3 || current_v4) {
        const auto ghost_target = decode_ghost_target(fields["ghost_target"]);
        if (!ghost_target) {
            return {std::nullopt, false, "invalid ghost target"};
        }
        state->ghost_target = *ghost_target;
    }
    if (current_v4) {
        const std::string& racer_name = fields["racer_name"];
        const std::string& racer_index = fields["racer_index"];
        if (racer_name.empty() != racer_index.empty()) {
            return {std::nullopt, false, "incomplete racer identity"};
        }
        if (!racer_name.empty()) {
            std::uint8_t index = 0;
            if (!parse_unsigned(racer_index, index)) {
                return {std::nullopt, false, "invalid racer index"};
            }
            HostRacerIdentity identity{racer_name, index};
            if (!valid_racer_identity(identity)) {
                return {std::nullopt, false, "invalid racer identity"};
            }
            state->racer_identity = std::move(identity);
        }
    }

    return {state, legacy_v1 || legacy_v2 || legacy_v3, {}};
}

HostProfileTransferStatus capture_stock_sram_for_profile(
    ExecutionMode mode,
    HostProfileState& state,
    const std::uint8_t* data,
    std::size_t size) noexcept {
    if (!policy_for(mode).host_profiles) {
        return HostProfileTransferStatus::RejectedByPolicy;
    }
    if (!data || size != kStockSramBytes ||
        !is_valid_profile_id(state.profile_id)) {
        return HostProfileTransferStatus::InvalidBuffer;
    }

    std::array<std::uint8_t, kStockSramBytes> snapshot{};
    std::memcpy(snapshot.data(), data, snapshot.size());
    state.stock_sram = snapshot;
    if (state.autosave_generation !=
        std::numeric_limits<std::uint64_t>::max()) {
        ++state.autosave_generation;
    }
    return HostProfileTransferStatus::Applied;
}

HostProfileTransferStatus restore_stock_sram_from_profile(
    ExecutionMode mode,
    const HostProfileState& state,
    std::uint8_t* data,
    std::size_t size) noexcept {
    if (!policy_for(mode).host_profiles) {
        return HostProfileTransferStatus::RejectedByPolicy;
    }
    if (!data || size != kStockSramBytes ||
        !is_valid_profile_id(state.profile_id)) {
        return HostProfileTransferStatus::InvalidBuffer;
    }
    if (!state.stock_sram) {
        return HostProfileTransferStatus::MissingSnapshot;
    }

    std::memcpy(data, state.stock_sram->data(), state.stock_sram->size());
    return HostProfileTransferStatus::Applied;
}

}  // namespace ur::product
