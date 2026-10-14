/* Real pinned Baldosa host's Modern root, using the already shipping shared
 * Modern painter and model. No guest writes or competing window/SDL loop.
 *
 * This is the first visible native root integration: Play yields the actual
 * existing guest title/menu to the player. It does not claim direct event
 * launch, Records callbacks, or route completeness for other destinations.
 */
#include "modern_root_overlay_presenter.hpp"
#include "modern_root_physical_edges.hpp"
#include "baldosa_native_records_summary.hpp"
#include "baldosa_native_multiplayer_records_summary.hpp"
#include "baldosa_native_run_save_feedback.hpp"
#include "uniracers_two_player_result.hpp"
#include "baldosa_native_two_seat_join.hpp"
#include "quick_practice_route.hpp"
#include "quick_practice_input_mask.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
void ur_baldosa_product_set_host_focus(int);
int ur_baldosa_product_queue_stock_menu_input(std::uint16_t mask);
void ur_baldosa_product_cancel_stock_menu_input(void);
extern std::uint8_t g_ram[0x20000];
const char* ur_baldosa_modern_profile_records_directory(void);
const char* ur_baldosa_modern_profile_multiplayer_records_directory(void);
const char* ur_baldosa_modern_profile_selected_id(void);
const char* ur_baldosa_modern_profile_catalog_path(void);
int ur_baldosa_modern_profile_can_join_opponent(
    const ur::product::HostProfileCatalogEntry* entry);
int ur_baldosa_modern_profile_can_begin_race(void);
int ur_baldosa_modern_create_first_preset(unsigned index);
}

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <optional>
#include <vector>
#include <utility>

