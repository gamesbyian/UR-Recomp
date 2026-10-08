#include "local_tournament_result_link_store.hpp"

#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ur::product {
namespace {
namespace fs = std::filesystem;
constexpr std::size_t kMaxLinkBytes = 6144;

std::string fixture_link_path(const std::string& directory,
                              std::size_t fixture_index) {
    return (fs::path(directory) /
        ("fixture-" + std::to_string(fixture_index) + ".urfixture")).string();
}

bool valid_run_filename(std::string_view name) {
    if (name.size() < 7 || name.size() > 240 ||
        name.substr(name.size() - 6) != ".urrun" ||
        name.find("..") != std::string_view::npos) return false;
    for (const char ch : name) {
        const bool letter = (ch >= 'a' && ch <= 'z') ||
                            (ch >= 'A' && ch <= 'Z');
        const bool digit = ch >= '0' && ch <= '9';
        if (!letter && !digit && ch != '-' && ch != '_' && ch != '.') {
            return false;
        }
    }
    return true;
}

std::optional<std::string> decode_hex(std::string_view hex) {
    if (hex.empty() || hex.size() % 2 || hex.size() > 4096) {
        return std::nullopt;
    }
    std::string value;
    value.reserve(hex.size() / 2);
    auto nibble = [](char ch) -> int {
        if (ch >= '0' && ch <= '9') return ch - '0';
        if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
        return -1;
    };
    for (std::size_t i = 0; i < hex.size(); i += 2) {
        const int hi = nibble(hex[i]);
        const int lo = nibble(hex[i + 1]);
        if (hi < 0 || lo < 0) return std::nullopt;
        value.push_back(static_cast<char>((hi << 4) | lo));
    }
    return value;
}

struct LinkData {
    std::string run_filename;
    std::string canonical_receipt;
};

std::string encode_link(const LinkData& link) {
    if (!valid_run_filename(link.run_filename) ||
        !decode_local_tournament_receipt(link.canonical_receipt)) return {};
    const std::string body =
        "UR-LOCAL-TOURNAMENT-RESULT-LINK/1\n"
        "run " + local_tournament_hex_bytes(link.run_filename) + "\n"
        "receipt " + local_tournament_hex_bytes(link.canonical_receipt) + "\n";
    const std::string sealed = body + "checksum " +
        local_tournament_hex64(local_tournament_fnv64(body)) + "\n";
    return sealed.size() <= kMaxLinkBytes ? sealed : std::string{};
}

std::optional<LinkData> decode_link(std::string_view encoded) {
    if (encoded.empty() || encoded.size() > kMaxLinkBytes) {
        return std::nullopt;
    }
    std::string_view lines[4];
    std::size_t position = 0;
    for (auto& line : lines) {
        const auto end = encoded.find('\n', position);
        if (end == std::string_view::npos) return std::nullopt;
        line = encoded.substr(position, end - position);
        position = end + 1;
    }
    if (position != encoded.size() ||
        lines[0] != "UR-LOCAL-TOURNAMENT-RESULT-LINK/1" ||
        lines[1].substr(0, 4) != "run " ||
        lines[2].substr(0, 8) != "receipt " ||
        lines[3].substr(0, 9) != "checksum ") return std::nullopt;
    const auto run = decode_hex(lines[1].substr(4));
    const auto receipt = decode_hex(lines[2].substr(8));
    if (!run || !receipt) return std::nullopt;
    LinkData result{*run, *receipt};
    if (encode_link(result) != encoded) return std::nullopt;
    return result;
}

std::optional<StoredMultiplayerMatch> load_exact_saved_pair(
    const std::string& multiplayer_runs_directory,
    const std::string& filename) {
    if (!valid_run_filename(filename) ||
        multiplayer_runs_directory.empty()) return std::nullopt;
    const std::string path =
        (fs::path(multiplayer_runs_directory) / filename).string();
    const auto run = load_completed_run_record_file(path);
    if (!run.loaded() || run.record->provenance.mode != "race-2p") {
        return std::nullopt;
    }
    const auto match =
        load_multiplayer_match_record_for_run(path, *run.record);
    if (!match) return std::nullopt;
    return StoredMultiplayerMatch{path, *run.record, *match.record};
}

// A fixture result is an immutable, instance-scoped receipt. A preflight
// fs::exists followed by REPLACE_EXISTING is not a transaction: concurrent
// game processes can both see it absent and overwrite one another's result.
// Give every writer its own atomically reserved staging directory, and
// publish the *final* fixture pathname with no-replace semantics.
enum class LinkPublishStatus { Published, Conflict, IoError };

std::optional<fs::path> reserve_link_staging(const fs::path& parent) {
    static std::atomic<std::uint64_t> serial{0};
    for (unsigned attempt = 0; attempt < 32; ++attempt) {
        const auto tick = std::chrono::steady_clock::now()
                              .time_since_epoch().count();
        const fs::path staging = parent /
            (".pending-urfixture-" + std::to_string(tick) + "-" +
             std::to_string(serial.fetch_add(1, std::memory_order_relaxed)));
        std::error_code ec;
        if (fs::create_directory(staging, ec)) return staging;
        if (ec) return std::nullopt;
    }
    return std::nullopt;
}

LinkPublishStatus publish_link(const std::string& path,
                               std::string_view bytes) {
    const fs::path final_path(path);
    const auto staging = reserve_link_staging(final_path.parent_path());
    if (!staging) return LinkPublishStatus::IoError;
    const fs::path staged_file = *staging / "fixture.tmp";
    std::error_code ec;
    auto cleanup = [&] {
        std::error_code ignored;
        fs::remove_all(*staging, ignored);
    };
    std::FILE* file = std::fopen(staged_file.string().c_str(), "wb");
    if (!file) {
        cleanup();
        return LinkPublishStatus::IoError;
    }
    const auto wrote = std::fwrite(bytes.data(), 1, bytes.size(), file);
    const bool flushed = std::fflush(file) == 0;
    const bool closed = std::fclose(file) == 0;
    if (wrote != bytes.size() || !flushed || !closed) {
        cleanup();
        return LinkPublishStatus::IoError;
    }

#if defined(_WIN32)
    // MoveFileExW without REPLACE_EXISTING refuses an existing destination.
    // Retain WRITE_THROUGH; staging and final share one directory.
    const bool published = MoveFileExW(staged_file.c_str(),
                                       final_path.c_str(),
                                       MOVEFILE_WRITE_THROUGH) != 0;
    const DWORD win_error = published ? ERROR_SUCCESS : GetLastError();
    const bool conflict = !published &&
        (win_error == ERROR_ALREADY_EXISTS || win_error == ERROR_FILE_EXISTS);
#else
    // A same-filesystem hard link atomically claims an absent name. Ordinary
    // rename() replaces existing names on POSIX and is forbidden for receipts.
    fs::create_hard_link(staged_file, final_path, ec);
    const bool published = !ec;
    const bool conflict = ec == std::errc::file_exists;
#endif
    cleanup();
    if (published) return LinkPublishStatus::Published;
    if (conflict) return LinkPublishStatus::Conflict;
    // Windows can report ACCESS_DENIED for an already present destination.
    // Recheck only for error classification; the no-replace publish has
    // already failed and will never overwrite the incumbent fixture.
    ec.clear();
    if (fs::exists(final_path, ec) && !ec) return LinkPublishStatus::Conflict;
    return LinkPublishStatus::IoError;
}

std::optional<std::string> read_link(const std::string& path) {
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) return std::nullopt;
    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return std::nullopt;
    }
    const long length = std::ftell(file);
    if (length <= 0 || length > static_cast<long>(kMaxLinkBytes) ||
        std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return std::nullopt;
    }
    std::string content(static_cast<std::size_t>(length), '\0');
    const bool complete =
        std::fread(content.data(), 1, content.size(), file) == content.size();
    const bool closed = std::fclose(file) == 0;
    const bool ok = complete && closed;
    if (!ok) return std::nullopt;
    return content;
}
} // namespace

