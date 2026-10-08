#include "local_tournament_session_store.hpp"

#include "local_tournament_fixture_receipt.hpp"
#include "local_tournament_atomic_replace.hpp"

#include <cerrno>
#include <charconv>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
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
constexpr std::size_t kMaxSessionBytes = 4096;

bool catalog_authorizes(
    const std::vector<std::string>& entrants,
    const std::vector<HostProfileCatalogEntry>& catalog) {
    for (const auto& selected : entrants) {
        if (selected.empty() || selected.size() > 128) return false;
        bool found = false;
        for (const auto& entry : catalog) {
            if (entry.profile_id == selected) {
                found = true;
                break;
            }
        }
        if (!found) return false;
    }
    return true;
}

bool canonical_empty_schedule(const LocalTournamentState& schedule) {
    const auto rebuilt = make_local_round_robin(
        schedule.entrants, schedule.course_pool, schedule.legs);
    if (!rebuilt ||
        schedule.fixtures.size() != rebuilt->fixtures.size() ||
        schedule.results.size() != rebuilt->results.size()) {
        return false;
    }
    for (std::size_t i = 0; i < rebuilt->fixtures.size(); ++i) {
        const auto& a = schedule.fixtures[i];
        const auto& b = rebuilt->fixtures[i];
        if (schedule.results[i] ||
            a.round != b.round || a.player1 != b.player1 ||
            a.player2 != b.player2 || a.course_id != b.course_id) {
            return false;
        }
    }
    return true;
}

bool parse_size(std::string_view value, std::size_t* number) {
    if (value.empty() || value.size() > 2) return false;
    if (value.size() > 1 && value.front() == '0') return false;
    const auto converted = std::from_chars(
        value.data(), value.data() + value.size(), *number);
    return converted.ec == std::errc{} &&
        converted.ptr == value.data() + value.size();
}

LocalTournamentSessionFileResult fail(
    LocalTournamentSessionFileStatus status, const char* reason) {
    return {status, std::nullopt, reason};
}
} // namespace

std::optional<LocalTournamentSessionDefinition>
make_local_tournament_session_definition(
    std::string_view instance_id,
    const std::vector<std::string>& selected_profile_ids,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog,
    const std::vector<std::string>& ordinary_race_course_pool,
    std::size_t legs) {
    if (!local_tournament_valid_instance_token(instance_id) ||
        !catalog_authorizes(selected_profile_ids, authoritative_catalog)) {
        return std::nullopt;
    }
    auto schedule = make_local_round_robin(
        selected_profile_ids, ordinary_race_course_pool, legs);
    if (!schedule) return std::nullopt;
    return LocalTournamentSessionDefinition{
        std::string(instance_id), std::move(*schedule)};
}

std::string encode_local_tournament_session_definition(
    const LocalTournamentSessionDefinition& session) {
    if (!local_tournament_valid_instance_token(session.instance_id) ||
        !canonical_empty_schedule(session.empty_schedule)) return {};
    // A single-leg event keeps the original v1 bytes exactly; only a
    // multi-leg event uses v2, which adds one explicit "legs" record.
    const std::size_t legs = session.empty_schedule.legs;
    std::string body = legs == 1
        ? "UR-LOCAL-TOURNAMENT-SESSION/1\n"
        : "UR-LOCAL-TOURNAMENT-SESSION/2\n";
    body += "instance " + session.instance_id + "\n";
    if (legs != 1) body += "legs " + std::to_string(legs) + "\n";
    body += "entrants " +
        std::to_string(session.empty_schedule.entrants.size()) + "\n";
    for (const auto& id : session.empty_schedule.entrants) {
        if (id.empty() || id.size() > 128) return {};
        body += "entrant " + local_tournament_hex_bytes(id) + "\n";
    }
    body += "courses " +
        std::to_string(session.empty_schedule.course_pool.size()) + "\n";
    for (const auto& course : session.empty_schedule.course_pool) {
        body += "course " + course + "\n";
    }
    body += "schedule " + local_tournament_hex64(
        local_tournament_immutable_schedule_digest(
            session.empty_schedule)) + "\n";
    const std::string sealed = body + "checksum " +
        local_tournament_hex64(local_tournament_fnv64(body)) + "\n";
    return sealed.size() <= kMaxSessionBytes ? sealed : std::string{};
}