namespace {
using ur::product::ModernRootDestination;
using ur::product::ModernRootMenu;
using ur::product::ModernRootOverlayPainter;
using ur::product::ModernRootOverlayView;
using ur::product::HostOverlayRect;
constexpr std::uint8_t kNativeRootAvailable =
    (1u << static_cast<unsigned>(ModernRootDestination::Play)) |
    (1u << static_cast<unsigned>(ModernRootDestination::Multiplayer)) |
    (1u << static_cast<unsigned>(ModernRootDestination::Records));
ModernRootMenu g_menu{};
ur::product::ModernRootPhysicalEdges g_navigation_edges{};
ur::product::ModernRootPhysicalEdges g_p2_join_edges{};
ur::product::BaldosaNativeTwoSeatJoin g_two_seat_join{};
std::string g_racer_name = "STOCK RACER - NO PROFILE";
bool g_visible = false;
bool g_confirm_quit = false;
bool g_records_open = false;
bool g_unbound_two_player_warning_open = false;
bool g_named_profile_stale = false;
bool g_first_racer_open = false;
bool g_first_racer_created = false;
bool g_first_racer_failed = false;
std::size_t g_first_racer_preset = 0;
ur::product::BaldosaNativeRunSaveFeedback g_run_save_feedback =
    ur::product::BaldosaNativeRunSaveFeedback::None;
std::string g_records_status;
std::string g_records_recent;
std::string g_records_detail;
std::string g_records_one_status;
std::string g_records_one_recent;
std::string g_records_two_status;
std::string g_records_two_recent;
std::string g_records_two_detail;
bool g_records_two_player = false;
bool g_render_reported = false;
unsigned g_paint_count = 0;
int g_stock_target = -1;
std::uint16_t g_stock_settle = 0;
std::uint32_t g_stock_budget = 0;
std::uint8_t g_stock_previous_cursor = 0;
bool g_stock_waiting_cursor = false;
bool g_stock_waiting_transition = false;
bool g_stock_handed_off = false;
unsigned g_handed_off_players = 0;
bool g_handed_off_saw_race = false;
bool g_reentry_smoke_queued = false;
bool g_reentry_needs_paint = false;

void stock_route_abort(const char* reason) {
    ur_baldosa_product_cancel_stock_menu_input();
    g_two_seat_join.cancel();
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT stock_rejected=%s\n", reason);
    g_stock_target = -1;
    g_stock_waiting_transition = false;
    g_stock_waiting_cursor = false;
    // Root remains visible and owns human inputs. Never dismiss on a
    // guessed stock surface or synthesize a completed event.
}

bool configured() {
    const char* opt = std::getenv("UR_BALDOSA_MODERN_ROOT");
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return opt && std::strcmp(opt, "1") == 0 &&
        !(mode && std::strcmp(mode, "authentic") == 0);
}
bool reopen_on_observed_stock_main() {
    // This is the only frontend reentry authority. Keyboard Escape and
    // P1 physical gamepad B share exactly the same guest-state admission.
    if (!configured() || g_visible || !g_stock_handed_off ||
        g_stock_target != -1 || g_ram[0x009f] != 0xd7u ||
        g_ram[0x0313] == 0x01u) return false;
    g_menu = ur::product::modern_root_menu_reset();
    g_visible = true;
    g_confirm_quit = false;
    g_records_open = false;
    g_unbound_two_player_warning_open = false;
    g_run_save_feedback = ur::product::BaldosaNativeRunSaveFeedback::None;
    g_two_seat_join.cancel();
    g_p2_join_edges.reset();
    g_stock_handed_off = false;
    g_handed_off_players = 0;
    g_handed_off_saw_race = false;
    g_reentry_needs_paint = true;
    ur_baldosa_product_set_host_focus(1);
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0\n");
    return true;
}
void select_records_page(bool two_player) {
    g_records_two_player = two_player;
    g_records_status = two_player ? g_records_two_status : g_records_one_status;
    g_records_recent = two_player ? g_records_two_recent : g_records_one_recent;
    g_records_detail = two_player ? g_records_two_detail : "";
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT records_page=%s\n",
        two_player ? "2p" : "1p");
    // Emit the real shared painter's last validated 2P detail only when
    // the player actually navigates to that read-only Records page.
    // This is archive-consumer evidence, not a guest-finished match.
    if (two_player && !g_records_two_detail.empty())
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT records_last_2p=%s "
            "source=historical_paired_archive\n",
            g_records_two_detail.c_str());
}
void open_records_archive() {
    g_records_open = true;
    g_records_two_player = false;
    g_records_two_detail.clear();
    const char* directory = ur_baldosa_modern_profile_records_directory();
    const char* match_directory =
        ur_baldosa_modern_profile_multiplayer_records_directory();
    const char* profile_id = ur_baldosa_modern_profile_selected_id();
    if (!directory || !*directory || !match_directory ||
        !*match_directory || !profile_id || !*profile_id) {
        g_records_one_status = "NO ACTIVE NAMED RACER";
        g_records_one_recent = "CREATE OR SELECT A RACER";
        g_records_two_status = g_records_one_status;
        g_records_two_recent = g_records_one_recent;
        select_records_page(false);
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=none validated=0 unavailable=0\n");
        return;
    }
    const auto result =
        ur::product::inspect_baldosa_native_records_archive(directory);
    if (!result.directory_available) {
        g_records_one_status = "RECORDS DIRECTORY INVALID";
        g_records_one_recent = "NOTHING WAS LOADED";
    } else {
        g_records_one_status =
            "VALID " + std::to_string(result.validated_archives) +
            "  UNAVAILABLE " + std::to_string(result.unavailable_artifacts);
        if (result.validated_archives == 0) {
            g_records_one_recent = "NO STORED RUNS YET";
        } else {
            g_records_one_recent =
                "LAST: " + result.recent_course + " " +
                ur::product::format_baldosa_native_record_ticks60(
                    result.recent_ticks60);
        }
    }
    const auto matches =
        ur::product::inspect_baldosa_native_two_player_records_archive(
            match_directory, profile_id);
    if (!matches.directory_available) {
        g_records_two_status = "2P HISTORY UNAVAILABLE";
        g_records_two_recent = "NOTHING WAS LOADED";
    } else {
        // Surface archive damage explicitly. Suppressed malformed matches
        // must not disappear as if the selected racer had no history.
        g_records_two_status =
            "MY 2P " + std::to_string(matches.selected_profile_matches) +
            "  UNAVAILABLE " + std::to_string(matches.unavailable_pairs);
        g_records_two_recent =
            "W " + std::to_string(matches.wins) +
            "  L " + std::to_string(matches.losses) +
            "  D " + std::to_string(matches.draws);
        g_records_two_detail = matches.latest_match_line;
    }
    select_records_page(false);
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=%zu unavailable=%zu\n",
        result.validated_archives, result.unavailable_artifacts);
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=%zu "
        "unavailable=%zu selected=%zu\n",
        matches.validated_pairs, matches.unavailable_pairs,
        matches.selected_profile_matches);
}
bool named_profile_still_playable() {
    // Once a selected profile becomes stale, require a process restart.
    // Reopening the root must never silently reactivate a different SRAM.
    if (g_named_profile_stale) return false;
    if (ur_baldosa_modern_profile_can_begin_race()) return true;
    g_named_profile_stale = true;
    g_racer_name = "PROFILE CHANGED - RESTART APP";
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT active_profile_stale=1 restart_required=1\n");
    return false;
}
void request_stock_route(int players) {
    g_stock_target = players - 1;
    g_stock_settle = 0;
    g_stock_budget = ur::product::kQuickPracticeLaunchMaxObservations;
    g_stock_waiting_cursor = false;
    g_stock_waiting_transition = false;
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT stock_requested players=%d\n", players);
}
bool confirmed_join_still_admissible() {
    if (!g_two_seat_join.ready()) return false;
    const auto* first = g_two_seat_join.participant(0);
    const auto* second = g_two_seat_join.participant(1);
    const char* selected = ur_baldosa_modern_profile_selected_id();
    const char* catalog_path = ur_baldosa_modern_profile_catalog_path();
    if (!first || !second || !selected || !*selected ||
        !catalog_path || !*catalog_path || first->profile_id != selected)
        return false;
    const auto current =
        ur::product::load_host_profile_catalog_file(catalog_path);
    return current &&
        named_profile_still_playable() &&
        g_two_seat_join.confirmed_profiles_match_catalog(*current) &&
        ur_baldosa_modern_profile_can_join_opponent(second);
}
void join_confirm(unsigned seat) {
    if (!g_two_seat_join.open()) return;
    if (!g_two_seat_join.confirm(seat)) {
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT join_rejected seat=%u\n", seat + 1u);
        return;
    }
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=%u\n", seat + 1u);
    if (g_two_seat_join.ready()) {
        if (!confirmed_join_still_admissible()) {
            stock_route_abort("join_authority_changed");
            return;
        }
        request_stock_route(2);
    }
}
void choose() {
    if (g_stock_target != -1) return;
    if (g_first_racer_open) {
        if (g_first_racer_created) return;
        const auto& presets = ur::product::legacy_racer_presets();
        if (g_first_racer_preset >= presets.size()) return;
        if (ur_baldosa_modern_create_first_preset(
                static_cast<unsigned>(g_first_racer_preset))) {
            g_first_racer_created = true;
            g_first_racer_failed = false;
            // The source SRAM/guest is still anonymous until *next boot*.
            // Blocking the stock route prevents accidental unrecorded play
            // under a UI that now claims a named racer.
            g_named_profile_stale = true;
            g_racer_name = "RESTART TO USE NEW RACER";
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT first_racer_created=1 "
                "activation=next_process\n");
        } else {
            g_first_racer_failed = true;
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT first_racer_created=0 "
                "reason=canonical_create_rejected\n");
        }
        return;
    }
    if (g_unbound_two_player_warning_open) {
        // Separate explicit consent for a playable unrecorded session.
        g_unbound_two_player_warning_open = false;
        if (!named_profile_still_playable()) return;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1\n");
        request_stock_route(2);
        return;
    }
    if (g_two_seat_join.open()) {
        join_confirm(0);
        return;
    }
    if (g_records_open) {
        g_records_open = false;
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT records_closed=1\n");
        return;
    }
    if (g_confirm_quit) {
        SDL_Event quit{};
        quit.type = SDL_QUIT;
        if (SDL_PushEvent(&quit) != 1)
            std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT quit_event_rejected\n");
        return;
    }
    const auto selected = ur::product::modern_root_menu_selected(g_menu);
    const auto index = ur::product::modern_root_destination_index(selected);
    if (selected == ModernRootDestination::Records) {
        open_records_archive();
        return;
    }
    if ((kNativeRootAvailable & (1u << index)) == 0) {
        // Practice and Options still require original Modern route admission.
        // Never invent guest course selection or an alternate storage root.
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT route=%zu unavailable=1\n", index);
        return;
    }
    if (!named_profile_still_playable()) return;
    if (selected == ModernRootDestination::Multiplayer) {
        // No anonymous match binding: historical stock 2P remains playable
        // without manufacturing profile identities. A verified named P1
        // with at least two catalog entries must explicitly confirm both.
        const char* active = ur_baldosa_modern_profile_selected_id();
        if (active && *active) {
            // Reuse the boot-verified Modern user-root catalog, never CWD.
            const char* catalog_path =
                ur_baldosa_modern_profile_catalog_path();
            const auto roster = catalog_path
                ? ur::product::load_host_profile_catalog_file(catalog_path)
                : std::optional<std::vector<
                    ur::product::HostProfileCatalogEntry>>{};
            std::vector<ur::product::HostProfileCatalogEntry> ready;
            if (roster) {
                ready = *roster;
                // Never offer a roster-only or partially created P2 racer
                // whose typed state and raw SRAM cannot be verified. The
                // P1 active profile was separately verified at native boot.
                ready.erase(std::remove_if(ready.begin(), ready.end(),
                    [active](const auto& entry) {
                        return entry.profile_id != active &&
                            !ur_baldosa_modern_profile_can_join_opponent(
                                &entry);
                    }), ready.end());
            }
            if (!roster || !g_two_seat_join.begin(std::move(ready), active)) {
                // A fresh named install can still play an unbound stock 2P
                // session. It cannot acquire match-history identity until
                // two real distinct profiles are confirmed. Do not strand
                // multiplayer behind missing optional product metadata.
                std::fprintf(stderr,
                    "UR_BALDOSA_MODERN_ROOT join_unavailable=1 "
                    "stock_2p_without_record_identity=1\n");
                g_unbound_two_player_warning_open = true;
                std::fprintf(stderr,
                    "UR_BALDOSA_MODERN_ROOT unbound_2p_warning_open=1\n");
                return;
            }
            g_p2_join_edges.reset();
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n");
            return;
        }
    }
    if (selected == ModernRootDestination::Multiplayer) {
        // Anonymous P1 needs the same explicit unrecorded-play consent.
        g_unbound_two_player_warning_open = true;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT unbound_2p_warning_open=1\n");
        return;
    }
    request_stock_route(1);
}
void navigate(int delta) {
    if (g_confirm_quit || g_stock_target != -1 ||
        g_unbound_two_player_warning_open) return;
    if (g_first_racer_open) {
        if (g_first_racer_created) return;
        const auto count =
            static_cast<int>(ur::product::legacy_racer_presets().size());
        const int pos = static_cast<int>(g_first_racer_preset);
        g_first_racer_preset = static_cast<std::size_t>(
            (pos + (delta > 0 ? 1 : -1) + count) % count);
        g_first_racer_failed = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT first_racer_preset=%zu\n",
            g_first_racer_preset);
        return;
    }
    if (g_two_seat_join.open()) {
        g_two_seat_join.move(0, delta);
        return;
    }
    if (g_records_open) {
        select_records_page(!g_records_two_player);
        return;
    }
    g_menu = ur::product::modern_root_menu_move(g_menu, delta);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT selected=%zu\n",
        ur::product::modern_root_destination_index(
            ur::product::modern_root_menu_selected(g_menu)));
}
void back() {
    if (g_first_racer_open) {
        g_first_racer_open = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT first_racer_closed=1\n");
        return;
    }
    if (g_unbound_two_player_warning_open) {
        g_unbound_two_player_warning_open = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT unbound_2p_declined=1\n");
        return;
    }
    if (g_two_seat_join.open()) {
        // Both confirmations may already have queued original stock menu
        // inputs. B/ESC must cancel that source route as well as the child
        // panel, rather than silently launching an unbound guest match.
        if (g_stock_target != -1)
            stock_route_abort("cancelled");
        else
            g_two_seat_join.cancel();
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT join_closed=1\n");
        return;
    }
    if (g_records_open) {
        g_records_open = false;
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT records_closed=1\n");
        return;
    }
    if (g_stock_target != -1) {
        stock_route_abort("cancelled");
        return;
    }
    if (g_confirm_quit) g_confirm_quit = false;
    else g_confirm_quit = true;
}
}  // namespace