LocalTournamentResultLinkStatus commit_saved_local_tournament_fixture(
    const std::string& fixture_links_directory,
    const std::string& multiplayer_runs_directory,
    const std::string& saved_run_path,
    std::string_view tournament_instance_id,
    std::string_view live_capture_attempt_id,
    LocalTournamentLaunchState& active_launch,
    LocalTournamentState& active_tournament) {
    using Status = LocalTournamentResultLinkStatus;
    if (fixture_links_directory.empty() ||
        multiplayer_runs_directory.empty() ||
        !active_launch.pending ||
        !local_tournament_valid_instance_token(tournament_instance_id) ||
        !local_tournament_valid_instance_token(live_capture_attempt_id)) {
        return Status::InvalidInput;
    }
    const fs::path given(saved_run_path);
    const std::string filename = given.filename().string();
    if (!valid_run_filename(filename) ||
        given.lexically_normal() !=
            (fs::path(multiplayer_runs_directory) / filename).lexically_normal()) {
        return Status::InvalidInput;
    }
    const auto saved_pair =
        load_exact_saved_pair(multiplayer_runs_directory, filename);
    if (!saved_pair) return Status::MatchRejected;

    const auto pending = *active_launch.pending;
    auto next_launch = active_launch;
    auto next_state = active_tournament;
    if (local_tournament_commit_live_result(
            next_launch, next_state, tournament_instance_id,
            live_capture_attempt_id, *saved_pair) !=
        LocalTournamentLaunchStatus::Recorded) {
        return Status::MatchRejected;
    }
    const auto receipt = make_local_tournament_receipt(
        next_state, tournament_instance_id, pending.fixture_index,
        *saved_pair);
    if (!receipt) return Status::MatchRejected;
    const std::string encoded = encode_link(
        {filename, encode_local_tournament_receipt(*receipt)});
    if (encoded.empty()) return Status::MatchRejected;

    const std::string path =
        fixture_link_path(fixture_links_directory, pending.fixture_index);
    std::error_code ec;
    const bool exists = fs::exists(path, ec);
    if (ec) return Status::IoError;
    if (exists) return Status::Conflict;
    const auto publication = publish_link(path, encoded);
    if (publication == LinkPublishStatus::Conflict) return Status::Conflict;
    if (publication != LinkPublishStatus::Published) return Status::IoError;

    active_launch = std::move(next_launch);
    active_tournament = std::move(next_state);
    return Status::Committed;
}

