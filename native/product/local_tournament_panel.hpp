#pragma once

// Pure presentation/selection model for the player-facing Modern Local
// Tournament panel. It owns no files, guest state or identity minting: the
// host feeds it the authoritative profile catalog, the confirmed live 2P
// participants and the restored coordinator state, and acts on the explicit
// requests it returns (create a roster / arm one fixture). The coordinator,
// receipts and stock 2P result remain the only result authority.

#include "host_profile_catalog.hpp"
#include "local_tournament_round_robin.hpp"
#include "quick_practice_catalog.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

// Canonical ordinary-Race course identity for a stock track index.
inline std::string local_tournament_course_id(std::uint8_t track_id) {
    char text[16];
    std::snprintf(text, sizeof(text), "course:%02u",
        static_cast<unsigned>(track_id) + 1u);
    return text;
}

// Display name for a canonical ordinary-Race course, or empty.
inline std::string_view local_tournament_course_name(std::string_view course) {
    if (!local_tournament_ordinary_race_course(course)) return {};
    const int ordinal = (course[7] - '0') * 10 + (course[8] - '0');
    const auto* entry = quick_practice_course(
        static_cast<std::uint8_t>(ordinal - 1));
    return entry ? entry->name : std::string_view{};
}

// Course pools offered at setup. Preset 0 is the first stock tour (always
// available to a fresh save); 1..7 are the later ordinary tours; the final
// preset is every ordinary Race. Hunter is never offered.
inline constexpr std::size_t kLocalTournamentCoursePresetCount = 9;

inline std::string local_tournament_course_preset_label(std::size_t preset) {
    if (preset + 1 == kLocalTournamentCoursePresetCount) return "ALL TOURS";
    if (preset >= kLocalTournamentCoursePresetCount) return {};
    const auto* course = quick_practice_course(
        static_cast<std::uint8_t>(preset * 5));
    if (!course) return {};
    std::string label(course->tour_name);
    for (char& ch : label) {
        if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
    }
    return label;
}

inline std::vector<std::string> local_tournament_course_preset(
    std::size_t preset) {
    std::vector<std::string> courses;
    if (preset >= kLocalTournamentCoursePresetCount) return courses;
    const std::size_t first_tour =
        preset + 1 == kLocalTournamentCoursePresetCount ? 0 : preset;
    const std::size_t last_tour =
        preset + 1 == kLocalTournamentCoursePresetCount ? 7 : preset;
    for (std::size_t tour = first_tour; tour <= last_tour; ++tour) {
        for (std::size_t slot : {std::size_t{0}, std::size_t{3}}) {
            const auto id = local_tournament_course_id(
                static_cast<std::uint8_t>(tour * 5 + slot));
            if (local_tournament_ordinary_race_course(id)) {
                courses.push_back(id);
            }
        }
    }
    return courses;
}

enum class LocalTournamentPanelPage {
    Setup,
    Standings,
    Fixtures,
    History, // completed events, read-only
};

struct LocalTournamentPanelState {
    LocalTournamentPanelPage page = LocalTournamentPanelPage::Setup;
    // Setup: one row per catalog entry, then COURSES, LEGS and START.
    std::vector<HostProfileCatalogEntry> candidates;
    std::vector<bool> selected;
    std::size_t course_preset = 0;
    std::size_t legs = 1; // meetings per pair (1..kLocalTournamentMaxLegs)
    std::size_t cursor = 0;
    // Fixtures page cursor.
    std::size_t fixture_cursor = 0;
    // Page Back returns to from History (Setup or Standings).
    LocalTournamentPanelPage history_return = LocalTournamentPanelPage::Standings;
};

enum class LocalTournamentPanelRequestKind {
    None,
    Create,      // create a new tournament from `roster` + `courses`
    ArmFixture,  // arm `fixture_index` for the seated pair
    Close,
};

struct LocalTournamentPanelRequest {
    LocalTournamentPanelRequestKind kind = LocalTournamentPanelRequestKind::None;
    std::vector<std::string> roster;
    std::vector<std::string> courses;
    std::size_t legs = 1;
    std::size_t fixture_index = 0;
};

enum class LocalTournamentPanelNav { Up, Down, Left, Right, Confirm, Back };

// Setup opens with the two confirmed seated profiles pre-selected; nothing
// else is implied. Catalog order is preserved.
inline LocalTournamentPanelState make_local_tournament_setup(
    const std::vector<HostProfileCatalogEntry>& catalog,
    std::string_view seated_p1,
    std::string_view seated_p2) {
    LocalTournamentPanelState state;
    state.page = LocalTournamentPanelPage::Setup;
    const std::size_t limit = std::min<std::size_t>(catalog.size(), 16);
    state.candidates.assign(catalog.begin(),
        catalog.begin() + static_cast<std::ptrdiff_t>(limit));
    state.selected.assign(state.candidates.size(), false);
    const auto k1 = local_tournament_storage_key(seated_p1);
    const auto k2 = local_tournament_storage_key(seated_p2);
    for (std::size_t i = 0; i < state.candidates.size(); ++i) {
        const auto key = local_tournament_storage_key(
            state.candidates[i].profile_id);
        state.selected[i] = !key.empty() && (key == k1 || key == k2);
    }
    return state;
}