// Only genuine root-controlled 2P handoff with two distinct explicit pad
// confirmations may expose identities to the existing source-result binder.
// A stock 2P race entered anonymously remains playable but unbound.
extern "C" int ur_baldosa_modern_root_source_bound_2p_profiles(
    ur::product::HostProfileCatalogEntry* p1,
    ur::product::HostProfileCatalogEntry* p2) {
    if (!p1 || !p2 || g_visible || !g_stock_handed_off ||
        g_handed_off_players != 2u || !g_two_seat_join.ready())
        return 0;
    const auto* first = g_two_seat_join.participant(0);
    const auto* second = g_two_seat_join.participant(1);
    if (!first || !second) return 0;
    *p1 = *first;
    *p2 = *second;
    return 1;
}

extern "C" void ur_baldosa_modern_root_set_run_save_feedback(unsigned status) {
    using ur::product::BaldosaNativeRunSaveFeedback;
    g_run_save_feedback = status >= 1u && status <= 3u
        ? static_cast<BaldosaNativeRunSaveFeedback>(status)
        : BaldosaNativeRunSaveFeedback::None;
}

extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name) {
    g_racer_name = name && *name ? name : "STOCK RACER - NO PROFILE";
}

extern "C" void ur_baldosa_modern_root_after_config(void) {
    if (!configured()) return;
    g_menu = ur::product::modern_root_menu_reset();
    g_navigation_edges.reset();
    g_p2_join_edges.reset();
    g_two_seat_join.cancel();
    g_confirm_quit = false;
    g_records_open = false;
    g_unbound_two_player_warning_open = false;
    g_named_profile_stale = false;
    g_first_racer_open = false;
    g_first_racer_created = false;
    g_first_racer_failed = false;
    g_first_racer_preset = 0;
    g_run_save_feedback = ur::product::BaldosaNativeRunSaveFeedback::None;
    g_visible = true;
    g_render_reported = false;
    g_paint_count = 0;
    g_stock_target = -1;
    g_stock_budget = 0;
    g_stock_handed_off = false;
    g_handed_off_players = 0;
    g_handed_off_saw_race = false;
    g_reentry_smoke_queued = false;
    g_reentry_needs_paint = false;
    ur_baldosa_product_set_host_focus(1);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT opened=1\n");
}

