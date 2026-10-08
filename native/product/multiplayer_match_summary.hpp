#pragma once

#include "multiplayer_match_catalog.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

/*
 * Aggregate history over already-admitted ordinary-2P Race match pairs.
 *
 * Every count is derived only from the persisted, checksum/course-bound
 * result outcome of each admitted pair. Profiles are keyed by their storage
 * identity (the same case-insensitive comparison the match binder uses), so a
 * Windows-equivalent spelling can never split one profile's history. Records
 * are kept in profile-identity order: this is aggregate history, not Local
 * Tournament standings, and it implies no ranking, points or seeding.
 */
struct MultiplayerProfileMatchRecord {
    std::string profile_id;   // spelling from the most recent admitted match
    std::string racer_name;   // racer name from the most recent admitted match
    std::size_t played = 0;
    std::size_t wins = 0;
    std::size_t losses = 0;
    std::size_t draws = 0;
};

struct MultiplayerHeadToHeadRecord {
    // Ordered by storage identity: first < second.
    std::string first_profile_id;
    std::string second_profile_id;
    std::size_t played = 0;
    std::size_t first_wins = 0;
    std::size_t second_wins = 0;
    std::size_t draws = 0;
};

struct MultiplayerMatchSummary {
    std::size_t matches = 0;
    // Admitted pairs whose two participants share one storage identity. The
    // binder already rejects these; they are counted, never aggregated.
    std::size_t ignored_matches = 0;
    std::vector<MultiplayerProfileMatchRecord> profiles;
    std::vector<MultiplayerHeadToHeadRecord> head_to_head;
};

/* Head-to-head oriented to one stored match's P1/P2 seats. */
struct MultiplayerMatchHeadToHead {
    std::size_t played = 0;
    std::size_t player1_wins = 0;
    std::size_t player2_wins = 0;
    std::size_t draws = 0;
};

MultiplayerMatchSummary summarize_multiplayer_matches(
    const std::vector<StoredMultiplayerMatch>& matches);

const MultiplayerProfileMatchRecord* find_multiplayer_profile_record(
    const MultiplayerMatchSummary& summary,
    const std::string& profile_id) noexcept;

std::optional<MultiplayerMatchHeadToHead> multiplayer_head_to_head_for_match(
    const MultiplayerMatchSummary& summary,
    const StoredMultiplayerMatch& match);

/* "P1 3  P2 1  DRAW 1" — counts only, oriented to the match's seats. */
std::string format_multiplayer_head_to_head(
    const MultiplayerMatchHeadToHead& head_to_head);

}  // namespace ur::product
