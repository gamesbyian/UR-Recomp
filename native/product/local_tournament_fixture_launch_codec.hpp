#pragma once

#include "local_tournament_fixture_launch.hpp"

#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

// Strict, bounded, canonical pending-launch checkpoint. The future host store
// must atomically publish it *before* the guest route and retire it on abort or
// receipt publication. A decoded checkpoint has no authority until it matches
// the host's active instance and current immutable tournament fixture.
inline constexpr std::size_t kLocalTournamentLaunchMaxBytes = 2048;

inline std::uint64_t local_tournament_launch_fnv64(
    std::string_view bytes) noexcept {
    std::uint64_t hash = 14695981039346656037ull;
    for (const unsigned char ch : bytes) {
        hash ^= ch;
        hash *= 1099511628211ull;
    }
    return hash;
}

inline std::string local_tournament_launch_hex64(std::uint64_t value) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string result(16, '0');
    for (int i = 15; i >= 0; --i) {
        result[static_cast<std::size_t>(i)] = digits[value & 15u];
        value >>= 4u;
    }
    return result;
}

inline std::string local_tournament_launch_hex(std::string_view text) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(text.size() * 2u);
    for (const unsigned char ch : text) {
        result += digits[ch >> 4u];
        result += digits[ch & 15u];
    }
    return result;
}

inline std::optional<std::string> local_tournament_launch_unhex(
    std::string_view encoded) {
    if (encoded.empty() || encoded.size() > 256 ||
        encoded.size() % 2u != 0u) return std::nullopt;
    auto nibble = [](char ch) -> int {
        if (ch >= '0' && ch <= '9') return ch - '0';
        if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
        return -1;
    };
    std::string decoded;
    decoded.reserve(encoded.size() / 2u);
    for (std::size_t i = 0; i < encoded.size(); i += 2u) {
        const int hi = nibble(encoded[i]), lo = nibble(encoded[i + 1u]);
        if (hi < 0 || lo < 0) return std::nullopt;
        decoded += static_cast<char>((hi << 4) | lo);
    }
    return decoded;
}

inline bool local_tournament_valid_pending_fixture(
    const LocalTournamentPendingFixture& p) {
    return local_tournament_valid_instance_token(p.tournament_id) &&
        local_tournament_valid_instance_token(p.attempt_id) &&
        p.tournament_id != p.attempt_id &&
        // 8 entrants x up to 3 legs: 84 fixtures across 21 rounds.
        p.fixture_index < 84u && p.round >= 1u && p.round <= 21u &&
        local_tournament_ordinary_race_course(p.course_id) &&
        !p.first_profile_key.empty() && !p.second_profile_key.empty() &&
        p.first_profile_key.size() <= 128u &&
        p.second_profile_key.size() <= 128u &&
        p.first_profile_key ==
            local_tournament_storage_key(p.first_profile_key) &&
        p.second_profile_key ==
            local_tournament_storage_key(p.second_profile_key) &&
        p.first_profile_key != p.second_profile_key;
}

inline std::string encode_local_tournament_pending_fixture(
    const LocalTournamentPendingFixture& p) {
    if (!local_tournament_valid_pending_fixture(p)) return {};
    std::string body =
        "UR-LOCAL-TOURNAMENT-LAUNCH/1\n"
        "tournament " + p.tournament_id + "\n"
        "attempt " + p.attempt_id + "\n"
        "fixture " + std::to_string(p.fixture_index) + "\n"
        "round " + std::to_string(p.round) + "\n"
        "first " + local_tournament_launch_hex(p.first_profile_key) + "\n"
        "second " + local_tournament_launch_hex(p.second_profile_key) + "\n"
        "course " + p.course_id + "\n"
        "schedule " + local_tournament_launch_hex64(
            p.immutable_schedule_digest) + "\n";
    const std::string encoded = body + "checksum " +
        local_tournament_launch_hex64(local_tournament_launch_fnv64(body)) +
        "\n";
    return encoded.size() <= kLocalTournamentLaunchMaxBytes
        ? encoded : std::string{};
}