extern "C" int ur_baldosa_modern_root_key(int key, int pressed) {
    int action = 0;
    std::size_t physical = 0;
    switch (key) {
    case SDLK_UP: physical = 0; action = -1; break;
    case SDLK_DOWN: physical = 1; action = 1; break;
    case SDLK_RETURN: physical = 2; action = 2; break;
    case SDLK_ESCAPE: physical = 3; action = 3; break;
    case SDLK_x: physical = 4; action = 4; break;
    default: return 0;
    }
    // Continue tracking release after a stock-game handoff. An Escape held
    // while the stock guest returned to main must not reopen the host root
    // on SDL key-repeat; a new physical press is required.
    const bool first_press =
        g_navigation_edges.keyboard(physical, pressed != 0);
    if (!g_visible)
        return key == SDLK_ESCAPE && first_press &&
               reopen_on_observed_stock_main() ? 1 : 0;
    if (!first_press) return 1;
    if (action == 2) choose();
    else if (action == 3) back();
    else if (action == 4 && !g_first_racer_created &&
             !ur_baldosa_modern_profile_selected_id() &&
             !g_first_racer_open && g_stock_target == -1 &&
             !g_records_open && !g_confirm_quit &&
             !g_unbound_two_player_warning_open) {
        g_first_racer_open = true;
        g_first_racer_failed = false;
        g_first_racer_preset = 0;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 "
            "activation=next_process\n");
    } else if (action != 4) navigate(action);
    return 1;
}