namespace {
std::optional<LocalTournamentSessionDefinition>
decode_session_impl(
    std::string_view encoded,
    const std::vector<HostProfileCatalogEntry>* authoritative_catalog) {
    if (encoded.empty() || encoded.size() > kMaxSessionBytes ||
        encoded.back() != '\n') return std::nullopt;
    std::vector<std::string_view> lines;
    std::size_t pos = 0;
    while (pos < encoded.size()) {
        const auto end = encoded.find('\n', pos);
        if (end == std::string_view::npos) return std::nullopt;
        lines.push_back(encoded.substr(pos, end - pos));
        pos = end + 1;
        if (lines.size() > 32) return std::nullopt;
    }
    if (lines.empty()) return std::nullopt;
    const bool v2 = lines[0] == "UR-LOCAL-TOURNAMENT-SESSION/2";
    if (!v2 && lines[0] != "UR-LOCAL-TOURNAMENT-SESSION/1") {
        return std::nullopt;
    }
    // v2 inserts exactly one "legs" record after the instance.
    const std::size_t shift = v2 ? 1 : 0;
    if (lines.size() < 8 + shift ||
        lines[1].substr(0, 9) != "instance " ||
        lines[2 + shift].substr(0, 9) != "entrants ") {
        return std::nullopt;
    }
    const auto instance = lines[1].substr(9);
    std::size_t legs = 1;
    if (v2 && (lines[2].substr(0, 5) != "legs " ||
               !parse_size(lines[2].substr(5), &legs) ||
               legs < 2 || legs > kLocalTournamentMaxLegs)) {
        return std::nullopt;
    }
    std::size_t n = 0;
    if (!parse_size(lines[2 + shift].substr(9), &n) ||
        n < 2 || n > kLocalTournamentMaxEntrants) return std::nullopt;
    const std::size_t courses_index = 3 + shift + n;
    if (lines.size() <= courses_index ||
        lines[courses_index].substr(0, 8) != "courses ") {
        return std::nullopt;
    }
    std::vector<std::string> entrants;
    entrants.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        const auto line = lines[3 + shift + i];
        if (line.substr(0, 8) != "entrant ") return std::nullopt;
        const auto decoded = local_tournament_unhex(line.substr(8));
        if (!decoded || decoded->empty() || decoded->size() > 128) {
            return std::nullopt;
        }
        entrants.push_back(std::move(*decoded));
    }
    std::size_t course_count = 0;
    if (!parse_size(lines[courses_index].substr(8), &course_count) ||
        course_count == 0 || course_count > 16 ||
        lines.size() != courses_index + course_count + 3) {
        return std::nullopt;
    }
    std::vector<std::string> courses;
    courses.reserve(course_count);
    for (std::size_t i = 0; i < course_count; ++i) {
        const auto line = lines[courses_index + i + 1];
        if (line.substr(0, 7) != "course ") return std::nullopt;
        courses.emplace_back(line.substr(7));
    }
    // Rebuild the entire fixture schedule from the canonical immutable inputs
    // rather than accepting persisted fixture/standings rows as authority.
    std::optional<LocalTournamentSessionDefinition> built;
    if (authoritative_catalog) {
        built = make_local_tournament_session_definition(
            instance, entrants, *authoritative_catalog, courses, legs);
    } else if (local_tournament_valid_instance_token(instance)) {
        auto schedule = make_local_round_robin(entrants, courses, legs);
        if (schedule) {
            built = LocalTournamentSessionDefinition{
                std::string(instance), std::move(*schedule)};
        }
    }
    if (!built) return std::nullopt;
    if (lines[lines.size() - 2] !=
        "schedule " + local_tournament_hex64(
            local_tournament_immutable_schedule_digest(
                built->empty_schedule))) {
        return std::nullopt;
    }
    // A strict re-encode simultaneously checks the checksum, field order,
    // canonical spelling, count forms and absence of trailing/extra records.
    if (encode_local_tournament_session_definition(*built) != encoded) {
        return std::nullopt;
    }
    return built;
}
} // namespace

std::optional<LocalTournamentSessionDefinition>
decode_local_tournament_session_definition(
    std::string_view encoded,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog) {
    return decode_session_impl(encoded, &authoritative_catalog);
}

std::optional<LocalTournamentSessionDefinition>
decode_local_tournament_historical_session_definition(
    std::string_view encoded) {
    return decode_session_impl(encoded, nullptr);
}

LocalTournamentSessionFileStatus save_local_tournament_session_definition(
    const std::string& path,
    const LocalTournamentSessionDefinition& session) {
    const std::string encoded =
        encode_local_tournament_session_definition(session);
    if (path.empty() || encoded.empty()) {
        return LocalTournamentSessionFileStatus::Rejected;
    }
    if (!write_tournament_replace_staged(path, encoded, "urtournament")) {
        return LocalTournamentSessionFileStatus::IoError;
    }
    return LocalTournamentSessionFileStatus::Saved;
}

namespace {
LocalTournamentSessionFileResult load_session_impl(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>* authoritative_catalog) {
    if (path.empty()) {
        return fail(LocalTournamentSessionFileStatus::Rejected,
                    "empty tournament session path");
    }
    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        return errno == ENOENT
            ? fail(LocalTournamentSessionFileStatus::Missing,
                   "tournament session absent")
            : fail(LocalTournamentSessionFileStatus::IoError,
                   "cannot open tournament session");
    }
    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return fail(LocalTournamentSessionFileStatus::IoError, "cannot size session");
    }
    const long length = std::ftell(file);
    if (length <= 0 || length > static_cast<long>(kMaxSessionBytes)) {
        std::fclose(file);
        return fail(LocalTournamentSessionFileStatus::Rejected,
                    "invalid session size");
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return fail(LocalTournamentSessionFileStatus::IoError,
                    "cannot rewind session");
    }
    std::string encoded(static_cast<std::size_t>(length), '\0');
    const auto read = std::fread(encoded.data(), 1, encoded.size(), file);
    const bool closed = std::fclose(file) == 0;
    if (read != encoded.size() || !closed) {
        return fail(LocalTournamentSessionFileStatus::IoError,
                    "incomplete session read");
    }
    auto session = authoritative_catalog
        ? decode_local_tournament_session_definition(
            encoded, *authoritative_catalog)
        : decode_local_tournament_historical_session_definition(encoded);
    if (!session) {
        return fail(LocalTournamentSessionFileStatus::Rejected,
                    "session not canonical or roster not admitted");
    }
    return {LocalTournamentSessionFileStatus::Loaded, std::move(*session), {}};
}
} // namespace

LocalTournamentSessionFileResult load_local_tournament_session_definition(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog) {
    return load_session_impl(path, &authoritative_catalog);
}

LocalTournamentSessionFileResult
load_historical_local_tournament_session_definition(const std::string& path) {
    return load_session_impl(path, nullptr);
}

} // namespace ur::product
