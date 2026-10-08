#pragma once

#include "host_profile_catalog.hpp"
#include "local_tournament_fixture_launch.hpp"

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

// The durable identity/immutable schedule of one Modern tournament. Completed
// results live ONLY in independently validated fixture receipts, never here.
struct LocalTournamentSessionDefinition {
    std::string instance_id;
    LocalTournamentState empty_schedule;
};

enum class LocalTournamentSessionFileStatus {
    Saved,
    Loaded,
    Missing,
    Rejected,
    IoError,
};

struct LocalTournamentSessionFileResult {
    LocalTournamentSessionFileStatus status =
        LocalTournamentSessionFileStatus::Rejected;
    std::optional<LocalTournamentSessionDefinition> session;
    std::string detail;

    bool loaded() const noexcept {
        return status == LocalTournamentSessionFileStatus::Loaded &&
            session.has_value();
    }
};

// The caller supplies the exact explicitly selected Modern profile IDs, not
// controller seats or guest rider indices. Each must be in the host catalog.
// Instance IDs must be independently minted by the host, never derived from
// player names or matches.
std::optional<LocalTournamentSessionDefinition>
make_local_tournament_session_definition(
    std::string_view instance_id,
    const std::vector<std::string>& selected_profile_ids,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog,
    const std::vector<std::string>& ordinary_race_course_pool);

// Strict bounded canonical v1 payload. On fresh-process decode, membership is
// rechecked against the then-current catalog, so deleted/renamed profiles do
// not silently inherit someone else's tournament fixture.
std::string encode_local_tournament_session_definition(
    const LocalTournamentSessionDefinition& session);
std::optional<LocalTournamentSessionDefinition>
decode_local_tournament_session_definition(
    std::string_view canonical_bytes,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog);

// Historical COMPLETED Records need not depend on the participant profiles
// still existing today. This read-only decoder keeps the exact same bounded
// canonical structure/digest rules; only *current catalog membership* is
// relaxed. Completed fixture receipts and separately validated saved 2P pairs
// must still fully establish all event results before display.
std::optional<LocalTournamentSessionDefinition>
decode_local_tournament_historical_session_definition(
    std::string_view canonical_bytes);
LocalTournamentSessionFileResult
load_historical_local_tournament_session_definition(
    const std::string& path);

LocalTournamentSessionFileStatus save_local_tournament_session_definition(
    const std::string& path,
    const LocalTournamentSessionDefinition& session);
LocalTournamentSessionFileResult load_local_tournament_session_definition(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog);

} // namespace ur::product
