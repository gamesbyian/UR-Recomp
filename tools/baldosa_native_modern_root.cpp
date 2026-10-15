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
#include "baldosa_native_options.hpp"
#include "quick_practice_route.hpp"
#include "quick_practice_input_mask.hpp"
#include "quick_practice_launch.hpp"
#include "quick_practice_available_selection.hpp"
#include "quick_practice_selection_view.hpp"
#include "uniracers_course_identity.h"
#include "uniracers_practice_tour_unlock.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
void RtlSetSaveRoot(const char*);
const char* RtlSaveRoot(void);
void RtlEnsureSaveDir(void);
extern unsigned char* g_sram;
extern int g_sram_size;
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
int ur_baldosa_modern_create_second_preset(unsigned index);
int ur_baldosa_modern_select_existing_p1_next_boot(const char* profile_id);
// Staged by tools/baldosa_modern_options_spike.py over the framework's own
// fullscreen / swap-interval / mixer machinery.
int snesrecomp_desktop_product_get_display(int* fullscreen, int* vsync);
int snesrecomp_desktop_product_apply_display(int fullscreen, int vsync);
int snesrecomp_desktop_product_get_volume(void);
int snesrecomp_desktop_product_set_volume(int percent);
}

#include <algorithm>
#include <cctype>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
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
    (1u << static_cast<unsigned>(ModernRootDestination::Practice)) |
    (1u << static_cast<unsigned>(ModernRootDestination::Multiplayer)) |
    (1u << static_cast<unsigned>(ModernRootDestination::Records)) |
    (1u << static_cast<unsigned>(ModernRootDestination::Options));
// Practice offers exactly the tours the ORIGINAL game's own TOUR_SELECT
// offers this rider (stock per-rider unlock tier in the live cartridge SRAM,
// the same read-only projection the legacy Modern host uses). The secret
// Hunter tour stays closed. A course the stock menus would not reach can
// never be listed, so the source route cannot be stranded by an unlock.
ur::product::QuickPracticeAvailability native_practice_availability() {
    constexpr std::size_t kRiderOffset = 0x0748;
    if (!g_sram || g_sram_size != static_cast<int>(ur::product::kStockSramBytes))
        return ur::product::quick_practice_no_tracks();
    const std::uint8_t saved = g_sram[kRiderOffset];
    const auto mask = ur::title::stock_practice_tour_option_mask(
        g_sram, ur::product::kStockSramBytes, saved < 16 ? saved : 0u);
    return mask
        ? ur::product::quick_practice_availability_from_tour_options(*mask)
        : ur::product::quick_practice_no_tracks();
}
int g_practice_target_track = -1;
// One short, player-facing sentence on the root (cleared by the next action).
std::string g_root_notice;
constexpr unsigned kPracticeInputGapFrames = 20;
unsigned g_practice_input_gap = 0;
ur::product::QuickPracticeSelection g_practice_picker{};
ur::product::QuickPracticeLaunchState g_practice_launch{};
// This is the existing Modern Practice contract: source play in a scratch
// save root with a retained exact stock-SRAM snapshot, never career data.
bool g_practice_session_active = false;
std::vector<std::uint8_t> g_practice_sram_snapshot;
std::string g_practice_previous_save_root;
ModernRootMenu g_menu{};
// Native OPTIONS: only controls the pinned host genuinely applies.
ur::product::BaldosaNativeOptions g_options{};
bool options_host_get_display(void*, int* fullscreen, int* vsync) {
    return snesrecomp_desktop_product_get_display(fullscreen, vsync) != 0;
}
bool options_host_apply_display(void*, int fullscreen, int vsync) {
    return snesrecomp_desktop_product_apply_display(fullscreen, vsync) != 0;
}
int options_host_get_volume(void*) {
    return snesrecomp_desktop_product_get_volume();
}
int options_host_set_volume(void*, int percent) {
    return snesrecomp_desktop_product_set_volume(percent);
}
ur::product::BaldosaOptionsHost options_host() {
    ur::product::BaldosaOptionsHost host;
    host.get_display = &options_host_get_display;
    host.apply_display = &options_host_apply_display;
    host.get_volume = &options_host_get_volume;
    host.set_volume = &options_host_set_volume;
    return host;
}
const char* options_load_name(ur::product::BaldosaOptionsLoad load) {
    switch (load) {
    case ur::product::BaldosaOptionsLoad::Missing: return "missing";
    case ur::product::BaldosaOptionsLoad::Loaded: return "loaded";
    case ur::product::BaldosaOptionsLoad::Damaged: return "damaged";
    case ur::product::BaldosaOptionsLoad::IoError: return "io_error";
    }
    return "unknown";
}
void log_options(const char* event) {
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT %s row=%s display=%s vsync=%s volume=%d "
        "status=%s help=%d load=%s\n",
        event,
        ur::product::baldosa_options_row_label(g_options.selected),
        ur::product::baldosa_options_display_label(g_options.display),
        ur::product::baldosa_options_vsync_label(g_options.vsync),
        g_options.volume,
        g_options.status == ur::product::BaldosaOptionsStatus::None
            ? "NONE" : ur::product::baldosa_options_status_text(
                  g_options.status),
        g_options.controls_help ? 1 : 0,
        options_load_name(g_options.load));
}
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
bool g_second_racer_open = false;
bool g_second_racer_created = false;
bool g_second_racer_failed = false;
bool g_can_add_second_racer = false;
bool g_existing_switch_available = false;
bool g_existing_switch_open = false;
bool g_existing_switch_saved = false;
bool g_existing_switch_failed = false;
std::string g_existing_switch_target;
std::size_t g_existing_switch_preset = 1;
bool g_ever_entered_stock = false;
std::size_t g_second_racer_preset = 1;
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

