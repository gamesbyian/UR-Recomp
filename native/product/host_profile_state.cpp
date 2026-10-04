#include "host_profile_state.hpp"

#include <charconv>
#include <cstring>
#include <limits>
#include <map>
#include <sstream>

namespace ur::product {
namespace {

constexpr std::string_view kHeaderV0 = "UR-HOST-PROFILE/0";
constexpr std::string_view kHeaderV1 = "UR-HOST-PROFILE/1";

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
    if (text.size() != kStockSramBytes * 2) {
        return false;
    }
    std::array<std::uint8_t, kStockSramBytes> bytes{};
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        const int high = hex_value(text[i * 2]);
        const int low = hex_value(text[i * 2 + 1]);
        if (high < 0 || low < 0) {
            return false;
        }
        bytes[i] = static_cast<std::uint8_t>((high << 4) | low);
    }
    out = bytes;
    return true;
}

bool parse_generation(std::string_view text, std::uint64_t& out) noexcept {
    if (text.empty()) return false;
    std::uint64_t value = 0;
    const char* begin = text.data();
    const char* end = begin + text.size();
    const auto parsed = std::from_chars(begin, end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end) {
        return false;
    }
    out = value;
    return true;
}

}  // namespace

std::string encode_host_profile_state(const HostProfileState& state) {
    if (!is_valid_profile_id(state.profile_id)) {
        return {};
    }

    std::ostringstream out;
    out << kHeaderV1 << '\n';
    out << "profile=" << state.profile_id << '\n';
    out << "generation=" << state.autosave_generation << '\n';
    out << "stock_sram=";
    if (state.stock_sram) {
        out << encode_sram(*state.stock_sram);
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

    const bool legacy_v0 = line == kHeaderV0;
    if (!legacy_v0 && line != kHeaderV1) {
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

    const std::size_t expected_fields = legacy_v0 ? 2u : 3u;
    if (fields.size() != expected_fields ||
        fields.find("profile") == fields.end() ||
        fields.find("stock_sram") == fields.end() ||
        (!legacy_v0 && fields.find("generation") == fields.end())) {
        return {std::nullopt, false, "unexpected profile-state field set"};
    }

    HostProfileState state;
    state.profile_id = fields["profile"];
    if (!is_valid_profile_id(state.profile_id)) {
        return {std::nullopt, false, "invalid profile identifier"};
    }

    if (!legacy_v0 &&
        !parse_generation(fields["generation"], state.autosave_generation)) {
        return {std::nullopt, false, "invalid autosave generation"};
    }

    if (!decode_sram(fields["stock_sram"], state.stock_sram)) {
        return {std::nullopt, false, "invalid stock SRAM snapshot"};
    }

    return {state, legacy_v0, {}};
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