extern "C" int ur_baldosa_modern_root_gamepad(
    int player, int button, int pressed) {
    if (player == 1 && g_visible && g_two_seat_join.open()) {
        int action = 0;
        std::size_t physical = 0;
        switch (button) {
        case kGamepadBtn_DpadUp: physical = 0; action = -1; break;
        case kGamepadBtn_DpadDown: physical = 1; action = 1; break;
        case kGamepadBtn_A: physical = 2; action = 2; break;
        case kGamepadBtn_Start: physical = 3; action = 2; break;
        case kGamepadBtn_B: physical = 4; action = 3; break;
        default: return 0;
        }
        const bool edge = g_p2_join_edges.p1_gamepad(physical, pressed != 0);
        if (!edge) return 1;
        if (g_stock_target != -1) return 1;
        if (action == 2) join_confirm(1);
        else if (action == 3) g_two_seat_join.clear(1);
        else g_two_seat_join.move(1, action);
        return 1;
    }
    if (player != 0) return 0;
    int action = 0;
    std::size_t physical = 0;
    switch (button) {
    case kGamepadBtn_DpadUp: physical = 0; action = -1; break;
    case kGamepadBtn_DpadDown: physical = 1; action = 1; break;
    case kGamepadBtn_A: physical = 2; action = 2; break;
    case kGamepadBtn_Start: physical = 3; action = 2; break;
    case kGamepadBtn_B: physical = 4; action = 3; break;
    case kGamepadBtn_X: physical = 5; action = 4; break;
    default: return 0;
    }
    // A and Start keep separate physical latches while sharing Confirm.
    // P2 never owns this root. These latches do not alter the guest word.
    const bool first_press =
        g_navigation_edges.p1_gamepad(physical, pressed != 0);
    if (!g_visible)
        return button == kGamepadBtn_B && first_press &&
               reopen_on_observed_stock_main() ? 1 : 0;
    if (!first_press) return 1;
    if (action == 2) choose();
    else if (action == 3) back();
    else if (action == 4 && !g_first_racer_created &&
             !ur_baldosa_modern_profile_selected_id() &&
             !g_first_racer_open && g_stock_target == -1 &&
             !g_records_open && !g_confirm_quit &&
             !g_unbound_two_player_warning_open) {
        g_first_racer_open = true;
        g_first_racer_failed = false;
        g_first_racer_preset = 0;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 "
            "activation=next_process\n");
    } else if (action != 4) navigate(action);
    return 1;
}

