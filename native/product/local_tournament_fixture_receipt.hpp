#pragma once

#include "local_tournament_round_robin.hpp"

#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

// A persistence-ready *supplemental* receipt, never a substitute for the
// validated .urrun + .urmatch pair. Tournament membership must originate from
// an explicitly active session fixture; Records history cannot retroactively
// mint receipts from participant/course coincidence.
struct LocalTournamentFixtureReceipt {
    std::string tournament_id; // host-created unique 32-char lowercase hex
    std::size_t fixture_index = 0;
    std::string run_checksum; // canonical 16-char artifact checksum
    std::string course_id;
    std::string source_p1_profile;
    std::string source_p2_profile;
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    bool seats_swapped = false;
};

inline bool local_tournament_lower_hex(
    std::string_view s, std::size_t length) noexcept {
    if (s.size() != length) return false;
    for (const char ch : s) {
        if (!((ch >= '0' && ch <= '9') ||
              (ch >= 'a' && ch <= 'f'))) return false;
    }
    return true;
}

inline std::string local_tournament_hex_bytes(std::string_view bytes) {
    constexpr char digits[] = "0123456789abcdef";
    std::string out;
    out.reserve(bytes.size() * 2);
    for (const unsigned char ch : bytes) {
        out.push_back(digits[ch >> 4]);
        out.push_back(digits[ch & 15]);
    }
    return out;
}

inline std::optional<std::string> local_tournament_unhex(
    std::string_view bytes) {
    if (bytes.empty() || (bytes.size() % 2) || bytes.size() > 512) {
        return std::nullopt;
    }
    auto nibble = [](char ch) -> int {
        if (ch >= '0' && ch <= '9') return ch - '0';
        if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
        return -1;
    };
    std::string out;
    out.reserve(bytes.size() / 2);
    for (std::size_t i = 0; i < bytes.size(); i += 2) {
        const int a = nibble(bytes[i]);
        const int b = nibble(bytes[i + 1]);
        if (a < 0 || b < 0) return std::nullopt;
        out.push_back(static_cast<char>((a << 4) | b));
    }
    return out;
}

inline std::uint64_t local_tournament_fnv64(std::string_view text) noexcept {
    std::uint64_t value = 14695981039346656037ull;
    for (const unsigned char ch : text) {
        value ^= ch;
        value *= 1099511628211ull;
    }
    return value;
}

inline std::string local_tournament_hex64(std::uint64_t value) {
    constexpr char digits[] = "0123456789abcdef";
    std::string out(16, '0');
    for (int i = 15; i >= 0; --i) {
        out[static_cast<std::size_t>(i)] = digits[value & 15];
        value >>= 4;
    }
    return out;
}

inline const char* local_tournament_outcome_label(
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome) noexcept {
    using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
    switch (outcome) {
    case Outcome::Player1Win: return "p1";
    case Outcome::Player2Win: return "p2";
    case Outcome::Draw: return "draw";
    }
    return nullptr;
}

inline bool valid_local_tournament_receipt(
    const LocalTournamentFixtureReceipt& receipt) {
    if (!local_tournament_lower_hex(receipt.tournament_id, 32) ||
        !local_tournament_lower_hex(receipt.run_checksum, 16) ||
        !local_tournament_ordinary_race_course(receipt.course_id) ||
        receipt.source_p1_profile.empty() ||
        receipt.source_p2_profile.empty() ||
        receipt.source_p1_profile.size() > 128 ||
        receipt.source_p2_profile.size() > 128 ||
        !local_tournament_outcome_label(receipt.outcome)) {
        return false;
    }
    // Canonical ASCII storage identity: no duplicate Windows-equivalent seats.
    const auto p1 = local_tournament_storage_key(receipt.source_p1_profile);
    const auto p2 = local_tournament_storage_key(receipt.source_p2_profile);
    return p1 == receipt.source_p1_profile &&
        p2 == receipt.source_p2_profile && p1 != p2;
}

inline std::string encode_local_tournament_receipt(
    const LocalTournamentFixtureReceipt& receipt) {
    if (!valid_local_tournament_receipt(receipt)) return {};
    std::string body =
        "UR-LOCAL-TOURNAMENT-FIXTURE/1\n"
        "tournament " + receipt.tournament_id + "\n"
        "fixture " + std::to_string(receipt.fixture_index) + "\n"
        "run_checksum " + receipt.run_checksum + "\n"
        "course " + receipt.course_id + "\n"
        "source_p1 " + local_tournament_hex_bytes(receipt.source_p1_profile) + "\n"
        "source_p2 " + local_tournament_hex_bytes(receipt.source_p2_profile) + "\n"
        "outcome " + local_tournament_outcome_label(receipt.outcome) + "\n"
        "swapped " + (receipt.seats_swapped ? "1\n" : "0\n");
    return body + "checksum " +
        local_tournament_hex64(local_tournament_fnv64(body)) + "\n";
}