inline std::optional<LocalTournamentPendingFixture>
decode_local_tournament_pending_fixture(std::string_view bytes) {
    if (bytes.empty() || bytes.size() > kLocalTournamentLaunchMaxBytes) {
        return std::nullopt;
    }
    std::array<std::string_view, 10> lines{};
    std::size_t offset = 0;
    for (auto& line : lines) {
        const std::size_t end = bytes.find('\n', offset);
        if (end == std::string_view::npos) return std::nullopt;
        line = bytes.substr(offset, end - offset);
        offset = end + 1u;
    }
    if (offset != bytes.size() ||
        lines[0] != "UR-LOCAL-TOURNAMENT-LAUNCH/1") {
        return std::nullopt;
    }
    auto val = [](std::string_view line,
                  std::string_view prefix) -> std::optional<std::string_view> {
        if (line.substr(0, prefix.size()) != prefix) return std::nullopt;
        return line.substr(prefix.size());
    };
    const auto tournament = val(lines[1], "tournament ");
    const auto attempt = val(lines[2], "attempt ");
    const auto fixture = val(lines[3], "fixture ");
    const auto round = val(lines[4], "round ");
    const auto first = val(lines[5], "first ");
    const auto second = val(lines[6], "second ");
    const auto course = val(lines[7], "course ");
    const auto schedule = val(lines[8], "schedule ");
    const auto seal = val(lines[9], "checksum ");
    if (!tournament || !attempt || !fixture || !round || !first ||
        !second || !course || !schedule || !seal ||
        schedule->size() != 16u || seal->size() != 16u) {
        return std::nullopt;
    }
    for (const auto field : {*seal, *schedule}) {
        for (const char ch : field) {
            if (!((ch >= '0' && ch <= '9') ||
                  (ch >= 'a' && ch <= 'f'))) return std::nullopt;
        }
    }
    const std::size_t body_end = bytes.size() - lines[9].size() - 1u;
    if (local_tournament_launch_hex64(
            local_tournament_launch_fnv64(bytes.substr(0, body_end))) !=
        *seal) return std::nullopt;

    std::size_t fixture_index = 0, round_index = 0;
    std::uint64_t immutable_digest = 0;
    const auto hash = std::from_chars(
        schedule->data(), schedule->data() + schedule->size(),
        immutable_digest, 16);
    const auto f = std::from_chars(
        fixture->data(), fixture->data() + fixture->size(), fixture_index);
    const auto n = std::from_chars(
        round->data(), round->data() + round->size(), round_index);
    if (hash.ec != std::errc{} ||
        hash.ptr != schedule->data() + schedule->size() ||
        f.ec != std::errc{} ||
        f.ptr != fixture->data() + fixture->size() ||
        n.ec != std::errc{} ||
        n.ptr != round->data() + round->size()) {
        return std::nullopt;
    }
    const auto p1 = local_tournament_launch_unhex(*first);
    const auto p2 = local_tournament_launch_unhex(*second);
    if (!p1 || !p2) return std::nullopt;
    LocalTournamentPendingFixture pending{
        std::string(*tournament), std::string(*attempt),
        fixture_index, round_index, *p1, *p2, std::string(*course),
        immutable_digest,
    };
    // Encoding is the sole canonical spelling, including fixed key order,
    // lowercase hex, decimal integers and exactly one final newline.
    if (!local_tournament_valid_pending_fixture(pending) ||
        encode_local_tournament_pending_fixture(pending) != bytes) {
        return std::nullopt;
    }
    return pending;
}

// Restart/restore admission: a checksum-valid token is not a free-standing
// entitlement. It must describe this exact active session's unfinished fixture
// and the immutable roster/schedule from the canonical tournament model.
inline bool local_tournament_restore_pending_fixture(
    LocalTournamentLaunchState& launch,
    const LocalTournamentState& tournament,
    std::string_view active_tournament_id,
    std::string_view encoded) {
    if (launch.pending) return false;
    const auto decoded = decode_local_tournament_pending_fixture(encoded);
    if (!decoded || decoded->tournament_id != active_tournament_id ||
        !local_tournament_pending_matches_fixture(*decoded, tournament)) {
        return false;
    }
    launch.pending = std::move(*decoded);
    return true;
}

} // namespace ur::product