extern "C" int ur_baldosa_modern_root_draw_frame(
    std::uint8_t* dst, std::size_t pitch, const std::uint8_t* field,
    int width, int height, double) {
    if (!g_visible &&
        g_run_save_feedback == ur::product::BaldosaNativeRunSaveFeedback::None)
        return 0;
    // Retain the stock 256x224 output and exact pitch. The HD/widescreen
    // compositors own all other raster modes; no attempt to fake density.
    if (!dst || !field || width != 256 || height != 224 ||
        pitch < static_cast<std::size_t>(width) * 4 ||
        pitch % 4 != 0) return 0;
    for (int y = 0; y < height; ++y)
        std::memcpy(dst + static_cast<std::size_t>(y) * pitch,
                    field + static_cast<std::size_t>(y) * width * 4,
                    static_cast<std::size_t>(width) * 4);
    const ModernRootOverlayPainter painter{
        &snes_ovl_fill_rect, &snes_ovl_stroke_rect, &snes_ovl_draw_text};
    if (!g_visible)
        return ur::product::render_baldosa_native_run_save_feedback(
            painter, reinterpret_cast<std::uint32_t*>(dst),
            static_cast<int>(pitch / 4), height, g_run_save_feedback) ? 1 : 0;
    ModernRootOverlayView view{
        g_menu, false, g_racer_name,
        false, g_confirm_quit, kNativeRootAvailable, false,
        g_records_open, g_records_status, g_records_recent,
        g_records_two_player, true};
    view.records_detail = g_records_detail;
    view.unbound_two_player_warning_open =
        g_unbound_two_player_warning_open;
    view.first_racer_shortcut_available =
        !ur_baldosa_modern_profile_selected_id() &&
        !g_first_racer_created;
    view.first_racer_open = g_first_racer_open;
    view.first_racer_created = g_first_racer_created;
    view.first_racer_failed = g_first_racer_failed;
    const auto& presets = ur::product::legacy_racer_presets();
    if (g_first_racer_preset < presets.size())
        view.first_racer_preset_name = presets[g_first_racer_preset].name;
    view.two_seat_join_open = g_two_seat_join.open();
    if (view.two_seat_join_open) {
        const auto* p1 = g_two_seat_join.candidate(0);
        const auto* p2 = g_two_seat_join.candidate(1);
        view.join_p1_name = p1 ? std::string_view(p1->identity.name) : "";
        view.join_p2_name = p2 ? std::string_view(p2->identity.name) : "";
        // Show the true cartridge rider presets the two Modern identities
        // are bound to. A completed 2P result only admits their exact
        // source-observed rider indices, never a guessed name match.
        const auto& stock = ur::product::legacy_racer_presets();
        view.join_p1_stock = p1 ? stock[p1->identity.rider_index].name : "";
        view.join_p2_stock = p2 ? stock[p2->identity.rider_index].name : "";
        view.join_p1_confirmed = g_two_seat_join.confirmed(0);
        view.join_p2_confirmed = g_two_seat_join.confirmed(1);
    }
    const bool drawn = ur::product::render_modern_root_overlay(
        painter, reinterpret_cast<std::uint32_t*>(dst),
        static_cast<int>(pitch / 4), height, 1, 240,
        HostOverlayRect{8,10,240,204}, view);
    if (drawn) {
        ++g_paint_count;
        if (g_reentry_needs_paint) {
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared\n");
            g_reentry_needs_paint = false;
        }
        if (!g_render_reported) {
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n");
            g_render_reported = true;
        }
    }
    return drawn ? 1 : 0;
}