inline std::size_t local_tournament_setup_selected_count(
    const LocalTournamentPanelState& state) {
    return static_cast<std::size_t>(
        std::count(state.selected.begin(), state.selected.end(), true));
}

inline std::size_t local_tournament_setup_row_count(
    const LocalTournamentPanelState& state) {
    return state.candidates.size() + 3; // + COURSES + LEGS + START
}

inline std::size_t local_tournament_setup_courses_row(
    const LocalTournamentPanelState& state) {
    return state.candidates.size();
}
inline std::size_t local_tournament_setup_legs_row(
    const LocalTournamentPanelState& state) {
    return state.candidates.size() + 1;
}
inline std::size_t local_tournament_setup_start_row(
    const LocalTournamentPanelState& state) {
    return state.candidates.size() + 2;
}

// Scheduled races for the current setup: pairs x legs.
inline std::size_t local_tournament_setup_race_count(
    const LocalTournamentPanelState& state) {
    const auto n = local_tournament_setup_selected_count(state);
    return n < 2 ? 0 : n * (n - 1) / 2 * state.legs;
}

inline bool local_tournament_setup_can_start(
    const LocalTournamentPanelState& state) {
    const auto count = local_tournament_setup_selected_count(state);
    return count >= 2 && count <= kLocalTournamentMaxEntrants &&
        state.legs >= 1 && state.legs <= kLocalTournamentMaxLegs &&
        !local_tournament_course_preset(state.course_preset).empty();
}

// Pure keyboard/controller navigation. Returns an explicit host request; the
// host performs creation/arming through the coordinator and then reloads
// the overview pages itself.
inline LocalTournamentPanelRequest local_tournament_panel_navigate(
    LocalTournamentPanelState& state,
    LocalTournamentPanelNav nav,
    std::size_t fixture_count) {
    LocalTournamentPanelRequest request;
    const bool sideways = nav == LocalTournamentPanelNav::Left ||
        nav == LocalTournamentPanelNav::Right;
    if (state.page == LocalTournamentPanelPage::History) {
        // History is a read-only leaf: any back/sideways step returns.
        if (sideways || nav == LocalTournamentPanelNav::Back) {
            state.page = state.history_return;
        }
        return request;
    }
    if (nav == LocalTournamentPanelNav::Back) {
        request.kind = LocalTournamentPanelRequestKind::Close;
        return request;
    }
    if (state.page == LocalTournamentPanelPage::Setup) {
        const std::size_t rows = local_tournament_setup_row_count(state);
        const std::size_t courses_row = local_tournament_setup_courses_row(state);
        const std::size_t legs_row = local_tournament_setup_legs_row(state);
        const std::size_t start_row = local_tournament_setup_start_row(state);
        if (state.cursor >= rows) state.cursor = rows - 1;
        switch (nav) {
        case LocalTournamentPanelNav::Up:
            state.cursor = state.cursor == 0 ? rows - 1 : state.cursor - 1;
            break;
        case LocalTournamentPanelNav::Down:
            state.cursor = (state.cursor + 1) % rows;
            break;
        case LocalTournamentPanelNav::Left:
        case LocalTournamentPanelNav::Right:
            if (state.cursor == courses_row) {
                const std::size_t n = kLocalTournamentCoursePresetCount;
                state.course_preset = nav == LocalTournamentPanelNav::Right
                    ? (state.course_preset + 1) % n
                    : (state.course_preset + n - 1) % n;
            } else if (state.cursor == legs_row) {
                const std::size_t n = kLocalTournamentMaxLegs;
                state.legs = nav == LocalTournamentPanelNav::Right
                    ? state.legs % n + 1
                    : (state.legs + n - 2) % n + 1;
            } else {
                state.history_return = LocalTournamentPanelPage::Setup;
                state.page = LocalTournamentPanelPage::History;
            }
            break;
        case LocalTournamentPanelNav::Confirm:
            if (state.cursor < courses_row) {
                const bool next = !state.selected[state.cursor];
                if (!next ||
                    local_tournament_setup_selected_count(state) <
                        kLocalTournamentMaxEntrants) {
                    state.selected[state.cursor] = next;
                }
            } else if (state.cursor == courses_row) {
                state.course_preset =
                    (state.course_preset + 1) %
                    kLocalTournamentCoursePresetCount;
            } else if (state.cursor == legs_row) {
                state.legs = state.legs % kLocalTournamentMaxLegs + 1;
            } else if (state.cursor == start_row &&
                       local_tournament_setup_can_start(state)) {
                request.kind = LocalTournamentPanelRequestKind::Create;
                for (std::size_t i = 0; i < state.candidates.size(); ++i) {
                    if (state.selected[i]) {
                        request.roster.push_back(
                            state.candidates[i].profile_id);
                    }
                }
                request.courses =
                    local_tournament_course_preset(state.course_preset);
                request.legs = state.legs;
            }
            break;
        default:
            break;
        }
        return request;
    }

    switch (nav) {
    case LocalTournamentPanelNav::Left:
    case LocalTournamentPanelNav::Right: {
        // Standings -> Fixtures -> History -> Standings (Left reverses).
        using Page = LocalTournamentPanelPage;
        const bool right = nav == LocalTournamentPanelNav::Right;
        if (state.page == Page::Standings) {
            if (right) {
                state.page = Page::Fixtures;
            } else {
                state.history_return = Page::Standings;
                state.page = Page::History;
            }
        } else {
            if (right) {
                state.history_return = Page::Standings;
                state.page = Page::History;
            } else {
                state.page = Page::Standings;
            }
        }
        break;
    }
    case LocalTournamentPanelNav::Up:
        if (state.page == LocalTournamentPanelPage::Fixtures &&
            fixture_count) {
            state.fixture_cursor = state.fixture_cursor == 0
                ? fixture_count - 1 : state.fixture_cursor - 1;
        }
        break;
    case LocalTournamentPanelNav::Down:
        if (state.page == LocalTournamentPanelPage::Fixtures &&
            fixture_count) {
            state.fixture_cursor = (state.fixture_cursor + 1) % fixture_count;
        }
        break;
    case LocalTournamentPanelNav::Confirm:
        if (state.page == LocalTournamentPanelPage::Fixtures &&
            state.fixture_cursor < fixture_count) {
            request.kind = LocalTournamentPanelRequestKind::ArmFixture;
            request.fixture_index = state.fixture_cursor;
        }
        break;
    default:
        break;
    }
    return request;
}