LocalTournamentResultLinkRestore restore_saved_local_tournament_fixtures(
    const std::string& fixture_links_directory,
    const std::string& multiplayer_runs_directory,
    std::string_view tournament_instance_id,
    const LocalTournamentState& canonical_empty_schedule) {
    using Status = LocalTournamentResultLinkStatus;
    if (fixture_links_directory.empty() ||
        multiplayer_runs_directory.empty() ||
        !local_tournament_valid_instance_token(tournament_instance_id)) {
        return {Status::InvalidInput, std::nullopt, "invalid restore context"};
    }
    std::vector<LocalTournamentReceiptEvidence> evidence;
    for (std::size_t i = 0; i < canonical_empty_schedule.fixtures.size(); ++i) {
        const std::string path = fixture_link_path(fixture_links_directory, i);
        std::error_code ec;
        const bool exists = fs::exists(path, ec);
        if (ec) return {Status::IoError, std::nullopt, "cannot inspect fixture"};
        if (!exists) continue;
        const auto content = read_link(path);
        const auto link = content ? decode_link(*content) : std::nullopt;
        if (!link) {
            return {Status::MatchRejected, std::nullopt,
                    "fixture link unreadable or noncanonical"};
        }
        const auto receipt =
            decode_local_tournament_receipt(link->canonical_receipt);
        if (!receipt || receipt->fixture_index != i ||
            receipt->tournament_id != tournament_instance_id) {
            return {Status::MatchRejected, std::nullopt,
                    "fixture link instance or index mismatch"};
        }
        const auto pair =
            load_exact_saved_pair(multiplayer_runs_directory,
                                  link->run_filename);
        if (!pair) {
            return {Status::MatchRejected, std::nullopt,
                    "fixture run and match pair unavailable"};
        }
        evidence.push_back({link->canonical_receipt, *pair});
    }
    const auto restored = restore_local_tournament_receipts(
        canonical_empty_schedule, tournament_instance_id, evidence);
    if (!restored.restored()) {
        return {Status::MatchRejected, std::nullopt,
                "fixture receipts fail all-or-nothing result admission"};
    }
    return {Status::Restored, std::move(restored.state), {}};
}

} // namespace ur::product