// CI-only genuine SDL event-pump route. This is NOT controller hardware QA.
// It proves the native host dispatches the five-way root's existing menu
// contract and Play releases the original guest input without fake guest state.
// Advance exclusively from the native guest's actual post-frame WRAM.
// Buttons travel on the existing host-only input filter, not RAM writes,
// fake menu flags, scripted debug inputs, or a competing emulator loop.
extern "C" void ur_baldosa_modern_root_stock_observe_guest(void) {
    if (g_stock_target == -1) return;
    // The stock-menu route itself takes several frames. Do not release host
    // input using participants revoked after their second confirmation.
    if (g_stock_target == 1 && g_two_seat_join.open() &&
        !confirmed_join_still_admissible()) {
        stock_route_abort("join_authority_changed");
        return;
    }
    if (g_stock_budget-- == 0) {
        stock_route_abort("timeout");
        return;
    }
    const std::uint8_t menu = g_ram[0x009f];
    // Reject stale P1 before another stock input is sent from MAIN.
    // Never attempt to rewind a guest that has already left MAIN.
    if (menu == 0xd7u && !named_profile_still_playable()) {
        stock_route_abort("active_profile_stale");
        return;
    }
    const std::uint8_t expected =
        g_stock_target == 0 ? 0x3cu : 0x3du;
    if (g_stock_waiting_transition) {
        if (menu == expected) {
            const int players = g_stock_target + 1;
            g_stock_target = -1;
            g_visible = false;
            g_stock_handed_off = true;
            g_handed_off_players = static_cast<unsigned>(players);
            g_handed_off_saw_race = false;
            ur_baldosa_product_set_host_focus(0);
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT stock_entered players=%d menu=%02x\n",
                players, static_cast<unsigned>(menu));
        }
        // A menu transition can pass through intermediary guest phases.
        // Only the exact expected settled 1P/2P surface authorizes handoff;
        // the bounded frame budget rejects any route that never arrives.
        return;
    }
    if (menu != 0xd7u) {
        g_stock_settle = 0;
        g_stock_waiting_cursor = false;
        return;
    }
    const std::uint8_t cursor = g_ram[0x009b];
    if (g_stock_waiting_cursor) {
        if (cursor == g_stock_previous_cursor) return;
        g_stock_waiting_cursor = false;
        g_stock_settle = 0;
    }
    if (++g_stock_settle < ur::product::kQuickPracticeMenuSettleObservations)
        return;
    if (cursor > 4u) {
        stock_route_abort("invalid_stock_cursor");
        return;
    }
    const auto desired = g_stock_target == 0
        ? ur::product::stock_main_menu_one_player_input(cursor)
        : (cursor < 1 ? ur::product::QuickPracticeMenuInput::Down
           : cursor > 1 ? ur::product::QuickPracticeMenuInput::Up
           : ur::product::QuickPracticeMenuInput::Accept);
    const auto mask = ur::product::quick_practice_runner_mask(
        ur::product::launch_input_from_menu_input(desired));
    if (!ur_baldosa_product_queue_stock_menu_input(mask)) {
        stock_route_abort("stock_input_rejected");
        return;
    }
    g_stock_settle = 0;
    if (desired == ur::product::QuickPracticeMenuInput::Accept) {
        g_stock_waiting_transition = true;
    } else {
        g_stock_previous_cursor = cursor;
        g_stock_waiting_cursor = true;
    }
}

