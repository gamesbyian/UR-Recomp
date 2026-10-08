#pragma once

#include "multiplayer_match_catalog.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace ur::product {

// Pure Modern Local Tournament policy, not stock League simulation.
// No public API here automatically assigns a historical Records match to a
// tournament. The eventual session/sidecar boundary must explicitly bind a
// fixture before giving an admitted StoredMultiplayerMatch to this reducer.
inline constexpr std::size_t kLocalTournamentMaxEntrants = 8;

struct LocalTournamentFixture {
    std::size_t round = 0;  // 1-based
    std::size_t player1 = 0; // index into immutable entrants
    std::size_t player2 = 0;
    std::string course_id;
};

struct LocalTournamentRecordedResult {
    std::string run_artifact_checksum;
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    bool seats_swapped = false;
};

struct LocalTournamentState {
    std::vector<std::string> entrants;
    std::vector<std::string> course_pool;
    std::vector<LocalTournamentFixture> fixtures;
    std::vector<std::optional<LocalTournamentRecordedResult>> results;
};

enum class LocalTournamentRecordStatus {
    Applied,
    InvalidFixture,
    AlreadyRecorded,
    EvidenceNotAdmitted,
    ParticipantsMismatch,
    CourseMismatch,
    DuplicateArtifact,
};

struct LocalTournamentStanding {
    std::string profile_id;
    std::size_t played = 0;
    std::size_t wins = 0;
    std::size_t draws = 0;
    std::size_t losses = 0;
    std::size_t points = 0;
    std::size_t rank = 0; // shared rank for equal points/wins
};

inline std::string local_tournament_storage_key(std::string_view id) {
    std::string key(id);
    for (char& ch : key) {
        if (ch >= 'A' && ch <= 'Z') {
            ch = static_cast<char>(ch - 'A' + 'a');
        }
    }
    return key;
}

// Ordinary tours only: one Race at ordinal 1 and one at 4 in each
// five-course tour. The Hunter/secret fifth group is deliberately excluded.
// This matches the existing race-2p producer; Stunt/Circuit/VS have no
// persisted authoritative outcome contract here.
inline bool local_tournament_ordinary_race_course(std::string_view course) {
    if (course.size() != 9 || course.substr(0, 7) != "course:" ||
        course[7] < '0' || course[7] > '9' ||
        course[8] < '0' || course[8] > '9') return false;
    const int ordinal = (course[7] - '0') * 10 + (course[8] - '0');
    return ordinal >= 1 && ordinal <= 40 &&
        ((ordinal - 1) % 5 == 0 || (ordinal - 1) % 5 == 3);
}

inline std::optional<LocalTournamentState> make_local_round_robin(
    std::vector<std::string> entrant_ids,
    std::vector<std::string> ordinary_race_courses) {
    if (entrant_ids.size() < 2 ||
        entrant_ids.size() > kLocalTournamentMaxEntrants ||
        ordinary_race_courses.empty() ||
        ordinary_race_courses.size() > 16) return std::nullopt;

    // This is an in-memory policy boundary. Session admission must separately
    // validate these IDs against the authoritative profile catalog.
    std::vector<std::string> names;
    names.reserve(entrant_ids.size());
    for (const auto& id : entrant_ids) {
        if (id.empty()) return std::nullopt;
        const auto key = local_tournament_storage_key(id);
        if (std::find(names.begin(), names.end(), key) != names.end()) {
            return std::nullopt;
        }
        names.push_back(key);
    }
    for (std::size_t i = 0; i < ordinary_race_courses.size(); ++i) {
        if (!local_tournament_ordinary_race_course(ordinary_race_courses[i])) {
            return std::nullopt;
        }
        if (std::find(ordinary_race_courses.begin(),
                ordinary_race_courses.begin() + static_cast<std::ptrdiff_t>(i),
                ordinary_race_courses[i]) !=
            ordinary_race_courses.begin() + static_cast<std::ptrdiff_t>(i)) {
            return std::nullopt;
        }
    }

    LocalTournamentState state;
    state.entrants = std::move(entrant_ids);
    state.course_pool = std::move(ordinary_race_courses);

    const std::size_t n = state.entrants.size();
    const std::size_t slot_count = n + (n % 2);
    std::vector<std::size_t> slots(slot_count);
    std::iota(slots.begin(), slots.end(), std::size_t{0});
    std::size_t next_course = 0;
    for (std::size_t round = 1; round < slot_count; ++round) {
        for (std::size_t pair = 0; pair < slot_count / 2; ++pair) {
            const auto first = slots[pair];
            const auto second = slots[slot_count - 1 - pair];
            if (first == n || second == n) continue; // explicit bye
            state.fixtures.push_back({
                round, first, second,
                state.course_pool[next_course % state.course_pool.size()],
            });
            ++next_course;
        }
        // Circle method: hold slot zero fixed; rotate all other positions.
        std::rotate(slots.begin() + 1, slots.end() - 1, slots.end());
    }
    state.results.resize(state.fixtures.size());
    return state;
}

