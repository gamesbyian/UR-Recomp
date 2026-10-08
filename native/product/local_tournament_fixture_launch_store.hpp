#pragma once

#include "local_tournament_fixture_launch_codec.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

// The host owns placement under its existing per-user data root. A caller must
// serialize one active tournament's writes; this does not own a new store root,
// tournament identity generator, or guest/router lifecycle.
enum class LocalTournamentLaunchFileStatus {
    Saved,
    Loaded,
    Missing,
    Rejected,
    IoError,
};

struct LocalTournamentLaunchFileResult {
    LocalTournamentLaunchFileStatus status =
        LocalTournamentLaunchFileStatus::Rejected;
    std::optional<LocalTournamentPendingFixture> pending;
    std::string detail;

    bool loaded() const noexcept {
        return status == LocalTournamentLaunchFileStatus::Loaded &&
            pending.has_value();
    }
};

// Canonical bounded checkpoint, written through a same-directory temporary
// file and replaced only after complete write/flush/close. No guest SRAM.
LocalTournamentLaunchFileStatus save_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentPendingFixture& pending);

// The disk payload is untrusted until *both* strict decoding and binding to
// the active immutable roster, course pool, selected fixture and instance.
LocalTournamentLaunchFileResult load_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentState& active_tournament,
    std::string_view active_tournament_id);

// Retire only the exact checkpoint previously published by this owner.
// Unlike restore, this also works *after* the fixture has completed and is no
// longer eligible to resume. A stale caller cannot delete a newer attempt.
// Missing is idempotent; corrupted/mismatched files fail closed.
LocalTournamentLaunchFileStatus retire_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentPendingFixture& expected_pending);

} // namespace ur::product