// Strict canonical byte codec: no duplicate/unknown fields, changed order,
// alternate integer spelling, extra bytes or unchecked primary artifact.
inline std::optional<LocalTournamentFixtureReceipt>
decode_local_tournament_receipt(std::string_view bytes) {
    if (bytes.empty() || bytes.size() > 2048) return std::nullopt;
    std::array<std::string_view, 10> lines{};
    std::size_t offset = 0;
    for (auto& line : lines) {
        const auto end = bytes.find('\n', offset);
        if (end == std::string_view::npos) return std::nullopt;
        line = bytes.substr(offset, end - offset);
        offset = end + 1;
    }
    if (offset != bytes.size() ||
        lines[0] != "UR-LOCAL-TOURNAMENT-FIXTURE/1") {
        return std::nullopt;
    }
    auto value = [](std::string_view line,
                    std::string_view prefix) -> std::optional<std::string_view> {
        if (line.substr(0, prefix.size()) != prefix) return std::nullopt;
        return line.substr(prefix.size());
    };
    const auto id = value(lines[1], "tournament ");
    const auto fixture = value(lines[2], "fixture ");
    const auto checksum = value(lines[3], "run_checksum ");
    const auto course = value(lines[4], "course ");
    const auto p1 = value(lines[5], "source_p1 ");
    const auto p2 = value(lines[6], "source_p2 ");
    const auto outcome = value(lines[7], "outcome ");
    const auto swapped = value(lines[8], "swapped ");
    const auto seal = value(lines[9], "checksum ");
    if (!id || !fixture || !checksum || !course || !p1 || !p2 ||
        !outcome || !swapped || !seal ||
        !local_tournament_lower_hex(*seal, 16)) return std::nullopt;
    std::size_t number = 0;
    const auto parsed = std::from_chars(
        fixture->data(), fixture->data() + fixture->size(), number);
    if (parsed.ec != std::errc{} ||
        parsed.ptr != fixture->data() + fixture->size()) {
        return std::nullopt;
    }
    const auto decoded_p1 = local_tournament_unhex(*p1);
    const auto decoded_p2 = local_tournament_unhex(*p2);
    if (!decoded_p1 || !decoded_p2) return std::nullopt;
    using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
    Outcome result = Outcome::Draw;
    if (*outcome == "p1") result = Outcome::Player1Win;
    else if (*outcome == "p2") result = Outcome::Player2Win;
    else if (*outcome != "draw") return std::nullopt;
    if (*swapped != "0" && *swapped != "1") return std::nullopt;
    LocalTournamentFixtureReceipt receipt{
        std::string(*id), number, std::string(*checksum),
        std::string(*course), *decoded_p1, *decoded_p2,
        result, *swapped == "1",
    };
    if (!valid_local_tournament_receipt(receipt) ||
        encode_local_tournament_receipt(receipt) != bytes) {
        return std::nullopt;
    }
    return receipt;
}

// Admission requires an explicit active fixture and an independently loaded
// catalog-verified run/sidecar pair. No inference from filename/time/history.
inline std::optional<LocalTournamentFixtureReceipt>
make_local_tournament_receipt(
    const LocalTournamentState& tournament,
    std::string_view tournament_id,
    std::size_t fixture_index,
    const StoredMultiplayerMatch& admitted) {
    if (!local_tournament_lower_hex(tournament_id, 32) ||
        fixture_index >= tournament.fixtures.size() ||
        fixture_index >= tournament.results.size() ||
        !tournament.results[fixture_index]) return std::nullopt;
    const auto& completed = *tournament.results[fixture_index];
    // Recheck the result from a clean fixture before sealing provenance,
    // rather than trusting mutable in-memory projection fields.
    LocalTournamentState probe = tournament;
    probe.results.assign(probe.fixtures.size(), std::nullopt);
    if (record_local_tournament_result(probe, fixture_index, admitted) !=
        LocalTournamentRecordStatus::Applied ||
        !probe.results[fixture_index] ||
        probe.results[fixture_index]->run_artifact_checksum !=
            completed.run_artifact_checksum ||
        probe.results[fixture_index]->outcome != completed.outcome ||
        probe.results[fixture_index]->seats_swapped != completed.seats_swapped) {
        return std::nullopt;
    }
    const auto& bound = admitted.match.context.match;
    LocalTournamentFixtureReceipt receipt{
        std::string(tournament_id),
        fixture_index,
        admitted.match.run_artifact_checksum,
        admitted.match.context.course_id,
        local_tournament_storage_key(bound.player1.profile_id),
        local_tournament_storage_key(bound.player2.profile_id),
        bound.result.outcome,
        completed.seats_swapped,
    };
    if (!valid_local_tournament_receipt(receipt)) return std::nullopt;
    return receipt;
}

inline bool local_tournament_receipt_matches(
    const LocalTournamentFixtureReceipt& receipt,
    const LocalTournamentState& tournament,
    std::string_view active_tournament_id,
    const StoredMultiplayerMatch& admitted) {
    if (receipt.tournament_id != active_tournament_id ||
        !valid_local_tournament_receipt(receipt) ||
        receipt.fixture_index >= tournament.fixtures.size()) return false;
    // A caller may be restoring a fresh process before results are attached:
    // compare the receipt to a clean explicit fixture and source pair.
    LocalTournamentState probe = tournament;
    probe.results.assign(probe.fixtures.size(), std::nullopt);
    if (record_local_tournament_result(
            probe, receipt.fixture_index, admitted) !=
        LocalTournamentRecordStatus::Applied) return false;
    const auto& bound = admitted.match.context.match;
    return receipt.run_checksum == admitted.match.run_artifact_checksum &&
        receipt.course_id == tournament.fixtures[receipt.fixture_index].course_id &&
        receipt.source_p1_profile ==
            local_tournament_storage_key(bound.player1.profile_id) &&
        receipt.source_p2_profile ==
            local_tournament_storage_key(bound.player2.profile_id) &&
        receipt.outcome == bound.result.outcome &&
        receipt.seats_swapped ==
            probe.results[receipt.fixture_index]->seats_swapped;
}

} // namespace ur::product
