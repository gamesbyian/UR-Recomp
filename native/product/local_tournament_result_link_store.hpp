#pragma once

#include "local_tournament_fixture_launch.hpp"
#include "local_tournament_fixture_receipt.hpp"
#include "local_tournament_receipt_restore.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

// A link lives at one exact fixture index in the host-owned tournament data
// directory. It names the exact already-saved .urrun file and contains the
// existing canonical fixture receipt. No global Records matching or new
// replay/result schema is introduced.
enum class LocalTournamentResultLinkStatus {
    Committed,
    Restored,
    InvalidInput,
    MatchRejected,
    Conflict,
    IoError,
};

struct LocalTournamentResultLinkRestore {
    LocalTournamentResultLinkStatus status =
        LocalTournamentResultLinkStatus::InvalidInput;
    std::optional<LocalTournamentState> state;
    std::string detail;

    bool restored() const noexcept {
        return status == LocalTournamentResultLinkStatus::Restored &&
            state.has_value();
    }
};

// The caller must hold the attempt ID from the *live* ordinary-2P recorder.
// It must call this only after append_multiplayer_match_pair succeeded.
// Re-loads the EXACT run+sidecar from disk, commits the existing attempt-based
// reducer on a private copy, and publishes the resulting receipt + explicit
// artifact path atomically. Only on successful publication are launch and
// standings updated; failed writes cannot award points.
//
// The host is the serialized sole writer for a given fixture link path.
// On failure, the already-saved pair remains ordinary Multiplayer Records
// evidence but acquires no tournament membership.
LocalTournamentResultLinkStatus commit_saved_local_tournament_fixture(
    const std::string& fixture_links_directory,
    const std::string& multiplayer_runs_directory,
    const std::string& saved_run_path,
    std::string_view tournament_instance_id,
    std::string_view live_capture_attempt_id,
    LocalTournamentLaunchState& active_launch,
    LocalTournamentState& active_tournament);

// Fresh-process restore reads ONLY fixture-indexed links, resolves each
// explicit named run from the supplied runs root, admits the exact bound
// run/sidecar pair and delegates all-or-nothing projection to the existing
// receipt restorer. A missing link is an unplayed fixture; a broken link
// invalidates the entire restore. This does not scan/generalize Records.
LocalTournamentResultLinkRestore restore_saved_local_tournament_fixtures(
    const std::string& fixture_links_directory,
    const std::string& multiplayer_runs_directory,
    std::string_view tournament_instance_id,
    const LocalTournamentState& canonical_empty_schedule);

} // namespace ur::product