// Whether `fixture_index` is the seated pair's own unplayed meeting. A round
// robin has at most one meeting per pair, so this is also unique.
inline bool local_tournament_fixture_playable_by(
    const LocalTournamentState& state,
    std::size_t fixture_index,
    std::string_view seated_p1,
    std::string_view seated_p2) {
    if (fixture_index >= state.fixtures.size() ||
        fixture_index >= state.results.size() ||
        state.results[fixture_index]) return false;
    const auto& fixture = state.fixtures[fixture_index];
    if (fixture.player1 >= state.entrants.size() ||
        fixture.player2 >= state.entrants.size()) return false;
    const auto a = local_tournament_storage_key(
        state.entrants[fixture.player1]);
    const auto b = local_tournament_storage_key(
        state.entrants[fixture.player2]);
    const auto p1 = local_tournament_storage_key(seated_p1);
    const auto p2 = local_tournament_storage_key(seated_p2);
    return (a == p1 && b == p2) || (a == p2 && b == p1);
}

inline std::optional<std::size_t> local_tournament_seated_fixture(
    const LocalTournamentState& state,
    std::string_view seated_p1,
    std::string_view seated_p2) {
    for (std::size_t i = 0; i < state.fixtures.size(); ++i) {
        if (local_tournament_fixture_playable_by(
                state, i, seated_p1, seated_p2)) return i;
    }
    return std::nullopt;
}

inline bool local_tournament_complete(const LocalTournamentState& state) {
    return !state.fixtures.empty() &&
        state.results.size() == state.fixtures.size() &&
        std::all_of(state.results.begin(), state.results.end(),
            [](const auto& result) { return result.has_value(); });
}

// Profile name used on the panel: the racer name from the authoritative
// catalog, else the storage identity. Upper-cased and bounded.
inline std::string local_tournament_entrant_label(
    const std::vector<HostProfileCatalogEntry>& catalog,
    std::string_view profile_id,
    std::size_t max_cells) {
    std::string label(profile_id);
    const auto key = local_tournament_storage_key(profile_id);
    for (const auto& entry : catalog) {
        if (local_tournament_storage_key(entry.profile_id) == key &&
            !entry.identity.name.empty()) {
            label = entry.identity.name;
            break;
        }
    }
    for (char& ch : label) {
        if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
    }
    if (label.size() > max_cells) label.resize(max_cells);
    return label;
}

inline std::string local_tournament_pad_right(std::string text,
                                              std::size_t width) {
    if (text.size() < width) text.append(width - text.size(), ' ');
    return text;
}