extern "C" void ur_baldosa_modern_root_after_run_frame(unsigned frame) {
    ur_baldosa_modern_root_stock_observe_guest();
    // A genuine 1P/2P terminal result may show the SAME existing Modern
    // acknowledgement strip. It is revoked on any new race, setup screen,
    // lost source handoff, or mode change. No guest result is fabricated.
    const bool stock_result_still_visible =
        (g_handed_off_players == 1u && g_ram[0x009fu] == 0x99u) ||
        (g_handed_off_players == 2u &&
         g_ram[0x009fu] == ur::title::kOrdinaryTwoPlayerRaceResultMenu);
    if (g_run_save_feedback !=
            ur::product::BaldosaNativeRunSaveFeedback::None &&
        (g_visible || !g_stock_handed_off ||
         g_ram[0x0313u] == 0x01u || !stock_result_still_visible))
        g_run_save_feedback = ur::product::BaldosaNativeRunSaveFeedback::None;
    // The original guest can return to stock setup and let a player change
    // the mode without revisiting our root. Such a new session must NOT
    // inherit the previous acknowledged 1P/2P result authority.
    if (!g_visible && g_handed_off_players) {
        const auto menu = g_ram[0x009fu];
        if (g_ram[0x0313u] == 1u)
            g_handed_off_saw_race = true;
        const bool opposite_mode =
            (g_handed_off_players == 1 && menu == 0x3du) ||
            (g_handed_off_players == 2 && menu == 0x3cu);
        const bool setup_after_race = g_handed_off_saw_race &&
            (menu == 0x3cu || menu == 0x3du ||
             menu == 0x6du || menu == 0xf6u);
        if (menu == 0xd7u || opposite_mode || setup_after_race) {
            // Returning to title/setup invalidates both source event and
            // the separately pad-confirmed human profile identities.
            g_two_seat_join.cancel();
            g_handed_off_players = 0;
            g_handed_off_saw_race = false;
        }
    }
    const char* reopen_test = std::getenv("UR_BALDOSA_MODERN_ROOT_REENTER_SMOKE");
    // Test-only trace of actual guest transitions. This is intentionally
    // passive: never type an input or modify a guest menu/state byte.
    if (reopen_test && std::strcmp(reopen_test, "1") == 0 &&
        g_stock_handed_off && !g_visible) {
        static unsigned last_menu = 0x100u;
        const unsigned menu = g_ram[0x009f];
        if (menu != last_menu || frame % 180u == 0u) {
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT source_menu frame=%u menu=%02x "
                "cursor=%02x race=%02x\n",
                frame, menu, static_cast<unsigned>(g_ram[0x009b]),
                static_cast<unsigned>(g_ram[0x0313]));
            last_menu = menu;
        }
    }
    if (reopen_test && std::strcmp(reopen_test, "1") == 0 &&
        g_stock_handed_off && !g_visible && !g_reentry_smoke_queued &&
        g_stock_target == -1 && g_ram[0x009f] == 0xd7u &&
        g_ram[0x0313] != 0x01u) {
        g_reentry_smoke_queued = true;
        SDL_Event event{};
        event.type = SDL_KEYDOWN;
#if SNESRECOMP_SDL3
        event.key.key = SDLK_ESCAPE;
#else
        event.key.keysym.sym = SDLK_ESCAPE;
#endif
        if (SDL_PushEvent(&event) != 1) std::abort();
        event.type = SDL_KEYUP;
        if (SDL_PushEvent(&event) != 1) std::abort();
    }
    const char* opt = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE");
    if (!g_visible || !opt || (std::strcmp(opt, "1") != 0 &&
                             std::strcmp(opt, "2") != 0 &&
                             std::strcmp(opt, "3") != 0 &&
                             std::strcmp(opt, "4") != 0)) return;
    // Controlled host-root edge on an anonymous install. No created racer
    // is activated in this guest; a new process must load canonical SRAM.
    if (std::strcmp(opt, "4") == 0) {
        int key = frame == 60 ? SDLK_x :
                  frame == 62 ? SDLK_RETURN : 0;
        if (!key) return;
        SDL_Event event{};
        event.type = SDL_KEYDOWN;
#if SNESRECOMP_SDL3
        event.key.key = key;
#else
        event.key.keysym.sym = key;
#endif
        if (SDL_PushEvent(&event) != 1) std::abort();
        event.type = SDL_KEYUP;
        if (SDL_PushEvent(&event) != 1) std::abort();
        return;
    }
    // Mode 3 is a deliberately TEST-ONLY synthetic gamepad semantic
    // injection, not an SDL hardware controller or guest memory write.
    // All stock menu transitions still occur inside the original guest.
    // The real direct gamepad entrypoints and physical-edge latches are
    // exercised; exact real-device routing needs independent QA later.
    if (std::strcmp(opt, "3") == 0 && (frame == 66 || frame == 68)) {
        if (!g_two_seat_join.open()) std::abort();
        const int player = frame == 66 ? 0 : 1;
        if (!ur_baldosa_modern_root_gamepad(
                player, kGamepadBtn_A, 1) ||
            !ur_baldosa_modern_root_gamepad(
                player, kGamepadBtn_A, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=%d\n",
            player + 1);
        return;
    }
    int key = 0;
    // In mode 1 open and switch 1P/2P read-only Records pages using
    // real SDL key edges, then close and enter 1P. Mode 2 proves the
    // actual stock 2P handoff.
    if (std::strcmp(opt, "2") == 0 ||
        std::strcmp(opt, "3") == 0) {
        if (frame == 60 || frame == 62) key = SDLK_DOWN;
        else if (frame == 64 ||
                 (frame == 66 && std::strcmp(opt, "2") == 0))
            key = SDLK_RETURN;
    } else {
        if (frame >= 60 && frame <= 62) key = SDLK_DOWN;
        else if (frame == 63 || frame == 70) key = SDLK_RETURN;
        else if (frame == 64) key = SDLK_DOWN; // open 2P archive page
        else if (frame == 65) key = SDLK_UP;   // return to 1P page
        else if (frame == 66) key = SDLK_ESCAPE;
        else if (frame >= 67 && frame <= 69) key = SDLK_UP;
    }
    if (!key) return;
    SDL_Event event{};
    event.type = SDL_KEYDOWN;
#if SNESRECOMP_SDL3
    event.key.key = key;
#else
    event.key.keysym.sym = key;
#endif
    if (SDL_PushEvent(&event) != 1) std::abort();
    if (key == SDLK_DOWN && frame == 60) {
        // An SDL keyboard auto-repeat must not skip a Modern destination.
        if (SDL_PushEvent(&event) != 1) std::abort();
    }
    event.type = SDL_KEYUP;
    if (SDL_PushEvent(&event) != 1) std::abort();
}

// Read-only handoff witnessed by the root after its exact expected stock
// 0x3C/0x3D guest transition. A root preview or arbitrary native script has
// no authority to classify guest results as player-owned.
extern "C" unsigned ur_baldosa_modern_root_guest_players(void) {
    return configured() && !g_visible && g_stock_handed_off
        ? g_handed_off_players : 0u;
}

extern "C" unsigned ur_baldosa_modern_root_paint_count(void) {
    return g_paint_count;
}