bool restore_practice_session() {
    if (!g_practice_session_active) return true;
    if (!g_sram || g_sram_size !=
            static_cast<int>(ur::product::kStockSramBytes) ||
        g_practice_sram_snapshot.size() !=
            ur::product::kStockSramBytes)
        return false;
    std::memcpy(g_sram, g_practice_sram_snapshot.data(),
                ur::product::kStockSramBytes);
    RtlSetSaveRoot(g_practice_previous_save_root.empty()
                       ? nullptr : g_practice_previous_save_root.c_str());
    const char* restored = RtlSaveRoot();
    if ((restored ? std::string_view(restored) : std::string_view{}) !=
        g_practice_previous_save_root)
        return false;
    g_practice_session_active = false;
    g_practice_sram_snapshot.clear();
    g_practice_previous_save_root.clear();
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 "
        "bytes=8192 original_root=1\n");
    return true;
}
bool begin_practice_session() {
    namespace fs = std::filesystem;
    const auto deny = [](const char* reason) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT practice_sandbox_rejected=%s\n", reason);
        return false;
    };
    if (g_practice_session_active || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes) ||
        g_ram[0x0313] == 1u || !g_visible || g_stock_target != -1)
        return deny("source_guest_not_ready");
    // The root is visible before the original title MAIN is guaranteed to
    // settle. The existing QuickPracticeLaunch::AwaitMain stage waits for
    // 0xD7 and its source-qualified 60-frame stable window; requiring MAIN
    // here prematurely rejects a valid real P1 Down/A/A root gesture.
    const char* configured_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!configured_root || !*configured_root) return deny("user_root_absent");
    const fs::path user_root(configured_root);
    if (!user_root.is_absolute()) return deny("user_root_not_absolute");
    std::error_code ec;
    if (!fs::is_directory(user_root, ec) || ec ||
        fs::is_symlink(user_root, ec) || ec) return deny("user_root_untrusted");
    const fs::path session_path = user_root / "practice-session";
    const auto status = fs::symlink_status(session_path, ec);
    if (status.type() == fs::file_type::not_found) {
        ec.clear();
        if (!fs::create_directory(session_path, ec) || ec) return deny("scratch_create_failed");
    } else if (ec || !fs::is_directory(status) || fs::is_symlink(status)) {
        return deny("scratch_root_untrusted");
    }
    ec.clear();
    const auto scratch_save = fs::symlink_status(
        session_path / "save.srm", ec);
    // A never-used scratch directory normally has NO save.srm. Standard
    // std::filesystem reports ENOENT even through is_symlink(path, ec):
    // that absence is safe, unlike an actual redirected or special file.
    if (scratch_save.type() == fs::file_type::not_found) {
        if (ec && ec != std::errc::no_such_file_or_directory)
            return deny("scratch_missing_unexpected_error");
    } else if (ec || !fs::is_regular_file(scratch_save)) {
        return deny("scratch_save_untrusted");
    }
    const char* original = RtlSaveRoot();
    g_practice_previous_save_root = original ? original : "";
    g_practice_sram_snapshot.assign(
        g_sram, g_sram + ur::product::kStockSramBytes);
    // Baldosa pins its mutable cwd to the validated explicit user root.
    // Keep the original fixed relative save-root spelling within the
    // framework\'s bounded save-root buffer, even when the user root has
    // a long Windows pathname.
    const std::string requested_root = "practice-session";
    RtlSetSaveRoot(requested_root.c_str());
    if (!RtlSaveRoot() ||
        std::string_view(RtlSaveRoot()) != requested_root) {
        RtlSetSaveRoot(g_practice_previous_save_root.c_str());
        g_practice_sram_snapshot.clear();
        g_practice_previous_save_root.clear();
        return deny("scratch_save_root_not_accepted");
    }
    RtlEnsureSaveDir();
    g_practice_session_active = true;
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 "
        "root=practice-session publication=disabled\n");
    return true;
}
void practice_route_abort(const char* reason) {
    ur_baldosa_product_cancel_stock_menu_input();
    g_practice_target_track = -1;
    if (std::strcmp(reason, "cancelled") != 0)
        g_root_notice = std::strcmp(reason, "timeout") == 0
            ? "COURSE NOT REACHABLE - RETRY"
            : std::strcmp(reason, "active_profile_stale") == 0
                ? "RACER CHANGED - RESTART GAME"
                : "PRACTICE STOPPED - TRY AGAIN";
    if (!restore_practice_session()) g_named_profile_stale = true;
    g_practice_launch = {};
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT practice_rejected=%s source_course_admitted=0\n",
        reason);
}
void stock_route_abort(const char* reason) {
    ur_baldosa_product_cancel_stock_menu_input();
    g_two_seat_join.cancel();
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT stock_rejected=%s\n", reason);
    if (std::strcmp(reason, "cancelled") != 0)
        g_root_notice = std::strcmp(reason, "active_profile_stale") == 0 ||
                        std::strcmp(reason, "join_authority_changed") == 0
            ? "RACER CHANGED - RESTART GAME"
            : "COULD NOT START - TRY AGAIN";
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
    if (!restore_practice_session()) return false;
    g_menu = ur::product::modern_root_menu_reset();
    g_visible = true;
    g_confirm_quit = false;
    g_records_open = false;
    g_options.open = false;
    g_options.controls_help = false;
    g_practice_picker = {};
    g_practice_launch = {};
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
    if (g_named_profile_stale) {
        g_root_notice = "RESTART TO USE NEW RACER";
        return false;
    }
    if (ur_baldosa_modern_profile_can_begin_race()) return true;
    g_named_profile_stale = true;
    g_racer_name = "PROFILE CHANGED - RESTART APP";
    g_root_notice = "RACER CHANGED - RESTART GAME";
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
void open_stock_racer_setup() {
    // No typed/catalog mutation from stock gameplay, stale authority, a
    // second seat's input, or while another root child owns focus.
    if (!g_visible || g_stock_target != -1 ||
        ur::product::quick_practice_launch_owns_player_input(g_practice_launch) ||
        g_practice_picker.visible || g_records_open || g_options.open ||
        g_confirm_quit || g_two_seat_join.open() ||
        g_unbound_two_player_warning_open || g_first_racer_open ||
        g_second_racer_open || g_existing_switch_open ||
        g_first_racer_created || g_second_racer_created ||
        g_existing_switch_saved || g_named_profile_stale) return;
    const char* selected = ur_baldosa_modern_profile_selected_id();
    if (!selected || !*selected) {
        g_first_racer_open = true;
        g_first_racer_failed = false;
        g_first_racer_preset = 0;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 "
            "activation=next_process\n");
        return;
    }
    // With two complete catalogued profiles, X enters a distinct explicit
    // existing-P1 selector. Only the other already-created stock identity
    // can be selected, never a directory/name guess or live guest hot-swap.
    if (g_existing_switch_available && !g_ever_entered_stock &&
        named_profile_still_playable()) {
        const char* catalog_path = ur_baldosa_modern_profile_catalog_path();
        const auto roster = catalog_path
            ? ur::product::load_host_profile_catalog_file(catalog_path)
            : std::optional<std::vector<
                ur::product::HostProfileCatalogEntry>>{};
        if (!roster || roster->size() != 2u) return;
        for (const auto& candidate : *roster) {
            if (candidate.profile_id == selected) continue;
            if (!ur_baldosa_modern_profile_can_join_opponent(&candidate))
                return;
            g_existing_switch_target = candidate.profile_id;
            g_existing_switch_preset = candidate.identity.rider_index;
            g_existing_switch_open = true;
            g_existing_switch_failed = false;
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 "
                "from=%s to=%s activation=next_process\n",
                selected, g_existing_switch_target.c_str());
            return;
        }
        return;
    }
    if (!g_can_add_second_racer || g_ever_entered_stock ||
        !named_profile_still_playable()) return;
    const char* catalog_path = ur_baldosa_modern_profile_catalog_path();
    const auto roster = catalog_path
        ? ur::product::load_host_profile_catalog_file(catalog_path)
        : std::optional<std::vector<
            ur::product::HostProfileCatalogEntry>>{};
    if (!roster || roster->size() != 1u ||
        roster->front().profile_id != selected ||
        !ur::product::valid_racer_identity(roster->front().identity))
        return;
    g_second_racer_open = true;
    g_second_racer_failed = false;
    g_second_racer_preset =
        (static_cast<std::size_t>(roster->front().identity.rider_index) + 1u) %
        ur::product::legacy_racer_presets().size();
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=%zu "
        "activation=next_process\n", g_second_racer_preset);
}
void choose() {
    if (g_stock_target != -1 ||
        ur::product::quick_practice_launch_owns_player_input(g_practice_launch))
        return;
    if (g_options.open) {
        ur::product::baldosa_options_activate(g_options);
        log_options("options_activated");
        return;
    }
    if (g_practice_picker.visible) {
        if (!named_profile_still_playable()) return;
        const auto selected = ur::product::quick_practice_available_selection_apply(
            g_practice_picker,
            ur::product::QuickPracticeSelectionCommand::Confirm,
            native_practice_availability());
        if (selected.result != ur::product::QuickPracticeSelectionResult::Confirmed ||
            !selected.target.valid) return;
        if (!begin_practice_session()) {
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT practice_rejected=save_sandbox "
                "source_course_admitted=0\n");
            return;
        }
        g_practice_picker = selected.state;
        g_practice_target_track = selected.target.track_id;
        g_practice_input_gap = 0;
        g_practice_launch = ur::product::begin_quick_practice_launch(selected.target);
        {
            const auto* course = ur::product::quick_practice_course(
                selected.target.track_id);
            std::string name(course ? course->name : "");
            for (auto& ch : name)
                ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT practice_requested=1 course=%d name=%s "
                "source_route=stock\n",
                static_cast<int>(selected.target.track_id), name.c_str());
        }
        return;
    }
    if (g_existing_switch_open) {
        if (g_existing_switch_saved || g_ever_entered_stock ||
            !named_profile_still_playable()) return;
        if (ur_baldosa_modern_select_existing_p1_next_boot(
                g_existing_switch_target.c_str())) {
            g_existing_switch_saved = true;
            g_existing_switch_failed = false;
            g_existing_switch_available = false;
            g_named_profile_stale = true;
            g_racer_name = "P1 CHANGED - RESTART";
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 "
                "activation=next_process\n");
        } else {
            g_existing_switch_failed = true;
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT existing_p1_saved=0 "
                "reason=verified_selector_rejected\n");
        }
        return;
    }
    if (g_second_racer_open) {
        if (g_second_racer_created || g_ever_entered_stock ||
            !named_profile_still_playable()) return;
        const auto& stock = ur::product::legacy_racer_presets();
        if (g_second_racer_preset >= stock.size()) return;
        if (ur_baldosa_modern_create_second_preset(
                static_cast<unsigned>(g_second_racer_preset))) {
            g_second_racer_created = true;
            g_second_racer_failed = false;
            g_can_add_second_racer = false;
            g_named_profile_stale = true;
            g_racer_name = "SECOND RACER SAVED - RESTART";
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
                "activation=next_process\n");
        } else {
            g_second_racer_failed = true;
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT second_racer_created=0 "
                "reason=canonical_create_rejected\n");
        }
        return;
    }
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
    if (selected == ModernRootDestination::Practice) {
        if (!named_profile_still_playable()) return;
        const auto availability = native_practice_availability();
        g_practice_picker = ur::product::open_available_quick_practice_selection(
            0u, availability);
        if (g_practice_picker.visible)
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=%d "
                "course=%d source_menu_required=1\n",
                ur::product::quick_practice_available_count(availability),
                static_cast<int>(g_practice_picker.picker.track_id));
        else
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT practice_unavailable=1 "
                "reason=no_unlocked_tours\n");
        return;
    }
    if (selected == ModernRootDestination::Records) {
        open_records_archive();
        return;
    }
    if (selected == ModernRootDestination::Options) {
        // Settings never depend on a racer: a stale or absent profile must
        // not lock the player out of volume or display recovery.
        ur::product::baldosa_options_open(g_options);
        log_options("options_opened");
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
        ur::product::quick_practice_launch_owns_player_input(g_practice_launch) ||
        g_unbound_two_player_warning_open) return;
    if (g_options.open) {
        ur::product::baldosa_options_move(g_options, delta);
        log_options("options_row");
        return;
    }
    if (g_practice_picker.visible) {
        const auto result = ur::product::quick_practice_available_selection_apply(
            g_practice_picker,
            delta > 0
                ? ur::product::QuickPracticeSelectionCommand::NextCourse
                : ur::product::QuickPracticeSelectionCommand::PreviousCourse,
            native_practice_availability());
        g_practice_picker = result.state;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT practice_course=%d\n",
            static_cast<int>(g_practice_picker.picker.track_id));
        return;
    }
    if (g_existing_switch_open) return;
    if (g_second_racer_open) {
        if (g_second_racer_created) return;
        const auto count =
            static_cast<int>(ur::product::legacy_racer_presets().size());
        const int pos = static_cast<int>(g_second_racer_preset);
        g_second_racer_preset = static_cast<std::size_t>(
            (pos + (delta > 0 ? 1 : -1) + count) % count);
        g_second_racer_failed = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT second_racer_preset=%zu\n",
            g_second_racer_preset);
        return;
    }
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
// LEFT / RIGHT. Only the Options modal consumes them today.
void adjust(int delta) {
    if (g_practice_picker.visible && g_stock_target == -1 &&
        !ur::product::quick_practice_launch_owns_player_input(
            g_practice_launch)) {
        const auto result = ur::product::quick_practice_available_selection_apply(
            g_practice_picker,
            delta > 0 ? ur::product::QuickPracticeSelectionCommand::NextTour
                      : ur::product::QuickPracticeSelectionCommand::PreviousTour,
            native_practice_availability());
        g_practice_picker = result.state;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT practice_course=%d tour_step=%d\n",
            static_cast<int>(g_practice_picker.picker.track_id), delta);
        return;
    }
    if (!g_options.open || g_confirm_quit || g_stock_target != -1) return;
    ur::product::baldosa_options_adjust(g_options, delta);
    log_options("options_adjusted");
}
void back() {
    if (g_options.open) {
        ur::product::baldosa_options_close(g_options);
        log_options(g_options.open ? "options_help_closed"
                                   : "options_closed");
        return;
    }
    if (ur::product::quick_practice_launch_owns_player_input(g_practice_launch)) {
        practice_route_abort("cancelled");
        return;
    }
    if (g_practice_picker.visible) {
        g_practice_picker = {};
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT practice_closed=1\n");
        return;
    }
    if (g_existing_switch_open) {
        g_existing_switch_open = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT existing_p1_closed=1\n");
        return;
    }
    if (g_second_racer_open) {
        g_second_racer_open = false;
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT second_racer_closed=1\n");
        return;
    }
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
    if (!restore_practice_session()) std::abort();
    g_menu = ur::product::modern_root_menu_reset();
    g_navigation_edges.reset();
    g_p2_join_edges.reset();
    g_two_seat_join.cancel();
    g_practice_picker = {};
    g_practice_launch = {};
    g_confirm_quit = false;
    g_records_open = false;
    {
        // Restore saved Display/VSync before the window is created; a
        // missing file leaves the framework's own config.ini authoritative
        // and a damaged one is reported in OPTIONS without being forced.
        const char* user_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
        const std::string options_path = user_root && *user_root
            ? ur::product::baldosa_options_path(user_root).string()
            : std::string{};
        ur::product::baldosa_options_boot(
            g_options, options_path, options_host());
        log_options("options_boot");
    }
    g_unbound_two_player_warning_open = false;
    g_named_profile_stale = false;
    g_first_racer_open = false;
    g_first_racer_created = false;
    g_first_racer_failed = false;
    g_first_racer_preset = 0;
    g_second_racer_open = false;
    g_second_racer_created = false;
    g_second_racer_failed = false;
    g_second_racer_preset = 1;
    g_existing_switch_open = false;
    g_existing_switch_saved = false;
    g_existing_switch_failed = false;
    g_existing_switch_target.clear();
    g_existing_switch_preset = 1;
    g_existing_switch_available = false;
    g_ever_entered_stock = false;
    g_can_add_second_racer = false;
    if (const char* selected = ur_baldosa_modern_profile_selected_id()) {
        const char* catalog = ur_baldosa_modern_profile_catalog_path();
        const auto entries = catalog
            ? ur::product::load_host_profile_catalog_file(catalog)
            : std::optional<std::vector<
                ur::product::HostProfileCatalogEntry>>{};
        g_can_add_second_racer = entries && entries->size() == 1u &&
            entries->front().profile_id == selected &&
            ur::product::valid_racer_identity(entries->front().identity);
        if (entries && entries->size() == 2u) {
            const bool active_found = std::any_of(
                entries->begin(), entries->end(),
                [selected](const auto& e) { return e.profile_id == selected; });
            const auto other = std::find_if(
                entries->begin(), entries->end(),
                [selected](const auto& e) { return e.profile_id != selected; });
            g_existing_switch_available = active_found &&
                other != entries->end() &&
                ur_baldosa_modern_profile_can_join_opponent(&*other);
        }
    }
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
    case SDLK_LEFT: physical = 5; action = 5; break;
    case SDLK_RIGHT: physical = 6; action = 6; break;
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
    g_root_notice.clear();
    if (action == 2) choose();
    else if (action == 3) back();
    else if (action == 4) open_stock_racer_setup();
    else if (action == 5) adjust(-1);
    else if (action == 6) adjust(1);
    else navigate(action);
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
    case kGamepadBtn_DpadLeft: physical = 6; action = 5; break;
    case kGamepadBtn_DpadRight: physical = 7; action = 6; break;
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
    g_root_notice.clear();
    if (action == 2) choose();
    else if (action == 3) back();
    else if (action == 4) open_stock_racer_setup();
    else if (action == 5) adjust(-1);
    else if (action == 6) adjust(1);
    else navigate(action);
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
    view.root_notice = g_root_notice;
    view.practice_picker_open = g_practice_picker.visible;
    view.practice_launch_pending =
        ur::product::quick_practice_launch_owns_player_input(g_practice_launch);
    if (view.practice_picker_open) {
        const auto preview = ur::product::quick_practice_selection_view(
            g_practice_picker);
        view.practice_course_name = preview.course_name;
        view.practice_courses_open = static_cast<std::uint8_t>(
            ur::product::quick_practice_available_count(
                native_practice_availability()));
        view.practice_tour_name = preview.tour_name;
        view.practice_kind_label = preview.kind_label;
    }
    view.unbound_two_player_warning_open =
        g_unbound_two_player_warning_open;
    view.first_racer_shortcut_available =
        !ur_baldosa_modern_profile_selected_id() &&
        !g_first_racer_created;
    view.second_racer_shortcut_available =
        g_can_add_second_racer && !g_ever_entered_stock &&
        !g_second_racer_created && !g_named_profile_stale;
    view.second_racer_created = g_second_racer_created;
    view.existing_profile_switch_available =
        g_existing_switch_available && !g_ever_entered_stock &&
        !g_named_profile_stale;
    view.existing_profile_switch_saved = g_existing_switch_saved;
    view.first_racer_open =
        g_first_racer_open || g_second_racer_open || g_existing_switch_open;
    view.first_racer_is_second = g_second_racer_open;
    view.first_racer_is_switch = g_existing_switch_open;
    view.first_racer_created =
        g_first_racer_created || g_second_racer_created ||
        g_existing_switch_saved;
    view.first_racer_failed =
        g_first_racer_failed || g_second_racer_failed ||
        g_existing_switch_failed;
    view.racer_shortcuts_available = false;
    const auto& presets = ur::product::legacy_racer_presets();
    const auto chosen = g_existing_switch_open
        ? g_existing_switch_preset
        : g_second_racer_open ? g_second_racer_preset : g_first_racer_preset;
    if (chosen < presets.size())
        view.first_racer_preset_name = presets[chosen].name;
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
    std::array<ur::product::BaldosaOptionsRowText,
               ur::product::kBaldosaOptionsRowCount> option_text{};
    if (g_options.open) {
        option_text = ur::product::baldosa_options_row_texts(g_options);
        view.options_open = true;
        view.options_controls_help = g_options.controls_help;
        view.options_selected = static_cast<std::size_t>(g_options.selected);
        view.options_row_count = option_text.size();
        for (std::size_t i = 0; i < option_text.size(); ++i)
            view.options_rows[i] = {option_text[i].label,
                                    option_text[i].value,
                                    option_text[i].adjustable};
        view.options_status =
            ur::product::baldosa_options_status_text(g_options.status);
        view.options_notice =
            ur::product::baldosa_options_standing_notice(g_options);
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
// Reuse the shipping QuickPracticeLaunch state machine and stock input
// transport. The original guest must enter the requested original course,
// not merely show a 1P picker, before the host releases controller focus.
void observe_practice_guest() {
    using namespace ur::product;
    if (!quick_practice_launch_owns_player_input(g_practice_launch)) return;
    if (!named_profile_still_playable()) {
        practice_route_abort("active_profile_stale");
        return;
    }
    const bool in_race = g_ram[0x0313] == 1u;
    const auto identity = in_race
        ? ur_uniracers_identify_course(g_ram + 0x10000u, 0x10000u)
        : UrUniracersCourseIdentity{};
    {
        // Bounded, change-only diagnostic of the ORIGINAL menus the route
        // is walking (menu id and cursor), so a stranded course shows
        // exactly where the stock game refused to go.
        static unsigned last = 0x10000u;
        const unsigned now = (static_cast<unsigned>(g_ram[0x009f]) << 8) |
                             g_ram[0x009b];
        if (now != last) {
            last = now;
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT practice_trace menu=%02x cursor=%u\n",
                static_cast<unsigned>(g_ram[0x009f]),
                static_cast<unsigned>(g_ram[0x009b]));
        }
    }
    // The stock list menus do not register a second discrete press issued on
    // the very next frame after a cursor move (measured on the real guest:
    // a one-step tour/track move works, a multi-step walk strands). Give each
    // queued input a short physical-style gap before the next is considered.
    if (g_practice_input_gap > 0) {
        --g_practice_input_gap;
        return;
    }
    const QuickPracticeLaunchObservation observation{
        g_ram[0x009f], g_ram[0x009b], in_race,
        identity.valid ? identity.course_index - 1 : -1};
    const auto step = advance_quick_practice_launch(
        g_practice_launch, observation);
    if (step.route_violation || step.course_mismatch || step.timed_out) {
        practice_route_abort(step.course_mismatch ? "wrong_source_course" :
                             step.timed_out ? "timeout" : "source_route_violation");
        // A wrong source race is playable but cannot gain this root's
        // profile/result authority. Do not leave its human controls frozen.
        if (in_race) {
            g_visible = false;
            g_stock_handed_off = false;
            g_handed_off_players = 0;
            ur_baldosa_product_set_host_focus(0);
        }
        return;
    }
    if (step.input != QuickPracticeLaunchInput::None) {
        const auto mask = quick_practice_runner_mask(step.input);
        if (!quick_practice_runner_mask_is_discrete_menu_input(mask) ||
            !ur_baldosa_product_queue_stock_menu_input(mask)) {
            g_practice_launch = quick_practice_launch_retry_state(
                g_practice_launch);
            if (g_practice_launch.observations_remaining == 0u)
                practice_route_abort("source_input_unavailable");
            return;
        }
    }
    g_practice_launch = step.state;
    if (step.input != QuickPracticeLaunchInput::None)
        g_practice_input_gap = kPracticeInputGapFrames;
    if (!step.race_ready) return;
    if (!in_race || !identity.valid || g_practice_target_track < 0 ||
        identity.course_index != g_practice_target_track + 1) {
        practice_route_abort("course_identity_unverified");
        return;
    }
    const int entered_track = g_practice_target_track;
    g_practice_target_track = -1;
    g_practice_launch = {};
    g_visible = false;
    g_stock_handed_off = true;
    g_ever_entered_stock = true;
    g_handed_off_players = 1u;
    g_handed_off_saw_race = true;
    ur_baldosa_product_set_host_focus(0);
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=%d "
        "original_course=%d race=1 source_identity=verified\n",
        entered_track, entered_track + 1);
}
extern "C" void ur_baldosa_modern_root_stock_observe_guest(void) {
    observe_practice_guest();
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
            g_ever_entered_stock = true;
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
    // Smoke modes are the decimal strings "1".."14" and nothing else.
    {
        char* parse_end = nullptr;
        const long mode = opt && *opt ? std::strtol(opt, &parse_end, 10) : 0;
        if (!g_visible || !opt || !parse_end || *parse_end != '\0' ||
            mode < 1 || mode > 14) return;
        // Test-only: stop scripted input after this frame so a human or a
        // screenshot harness can inspect the held screen.
        const char* last = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE_LAST_FRAME");
        if (last && *last && frame > static_cast<unsigned>(std::strtoul(
                last, nullptr, 10))) return;
    }
    // Controlled host-root edge on an anonymous install. No created racer
    // is activated in this guest; a new process must load canonical SRAM.
    if (std::strcmp(opt, "4") == 0) {
        // No-argument real CMD-launcher acceptance only. The existing stock
        // profile creation smoke remains identical without this explicit
        // test-only environment flag. Exercise Quit in process one and Quit
        // again after the CMD launcher restarted the *same* native game.
        const char* launcher_probe =
            std::getenv("UR_BALDOSA_LAUNCHER_RESTART_SMOKE");
        const bool launcher_smoke = launcher_probe &&
            std::strcmp(launcher_probe, "1") == 0;
        int key = 0;
        if (!launcher_smoke) {
            // Separate opt-in, TEST ONLY: navigate to stock preset 1 and
            // confirm through the very same real root menu edges. Nothing
            // changes in the no-args launcher or default Mike acceptance.
            const char* preset_probe =
                std::getenv("UR_BALDOSA_FIRST_RACER_TEST_PRESET");
            const bool second_stock_preset = preset_probe &&
                std::strcmp(preset_probe, "1") == 0;
            key = frame == 60 ? SDLK_x :
                  second_stock_preset && frame == 61 ? SDLK_DOWN :
                  frame == (second_stock_preset ? 63u : 62u)
                      ? SDLK_RETURN : 0;
        } else if (ur_baldosa_modern_profile_selected_id()) {
            // Second game: no first-racer creation or stock-route input.
            key = frame == 90 ? SDLK_ESCAPE :
                  frame == 92 ? SDLK_RETURN : 0;
        } else {
            // First game: create; close modal; request Quit; confirm Quit.
            key = frame == 60 ? SDLK_x :
                  frame == 62 ? SDLK_RETURN :
                  (frame == 90 || frame == 92) ? SDLK_ESCAPE :
                  frame == 94 ? SDLK_RETURN : 0;
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
        event.type = SDL_KEYUP;
        if (SDL_PushEvent(&event) != 1) std::abort();
        return;
    }
    // Distinct stock P2 profile from an already named P1 native guest.
    // Test-only SDL button edges; never an automatic profile/catalog
    // update, forged native result, or change to live original SRAM.
    if (std::strcmp(opt, "5") == 0 ||
        std::strcmp(opt, "6") == 0) {
        // Mode 6 additionally cancels the successful modal, then attempts
        // a stock Play command against the same STILL-OLD guest. The sticky
        // stale barrier must keep P1 on its original SRAM until restart.
        const bool selector_smoke = std::strcmp(opt, "6") == 0;
        if (selector_smoke && frame == 90) {
            if (!g_named_profile_stale || !g_existing_switch_saved ||
                !g_visible || g_stock_target != -1)
                std::abort();
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT "
                "existing_p1_stale_race_blocked=1\n");
            return;
        }
        // Test-only existing P2 creation selects Martin via X/Down/A,
        // matching the already-proven original 2P source picker exactly.
        // Mode 6's existing P1 selector path remains unchanged.
        const char* preset_probe =
            std::getenv("UR_BALDOSA_SECOND_RACER_TEST_PRESET");
        const bool source_martin = !selector_smoke && preset_probe &&
            std::strcmp(preset_probe, "2") == 0;
        const int key = frame == 60 ? SDLK_x :
                        source_martin && frame == 61 ? SDLK_DOWN :
                        frame == (source_martin ? 63u : 62u)
                            ? SDLK_RETURN :
                        selector_smoke && frame == 76 ? SDLK_ESCAPE :
                        selector_smoke && frame == 80 ? SDLK_RETURN : 0;
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
    // Test-only mode 7 exercises the REAL P1 gamepad dispatch/physical-edge
    // owner for selecting an existing racer. It is semantic gamepad input,
    // NOT a physical USB/Bluetooth controller or artificial guest event.
    // The source guest cannot race after next-boot selection is committed.
    if (std::strcmp(opt, "7") == 0) {
        if (frame == 90) {
            if (!g_named_profile_stale || !g_existing_switch_saved ||
                !g_visible || g_stock_target != -1)
                std::abort();
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_ROOT "
                "existing_p1_stale_race_blocked=1\n");
            return;
        }
        const int button = frame == 60 ? kGamepadBtn_X :
                           frame == 62 ? kGamepadBtn_A :
                           frame == 76 ? kGamepadBtn_B :
                           frame == 80 ? kGamepadBtn_A : -1;
        if (button < 0) return;
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=%d\n",
            button);
        return;
    }
    // Test-only first and second profile creation via the already-shipping
    // P1 native gamepad handler: X, (P2 Down), A. Preserve the old keyboard
    // fixture modes 4/5 and the P1 gamepad selector mode 7 unchanged.
    // These inputs are semantic controller edges, never synthetic guest
    // writes, a fake achievement or a physical-controller certification.
    if (std::strcmp(opt, "8") == 0 || std::strcmp(opt, "9") == 0) {
        const bool first_racer = std::strcmp(opt, "8") == 0;
        const int button = frame == 60 ? kGamepadBtn_X :
                           !first_racer && frame == 61
                               ? kGamepadBtn_DpadDown :
                           frame == (first_racer ? 62u : 63u)
                               ? kGamepadBtn_A : -1;
        if (button < 0) return;
        const char* const action =
            button == kGamepadBtn_X ? "X" :
            button == kGamepadBtn_DpadDown ? "DPAD_DOWN" : "A";
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT "
            "synthetic_profile_gamepad mode=%s button=%s\n", opt, action);
        return;
    }
    // Test-only no-argument extracted Windows CMD startup route:
    // actually dispatch native P1 gamepad X/A then B/B/A to create Mike,
    // quit and let the unchanged CMD launcher detect the new selector.
    // Its second unmodified native process receives B/A to quit after
    // validating the newly booted named SRAM. No --script/ROM argument,
    // synthetic result, guest write, or second launcher implementation.
    if (std::strcmp(opt, "10") == 0) {
        const char* launcher = std::getenv(
            "UR_BALDOSA_LAUNCHER_RESTART_SMOKE");
        if (!launcher || std::strcmp(launcher, "1") != 0) return;
        const char* selected = ur_baldosa_modern_profile_selected_id();
        const bool named = selected && *selected;
        const int button = named
            ? (frame == 90 ? kGamepadBtn_B :
               frame == 92 ? kGamepadBtn_A : -1)
            : (frame == 60 ? kGamepadBtn_X :
               frame == 62 ? kGamepadBtn_A :
               (frame == 90 || frame == 92) ? kGamepadBtn_B :
               frame == 94 ? kGamepadBtn_A : -1);
        if (button < 0) return;
        const char* action = button == kGamepadBtn_X ? "X" :
                             button == kGamepadBtn_B ? "B" : "A";
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=%s button=%s\n",
            named ? "mike" : "anonymous", action);
        return;
    }
    // CI-only mode 12 drives the real native OPTIONS journey through the
    // production P1 gamepad handler: Down x4 and A open OPTIONS; RIGHT
    // changes Display to borderless; Down + RIGHT moves VSync to adaptive;
    // Down + LEFT lowers Volume to 90; Down + A opens the Controls page,
    // B closes it, B closes OPTIONS, then B / A confirms Quit so the
    // normal host shutdown persists nothing it has not already saved.
    // Semantic pad edges only: not physical controller acceptance.
    if (std::strcmp(opt, "12") == 0) {
        const int button =
            frame >= 60 && frame <= 63 ? kGamepadBtn_DpadDown :
            frame == 64 ? kGamepadBtn_A :
            frame == 66 ? kGamepadBtn_DpadRight :
            frame == 68 ? kGamepadBtn_DpadDown :
            frame == 70 ? kGamepadBtn_DpadRight :
            frame == 72 ? kGamepadBtn_DpadDown :
            frame == 74 ? kGamepadBtn_DpadLeft :
            frame == 76 ? kGamepadBtn_DpadDown :
            frame == 78 ? kGamepadBtn_A :
            frame == 80 || frame == 82 || frame == 90 ? kGamepadBtn_B :
            frame == 92 ? kGamepadBtn_A : -1;
        if (button < 0) return;
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT options_gamepad frame=%u button=%d\n",
            frame, button);
        return;
    }
    // CI-only mode 14: boot, then ask to quit and confirm (B, A) through the
    // production P1 handler. Used by packaged-launcher runs that must not
    // change any setting but still need a clean, script-free exit.
    if (std::strcmp(opt, "14") == 0) {
        const int button = frame == 60 ? kGamepadBtn_B :
                           frame == 62 ? kGamepadBtn_A : -1;
        if (button < 0) return;
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT quit_gamepad frame=%u button=%d\n",
            frame, button);
        return;
    }
    // CI-only mode 13: a fresh process proves the persisted choices were
    // restored, then reaches DEFAULTS (Down x4 after A opens OPTIONS) and
    // restores them, then quits.
    if (std::strcmp(opt, "13") == 0) {
        const int button =
            frame >= 60 && frame <= 63 ? kGamepadBtn_DpadDown :
            frame == 64 ? kGamepadBtn_A :
            frame >= 66 && frame <= 69 ? kGamepadBtn_DpadDown :
            frame == 71 ? kGamepadBtn_A :
            frame == 80 || frame == 82 ? kGamepadBtn_B :
            frame == 84 ? kGamepadBtn_A : -1;
        if (button < 0) return;
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT options_gamepad frame=%u button=%d\n",
            frame, button);
        return;
    }
    // CI-only mode 11 traverses the real P1 handler: Down, A to open
    // Practice, A to confirm Dragster. The original tour/racer/track/GO
    // navigation thereafter belongs solely to the shared route state.
    if (std::strcmp(opt, "11") == 0) {
        // Optional CI-only course walk: UR_BALDOSA_PRACTICE_TEST_STEPS=n
        // presses DPAD DOWN n more times inside the picker (each is one
        // genuine NextCourse over the unlocked courses) before the confirm A.
        // Unset keeps the original Down, A, A (Dragster) gesture exactly.
        const char* steps_env = std::getenv("UR_BALDOSA_PRACTICE_TEST_STEPS");
        const unsigned steps = steps_env && *steps_env
            ? static_cast<unsigned>(std::strtoul(steps_env, nullptr, 10)) : 0u;
        const unsigned confirm = 64u + 2u * steps;
        int button = -1;
        if (frame == 60) button = kGamepadBtn_DpadDown;
        else if (frame == 62 || frame == confirm) button = kGamepadBtn_A;
        else if (frame > 62 && frame < confirm && (frame % 2u) == 0u)
            button = kGamepadBtn_DpadDown;
        if (button < 0) return;
        if (!ur_baldosa_modern_root_gamepad(0, button, 1) ||
            !ur_baldosa_modern_root_gamepad(0, button, 0))
            std::abort();
        std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT practice_gamepad=%s\n",
                     button == kGamepadBtn_DpadDown ? "DOWN" : "A");
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
extern "C" int ur_baldosa_modern_root_practice_active(void) {
    return configured() && g_practice_session_active ? 1 : 0;
}
extern "C" int ur_baldosa_modern_root_restore_practice_on_shutdown(void) {
    return restore_practice_session() ? 1 : 0;
}
extern "C" unsigned ur_baldosa_modern_root_guest_players(void) {
    return configured() && !g_practice_session_active &&
        !g_visible && g_stock_handed_off
        ? g_handed_off_players : 0u;
}

extern "C" unsigned ur_baldosa_modern_root_paint_count(void) {
    return g_paint_count;
}