// "1 ALPHA   2 0 1  6" style standings row, within 24 cells.
inline std::string local_tournament_standing_row(
    const LocalTournamentStanding& standing,
    const std::vector<HostProfileCatalogEntry>& catalog) {
    char tail[24];
    std::snprintf(tail, sizeof(tail), "%zu %zu %zu %2zu",
        standing.wins % 10, standing.draws % 10, standing.losses % 10,
        standing.points % 100);
    char rank[4];
    std::snprintf(rank, sizeof(rank), "%zu ", standing.rank % 10);
    return std::string(rank) +
        local_tournament_pad_right(
            local_tournament_entrant_label(catalog, standing.profile_id, 9),
            10) +
        tail;
}

// Compact fixture row: "R1 ALPHA   V BRAVO   *".
inline std::string local_tournament_fixture_row(
    const LocalTournamentState& state,
    std::size_t index,
    const std::vector<HostProfileCatalogEntry>& catalog,
    bool armed) {
    if (index >= state.fixtures.size()) return {};
    const auto& fixture = state.fixtures[index];
    if (fixture.player1 >= state.entrants.size() ||
        fixture.player2 >= state.entrants.size()) return {};
    char round[8];
    std::snprintf(round, sizeof(round), "R%zu ", fixture.round % 100);
    const bool played = index < state.results.size() &&
        state.results[index].has_value();
    return std::string(round) +
        local_tournament_pad_right(local_tournament_entrant_label(
            catalog, state.entrants[fixture.player1], 7), 8) +
        "V " +
        local_tournament_pad_right(local_tournament_entrant_label(
            catalog, state.entrants[fixture.player2], 7), 8) +
        (armed ? ">" : played ? "*" : " ");
}

// Detail line for the selected fixture: course and outcome/status.
inline std::string local_tournament_fixture_detail(
    const LocalTournamentState& state,
    std::size_t index,
    const std::vector<HostProfileCatalogEntry>& catalog) {
    if (index >= state.fixtures.size()) return {};
    const auto& fixture = state.fixtures[index];
    std::string course(local_tournament_course_name(fixture.course_id));
    for (char& ch : course) {
        if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
    }
    if (index >= state.results.size() || !state.results[index]) {
        return course + "  UNPLAYED";
    }
    const auto& result = *state.results[index];
    using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
    if (result.outcome == Outcome::Draw) return course + "  DRAW";
    const bool first_won =
        (result.outcome == Outcome::Player1Win) != result.seats_swapped;
    return course + "  " + local_tournament_entrant_label(
        catalog,
        state.entrants[first_won ? fixture.player1 : fixture.player2], 8) +
        " WON";
}

// One completed event: "MIKE WON  3 RACERS" or "TIE  4 RACERS". The
// champion is the unique rank-1 entrant of the receipt-derived standings.
inline std::string local_tournament_history_row(
    const LocalTournamentState& state,
    const std::vector<HostProfileCatalogEntry>& catalog) {
    const auto standings = local_tournament_standings(state);
    std::size_t leaders = 0;
    const LocalTournamentStanding* champion = nullptr;
    for (const auto& standing : standings) {
        if (standing.rank == 1) {
            ++leaders;
            champion = &standing;
        }
    }
    char tail[24];
    std::snprintf(tail, sizeof(tail), "  %zu RACERS",
        state.entrants.size() % 10);
    if (leaders != 1 || !champion) return std::string("TIE") + tail;
    return local_tournament_entrant_label(catalog, champion->profile_id, 9) +
        " WON" + tail;
}

// One-row event status shown after a fixture is credited, within 29
// cells: "CHAMPION: MIKE", "EVENT TIED ON 3 PTS", "LEADS: MIKE 3 PTS 1/3"
// or "LEAD SHARED 3 PTS 2/6". Derived from receipt-backed standings only.
inline std::string local_tournament_result_notice(
    const LocalTournamentState& state,
    const std::vector<HostProfileCatalogEntry>& catalog) {
    const auto standings = local_tournament_standings(state);
    if (standings.empty()) return {};
    std::size_t leaders = 0;
    for (const auto& standing : standings) leaders += standing.rank == 1;
    const auto& top = standings.front();
    std::size_t played = 0;
    for (const auto& result : state.results) played += result ? 1 : 0;
    char tail[32];
    if (local_tournament_complete(state)) {
        if (leaders == 1) {
            return "CHAMPION: " +
                local_tournament_entrant_label(catalog, top.profile_id, 12);
        }
        std::snprintf(tail, sizeof(tail), "EVENT TIED ON %zu PTS",
            top.points % 1000);
        return tail;
    }
    std::snprintf(tail, sizeof(tail), " %zu PTS %zu/%zu", top.points % 1000,
        played % 1000, state.fixtures.size() % 1000);
    if (leaders == 1) {
        return "LEADS: " +
            local_tournament_entrant_label(catalog, top.profile_id, 9) + tail;
    }
    return std::string("LEAD SHARED") + tail;
}

} // namespace ur::product