inline LocalTournamentRecordStatus record_local_tournament_result(
    LocalTournamentState& state,
    std::size_t fixture_index,
    const StoredMultiplayerMatch& catalog_admitted_match) {
    if (fixture_index >= state.fixtures.size() ||
        fixture_index >= state.results.size()) {
        return LocalTournamentRecordStatus::InvalidFixture;
    }
    if (state.results[fixture_index]) {
        return LocalTournamentRecordStatus::AlreadyRecorded;
    }
    const auto& stored = catalog_admitted_match;
    const auto& m = stored.match;
    const auto& bound = m.context.match;
    const auto& fixture = state.fixtures[fixture_index];
    if (fixture.player1 >= state.entrants.size() ||
        fixture.player2 >= state.entrants.size() ||
        fixture.player1 == fixture.player2) {
        return LocalTournamentRecordStatus::InvalidFixture;
    }
    // The caller must supply a *catalog-admitted* run/sidecar pair, explicitly
    // associated with this active fixture. Never scan Records to guess it.
    if (stored.run_path.empty() ||
        stored.run.provenance.mode != "race-2p" ||
        m.run_artifact_checksum.empty() ||
        m.schema_version != kMultiplayerMatchRecordSchemaVersion) {
        return LocalTournamentRecordStatus::EvidenceNotAdmitted;
    }
    if (fixture.course_id != m.context.course_id ||
        fixture.course_id != stored.run.provenance.course_id) {
        return LocalTournamentRecordStatus::CourseMismatch;
    }
    const auto p1 = local_tournament_storage_key(bound.player1.profile_id);
    const auto p2 = local_tournament_storage_key(bound.player2.profile_id);
    const auto a = local_tournament_storage_key(
        state.entrants[fixture.player1]);
    const auto b = local_tournament_storage_key(
        state.entrants[fixture.player2]);
    const bool same = p1 == a && p2 == b;
    const bool reversed = p1 == b && p2 == a;
    if (!same && !reversed) {
        return LocalTournamentRecordStatus::ParticipantsMismatch;
    }
    for (const auto& previous : state.results) {
        if (previous &&
            previous->run_artifact_checksum == m.run_artifact_checksum) {
            return LocalTournamentRecordStatus::DuplicateArtifact;
        }
    }
    const auto outcome = bound.result.outcome;
    using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
    if (outcome != Outcome::Player1Win &&
        outcome != Outcome::Player2Win &&
        outcome != Outcome::Draw) {
        return LocalTournamentRecordStatus::EvidenceNotAdmitted;
    }
    state.results[fixture_index] = LocalTournamentRecordedResult{
        m.run_artifact_checksum, outcome, reversed};
    return LocalTournamentRecordStatus::Applied;
}

// Standings derive solely from accepted explicit fixture assignments.
// 3/1/0 is a Modern product policy, not a recovered stock League score.
// Rankings are deterministic: points, then wins, then storage identity; a
// complete tie shares the same rank. No guest state or file is modified.
inline std::vector<LocalTournamentStanding> local_tournament_standings(
    const LocalTournamentState& state) {
    std::vector<LocalTournamentStanding> standings;
    standings.reserve(state.entrants.size());
    for (const auto& id : state.entrants) standings.push_back({id});
    using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
    const auto count = std::min(state.fixtures.size(), state.results.size());
    for (std::size_t i = 0; i < count; ++i) {
        if (!state.results[i]) continue;
        const auto& fixture = state.fixtures[i];
        if (fixture.player1 >= standings.size() ||
            fixture.player2 >= standings.size() ||
            fixture.player1 == fixture.player2) continue;
        auto& a = standings[fixture.player1];
        auto& b = standings[fixture.player2];
        ++a.played;
        ++b.played;
        const auto& result = *state.results[i];
        if (result.outcome == Outcome::Draw) {
            ++a.draws; ++b.draws; ++a.points; ++b.points;
        } else {
            const bool first_won = 
                (result.outcome == Outcome::Player1Win) != result.seats_swapped;
            auto& winner = first_won ? a : b;
            auto& loser = first_won ? b : a;
            ++winner.wins; ++loser.losses;
            winner.points += 3;
        }
    }
    std::sort(standings.begin(), standings.end(),
        [](const auto& lhs, const auto& rhs) {
            if (lhs.points != rhs.points) return lhs.points > rhs.points;
            if (lhs.wins != rhs.wins) return lhs.wins > rhs.wins;
            return local_tournament_storage_key(lhs.profile_id) <
                   local_tournament_storage_key(rhs.profile_id);
        });
    for (std::size_t i = 0; i < standings.size(); ++i) {
        standings[i].rank = i > 0 &&
            standings[i].points == standings[i - 1].points &&
            standings[i].wins == standings[i - 1].wins
            ? standings[i - 1].rank : i + 1;
    }
    return standings;
}

} // namespace ur::product
