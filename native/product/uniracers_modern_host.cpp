#include "uniracers_modern_host.h"

extern "C" {
#include "common_rtl.h"
#include "snes_overlay_draw.h"
}

// config.h is a plain C header without __cplusplus guards; give its
// functions (e.g. the live GamepadMap lookup) C linkage.
extern "C" {
#include "desktop/config.h"
}
#include "desktop/host_main.h"
#include "desktop/sdl_compat.h"
#include "keybinds.h"
#include "completed_run_browser_host.h"
#include "completed_run_capture.hpp"
#include "completed_run_ghost.hpp"
#include "completed_run_ghost_frame.hpp"
#include "completed_run_ghost_policy.hpp"
#include "completed_run_ghost_trace.hpp"
#include "completed_run_presentation.hpp"
#include "completed_run_ghost_world_sample.hpp"
#include "completed_run_record.hpp"
#include "completed_run_store.hpp"
#include "clean_stock_sram.hpp"
#include "controller_hotplug_policy.hpp"
#include "focus_pause_policy.hpp"
#include "haptic_feedback_policy.hpp"
#include "fast_repeat_navigation.hpp"
#include "host_product_state.hpp"
#include "host_product_store.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_state.hpp"
#include "host_profile_catalog.hpp"
#include "modern_racer_identity.hpp"
#include "modern_tour_action_menu.hpp"
#include "modern_results_navigation.hpp"
#include "modern_tour_continue.hpp"
#include "modern_host_input_release_latch.hpp"
#include "modern_main_menu_strip.hpp"
#include "next_event_derivation.hpp"
#include "modern_challenge_tier_selector.hpp"
#include "quick_practice_catalog.hpp"
#include "quick_practice_available_selection.hpp"
#include "quick_practice_selection_view.hpp"
#include "../title/uniracers_practice_tour_unlock.hpp"
#include "../title/uniracers_tour_progress_overview.hpp"
#include "quick_practice_input_mask.hpp"
#include "quick_practice_launch.hpp"
#include "recent_course_origin.hpp"
#include "regional_presentation_input_policy.hpp"
#include "regional_presentation_input_coordinator.hpp"
#include "regional_title_presenter.hpp"
#include "host_profile_store.hpp"
#include "internal_render_scale_policy.hpp"
#include "local_multiplayer_setup.hpp"
#include "local_multiplayer_participants.hpp"
#include "local_multiplayer_match_binding.hpp"
#include "multiplayer_match_record.hpp"
#include "run_record_capture_policy.hpp"
#include "local_multiplayer_seat_text.hpp"
#include "modern_pause_input.h"
#include "modern_pause_menu.h"
#include "modern_profile_reset.hpp"
#include "modern_options_menu.h"
#include "modern_controls_binding_authority.hpp"
#include "modern_controls_presenter.hpp"
#include "modern_controls_rebind.hpp"
#include "modern_overlay_composition.hpp"
#include "modern_overlay_text_fit.hpp"
#include "modern_pad_glyphs.hpp"
#include "modern_session_c_api.h"
#include "output_resolution_runtime_policy.hpp"
#include "presentation_density_compositor.hpp"
#include "presentation_sampling_policy.hpp"
#include "uniracers_course_identity.h"
#include "uniracers_restart_policy.h"
#include "uniracers_run_data.h"
#include "uniracers_two_player_result.hpp"
#include "uniracers_ws_margins.h"
#include "uniracers_tour_resume.hpp"
#include "widescreen_output_composition.hpp"
#include "../presentation/completed_run_ghost_racer_selector.hpp"
#include "../presentation/completed_run_ghost_raster.hpp"
#include "../presentation/racer_hd_presenter.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <cstring>
#include <cstdio>
#include <optional>
#include <string>
#include <utility>
#include <vector>

extern "C" void snesrecomp_desktop_arm_relative_input(uint64_t post_frame_origin);
extern "C" int snesrecomp_desktop_load_relative_input_file(const char* path);

namespace {

std::string uppercase_keybind_label(SDL_Scancode scancode) {
    if (scancode == SDL_SCANCODE_UNKNOWN) return "NONE";
    const char* raw = SDL_GetScancodeName(scancode);
    if (!raw || !raw[0]) return "NONE";
    std::string out(raw);
    for (char& ch : out) {
        if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
    }
    return out;
}

UrModernSession* g_session;
ur::product::HostProductState g_product_state;
std::optional<ur::product::RegionalPresentationInputCoordinator>
    g_regional_input;
bool g_regional_title_surface_previous;
ur::product::HostPresentationFpsMode g_live_presentation_fps_mode =
    ur::product::HostPresentationFpsMode::Game;
bool g_product_state_initialized;
std::string g_product_state_path;
std::optional<ur::product::HostProfileState> g_profile_state;
std::string g_profile_state_path;
bool g_profile_state_writable;
UrModernPauseMenu g_pause_menu;
UrModernOptionsMenu g_options_menu;
bool g_options_visible;
bool g_frontend_options_active = false;
bool g_frontend_options_draw_reported = false;
bool g_frontend_controls_draw_reported = false;
bool g_controls_visible;
ur::product::ModernControlsRebindState g_controls_rebind;
bool g_run_data_visible;
bool g_quit_confirm_visible;
bool g_onboarding_initialized;
bool g_onboarding_visible;
bool g_onboarding_manual_open;
bool g_onboarding_acceptance_fired;
bool g_binding_diagnostics_reported;
std::string g_onboarding_seen_path;

ur::product::LocalMultiplayerSetupState g_local_multiplayer_setup;
ur::product::LocalMultiplayerParticipantSelection
    g_local_multiplayer_participants;
bool g_local_multiplayer_participants_ready;
ur::product::ControllerHotplugState g_controller_hotplug;
std::array<std::string, ur::product::kControllerSeatCount>
    g_controller_seat_names{};
bool g_controller_hotplug_acceptance_done;
bool g_vibration_options_acceptance_done;
bool g_volume_options_acceptance_done;
unsigned g_volume_options_acceptance_frames;
unsigned g_vibration_options_acceptance_frames;
int g_haptic_acceptance_stage;
unsigned g_haptic_acceptance_device_rumbles;
int g_main_menu_pad_acceptance_stage;
unsigned g_main_menu_pad_acceptance_frames;
std::string g_main_menu_strip_reported;
int g_controller_hotplug_acceptance_stage;
unsigned g_controller_hotplug_acceptance_frames;
std::uint64_t g_controller_hotplug_acceptance_source;
std::uint32_t g_controller_hotplug_acceptance_held;
std::uint32_t g_last_human_input_word;
std::uint64_t g_human_input_observations;
std::uint64_t g_controller_hotplug_acceptance_observation;
std::array<ur::product::LocalInputSource, 2> g_local_multiplayer_sources{};
std::array<std::uint32_t, 2> g_local_multiplayer_consumed_buttons{};
bool g_local_multiplayer_join_visible;
bool g_local_multiplayer_two_player_visit;

bool g_practice_active;
bool g_practice_acceptance_fired;
bool g_practice_race_ready_reported;
unsigned g_practice_cancel_acceptance_frames;
bool g_profile_panel_acceptance_confirm_pending;
std::string g_profile_panel_acceptance_input_path;
bool g_suppress_human_input_once;
ur::product::ModernHostInputReleaseLatch g_human_input_release_latch;
unsigned g_fast_repeat_acceptance_frames;
bool g_fast_repeat_acceptance_fired;
bool g_ghost_target_acceptance_fired;
unsigned g_recent_course_acceptance_frames;
bool g_recent_course_acceptance_fired;
int g_next_event_acceptance_stage;
unsigned g_next_event_acceptance_frames;
int g_results_navigation_acceptance_stage;
unsigned g_results_navigation_acceptance_frames;
unsigned g_pause_open_acceptance_frames;
bool g_pause_open_acceptance_fired;
int g_practice_cancel_gamepad_button = -1;
ur::product::QuickPracticeLaunchState g_practice_launch;
ur::product::QuickPracticeSelection g_practice_picker;
bool g_practice_picker_draw_reported = false;
std::optional<std::string> g_practice_picker_profile_id;
ur::product::QuickPracticeAvailability g_practice_picker_availability;
bool g_progress_overview_visible = false;
bool g_progress_overview_draw_reported = false;
ur::title::StockTourProgressOverview g_progress_overview;
std::optional<std::string> g_progress_overview_profile_id;
std::optional<std::uint8_t> g_recent_course_track_id;
std::string g_recent_course_profile_key;
ur::product::RecentCourseOriginState g_recent_course_origin;
bool g_recent_course_attract_reported = false;
std::optional<std::uint32_t> g_fast_repeat_sram_before;
std::optional<std::uint8_t> g_fast_repeat_course_before;
std::vector<uint8_t> g_practice_sram_snapshot;
std::string g_practice_original_save_root;
std::string g_practice_input_path;

ur::product::ModernTourContinueState g_tour_continue;
std::string g_tour_continue_profile_id;
// Next Event target for the in-flight route, and the track to verify once the
// routed confirm has entered an authoritative race.
std::optional<std::uint8_t> g_next_event_target_track;
std::optional<std::uint8_t> g_next_event_verify_track;
std::string g_tour_continue_input_path;
bool g_tour_continue_acceptance_fired;
bool g_tour_action_visible;
ur::product::ModernTourActionMenu g_tour_action_menu;
ur::product::ModernResultsNavigationMenu g_results_navigation_menu;
std::optional<ur::title::TourProgress> g_results_route_progress;
std::string g_results_route_profile_id;
ur::product::ModernResultsAction g_results_route_pending =
    ur::product::ModernResultsAction::None;
bool g_results_tour_route_active;

bool g_display_caps_reported;
bool g_profile_sram_reported;
std::vector<ur::product::HostProfileCatalogEntry> g_profile_catalog;
std::string g_profile_catalog_path;
bool g_profile_menu_visible;
enum class ProfileEditMode { None, Create, Rename };
ProfileEditMode g_profile_edit_mode = ProfileEditMode::None;
std::size_t g_profile_menu_index;
std::size_t g_profile_preset_index;
std::string g_profile_edit_name;
bool g_profile_edit_pristine;
bool g_profile_cool_name_notice;
ur::product::ModernProfileResetState g_profile_reset;
bool g_exit_frontend_waiting_for_main;
bool g_exit_frontend_waiting_for_usable;
bool g_exit_frontend_acceptance_fired;
unsigned g_exit_frontend_acceptance_surface_frames;
bool g_pause_records_acceptance_fired;
unsigned g_pause_records_acceptance_surface_frames;
ur::product::CompletedRunCapture g_run_capture;
ur::product::CompletedRunCapture g_multiplayer_run_capture;
std::optional<ur::product::HostProfileCatalogEntry>
    g_multiplayer_capture_player1;
std::optional<ur::product::HostProfileCatalogEntry>
    g_multiplayer_capture_player2;
UrUniracersCourseIdentity g_multiplayer_capture_course{};
std::uint64_t g_multiplayer_capture_origin_frame;
bool g_multiplayer_match_acceptance_seeded;
ur::product::CompletedRunGhostState g_run_ghosts;
ur::product::CompletedRunGhostTraceCapture g_run_ghost_trace_capture;
std::optional<ur::product::CompletedRunGhostTrace> g_run_ghost_playback_trace;
std::optional<ur::product::CompletedRunGhostPresentationFrame>
    g_run_ghost_presentation_frame;
bool g_run_capture_previous_active;
bool g_run_ghost_draw_reported;
uint64_t g_run_capture_origin_frame;
uint16_t g_run_capture_checkpoint;
std::optional<ur::product::RunDataDeltaPresentation> g_run_timing_last_split;
bool g_run_timing_supported;
bool g_run_timing_race_diag_reported;
bool g_run_timing_results_diag_reported;
UrUniracersRestartPolicyState g_title_policy;
UrUniracersRestartSurface g_surface = UR_UNIRACERS_RESTART_UNSUPPORTED;
ur::product::HostWidescreenSceneState g_widescreen_scene_state;
ur::product::HostSceneComposition g_widescreen_scene =
    ur::product::HostSceneComposition::FixedCenter;

// Acceptance-only capability probe. Ordinary product code must consume the
// normalized host contract rather than SDL display identifiers or mode lists.
// The probe also verifies exact-mode and index validation fail closed before
// output resolution is allowed to become a persisted product setting.
void report_display_capabilities_once() {
    if (g_display_caps_reported ||
        !std::getenv("UR_DISPLAY_CAPS_DIAGNOSTICS")) {
        return;
    }
    g_display_caps_reported = true;

    const int count = snesrecomp_desktop_output_mode_count();
    SnesDesktopOutputMode native{};
    SnesDesktopOutputMode first{};
    const int native_ok =
        snesrecomp_desktop_get_native_output_mode(&native);
    const int first_ok =
        count > 0 ? snesrecomp_desktop_get_output_mode(0, &first) : 0;
    const int apply_ok =
        first_ok ? snesrecomp_desktop_set_output_mode(&first) : 0;
    const SnesDesktopOutputMode impossible{1, 1, 12345};
    const int reject_ok =
        !snesrecomp_desktop_set_output_mode(&impossible);
    SnesDesktopOutputMode out_of_range{};
    const int range_reject_ok =
        !snesrecomp_desktop_get_output_mode(count, &out_of_range);

    std::fprintf(
        stderr,
        "UR_DISPLAY_CAPS modes=%d native_ok=%d native=%dx%d@%d first_ok=%d first=%dx%d@%d apply_ok=%d reject_ok=%d range_reject_ok=%d\n",
        count,
        native_ok,
        native.width,
        native.height,
        native.refresh_millihz,
        first_ok,
        first.width,
        first.height,
        first.refresh_millihz,
        apply_ok,
        reject_ok,
        range_reject_ok);
    std::fflush(stderr);
}

bool modern_mode() {
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return !(mode && std::strcmp(mode, "authentic") == 0);
}

void ensure_product_state();
bool persist_product_state(const ur::product::HostProductState& candidate);
void ensure_profile_catalog();
void product_diagnostic(const char* message);
std::string controller_display_name(std::uint64_t source_id);
bool paused();
bool restart_surface();
bool dispatch(UrModernPauseAction action);
bool abort_practice_route_to_frontend(const char* diagnostic);
bool request_desktop_quit();
void clear_results_navigation_route();
void rearm_run_capture_after_retry();
uint32_t current_sram_digest();
const char* regional_presentation_name(
    ur::product::RegionalPresentation presentation) noexcept {
    return presentation == ur::product::RegionalPresentation::Europe
        ? "europe" : "north_america";
}

bool regional_host_text_entry_active() noexcept {
    return g_profile_edit_mode != ProfileEditMode::None;
}

ur::product::RegionalSecretContext current_regional_secret_context() noexcept {
    const bool in_race =
        g_ram && g_ram[0x0313] == 0x01;
    const std::uint8_t current_menu =
        g_ram ? g_ram[0x009F] : 0u;
    return ur::product::regional_secret_context(
        modern_mode(),
        current_menu,
        in_race,
        regional_host_text_entry_active());
}

ur::product::RegionalPresentationInputCoordinator&
regional_input_coordinator() {
    ensure_product_state();
    if (!g_regional_input) {
        g_regional_input.emplace(g_product_state);
    }
    return *g_regional_input;
}

bool apply_regional_input_decision(
    const ur::product::RegionalInputDecision& decision,
    const char* source) {
    if (decision.update ==
        ur::product::RegionalPresentationUpdate::SaveRequired) {
        const bool saved = persist_product_state(g_product_state);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_REGIONAL SWITCH source=%s presentation=%s saved=%d\n",
                source,
                regional_presentation_name(
                    g_product_state.regional_presentation),
                saved ? 1 : 0);
            std::fflush(stderr);
        }
    }
    return decision.consume;
}

ur::product::LocalInputSource local_multiplayer_controller_source(
    std::uint64_t source_id,
    bool connected) noexcept {
    // SDL joystick instance IDs are 32-bit process-local identities and may be
    // zero. The product model reserves zero for "no source", so store id+1.
    return {
        ur::product::LocalInputKind::Controller,
        source_id + 1u,
        connected,
    };
}

ur::product::LocalMultiplayerSlot local_multiplayer_slot_for_player(
    int player_index) noexcept {
    return player_index == 1
        ? ur::product::LocalMultiplayerSlot::Player2
        : ur::product::LocalMultiplayerSlot::Player1;
}

void clear_local_multiplayer_session() {
    g_local_multiplayer_join_visible = false;
    g_local_multiplayer_two_player_visit = false;
    g_local_multiplayer_setup = {};
    g_local_multiplayer_participants = {};
    g_local_multiplayer_participants_ready = false;
}

std::string local_multiplayer_seat_device_line(
    ur::product::LocalMultiplayerSlot slot) {
    const auto presentation = ur::product::local_multiplayer_seat_presentation(
        g_local_multiplayer_setup, slot);
    const auto& assignment = ur::product::local_multiplayer_assignment(
        g_local_multiplayer_setup, slot);
    std::string name;
    if (assignment.assigned &&
        assignment.source.kind == ur::product::LocalInputKind::Controller &&
        assignment.source.stable_id != 0u) {
        name = controller_display_name(assignment.source.stable_id - 1u);
    }
    return ur::product::local_multiplayer_seat_device_text(presentation, name);
}

void observe_local_multiplayer_seat_lines() {
    static std::array<std::string, 2> last{};
    if (!g_local_multiplayer_join_visible) {
        last = {};
        return;
    }
    constexpr ur::product::LocalMultiplayerSlot kSlots[2] = {
        ur::product::LocalMultiplayerSlot::Player1,
        ur::product::LocalMultiplayerSlot::Player2,
    };
    for (std::size_t i = 0; i < 2; ++i) {
        std::string line = local_multiplayer_seat_device_line(kSlots[i]);
        if (line == last[i]) continue;
        last[i] = line;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr, "UR_LOCAL_MULTIPLAYER SEAT slot=%s device=%s\n",
                ur::product::local_multiplayer_slot_label(kSlots[i]),
                line.empty() ? "EMPTY" : line.c_str());
            std::fflush(stderr);
        }
    }
}

void update_local_multiplayer_join_surface() {
    if (!modern_mode() || !g_ram) {
        clear_local_multiplayer_session();
        return;
    }

    const bool two_player_select = g_ram[0x009F] == 0x3D;
    const bool settled_frontend =
        g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7;
    if (settled_frontend) {
        clear_local_multiplayer_session();
        return;
    }

    if (!two_player_select) {
        g_local_multiplayer_join_visible = false;
        g_local_multiplayer_two_player_visit = false;
        // Once both explicit participant profiles are confirmed, retain the
        // session identity through stock setup, race, result and track choice.
        // It is retired only on return to the settled frontend above.
        if (!g_local_multiplayer_participants_ready) {
            g_local_multiplayer_setup = {};
            g_local_multiplayer_participants = {};
        }
        return;
    }

    if (!g_local_multiplayer_two_player_visit) {
        g_local_multiplayer_two_player_visit = true;
        if (g_local_multiplayer_participants_ready) {
            // A confirmed session may revisit this stock menu while remaining
            // the same local multiplayer session. Do not erase identity or
            // reopen the Modern join/profile surface.
            return;
        }
        g_local_multiplayer_setup = {};
        g_local_multiplayer_participants = {};
        g_local_multiplayer_participants_ready = false;
        ensure_profile_catalog();
        const bool has_controller_source = std::any_of(
            g_local_multiplayer_sources.begin(),
            g_local_multiplayer_sources.end(),
            [](const ur::product::LocalInputSource& source) {
                return source.connected;
            });
        g_local_multiplayer_join_visible =
            has_controller_source && !g_profile_catalog.empty();
        if (g_local_multiplayer_join_visible) {
            product_diagnostic("UR_LOCAL_MULTIPLAYER JOIN_OPENED");
        } else if (g_profile_catalog.empty()) {
            product_diagnostic(
                "UR_LOCAL_MULTIPLAYER STOCK_FALLBACK_NO_PROFILES");
        } else {
            product_diagnostic(
                "UR_LOCAL_MULTIPLAYER STOCK_FALLBACK_NO_CONTROLLER");
        }
    }
}

bool local_multiplayer_refresh_ready() {
    const bool ready = ur::product::local_multiplayer_participants_ready(
        g_local_multiplayer_setup,
        g_local_multiplayer_participants);
    g_local_multiplayer_participants_ready = ready;
    if (ready) {
        g_local_multiplayer_join_visible = false;
        product_diagnostic("UR_LOCAL_MULTIPLAYER SESSION_READY");
    }
    return ready;
}

bool local_multiplayer_assign_source(
    ur::product::LocalMultiplayerSlot slot,
    ur::product::LocalInputSource source) {
    const auto result =
        ur::product::local_multiplayer_assign(
            g_local_multiplayer_setup, slot, source);
    if (!result.applied()) return false;
    g_local_multiplayer_setup = result.state;
    return true;
}

bool local_multiplayer_confirm_profile(
    ur::product::LocalMultiplayerSlot slot) {
    ensure_profile_catalog();
    const auto* candidate =
        ur::product::local_multiplayer_profile_candidate(
            g_local_multiplayer_participants,
            g_profile_catalog,
            slot);
    if (!candidate) return false;
    const auto selected = ur::product::local_multiplayer_select_profile(
        g_local_multiplayer_participants,
        g_local_multiplayer_setup,
        slot,
        *candidate);
    if (!selected.applied()) {
        if (selected.status ==
            ur::product::LocalMultiplayerParticipantStatus::DuplicateProfile) {
            product_diagnostic(
                "UR_LOCAL_MULTIPLAYER PROFILE_DUPLICATE");
        }
        return false;
    }
    g_local_multiplayer_participants = selected.state;
    (void)local_multiplayer_refresh_ready();
    return true;
}

void local_multiplayer_move_profile(
    ur::product::LocalMultiplayerSlot slot,
    int delta) {
    ensure_profile_catalog();
    const auto moved =
        ur::product::local_multiplayer_move_profile_cursor(
            g_local_multiplayer_participants,
            g_profile_catalog,
            slot,
            delta);
    if (moved.applied()) {
        g_local_multiplayer_participants = moved.state;
    }
}

void maybe_run_multiplayer_match_acceptance() {
    if (g_multiplayer_match_acceptance_seeded ||
        !std::getenv("UR_MULTIPLAYER_MATCH_ACCEPTANCE") ||
        !modern_mode() || !g_ram ||
        g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0x3D) {
        return;
    }

    // Acceptance owns a process-local deterministic participant catalog.
    // Do not depend on whichever user/default catalog happens to be present,
    // and do not persist these synthetic acceptance identities.
    g_profile_catalog = {
        {"accept-p1", {"MIKE", 0}},
        {"accept-p2", {"ANDREW", 1}},
    };
    product_diagnostic(
        "UR_MULTIPLAYER_MATCH ACCEPTANCE_PROFILES_SEEDED");

    const auto p1_slot = ur::product::LocalMultiplayerSlot::Player1;
    const auto p2_slot = ur::product::LocalMultiplayerSlot::Player2;
    const bool p1_joined = local_multiplayer_assign_source(
        p1_slot,
        {ur::product::LocalInputKind::Keyboard, 1u, true});
    const bool p2_joined = local_multiplayer_assign_source(
        p2_slot,
        {ur::product::LocalInputKind::Controller, 2u, true});
    const bool p1_profile =
        p1_joined && local_multiplayer_confirm_profile(p1_slot);
    local_multiplayer_move_profile(p2_slot, 1);
    const bool p2_profile =
        p2_joined && local_multiplayer_confirm_profile(p2_slot);

    if (!p1_profile || !p2_profile ||
        !g_local_multiplayer_participants_ready) {
        product_diagnostic(
            "UR_MULTIPLAYER_MATCH ACCEPTANCE_PROFILE_REJECTED");
        return;
    }

    g_multiplayer_match_acceptance_seeded = true;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_MULTIPLAYER_MATCH ACCEPTANCE_READY p1=%s p2=%s\n",
            g_local_multiplayer_participants.player1->profile_id.c_str(),
            g_local_multiplayer_participants.player2->profile_id.c_str());
        std::fflush(stderr);
    }
}

void observe_regional_title_surface() {
    const bool current = current_regional_secret_context().idle_title_surface;
    if (g_regional_input && g_regional_title_surface_previous && !current) {
        g_regional_input->reset();
        product_diagnostic("UR_REGIONAL MATCHER_RESET_TITLE_EXIT");
    }
    g_regional_title_surface_previous = current;
}

void apply_profile_save_root() {
    ensure_product_state();

    const char* override_root = std::getenv("UR_PROFILE_SAVE_ROOT");
    const auto decision = ur::product::resolve_host_profile_save_root(
        modern_mode() ? ur::product::ExecutionMode::Modern
                      : ur::product::ExecutionMode::Authentic,
        g_product_state.active_profile_id,
        override_root ? std::string_view(override_root) : std::string_view{});

    if (decision.status == ur::product::HostProfileSaveRootStatus::Rejected) {
        RtlSetSaveRoot(nullptr);
        product_diagnostic("UR_PROFILE_SAVE_ROOT REJECTED_DEFAULT");
        return;
    }

    if (!decision.isolated()) {
        RtlSetSaveRoot(nullptr);
        if (modern_mode()) {
            product_diagnostic("UR_PROFILE_SAVE_ROOT NO_PROFILE_DEFAULT root=saves");
        } else {
            product_diagnostic("UR_PROFILE_SAVE_ROOT AUTHENTIC_DEFAULT root=saves");
        }
        return;
    }

    RtlSetSaveRoot(decision.save_root.c_str());
    RtlEnsureSaveDir();

    g_profile_state_path = std::string(RtlSaveRoot()) + "/host-profile.txt";
    const auto resolved = ur::product::resolve_host_profile_state_file(
        ur::product::ExecutionMode::Modern,
        g_profile_state_path,
        *g_product_state.active_profile_id);
    if (resolved) {
        g_profile_state = *resolved.state;
        g_profile_state_writable =
            ur::product::host_profile_resolve_writable(resolved.status);
        if (!g_profile_state_writable) {
            product_diagnostic(
                resolved.status ==
                        ur::product::HostProfileResolveStatus::DefaultedMissing
                    ? "UR_PROFILE_STATE MISSING_READ_ONLY"
                    : "UR_PROFILE_STATE MALFORMED_READ_ONLY");
        } else {
            // Identity-less v1-v3 profiles are a valid historical
            // migration state and retain their progression/resume behavior.
            // Once a profile claims a Modern racer identity, however, that
            // identity must be backed by the authoritative catalog and an
            // exact SRAM snapshot before it can affect the live product.
            if (g_profile_state->racer_identity) {
                ensure_profile_catalog();
                if (!ur::product::profile_catalog_authorizes_state(
                        g_profile_catalog, *g_profile_state)) {
                    g_profile_state.reset();
                    g_profile_state_writable = false;
                    product_diagnostic(
                        "UR_PROFILE_STATE REJECTED_NONAUTHORITATIVE");
                }
            } else {
                product_diagnostic(
                    "UR_PROFILE_STATE LEGACY_IDENTITYLESS");
            }
        }
    } else {
        g_profile_state.reset();
        g_profile_state_path.clear();
        g_profile_state_writable = false;
        product_diagnostic("UR_PROFILE_STATE LOAD_FAILED");
    }

    // A named profile's durable Recent Course becomes this process's Recent
    // Course for that profile. The codec has already rejected out-of-catalog
    // values, and the existing profile-key scoping keeps it off other profiles.
    if (g_profile_state && g_profile_state->recent_track) {
        g_recent_course_track_id = *g_profile_state->recent_track;
        g_recent_course_profile_key = g_profile_state->profile_id;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_FAST_NAV RECENT_RESTORED track=%u\n",
                static_cast<unsigned>(*g_profile_state->recent_track));
            std::fflush(stderr);
        }
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_PROFILE_SAVE_ROOT APPLIED profile=%s root=%s\n",
            g_product_state.active_profile_id
                ? g_product_state.active_profile_id->c_str() : "",
            RtlSaveRoot());
        std::fflush(stderr);
    }
}


const char* widescreen_mode_name(ur::product::HostWidescreenMode mode) {
    return mode == ur::product::HostWidescreenMode::Authentic16x9
        ? "16x9" : "original";
}

void synchronize_widescreen_provider_selector() {
    // Explicit probe selectors own the guest-lane policy. Shipping Modern
    // presentation does not: its margins are materialized host-side and the
    // hook's hypothetical future strip must never mutate the stock VRAM ring.
    if (std::getenv("URRECOMP_WS_MARGIN")) return;
    const char* explicit_view = std::getenv("URRECOMP_WS_VIEW");
    if (explicit_view && *explicit_view) return;

    const bool enabled =
        g_product_state.settings.widescreen_mode ==
        ur::product::HostWidescreenMode::Authentic16x9;
#if defined(_WIN32)
    _putenv_s("URRECOMP_WS_GUEST_LANE", "0");
    _putenv_s("URRECOMP_WS_VIEW", enabled ? "authentic-16x9" : "");
#else
    setenv("URRECOMP_WS_GUEST_LANE", "0", 1);
    if (enabled) {
        setenv("URRECOMP_WS_VIEW", "authentic-16x9", 1);
    } else {
        unsetenv("URRECOMP_WS_VIEW");
    }
#endif
}

bool authentic_16x9_view_enabled() {
    if (!modern_mode()) return false;

    // Retain the environment selector as a deterministic diagnostic override.
    // Any non-empty unknown spelling fails closed instead of falling through
    // to persisted state.
    const char* view = std::getenv("URRECOMP_WS_VIEW");
    if (view && *view) {
        return std::strcmp(view, "authentic-16x9") == 0 ||
               std::strcmp(view, "authentic-16x9-candidate") == 0;
    }

    ensure_product_state();
    return g_product_state.settings.widescreen_mode ==
           ur::product::HostWidescreenMode::Authentic16x9;
}

void product_diagnostic(const char* message) {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS")) return;
    std::fprintf(stderr, "%s\n", message);
    std::fflush(stderr);
}

std::string product_user_data_root() {
    const char* override_root = std::getenv("UR_RECOMP_USER_DATA_ROOT");
    if (override_root && *override_root) {
        std::string root(override_root);
        while (!root.empty() && (root.back() == '/' || root.back() == '\\')) {
            root.pop_back();
        }
        return root;
    }

    char* pref_path = SDL_GetPrefPath("gamesbyian", "UR-Recomp");
    if (!pref_path) return {};
    std::string root(pref_path);
    SDL_free(pref_path);
    while (!root.empty() && (root.back() == '/' || root.back() == '\\')) {
        root.pop_back();
    }
    return root;
}

std::string product_user_data_path(const char* leaf) {
    std::string root = product_user_data_root();
    if (root.empty() || !leaf || !*leaf) return {};
    root += "/";
    root += leaf;
    return root;
}

std::string resolve_onboarding_seen_path() {
    const char* override_path = std::getenv("UR_ONBOARDING_STATE_PATH");
    if (override_path && *override_path) return override_path;

    return product_user_data_path("onboarding-v1.seen");
}

void ensure_onboarding_state() {
    if (g_onboarding_initialized) return;
    g_onboarding_initialized = true;
    if (!modern_mode()) return;

    g_onboarding_seen_path = resolve_onboarding_seen_path();
    bool seen = false;
    if (!g_onboarding_seen_path.empty()) {
        std::ifstream in(g_onboarding_seen_path, std::ios::binary);
        seen = in.good();
    }

    // Existing Modern installations predate onboarding. Treat an existing
    // product-state file as an already-established install unless acceptance
    // explicitly supplies a dedicated onboarding marker path. This keeps the
    // first-run overlay from contaminating deterministic regression captures
    // or surprising upgraded users, while a genuinely fresh install still
    // receives the explanation.
    const char* onboarding_override = std::getenv("UR_ONBOARDING_STATE_PATH");
    if (!seen && !(onboarding_override && *onboarding_override) &&
        !g_product_state_path.empty()) {
        std::ifstream product_state(g_product_state_path, std::ios::binary);
        seen = product_state.good();
    }

    g_onboarding_visible = !seen;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_ONBOARDING %s first_run=%d\n",
            g_onboarding_visible ? "SHOWN" : "HIDDEN",
            g_onboarding_visible ? 1 : 0);
        std::fflush(stderr);
    }
}

bool dismiss_onboarding() {
    if (!modern_mode()) return false;
    g_onboarding_visible = false;
    g_onboarding_manual_open = false;
    if (g_onboarding_seen_path.empty()) {
        g_onboarding_seen_path = resolve_onboarding_seen_path();
    }
    if (!g_onboarding_seen_path.empty()) {
        std::ofstream out(
            g_onboarding_seen_path,
            std::ios::binary | std::ios::trunc);
        if (!out) {
            product_diagnostic("UR_ONBOARDING DISMISS_SAVE_FAILED");
            return true;
        }
        out << "seen-v1\n";
        out.flush();
        if (!out) {
            product_diagnostic("UR_ONBOARDING DISMISS_SAVE_FAILED");
            return true;
        }
    }
    product_diagnostic("UR_ONBOARDING DISMISSED");
    return true;
}

bool onboarding_surface_active() {
    if (!modern_mode() || !g_onboarding_visible) return false;
    if (g_onboarding_manual_open) return true;
    return g_ram && g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7;
}

std::string live_gamepad_binding_label(int control_offset) {
    // Name the physical P1 pad button the live [GamepadMap] binds to this
    // SNES control (0..11, Up..R), reverse-looked-up through the framework's
    // own GamepadMap authority. The default map is positional, so SNES B
    // (jump) is the south button printed "A" -- never guess from the SNES
    // letter or the controller brand.
    return ur::product::modern_pad_glyph_for_control(
        control_offset, kKeys_Controls,
        [](int button) { return FindCmdForGamepadButton(button, 0); });
}

std::string resolve_practice_root() {
    const char* override_root = std::getenv("UR_PRACTICE_SAVE_ROOT");
    if (override_root && *override_root) return override_root;

    return product_user_data_path("practice-session");
}

std::string resolve_practice_input_path() {
    const char* override_path = std::getenv("UR_PRACTICE_INPUT_PATH");
    if (override_path && *override_path) return override_path;

    return product_user_data_path("practice-input.txt");
}

std::string resolve_tour_continue_input_path() {
    const char* override_path = std::getenv("UR_TOUR_CONTINUE_INPUT_PATH");
    if (override_path && *override_path) return override_path;

    return product_user_data_path("tour-continue-input.txt");
}

std::string resolve_profile_panel_acceptance_input_path() {
    const char* override_path =
        std::getenv("UR_PROFILE_PANEL_ACCEPTANCE_INPUT_PATH");
    if (override_path && *override_path) return override_path;

    return product_user_data_path("profile-panel-acceptance-input.txt");
}

bool queue_relative_menu_input(
    std::string& input_path,
    uint64_t origin_frame,
    std::uint16_t mask) {
    if (!ur::product::quick_practice_runner_mask_is_discrete_menu_input(mask) ||
        input_path.empty()) {
        return false;
    }

    {
        std::ofstream out(
            input_path,
            std::ios::binary | std::ios::trunc);
        if (!out) return false;
        char encoded[32];
        std::snprintf(
            encoded, sizeof(encoded), "0:2:%X\n",
            static_cast<unsigned>(mask));
        out << encoded;
        out.flush();
        if (!out) return false;
    }

    if (!snesrecomp_desktop_load_relative_input_file(input_path.c_str())) {
        return false;
    }
    snesrecomp_desktop_arm_relative_input(origin_frame);
    return true;
}

bool queue_tour_continue_input(
    ur::product::QuickPracticeMenuInput input,
    uint64_t origin_frame) {
    const std::uint16_t mask = ur::product::quick_practice_runner_mask(
        ur::product::launch_input_from_menu_input(input));
    if (mask == 0) return input == ur::product::QuickPracticeMenuInput::None;

    if (g_tour_continue_input_path.empty()) {
        g_tour_continue_input_path = resolve_tour_continue_input_path();
    }
    return queue_relative_menu_input(
        g_tour_continue_input_path,
        origin_frame,
        mask);
}

bool queue_practice_input(
    uint64_t origin_frame,
    ur::product::QuickPracticeLaunchInput input) {
    if (!g_practice_active) return false;
    if (g_practice_input_path.empty()) {
        g_practice_input_path = resolve_practice_input_path();
    }
    return queue_relative_menu_input(
        g_practice_input_path,
        origin_frame,
        ur::product::quick_practice_runner_mask(input));
}

bool begin_practice(std::uint8_t track_id = 0) {
    const auto target = ur::product::quick_practice_target_for_track(track_id);
    if (!target.valid || !modern_mode() || g_practice_active || paused() ||
        g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7 || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    g_practice_sram_snapshot.assign(
        g_sram,
        g_sram + static_cast<std::size_t>(g_sram_size));
    const char* root = RtlSaveRoot();
    g_practice_original_save_root = root ? root : "";

    const std::string practice_root = resolve_practice_root();
    if (practice_root.empty()) {
        g_practice_sram_snapshot.clear();
        return false;
    }
    RtlSetSaveRoot(practice_root.c_str());
    RtlEnsureSaveDir();

    g_practice_active = true;
    g_practice_race_ready_reported = false;
    g_practice_cancel_gamepad_button = -1;
    g_practice_launch = ur::product::begin_quick_practice_launch(target);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_PRACTICE STARTED sram=%08X root=%s track=%u\n",
            static_cast<unsigned>(current_sram_digest()),
            RtlSaveRoot(),
            static_cast<unsigned>(track_id));
        std::fflush(stderr);
    }
    return true;
}

bool restore_practice_profile_before_reboot() {
    if (!g_practice_active) return true;
    if (!g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes) ||
        g_practice_sram_snapshot.size() != ur::product::kStockSramBytes) {
        product_diagnostic("UR_PRACTICE RESTORE_FAILED");
        return false;
    }

    std::memcpy(
        g_sram,
        g_practice_sram_snapshot.data(),
        ur::product::kStockSramBytes);
    RtlSetSaveRoot(
        g_practice_original_save_root.empty()
            ? nullptr
            : g_practice_original_save_root.c_str());

    g_practice_active = false;
    g_practice_race_ready_reported = false;
    g_practice_launch = {};
    g_practice_sram_snapshot.clear();
    g_practice_original_save_root.clear();
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_PRACTICE RESTORED sram=%08X root=%s\n",
            static_cast<unsigned>(current_sram_digest()),
            RtlSaveRoot());
        std::fflush(stderr);
    }
    return true;
}

int authoritative_active_track_id() {
    if (!g_ram || g_ram[0x0313] != 0x01) return -1;
    const UrUniracersCourseIdentity course =
        ur_uniracers_identify_course(g_ram + 0x10000u, 0x10000u);
    if (!course.valid || course.course_index < 1 || course.course_index > 45) {
        return -1;
    }
    return course.course_index - 1;
}

void advance_practice_route(uint64_t next_frame) {
    if (!g_practice_active) return;

    const int active_track_id = authoritative_active_track_id();
    const auto launch_before = g_practice_launch;
    const auto step = ur::product::advance_quick_practice_launch(
        g_practice_launch,
        ur::product::QuickPracticeLaunchObservation{
            g_ram[0x009F],
            g_ram[0x009B],
            g_ram[0x0313] == 0x01,
            active_track_id,
        });
    const auto expected_track_id = launch_before.target.track_id;
    const auto retry_state =
        ur::product::quick_practice_launch_retry_state(launch_before);
    g_practice_launch = step.state;

    if (step.timed_out) {
        // Preserve the timed-out routing state until the reboot request is
        // accepted. If the request fails transactionally, the next host frame
        // retries the same fail-closed abort rather than releasing guest input.
        g_practice_launch = retry_state;
        if (!abort_practice_route_to_frontend("UR_PRACTICE ROUTE_TIMEOUT")) {
            product_diagnostic("UR_PRACTICE ROUTE_TIMEOUT_EXIT_RETRY");
        }
        return;
    }

    if (step.route_violation || step.course_mismatch) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                step.route_violation
                    ? "UR_PRACTICE ROUTE_VIOLATION expected=%u actual=%d stage_bypassed=1\n"
                    : "UR_PRACTICE COURSE_MISMATCH expected=%u actual=%d\n",
                static_cast<unsigned>(expected_track_id),
                active_track_id);
            std::fflush(stderr);
        }
        // A target-aware Practice launch must never silently bless an attract
        // race, bypassed frontend route, or different stock course.
        g_practice_launch = retry_state;
        if (!abort_practice_route_to_frontend(
                step.route_violation
                    ? "UR_PRACTICE ROUTE_VIOLATION_ABORTED"
                    : "UR_PRACTICE COURSE_MISMATCH_ABORTED")) {
            product_diagnostic(
                step.route_violation
                    ? "UR_PRACTICE ROUTE_VIOLATION_EXIT_RETRY"
                    : "UR_PRACTICE COURSE_MISMATCH_EXIT_RETRY");
        }
        return;
    }

    if (step.race_ready) {
        if (!g_practice_race_ready_reported) {
            g_practice_race_ready_reported = true;
            product_diagnostic("UR_PRACTICE RACE_READY");
        }
        return;
    }
    if (step.input == ur::product::QuickPracticeLaunchInput::None) {
        return;
    }
    const auto stage_before = g_practice_launch.stage;
    if (!queue_practice_input(next_frame, step.input)) {
        // The state machine advances when it *requests* an input. If transport
        // fails, restore the prior state so the same semantic input is retried
        // instead of pretending the stock menu consumed an edge it never saw.
        g_practice_launch = retry_state;
        product_diagnostic("UR_PRACTICE INPUT_FAILED");
        return;
    }
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        const char* compatibility_stage =
            stage_before == ur::product::QuickPracticeLaunchStage::AwaitRider
                ? "main"
                : nullptr;
        if (compatibility_stage) {
            std::fprintf(
                stderr, "UR_PRACTICE ACCEPT stage=%s\n",
                compatibility_stage);
        }
        std::fprintf(
            stderr,
            "UR_PRACTICE INPUT stage=%u input=%u selected=%u\n",
            static_cast<unsigned>(g_practice_launch.stage),
            static_cast<unsigned>(step.input),
            static_cast<unsigned>(g_ram[0x009B]));
        std::fflush(stderr);
    }
}

std::string active_profile_key() {
    ensure_product_state();
    return g_product_state.active_profile_id
        ? *g_product_state.active_profile_id
        : std::string{};
}

bool recent_course_available_for_active_profile() {
    return g_recent_course_track_id &&
           g_recent_course_profile_key == active_profile_key();
}

bool practice_routing() {
    return g_practice_active &&
           ur::product::quick_practice_launch_owns_player_input(
               g_practice_launch);
}

// Recent Course is navigation metadata on the active named profile. Persist it
// without touching progression: re-save the in-memory profile (which mirrors
// the durable file, including its exact SRAM snapshot and generation) with
// only recent_track changed. Live and Practice SRAM are never captured here.
void persist_recent_course_for_active_profile(std::uint8_t track_id) {
    if (!modern_mode() || !g_profile_state || !g_profile_state_writable ||
        g_profile_state_path.empty() ||
        g_profile_state->profile_id != active_profile_key() ||
        !ur::product::valid_recent_track(track_id) ||
        g_profile_state->recent_track == track_id) {
        return;
    }
    auto candidate = *g_profile_state;
    candidate.recent_track = track_id;
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        // The in-memory recent still works for this process; the durable
        // profile keeps its previous value.
        product_diagnostic("UR_FAST_NAV RECENT_PERSIST_FAILED");
        return;
    }
    g_profile_state = std::move(candidate);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_FAST_NAV RECENT_PERSISTED track=%u generation=%llu\n",
            static_cast<unsigned>(track_id),
            static_cast<unsigned long long>(
                g_profile_state->autosave_generation));
        std::fflush(stderr);
    }
}

void observe_recent_course_identity() {
    if (!modern_mode()) return;
    g_recent_course_origin = ur::product::observe_recent_course_origin(
        g_recent_course_origin, g_ram[0x0313], g_ram[0x009F]);
    // The idle attract demo is a validated live course the player never
    // chose; it must not replace the profile's Recent Course.
    if (!ur::product::recent_course_origin_admits(g_recent_course_origin)) {
        if (g_ram[0x0313] == 0x01 && !g_recent_course_attract_reported) {
            g_recent_course_attract_reported = true;
            product_diagnostic("UR_FAST_NAV RECENT_IGNORED_ATTRACT");
        }
        return;
    }
    g_recent_course_attract_reported = false;
    // During Practice launch, do not let an attract/demo or wrong-course race
    // poison Recent Course before the target-aware router has validated it.
    if (g_practice_active &&
        g_practice_launch.stage !=
            ur::product::QuickPracticeLaunchStage::Active) {
        return;
    }
    const int active_track_id = authoritative_active_track_id();
    if (active_track_id < 0 || active_track_id >= 45) return;

    const auto track_id =
        static_cast<std::uint8_t>(active_track_id);
    const std::string profile_key = active_profile_key();
    const bool changed =
        !g_recent_course_track_id ||
        *g_recent_course_track_id != track_id ||
        g_recent_course_profile_key != profile_key;

    g_recent_course_track_id = track_id;
    g_recent_course_profile_key = profile_key;
    if (changed && std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_FAST_NAV RECENT_OBSERVED track=%u profile_context=%s\n",
            static_cast<unsigned>(track_id),
            profile_key.empty() ? "none" : "named");
        std::fflush(stderr);
    }
    if (!profile_key.empty()) {
        persist_recent_course_for_active_profile(track_id);
    }
}

ur::product::FastNavigationContext fast_navigation_context() {
    return {
        modern_mode(),
        restart_surface(),
        g_session && ur_modern_session_restart_available(g_session),
        g_ram && g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7,
        g_practice_active,
        g_recent_course_track_id.has_value(),
        recent_course_available_for_active_profile(),
    };
}

bool repeat_current_attempt() {
    if (ur::product::resolve_fast_navigation(
            ur::product::FastNavigationCommand::RepeatAttempt,
            fast_navigation_context()) !=
        ur::product::FastNavigationAction::RestartAttempt) {
        return false;
    }

    // Capture the completed/current attempt before Restart mutates volatile
    // race state. The accepted Restart loader preserves current SRAM, so the
    // subsequent active-race observation can prove that persistence boundary
    // rather than merely comparing two post-restart samples.
    const uint32_t sram_before = current_sram_digest();
    const auto course_before = g_recent_course_track_id;

    const bool handled = dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY);
    if (handled) {
        g_fast_repeat_sram_before = sram_before;
        g_fast_repeat_course_before = course_before;
        rearm_run_capture_after_retry();
        product_diagnostic(
            g_practice_active
                ? "UR_FAST_NAV REPEAT_PRACTICE"
                : "UR_FAST_NAV REMATCH");
    }
    return handled;
}

bool launch_recent_course_practice() {
    if (ur::product::resolve_fast_navigation(
            ur::product::FastNavigationCommand::RecentCourse,
            fast_navigation_context()) !=
        ur::product::FastNavigationAction::LaunchRecentPractice ||
        !recent_course_available_for_active_profile() ||
        !g_recent_course_track_id) {
        return false;
    }
    const std::uint8_t track_id = *g_recent_course_track_id;
    if (!begin_practice(track_id)) return false;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_FAST_NAV RECENT_PRACTICE track=%u\n",
            static_cast<unsigned>(track_id));
        std::fflush(stderr);
    }
    return true;
}

const char* display_mode_name(ur::product::HostDisplayMode mode) {
    switch (mode) {
    case ur::product::HostDisplayMode::BorderlessFullscreen:
        return "borderless";
    case ur::product::HostDisplayMode::Fullscreen:
        return "fullscreen";
    case ur::product::HostDisplayMode::Windowed:
    default:
        return "windowed";
    }
}

int display_mode_value(ur::product::HostDisplayMode mode) {
    switch (mode) {
    case ur::product::HostDisplayMode::BorderlessFullscreen:
        return SNES_DESKTOP_DISPLAY_BORDERLESS;
    case ur::product::HostDisplayMode::Fullscreen:
        return SNES_DESKTOP_DISPLAY_FULLSCREEN;
    case ur::product::HostDisplayMode::Windowed:
    default:
        return SNES_DESKTOP_DISPLAY_WINDOWED;
    }
}

const char* vsync_mode_name(ur::product::HostVSyncMode mode) {
    switch (mode) {
    case ur::product::HostVSyncMode::Off:
        return "off";
    case ur::product::HostVSyncMode::Adaptive:
        return "adaptive";
    case ur::product::HostVSyncMode::On:
    default:
        return "on";
    }
}

int vsync_mode_value(ur::product::HostVSyncMode mode) {
    switch (mode) {
    case ur::product::HostVSyncMode::Off:
        return SNES_DESKTOP_VSYNC_OFF;
    case ur::product::HostVSyncMode::Adaptive:
        return SNES_DESKTOP_VSYNC_ADAPTIVE;
    case ur::product::HostVSyncMode::On:
    default:
        return SNES_DESKTOP_VSYNC_ON;
    }
}

const char* presentation_fps_mode_name(
    ur::product::HostPresentationFpsMode mode) {
    switch (mode) {
    case ur::product::HostPresentationFpsMode::Fps60:
        return "60";
    case ur::product::HostPresentationFpsMode::Fps90:
        return "90";
    case ur::product::HostPresentationFpsMode::Fps120:
        return "120";
    case ur::product::HostPresentationFpsMode::Fps144:
        return "144";
    case ur::product::HostPresentationFpsMode::Native:
        return "native";
    case ur::product::HostPresentationFpsMode::Game:
    default:
        return "game";
    }
}

double presentation_fps_target(
    ur::product::HostPresentationFpsMode mode,
    double display_refresh) {
    switch (mode) {
    case ur::product::HostPresentationFpsMode::Fps60:
        return 60.0;
    case ur::product::HostPresentationFpsMode::Fps90:
        return 90.0;
    case ur::product::HostPresentationFpsMode::Fps120:
        return 120.0;
    case ur::product::HostPresentationFpsMode::Fps144:
        return 144.0;
    case ur::product::HostPresentationFpsMode::Native:
        return display_refresh > 0.0 ? display_refresh : 60.0;
    case ur::product::HostPresentationFpsMode::Game:
    default:
        return 0.0;
    }
}

bool apply_vsync_setting(const ur::product::HostSettings& settings) {
    if (!modern_mode()) return false;
    if (!snesrecomp_desktop_set_vsync(vsync_mode_value(settings.vsync_mode))) {
        product_diagnostic("UR_VSYNC APPLY_FAILED");
        return false;
    }
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_VSYNC APPLIED mode=%s host=%d\n",
            vsync_mode_name(settings.vsync_mode),
            snesrecomp_desktop_get_vsync());
        std::fflush(stderr);
    }
    return true;
}

bool apply_presentation_fps_setting(
    const ur::product::HostSettings& settings) {
    if (!modern_mode()) return false;

    g_live_presentation_fps_mode = settings.presentation_fps_mode;
    snesrecomp_desktop_request_clock_reset();

    // A decoupled presentation clock must own pacing rather than blocking in
    // the driver. Re-applying the semantic VSync setting lets SNESRecomp's
    // VSyncInterval() select the correct live swap interval for this mode.
    if (!snesrecomp_desktop_set_vsync(vsync_mode_value(settings.vsync_mode))) {
        product_diagnostic("UR_PRESENTATION_FPS APPLY_FAILED");
        return false;
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_PRESENTATION_FPS APPLIED mode=%s target=%.0f decoupled=%d\n",
            presentation_fps_mode_name(settings.presentation_fps_mode),
            presentation_fps_target(settings.presentation_fps_mode, 0.0),
            settings.presentation_fps_mode ==
                    ur::product::HostPresentationFpsMode::Game
                ? 0 : 1);
        std::fflush(stderr);
    }
    return true;
}

bool apply_display_mode_setting(const ur::product::HostSettings& settings) {
    if (!modern_mode()) return false;
    if (!snesrecomp_desktop_set_display_mode(
            display_mode_value(settings.display_mode))) {
        product_diagnostic("UR_DISPLAY_MODE APPLY_FAILED");
        return false;
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_DISPLAY_MODE APPLIED mode=%s host=%d\n",
            display_mode_name(settings.display_mode),
            snesrecomp_desktop_get_display_mode());
        std::fflush(stderr);
    }
    return true;
}

ur::product::HostOutputMode product_output_mode(
    const SnesDesktopOutputMode& mode) {
    return {mode.width, mode.height, mode.refresh_millihz};
}

SnesDesktopOutputMode desktop_output_mode(
    const ur::product::HostOutputMode& mode) {
    return {mode.width, mode.height, mode.refresh_millihz};
}

std::vector<ur::product::HostOutputMode> active_output_modes() {
    std::vector<ur::product::HostOutputMode> modes;
    const int count = snesrecomp_desktop_output_mode_count();
    if (count <= 0) return modes;
    modes.reserve(static_cast<std::size_t>(count));
    for (int index = 0; index < count; ++index) {
        SnesDesktopOutputMode mode{};
        if (snesrecomp_desktop_get_output_mode(index, &mode)) {
            modes.push_back(product_output_mode(mode));
        }
    }
    return modes;
}

bool active_native_output_mode(ur::product::HostOutputMode& out) {
    SnesDesktopOutputMode mode{};
    if (!snesrecomp_desktop_get_native_output_mode(&mode)) {
        return false;
    }
    out = product_output_mode(mode);
    return ur::product::valid_output_mode(out);
}

bool apply_concrete_output_mode(
    void*,
    const ur::product::HostOutputMode& mode) {
    const SnesDesktopOutputMode host_mode = desktop_output_mode(mode);
    return snesrecomp_desktop_set_output_mode(&host_mode) != 0;
}

const char* output_resolution_status_name(
    ur::product::OutputResolutionApplyStatus status) {
    switch (status) {
    case ur::product::OutputResolutionApplyStatus::NotApplicable:
        return "not-applicable";
    case ur::product::OutputResolutionApplyStatus::Applied:
        return "applied";
    case ur::product::OutputResolutionApplyStatus::Unsupported:
        return "unsupported";
    case ur::product::OutputResolutionApplyStatus::HostRejected:
        return "host-rejected";
    }
    return "unknown";
}

std::string output_resolution_name(
    const ur::product::HostOutputResolution& resolution) {
    if (resolution.kind == ur::product::HostOutputResolutionKind::Native) {
        return "native";
    }
    return std::to_string(resolution.width) + "x" +
           std::to_string(resolution.height);
}

bool apply_output_resolution_setting(
    const ur::product::HostSettings& settings) {
    if (!modern_mode()) return false;
    if (settings.display_mode != ur::product::HostDisplayMode::Fullscreen) {
        return true;
    }

    const auto modes = active_output_modes();
    const auto choices = ur::product::build_output_resolution_choices(modes);
    const auto effective = ur::product::select_supported_output_resolution(
        settings.output_resolution, choices);
    ur::product::HostOutputMode native_mode{};
    if (!active_native_output_mode(native_mode)) {
        product_diagnostic("UR_OUTPUT_RESOLUTION NATIVE_MODE_UNAVAILABLE");
        return false;
    }

    const auto result = ur::product::apply_output_resolution_policy(
        settings.display_mode,
        effective,
        modes,
        native_mode,
        &apply_concrete_output_mode,
        nullptr);
    if (!result) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_OUTPUT_RESOLUTION APPLY_FAILED requested=%s effective=%s status=%s\n",
                output_resolution_name(settings.output_resolution).c_str(),
                output_resolution_name(effective).c_str(),
                output_resolution_status_name(result.status));
            std::fflush(stderr);
        }
        return false;
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_OUTPUT_RESOLUTION APPLIED requested=%s effective=%s status=%s mode=%dx%d@%d\n",
            output_resolution_name(settings.output_resolution).c_str(),
            output_resolution_name(effective).c_str(),
            output_resolution_status_name(result.status),
            result.selected_mode ? result.selected_mode->width : 0,
            result.selected_mode ? result.selected_mode->height : 0,
            result.selected_mode ? result.selected_mode->refresh_millihz : 0);
        std::fflush(stderr);
    }
    return true;
}

std::string resolve_product_state_path() {
    const char* override_path = std::getenv("UR_HOST_STATE_PATH");
    if (override_path && *override_path) {
        return override_path;
    }

    return product_user_data_path("host-state-v1.txt");
}

void ensure_product_state() {
    if (g_product_state_initialized) return;
    g_product_state_initialized = true;

    if (!modern_mode()) {
        product_diagnostic("UR_HOST_STATE AUTHENTIC_INERT");
        return;
    }

    g_product_state_path = resolve_product_state_path();
    if (g_product_state_path.empty()) {
        product_diagnostic("UR_HOST_STATE PATH_UNAVAILABLE");
        return;
    }

    const auto loaded =
        ur::product::load_host_product_state_file(g_product_state_path);
    if (loaded.loaded()) {
        g_product_state = *loaded.state;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_HOST_STATE LOADED regional_presentation=%s pause_on_focus_loss=%d display_mode=%s vsync=%s presentation_fps=%s output_resolution=%s widescreen=%s internal_render_scale=%dx\n",
                regional_presentation_name(
                    g_product_state.regional_presentation),
                g_product_state.settings.pause_on_focus_loss ? 1 : 0,
                display_mode_name(g_product_state.settings.display_mode),
                vsync_mode_name(g_product_state.settings.vsync_mode),
                presentation_fps_mode_name(
                    g_product_state.settings.presentation_fps_mode),
                output_resolution_name(
                    g_product_state.settings.output_resolution).c_str(),
                widescreen_mode_name(
                    g_product_state.settings.widescreen_mode),
                ur::product::internal_render_scale_value(
                    g_product_state.settings.internal_render_scale));
            std::fflush(stderr);
        }
    } else if (loaded.status == ur::product::HostProductLoadStatus::Missing) {
        product_diagnostic("UR_HOST_STATE MISSING_DEFAULTS");
    } else if (loaded.status == ur::product::HostProductLoadStatus::Rejected) {
        product_diagnostic("UR_HOST_STATE REJECTED_DEFAULTS");
    } else {
        product_diagnostic("UR_HOST_STATE IO_ERROR_DEFAULTS");
    }

    synchronize_widescreen_provider_selector();
    g_live_presentation_fps_mode =
        g_product_state.settings.presentation_fps_mode;
}

bool persist_product_state(const ur::product::HostProductState& candidate) {
    if (!modern_mode() || g_product_state_path.empty()) {
        return false;
    }
    const auto status = ur::product::save_host_product_state_file(
        g_product_state_path, candidate);
    if (status != ur::product::HostProductSaveStatus::Saved) {
        product_diagnostic("UR_HOST_STATE SAVE_FAILED");
        return false;
    }
    product_diagnostic("UR_HOST_STATE SAVED");
    return true;
}


std::string profile_catalog_path() {
    if (!g_profile_catalog_path.empty()) return g_profile_catalog_path;
    g_profile_catalog_path = product_user_data_path("profiles-v1.txt");
    return g_profile_catalog_path;
}

void ensure_profile_catalog() {
    if (!g_profile_catalog.empty()) return;
    const std::string path = profile_catalog_path();
    if (path.empty()) return;
    const auto loaded = ur::product::load_host_profile_catalog_file(path);
    if (loaded) g_profile_catalog = *loaded;
}

bool persist_profile_catalog() {
    const std::string path = profile_catalog_path();
    return !path.empty() &&
        ur::product::save_host_profile_catalog_file(path, g_profile_catalog);
}

std::string profile_state_path_for(std::string_view profile_id) {
    const auto root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern,
        std::optional<std::string>{std::string(profile_id)});
    if (!root.isolated()) return {};
    return root.save_root + "/host-profile.txt";
}

bool persist_live_profile_snapshot() {
    if (!modern_mode() || !g_profile_state || !g_profile_state_writable ||
        g_profile_state_path.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return true;
    }
    auto candidate = *g_profile_state;
    if (ur::product::capture_stock_sram_for_profile(
            ur::product::ExecutionMode::Modern,
            candidate,
            g_sram,
            static_cast<std::size_t>(g_sram_size)) !=
        ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        return false;
    }
    g_profile_state = std::move(candidate);
    return RtlTryWriteSram();
}

bool activate_profile_id(const std::string& profile_id) {
    if (!modern_mode() || !ur::product::is_valid_profile_id(profile_id)) {
        return false;
    }
    ensure_profile_catalog();
    const std::string target_path = profile_state_path_for(profile_id);
    const auto target = ur::product::load_host_profile_state_file(
        ur::product::ExecutionMode::Modern, target_path, profile_id);
    if (!target.loaded() ||
        !ur::product::profile_catalog_authorizes_state(
            g_profile_catalog, *target.state)) {
        product_diagnostic("UR_PROFILE_SELECT REJECTED_METADATA");
        return false;
    }
    if (!persist_live_profile_snapshot()) return false;

    auto product = g_product_state;
    product.active_profile_id = profile_id;
    if (!persist_product_state(product)) return false;
    g_product_state = product;
    apply_profile_save_root();
    if (!g_profile_state || !g_profile_state->racer_identity ||
        !g_profile_state->stock_sram || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    if (ur::product::restore_stock_sram_from_profile(
            ur::product::ExecutionMode::Modern,
            *g_profile_state,
            g_sram,
            static_cast<std::size_t>(g_sram_size)) !=
        ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }
    g_sram[0x0748] = g_profile_state->racer_identity->rider_index;
    (void)RtlTryWriteSram();
    product_diagnostic("UR_PROFILE_SELECT APPLIED");
    return true;
}

bool create_profile_from_editor() {
    if (!ur::product::valid_racer_name(g_profile_edit_name) ||
        g_profile_preset_index >= ur::product::legacy_racer_presets().size()) {
        return false;
    }
    ensure_profile_catalog();
    const auto& preset =
        ur::product::legacy_racer_presets()[g_profile_preset_index];

    // A pre-catalog active profile still owns its opaque storage id even if
    // it has no Modern identity entry yet. Reserve that id so creating a new
    // racer can never silently adopt the legacy profile's namespace.
    auto occupied_profiles = g_profile_catalog;
    if (g_product_state.active_profile_id) {
        const bool already_catalogued = std::any_of(
            occupied_profiles.begin(),
            occupied_profiles.end(),
            [&](const ur::product::HostProfileCatalogEntry& entry) {
                return entry.profile_id == *g_product_state.active_profile_id;
            });
        if (!already_catalogued) {
            occupied_profiles.push_back({
                *g_product_state.active_profile_id,
                ur::product::HostRacerIdentity{
                    std::string(preset.name), preset.rider_index}});
        }
    }
    const std::string id =
        ur::product::make_profile_id(g_profile_edit_name, occupied_profiles);
    if (id.empty()) return false;

    auto state = ur::product::make_default_host_profile_state(id);
    if (!state || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }
    state->racer_identity =
        ur::product::HostRacerIdentity{
            g_profile_edit_name, preset.rider_index};
    // A new profile is a new progression owner, not a clone of whichever
    // profile happens to be active. Seed it from the exact stock clean SRAM
    // image, then let ordinary guest-authored progression diverge from there.
    const auto& clean_sram = ur::product::clean_stock_sram();
    if (ur::product::capture_stock_sram_for_profile(
            ur::product::ExecutionMode::Modern,
            *state,
            clean_sram.data(),
            clean_sram.size()) !=
        ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }

    const auto root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern,
        std::optional<std::string>{id});
    if (!root.isolated()) return false;
    std::error_code ec;
    const bool root_exists = std::filesystem::exists(root.save_root, ec);
    if (ec || root_exists) {
        product_diagnostic("UR_PROFILE_CREATE REJECTED_EXISTING_ROOT");
        return false;
    }
    std::filesystem::create_directories(root.save_root, ec);
    if (ec) return false;
    const std::string path = root.save_root + "/host-profile.txt";
    std::error_code exists_ec;
    if (std::filesystem::exists(path, exists_ec) || exists_ec) {
        product_diagnostic("UR_PROFILE_CREATE REJECTED_EXISTING_STATE");
        return false;
    }
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern, path, *state) !=
        ur::product::HostProfileSaveStatus::Saved) {
        return false;
    }

    g_profile_catalog.push_back({id, *state->racer_identity});
    if (!persist_profile_catalog()) {
        g_profile_catalog.pop_back();
        std::error_code remove_ec;
        (void)std::filesystem::remove(path, remove_ec);
        product_diagnostic("UR_PROFILE_CREATE ROLLED_BACK");
        return false;
    }
    g_profile_menu_index = g_profile_catalog.size() - 1;
    g_profile_cool_name_notice =
        ur::product::stock_forbidden_name_match(g_profile_edit_name);
    if (g_profile_cool_name_notice) {
        product_diagnostic("UR_PROFILE_UI COOL_NAME");
    }
    g_profile_edit_mode = ProfileEditMode::None;
    const bool activated = activate_profile_id(id);
    if (activated) product_diagnostic("UR_PROFILE_UI CREATED");
    return activated;
}

bool rename_profile_from_editor() {
    ensure_profile_catalog();
    if (g_profile_menu_index >= g_profile_catalog.size() ||
        !ur::product::valid_racer_name(g_profile_edit_name)) return false;
    auto& entry = g_profile_catalog[g_profile_menu_index];
    const std::string path = profile_state_path_for(entry.profile_id);
    const auto loaded = ur::product::load_host_profile_state_file(
        ur::product::ExecutionMode::Modern, path, entry.profile_id);
    if (!loaded.loaded() || !loaded.state->racer_identity ||
        !loaded.state->stock_sram ||
        !ur::product::catalog_entry_matches_profile_state(
            entry, *loaded.state)) {
        product_diagnostic("UR_PROFILE_RENAME REJECTED_METADATA");
        return false;
    }

    const auto original_state = *loaded.state;
    const auto original_identity = entry.identity;
    auto state = original_state;
    state.racer_identity->name = g_profile_edit_name;
    if (!ur::product::valid_racer_identity(*state.racer_identity)) return false;
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern, path, state) !=
        ur::product::HostProfileSaveStatus::Saved) return false;
    entry.identity = *state.racer_identity;
    if (!persist_profile_catalog()) {
        entry.identity = original_identity;
        const auto rollback = ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern, path, original_state);
        product_diagnostic(
            rollback == ur::product::HostProfileSaveStatus::Saved
                ? "UR_PROFILE_RENAME ROLLED_BACK"
                : "UR_PROFILE_RENAME ROLLBACK_FAILED");
        return false;
    }
    if (g_product_state.active_profile_id &&
        *g_product_state.active_profile_id == entry.profile_id) {
        g_profile_state = state;
    }
    g_profile_cool_name_notice =
        ur::product::stock_forbidden_name_match(g_profile_edit_name);
    if (g_profile_cool_name_notice) {
        product_diagnostic("UR_PROFILE_UI COOL_NAME");
    }
    g_profile_edit_mode = ProfileEditMode::None;
    product_diagnostic("UR_PROFILE_UI RENAMED");
    return true;
}

void open_profile_menu() {
    ensure_profile_catalog();
    g_profile_menu_visible = true;
    product_diagnostic("UR_PROFILE_UI OPENED");
    g_profile_edit_mode = ProfileEditMode::None;
    g_profile_cool_name_notice = false;
    g_profile_reset = {};
    g_profile_menu_index = 0;
    if (g_product_state.active_profile_id) {
        for (std::size_t i = 0; i < g_profile_catalog.size(); ++i) {
            if (g_profile_catalog[i].profile_id ==
                *g_product_state.active_profile_id) {
                g_profile_menu_index = i;
                break;
            }
        }
    }
}

void begin_profile_create() {
    g_profile_edit_mode = ProfileEditMode::Create;
    g_profile_preset_index = 0;
    g_profile_edit_name =
        std::string(ur::product::legacy_racer_presets()[0].name);
    g_profile_edit_pristine = true;
    g_profile_cool_name_notice = false;
}

void begin_profile_rename() {
    ensure_profile_catalog();
    if (g_profile_menu_index >= g_profile_catalog.size()) return;
    g_profile_edit_mode = ProfileEditMode::Rename;
    g_profile_edit_name = g_profile_catalog[g_profile_menu_index].identity.name;
    g_profile_edit_pristine = true;
    g_profile_cool_name_notice = false;
}

bool selected_profile_is_active() {
    return g_product_state.active_profile_id &&
           g_profile_menu_index < g_profile_catalog.size() &&
           g_profile_catalog[g_profile_menu_index].profile_id ==
               *g_product_state.active_profile_id;
}

bool active_profile_reset_authoritative() {
    return modern_mode() && g_profile_state && g_profile_state_writable &&
           !g_profile_state_path.empty() &&
           g_profile_state->racer_identity &&
           g_profile_state->stock_sram &&
           g_sram &&
           g_sram_size == static_cast<int>(ur::product::kStockSramBytes);
}

bool execute_active_profile_progress_reset() {
    if (!active_profile_reset_authoritative() ||
        !selected_profile_is_active()) {
        product_diagnostic("UR_PROFILE_RESET REJECTED_CONTEXT");
        return false;
    }

    auto reset_sram = ur::product::clean_stock_sram();
    reset_sram[0x0748] = g_profile_state->racer_identity->rider_index;

    auto candidate = *g_profile_state;
    candidate.tour_continuation.reset();
    if (ur::product::capture_stock_sram_for_profile(
            ur::product::ExecutionMode::Modern,
            candidate,
            reset_sram.data(),
            reset_sram.size()) !=
        ur::product::HostProfileTransferStatus::Applied) {
        product_diagnostic("UR_PROFILE_RESET REJECTED_SNAPSHOT");
        return false;
    }

    const auto original_state = *g_profile_state;
    std::array<std::uint8_t, ur::product::kStockSramBytes> original_sram{};
    std::memcpy(original_sram.data(), g_sram, original_sram.size());

    // Publish host metadata first. If the framework SRAM write then fails,
    // restore both the live bytes and the original host profile state.
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        product_diagnostic("UR_PROFILE_RESET PROFILE_SAVE_FAILED");
        return false;
    }

    std::memcpy(g_sram, reset_sram.data(), reset_sram.size());
    if (!RtlTryWriteSram()) {
        std::memcpy(g_sram, original_sram.data(), original_sram.size());
        const bool profile_rolled_back =
            ur::product::save_host_profile_state_file(
                ur::product::ExecutionMode::Modern,
                g_profile_state_path,
                original_state) == ur::product::HostProfileSaveStatus::Saved;
        const bool sram_rolled_back = RtlTryWriteSram();
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_PROFILE_RESET ROLLED_BACK profile=%d sram=%d\n",
                profile_rolled_back ? 1 : 0,
                sram_rolled_back ? 1 : 0);
            std::fflush(stderr);
        }
        return false;
    }

    g_profile_state = candidate;
    g_tour_continue = {};
    g_tour_continue_profile_id.clear();
    product_diagnostic("UR_PROFILE_RESET APPLIED");
    return true;
}

void open_profile_reset_confirmation() {
    g_profile_reset = ur::product::modern_profile_reset_open(
        modern_mode()
            ? ur::product::ExecutionMode::Modern
            : ur::product::ExecutionMode::Authentic,
        active_profile_reset_authoritative(),
        selected_profile_is_active());
    if (ur::product::modern_profile_reset_confirming(g_profile_reset)) {
        product_diagnostic("UR_PROFILE_RESET CONFIRM_OPENED");
    } else {
        product_diagnostic("UR_PROFILE_RESET REJECTED_CONTEXT");
    }
}

bool append_profile_editor_key(int key) {
    if (g_profile_edit_mode == ProfileEditMode::None) return false;
    if (key == SDLK_BACKSPACE) {
        if (!g_profile_edit_name.empty()) g_profile_edit_name.pop_back();
        g_profile_edit_pristine = false;
        return true;
    }
    char ch = 0;
    if (key >= SDLK_a && key <= SDLK_z) ch = static_cast<char>('A' + key - SDLK_a);
    else if (key >= SDLK_0 && key <= SDLK_9) ch = static_cast<char>('0' + key - SDLK_0);
    else if (key == SDLK_SPACE) ch = ' ';
    if (!ch) return false;
    if (g_profile_edit_pristine) {
        g_profile_edit_name.clear();
        g_profile_edit_pristine = false;
    }
    if (g_profile_edit_name.size() < 16) g_profile_edit_name += ch;
    return true;
}

bool handle_profile_menu_key(int key) {
    ensure_profile_catalog();

    if (ur::product::modern_profile_reset_confirming(g_profile_reset)) {
        if (key == SDLK_ESCAPE || key == SDLK_b) {
            g_profile_reset = ur::product::modern_profile_reset_cancel(
                g_profile_reset);
            product_diagnostic("UR_PROFILE_RESET CANCELLED");
            return true;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            const auto decision = ur::product::modern_profile_reset_confirm(
                g_profile_reset,
                modern_mode()
                    ? ur::product::ExecutionMode::Modern
                    : ur::product::ExecutionMode::Authentic,
                active_profile_reset_authoritative(),
                selected_profile_is_active());
            g_profile_reset = decision.state;
            if (decision.action ==
                ur::product::ModernProfileResetAction::Execute) {
                (void)execute_active_profile_progress_reset();
            }
            return true;
        }
        return true;
    }

    if (g_profile_edit_mode != ProfileEditMode::None) {
        if (key == SDLK_ESCAPE) {
            g_profile_edit_mode = ProfileEditMode::None;
            return true;
        }
        if (g_profile_edit_mode == ProfileEditMode::Create &&
            (key == SDLK_LEFT || key == SDLK_RIGHT)) {
            const auto count = ur::product::legacy_racer_presets().size();
            if (key == SDLK_RIGHT) g_profile_preset_index = (g_profile_preset_index + 1) % count;
            else g_profile_preset_index = (g_profile_preset_index + count - 1) % count;
            g_profile_edit_name = std::string(
                ur::product::legacy_racer_presets()[g_profile_preset_index].name);
            g_profile_edit_pristine = true;
            return true;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            const bool saved =
                g_profile_edit_mode == ProfileEditMode::Create
                    ? create_profile_from_editor()
                    : rename_profile_from_editor();
            if (!saved) {
                product_diagnostic("UR_PROFILE_UI SAVE_REJECTED");
            }
            // The profile editor is modal. A rejected save must not leak the
            // same Enter press into the stock rider-select screen underneath.
            return true;
        }
        (void)append_profile_editor_key(key);
        // The text editor is modal even for keys it does not accept as name
        // input. Never leak those keys into the stock frontend underneath.
        return true;
    }

    if (key == SDLK_ESCAPE || key == SDLK_F2) {
        g_profile_menu_visible = false;
        if (std::getenv("UR_PROFILE_PANEL_ACCEPTANCE")) {
            g_profile_panel_acceptance_confirm_pending = true;
            product_diagnostic("UR_PROFILE_UI ACCEPTANCE_CONFIRM_ARMED");
        }
        return true;
    }
    if (key == SDLK_n) { begin_profile_create(); return true; }
    if (key == SDLK_r) { begin_profile_rename(); return true; }
    if (key == SDLK_d) { open_profile_reset_confirmation(); return true; }
    if (key == SDLK_UP && !g_profile_catalog.empty()) {
        g_profile_menu_index =
            (g_profile_menu_index + g_profile_catalog.size() - 1) %
            g_profile_catalog.size();
        return true;
    }
    if (key == SDLK_DOWN && !g_profile_catalog.empty()) {
        g_profile_menu_index =
            (g_profile_menu_index + 1) % g_profile_catalog.size();
        return true;
    }
    if ((key == SDLK_RETURN || key == SDLK_KP_ENTER) &&
        g_profile_menu_index < g_profile_catalog.size()) {
        return activate_profile_id(
            g_profile_catalog[g_profile_menu_index].profile_id);
    }
    return true;
}

void project_profile_identity_to_stock_rider() {
    if (!modern_mode() || !g_profile_state ||
        !g_profile_state->racer_identity || !g_sram ||
        g_sram_size <= 0x0748) return;

    const std::uint8_t rider =
        g_profile_state->racer_identity->rider_index;
    g_sram[0x0748] = rider;

    // PLAYER_SELECT_P1 is still the authoritative stock handoff. Keep its
    // ordinary cursor state aligned with the Modern identity so confirmation
    // performs the stock write to P1_RiderIndex ($017D):
    //   rider = 2 * Frontend_SelectedRow + (column - 0x06)
    if (g_ram && g_ram[0x009F] == 0x3C) {
        g_ram[0x000E] = static_cast<std::uint8_t>(rider / 2u);
        g_ram[0x0C63] = static_cast<std::uint8_t>(
            0x06u + (rider & 1u));
    }
}

bool toggle_focus_pause_setting() {
    if (!modern_mode()) return false;
    ur::product::HostProductState candidate = g_product_state;
    candidate.settings.pause_on_focus_loss =
        !candidate.settings.pause_on_focus_loss;
    if (!persist_product_state(candidate)) {
        return false;
    }
    g_product_state = candidate;
    return true;
}

bool toggle_vibration_setting() {
    if (!modern_mode()) return false;
    ur::product::HostProductState candidate = g_product_state;
    candidate.settings.vibration_enabled =
        !candidate.settings.vibration_enabled;
    if (!persist_product_state(candidate)) {
        return false;
    }
    g_product_state = candidate;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr, "UR_VIBRATION SELECTED enabled=%d\n",
            g_product_state.settings.vibration_enabled ? 1 : 0);
        std::fflush(stderr);
    }
    return true;
}

// Volume is the framework's own [Sound] Volume (config.ini, keypad +/-, OSD
// bar). The Options row only steps that authority; Modern keeps no copy.
bool step_volume_setting(int direction) {
    if (!modern_mode()) return false;
    const int percent = snesrecomp_desktop_step_volume(direction);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_VOLUME SELECTED percent=%d\n", percent);
        std::fflush(stderr);
    }
    return true;
}

bool restore_video_output_settings(
    const ur::product::HostSettings& settings) {
    if (!apply_display_mode_setting(settings)) {
        return false;
    }
    return apply_output_resolution_setting(settings);
}

bool toggle_display_mode_setting() {
    if (!modern_mode()) return false;

    ur::product::HostProductState candidate = g_product_state;
    switch (candidate.settings.display_mode) {
    case ur::product::HostDisplayMode::Windowed:
        candidate.settings.display_mode =
            ur::product::HostDisplayMode::BorderlessFullscreen;
        break;
    case ur::product::HostDisplayMode::BorderlessFullscreen:
        candidate.settings.display_mode =
            ur::product::HostDisplayMode::Fullscreen;
        break;
    case ur::product::HostDisplayMode::Fullscreen:
        candidate.settings.display_mode =
            ur::product::HostDisplayMode::Windowed;
        break;
    }

    if (!apply_display_mode_setting(candidate.settings)) {
        return false;
    }
    if (!apply_output_resolution_setting(candidate.settings)) {
        (void)restore_video_output_settings(g_product_state.settings);
        return false;
    }
    if (!persist_product_state(candidate)) {
        (void)restore_video_output_settings(g_product_state.settings);
        return false;
    }

    g_product_state = candidate;
    return true;
}

bool cycle_vsync_setting() {
    if (!modern_mode()) return false;

    ur::product::HostProductState candidate = g_product_state;
    switch (candidate.settings.vsync_mode) {
    case ur::product::HostVSyncMode::Off:
        candidate.settings.vsync_mode = ur::product::HostVSyncMode::On;
        break;
    case ur::product::HostVSyncMode::On:
        candidate.settings.vsync_mode = ur::product::HostVSyncMode::Adaptive;
        break;
    case ur::product::HostVSyncMode::Adaptive:
        candidate.settings.vsync_mode = ur::product::HostVSyncMode::Off;
        break;
    }

    if (!apply_vsync_setting(candidate.settings)) {
        return false;
    }
    if (!persist_product_state(candidate)) {
        (void)apply_vsync_setting(g_product_state.settings);
        return false;
    }

    g_product_state = candidate;
    return true;
}

bool cycle_presentation_fps_setting() {
    if (!modern_mode()) return false;

    ur::product::HostProductState candidate = g_product_state;
    switch (candidate.settings.presentation_fps_mode) {
    case ur::product::HostPresentationFpsMode::Game:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Fps60;
        break;
    case ur::product::HostPresentationFpsMode::Fps60:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Fps90;
        break;
    case ur::product::HostPresentationFpsMode::Fps90:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Fps120;
        break;
    case ur::product::HostPresentationFpsMode::Fps120:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Fps144;
        break;
    case ur::product::HostPresentationFpsMode::Fps144:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Native;
        break;
    case ur::product::HostPresentationFpsMode::Native:
        candidate.settings.presentation_fps_mode =
            ur::product::HostPresentationFpsMode::Game;
        break;
    }

    if (!apply_presentation_fps_setting(candidate.settings)) {
        return false;
    }
    if (!persist_product_state(candidate)) {
        (void)apply_presentation_fps_setting(g_product_state.settings);
        return false;
    }

    g_product_state = candidate;
    return true;
}

bool cycle_output_resolution_setting() {
    if (!modern_mode()) return false;

    const auto modes = active_output_modes();
    const auto choices = ur::product::build_output_resolution_choices(modes);
    if (choices.empty()) {
        product_diagnostic("UR_OUTPUT_RESOLUTION CATALOG_EMPTY");
        return false;
    }

    ur::product::HostProductState candidate = g_product_state;
    candidate.settings.output_resolution =
        ur::product::cycle_output_resolution(
            g_product_state.settings.output_resolution, choices, 1);

    if (!apply_output_resolution_setting(candidate.settings)) {
        return false;
    }
    if (!persist_product_state(candidate)) {
        const bool restored =
            apply_output_resolution_setting(g_product_state.settings);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_OUTPUT_RESOLUTION ROLLBACK restored=%d value=%s\n",
                restored ? 1 : 0,
                output_resolution_name(
                    g_product_state.settings.output_resolution).c_str());
            std::fflush(stderr);
        }
        return false;
    }

    g_product_state = candidate;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_OUTPUT_RESOLUTION SELECTED value=%s choices=%zu\n",
            output_resolution_name(
                g_product_state.settings.output_resolution).c_str(),
            choices.size());
        std::fflush(stderr);
    }
    return true;
}

bool apply_internal_render_scale_setting(
    const ur::product::HostSettings& settings) {
    if (!modern_mode()) return false;
    const int scale = ur::product::internal_render_scale_value(
        settings.internal_render_scale);
    if (!ur::presentation::racer_hd_set_internal_render_scale(scale)) {
        return false;
    }
    snesrecomp_desktop_request_clock_reset();
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_RENDER_SCALE APPLIED scale=%dx\n", scale);
        std::fflush(stderr);
    }
    return true;
}

bool cycle_internal_render_scale_setting() {
    if (!modern_mode()) return false;
    ur::product::HostProductState candidate = g_product_state;
    candidate.settings.internal_render_scale =
        ur::product::next_internal_render_scale(
            candidate.settings.internal_render_scale);
    if (!apply_internal_render_scale_setting(candidate.settings)) return false;
    if (!persist_product_state(candidate)) {
        (void)apply_internal_render_scale_setting(g_product_state.settings);
        return false;
    }
    g_product_state = candidate;
    return true;
}

void refresh_run_ghost_playback_trace();

bool cycle_widescreen_setting() {
    if (!modern_mode()) return false;

    ur::product::HostProductState candidate = g_product_state;
    candidate.settings.widescreen_mode =
        candidate.settings.widescreen_mode ==
                ur::product::HostWidescreenMode::Authentic16x9
            ? ur::product::HostWidescreenMode::Original
            : ur::product::HostWidescreenMode::Authentic16x9;

    if (!persist_product_state(candidate)) {
        return false;
    }

    g_product_state = candidate;
    synchronize_widescreen_provider_selector();
    snesrecomp_desktop_request_clock_reset();
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_WIDESCREEN SELECTED mode=%s\n",
            widescreen_mode_name(g_product_state.settings.widescreen_mode));
        std::fflush(stderr);
    }
    return true;
}

bool cycle_ghost_target_setting() {
    if (!modern_mode() || !g_profile_state || !g_profile_state_writable ||
        g_profile_state_path.empty()) {
        return false;
    }

    auto candidate = *g_profile_state;
    switch (candidate.ghost_target) {
    case ur::product::CompletedRunGhostTarget::Off:
        candidate.ghost_target =
            ur::product::CompletedRunGhostTarget::Previous;
        break;
    case ur::product::CompletedRunGhostTarget::Previous:
        candidate.ghost_target =
            ur::product::CompletedRunGhostTarget::PersonalBest;
        break;
    case ur::product::CompletedRunGhostTarget::PersonalBest:
        candidate.ghost_target = ur::product::CompletedRunGhostTarget::Off;
        break;
    }

    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        product_diagnostic("UR_RUN_GHOST TARGET_SAVE_FAILED");
        return false;
    }

    g_profile_state = candidate;
    refresh_run_ghost_playback_trace();
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RUN_GHOST TARGET_SELECTED target=%s\n",
            ur::product::completed_run_ghost_target_name(
                g_profile_state->ghost_target));
        std::fflush(stderr);
    }
    return true;
}

bool activate_options_selection() {
    switch (ur_modern_options_menu_selected(&g_options_menu)) {
    case UR_MODERN_OPTIONS_FOCUS_PAUSE:
        return toggle_focus_pause_setting();
    case UR_MODERN_OPTIONS_DISPLAY_MODE:
        return toggle_display_mode_setting();
    case UR_MODERN_OPTIONS_VSYNC:
        return cycle_vsync_setting();
    case UR_MODERN_OPTIONS_PRESENTATION_FPS:
        return cycle_presentation_fps_setting();
    case UR_MODERN_OPTIONS_OUTPUT_RESOLUTION:
        return cycle_output_resolution_setting();
    case UR_MODERN_OPTIONS_RENDER_SCALE:
        return cycle_internal_render_scale_setting();
    case UR_MODERN_OPTIONS_WIDESCREEN:
        return cycle_widescreen_setting();
    case UR_MODERN_OPTIONS_GHOST:
        return cycle_ghost_target_setting();
    case UR_MODERN_OPTIONS_VIBRATION:
        return toggle_vibration_setting();
    case UR_MODERN_OPTIONS_VOLUME:
        return step_volume_setting(1);
    }
    return false;
}

std::size_t save_snapshot(void* dst, std::size_t capacity) {
    return RtlRollbackSaveToMemory(dst, capacity);
}

bool load_snapshot(const void* src, std::size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &RtlRollbackLoadFromMemory,
        src,
        size,
        g_sram,
        g_sram_size > 0 ? static_cast<std::size_t>(g_sram_size) : 0u);
}

void set_timing_lock(int active) {
    RtlSetRewindAudioTimingLock(active != 0);
}

void reconcile_presentation() {
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

bool exit_to_frontend();

uint32_t current_sram_digest() {
    uint32_t hash = 2166136261u;
    if (!g_sram || g_sram_size <= 0) return hash;
    for (int i = 0; i < g_sram_size; ++i) {
        hash ^= g_sram[i];
        hash *= 16777619u;
    }
    return hash;
}

bool ensure_session() {
    if (g_session) return true;
    ensure_product_state();
    ensure_onboarding_state();
    const std::size_t capacity = RtlRollbackSnapshotBound();
    if (!capacity) return false;

    g_session = ur_modern_session_create(
        modern_mode() ? 1 : 0,
        capacity,
        &save_snapshot,
        &load_snapshot,
        &snesrecomp_desktop_set_paused,
        &snesrecomp_desktop_is_paused,
        &set_timing_lock,
        &reconcile_presentation,
        &exit_to_frontend);
    // The Modern pause family (pause root, Options, Controls, Run Data,
    // Records, Quit) is drawn by the system overlay while the guest is
    // frozen, so the paused host must keep presenting it. Authentic keeps the
    // framework default of presenting nothing new while paused.
    snesrecomp_desktop_set_paused_overlay_presentation(modern_mode() ? 1 : 0);
    ur_modern_pause_menu_reset(&g_pause_menu);
    ur_modern_options_menu_reset(&g_options_menu);
    ur_uniracers_restart_policy_reset(&g_title_policy);
    ur::product::reset_widescreen_scene_state(&g_widescreen_scene_state);
    g_widescreen_scene = ur::product::HostSceneComposition::FixedCenter;
    if (g_session && modern_mode()) {
        (void)apply_display_mode_setting(g_product_state.settings);
        (void)apply_output_resolution_setting(g_product_state.settings);
        (void)apply_presentation_fps_setting(g_product_state.settings);
        (void)apply_vsync_setting(g_product_state.settings);
        (void)apply_internal_render_scale_setting(g_product_state.settings);
    }
    return g_session != nullptr;
}

ur::product::HostTourContinuation product_continuation(
    const ur::title::TourProgress& progress) {
    ur::product::HostTourContinuation out;
    out.rider_index = progress.rider_index;
    out.tour_row = progress.tour_row;
    out.medal_value = progress.medal_value;
    out.qualified = progress.qualified;
    return out;
}

ur::title::TourProgress title_continuation(
    const ur::product::HostTourContinuation& continuation) {
    ur::title::TourProgress out;
    out.rider_index = continuation.rider_index;
    out.tour_row = continuation.tour_row;
    out.medal_value = continuation.medal_value;
    out.qualified = continuation.qualified;
    return out;
}

bool profile_snapshot_matches_live_sram(
    const ur::product::HostProfileState& state) {
    if (!state.stock_sram || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }
    return std::memcmp(
        state.stock_sram->data(),
        g_sram,
        ur::product::kStockSramBytes) == 0;
}

bool tour_continue_available() {
    if (!modern_mode() || g_practice_active || paused() || !g_ram ||
        g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7 ||
        !g_profile_state || !g_profile_state_writable ||
        !g_profile_state->tour_continuation ||
        !g_profile_state->stock_sram ||
        !ur::product::valid_tour_continuation(
            *g_profile_state->tour_continuation) ||
        !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    const auto continuation =
        title_continuation(*g_profile_state->tour_continuation);
    return ur::title::tour_resume_source_matches_sram(
               continuation,
               g_profile_state->stock_sram->data(),
               g_profile_state->stock_sram->size()) &&
           ur::title::tour_resume_frontend_source_matches_sram(
               continuation,
               g_sram,
               static_cast<std::size_t>(g_sram_size));
}

bool tour_continue_routing() {
    return g_tour_continue.stage !=
               ur::product::ModernTourContinueStage::Idle &&
           g_tour_continue.stage !=
               ur::product::ModernTourContinueStage::Ready;
}

std::optional<std::uint8_t> available_next_event_slot() {
    if (!g_profile_state || !g_profile_state->tour_continuation) {
        return std::nullopt;
    }
    return ur::product::unique_remaining_tour_slot(
        g_profile_state->tour_continuation->qualified);
}

std::optional<ur::title::TourProgress> current_results_tour_progress() {
    if (!modern_mode() || g_practice_active || !g_ram || !g_sram ||
        g_surface != UR_UNIRACERS_RESTART_RESULTS ||
        g_widescreen_scene_state.race_mode !=
            ur::product::HostRacePresentationMode::OnePlayer ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return std::nullopt;
    }
    return ur::title::observe_tour_progress(
        g_ram,
        0x20000,
        g_sram,
        static_cast<std::size_t>(g_sram_size));
}

bool results_navigation_router_available() {
    return modern_mode() && !paused() &&
           !g_exit_frontend_waiting_for_main &&
           !g_exit_frontend_waiting_for_usable &&
           !practice_routing() &&
           !tour_continue_routing() &&
           !g_tour_action_visible &&
           g_results_route_pending == ur::product::ModernResultsAction::None &&
           !g_results_tour_route_active;
}

ur::product::ModernResultsNavigationContext
current_results_navigation_context() {
    const auto progress = current_results_tour_progress();
    const bool profile_matches =
        progress &&
        g_profile_state &&
        g_profile_state_writable &&
        g_profile_state->stock_sram &&
        g_product_state.active_profile_id &&
        *g_product_state.active_profile_id == g_profile_state->profile_id &&
        profile_snapshot_matches_live_sram(*g_profile_state);
    return {
        modern_mode() ? ur::product::ExecutionMode::Modern
                      : ur::product::ExecutionMode::Authentic,
        g_surface == UR_UNIRACERS_RESTART_RESULTS,
        g_practice_active,
        progress.has_value(),
        g_profile_state.has_value() && g_profile_state_writable,
        profile_matches,
        results_navigation_router_available(),
        g_session && ur_modern_session_restart_available(g_session),
        progress &&
            ur::product::unique_remaining_tour_slot(
                progress->qualified).has_value(),
    };
}

void refresh_results_navigation_menu() {
    const auto previous =
        ur::product::selected_modern_results_action(g_results_navigation_menu);
    auto next = ur::product::make_modern_results_navigation_menu(
        current_results_navigation_context());
    for (std::size_t i = 0; i < next.row_count; ++i) {
        if (next.rows[i] == previous) {
            next.selected = i;
            break;
        }
    }
    g_results_navigation_menu = next;
}

bool results_navigation_active() {
    if (!modern_mode() || paused() ||
        g_surface != UR_UNIRACERS_RESTART_RESULTS) {
        return false;
    }
    const auto context = current_results_navigation_context();
    // This slice intentionally owns only ordinary one-player tour results and
    // Quick Practice results. Preserve the existing stock/host presentation
    // for VS and other unsupported result families instead of broadening the
    // feature by virtue of generic Retry/Records availability.
    if (!context.practice_active && !context.ordinary_tour_result) {
        return false;
    }
    refresh_results_navigation_menu();
    return g_results_navigation_menu.row_count != 0;
}

ur::product::ModernTourEntryContext current_tour_entry_context() {
    const bool available = tour_continue_available();
    return {
        modern_mode() ? ur::product::ExecutionMode::Modern
                      : ur::product::ExecutionMode::Authentic,
        available,
        available,
        available,
        available && available_next_event_slot().has_value(),
    };
}

const char* tour_entry_intent_name(
    ur::product::ModernTourEntryIntent intent) noexcept {
    switch (intent) {
    case ur::product::ModernTourEntryIntent::Resume:
        return "resume";
    case ur::product::ModernTourEntryIntent::Restart:
        return "restart";
    case ur::product::ModernTourEntryIntent::NextEvent:
        return "next_event";
    case ur::product::ModernTourEntryIntent::None:
    default:
        return "none";
    }
}

const char* challenge_tier_name(
    ur::product::ModernChallengeTier tier) noexcept {
    switch (tier) {
    case ur::product::ModernChallengeTier::Silver:
        return "SILVER";
    case ur::product::ModernChallengeTier::Gold:
        return "GOLD";
    case ur::product::ModernChallengeTier::Bronze:
    default:
        return "BRONZE";
    }
}

void close_tour_action_menu(const char* diagnostic) {
    g_tour_action_visible = false;
    g_tour_action_menu = {};
    if (diagnostic) product_diagnostic(diagnostic);
}

bool open_tour_action_menu() {
    const auto context = current_tour_entry_context();
    const auto actions = ur::product::modern_tour_entry_actions(context);
    if (!actions.resume_available || !g_profile_state ||
        !g_profile_state->tour_continuation) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_TOUR_ENTRY MENU_UNAVAILABLE modern=%d paused=%d menu=%02X race=%u profile=%d writable=%d continuation=%d snapshot=%d\n",
                modern_mode() ? 1 : 0,
                paused() ? 1 : 0,
                g_ram ? static_cast<unsigned>(g_ram[0x009F]) : 0u,
                g_ram ? static_cast<unsigned>(g_ram[0x0313]) : 0u,
                g_profile_state.has_value() ? 1 : 0,
                g_profile_state_writable ? 1 : 0,
                (g_profile_state &&
                 g_profile_state->tour_continuation.has_value()) ? 1 : 0,
                (g_profile_state &&
                 g_profile_state->stock_sram.has_value()) ? 1 : 0);
            std::fflush(stderr);
        }
        return false;
    }
    g_tour_action_menu =
        ur::product::make_modern_tour_action_menu(context);
    g_tour_action_visible = true;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        const auto tier = ur::product::default_modern_challenge_tier(
            g_profile_state->tour_continuation->medal_value);
        std::fprintf(
            stderr,
            "UR_TOUR_ENTRY MENU_OPENED rider=%u tour=%u tier=%s next_event=%d\n",
            static_cast<unsigned>(
                g_profile_state->tour_continuation->rider_index),
            static_cast<unsigned>(
                g_profile_state->tour_continuation->tour_row),
            challenge_tier_name(tier),
            context.next_event_unique ? 1 : 0);
        std::fflush(stderr);
    }
    return true;
}

void cancel_tour_continue(const char* diagnostic) {
    const bool results_route = g_results_tour_route_active;
    g_tour_continue = {};
    g_next_event_target_track.reset();
    g_tour_continue_profile_id.clear();
    if (results_route) {
        g_results_tour_route_active = false;
        g_results_route_progress.reset();
        g_results_route_profile_id.clear();
    }
    if (diagnostic) product_diagnostic(diagnostic);
}

bool tour_entry_crossed_stock_rider_wipe() noexcept {
    if (!g_ram) return false;

    // During the rider -> tour transition the frontend byte can be transient
    // even though stock has already cleared the qualification row. The route
    // starts only from an exact non-empty continuation source, so an empty
    // saved-tour row is direct title-owned evidence that the destructive stock
    // boundary has been crossed.
    if (g_profile_state && g_profile_state->tour_continuation && g_sram &&
        g_sram_size == static_cast<int>(ur::product::kStockSramBytes)) {
        const auto saved =
            title_continuation(*g_profile_state->tour_continuation);
        if (ur::title::tour_qualification_row_empty(
                saved.tour_row,
                g_sram,
                static_cast<std::size_t>(g_sram_size))) {
            return true;
        }
    }

    if (g_ram[0x009F] == 0x6D || g_ram[0x009F] == 0xF6) return true;
    return g_tour_continue.stage ==
               ur::product::ModernTourContinueStage::AwaitTrack ||
           g_tour_continue.stage ==
               ur::product::ModernTourContinueStage::Ready;
}

bool rollback_tour_entry_to_profile_snapshot() {
    if (!modern_mode() || !g_profile_state || !g_profile_state->stock_sram ||
        g_tour_continue_profile_id.empty() ||
        g_tour_continue_profile_id != g_profile_state->profile_id ||
        !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    const auto restored = ur::product::restore_stock_sram_from_profile(
        ur::product::ExecutionMode::Modern,
        *g_profile_state,
        g_sram,
        static_cast<std::size_t>(g_sram_size));
    if (restored != ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }
    if (!RtlTryWriteSram()) {
        product_diagnostic("UR_TOUR_CONTINUE ROLLBACK_SRAM_WRITE_FAILED");
        return false;
    }
    product_diagnostic("UR_TOUR_CONTINUE ROLLED_BACK_PROFILE_SNAPSHOT");
    return true;
}

void abort_tour_continue(
    const char* diagnostic,
    bool rollback_required) {
    // The full profile SRAM snapshot is a recovery authority only after stock
    // rider confirmation has crossed its historical qualification-row wipe.
    // Before that boundary, live SRAM has not been destructively changed by
    // this route and replacing all 8 KiB could discard unrelated live state.
    const bool restored =
        !rollback_required || rollback_tour_entry_to_profile_snapshot();
    cancel_tour_continue(nullptr);
    if (diagnostic) product_diagnostic(diagnostic);
    if (rollback_required && !restored) {
        product_diagnostic("UR_TOUR_CONTINUE ROLLBACK_UNAVAILABLE");
    }
}

void abort_tour_continue(const char* diagnostic) {
    abort_tour_continue(
        diagnostic,
        tour_entry_crossed_stock_rider_wipe());
}

bool begin_tour_entry(ur::product::ModernTourEntryIntent intent) {
    const auto context = current_tour_entry_context();
    const auto decision = ur::product::resolve_modern_tour_entry(
        context,
        intent,
        intent == ur::product::ModernTourEntryIntent::Restart);
    if (decision.intent == ur::product::ModernTourEntryIntent::None ||
        !g_profile_state || !g_profile_state->tour_continuation) {
        product_diagnostic("UR_TOUR_ENTRY REJECTED");
        return false;
    }

    const auto& continuation = *g_profile_state->tour_continuation;
    std::optional<std::uint8_t> next_event_track;
    if (decision.intent == ur::product::ModernTourEntryIntent::NextEvent) {
        const auto slot = available_next_event_slot();
        next_event_track = ur::product::unique_next_track_id(
            continuation.tour_row, continuation.qualified);
        g_tour_continue = slot && next_event_track
            ? ur::product::begin_modern_tour_next_event(
                  continuation.tour_row, decision, *slot)
            : ur::product::ModernTourContinueState{};
    } else {
        g_tour_continue = ur::product::begin_modern_tour_entry(
            continuation.tour_row, decision);
    }
    if (g_tour_continue.stage ==
        ur::product::ModernTourContinueStage::Idle) {
        return false;
    }
    g_tour_continue_profile_id = g_profile_state->profile_id;
    g_next_event_target_track = next_event_track;
    g_next_event_verify_track.reset();

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        unsigned completed = 0;
        for (const auto flag : continuation.qualified) completed += flag;
        const auto tier = ur::product::default_modern_challenge_tier(
            continuation.medal_value);
        std::fprintf(
            stderr,
            "UR_TOUR_CONTINUE STARTED intent=%s rider=%u tour=%u completed=%u tier=%s menu=%02X race=%u\n",
            tour_entry_intent_name(intent),
            static_cast<unsigned>(continuation.rider_index),
            static_cast<unsigned>(continuation.tour_row),
            completed,
            challenge_tier_name(tier),
            static_cast<unsigned>(g_ram[0x009F]),
            static_cast<unsigned>(g_ram[0x0313]));
        std::fflush(stderr);
    }
    return true;
}



void close_progress_overview(const char* diagnostic) {
    g_progress_overview_visible = false;
    g_progress_overview_draw_reported = false;
    g_progress_overview = {};
    g_progress_overview_profile_id.reset();
    if (diagnostic) product_diagnostic(diagnostic);
}

bool progress_overview_context_valid() {
    return g_progress_overview_visible && g_progress_overview.valid &&
        modern_mode() && !paused() && g_ram &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        !g_practice_active &&
        g_progress_overview_profile_id == g_product_state.active_profile_id;
}

bool open_progress_overview() {
    if (!modern_mode() || !g_ram || !g_sram || paused() ||
        g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01 ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes) ||
        g_progress_overview_visible || g_practice_picker.visible ||
        g_practice_active || g_profile_menu_visible ||
        g_tour_action_visible || onboarding_surface_active() ||
        g_local_multiplayer_join_visible || results_navigation_active() ||
        tour_continue_routing() || practice_routing() ||
        g_exit_frontend_waiting_for_main ||
        g_exit_frontend_waiting_for_usable) {
        return false;
    }
    const std::uint8_t selected = g_sram[0x0748];
    const std::uint8_t rider = selected < 16 ? selected : 0;
    if (g_profile_state && g_profile_state->racer_identity &&
        g_profile_state->racer_identity->rider_index != rider) {
        return false;
    }
    const auto overview = ur::title::observe_stock_tour_progress_overview(
        g_sram, static_cast<std::size_t>(g_sram_size), rider);
    if (!overview.valid) {
        product_diagnostic("UR_TOUR_OVERVIEW SOURCE_INVALID");
        return false;
    }
    g_progress_overview = overview;
    g_progress_overview_visible = true;
    g_progress_overview_draw_reported = false;
    g_progress_overview_profile_id = g_product_state.active_profile_id;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(stderr,
            "UR_TOUR_OVERVIEW OPENED rider=%u bronze=%u silver=%u gold=%u visible=%04X\n",
            static_cast<unsigned>(rider),
            overview.bronze_or_better, overview.silver_or_better,
            overview.gold, static_cast<unsigned>(overview.visible_tour_options));
        std::fflush(stderr);
    }
    return true;
}

void close_practice_picker(const char* diagnostic) {
    g_practice_picker = {};
    g_practice_picker_draw_reported = false;
    g_practice_picker_profile_id.reset();
    if (diagnostic) product_diagnostic(diagnostic);
}

bool practice_picker_context_valid() {
    return g_practice_picker.visible && modern_mode() &&
        !g_practice_active && !paused() && g_ram &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        g_practice_picker_profile_id == g_product_state.active_profile_id;
}

bool open_practice_picker() {
    if (!modern_mode() || !g_ram || paused() || g_practice_active ||
        g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01 ||
        g_profile_menu_visible || g_tour_action_visible ||
        g_local_multiplayer_join_visible || onboarding_surface_active() ||
        practice_routing() || tour_continue_routing() ||
        results_navigation_active() || g_exit_frontend_waiting_for_main ||
        g_exit_frontend_waiting_for_usable) {
        return false;
    }
    if (!g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }
    const std::uint8_t selected_rider = g_sram[0x0748];
    const std::uint8_t stock_rider = selected_rider < 16
        ? selected_rider : 0;
    if (g_profile_state && g_profile_state->racer_identity &&
        g_profile_state->racer_identity->rider_index != stock_rider) {
        return false;
    }
    const auto stock_tour_options = ur::title::stock_practice_tour_option_mask(
        g_sram, static_cast<std::size_t>(g_sram_size), stock_rider);
    if (!stock_tour_options) {
        product_diagnostic("UR_PRACTICE_PICKER UNLOCK_SOURCE_INVALID");
        return false;
    }
    g_practice_picker_availability =
        ur::product::quick_practice_availability_from_tour_options(
            *stock_tour_options);
    const std::uint8_t initial_track =
        recent_course_available_for_active_profile()
            ? *g_recent_course_track_id : 0;
    g_practice_picker = ur::product::open_available_quick_practice_selection(
        initial_track, g_practice_picker_availability);
    g_practice_picker_draw_reported = false;
    if (!g_practice_picker.visible) return false;
    g_practice_picker_profile_id = g_product_state.active_profile_id;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_PRACTICE_PICKER OPENED track=%u available=%d\n",
            static_cast<unsigned>(g_practice_picker.picker.track_id),
            ur::product::quick_practice_available_count(
                g_practice_picker_availability));
        std::fflush(stderr);
    }
    return true;
}

bool handle_practice_picker_navigation(UrModernHostNavigationAction action) {
    if (!g_practice_picker.visible) return false;
    if (!practice_picker_context_valid()) {
        close_practice_picker("UR_PRACTICE_PICKER STALE_CONTEXT");
        return true;
    }
    using ur::product::QuickPracticeSelectionCommand;
    QuickPracticeSelectionCommand command;
    switch (action) {
    case UR_MODERN_HOST_NAV_UP:
        command = QuickPracticeSelectionCommand::PreviousCourse;
        break;
    case UR_MODERN_HOST_NAV_DOWN:
        command = QuickPracticeSelectionCommand::NextCourse;
        break;
    case UR_MODERN_HOST_NAV_LEFT:
        command = QuickPracticeSelectionCommand::PreviousTour;
        break;
    case UR_MODERN_HOST_NAV_RIGHT:
        command = QuickPracticeSelectionCommand::NextTour;
        break;
    case UR_MODERN_HOST_NAV_CONFIRM:
        command = QuickPracticeSelectionCommand::Confirm;
        break;
    case UR_MODERN_HOST_NAV_BACK:
        command = QuickPracticeSelectionCommand::Cancel;
        break;
    default:
        return true;
    }
    const auto result = ur::product::quick_practice_available_selection_apply(
        g_practice_picker, command, g_practice_picker_availability);
    g_practice_picker = result.state;
    if (result.result == ur::product::QuickPracticeSelectionResult::Updated) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(stderr, "UR_PRACTICE_PICKER SELECTED track=%u\n",
                static_cast<unsigned>(g_practice_picker.picker.track_id));
            std::fflush(stderr);
        }
    } else if (result.result ==
               ur::product::QuickPracticeSelectionResult::Cancelled) {
        close_practice_picker("UR_PRACTICE_PICKER CANCELLED");
    } else if (result.result ==
               ur::product::QuickPracticeSelectionResult::Confirmed) {
        const auto track_id = result.target.track_id;
        close_practice_picker(nullptr);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(stderr, "UR_PRACTICE_PICKER CONFIRMED track=%u\n",
                static_cast<unsigned>(track_id));
            std::fflush(stderr);
        }
        if (!begin_practice(track_id)) {
            product_diagnostic("UR_PRACTICE_PICKER ROUTE_START_FAILED");
        }
    }
    return true;
}

bool handle_tour_action_navigation(
    UrModernHostNavigationAction action) {
    if (!g_tour_action_visible) return false;

    const auto context = current_tour_entry_context();
    if (ur_modern_host_navigation_vertical_delta(action) != 0) {
        g_tour_action_menu =
            ur::product::navigate_modern_tour_action_menu(
                g_tour_action_menu, action);
        return true;
    }

    if (ur_modern_host_navigation_is_back(action) ||
        ur_modern_host_navigation_is_confirm(action)) {
        const auto result = ur::product::activate_modern_tour_action_menu(
            g_tour_action_menu, context, action);
        g_tour_action_menu = result.menu;

        if (result.intent != ur::product::ModernTourEntryIntent::None) {
            const auto intent = result.intent;
            close_tour_action_menu(nullptr);
            if (!begin_tour_entry(intent)) {
                product_diagnostic("UR_TOUR_ENTRY ROUTE_START_FAILED");
            }
            return true;
        }
        if (result.close_menu) {
            close_tour_action_menu("UR_TOUR_ENTRY CANCELLED");
        }
        return true;
    }
    return true;
}

bool begin_tour_continue() {
    if (!tour_continue_available()) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            const bool has_profile = g_profile_state.has_value();
            const bool has_continuation =
                has_profile && g_profile_state->tour_continuation.has_value();
            const bool has_snapshot =
                has_profile && g_profile_state->stock_sram.has_value();
            bool persisted_source_ok = false;
            bool live_source_ok = false;
            if (has_continuation && has_snapshot &&
                ur::product::valid_tour_continuation(
                    *g_profile_state->tour_continuation)) {
                const auto continuation =
                    title_continuation(*g_profile_state->tour_continuation);
                persisted_source_ok =
                    ur::title::tour_resume_source_matches_sram(
                        continuation,
                        g_profile_state->stock_sram->data(),
                        g_profile_state->stock_sram->size());
                if (g_sram &&
                    g_sram_size ==
                        static_cast<int>(ur::product::kStockSramBytes)) {
                    live_source_ok =
                        ur::title::tour_resume_frontend_source_matches_sram(
                            continuation,
                            g_sram,
                            static_cast<std::size_t>(g_sram_size));
                }
            }
            std::fprintf(
                stderr,
                "UR_TOUR_CONTINUE REJECTED modern=%d practice=%d paused=%d menu=%02X race=%u profile=%d writable=%d continuation=%d snapshot=%d persisted_source=%d live_source=%d\n",
                modern_mode() ? 1 : 0,
                g_practice_active ? 1 : 0,
                paused() ? 1 : 0,
                g_ram ? static_cast<unsigned>(g_ram[0x009F]) : 0u,
                g_ram ? static_cast<unsigned>(g_ram[0x0313]) : 0u,
                has_profile ? 1 : 0,
                g_profile_state_writable ? 1 : 0,
                has_continuation ? 1 : 0,
                has_snapshot ? 1 : 0,
                persisted_source_ok ? 1 : 0,
                live_source_ok ? 1 : 0);
            std::fflush(stderr);
        }
        return false;
    }

    return begin_tour_entry(
        ur::product::ModernTourEntryIntent::Resume);
}

void advance_tour_continue_route(uint64_t next_frame) {
    if (!tour_continue_routing()) return;

    const bool result_route_context_ok =
        g_results_tour_route_active &&
        g_results_route_progress &&
        g_results_route_progress->tour_row == g_tour_continue.tour_row &&
        g_results_route_profile_id == g_tour_continue_profile_id;
    const bool continuation_route_context_ok =
        !g_results_tour_route_active &&
        g_profile_state &&
        g_profile_state->tour_continuation &&
        ur::product::valid_tour_continuation(
            *g_profile_state->tour_continuation) &&
        g_profile_state->tour_continuation->tour_row ==
            g_tour_continue.tour_row;
    if (!modern_mode() || !g_profile_state ||
        !g_profile_state_writable ||
        g_tour_continue_profile_id.empty() ||
        g_profile_state->profile_id != g_tour_continue_profile_id ||
        (!result_route_context_ok && !continuation_route_context_ok)) {
        abort_tour_continue("UR_TOUR_CONTINUE ABORTED_CONTEXT");
        if (g_results_tour_route_active) clear_results_navigation_route();
        return;
    }

    const bool crossed_stock_rider_wipe =
        tour_entry_crossed_stock_rider_wipe();
    const auto step = ur::product::advance_modern_tour_continue(
        g_tour_continue,
        {
            g_ram[0x009F],
            g_ram[0x009B],
            g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE,
        });
    g_tour_continue = step.state;

    if (step.timed_out) {
        abort_tour_continue(
            "UR_TOUR_CONTINUE ABORTED_TIMEOUT",
            crossed_stock_rider_wipe);
        return;
    }
    if (step.tour_select_ready && g_results_tour_route_active) {
        const bool restore =
            g_results_route_progress &&
            ur::title::valid_unfinished_tour_progress(
                *g_results_route_progress);
        if (restore && !rollback_tour_entry_to_profile_snapshot()) {
            abort_tour_continue(
                "UR_RESULTS_NAV TOUR_SELECT_ROLLBACK_FAILED", true);
            clear_results_navigation_route();
            return;
        }
        cancel_tour_continue("UR_RESULTS_NAV TOUR_SELECT_READY");
        clear_results_navigation_route();
        return;
    }
    if (step.next_event_race_entered) {
        // The stock NOW_PLAYING confirm started an ordinary tour race. That
        // race owns progression from here; never roll SRAM back under it.
        g_next_event_verify_track = g_next_event_target_track;
        cancel_tour_continue("UR_NEXT_EVENT RACE_ENTERED");
        return;
    }
    if (g_tour_continue.stage == ur::product::ModernTourContinueStage::Idle) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_TOUR_CONTINUE ABORTED_UNEXPECTED_RACE menu=%02X race_surface=%d previous_race=%d\n",
                static_cast<unsigned>(g_ram[0x009F]),
                g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ? 1 : 0,
                g_run_capture_previous_active ? 1 : 0);
            std::fflush(stderr);
        }
        abort_tour_continue(
            nullptr,
            crossed_stock_rider_wipe);
        return;
    }

    if (step.input != ur::product::QuickPracticeMenuInput::None &&
        !queue_tour_continue_input(step.input, next_frame)) {
        abort_tour_continue("UR_TOUR_CONTINUE INPUT_FAILED");
        return;
    }

    if (step.track_select_ready) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_TOUR_CONTINUE READY intent=%s tour=%u menu=%02X\n",
                tour_entry_intent_name(g_tour_continue.intent),
                static_cast<unsigned>(
                    g_profile_state->tour_continuation->tour_row),
                static_cast<unsigned>(g_ram[0x009F]));
            std::fflush(stderr);
        }
        // Keep the typed intent in Ready until reconcile_tour_resume() settles
        // the TRACK_SELECT boundary. Input ownership is already released
        // because tour_continue_routing() excludes Ready.
    }
}

bool retire_tour_continuation_after_stock_reset() {
    if (!modern_mode() || g_practice_active || !g_profile_state ||
        !g_profile_state_writable || g_profile_state_path.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    const auto original = *g_profile_state;
    auto candidate = original;
    candidate.tour_continuation.reset();
    if (ur::product::capture_stock_sram_for_profile(
            ur::product::ExecutionMode::Modern,
            candidate,
            g_sram,
            static_cast<std::size_t>(g_sram_size)) !=
        ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }

    // Retirement is a two-file transaction. Publish the host profile first so
    // a profile-file failure cannot leave save.srm durably wiped while the old
    // resumable continuation remains. If the SRAM write then fails, roll the
    // profile metadata back to the exact pre-retirement state.
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        product_diagnostic("UR_TOUR_RESTART PROFILE_SAVE_FAILED");
        return false;
    }

    if (!RtlTryWriteSram()) {
        const auto rollback = ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            original);
        product_diagnostic(
            rollback == ur::product::HostProfileSaveStatus::Saved
                ? "UR_TOUR_RESTART PROFILE_ROLLED_BACK"
                : "UR_TOUR_RESTART PROFILE_ROLLBACK_FAILED");
        return false;
    }

    g_profile_state = std::move(candidate);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_TOUR_RESTART RETIRED generation=%llu\n",
            static_cast<unsigned long long>(
                g_profile_state->autosave_generation));
        std::fflush(stderr);
    }
    return true;
}

bool save_active_profile_state(
    const std::optional<ur::product::HostTourContinuation>& continuation,
    const char* diagnostic) {
    if (!modern_mode() || g_practice_active || !g_profile_state ||
        !g_profile_state_writable || g_profile_state_path.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return false;
    }

    if (g_profile_state->tour_continuation == continuation &&
        profile_snapshot_matches_live_sram(*g_profile_state)) {
        return true;
    }

    if (!RtlTryWriteSram()) {
        product_diagnostic("UR_TOUR_RESUME SRAM_SAVE_FAILED");
        return false;
    }

    auto candidate = *g_profile_state;
    candidate.tour_continuation = continuation;
    if (ur::product::capture_stock_sram_for_profile(
            ur::product::ExecutionMode::Modern,
            candidate,
            g_sram,
            static_cast<std::size_t>(g_sram_size)) !=
        ur::product::HostProfileTransferStatus::Applied) {
        return false;
    }
    if (ur::product::save_host_profile_state_file(
            ur::product::ExecutionMode::Modern,
            g_profile_state_path,
            candidate) != ur::product::HostProfileSaveStatus::Saved) {
        product_diagnostic("UR_TOUR_RESUME PROFILE_SAVE_FAILED");
        return false;
    }

    g_profile_state = candidate;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS") && diagnostic) {
        std::fprintf(
            stderr,
            "%s generation=%llu\n",
            diagnostic,
            static_cast<unsigned long long>(
                g_profile_state->autosave_generation));
        std::fflush(stderr);
    }
    return true;
}

void reconcile_tour_resume() {
    if (!modern_mode() || !g_profile_state || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        return;
    }

    const auto current = ur::title::observe_tour_progress(
        g_ram,
        0x20000,
        g_sram,
        static_cast<std::size_t>(g_sram_size));
    if (!current) return;

    // An explicit Resume/Restart route owns continuation semantics until its
    // TRACK_SELECT settle window has completed. In particular, first-visible
    // F6 must not fall through to the legacy passive restore path while a
    // Restart is still proving the stock wipe.
    if (g_tour_continue.stage !=
            ur::product::ModernTourContinueStage::Idle &&
        g_tour_continue.stage !=
            ur::product::ModernTourContinueStage::Ready) {
        return;
    }

    // Stock TRACK_SELECT is the first stable point after rider/tour
    // confirmation. Rider select has already performed its historical wipe.
    if (g_tour_continue.stage ==
            ur::product::ModernTourContinueStage::Ready &&
        g_ram[0x009F] != 0xF6) {
        abort_tour_continue("UR_TOUR_ENTRY SETTLEMENT_LEFT_TRACK_SELECT");
    }

    if (g_results_tour_route_active &&
        g_tour_continue.stage ==
            ur::product::ModernTourContinueStage::Ready &&
        g_ram[0x009F] == 0xF6 &&
        g_results_route_progress &&
        !ur::title::valid_unfinished_tour_progress(
            *g_results_route_progress)) {
        cancel_tour_continue("UR_RESULTS_NAV TRACK_SELECT_READY");
        clear_results_navigation_route();
        return;
    }

    if (g_ram[0x009F] == 0xF6 && g_profile_state->tour_continuation) {
        const auto saved =
            title_continuation(*g_profile_state->tour_continuation);

        const bool settling_routed_entry =
            g_tour_continue.stage ==
                ur::product::ModernTourContinueStage::Ready &&
            !g_tour_continue_profile_id.empty() &&
            g_tour_continue_profile_id == g_profile_state->profile_id &&
            g_tour_continue.tour_row == saved.tour_row;

        if (settling_routed_entry &&
            g_tour_continue.intent ==
                ur::product::ModernTourEntryIntent::Restart) {
            const ur::product::ModernTourEntryDecision decision{
                g_tour_continue.intent,
                true,
                g_tour_continue.restore_continuation_at_track_select,
                g_tour_continue.retire_continuation_after_stock_wipe,
            };
            const bool stock_context_matches =
                current->rider_index == saved.rider_index &&
                current->tour_row == saved.tour_row &&
                current->medal_value == saved.medal_value;
            const bool stock_row_empty =
                stock_context_matches &&
                ur::title::tour_qualification_row_empty(
                    saved.tour_row,
                    g_sram,
                    static_cast<std::size_t>(g_sram_size));
            if (ur::product::modern_tour_entry_may_retire_continuation(
                    decision, true, stock_row_empty)) {
                product_diagnostic("UR_TOUR_RESTART STOCK_RESET_PROVEN");
                if (retire_tour_continuation_after_stock_reset()) {
                    cancel_tour_continue(nullptr);
                } else {
                    // A failed retirement must not leave the live stock-empty
                    // row hanging around for a later framework shutdown/save.
                    // Restore the authoritative profile snapshot immediately
                    // and release the explicit route with continuation intact.
                    abort_tour_continue(
                        "UR_TOUR_RESTART RETIRE_PERSIST_FAILED");
                }
            } else {
                // A non-empty row means the stock destructive boundary has not
                // been proven. Preserve the resumable host continuation and
                // refuse to reinterpret this as Resume.
                product_diagnostic(
                    "UR_TOUR_RESTART RESET_NOT_PROVEN");
            }
            return;
        }

        if (current->rider_index == saved.rider_index &&
            current->tour_row == saved.tour_row &&
            current->medal_value != saved.medal_value) {
            (void)save_active_profile_state(
                std::nullopt,
                "UR_TOUR_RESUME CLEARED_STALE_MEDAL");
            cancel_tour_continue(nullptr);
            return;
        }

        if (settling_routed_entry &&
            (g_tour_continue.intent ==
                 ur::product::ModernTourEntryIntent::Resume ||
             g_tour_continue.intent ==
                 ur::product::ModernTourEntryIntent::NextEvent)) {
            const auto applied = ur::title::apply_tour_resume(
                saved,
                g_ram,
                0x20000,
                g_sram,
                static_cast<std::size_t>(g_sram_size));
            if (applied == ur::title::TourResumeApplyStatus::Applied ||
                applied ==
                    ur::title::TourResumeApplyStatus::AlreadyPresent) {
                if (applied ==
                    ur::title::TourResumeApplyStatus::Applied) {
                    (void)save_active_profile_state(
                        g_profile_state->tour_continuation,
                        "UR_TOUR_RESUME APPLIED");
                }
                if (g_tour_continue.intent ==
                    ur::product::ModernTourEntryIntent::NextEvent) {
                    // The restored row is now live. Keep input ownership and
                    // select the derived event through the stock cursor.
                    g_tour_continue =
                        ur::product::enter_modern_tour_next_event_selection(
                            g_tour_continue);
                    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                        std::fprintf(
                            stderr,
                            "UR_NEXT_EVENT SELECTING track=%u slot=%u\n",
                            g_next_event_target_track
                                ? static_cast<unsigned>(
                                      *g_next_event_target_track)
                                : 255u,
                            static_cast<unsigned>(
                                g_tour_continue.next_event_slot));
                        std::fflush(stderr);
                    }
                } else {
                    const bool results_route = g_results_tour_route_active;
                    cancel_tour_continue(
                        results_route
                            ? "UR_RESULTS_NAV TRACK_SELECT_READY"
                            : nullptr);
                    if (results_route) clear_results_navigation_route();
                }
            } else {
                product_diagnostic("UR_TOUR_RESUME ROUTE_SETTLEMENT_FAILED");
            }
            return;
        }

        // Passive stock arrival at TRACK_SELECT keeps the established safety
        // net for a saved continuation outside an explicitly routed action.
        const auto applied = ur::title::apply_tour_resume(
            saved,
            g_ram,
            0x20000,
            g_sram,
            static_cast<std::size_t>(g_sram_size));
        if (applied == ur::title::TourResumeApplyStatus::Applied) {
            (void)save_active_profile_state(
                g_profile_state->tour_continuation,
                "UR_TOUR_RESUME APPLIED");
        }
    }

    // Every settled stock result is an autosave boundary. This durably
    // publishes records/stats/medals as well as unfinished-tour flags. A
    // five-track completion carries no continuation because stock has already
    // awarded the medal and cleared the row.
    const bool track_select = g_ram[0x009F] == 0xF6;
    const bool results = g_surface == UR_UNIRACERS_RESTART_RESULTS;
    std::optional<ur::title::TourProgress> updated;
    if (track_select || results) {
        updated = ur::title::observe_tour_progress(
            g_ram,
            0x20000,
            g_sram,
            static_cast<std::size_t>(g_sram_size));
    }

    if (results && updated) {
        std::optional<ur::product::HostTourContinuation> continuation;
        if (ur::title::valid_unfinished_tour_progress(*updated)) {
            continuation = product_continuation(*updated);
        }
        (void)save_active_profile_state(
            continuation,
            continuation
                ? "UR_TOUR_RESUME CAPTURED"
                : "UR_PROFILE_AUTOSAVE RESULT");
    } else if (track_select && updated &&
               ur::title::valid_unfinished_tour_progress(*updated)) {
        const auto continuation = product_continuation(*updated);
        if (!g_profile_state->tour_continuation ||
            *g_profile_state->tour_continuation != continuation) {
            (void)save_active_profile_state(
                continuation,
                "UR_TOUR_RESUME CAPTURED");
        }
    }
}

bool restart_surface() {
    return g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ||
           g_surface == UR_UNIRACERS_RESTART_RESULTS;
}

bool request_frontend_reboot(bool require_restart_surface) {
    if (!modern_mode() ||
        (require_restart_surface && !restart_surface())) {
        product_diagnostic("UR_EXIT_FRONTEND REJECTED_UNSAFE_SURFACE");
        return false;
    }

    const int source_surface = static_cast<int>(g_surface);
    const uint32_t before_sram = current_sram_digest();
    const bool returning_from_practice = g_practice_active;

    // Practice restore must happen before requesting the session reboot because
    // the framework durably publishes the *current* cartridge SRAM as part of
    // an accepted reboot request. Make that transition transactional: if the
    // request fails, put the live disposable Practice SRAM/root and all host
    // bookkeeping back exactly so isolation is preserved and retry is safe.
    std::vector<std::uint8_t> practice_live_sram;
    std::vector<std::uint8_t> practice_profile_snapshot;
    std::string practice_live_root;
    std::string practice_original_root;
    ur::product::QuickPracticeLaunchState practice_launch;
    bool practice_race_ready_reported = false;

    if (returning_from_practice) {
        if (!g_sram ||
            g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
            product_diagnostic("UR_PRACTICE RESTORE_FAILED");
            return false;
        }
        practice_live_sram.assign(
            g_sram,
            g_sram + static_cast<std::size_t>(g_sram_size));
        practice_profile_snapshot = g_practice_sram_snapshot;
        const char* live_root = RtlSaveRoot();
        practice_live_root = live_root ? live_root : "";
        practice_original_root = g_practice_original_save_root;
        practice_launch = g_practice_launch;
        practice_race_ready_reported = g_practice_race_ready_reported;

        if (!restore_practice_profile_before_reboot()) {
            return false;
        }
    }

    // Queue a full host-owned session rebuild. The request durably publishes
    // current cartridge SRAM before it can succeed; the host consumes it only
    // after the SDL callback returns, then rebuilds the guest through the same
    // snes_free + SnesInit + RtlReadSram lifecycle used for framework session
    // replacement. No guest PC, WRAM menu byte or progression state is forged.
    if (!snesrecomp_desktop_request_session_reboot()) {
        if (returning_from_practice &&
            practice_live_sram.size() == ur::product::kStockSramBytes) {
            std::memcpy(
                g_sram,
                practice_live_sram.data(),
                ur::product::kStockSramBytes);
            RtlSetSaveRoot(
                practice_live_root.empty()
                    ? nullptr
                    : practice_live_root.c_str());
            g_practice_active = true;
            g_practice_race_ready_reported = practice_race_ready_reported;
            g_practice_launch = practice_launch;
            g_practice_sram_snapshot = std::move(practice_profile_snapshot);
            g_practice_original_save_root = std::move(practice_original_root);
            product_diagnostic("UR_PRACTICE RESTORE_ROLLED_BACK");
        }
        product_diagnostic("UR_EXIT_FRONTEND RESET_REQUEST_FAILED");
        return false;
    }

    g_options_visible = false;
    g_frontend_options_active = false;
    g_frontend_options_draw_reported = false;
    g_frontend_controls_draw_reported = false;
    g_controls_visible = false;
    g_run_data_visible = false;
    g_quit_confirm_visible = false;
    ur_modern_pause_menu_reset(&g_pause_menu);
    ur_modern_options_menu_reset(&g_options_menu);
    ur_uniracers_restart_policy_reset(&g_title_policy);
    ur::product::reset_widescreen_scene_state(&g_widescreen_scene_state);
    g_widescreen_scene = ur::product::HostSceneComposition::FixedCenter;
    g_surface = UR_UNIRACERS_RESTART_UNSUPPORTED;
    g_exit_frontend_waiting_for_main = true;
    g_exit_frontend_waiting_for_usable = false;

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_EXIT_FRONTEND REQUESTED source=%d sram=%08X practice=%d\n",
            source_surface,
            static_cast<unsigned>(before_sram),
            returning_from_practice ? 1 : 0);
        std::fflush(stderr);
    }
    return true;
}

bool exit_to_frontend() {
    return request_frontend_reboot(true);
}

bool abort_practice_route_to_frontend(const char* diagnostic) {
    if (!g_practice_active) return false;
    const bool requested = request_frontend_reboot(false);
    if (requested && diagnostic) {
        product_diagnostic(diagnostic);
    }
    return requested;
}

void clear_results_navigation_route() {
    g_results_route_pending = ur::product::ModernResultsAction::None;
    g_results_tour_route_active = false;
    g_results_route_progress.reset();
    g_results_route_profile_id.clear();
}

bool begin_pending_results_navigation_route() {
    const auto action = g_results_route_pending;
    if (action != ur::product::ModernResultsAction::NextEvent &&
        action != ur::product::ModernResultsAction::TrackSelect &&
        action != ur::product::ModernResultsAction::TourSelect) {
        return false;
    }
    if (!modern_mode() || !g_ram || g_ram[0x0313] == 0x01 ||
        g_ram[0x009F] != 0xD7 || !g_results_route_progress ||
        !g_profile_state || !g_profile_state_writable ||
        g_results_route_profile_id.empty() ||
        g_profile_state->profile_id != g_results_route_profile_id) {
        product_diagnostic("UR_RESULTS_NAV ROUTE_REJECTED_STALE");
        clear_results_navigation_route();
        return false;
    }

    const auto progress = *g_results_route_progress;
    const bool unfinished =
        ur::title::valid_unfinished_tour_progress(progress);
    if (unfinished) {
        const auto expected = product_continuation(progress);
        if (!g_profile_state->tour_continuation ||
            *g_profile_state->tour_continuation != expected ||
            !tour_continue_available()) {
            product_diagnostic("UR_RESULTS_NAV ROUTE_REJECTED_CONTEXT");
            clear_results_navigation_route();
            return false;
        }
    } else if (action == ur::product::ModernResultsAction::NextEvent) {
        product_diagnostic("UR_RESULTS_NAV NEXT_EVENT_REJECTED");
        clear_results_navigation_route();
        return false;
    }

    bool started = false;
    if (action == ur::product::ModernResultsAction::NextEvent) {
        started = begin_tour_entry(
            ur::product::ModernTourEntryIntent::NextEvent);
    } else {
        g_tour_continue = ur::product::begin_modern_tour_results_route(
            progress.tour_row,
            action == ur::product::ModernResultsAction::TourSelect,
            unfinished);
        started =
            g_tour_continue.stage != ur::product::ModernTourContinueStage::Idle;
        if (started) {
            g_tour_continue_profile_id = g_profile_state->profile_id;
            g_next_event_target_track.reset();
            g_next_event_verify_track.reset();
            g_results_tour_route_active = true;
        }
    }

    g_results_route_pending = ur::product::ModernResultsAction::None;
    if (started && action == ur::product::ModernResultsAction::NextEvent) {
        // From here the established continuation/Next Event route owns all
        // validation; the result snapshot was only the reboot handoff token.
        g_results_route_progress.reset();
        g_results_route_profile_id.clear();
    }
    if (!started) {
        product_diagnostic("UR_RESULTS_NAV ROUTE_START_FAILED");
        clear_results_navigation_route();
        return false;
    }
    product_diagnostic(
        action == ur::product::ModernResultsAction::NextEvent
            ? "UR_RESULTS_NAV NEXT_EVENT_STARTED"
            : action == ur::product::ModernResultsAction::TrackSelect
                ? "UR_RESULTS_NAV TRACK_SELECT_STARTED"
                : "UR_RESULTS_NAV TOUR_SELECT_STARTED");
    return true;
}

bool activate_results_navigation_action(
    ur::product::ModernResultsAction action) {
    refresh_results_navigation_menu();
    const auto context = current_results_navigation_context();
    if (!ur::product::modern_results_action_available(action, context)) {
        product_diagnostic("UR_RESULTS_NAV ACTION_REJECTED");
        return false;
    }

    if (action == ur::product::ModernResultsAction::Retry ||
        action == ur::product::ModernResultsAction::RepeatPractice) {
        return repeat_current_attempt();
    }
    if (action == ur::product::ModernResultsAction::Records) {
        // Re-enter the existing F8 results path owned by the completed-run
        // browser. That path already acquires pause authority before opening
        // Records and preserves the shipping F8 / physical-Y behavior.
        return ur_uniracers_product_system_key_down(SDLK_F8, 0, 0) != 0;
    }

    const auto progress = current_results_tour_progress();
    if (!progress || !g_profile_state ||
        !g_product_state.active_profile_id ||
        *g_product_state.active_profile_id != g_profile_state->profile_id ||
        !profile_snapshot_matches_live_sram(*g_profile_state)) {
        product_diagnostic("UR_RESULTS_NAV ROUTE_REJECTED_STALE");
        return false;
    }

    g_results_route_progress = *progress;
    g_results_route_profile_id = g_profile_state->profile_id;
    g_results_route_pending = action;
    if (!request_frontend_reboot(true)) {
        clear_results_navigation_route();
        return false;
    }
    return true;
}

bool handle_results_navigation(
    UrModernHostNavigationAction action) {
    if (!results_navigation_active()) return false;
    if (ur_modern_host_navigation_vertical_delta(action) != 0) {
        g_results_navigation_menu =
            ur::product::navigate_modern_results_navigation_menu(
                g_results_navigation_menu, action);
        return true;
    }
    if (!ur_modern_host_navigation_is_confirm(action)) return false;
    const auto selected = ur::product::activate_modern_results_navigation_menu(
        g_results_navigation_menu,
        current_results_navigation_context(),
        action);
    if (selected == ur::product::ModernResultsAction::None) return true;
    (void)activate_results_navigation_action(selected);
    return true;
}

bool paused() {
    return g_session && ur_modern_session_is_paused(g_session);
}

bool host_subview_visible() {
    return g_options_visible ||
           g_controls_visible ||
           g_run_data_visible ||
           g_quit_confirm_visible;
}

bool host_owns_human_player_input() {
    return modern_mode() &&
           (g_local_multiplayer_join_visible ||
            g_practice_picker.visible ||
            g_progress_overview_visible ||
            practice_routing() ||
            g_tour_action_visible ||
            results_navigation_active() ||
            onboarding_surface_active() ||
            tour_continue_routing() ||
            g_profile_menu_visible ||
            host_subview_visible());
}

UrUniracersRunData current_run_data() {
    return ur_uniracers_read_run_data(g_ram, 0x20000u);
}

uint16_t read_run_word(size_t offset) {
    return static_cast<uint16_t>(
        static_cast<uint16_t>(g_ram[offset]) |
        (static_cast<uint16_t>(g_ram[offset + 1]) << 8));
}

const char* run_record_capture_override_path() {
    if (!modern_mode()) return nullptr;
    const char* path = std::getenv("UR_RUN_RECORD_CAPTURE_PATH");
    return path && *path ? path : nullptr;
}

const char* run_ghost_acceptance_record_path() {
    if (!run_record_capture_override_path()) return nullptr;
    const char* path = std::getenv("UR_RUN_GHOST_ACCEPTANCE_RECORD");
    return path && *path ? path : nullptr;
}

ur::product::CompletedRunGhostTarget active_run_ghost_target() {
    if (run_record_capture_override_path()) {
        const char* value = std::getenv("UR_RUN_GHOST_ACCEPTANCE_TARGET");
        if (value && *value) {
            const auto parsed =
                ur::product::parse_completed_run_ghost_target(value);
            if (parsed) return *parsed;
        }
        return ur::product::CompletedRunGhostTarget::Off;
    }
    return g_profile_state
        ? g_profile_state->ghost_target
        : ur::product::CompletedRunGhostTarget::Off;
}

bool run_record_capture_enabled() {
    return modern_mode() && !g_practice_active &&
           g_widescreen_scene_state.race_mode ==
               ur::product::HostRacePresentationMode::OnePlayer;
}

bool multiplayer_participant_session_ready() {
    return g_local_multiplayer_participants_ready &&
           g_local_multiplayer_participants.player1.has_value() &&
           g_local_multiplayer_participants.player2.has_value();
}

std::string default_multiplayer_run_directory() {
    if (!modern_mode()) return {};
    if (const char* override_path =
            std::getenv("UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY")) {
        if (*override_path) return override_path;
    }
    return product_user_data_path("multiplayer-runs");
}

void reset_multiplayer_run_capture() {
    if (g_multiplayer_run_capture.capturing()) {
        g_multiplayer_run_capture.abort_attempt();
    }
    g_multiplayer_capture_player1.reset();
    g_multiplayer_capture_player2.reset();
    g_multiplayer_capture_course = {};
    g_multiplayer_capture_origin_frame = 0;
}

std::string default_run_record_directory() {
    if (!run_record_capture_enabled()) return {};
    ensure_product_state();

    std::string path = product_user_data_path("runs");
    if (path.empty()) return {};
    path += "/";
    path += g_product_state.active_profile_id.value_or("default");
    return path;
}

ur::product::RunPlaybackTarget playback_target_for(
    const ur::product::RunRecordProvenance& provenance) {
    return {
        provenance.game_id,
        provenance.rom_sha256,
        provenance.build_compat_id,
        provenance.course_id,
        provenance.mode,
    };
}

void refresh_run_ghosts(
    const ur::product::RunRecordProvenance& provenance) {
    g_run_ghosts.clear();

    // Acceptance capture writes explicit artifacts outside the ordinary
    // profile catalog. An optional exact source record may be bound only when
    // the capture override is active, keeping this plumbing isolated from
    // ordinary profile ghost state.
    if (run_record_capture_override_path()) {
        const char* source_path = run_ghost_acceptance_record_path();
        if (!source_path) return;
        const auto loaded =
            ur::product::load_completed_run_record_file(source_path);
        if (!loaded.loaded()) return;
        const auto target = playback_target_for(provenance);
        g_run_ghosts.bind(
            {{std::string(source_path), *loaded.record}}, target);
        return;
    }

    const std::string directory = default_run_record_directory();
    if (directory.empty()) return;

    const auto target = playback_target_for(provenance);
    const auto records =
        ur::product::load_compatible_run_records(directory, target);
    g_run_ghosts.bind(records, target);

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        const auto* previous = g_run_ghosts.record(
            ur::product::CompletedRunGhostKind::Previous);
        const auto* personal_best = g_run_ghosts.record(
            ur::product::CompletedRunGhostKind::PersonalBest);
        std::fprintf(
            stderr,
            "UR_RUN_GHOSTS BOUND compatible=%zu previous_ticks60=%llu pb_ticks60=%llu\n",
            g_run_ghosts.compatible_count(),
            previous
                ? static_cast<unsigned long long>(previous->elapsed_ticks60)
                : 0ull,
            personal_best
                ? static_cast<unsigned long long>(personal_best->elapsed_ticks60)
                : 0ull);
        std::fflush(stderr);
    }
}

void refresh_run_ghost_playback_trace() {
    g_run_ghost_playback_trace.reset();
    g_run_ghost_presentation_frame.reset();
    if (!modern_mode()) return;

    const auto ghost_target = active_run_ghost_target();
    const auto selection = ur::product::select_completed_run_ghost_target(
        g_run_ghosts, ghost_target);
    if (!selection.active() || !selection.kind) return;

    const auto loaded = ur::product::load_selected_completed_run_ghost_trace(
        g_run_ghosts, *selection.kind);
    if (!loaded.loaded()) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_RUN_GHOST_TRACE PLAYBACK_UNAVAILABLE target=%s detail=%s\n",
                ur::product::completed_run_ghost_target_name(
                    ghost_target),
                loaded.detail.c_str());
            std::fflush(stderr);
        }
        return;
    }

    g_run_ghost_playback_trace = *loaded.trace;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RUN_GHOST_TRACE PLAYBACK_BOUND target=%s samples=%zu\n",
            ur::product::completed_run_ghost_target_name(
                ghost_target),
            g_run_ghost_playback_trace->samples.size());
        std::fflush(stderr);
    }
}

void resolve_run_ghost_presentation_frame(std::uint64_t race_frame) {
    g_run_ghost_presentation_frame.reset();
    if (!g_run_ghost_playback_trace || !modern_mode()) return;

    const auto projection =
        ur::product::read_completed_run_ghost_projection_context(
            g_ram, 0x20000u);
    if (!projection) return;

    g_run_ghost_presentation_frame =
        ur::product::resolve_completed_run_ghost_presentation_frame(
            *g_run_ghost_playback_trace, race_frame, *projection);
}

bool begin_run_record_capture(uint64_t host_frame) {
    g_run_timing_supported = false;
    g_run_timing_last_split.reset();
    g_run_timing_race_diag_reported = false;
    g_run_timing_results_diag_reported = false;
    if (!run_record_capture_enabled()) return false;

    snesrecomp_desktop_arm_relative_input(host_frame);

    const UrUniracersCourseIdentity course =
        ur_uniracers_identify_course(g_ram + 0x10000u, 0x10000u);
    if (!course.valid) {
        product_diagnostic("UR_RUN_RECORD COURSE_IDENTITY_REJECTED");
        return false;
    }
    const int tour_slot = ((course.course_index - 1) % 5) + 1;
    if (tour_slot != 1 && tour_slot != 4) {
        product_diagnostic("UR_RUN_RECORD NON_RACE_TRACK_INERT");
        return false;
    }

    char course_id[32];
    std::snprintf(course_id, sizeof(course_id), "course:%02d", course.course_index);
    ur::product::RunRecordProvenance provenance{
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1",
        course_id,
        "race-1p",
    };
    if (!g_run_capture.begin_attempt(provenance)) {
        product_diagnostic("UR_RUN_RECORD BEGIN_REJECTED");
        return false;
    }
    refresh_run_ghosts(provenance);
    refresh_run_ghost_playback_trace();
    g_run_ghost_draw_reported = false;
    (void)g_run_ghost_trace_capture.begin_attempt();
    g_run_capture_origin_frame = host_frame;
    g_run_capture_checkpoint = read_run_word(0x1199u);
    g_run_timing_supported = true;
    return true;
}

bool begin_multiplayer_run_record_capture(std::uint64_t host_frame) {
    reset_multiplayer_run_capture();

    const UrUniracersCourseIdentity course =
        ur_uniracers_identify_course(g_ram + 0x10000u, 0x10000u);
    if (!course.valid) {
        product_diagnostic("UR_MULTIPLAYER_MATCH COURSE_IDENTITY_REJECTED");
        return false;
    }

    const int tour_slot = ((course.course_index - 1) % 5) + 1;
    const bool ordinary_race_course = tour_slot == 1 || tour_slot == 4;
    const auto plan = ur::product::resolve_run_record_capture_plan(
        modern_mode(),
        g_practice_active,
        g_widescreen_scene_state.race_mode,
        multiplayer_participant_session_ready(),
        ordinary_race_course);
    if (!plan.enabled() ||
        plan.kind != ur::product::RunRecordCaptureKind::OrdinaryTwoPlayerRace ||
        !plan.require_match_record) {
        if (!ordinary_race_course) {
            product_diagnostic("UR_MULTIPLAYER_MATCH NON_RACE_TRACK_INERT");
        }
        return false;
    }

    char course_id[32];
    std::snprintf(
        course_id, sizeof(course_id), "course:%02d", course.course_index);
    ur::product::RunRecordProvenance provenance{
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1",
        course_id,
        std::string(plan.provenance_mode),
    };
    if (!g_multiplayer_run_capture.begin_attempt(provenance)) {
        product_diagnostic("UR_MULTIPLAYER_MATCH BEGIN_REJECTED");
        return false;
    }

    g_multiplayer_capture_player1 =
        *g_local_multiplayer_participants.player1;
    g_multiplayer_capture_player2 =
        *g_local_multiplayer_participants.player2;
    g_multiplayer_capture_course = course;
    g_multiplayer_capture_origin_frame = host_frame;
    product_diagnostic("UR_MULTIPLAYER_MATCH CAPTURE_STARTED");
    return true;
}

void observe_run_ghost_trace_sample() {
    if (!g_run_capture.capturing() ||
        !g_run_ghost_trace_capture.capturing() ||
        g_run_capture.captured_frames() == 0) {
        return;
    }

    const std::uint64_t race_frame =
        g_run_capture.captured_frames() - 1u;
    const auto sample =
        ur::product::read_completed_run_ghost_world_sample(
            g_ram, 0x20000u, race_frame);
    if (!sample || !g_run_ghost_trace_capture.observe(*sample)) {
        g_run_ghost_trace_capture.abort_attempt();
        product_diagnostic("UR_RUN_GHOST_TRACE SAMPLE_DISABLED");
    }
}

// Sends a policy-approved pulse to the controller in the P1 framework seat.
// SDL owns the device; a missing or rumble-less device simply does nothing.
bool rumble_p1_controller(const ur::product::HapticPulse& pulse) {
    if (!g_controller_hotplug.seats[0].connected) return false;
    const auto id = static_cast<SDL_JoystickID>(
        g_controller_hotplug.seats[0].source_id);
#if SNESRECOMP_SDL3
    if (SDL_Gamepad* pad = SDL_GetGamepadFromID(id)) {
        return SDL_RumbleGamepad(
            pad, pulse.low_frequency, pulse.high_frequency,
            pulse.duration_ms);
    }
    if (SDL_Joystick* joystick = SDL_GetJoystickFromID(id)) {
        return SDL_RumbleJoystick(
            joystick, pulse.low_frequency, pulse.high_frequency,
            pulse.duration_ms);
    }
#else
    if (SDL_GameController* pad = SDL_GameControllerFromInstanceID(id)) {
        return SDL_GameControllerRumble(
                   pad, pulse.low_frequency, pulse.high_frequency,
                   pulse.duration_ms) == 0;
    }
    if (SDL_Joystick* joystick = SDL_JoystickFromInstanceID(id)) {
        return SDL_JoystickRumble(
                   joystick, pulse.low_frequency, pulse.high_frequency,
                   pulse.duration_ms) == 0;
    }
#endif
    return false;
}

void emit_haptic_event(ur::product::HapticEvent event) {
    const ur::product::HapticContext context{
        modern_mode() ? ur::product::ExecutionMode::Modern
                      : ur::product::ExecutionMode::Authentic,
        g_run_timing_supported && g_run_capture.capturing(),
        g_controller_hotplug.seats[0].connected,
        paused(),
    };
    const auto pulse = ur::product::haptic_pulse_for(
        g_product_state.settings, context, event);
    if (!pulse) return;
    const bool sent = rumble_p1_controller(*pulse);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_HAPTIC PULSE event=%s low=%u high=%u ms=%u sent=%d\n",
            event == ur::product::HapticEvent::Finish ? "finish"
                                                      : "checkpoint",
            static_cast<unsigned>(pulse->low_frequency),
            static_cast<unsigned>(pulse->high_frequency),
            static_cast<unsigned>(pulse->duration_ms),
            sent ? 1 : 0);
        std::fflush(stderr);
    }
}

void observe_run_record_split() {
    if (!g_run_capture.capturing()) return;
    const uint16_t checkpoint = read_run_word(0x1199u);
    if (checkpoint == g_run_capture_checkpoint) return;

    const int64_t ticks60 = ur_uniracers_run_data_ticks60(current_run_data());
    if (ticks60 >= 0) {
        const std::string id = "checkpoint-" + std::to_string(checkpoint);
        (void)g_run_capture.observe_split(
            id, static_cast<uint64_t>(ticks60));
        emit_haptic_event(ur::product::HapticEvent::Checkpoint);
        g_run_timing_last_split.reset();
        const auto* personal_best = g_run_ghosts.record(
            ur::product::CompletedRunGhostKind::PersonalBest);
        if (personal_best) {
            g_run_timing_last_split =
                ur::product::present_run_split_delta(
                    *personal_best,
                    id,
                    static_cast<uint64_t>(ticks60));
        }
        if (std::getenv("UR_TIMING_HUD_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_TIMING_HUD SPLIT id=%s current_ticks60=%lld delta=%s\n",
                id.c_str(),
                static_cast<long long>(ticks60),
                g_run_timing_last_split
                    ? g_run_timing_last_split->delta_text.c_str() : "--");
            std::fflush(stderr);
        }
    }
    g_run_capture_checkpoint = checkpoint;
}

void complete_multiplayer_run_record_capture() {
    if (!g_multiplayer_run_capture.capturing()) return;

    if (!g_local_multiplayer_participants_ready ||
        !g_multiplayer_capture_player1 ||
        !g_multiplayer_capture_player2 ||
        !g_multiplayer_capture_course.valid ||
        !g_sram || g_sram_size <= 0) {
        product_diagnostic("UR_MULTIPLAYER_MATCH SESSION_IDENTITY_LOST");
        reset_multiplayer_run_capture();
        return;
    }

    const auto observed =
        ur::title::observe_ordinary_two_player_race_result(
            true,
            g_ram,
            0x20000u,
            g_sram,
            static_cast<std::size_t>(g_sram_size));
    if (!observed) {
        // 0xF9 appears before the stock SRAM result words settle. Keep the
        // in-flight capture armed until the title observer sees a valid pair.
        return;
    }

    const auto context = ur::product::bind_local_multiplayer_match_context(
        *observed,
        *g_multiplayer_capture_player1,
        *g_multiplayer_capture_player2,
        g_multiplayer_capture_course);
    if (!context.bound()) {
        product_diagnostic("UR_MULTIPLAYER_MATCH PARTICIPANT_BIND_REJECTED");
        reset_multiplayer_run_capture();
        return;
    }

    const std::uint64_t carrier_ticks60 =
        ur::product::ordinary_two_player_carrier_elapsed_ticks60(*observed);
    const auto run =
        g_multiplayer_run_capture.complete(carrier_ticks60);
    if (!run) {
        product_diagnostic("UR_MULTIPLAYER_MATCH FINALIZE_REJECTED");
        reset_multiplayer_run_capture();
        return;
    }

    const auto match =
        ur::product::make_multiplayer_match_record(*run, *context.context);
    if (!match) {
        product_diagnostic("UR_MULTIPLAYER_MATCH METADATA_REJECTED");
        reset_multiplayer_run_capture();
        return;
    }

    const std::string directory = default_multiplayer_run_directory();
    std::string stored_path;
    std::string detail;
    if (directory.empty() ||
        !ur::product::append_multiplayer_match_pair(
            directory, *run, *match, &stored_path, &detail)) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_MULTIPLAYER_MATCH STORE_FAILED detail=%s\n",
                detail.c_str());
            std::fflush(stderr);
        }
        reset_multiplayer_run_capture();
        return;
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_MULTIPLAYER_MATCH CAPTURED path=%s course=%s p1=%s p2=%s outcome=%u origin_frame=%llu inputs=%zu\n",
            stored_path.c_str(),
            match->context.course_id.c_str(),
            match->context.match.player1.profile_id.c_str(),
            match->context.match.player2.profile_id.c_str(),
            static_cast<unsigned>(match->context.match.result.outcome),
            static_cast<unsigned long long>(
                g_multiplayer_capture_origin_frame),
            run->inputs.size());
        std::fflush(stderr);
    }

    reset_multiplayer_run_capture();
    if (std::getenv("UR_MULTIPLAYER_MATCH_ACCEPTANCE")) {
        if (request_desktop_quit()) {
            product_diagnostic("UR_MULTIPLAYER_MATCH ACCEPTANCE_COMPLETE");
        } else {
            product_diagnostic("UR_MULTIPLAYER_MATCH ACCEPTANCE_QUIT_REJECTED");
        }
    }
}

void complete_run_record_capture() {
    if (!g_run_capture.capturing()) return;

    const int64_t ticks60 = ur_uniracers_run_data_ticks60(current_run_data());
    if (ticks60 < 0) {
        product_diagnostic("UR_RUN_RECORD FINISH_TIMER_REJECTED");
        g_run_capture.abort_attempt();
        g_run_ghost_trace_capture.abort_attempt();
        return;
    }

    // The pulse needs the capture still active to prove 1P split ownership.
    emit_haptic_event(ur::product::HapticEvent::Finish);
    (void)g_run_capture.observe_split(
        "finish", static_cast<uint64_t>(ticks60));
    const auto record =
        g_run_capture.complete(static_cast<uint64_t>(ticks60));
    if (!record) {
        product_diagnostic("UR_RUN_RECORD FINALIZE_REJECTED");
        g_run_ghost_trace_capture.abort_attempt();
        return;
    }

    const auto ghost_trace =
        g_run_ghost_trace_capture.complete(*record);

    std::string detail;
    std::string stored_path;
    bool replay_written = false;
    if (const char* override_path = run_record_capture_override_path()) {
        stored_path = override_path;
        if (!ur::product::save_completed_run_record_file(
                stored_path, *record, &detail)) {
            if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                std::fprintf(
                    stderr, "UR_RUN_RECORD SAVE_FAILED detail=%s\n",
                    detail.c_str());
                std::fflush(stderr);
            }
            return;
        }

        std::ofstream replay(
            stored_path + ".input", std::ios::binary | std::ios::trunc);
        const std::string replay_text =
            ur::product::encode_completed_run_input_file(*record);
        replay.write(
            replay_text.data(),
            static_cast<std::streamsize>(replay_text.size()));
        replay.close();
        replay_written = static_cast<bool>(replay);
    } else {
        const std::string directory = default_run_record_directory();
        if (directory.empty() ||
            !ur::product::append_completed_run_record(
                directory, *record, &stored_path, &detail)) {
            if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                std::fprintf(
                    stderr, "UR_RUN_RECORD STORE_FAILED detail=%s\n",
                    detail.c_str());
                std::fflush(stderr);
            }
            return;
        }
    }

    bool ghost_trace_written = false;
    if (ghost_trace) {
        std::string trace_detail;
        ghost_trace_written =
            ur::product::save_completed_run_ghost_trace_file(
                stored_path + ".urghost", *ghost_trace, &trace_detail);
        if (!ghost_trace_written && std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_RUN_GHOST_TRACE SAVE_FAILED detail=%s\n",
                trace_detail.c_str());
            std::fflush(stderr);
        }
    }

    std::fprintf(
        stderr,
        "UR_RUN_RECORD CAPTURED path=%s course=%s elapsed_ticks60=%llu origin_frame=%llu inputs=%zu splits=%zu replay_input=%d ghost_trace=%d\n",
        stored_path.c_str(),
        record->provenance.course_id.c_str(),
        static_cast<unsigned long long>(record->elapsed_ticks60),
        static_cast<unsigned long long>(g_run_capture_origin_frame),
        record->inputs.size(),
        record->splits.size(),
        replay_written ? 1 : 0,
        ghost_trace_written ? 1 : 0);
    std::fflush(stderr);
}

void rearm_run_capture_after_retry() {
    if (!g_run_capture.capturing()) return;
    g_run_capture.abort_attempt();
    g_run_timing_supported = false;
    g_run_timing_last_split.reset();
    g_run_ghost_trace_capture.abort_attempt();
    g_run_ghosts.clear();
    g_run_ghost_playback_trace.reset();
    g_run_ghost_presentation_frame.reset();
    g_run_capture_previous_active = false;
    product_diagnostic("UR_RUN_RECORD RETRY_REARMED");
}

ur::product::ModernControlsBindingAuthority live_controls_authority() {
    return {
        [](int button, int scancode) {
            keybinds_set_button(
                1, button, static_cast<SDL_Scancode>(scancode));
        },
        []() { keybinds_reset_player(1); },
        []() { keybinds_save(); },
    };
}

void diagnose_controls_bindings() {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS")) return;
    std::array<std::string, 12> labels{};
    for (int i = 0; i < ur::product::modern_control_binding_count(); ++i) {
        labels[static_cast<std::size_t>(i)] =
            uppercase_keybind_label(keybinds_get_button(1, i));
    }
    std::fprintf(
        stderr,
        "UR_CONTROLS BINDINGS a=%s b=%s x=%s y=%s l=%s r=%s "
        "start=%s select=%s up=%s down=%s left=%s right=%s\n",
        labels[0].c_str(), labels[1].c_str(), labels[2].c_str(),
        labels[3].c_str(), labels[4].c_str(), labels[5].c_str(),
        labels[6].c_str(), labels[7].c_str(), labels[8].c_str(),
        labels[9].c_str(), labels[10].c_str(), labels[11].c_str());
    std::fflush(stderr);
}

bool apply_live_controls_command(
    const ur::product::ModernControlsCommand& command) {
    const bool applied = ur::product::apply_modern_controls_command(
        command, live_controls_authority());
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS") && command.actionable()) {
        std::fprintf(
            stderr,
            "UR_CONTROLS command=%d binding=%d scancode=%d applied=%d\n",
            static_cast<int>(command.kind),
            static_cast<int>(command.binding),
            command.key_scancode,
            applied ? 1 : 0);
        std::fflush(stderr);
    }
    if (applied) diagnose_controls_bindings();
    return applied;
}

bool handle_controls_action(ur::product::ModernControlsAction action) {
    if (!modern_mode() || !g_controls_visible) return false;
    auto command = ur::product::modern_controls_handle_action(
        &g_controls_rebind, action);
    if (command.kind == ur::product::ModernControlsCommandKind::Close) {
        g_controls_visible = false;
        if (g_frontend_options_active) {
            // Controls is a child of the same frontend Options surface.
            // Return to its existing selected row, never to guest input.
            g_options_visible = true;
            g_frontend_options_draw_reported = false;
            g_frontend_controls_draw_reported = false;
            product_diagnostic("UR_FRONTEND_CONTROLS RETURNED_OPTIONS");
        } else {
            product_diagnostic("UR_PAUSE_CONTROLS CLOSED");
        }
        return true;
    }
    if (command.kind == ur::product::ModernControlsCommandKind::ClearBinding ||
        command.kind == ur::product::ModernControlsCommandKind::ResetPlayer) {
        (void)apply_live_controls_command(command);
    }
    return true;
}

bool handle_controls_key(int key) {
    if (!modern_mode() || !g_controls_visible) return false;

    if (g_controls_rebind.capturing) {
        if (key == SDLK_ESCAPE) {
            (void)ur::product::modern_controls_handle_action(
                &g_controls_rebind, ur::product::ModernControlsAction::Back);
            product_diagnostic("UR_CONTROLS CAPTURE_CANCELLED");
            return true;
        }
        const SDL_Scancode scancode = snesrecomp_sdl_scancode_from_key(
            static_cast<SDL_Keycode>(key));
        auto command = ur::product::modern_controls_capture_key(
            &g_controls_rebind, static_cast<int>(scancode));
        if (!command.actionable()) return true;
        if (!apply_live_controls_command(command)) {
            g_controls_rebind.capturing = true;
            product_diagnostic("UR_CONTROLS CAPTURE_APPLY_FAILED");
        }
        return true;
    }

    if (key == SDLK_UP) {
        return handle_controls_action(ur::product::ModernControlsAction::Previous);
    }
    if (key == SDLK_DOWN) {
        return handle_controls_action(ur::product::ModernControlsAction::Next);
    }
    if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
        return handle_controls_action(ur::product::ModernControlsAction::Confirm);
    }
    if (key == SDLK_DELETE || key == SDLK_BACKSPACE) {
        return handle_controls_action(ur::product::ModernControlsAction::Clear);
    }
    if (key == SDLK_r) {
        return handle_controls_action(ur::product::ModernControlsAction::Reset);
    }
    if (key == SDLK_ESCAPE) {
        return handle_controls_action(ur::product::ModernControlsAction::Back);
    }
    return true;
}

void close_host_subview() {
    if (g_options_visible) {
        g_options_visible = false;
        if (g_frontend_options_active) {
            g_frontend_options_active = false;
            g_frontend_options_draw_reported = false;
            product_diagnostic("UR_FRONTEND_OPTIONS CLOSED");
        } else {
            product_diagnostic("UR_PAUSE_OPTIONS CLOSED");
        }
    }
    if (g_controls_visible) {
        g_controls_rebind.capturing = false;
        g_controls_visible = false;
        if (g_frontend_options_active) {
            g_frontend_options_active = false;
            g_frontend_options_draw_reported = false;
            g_frontend_controls_draw_reported = false;
            product_diagnostic("UR_FRONTEND_CONTROLS CLOSED");
        } else {
            product_diagnostic("UR_PAUSE_CONTROLS CLOSED");
        }
    }
    if (g_run_data_visible) {
        g_run_data_visible = false;
        product_diagnostic("UR_PAUSE_RUN_DATA CLOSED");
    }
    if (g_quit_confirm_visible) {
        g_quit_confirm_visible = false;
        product_diagnostic("UR_PAUSE_QUIT CANCELLED");
    }
}

// Reuse the shipping Options model, settings authority and existing input
// surface from the settled stock main menu. This never creates a pause or a
// second persisted settings store, and cannot interrupt stock routing.
bool open_frontend_options() {
    if (!modern_mode() || !g_ram || paused() ||
        g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01 ||
        g_options_visible || g_controls_visible || g_run_data_visible ||
        g_quit_confirm_visible || g_profile_menu_visible ||
        g_progress_overview_visible || g_practice_picker.visible ||
        g_practice_active || g_tour_action_visible ||
        g_local_multiplayer_join_visible || onboarding_surface_active() ||
        results_navigation_active() || tour_continue_routing() ||
        practice_routing() || g_exit_frontend_waiting_for_main ||
        g_exit_frontend_waiting_for_usable) return false;
    ur_modern_options_menu_reset(&g_options_menu);
    g_frontend_options_active = true;
    g_frontend_options_draw_reported = false;
    g_options_visible = true;
    product_diagnostic("UR_FRONTEND_OPTIONS OPENED");
    return true;
}

bool open_frontend_controls() {
    if (!g_frontend_options_active) {
        if (!open_frontend_options()) return false;
    }
    if (!g_options_visible || g_controls_visible) return false;
    g_options_visible = false;
    g_controls_rebind = {};
    g_controls_visible = true;
    g_frontend_controls_draw_reported = false;
    diagnose_controls_bindings();
    product_diagnostic("UR_FRONTEND_CONTROLS OPENED");
    return true;
}

bool request_desktop_quit() {
    SDL_Event event{};
    event.type = SDL_QUIT;
    if (SDL_PushEvent(&event) != 1) {
        product_diagnostic("UR_PAUSE_QUIT REQUEST_FAILED");
        return false;
    }
    product_diagnostic("UR_PAUSE_QUIT REQUESTED");
    return true;
}

void maybe_run_exit_frontend_acceptance() {
    if (g_exit_frontend_acceptance_fired || !modern_mode() || !g_session) return;
    const char* mode = std::getenv("UR_EXIT_FRONTEND_ACCEPTANCE");
    if (!mode || !*mode) return;

    const bool wants_active =
        std::strcmp(mode, "active") == 0 &&
        g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE;
    const bool wants_results =
        std::strcmp(mode, "results") == 0 &&
        g_surface == UR_UNIRACERS_RESTART_RESULTS;
    if (!wants_active && !wants_results) {
        g_exit_frontend_acceptance_surface_frames = 0;
        return;
    }

    // The script must first observe and retain the same semantic surface.
    // Waiting 90 guest frames keeps this CI-only trigger behind the script's
    // 60-frame settled active-race checkpoint and comfortably behind the
    // results dump, rather than rebooting underneath their prerequisite waits.
    if (++g_exit_frontend_acceptance_surface_frames < 90) return;

    g_exit_frontend_acceptance_fired = true;
    const UrModernSessionResult pause_result = ur_modern_session_pause(g_session);
    const UrModernSessionResult exit_result =
        ur_modern_session_exit_to_frontend(g_session);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_EXIT_FRONTEND ACCEPTANCE_TRIGGER surface=%d pause=%d exit=%d\n",
            static_cast<int>(g_surface),
            static_cast<int>(pause_result),
            static_cast<int>(exit_result));
        std::fflush(stderr);
    }
}

bool activate_pause_selection();

void maybe_run_pause_records_acceptance() {
    if (g_pause_records_acceptance_fired || !modern_mode() || !g_session ||
        !std::getenv("UR_PAUSE_RECORDS_ACCEPTANCE")) {
        return;
    }
    if (g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE || paused()) {
        g_pause_records_acceptance_surface_frames = 0;
        return;
    }
    if (++g_pause_records_acceptance_surface_frames < 90) return;

    g_pause_records_acceptance_fired = true;
    const int pause_handled =
        ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    const int restart = ur_modern_session_restart_available(g_session);
    ur_modern_pause_menu_reset(&g_pause_menu);

    int moves = 0;
    while (moves < 10 &&
           ur_modern_pause_menu_selected(&g_pause_menu, restart) !=
               UR_MODERN_PAUSE_RECORDS) {
        ur_modern_pause_menu_move(&g_pause_menu, 1, restart);
        ++moves;
    }
    const bool selected =
        ur_modern_pause_menu_selected(&g_pause_menu, restart) ==
        UR_MODERN_PAUSE_RECORDS;
    const bool opened = selected && activate_pause_selection();

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_PAUSE_RECORDS ACCEPTANCE_TRIGGER pause=%d restart=%d moves=%d selected=%d opened=%d\n",
            pause_handled,
            restart,
            moves,
            selected ? 1 : 0,
            opened ? 1 : 0);
        std::fflush(stderr);
    }

    SDL_Event event{};
    event.type = SDL_QUIT;
    (void)SDL_PushEvent(&event);
}

void apply_focus_pause_policy() {
    if (!g_session || !restart_surface()) return;
    const bool focused = SDL_GetKeyboardFocus() != nullptr;
    if (!ur::product::should_pause_on_focus_loss(
            modern_mode() ? ur::product::ExecutionMode::Modern
                          : ur::product::ExecutionMode::Authentic,
            g_product_state.settings,
            focused,
            paused())) {
        return;
    }
    const UrModernSessionResult result = ur_modern_session_pause(g_session);
    if (result == UR_MODERN_SESSION_APPLIED &&
        std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_FOCUS_PAUSE APPLIED focus=0 setting=1 modern=1\n");
        std::fflush(stderr);
    }
}

std::string controller_display_name(std::uint64_t source_id) {
    const auto id = static_cast<SDL_JoystickID>(source_id);
    const char* raw = nullptr;
    if (SDL_GameController* pad = SDL_GameControllerFromInstanceID(id)) {
        raw = SDL_GameControllerName(pad);
    }
    if (!raw) {
        if (SDL_Joystick* joystick = SDL_JoystickFromInstanceID(id)) {
            raw = SDL_JoystickName(joystick);
        }
    }
    // The overlay font is uppercase ASCII; keep the label short enough for
    // the Controls panel and never trust device-provided bytes verbatim.
    std::string out;
    if (raw) {
        for (const char* p = raw; *p && out.size() < 18u; ++p) {
            char ch = *p;
            if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
            const bool keep = (ch >= 'A' && ch <= 'Z') ||
                              (ch >= '0' && ch <= '9') || ch == '-';
            if (keep) {
                out.push_back(ch);
            } else if (!out.empty() && out.back() != ' ') {
                out.push_back(' ');
            }
        }
    }
    while (!out.empty() && out.back() == ' ') out.pop_back();
    return out.empty() ? std::string("CONTROLLER") : out;
}

void apply_controller_disconnect_pause() {
    if (!g_session) return;
    const auto decision = ur::product::controller_hotplug_take_pause(
        g_controller_hotplug,
        modern_mode() ? ur::product::ExecutionMode::Modern
                      : ur::product::ExecutionMode::Authentic,
        restart_surface(),
        paused());
    g_controller_hotplug = decision.state;
    if (decision.pause &&
        ur_modern_session_pause(g_session) == UR_MODERN_SESSION_APPLIED) {
        product_diagnostic("UR_CONTROLLER DISCONNECT_PAUSED");
    }
    // Notices explain why the game paused; they retire once play resumes.
    if (!paused() &&
        ur::product::controller_hotplug_any_notice(g_controller_hotplug)) {
        g_controller_hotplug =
            ur::product::controller_hotplug_clear_notices(g_controller_hotplug);
    }
}

#if SNESRECOMP_SDL3
SDL_JoystickID g_controller_hotplug_acceptance_pad_id;
SDL_Joystick* g_controller_hotplug_acceptance_pad;

bool SDLCALL record_acceptance_pad_rumble(
    void*, Uint16 low_frequency, Uint16 high_frequency) {
    // SDL also delivers a zero-strength stop when a pulse expires.
    if (low_frequency == 0 && high_frequency == 0) return true;
    ++g_haptic_acceptance_device_rumbles;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_HAPTIC_ACCEPTANCE DEVICE_RUMBLE low=%u high=%u count=%u\n",
            static_cast<unsigned>(low_frequency),
            static_cast<unsigned>(high_frequency),
            g_haptic_acceptance_device_rumbles);
        std::fflush(stderr);
    }
    return true;
}

bool attach_controller_hotplug_acceptance_pad(bool with_rumble = false) {
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
    desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
    desc.name = "UR hotplug acceptance pad";
    if (with_rumble) desc.Rumble = &record_acceptance_pad_rumble;
    g_controller_hotplug_acceptance_pad_id = SDL_AttachVirtualJoystick(&desc);
    g_controller_hotplug_acceptance_pad =
        g_controller_hotplug_acceptance_pad_id
            ? SDL_OpenJoystick(g_controller_hotplug_acceptance_pad_id)
            : nullptr;
    return g_controller_hotplug_acceptance_pad != nullptr;
}

void detach_controller_hotplug_acceptance_pad() {
    if (g_controller_hotplug_acceptance_pad) {
        SDL_CloseJoystick(g_controller_hotplug_acceptance_pad);
        g_controller_hotplug_acceptance_pad = nullptr;
    }
    if (g_controller_hotplug_acceptance_pad_id) {
        (void)SDL_DetachVirtualJoystick(g_controller_hotplug_acceptance_pad_id);
        g_controller_hotplug_acceptance_pad_id = 0;
    }
}

enum class JoinAcceptanceStepKind : std::uint8_t { Press, Detach, Attach };
struct LocalMultiplayerJoinAcceptanceStep {
    int pad;
    SDL_GamepadButton button;
    JoinAcceptanceStepKind kind;
};
constexpr auto kJoinPress = JoinAcceptanceStepKind::Press;
// P2 first tries P1's profile (refused as a duplicate), then moves right and
// confirms a distinct profile.
constexpr LocalMultiplayerJoinAcceptanceStep kLocalMultiplayerJoinSteps[] = {
    {0, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P1 joins
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P2 joins
    {0, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P1 confirms profile 1
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P2 tries the same one
    {1, SDL_GAMEPAD_BUTTON_DPAD_RIGHT, kJoinPress},  // P2 moves on
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P2 confirms it
};
// P2's pad is unplugged after joining, which must block the session; a pad
// plugged back in (a new SDL instance) leaves the stale seat with B, joins
// again and confirms; the seat's profile cursor survives the unplug.
constexpr LocalMultiplayerJoinAcceptanceStep kLocalMultiplayerDisconnectSteps[] = {
    {0, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P1 joins
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P2 joins
    {0, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // P1 confirms profile 1
    {1, SDL_GAMEPAD_BUTTON_DPAD_RIGHT, kJoinPress},  // P2 moves to profile 2
    {1, SDL_GAMEPAD_BUTTON_SOUTH, JoinAcceptanceStepKind::Detach},
    {1, SDL_GAMEPAD_BUTTON_SOUTH, JoinAcceptanceStepKind::Attach},
    {1, SDL_GAMEPAD_BUTTON_EAST, kJoinPress},        // leave the stale seat
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // join again
    {1, SDL_GAMEPAD_BUTTON_SOUTH, kJoinPress},       // confirm the retained
                                                     // profile-2 cursor
};
std::array<SDL_JoystickID, 2> g_local_multiplayer_acceptance_pad_ids{};
std::array<SDL_Joystick*, 2> g_local_multiplayer_acceptance_pads{};
int g_local_multiplayer_acceptance_stage = -1;
unsigned g_local_multiplayer_acceptance_frames;

bool attach_local_multiplayer_acceptance_pad(std::size_t i) {
    constexpr const char* kNames[2] = {"UR JOIN PAD ONE", "UR JOIN PAD TWO"};
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
    desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
    desc.name = kNames[i];
    // Distinct USB identities, as two different physical pads would have;
    // SDL derives a gamepad's mapping (and name) from its GUID.
    desc.vendor_id = 0x1209;
    desc.product_id = static_cast<Uint16>(0x5501 + i);
    g_local_multiplayer_acceptance_pad_ids[i] = SDL_AttachVirtualJoystick(&desc);
    g_local_multiplayer_acceptance_pads[i] =
        g_local_multiplayer_acceptance_pad_ids[i]
            ? SDL_OpenJoystick(g_local_multiplayer_acceptance_pad_ids[i])
            : nullptr;
    return g_local_multiplayer_acceptance_pads[i] != nullptr;
}

void detach_local_multiplayer_acceptance_pad(std::size_t i) {
    if (g_local_multiplayer_acceptance_pads[i]) {
        SDL_CloseJoystick(g_local_multiplayer_acceptance_pads[i]);
        g_local_multiplayer_acceptance_pads[i] = nullptr;
    }
    if (g_local_multiplayer_acceptance_pad_ids[i]) {
        (void)SDL_DetachVirtualJoystick(g_local_multiplayer_acceptance_pad_ids[i]);
        g_local_multiplayer_acceptance_pad_ids[i] = 0;
    }
}

// Native acceptance for the Modern 2P join surface. Two named SDL virtual
// gamepads are seated by the framework; once the stock route reaches the 2P
// select surface and the join overlay opens, their real buttons are pulsed
// through SDL so every join/profile action arrives through the framework's
// source-aware callbacks. UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=disconnect
// runs the unplug/replug variant.
void run_local_multiplayer_join_acceptance() {
    const char* mode = std::getenv("UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE");
    if (!mode) return;
    const bool disconnect = std::strcmp(mode, "disconnect") == 0;
    const LocalMultiplayerJoinAcceptanceStep* steps =
        disconnect ? kLocalMultiplayerDisconnectSteps : kLocalMultiplayerJoinSteps;
    const int step_count = disconnect
        ? static_cast<int>(sizeof(kLocalMultiplayerDisconnectSteps) /
                           sizeof(kLocalMultiplayerDisconnectSteps[0]))
        : static_cast<int>(sizeof(kLocalMultiplayerJoinSteps) /
                           sizeof(kLocalMultiplayerJoinSteps[0]));
    if (g_local_multiplayer_acceptance_stage == -1) {
        const bool attached = attach_local_multiplayer_acceptance_pad(0) &&
                              attach_local_multiplayer_acceptance_pad(1);
        product_diagnostic(
            attached ? "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE PADS_ATTACHED"
                     : "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE ATTACH_FAILED");
        g_local_multiplayer_acceptance_stage = attached ? 0 : 1000;
        g_local_multiplayer_acceptance_frames = 0;
        if (!attached) (void)request_desktop_quit();
        return;
    }
    if (g_local_multiplayer_acceptance_stage >= 1000) return;
    ++g_local_multiplayer_acceptance_frames;
    if (g_local_multiplayer_acceptance_stage == 0) {
        if (!g_local_multiplayer_join_visible) {
            if (g_local_multiplayer_acceptance_frames > 3000u) {
                product_diagnostic(
                    "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE JOIN_NOT_OPENED");
                g_local_multiplayer_acceptance_stage = 1000;
                (void)request_desktop_quit();
            }
            return;
        }
        g_local_multiplayer_acceptance_stage = 1;
        g_local_multiplayer_acceptance_frames = 0;
        return;
    }
    // Each press holds its button for 4 frames, then releases for 8 frames so
    // the framework sees distinct press and release edges; an unplug or
    // replug gets 30 frames for the framework to observe the device change.
    const int step = g_local_multiplayer_acceptance_stage - 1;
    if (step < step_count) {
        const auto& action = steps[step];
        const auto pad_index = static_cast<std::size_t>(action.pad);
        if (action.kind == JoinAcceptanceStepKind::Press) {
            SDL_Joystick* pad = g_local_multiplayer_acceptance_pads[pad_index];
            if (g_local_multiplayer_acceptance_frames == 1u) {
                (void)SDL_SetJoystickVirtualButton(pad, action.button, true);
            } else if (g_local_multiplayer_acceptance_frames == 5u) {
                (void)SDL_SetJoystickVirtualButton(pad, action.button, false);
            } else if (g_local_multiplayer_acceptance_frames >= 13u) {
                ++g_local_multiplayer_acceptance_stage;
                g_local_multiplayer_acceptance_frames = 0;
            }
            return;
        }
        if (g_local_multiplayer_acceptance_frames == 1u) {
            if (action.kind == JoinAcceptanceStepKind::Detach) {
                detach_local_multiplayer_acceptance_pad(pad_index);
            } else {
                (void)attach_local_multiplayer_acceptance_pad(pad_index);
            }
        } else if (g_local_multiplayer_acceptance_frames >= 30u) {
            if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                std::fprintf(
                    stderr,
                    "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE %s pad=%d ready=%d overlay=%d\n",
                    action.kind == JoinAcceptanceStepKind::Detach
                        ? "DETACHED" : "REATTACHED",
                    action.pad + 1,
                    g_local_multiplayer_participants_ready ? 1 : 0,
                    g_local_multiplayer_join_visible ? 1 : 0);
                std::fflush(stderr);
            }
            ++g_local_multiplayer_acceptance_stage;
            g_local_multiplayer_acceptance_frames = 0;
        }
        return;
    }
    const auto& p1 = ur::product::local_multiplayer_participant(
        g_local_multiplayer_participants,
        ur::product::LocalMultiplayerSlot::Player1);
    const auto& p2 = ur::product::local_multiplayer_participant(
        g_local_multiplayer_participants,
        ur::product::LocalMultiplayerSlot::Player2);
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE DONE ready=%d overlay=%d p1=%s p2=%s\n",
            g_local_multiplayer_participants_ready ? 1 : 0,
            g_local_multiplayer_join_visible ? 1 : 0,
            p1 ? p1->profile_id.c_str() : "-",
            p2 ? p2->profile_id.c_str() : "-");
        std::fflush(stderr);
    }
    g_local_multiplayer_acceptance_stage = 1000;
    (void)request_desktop_quit();
}
#endif

// Native Options acceptance for Vibration: from an authoritative race, press
// the real keys a player would (Escape, Down to OPTIONS, Enter, Down to
// VIBRATION, Enter) through the production keyboard handler on one frame
// boundary, then quit so the next process proves the persisted value.
void run_vibration_options_acceptance() {
    if (g_vibration_options_acceptance_done ||
        !std::getenv("UR_VIBRATION_OPTIONS_ACCEPTANCE")) {
        return;
    }
    if (g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE || paused()) {
        g_vibration_options_acceptance_frames = 0;
        return;
    }
    if (++g_vibration_options_acceptance_frames < 120u) return;
    g_vibration_options_acceptance_done = true;

    (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    const int restart = ur_modern_session_restart_available(g_session);
    for (int step = 0; step < 12 && paused() &&
         ur_modern_pause_menu_selected(&g_pause_menu, restart) !=
             UR_MODERN_PAUSE_OPTIONS;
         ++step) {
        (void)ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0);
    }
    (void)ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0);
    for (int step = 0; step < 12 && g_options_visible &&
         ur_modern_options_menu_selected(&g_options_menu) !=
             UR_MODERN_OPTIONS_VIBRATION;
         ++step) {
        (void)ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0);
    }
    if (!g_options_visible ||
        ur_modern_options_menu_selected(&g_options_menu) !=
            UR_MODERN_OPTIONS_VIBRATION) {
        product_diagnostic("UR_VIBRATION_ACCEPTANCE ROW_NOT_REACHED");
    } else {
        (void)ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0);
    }
    (void)request_desktop_quit();
}

// Native Options acceptance for Volume. "adjust" walks the real keys a player
// would (Escape, OPTIONS, Down to VOLUME, Left, Left, Enter) on one frame
// boundary and quits, so the framework writes config.ini; "verify" only
// reports the value a fresh process loaded.
void run_volume_options_acceptance() {
    const char* phase = std::getenv("UR_VOLUME_OPTIONS_ACCEPTANCE");
    if (g_volume_options_acceptance_done || !phase) return;
    if (g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE || paused()) {
        g_volume_options_acceptance_frames = 0;
        return;
    }
    if (++g_volume_options_acceptance_frames < 120u) return;
    g_volume_options_acceptance_done = true;
    std::fprintf(
        stderr, "UR_VOLUME_ACCEPTANCE START percent=%d\n",
        snesrecomp_desktop_get_volume());
    std::fflush(stderr);
    if (std::strcmp(phase, "adjust") == 0) {
        (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
        const int restart = ur_modern_session_restart_available(g_session);
        for (int step = 0; step < 12 && paused() &&
             ur_modern_pause_menu_selected(&g_pause_menu, restart) !=
                 UR_MODERN_PAUSE_OPTIONS;
             ++step) {
            (void)ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0);
        }
        (void)ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0);
        for (int step = 0; step < 12 && g_options_visible &&
             ur_modern_options_menu_selected(&g_options_menu) !=
                 UR_MODERN_OPTIONS_VOLUME;
             ++step) {
            (void)ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0);
        }
        if (!g_options_visible ||
            ur_modern_options_menu_selected(&g_options_menu) !=
                UR_MODERN_OPTIONS_VOLUME) {
            product_diagnostic("UR_VOLUME_ACCEPTANCE ROW_NOT_REACHED");
        } else {
            (void)ur_uniracers_modern_system_key_down(SDLK_LEFT, 0, 0);
            (void)ur_uniracers_modern_system_key_down(SDLK_LEFT, 0, 0);
            (void)ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0);
        }
    }
    (void)request_desktop_quit();
}

// Native vibration acceptance: seat a real SDL virtual gamepad whose Rumble
// callback records what actually reaches the device, then let the scripted
// race run. The production split/finish observers decide every pulse.
void run_haptic_acceptance() {
#if SNESRECOMP_SDL3
    if (!std::getenv("UR_HAPTIC_ACCEPTANCE") ||
        g_haptic_acceptance_stage != 0 ||
        g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01) {
        return;
    }
    g_haptic_acceptance_stage = 1;
    product_diagnostic(
        attach_controller_hotplug_acceptance_pad(true)
            ? "UR_HAPTIC_ACCEPTANCE PAD_ATTACHED"
            : "UR_HAPTIC_ACCEPTANCE ATTACH_FAILED");
#endif
}

// Native acceptance for main-menu controller shortcuts: from the settled
// Modern main menu, attach a real SDL virtual gamepad and tap one physical
// button through SDL -> SNESRecomp -> the title gamepad hook. Only the
// production handler decides what the button does.
void run_main_menu_pad_acceptance() {
#if SNESRECOMP_SDL3
    const char* button_name = std::getenv("UR_MAIN_MENU_PAD_ACCEPTANCE");
    if (!button_name || !*button_name || g_main_menu_pad_acceptance_stage < 0) {
        return;
    }
    SDL_GamepadButton button = SDL_GAMEPAD_BUTTON_INVALID;
    if (std::strcmp(button_name, "r") == 0) {
        button = SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER;
    } else if (std::strcmp(button_name, "y") == 0) {
        button = SDL_GAMEPAD_BUTTON_NORTH;
    }
    if (button == SDL_GAMEPAD_BUTTON_INVALID) {
        g_main_menu_pad_acceptance_stage = -1;
        return;
    }
    switch (g_main_menu_pad_acceptance_stage) {
    case 0:
        if (g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7) {
            g_main_menu_pad_acceptance_frames = 0;
            return;
        }
        if (++g_main_menu_pad_acceptance_frames < 90u) return;
        if (!attach_controller_hotplug_acceptance_pad()) {
            product_diagnostic("UR_MAIN_MENU_PAD_ACCEPTANCE ATTACH_FAILED");
            g_main_menu_pad_acceptance_stage = -1;
            return;
        }
        g_main_menu_pad_acceptance_frames = 0;
        g_main_menu_pad_acceptance_stage = 1;
        return;
    case 1:
        // Wait for the framework to seat the pad before pressing.
        if (!g_controller_hotplug.seats[0].connected) {
            if (++g_main_menu_pad_acceptance_frames > 300u) {
                product_diagnostic("UR_MAIN_MENU_PAD_ACCEPTANCE SEAT_TIMEOUT");
                detach_controller_hotplug_acceptance_pad();
                g_main_menu_pad_acceptance_stage = -1;
            }
            return;
        }
        (void)SDL_SetJoystickVirtualButton(
            g_controller_hotplug_acceptance_pad, button, true);
        product_diagnostic("UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED");
        g_main_menu_pad_acceptance_frames = 0;
        g_main_menu_pad_acceptance_stage = 2;
        return;
    case 2:
        if (++g_main_menu_pad_acceptance_frames < 3u) return;
        (void)SDL_SetJoystickVirtualButton(
            g_controller_hotplug_acceptance_pad, button, false);
        g_main_menu_pad_acceptance_stage = 3;
        return;
    case 3:
        // Leave the pad seated so the release edge is delivered normally.
        g_main_menu_pad_acceptance_stage = -1;
        return;
    default:
        return;
    }
#endif
}

// Native acceptance for device removal: attach a real SDL virtual gamepad
// during an authoritative race, hold a mapped direction until the framework
// delivers it in the human input word, then unplug it while still held. The
// framework must release the held control before clearing the seat, and
// Modern must pause through the ordinary session command. Reconnection is
// then observed through the framework's own seat assignment while paused.
void run_controller_hotplug_acceptance() {
#if SNESRECOMP_SDL3
    if (g_controller_hotplug_acceptance_done ||
        !std::getenv("UR_CONTROLLER_HOTPLUG_ACCEPTANCE")) {
        return;
    }
    switch (g_controller_hotplug_acceptance_stage) {
    case 0:
        if (g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE || paused()) {
            g_controller_hotplug_acceptance_frames = 0;
            return;
        }
        if (++g_controller_hotplug_acceptance_frames < 120u) return;
        if (!attach_controller_hotplug_acceptance_pad()) {
            product_diagnostic("UR_CONTROLLER_HOTPLUG_ACCEPTANCE ATTACH_FAILED");
            g_controller_hotplug_acceptance_done = true;
            return;
        }
        g_controller_hotplug_acceptance_source =
            static_cast<std::uint64_t>(g_controller_hotplug_acceptance_pad_id);
        g_controller_hotplug_acceptance_frames = 0;
        g_controller_hotplug_acceptance_stage = 1;
        return;
    case 1: {
        const auto& seat = g_controller_hotplug.seats[0];
        if (!seat.connected ||
            seat.source_id != g_controller_hotplug_acceptance_source) {
            if (++g_controller_hotplug_acceptance_frames > 300u) {
                product_diagnostic(
                    "UR_CONTROLLER_HOTPLUG_ACCEPTANCE SEAT_TIMEOUT");
                detach_controller_hotplug_acceptance_pad();
                g_controller_hotplug_acceptance_done = true;
            }
            return;
        }
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_CONTROLLER_HOTPLUG_ACCEPTANCE SEATED seat=1 name=%s\n",
                g_controller_seat_names[0].c_str());
            std::fflush(stderr);
        }
        g_controller_hotplug_acceptance_held = g_last_human_input_word;
        (void)SDL_SetJoystickVirtualButton(
            g_controller_hotplug_acceptance_pad,
            SDL_GAMEPAD_BUTTON_DPAD_LEFT,
            true);
        g_controller_hotplug_acceptance_frames = 0;
        g_controller_hotplug_acceptance_stage = 2;
        return;
    }
    case 2: {
        const std::uint32_t baseline = g_controller_hotplug_acceptance_held;
        const std::uint32_t held =
            g_last_human_input_word & ~baseline & 0x0FFFu;
        if (!held) {
            if (++g_controller_hotplug_acceptance_frames > 120u) {
                product_diagnostic(
                    "UR_CONTROLLER_HOTPLUG_ACCEPTANCE HOLD_TIMEOUT");
                detach_controller_hotplug_acceptance_pad();
                g_controller_hotplug_acceptance_done = true;
            }
            return;
        }
        g_controller_hotplug_acceptance_held = held;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_CONTROLLER_HOTPLUG_ACCEPTANCE HELD bits=%03X\n",
                static_cast<unsigned>(held));
            std::fflush(stderr);
        }
        // Unplug while the direction is still physically held.
        detach_controller_hotplug_acceptance_pad();
        g_controller_hotplug_acceptance_observation = g_human_input_observations;
        g_controller_hotplug_acceptance_stage = 3;
        return;
    }
    case 3: {
        if (g_human_input_observations ==
            g_controller_hotplug_acceptance_observation) {
            return;
        }
        if (g_controller_hotplug.seats[0].connected) return;
        const std::uint32_t remaining =
            g_last_human_input_word & g_controller_hotplug_acceptance_held;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_CONTROLLER_HOTPLUG_ACCEPTANCE RELEASED held=%03X after=%03X "
                "seat_connected=0 paused=%d modern=%d\n",
                static_cast<unsigned>(g_controller_hotplug_acceptance_held),
                static_cast<unsigned>(remaining),
                paused() ? 1 : 0,
                modern_mode() ? 1 : 0);
            std::fflush(stderr);
        }
        if (!paused()) {
            // Authentic, or a Modern failure: nothing further to observe.
            g_controller_hotplug_acceptance_done = true;
            (void)request_desktop_quit();
            return;
        }
        // Reconnect while paused. Seat choice stays framework-owned; the
        // connection callback reports the outcome and ends the run.
        if (!attach_controller_hotplug_acceptance_pad()) {
            product_diagnostic(
                "UR_CONTROLLER_HOTPLUG_ACCEPTANCE REATTACH_FAILED");
            g_controller_hotplug_acceptance_done = true;
            (void)request_desktop_quit();
            return;
        }
        g_controller_hotplug_acceptance_stage = 4;
        return;
    }
    default:
        return;
    }
#endif
}

bool dispatch(UrModernPauseAction action) {
    if (!ensure_session()) return false;
    const UrModernSessionResult result =
        ur_modern_pause_handle_action(g_session, &g_pause_menu, action);
    return result == UR_MODERN_SESSION_APPLIED ||
           result == UR_MODERN_SESSION_NO_OP;
}

// Diagnostics also give native acceptance a semantic acknowledgement of
// system-input delivery without exposing mutable product state.
void diagnose_pause_state() {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS") || !g_session) return;
    std::fprintf(
        stderr,
        "UR_PAUSE_STATE paused=%d surface=%d\n",
        ur_modern_session_is_paused(g_session),
        static_cast<int>(g_surface));
    std::fflush(stderr);
}

void diagnose_pause_selection() {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS") || !g_session) return;
    const int restart = ur_modern_session_restart_available(g_session);
    std::fprintf(
        stderr,
        "UR_PAUSE_SELECTION selected=%d restart=%d\n",
        static_cast<int>(ur_modern_pause_menu_selected(&g_pause_menu, restart)),
        restart);
    std::fflush(stderr);
}

bool activate_pause_selection() {
    if (!ensure_session() || !paused()) return false;
    const int restart = ur_modern_session_restart_available(g_session);
    const UrModernPauseItem selected =
        ur_modern_pause_menu_selected(&g_pause_menu, restart);
    if (selected == UR_MODERN_PAUSE_FOCUS_PAUSE) {
        return toggle_focus_pause_setting();
    }
    if (selected == UR_MODERN_PAUSE_OPTIONS) {
        g_controls_visible = false;
        g_run_data_visible = false;
        g_quit_confirm_visible = false;
        g_options_visible = true;
        g_frontend_options_active = false;
        ur_modern_options_menu_reset(&g_options_menu);
        product_diagnostic("UR_PAUSE_OPTIONS OPENED");
        return true;
    }
    if (selected == UR_MODERN_PAUSE_CONTROLS) {
        g_options_visible = false;
        g_run_data_visible = false;
        g_controls_rebind = {};
        g_controls_visible = true;
        product_diagnostic("UR_PAUSE_CONTROLS OPENED");
        diagnose_controls_bindings();
        return true;
    }
    if (selected == UR_MODERN_PAUSE_EXIT_FRONTEND) {
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_EXIT_FRONTEND SELECTED restart=%d\n",
                restart);
            std::fflush(stderr);
        }
        return dispatch(UR_MODERN_PAUSE_ACTIVATE);
    }
    if (selected == UR_MODERN_PAUSE_RUN_DATA) {
        g_options_visible = false;
        g_controls_visible = false;
        g_quit_confirm_visible = false;
        g_run_data_visible = true;
        const UrUniracersRunData data = current_run_data();
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_PAUSE_RUN_DATA OPENED valid=%d time=%d:%d%d.%d subtick=%d surface=%d retry=%d\n",
                data.valid,
                data.minutes,
                data.tens_seconds,
                data.seconds,
                data.tenths,
                data.sub_tick,
                static_cast<int>(g_surface),
                ur_modern_session_restart_available(g_session));
            std::fflush(stderr);
        }
        return true;
    }
    if (selected == UR_MODERN_PAUSE_RECORDS) {
        g_options_visible = false;
        g_controls_visible = false;
        g_run_data_visible = false;
        g_quit_confirm_visible = false;
        const int opened = ur_uniracers_product_open_records();
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_PAUSE_RECORDS OPENED opened=%d\n",
                opened);
            std::fflush(stderr);
        }
        return opened != 0;
    }
    if (selected == UR_MODERN_PAUSE_QUIT) {
        g_options_visible = false;
        g_controls_visible = false;
        g_run_data_visible = false;
        g_quit_confirm_visible = true;
        product_diagnostic("UR_PAUSE_QUIT CONFIRM_OPENED");
        return true;
    }
    if (selected == UR_MODERN_PAUSE_RESTART) {
        const bool handled = dispatch(UR_MODERN_PAUSE_ACTIVATE);
        if (handled) rearm_run_capture_after_retry();
        return handled;
    }
    return dispatch(UR_MODERN_PAUSE_ACTIVATE);
}

int modern_overlay_surface_scale(int width, int height) {
    return ur::product::resolve_modern_overlay_surface_scale(
        ur_uniracers_modern_presentation_scale(),
        width,
        height);
}

ur::product::HostOverlayCompositionPlan centered_modern_modal_layout(
    int width,
    int height,
    int presentation_scale,
    int preferred_width,
    int preferred_height,
    int minimum_width,
    int minimum_height) {
    ur::product::HostOverlayCompositionRequest request{};
    request.logical_surface_width = width / presentation_scale;
    request.logical_surface_height = height / presentation_scale;
    request.presentation_scale = presentation_scale;
    request.output_viewport = {0, 0, width, height};
    request.anchor = ur::product::HostOverlayAnchor::Center;
    request.preferred_width = preferred_width;
    request.preferred_height = preferred_height;
    request.minimum_width = minimum_width;
    request.minimum_height = minimum_height;
    request.edge_margin = 2;
    return ur::product::resolve_modern_overlay_composition(request);
}

void draw_run_timing_hud(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    const bool race_or_results =
        g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ||
        g_surface == UR_UNIRACERS_RESTART_RESULTS;
    if (!ur::product::should_present_run_timing(
            modern_mode(), g_run_timing_supported, race_or_results) ||
        paused() || !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }

    const int64_t ticks60 =
        ur_uniracers_run_data_ticks60(current_run_data());
    if (ticks60 < 0) return;

    const auto* personal_best = g_run_ghosts.record(
        ur::product::CompletedRunGhostKind::PersonalBest);
    const bool results =
        g_surface == UR_UNIRACERS_RESTART_RESULTS;
    auto panel = ur::product::present_run_timing_panel(
        static_cast<std::uint64_t>(ticks60),
        personal_best,
        results ? ur::product::RunTimingPresentationPoint::Finish
                : ur::product::RunTimingPresentationPoint::Live);

    if (!results && g_run_timing_last_split) {
        panel.comparison_label = "SPLIT";
        panel.comparison_text = g_run_timing_last_split->delta_text;
        panel.comparison_available = true;
    }

    char clock_row[48];
    char pb_row[48];
    char comparison_row[56];
    std::snprintf(
        clock_row, sizeof(clock_row), "%s  %s",
        panel.clock_label.c_str(), panel.clock_text.c_str());
    std::snprintf(
        pb_row, sizeof(pb_row), "PB      %s",
        panel.target_text.c_str());
    std::snprintf(
        comparison_row, sizeof(comparison_row), "%s  %s",
        panel.comparison_label.c_str(), panel.comparison_text.c_str());

    const int presentation_scale =
        modern_overlay_surface_scale(width, height);
    const int logical_width = width / presentation_scale;
    const int logical_height = height / presentation_scale;
    ur::product::HostOverlayCompositionRequest layout_request{};
    layout_request.logical_surface_width = logical_width;
    layout_request.logical_surface_height = logical_height;
    layout_request.presentation_scale = presentation_scale;
    layout_request.output_viewport = {0, 0, width, height};
    layout_request.anchor = ur::product::HostOverlayAnchor::TopRight;
    layout_request.preferred_width = 178;
    layout_request.preferred_height = 52;
    layout_request.minimum_width = 178;
    layout_request.minimum_height = 52;
    layout_request.edge_margin = 8;
    const auto layout =
        ur::product::resolve_modern_overlay_composition(layout_request);
    if (!layout.visible) return;

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const auto& panel_rect = layout.presentation_rect;
    const int text_scale = layout.presentation_scale;
    snes_ovl_fill_rect(
        pixels, stride, height,
        panel_rect.x, panel_rect.y,
        panel_rect.width, panel_rect.height, 0xC0202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height,
        panel_rect.x, panel_rect.y,
        panel_rect.width, panel_rect.height, 0xFFF0F0F0u);
    snes_ovl_draw_text(
        pixels, stride, height,
        panel_rect.x + 7 * text_scale,
        panel_rect.y + 6 * text_scale,
        clock_row, 0xFFFFFFFFu, text_scale);
    snes_ovl_draw_text(
        pixels, stride, height,
        panel_rect.x + 7 * text_scale,
        panel_rect.y + 21 * text_scale,
        pb_row, 0xFFFFFFFFu, text_scale);
    snes_ovl_draw_text(
        pixels, stride, height,
        panel_rect.x + 7 * text_scale,
        panel_rect.y + 36 * text_scale,
        comparison_row, 0xFFFFFFFFu, text_scale);

    if (const char* timing_diagnostics =
            std::getenv("UR_TIMING_HUD_DIAGNOSTICS")) {
        bool& reported = results
            ? g_run_timing_results_diag_reported
            : g_run_timing_race_diag_reported;
        const bool log_every_frame =
            std::strcmp(timing_diagnostics, "all") == 0;
        if (log_every_frame || !reported) {
            reported = true;
            std::fprintf(
                stderr,
                "UR_TIMING_HUD %s current_ticks60=%lld current=%s pb=%s comparison=%s\n",
                results ? "RESULTS" : "RACE",
                static_cast<long long>(ticks60),
                panel.clock_text.c_str(),
                panel.target_text.c_str(),
                panel.comparison_text.c_str());
            std::fflush(stderr);
        }
    }
}

}  // namespace

extern "C" void ur_uniracers_modern_after_config(void) {
    apply_profile_save_root();

    // Final-window sampling is host presentation only. Authentic execution
    // leaves the framework's own configured treatment untouched. Modern uses
    // crisp nearest filtering for the current mixed-source compositor; avoid
    // a renderer reconfigure when the loaded framework config already agrees.
    if (modern_mode()) {
        const int linear =
            ur::product::default_final_window_filter() ==
                    ur::product::HostFinalWindowFilter::Linear
                ? 1
                : 0;
        if (snesrecomp_desktop_get_linear_filtering() != linear) {
            (void)snesrecomp_desktop_set_linear_filtering(linear);
        }
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_PRESENTATION FINAL_WINDOW_FILTER mode=%s\n",
                linear ? "linear" : "nearest");
            std::fflush(stderr);
        }
    }
}

extern "C" int ur_uniracers_modern_native_widescreen_enabled(void) {
    return authentic_16x9_view_enabled() &&
           g_widescreen_scene == ur::product::HostSceneComposition::WorldExpand
        ? 1 : 0;
}

extern "C" void ur_uniracers_modern_prepare_frame(
    int,
    int,
    int* frame_width,
    int* frame_height) {
    if (!frame_width || !frame_height) {
        return;
    }
    if (modern_mode()) {
        ur::presentation::racer_hd_prepare_frame(
            0, 0, frame_width, frame_height);
    }
    if (!authentic_16x9_view_enabled()) return;

    const auto plan = ur::product::resolve_16x9_output_composition(
        ur::product::resolve_output_geometry_representation(false),
        g_widescreen_scene);
    *frame_width = plan.logical_view_width;
    *frame_height = plan.logical_view_height;

    // Every widened race presents its margins host-side; split-screen
    // viewports each get their own band origin in the shared store.
    ur_ws_margins_prepare_frame(
        plan.expose_added_world ? 1 : 0,
        (plan.logical_view_width - 256) / 2);
}

extern "C" void ur_uniracers_modern_begin_sim_frame(unsigned frame_number) {
    if (modern_mode()) {
        ur::presentation::racer_hd_begin_sim_frame(frame_number);
    }
}

extern "C" int ur_uniracers_modern_presentation_scale(void) {
    const bool world_expanded =
        authentic_16x9_view_enabled() &&
        g_widescreen_scene == ur::product::HostSceneComposition::WorldExpand;

    // Internal Render Scale is a stable product setting, not a per-pose
    // Racer-HD signal. Fixed and evidence-backed widened scenes keep the
    // configured density even when the authored replacement presenter
    // declines the current frame; the generic nearest-density compositor then
    // preserves the complete logical field, including widened world margins.
    const char* racer_hd = std::getenv("UR_RACER_HD");
    const bool racer_hd_enabled =
        racer_hd != nullptr && racer_hd[0] != '\0' &&
        !(racer_hd[0] == '0' && racer_hd[1] == '\0');
    const int requested_scale =
        racer_hd_enabled
            ? ur::product::internal_render_scale_value(
                  g_product_state.settings.internal_render_scale)
            : 1;

    const bool logical_overlay_active = false;

    return ur::product::resolve_internal_render_scale(
        modern_mode(),
        world_expanded,
        logical_overlay_active,
        requested_scale);
}

extern "C" int ur_uniracers_modern_draw_frame(
    uint8_t* dst, size_t pitch, const uint8_t* field,
    int frame_width, int frame_height, double alpha) {
    if (!modern_mode()) return 0;

    ensure_product_state();
    const bool regional_title =
        g_product_state.regional_presentation ==
            ur::product::RegionalPresentation::Europe &&
        current_regional_secret_context().idle_title_surface;
    if (regional_title && dst && field && frame_width > 0 &&
        frame_height > 0) {
        const int presentation_scale =
            ur_uniracers_modern_presentation_scale();
        if (!ur::product::compose_nearest_density_frame(
                dst,
                pitch,
                field,
                frame_width,
                frame_height,
                presentation_scale)) {
            return 0;
        }
        const auto regional_result =
            ur::product::apply_regional_title_presentation(
                g_product_state.regional_presentation,
                true,
                dst,
                pitch,
                frame_width * presentation_scale,
                frame_height * presentation_scale,
                presentation_scale);
        if (regional_result ==
            ur::product::RegionalTitlePresentationResult::FailedClosed) {
            // Restore the exact canonical field at the same presentation
            // density if any provenance/paint verification fails.
            (void)ur::product::compose_nearest_density_frame(
                dst,
                pitch,
                field,
                frame_width,
                frame_height,
                presentation_scale);
        }
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            static ur::product::RegionalTitlePresentationResult last_result =
                ur::product::RegionalTitlePresentationResult::Canonical;
            if (regional_result != last_result) {
                const char* result_name =
                    regional_result ==
                            ur::product::RegionalTitlePresentationResult::EuropeApplied
                        ? "unirally"
                        : regional_result ==
                                  ur::product::RegionalTitlePresentationResult::FailedClosed
                              ? "canonical-fail-closed"
                              : "uniracers";
                std::fprintf(
                    stderr,
                    "UR_REGIONAL_TITLE visible=%s guest_state_unchanged=1\n",
                    result_name);
                std::fflush(stderr);
                last_result = regional_result;
            }
        }
        // Even a provenance mismatch returns the untouched canonical copy.
        // The regional presenter never writes guest PPU/WRAM state.
        return 1;
    }

    if (ur::presentation::racer_hd_draw_frame(
            dst, pitch, field, frame_width, frame_height, alpha)) {
        return 1;
    }

    const int presentation_scale = ur_uniracers_modern_presentation_scale();
    if (presentation_scale <= 1) return 0;

    // A frame without authored Remastered racer art is still presented at the
    // configured density. Preserve the stock guest raster exactly with an
    // integer nearest-neighbour expansion rather than letting density flicker
    // between replacement and fallback poses.
    return ur::product::compose_nearest_density_frame(
        dst,
        pitch,
        field,
        frame_width,
        frame_height,
        presentation_scale)
        ? 1
        : 0;
}

extern "C" void ur_uniracers_modern_compute_viewport(
    int,
    int,
    int drawable_width,
    int drawable_height,
    SnesDisplayViewport* viewport) {
    if (!viewport || !authentic_16x9_view_enabled()) {
        return;
    }

    const auto plan = ur::product::resolve_16x9_output_composition(
        ur::product::resolve_output_geometry_representation(false),
        g_widescreen_scene);
    const auto resolved = ur::product::resolve_output_viewport(
        plan, drawable_width, drawable_height);
    if (resolved.width <= 0 || resolved.height <= 0) {
        return;
    }

    viewport->x = resolved.x;
    viewport->y = resolved.y;
    viewport->width = resolved.width;
    viewport->height = resolved.height;
}

extern "C" double ur_uniracers_modern_presentation_hz(
    double display_refresh) {
    if (!modern_mode()) return 0.0;
    ensure_product_state();
    return presentation_fps_target(
        g_live_presentation_fps_mode,
        display_refresh);
}

// Native Next Event acceptance drives the real Modern keyboard handler on
// emulated-frame boundaries instead of wall-clock window input: F3 at settled
// MAIN_MENU, then Enter on the preselected row (or Escape to inspect/cancel).
// Every stock menu edge after that comes from the production tour route.
void run_next_event_acceptance() {
    const char* mode = std::getenv("UR_NEXT_EVENT_ACCEPTANCE");
    if (!mode || !*mode || !modern_mode() ||
        g_next_event_acceptance_stage < 0) {
        return;
    }
    const bool inspect = std::strcmp(mode, "inspect") == 0;
    const bool cancel = std::strcmp(mode, "cancel") == 0;
    switch (g_next_event_acceptance_stage) {
    case 0:
        if (g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7 ||
            !tour_continue_available()) {
            g_next_event_acceptance_frames = 0;
            return;
        }
        if (++g_next_event_acceptance_frames < 90u) return;
        (void)ur_uniracers_modern_system_key_down(SDLK_F3, 0, 0);
        g_next_event_acceptance_stage = g_tour_action_visible ? 1 : -1;
        return;
    case 1:
        (void)ur_uniracers_modern_system_key_down(
            inspect ? SDLK_ESCAPE : SDLK_RETURN, 0, 0);
        if (inspect) {
            g_next_event_acceptance_stage = -1;
            (void)request_desktop_quit();
            return;
        }
        g_next_event_acceptance_stage = cancel ? 2 : -1;
        return;
    case 2:
        if (g_tour_continue.stage !=
            ur::product::ModernTourContinueStage::SelectNextEvent) {
            // Ready is a released-input settlement stage, not the end of
            // the route; only an Idle route ended without selection.
            if (g_tour_continue.stage ==
                ur::product::ModernTourContinueStage::Idle) {
                g_next_event_acceptance_stage = -1;
                (void)request_desktop_quit();
            }
            return;
        }
        (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
        g_next_event_acceptance_stage = -1;
        (void)request_desktop_quit();
        return;
    default:
        return;
    }
}

const char* results_navigation_action_name(
    ur::product::ModernResultsAction action) {
    switch (action) {
    case ur::product::ModernResultsAction::NextEvent: return "next";
    case ur::product::ModernResultsAction::Retry: return "retry";
    case ur::product::ModernResultsAction::TrackSelect: return "track";
    case ur::product::ModernResultsAction::TourSelect: return "tour";
    case ur::product::ModernResultsAction::Records: return "records";
    case ur::product::ModernResultsAction::RepeatPractice: return "repeat";
    case ur::product::ModernResultsAction::None:
    default: return "none";
    }
}

void run_results_navigation_acceptance() {
    const char* mode = std::getenv("UR_RESULTS_NAV_ACCEPTANCE");
    if (!mode || !*mode || !modern_mode() ||
        g_results_navigation_acceptance_stage < 0) {
        return;
    }

    if (g_results_navigation_acceptance_stage == 0) {
        if (g_surface != UR_UNIRACERS_RESTART_RESULTS || paused()) {
            g_results_navigation_acceptance_frames = 0;
            return;
        }
        if (++g_results_navigation_acceptance_frames < 90u) return;
        g_results_navigation_acceptance_frames = 0;
        refresh_results_navigation_menu();

        bool next = false;
        bool track = false;
        bool tour = false;
        bool repeat = false;
        bool records = false;
        for (std::size_t i = 0;
             i < g_results_navigation_menu.row_count;
             ++i) {
            switch (g_results_navigation_menu.rows[i]) {
            case ur::product::ModernResultsAction::NextEvent: next = true; break;
            case ur::product::ModernResultsAction::TrackSelect: track = true; break;
            case ur::product::ModernResultsAction::TourSelect: tour = true; break;
            case ur::product::ModernResultsAction::RepeatPractice: repeat = true; break;
            case ur::product::ModernResultsAction::Records: records = true; break;
            default: break;
            }
        }
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_RESULTS_NAV MENU rows=%zu next=%d track=%d tour=%d repeat=%d records=%d practice=%d\n",
                g_results_navigation_menu.row_count,
                next ? 1 : 0,
                track ? 1 : 0,
                tour ? 1 : 0,
                repeat ? 1 : 0,
                records ? 1 : 0,
                g_practice_active ? 1 : 0);
            std::fflush(stderr);
        }

        if (std::strcmp(mode, "inspect") == 0 ||
            std::strcmp(mode, "practice") == 0) {
            g_results_navigation_acceptance_stage = -1;
            (void)request_desktop_quit();
            return;
        }

        ur::product::ModernResultsAction target =
            ur::product::ModernResultsAction::None;
        if (std::strcmp(mode, "track") == 0) {
            target = ur::product::ModernResultsAction::TrackSelect;
        } else if (std::strcmp(mode, "tour") == 0) {
            target = ur::product::ModernResultsAction::TourSelect;
        } else if (std::strcmp(mode, "next") == 0) {
            target = ur::product::ModernResultsAction::NextEvent;
        }
        if (target == ur::product::ModernResultsAction::None) {
            g_results_navigation_acceptance_stage = -1;
            return;
        }

        for (std::size_t guard = 0;
             guard < g_results_navigation_menu.row_count &&
             ur::product::selected_modern_results_action(
                 g_results_navigation_menu) != target;
             ++guard) {
            (void)ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0);
        }
        if (ur::product::selected_modern_results_action(
                g_results_navigation_menu) != target) {
            product_diagnostic("UR_RESULTS_NAV ACCEPTANCE_TARGET_MISSING");
            g_results_navigation_acceptance_stage = -1;
            (void)request_desktop_quit();
            return;
        }
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_RESULTS_NAV ACCEPT target=%s\n",
                results_navigation_action_name(target));
            std::fflush(stderr);
        }
        (void)ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0);
        g_results_navigation_acceptance_stage = 1;
        return;
    }

    if (g_results_navigation_acceptance_stage == 1) {
        const bool route_idle =
            g_results_route_pending == ur::product::ModernResultsAction::None &&
            !g_results_tour_route_active &&
            !tour_continue_routing();
        if (std::strcmp(mode, "track") == 0 &&
            route_idle && g_ram[0x0313] != 0x01 &&
            g_ram[0x009F] == 0xF6) {
            product_diagnostic("UR_RESULTS_NAV ACCEPT_TRACK_READY");
        } else if (std::strcmp(mode, "tour") == 0 &&
                   route_idle && g_ram[0x0313] != 0x01 &&
                   g_ram[0x009F] == 0x6D) {
            product_diagnostic("UR_RESULTS_NAV ACCEPT_TOUR_READY");
        } else if (std::strcmp(mode, "next") == 0 &&
                   g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE &&
                   !g_next_event_verify_track) {
            // Do not let acceptance quit on the first ACTIVE_RACE frame.
            // The route's authoritative course identity may not be readable
            // until a later frame; require that verifier to finish first.
            product_diagnostic("UR_RESULTS_NAV ACCEPT_NEXT_RACE");
        } else {
            return;
        }
        g_results_navigation_acceptance_stage = -1;
        (void)request_desktop_quit();
    }
}

extern "C" void ur_uniracers_modern_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    report_display_capabilities_once();
    if (!ensure_session()) return;

    if (!g_profile_sram_reported &&
        std::getenv("UR_PROFILE_SRAM_DIAGNOSTICS")) {
        g_profile_sram_reported = true;
        std::fprintf(
            stderr,
            "UR_PROFILE_SRAM LOADED root=%s digest=%08X size=%d\n",
            RtlSaveRoot(),
            static_cast<unsigned>(current_sram_digest()),
            g_sram_size);
        std::fflush(stderr);
    }

    const UrUniracersRestartDecision decision =
        ur_uniracers_restart_policy_observe(
            &g_title_policy,
            g_ram[0x0313],
            g_ram[0x009F]);
    g_surface = decision.surface;
    observe_recent_course_identity();
    if (g_next_event_verify_track) {
        const int actual = g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE
            ? authoritative_active_track_id()
            : -1;
        if (actual >= 0 ||
            g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE) {
            if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                std::fprintf(
                    stderr,
                    "UR_NEXT_EVENT RACE_VERIFIED expected=%u actual=%d course_equal=%d\n",
                    static_cast<unsigned>(*g_next_event_verify_track),
                    actual,
                    actual == static_cast<int>(*g_next_event_verify_track)
                        ? 1 : 0);
                std::fflush(stderr);
            }
            g_next_event_verify_track.reset();
        }
    }
    if (g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE &&
        g_fast_repeat_sram_before) {
        const bool sram_equal =
            current_sram_digest() == *g_fast_repeat_sram_before;
        const bool course_equal =
            !g_fast_repeat_course_before ||
            (g_recent_course_track_id &&
             *g_recent_course_track_id == *g_fast_repeat_course_before);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_FAST_NAV REPEAT_VERIFIED sram_equal=%d course_equal=%d practice=%d\n",
                sram_equal ? 1 : 0,
                course_equal ? 1 : 0,
                g_practice_active ? 1 : 0);
            std::fflush(stderr);
        }
        g_fast_repeat_sram_before.reset();
        g_fast_repeat_course_before.reset();
    }
    g_widescreen_scene = ur::product::observe_widescreen_scene(
        &g_widescreen_scene_state,
        g_ram[0x0313],
        g_ram[0x009F]);
    if (g_practice_picker.visible && !practice_picker_context_valid()) {
        close_practice_picker("UR_PRACTICE_PICKER STALE_CONTEXT");
    }
    if (g_progress_overview_visible && !progress_overview_context_valid()) {
        close_progress_overview("UR_TOUR_OVERVIEW STALE_CONTEXT");
    }
    if (g_frontend_options_active &&
        (!modern_mode() || !g_ram || paused() ||
         g_ram[0x009F] != 0xD7 || g_ram[0x0313] == 0x01 ||
         g_exit_frontend_waiting_for_main ||
         g_exit_frontend_waiting_for_usable)) {
        close_host_subview();
        product_diagnostic("UR_FRONTEND_OPTIONS STALE_CONTEXT");
    }

    if (!g_practice_acceptance_fired &&
        std::getenv("UR_PRACTICE_ACCEPTANCE") &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        g_practice_acceptance_fired = true;
        (void)begin_practice();
    }
    if (!g_tour_continue_acceptance_fired &&
        std::getenv("UR_TOUR_CONTINUE_ACCEPTANCE") &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        g_tour_continue_acceptance_fired = true;
        (void)begin_tour_continue();
    }
    if (!g_onboarding_acceptance_fired &&
        std::getenv("UR_ONBOARDING_ACCEPTANCE") &&
        g_onboarding_visible && g_binding_diagnostics_reported &&
        g_ram[0x009F] == 0xD7) {
        g_onboarding_acceptance_fired = true;
        (void)dismiss_onboarding();
    }
    if (stats) {
        advance_practice_route(stats->frame + 1u);
        advance_tour_continue_route(stats->frame + 1u);

        // Acceptance-only synchronization belongs on the emulated-frame
        // boundary, not in wall-clock X11 polling. Hold the real Practice
        // router at rider select long enough for the script to retain its
        // checkpoint, then exercise the ordinary abort/reboot path.
        if (std::getenv("UR_PRACTICE_CANCEL_ACCEPTANCE") &&
            g_practice_active && g_ram[0x0313] != 0x01 &&
            g_ram[0x009F] == 0x3C) {
            ++g_practice_cancel_acceptance_frames;
            if (g_practice_cancel_acceptance_frames >= 30u) {
                g_practice_cancel_acceptance_frames = 0;
                (void)abort_practice_route_to_frontend(
                    "UR_PRACTICE ROUTE_CANCELLED");
            }
        } else {
            g_practice_cancel_acceptance_frames = 0;
        }

        // The profile acceptance still drives the real host UI, but once that
        // modal surface closes, hand stock rider confirmation back to the
        // deterministic guest-input transport on an observed rider-select
        // frame. This removes the host/guest wall-clock race without bypassing
        // stock confirmation or rider initialization.
        if (g_profile_panel_acceptance_confirm_pending &&
            g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0x3C) {
            project_profile_identity_to_stock_rider();
            if (g_profile_panel_acceptance_input_path.empty()) {
                g_profile_panel_acceptance_input_path =
                    resolve_profile_panel_acceptance_input_path();
            }
            if (queue_relative_menu_input(
                    g_profile_panel_acceptance_input_path,
                    stats->frame + 1u,
                    ur::product::quick_practice_runner_mask(
                        ur::product::QuickPracticeLaunchInput::Accept))) {
                g_profile_panel_acceptance_confirm_pending = false;
                product_diagnostic(
                    "UR_PROFILE_UI ACCEPTANCE_CONFIRM_QUEUED");
            }
        }

        // Results acceptance uses the same production rematch command as the
        // R / pad-X surface, but fires on the emulated-frame boundary after
        // the results screen has remained stable long enough for the scripted
        // checkpoint to be captured.
        if (!g_fast_repeat_acceptance_fired &&
            std::getenv("UR_FAST_REPEAT_ACCEPTANCE") &&
            g_surface == UR_UNIRACERS_RESTART_RESULTS) {
            ++g_fast_repeat_acceptance_frames;
            if (g_fast_repeat_acceptance_frames >= 90u) {
                g_fast_repeat_acceptance_fired = true;
                g_fast_repeat_acceptance_frames = 0;
                (void)repeat_current_attempt();
            }
        } else if (g_surface != UR_UNIRACERS_RESTART_RESULTS) {
            g_fast_repeat_acceptance_frames = 0;
        }

        // Exercise the real pause/options/ghost selection path on the first
        // authoritative active-race frame. This acceptance does not consume a
        // guest checkpoint before acting, so an extra dwell only creates a
        // transient-state race without adding evidence.
        if (!g_ghost_target_acceptance_fired &&
            std::getenv("UR_GHOST_TARGET_ACCEPTANCE") &&
            g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
            // g_surface is observed before the Modern session receives this
            // frame's race-active update below. Treat a rejected first-frame
            // pause as retryable instead of consuming the one-shot trigger.
            const bool paused_now = dispatch(UR_MODERN_PAUSE_TOGGLE);
            if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                std::fprintf(
                    stderr,
                    "UR_GHOST_ACCEPTANCE pause=%d paused=%d surface=%d\n",
                    paused_now ? 1 : 0,
                    paused() ? 1 : 0,
                    static_cast<int>(g_surface));
                std::fflush(stderr);
            }
            if (paused_now) {
                const int restart =
                    ur_modern_session_restart_available(g_session);
                for (int step = 0; step < 8 &&
                     ur_modern_pause_menu_selected(&g_pause_menu, restart) !=
                         UR_MODERN_PAUSE_OPTIONS;
                     ++step) {
                    ur_modern_pause_menu_move(&g_pause_menu, 1, restart);
                }
                const auto pause_selected =
                    ur_modern_pause_menu_selected(&g_pause_menu, restart);
                if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                    std::fprintf(
                        stderr,
                        "UR_GHOST_ACCEPTANCE pause_selected=%d restart=%d\n",
                        static_cast<int>(pause_selected),
                        restart);
                    std::fflush(stderr);
                }
                if (pause_selected == UR_MODERN_PAUSE_OPTIONS &&
                    activate_pause_selection()) {
                    for (int step = 0; step < 12 &&
                         ur_modern_options_menu_selected(&g_options_menu) !=
                             UR_MODERN_OPTIONS_GHOST;
                         ++step) {
                        ur_modern_options_menu_move(&g_options_menu, 1);
                    }
                    const auto option_selected =
                        ur_modern_options_menu_selected(&g_options_menu);
                    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                        std::fprintf(
                            stderr,
                            "UR_GHOST_ACCEPTANCE option_selected=%d\n",
                            static_cast<int>(option_selected));
                        std::fflush(stderr);
                    }
                    if (option_selected == UR_MODERN_OPTIONS_GHOST &&
                        activate_options_selection()) {
                        g_ghost_target_acceptance_fired = true;
                        product_diagnostic("UR_GHOST_ACCEPTANCE COMPLETE");
                    }
                }
            }
        }

        // After Exit Frontend has returned the source race to settled Modern
        // main, launch the already-observed Recent Course through the real
        // product command on an emulated-frame boundary. This replaces the
        // workflow's wall-clock F6 injection while preserving the production
        // Quick Practice route and profile/course identity checks.
        if (!g_recent_course_acceptance_fired &&
            std::getenv("UR_RECENT_COURSE_ACCEPTANCE") &&
            g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7 &&
            recent_course_available_for_active_profile()) {
            ++g_recent_course_acceptance_frames;
            if (g_recent_course_acceptance_frames >= 90u) {
                g_recent_course_acceptance_fired = true;
                g_recent_course_acceptance_frames = 0;
                (void)launch_recent_course_practice();
            }
        } else if (g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7) {
            g_recent_course_acceptance_frames = 0;
        }

        run_next_event_acceptance();

        // Native pause-surface acceptances need to enter the host layer only
        // after an authoritative active-race checkpoint is observable. Do that
        // once on the emulated-frame boundary; individual tests can still drive
        // the real pause/options/controls surfaces through desktop input.
        if (!g_pause_open_acceptance_fired &&
            std::getenv("UR_PAUSE_OPEN_ACCEPTANCE") &&
            g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE && !paused()) {
            ++g_pause_open_acceptance_frames;
            if (g_pause_open_acceptance_frames >= 120u) {
                g_pause_open_acceptance_fired = true;
                g_pause_open_acceptance_frames = 0;
                if (dispatch(UR_MODERN_PAUSE_TOGGLE)) {
                    diagnose_pause_state();
                    product_diagnostic("UR_PAUSE_ACCEPTANCE OPENED");
                }
            }
        } else if (g_surface != UR_UNIRACERS_RESTART_ACTIVE_RACE) {
            g_pause_open_acceptance_frames = 0;
        }
    }

    const bool run_active =
        g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE;
    if (stats && g_run_capture_previous_active && g_run_capture.capturing()) {
        (void)g_run_capture.observe_guest_frame(stats->controller_word);
        observe_run_ghost_trace_sample();
        if (g_run_capture.captured_frames() != 0) {
            resolve_run_ghost_presentation_frame(
                g_run_capture.captured_frames() - 1u);
        }
    }
    if (stats && g_run_capture_previous_active &&
        g_multiplayer_run_capture.capturing()) {
        if (!g_local_multiplayer_participants_ready) {
            product_diagnostic(
                "UR_MULTIPLAYER_MATCH ABORTED_IDENTITY_LOST");
            reset_multiplayer_run_capture();
        } else {
            const bool participant_context_matches =
                g_multiplayer_capture_player1 &&
                g_multiplayer_capture_player2 &&
                g_local_multiplayer_participants.player1 &&
                g_local_multiplayer_participants.player2 &&
                *g_local_multiplayer_participants.player1 ==
                    *g_multiplayer_capture_player1 &&
                *g_local_multiplayer_participants.player2 ==
                    *g_multiplayer_capture_player2;
            bool course_context_matches = true;
            if (run_active) {
                const auto current_course =
                    ur_uniracers_identify_course(
                        g_ram + 0x10000u, 0x10000u);
                course_context_matches =
                    current_course.valid &&
                    current_course.course_index ==
                        g_multiplayer_capture_course.course_index;
            }
            if (!participant_context_matches ||
                !course_context_matches) {
                product_diagnostic(
                    "UR_MULTIPLAYER_MATCH STALE_SESSION_CONTEXT");
                reset_multiplayer_run_capture();
            } else {
                (void)g_multiplayer_run_capture.observe_guest_frame(
                    stats->controller_word);
            }
        }
    }
    if (stats && !g_run_capture_previous_active && run_active) {
        (void)begin_run_record_capture(stats->frame);
        (void)begin_multiplayer_run_record_capture(stats->frame);
    }
    if (run_active && g_run_capture.capturing()) {
        observe_run_record_split();
    }
    if (g_surface == UR_UNIRACERS_RESTART_RESULTS &&
        g_run_capture.capturing()) {
        complete_run_record_capture();
    }
    if (g_multiplayer_run_capture.capturing() && g_ram &&
        g_ram[0x009F] ==
            ur::title::kOrdinaryTwoPlayerRaceResultMenu) {
        // Ordinary 2P owns a distinct stock result surface (0xF9). Do not
        // route it through the generic 1P Restart/result classifier; the
        // multiplayer result observer independently validates this boundary.
        complete_multiplayer_run_record_capture();
    }
    if (decision.retire_attempt && g_run_capture.capturing()) {
        g_run_capture.abort_attempt();
        g_run_ghost_trace_capture.abort_attempt();
        g_run_ghost_playback_trace.reset();
        g_run_ghost_presentation_frame.reset();
    }
    if (decision.retire_attempt &&
        g_multiplayer_run_capture.capturing()) {
        reset_multiplayer_run_capture();
    }
    g_run_capture_previous_active = run_active;

    reconcile_tour_resume();
    run_results_navigation_acceptance();

    if (g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
        ur_modern_session_observe_race_active(g_session, 1);
    } else {
        ur_modern_session_observe_race_active(g_session, 0);
        if (decision.retire_attempt) {
            ur_modern_session_retire_race_attempt(g_session);
        }
    }

    maybe_run_exit_frontend_acceptance();
    maybe_run_pause_records_acceptance();

    if (g_exit_frontend_waiting_for_main &&
        g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7) {
        g_exit_frontend_waiting_for_main = false;
        g_exit_frontend_waiting_for_usable = true;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_EXIT_FRONTEND FRONTEND_READY menu=%02X sram=%08X\n",
                static_cast<unsigned>(g_ram[0x009F]),
                static_cast<unsigned>(current_sram_digest()));
            std::fflush(stderr);
        }
    } else if (g_exit_frontend_waiting_for_usable &&
               g_ram[0x009F] == 0x3C) {
        g_exit_frontend_waiting_for_usable = false;
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_EXIT_FRONTEND FRONTEND_USABLE menu=%02X sram=%08X\n",
                static_cast<unsigned>(g_ram[0x009F]),
                static_cast<unsigned>(current_sram_digest()));
            std::fflush(stderr);
        }
    }

    if (g_results_route_pending !=
            ur::product::ModernResultsAction::None &&
        !g_exit_frontend_waiting_for_main &&
        g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7) {
        (void)begin_pending_results_navigation_route();
    }

    observe_regional_title_surface();
    update_local_multiplayer_join_surface();
    observe_local_multiplayer_seat_lines();
    maybe_run_multiplayer_match_acceptance();
    project_profile_identity_to_stock_rider();
    apply_focus_pause_policy();
    apply_controller_disconnect_pause();
    run_controller_hotplug_acceptance();
    run_main_menu_pad_acceptance();
    run_haptic_acceptance();
    run_vibration_options_acceptance();
    run_volume_options_acceptance();
#if SNESRECOMP_SDL3
    run_local_multiplayer_join_acceptance();
#endif
}

extern "C" int ur_uniracers_modern_system_key_down(
    int key,
    int mod,
    int repeat) {
    if (repeat || !ensure_session()) return 0;

    // Host-owned surfaces consume the corresponding human input word too.
    // Capture ownership before handlers can close/change the surface so the
    // closing edge cannot leak into the stock game later in this frame.
    if (host_owns_human_player_input()) {
        g_suppress_human_input_once = true;
    }

    if (g_local_multiplayer_join_visible) {
        if (key == SDLK_ESCAPE) {
            // Suppress this Modern surface for the remainder of the current
            // stock 0x3D visit without causing it to reopen next frame.
            g_local_multiplayer_join_visible = false;
            g_local_multiplayer_setup = {};
            g_local_multiplayer_participants = {};
            g_local_multiplayer_participants_ready = false;
            product_diagnostic("UR_LOCAL_MULTIPLAYER STOCK_FALLBACK");
            return 1;
        }
        if (key == SDLK_LEFT || key == SDLK_RIGHT) {
            local_multiplayer_move_profile(
                ur::product::LocalMultiplayerSlot::Player1,
                key == SDLK_RIGHT ? 1 : -1);
            return 1;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            const auto slot = ur::product::LocalMultiplayerSlot::Player1;
            if (!g_local_multiplayer_setup.player1.assigned) {
                (void)local_multiplayer_assign_source(
                    slot,
                    {ur::product::LocalInputKind::Keyboard, 1u, true});
            } else {
                (void)local_multiplayer_confirm_profile(slot);
            }
            return 1;
        }
        if (key == SDLK_BACKSPACE) {
            const auto slot = ur::product::LocalMultiplayerSlot::Player1;
            if (ur::product::local_multiplayer_participant(
                    g_local_multiplayer_participants, slot)) {
                g_local_multiplayer_participants =
                    ur::product::local_multiplayer_clear_profile(
                        g_local_multiplayer_participants, slot).state;
                g_local_multiplayer_participants_ready = false;
            } else {
                const auto left = ur::product::local_multiplayer_leave(
                    g_local_multiplayer_setup, slot);
                if (left.applied()) g_local_multiplayer_setup = left.state;
            }
            return 1;
        }
        return 1;
    }

    if (g_progress_overview_visible) {
        if (key == SDLK_ESCAPE || key == SDLK_F7 ||
            key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            close_progress_overview("UR_TOUR_OVERVIEW CLOSED");
        }
        return 1;
    }

    if (g_practice_picker.visible) {
        switch (key) {
        case SDLK_UP: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        case SDLK_DOWN: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        case SDLK_LEFT: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_LEFT) ? 1 : 0;
        case SDLK_RIGHT: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_RIGHT) ? 1 : 0;
        case SDLK_RETURN:
        case SDLK_KP_ENTER: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        case SDLK_ESCAPE:
        case SDLK_F5: return handle_practice_picker_navigation(UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        default: return 1;
        }
    }

    if (practice_routing()) {
        // Host-owned stock-menu routing is exclusive until the requested
        // Practice race has been authoritatively validated. Escape is the one
        // explicit cancellation affordance; every other edge is consumed.
        if (key == SDLK_ESCAPE) {
            (void)abort_practice_route_to_frontend(
                "UR_PRACTICE ROUTE_CANCELLED");
        }
        return 1;
    }

    if (g_tour_action_visible) {
        if (key == SDLK_UP) {
            return handle_tour_action_navigation(
                UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (key == SDLK_DOWN) {
            return handle_tour_action_navigation(
                UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            return handle_tour_action_navigation(
                UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        if (key == SDLK_ESCAPE || key == SDLK_F3) {
            return handle_tour_action_navigation(
                UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        }
        return 1;
    }

    if (results_navigation_active()) {
        if (key == SDLK_UP) {
            return handle_results_navigation(
                UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (key == SDLK_DOWN) {
            return handle_results_navigation(
                UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            return handle_results_navigation(
                UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        // Keep the established Escape pause and R / Ctrl+R retry shortcuts
        // below. Their edge is still suppressed from the guest by ownership.
    }

    {
        const auto regional = regional_input_coordinator().keyboard_key(
            g_product_state,
            key,
            static_cast<std::uint64_t>(SDL_GetTicks()),
            current_regional_secret_context());
        if (apply_regional_input_decision(regional, "keyboard")) {
            return 1;
        }
    }

    // Controls is modal input ownership. In particular, capture must see keys
    // such as F1/F3 before any global Modern shortcut can consume them.
    if (g_controls_visible) {
        return handle_controls_key(key) ? 1 : 0;
    }

    if (modern_mode() && key == SDLK_F1 && !host_subview_visible()) {
        g_onboarding_visible = true;
        g_onboarding_manual_open = true;
        product_diagnostic("UR_ONBOARDING HELP_OPENED");
        return 1;
    }
    if (onboarding_surface_active()) {
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER ||
            key == SDLK_ESCAPE) {
            (void)dismiss_onboarding();
        }
        return 1;
    }
    if (tour_continue_routing()) {
        if (key == SDLK_ESCAPE) {
            abort_tour_continue("UR_TOUR_CONTINUE CANCELLED");
        }
        return 1;
    }
    if (modern_mode() && key == SDLK_F9 && !paused() &&
        g_ram && g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        (void)open_frontend_controls();
        return 1;
    }
    if (g_frontend_options_active && key == SDLK_F10) {
        close_host_subview();
        return 1;
    }
    if (modern_mode() && key == SDLK_F10 && !paused() &&
        g_ram && g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        (void)open_frontend_options();
        return 1;
    }
    if (modern_mode() && key == SDLK_F7 && !host_subview_visible() && !paused() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        (void)open_progress_overview();
        return 1;
    }
    if (modern_mode() && key == SDLK_F3 && !paused() &&
        !host_subview_visible() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        // F3 is now the explicit player-facing Resume / Restart surface.
        // The acceptance-only environment hook still exercises direct Resume.
        return open_tour_action_menu() ? 1 : 0;
    }
    if (modern_mode() && key == SDLK_F5 && !paused() &&
        !host_subview_visible() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        (void)open_practice_picker();
        return 1;
    }
    if (modern_mode() && key == SDLK_F6 && !paused() &&
        !host_subview_visible() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        recent_course_available_for_active_profile()) {
        (void)launch_recent_course_practice();
        return 1;
    }

    if (g_profile_menu_visible) {
        return handle_profile_menu_key(key) ? 1 : 0;
    }
    if (key == SDLK_F2 && modern_mode() && !paused() &&
        g_ram[0x009F] == 0x3C) {
        open_profile_menu();
        return 1;
    }

    if (g_quit_confirm_visible &&
        (key == SDLK_RETURN || key == SDLK_KP_ENTER)) {
        return request_desktop_quit() ? 1 : 0;
    }

    if (g_options_visible) {
        if (key == SDLK_UP) {
            ur_modern_options_menu_move(&g_options_menu, -1);
            return 1;
        }
        if (key == SDLK_DOWN) {
            ur_modern_options_menu_move(&g_options_menu, 1);
            return 1;
        }
        if ((key == SDLK_LEFT || key == SDLK_RIGHT) &&
            ur_modern_options_menu_selected(&g_options_menu) ==
                UR_MODERN_OPTIONS_VOLUME) {
            return step_volume_setting(key == SDLK_RIGHT ? 1 : -1) ? 1 : 0;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            return activate_options_selection() ? 1 : 0;
        }
    }

    if (host_subview_visible() && key == SDLK_ESCAPE) {
        close_host_subview();
        return 1;
    }

    if (host_subview_visible()) {
        return 1;
    }

    if (paused() && key == SDLK_f && modern_mode()) {
        (void)toggle_focus_pause_setting();
        return 1;
    }

    if (key == SDLK_ESCAPE) {
        if (!paused() && !restart_surface()) return 0;
        const bool handled = dispatch(UR_MODERN_PAUSE_TOGGLE);
        diagnose_pause_state();
        return handled ? 1 : 0;
    }
    if (paused() && key == SDLK_UP) {
        const bool handled = dispatch(UR_MODERN_PAUSE_PREVIOUS);
        diagnose_pause_selection();
        return handled ? 1 : 0;
    }
    if (paused() && key == SDLK_DOWN) {
        const bool handled = dispatch(UR_MODERN_PAUSE_NEXT);
        diagnose_pause_selection();
        return handled ? 1 : 0;
    }
    if (paused() && (key == SDLK_RETURN || key == SDLK_KP_ENTER)) {
        return activate_pause_selection() ? 1 : 0;
    }
    if (modern_mode() && key == SDLK_r && (mod & KMOD_CTRL) &&
        restart_surface()) {
        (void)repeat_current_attempt();
        return 1;
    }
    if (modern_mode() && key == SDLK_r &&
        g_surface == UR_UNIRACERS_RESTART_RESULTS) {
        (void)repeat_current_attempt();
        return 1;
    }
    return 0;
}

extern "C" int ur_uniracers_modern_controls_active(void) {
    return modern_mode() && g_controls_visible ? 1 : 0;
}

extern "C" int ur_uniracers_modern_subview_active(void) {
    return modern_mode() && host_subview_visible() ? 1 : 0;
}

extern "C" void ur_uniracers_modern_system_gamepad_source_connection(
    int player_index,
    uint64_t source_id,
    int connected) {
    if (player_index < 0 || player_index >= 2) return;
    g_controller_hotplug = ur::product::controller_hotplug_observe(
        g_controller_hotplug, player_index, source_id, connected != 0);
    const auto seat_index = static_cast<std::size_t>(player_index);
    if (connected) {
        g_controller_seat_names[seat_index] = controller_display_name(source_id);
    } else if (!g_controller_hotplug.seats[seat_index].connected) {
        g_controller_seat_names[seat_index].clear();
    }
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_CONTROLLER SEAT_%s seat=%d name=%s\n",
            connected ? "CONNECTED" : "DISCONNECTED",
            player_index + 1,
            connected ? g_controller_seat_names[seat_index].c_str() : "-");
        std::fflush(stderr);
    }
#if SNESRECOMP_SDL3
    if (connected && g_controller_hotplug_acceptance_stage == 4 &&
        !g_controller_hotplug_acceptance_done &&
        source_id ==
            static_cast<std::uint64_t>(g_controller_hotplug_acceptance_pad_id)) {
        const char* notice =
            ur::product::controller_hotplug_notice_text(g_controller_hotplug);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::fprintf(
                stderr,
                "UR_CONTROLLER_HOTPLUG_ACCEPTANCE RECONNECTED seat=%d paused=%d notice=%s\n",
                player_index + 1,
                paused() ? 1 : 0,
                notice ? notice : "-");
            std::fflush(stderr);
        }
        g_controller_hotplug_acceptance_done = true;
        detach_controller_hotplug_acceptance_pad();
        (void)request_desktop_quit();
    }
#endif
    auto source = local_multiplayer_controller_source(
        source_id, connected != 0);
    const auto seat = static_cast<std::size_t>(player_index);
    g_local_multiplayer_sources[seat] = source;
    if (!connected) g_local_multiplayer_consumed_buttons[seat] = 0u;
    g_local_multiplayer_setup = ur::product::local_multiplayer_set_connected(
        g_local_multiplayer_setup, source, connected != 0);
    if (!connected) {
        const auto slot = local_multiplayer_slot_for_player(player_index);
        g_local_multiplayer_participants =
            ur::product::local_multiplayer_clear_profile(
                g_local_multiplayer_participants, slot).state;
        g_local_multiplayer_participants_ready = false;

        // If the session is still on the stock 2P select surface, a lost
        // source must return ownership to the Modern join overlay. Outside
        // that surface (for example during a race), do not invent a modal
        // frontend interruption; the ordinary controller-disconnect policy
        // remains responsible there.
        const bool two_player_select =
            modern_mode() && g_ram && g_ram[0x009F] == 0x3D;
        if (two_player_select) {
            g_local_multiplayer_join_visible = true;
            product_diagnostic("UR_LOCAL_MULTIPLAYER SOURCE_DISCONNECTED");
        }
    }
}

extern "C" int ur_uniracers_modern_system_gamepad_source_button(
    int player_index,
    uint64_t source_id,
    int button,
    int pressed) {
    if (!ensure_session()) return 0;
    if (player_index < 0 || player_index >= 2) {
        return g_local_multiplayer_join_visible ? 1 : 0;
    }

    const auto seat = static_cast<std::size_t>(player_index);
    const std::uint32_t button_bit =
        button >= 0 && button < 32 ? (1u << static_cast<unsigned>(button)) : 0u;
    if (!pressed) {
        if (button_bit && (g_local_multiplayer_consumed_buttons[seat] & button_bit)) {
            g_local_multiplayer_consumed_buttons[seat] &= ~button_bit;
            return 1;
        }
        return g_local_multiplayer_join_visible ? 1 : 0;
    }
    if (!g_local_multiplayer_join_visible) return 0;
    if (button_bit) g_local_multiplayer_consumed_buttons[seat] |= button_bit;

    const auto slot = local_multiplayer_slot_for_player(player_index);
    const auto source = local_multiplayer_controller_source(source_id, true);
    g_local_multiplayer_sources[seat] = source;

    if (button == kGamepadBtn_DpadLeft ||
        button == kGamepadBtn_DpadRight) {
        local_multiplayer_move_profile(
            slot, button == kGamepadBtn_DpadRight ? 1 : -1);
        return 1;
    }
    if (button == kGamepadBtn_B) {
        if (ur::product::local_multiplayer_participant(
                g_local_multiplayer_participants, slot)) {
            g_local_multiplayer_participants =
                ur::product::local_multiplayer_clear_profile(
                    g_local_multiplayer_participants, slot).state;
            g_local_multiplayer_participants_ready = false;
        } else {
            const auto left = ur::product::local_multiplayer_leave(
                g_local_multiplayer_setup, slot);
            if (left.applied()) g_local_multiplayer_setup = left.state;
        }
        return 1;
    }
    if (button == kGamepadBtn_A || button == kGamepadBtn_Start) {
        const auto& assignment =
            ur::product::local_multiplayer_assignment(
                g_local_multiplayer_setup, slot);
        if (!assignment.assigned) {
            (void)local_multiplayer_assign_source(slot, source);
        } else {
            (void)local_multiplayer_confirm_profile(slot);
        }
        return 1;
    }
    return 1;
}

extern "C" int ur_uniracers_modern_system_gamepad_button(
    int button,
    int pressed) {
    if (!ensure_session()) return 0;

    if (host_owns_human_player_input()) {
        g_suppress_human_input_once = true;
    }

    if (g_progress_overview_visible) {
        return -1;
    }
    if (g_practice_picker.visible) {
        // Consume host modal input through the live GamepadMap semantics.
        return -1;
    }

    if (g_tour_action_visible) {
        // Defer physical buttons to SNESRecomp's configured GamepadMap, then
        // consume only the resulting P1 semantic controls below.
        return -1;
    }

    if (practice_routing()) {
        // Consume both press and release edges while the host owns stock-menu
        // traversal. B/Start cancel the route safely; once Active, normal race
        // controls are guest-owned again.
        if (!pressed && button == g_practice_cancel_gamepad_button) {
            g_practice_cancel_gamepad_button = -1;
            return 1;
        }
        if (pressed &&
            (button == kGamepadBtn_B || button == kGamepadBtn_Start)) {
            g_practice_cancel_gamepad_button = button;
            (void)abort_practice_route_to_frontend(
                "UR_PRACTICE ROUTE_CANCELLED");
        }
        return 1;
    }

    if (g_profile_menu_visible) {
        if (!pressed) return 1;
        if (ur::product::modern_profile_reset_confirming(g_profile_reset)) {
            if (button == kGamepadBtn_A) {
                (void)handle_profile_menu_key(SDLK_RETURN);
            } else if (button == kGamepadBtn_B ||
                       button == kGamepadBtn_Start) {
                (void)handle_profile_menu_key(SDLK_ESCAPE);
            }
            return 1;
        }
        if (g_profile_edit_mode == ProfileEditMode::Create &&
            button == kGamepadBtn_DpadLeft) {
            (void)handle_profile_menu_key(SDLK_LEFT);
        } else if (g_profile_edit_mode == ProfileEditMode::Create &&
                   button == kGamepadBtn_DpadRight) {
            (void)handle_profile_menu_key(SDLK_RIGHT);
        } else if (g_profile_edit_mode == ProfileEditMode::None &&
                   button == kGamepadBtn_X) {
            (void)handle_profile_menu_key(SDLK_n);
        } else if (g_profile_edit_mode == ProfileEditMode::None &&
                   button == kGamepadBtn_Y) {
            (void)handle_profile_menu_key(SDLK_d);
        } else if (button == kGamepadBtn_DpadUp) {
            (void)handle_profile_menu_key(SDLK_UP);
        } else if (button == kGamepadBtn_DpadDown) {
            (void)handle_profile_menu_key(SDLK_DOWN);
        } else if (button == kGamepadBtn_A) {
            (void)handle_profile_menu_key(SDLK_RETURN);
        } else if (button == kGamepadBtn_B ||
                   button == kGamepadBtn_Start) {
            (void)handle_profile_menu_key(SDLK_ESCAPE);
        }
        return 1;
    }

    if (tour_continue_routing()) {
        if (pressed &&
            (button == kGamepadBtn_B || button == kGamepadBtn_Start)) {
            abort_tour_continue("UR_TOUR_CONTINUE CANCELLED");
        }
        return 1;
    }

    if (results_navigation_active()) {
        if (!pressed) return 1;
        // Preserve the established one-button Rematch / Repeat Practice
        // shortcut. All other physical buttons are resolved through the live
        // framework GamepadMap and the semantic callback below.
        if (button == kGamepadBtn_X) {
            (void)repeat_current_attempt();
            return 1;
        }
        return -1;
    }

    if (g_frontend_options_active && g_options_visible) {
        // Resolve user-remapped GamepadMap semantics rather than consuming
        // the physical default buttons and losing the remapped identity.
        return -1;
    }

    if (g_controls_visible) {
        // Framework physical/modifier bookkeeping already happened before this
        // callback. Negative means "resolve mapped P1 semantics only":
        // framework/system commands and guest dispatch stay suppressed.
        return -1;
    }

    if (!pressed) {
        if (button == g_practice_cancel_gamepad_button) {
            g_practice_cancel_gamepad_button = -1;
            return 1;
        }
        const bool settled_main =
            modern_mode() && g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7;
        const bool fast_nav_release =
            (modern_mode() &&
             g_surface == UR_UNIRACERS_RESTART_RESULTS &&
             button == kGamepadBtn_X) ||
            (settled_main && button == kGamepadBtn_X) ||
            (settled_main && button == kGamepadBtn_Y &&
             (tour_continue_available() ||
              recent_course_available_for_active_profile())) ||
            (settled_main && button == kGamepadBtn_R1 &&
             recent_course_available_for_active_profile());
        return fast_nav_release || paused() || onboarding_surface_active()
            ? 1 : 0;
    }

    if (onboarding_surface_active()) {
        if (button == kGamepadBtn_A || button == kGamepadBtn_B ||
            button == kGamepadBtn_Start) {
            (void)dismiss_onboarding();
        }
        return 1;
    }
    if (modern_mode() && button == kGamepadBtn_X && !paused() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01) {
        // This is a product-owned navigation button on the settled Modern
        // frontend. Consume it even when Practice safely refuses to launch so
        // the same physical edge cannot leak into the stock guest controller.
        (void)open_practice_picker();
        return 1;
    }
    // Pad Y opens the Tour surface while a tour is resumable, matching the
    // main-menu strip's F3/Y. Like X, this is a physical product shortcut:
    // under the positional default GamepadMap, SNES Y comes from physical X,
    // which Quick Practice already owns.
    if (modern_mode() && button == kGamepadBtn_Y && !paused() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        tour_continue_available()) {
        (void)open_tour_action_menu();
        return 1;
    }
    if (modern_mode() && button == kGamepadBtn_Y && !paused() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        recent_course_available_for_active_profile()) {
        (void)launch_recent_course_practice();
        return 1;
    }
    // R always reaches Recent Course from the settled main menu, including
    // when pad Y is taken by the Tour surface. Modern already filters L/R out
    // of the guest word there, so the stock menu loses nothing.
    if (modern_mode() && button == kGamepadBtn_R1 && !paused() &&
        g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        recent_course_available_for_active_profile()) {
        (void)launch_recent_course_practice();
        return 1;
    }
    if (modern_mode() && button == kGamepadBtn_X &&
        g_surface == UR_UNIRACERS_RESTART_RESULTS) {
        (void)repeat_current_attempt();
        return 1;
    }

    if (modern_mode() && button == kGamepadBtn_X && !paused() &&
        g_ram[0x009F] == 0x3C) {
        open_profile_menu();
        return 1;
    }

    if (g_quit_confirm_visible && button == kGamepadBtn_A) {
        return request_desktop_quit() ? 1 : 0;
    }

    if (g_options_visible) {
        if (button == kGamepadBtn_DpadUp) {
            ur_modern_options_menu_move(&g_options_menu, -1);
            return 1;
        }
        if (button == kGamepadBtn_DpadDown) {
            ur_modern_options_menu_move(&g_options_menu, 1);
            return 1;
        }
        if ((button == kGamepadBtn_DpadLeft ||
             button == kGamepadBtn_DpadRight) &&
            ur_modern_options_menu_selected(&g_options_menu) ==
                UR_MODERN_OPTIONS_VOLUME) {
            return step_volume_setting(
                       button == kGamepadBtn_DpadRight ? 1 : -1) ? 1 : 0;
        }
        if (button == kGamepadBtn_A) {
            return activate_options_selection() ? 1 : 0;
        }
    }

    if (host_subview_visible()) {
        if (button == kGamepadBtn_B || button == kGamepadBtn_Start) {
            close_host_subview();
        }
        return 1;
    }

    if (button == kGamepadBtn_Start) {
        if (!paused() && !restart_surface()) return 0;
        const bool handled = dispatch(UR_MODERN_PAUSE_TOGGLE);
        diagnose_pause_state();
        return handled ? 1 : 0;
    }
    if (!paused()) return 0;

    if (button == kGamepadBtn_DpadUp) {
        const bool handled = dispatch(UR_MODERN_PAUSE_PREVIOUS);
        diagnose_pause_selection();
        return handled ? 1 : 0;
    }
    if (button == kGamepadBtn_DpadDown) {
        const bool handled = dispatch(UR_MODERN_PAUSE_NEXT);
        diagnose_pause_selection();
        return handled ? 1 : 0;
    }
    if (button == kGamepadBtn_A) {
        return activate_pause_selection() ? 1 : 0;
    }
    if (button == kGamepadBtn_B) {
        return dispatch(UR_MODERN_PAUSE_CANCEL) ? 1 : 0;
    }
    return 0;
}

extern "C" int ur_uniracers_modern_system_gamepad_control(
    int control,
    int pressed) {
    if (!ensure_session()) return 0;

    if (host_owns_human_player_input()) {
        g_suppress_human_input_once = true;
    }

    // SNESRecomp's mapped-control order is stable:
    // Up, Down, Left, Right, Select, Start, A, B, X, Y, L, R.
    if (g_progress_overview_visible) {
        if (pressed && (control == 5 || control == 6 || control == 7 ||
                        control == 10)) {
            close_progress_overview("UR_TOUR_OVERVIEW CLOSED");
        }
        return 1;
    }
    if (g_practice_picker.visible) {
        if (!pressed) return 1;
        switch (control) {
        case 0: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_UP); break;
        case 1: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_DOWN); break;
        case 2: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_LEFT); break;
        case 3: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_RIGHT); break;
        case 6: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_CONFIRM); break;
        case 5:
        case 7: (void)handle_practice_picker_navigation(UR_MODERN_HOST_NAV_BACK); break;
        default: break;
        }
        return 1;
    }
    if (g_tour_action_visible) {
        if (!pressed) return 1;
        switch (control) {
        case 0:
            (void)handle_tour_action_navigation(UR_MODERN_HOST_NAV_UP);
            break;
        case 1:
            (void)handle_tour_action_navigation(UR_MODERN_HOST_NAV_DOWN);
            break;
        case 6:
            (void)handle_tour_action_navigation(UR_MODERN_HOST_NAV_CONFIRM);
            break;
        case 5:
        case 7:
            (void)handle_tour_action_navigation(UR_MODERN_HOST_NAV_BACK);
            break;
        default:
            break;
        }
        return 1;
    }

    if (results_navigation_active()) {
        if (!pressed) return 1;
        switch (control) {
        case 0:
            (void)handle_results_navigation(UR_MODERN_HOST_NAV_UP);
            break;
        case 1:
            (void)handle_results_navigation(UR_MODERN_HOST_NAV_DOWN);
            break;
        case 6:
            (void)handle_results_navigation(UR_MODERN_HOST_NAV_CONFIRM);
            break;
        case 5:
        case 7:
            (void)dispatch(UR_MODERN_PAUSE_TOGGLE);
            diagnose_pause_state();
            break;
        default:
            break;
        }
        return 1;
    }

    if (g_frontend_options_active && g_options_visible) {
        if (!pressed) return 1;
        if (control == 8) {
            (void)open_frontend_controls();
            return 1;
        }
        switch (control) {
        case 0: ur_modern_options_menu_move(&g_options_menu, -1); break;
        case 1: ur_modern_options_menu_move(&g_options_menu, 1); break;
        case 2:
        case 3:
            if (ur_modern_options_menu_selected(&g_options_menu) ==
                UR_MODERN_OPTIONS_VOLUME) {
                (void)step_volume_setting(control == 3 ? 1 : -1);
            }
            break;
        case 6: (void)activate_options_selection(); break;
        case 4:
        case 5:
        case 7: close_host_subview(); break;
        default: break;
        }
        return 1;
    }
    if (g_controls_visible) {
        if (!pressed) return 1;

        if (g_controls_rebind.capturing) {
            if (control == 7 || control == 5) {
                (void)ur::product::modern_controls_handle_action(
                    &g_controls_rebind, ur::product::ModernControlsAction::Back);
                product_diagnostic("UR_CONTROLS CAPTURE_CANCELLED");
            }
            return 1;
        }

        ur::product::ModernControlsAction action{};
        if (ur::product::modern_controls_action_for_snes_control(
                control, &action)) {
            (void)handle_controls_action(action);
        }
        return 1;
    }
    // The Select semantic enters the same live Options surface used by pause.
    if (pressed && control == 4 && open_frontend_options()) return 1;
    // The L semantic is resolved through the live GamepadMap (including
    // user remaps); its stock bit is filtered on settled Modern MAIN_MENU.
    if (pressed && control == 10 && modern_mode() && !paused() &&
        g_ram && g_ram[0x009F] == 0xD7 && g_ram[0x0313] != 0x01 &&
        open_progress_overview()) {
        return 1;
    }
    ur::product::RegionalControllerAction regional_action =
        ur::product::RegionalControllerAction::Other;
    switch (control) {
    case 2:
        regional_action = ur::product::RegionalControllerAction::Left;
        break;
    case 3:
        regional_action = ur::product::RegionalControllerAction::Right;
        break;
    case 6:
        regional_action = ur::product::RegionalControllerAction::Accept;
        break;
    case 10:
        regional_action = ur::product::RegionalControllerAction::ShoulderL;
        break;
    case 11:
        regional_action = ur::product::RegionalControllerAction::ShoulderR;
        break;
    default:
        break;
    }
    const auto regional = regional_input_coordinator().controller_button(
        g_product_state,
        regional_action,
        pressed != 0,
        static_cast<std::uint64_t>(SDL_GetTicks()),
        current_regional_secret_context());
    if (apply_regional_input_decision(regional, "controller")) {
        return 1;
    }
    return 0;
}

extern "C" uint32_t ur_uniracers_modern_filter_player_input(uint32_t inputs) {
    g_last_human_input_word = inputs;
    ++g_human_input_observations;
    // This seam sees the final HUMAN P1 word after both keyboard and gamepad
    // mapping but before guest dispatch. Host-owned input must not also reach
    // the stock game underneath. The latch covers the closing edge, where the
    // handler may have already hidden the modal before this filter runs.
    // Bits still held when a surface closes stay withheld until released, so
    // the Enter/Start press that dismisses a panel cannot select the stock
    // menu row underneath on a later frame.
    const bool host_owned =
        g_suppress_human_input_once || host_owns_human_player_input();
    g_suppress_human_input_once = false;
    const auto filtered = ur::product::modern_host_input_filter(
        g_human_input_release_latch, host_owned, inputs);
    g_human_input_release_latch = filtered.latch;
    if (host_owned) return 0u;
    inputs = filtered.inputs;

    // L/R have no ordinary settled-main action, so removing only those two
    // bits makes the stock Left+A+L+R erase-all gesture impossible in Modern
    // mode without disturbing Left/A navigation. Scripted/reference input
    // bypasses this filter, and Authentic mode returns the word byte-for-byte.
    const bool settled_main_menu =
        g_ram && g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7;
    return ur::product::modern_profile_admin_filter_human_input(
        modern_mode()
            ? ur::product::ExecutionMode::Modern
            : ur::product::ExecutionMode::Authentic,
        settled_main_menu,
        inputs);
}

// The stock MAIN_MENU starts its attract demo after ~503 idle frames. Host
// modals own human input there, so without a hold the attract timer expires
// underneath them and the title leaves MAIN_MENU, closing the panel the
// player is reading. Freeze guest frames (not a pause) while a host modal is
// open on the settled main menu. Routes never hold: they need guest frames.
// A --script harness drives the stock menu directly while the first-run
// Welcome panel is visible (its input bypasses the human-input filter), so
// Welcome holds only for human-driven sessions.
bool frontend_modal_hold_wanted() {
    if (!modern_mode() || !g_ram || paused() ||
        g_ram[0x0313] == 0x01 || g_ram[0x009F] != 0xD7 ||
        practice_routing() || tour_continue_routing() ||
        g_practice_active) {
        return false;
    }
    const bool frontend_settings =
        g_frontend_options_active && (g_options_visible || g_controls_visible);
    if (g_practice_picker.visible || g_progress_overview_visible ||
        g_tour_action_visible || frontend_settings) {
        return true;
    }
    return onboarding_surface_active() && !snesrecomp_desktop_script_active();
}

void update_frontend_modal_hold() {
    const bool wanted = frontend_modal_hold_wanted();
    if (wanted == (snesrecomp_desktop_frame_hold() != 0)) return;
    snesrecomp_desktop_set_frame_hold(wanted ? 1 : 0);
    product_diagnostic(wanted ? "UR_FRONTEND_HOLD ENGAGED"
                              : "UR_FRONTEND_HOLD RELEASED");
}

extern "C" void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!ensure_session() || !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }
    update_frontend_modal_hold();

    if (onboarding_surface_active()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w_logical = logical_width < 340
            ? logical_width - 16
            : 324;
        constexpr int kOnboardingPanelHeight = 206;
        const auto layout = centered_modern_modal_layout(
            width, height, scale,
            panel_w_logical, kOnboardingPanelHeight,
            panel_w_logical, kOnboardingPanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        const KeyBinds* binds = keybinds_get();
        const PlayerBinds fallback{};
        const PlayerBinds& p1 = binds ? binds->p1 : fallback;
        const std::string left = uppercase_keybind_label(p1.left);
        const std::string right = uppercase_keybind_label(p1.right);
        const std::string jump = uppercase_keybind_label(p1.b);
        const std::string brake = uppercase_keybind_label(p1.y);
        const std::string a = uppercase_keybind_label(p1.a);
        const std::string x_key = uppercase_keybind_label(p1.x);
        const std::string l = uppercase_keybind_label(p1.l);
        const std::string r = uppercase_keybind_label(p1.r);
        const std::string pad_left = live_gamepad_binding_label(2);
        const std::string pad_right = live_gamepad_binding_label(3);
        const std::string pad_jump = live_gamepad_binding_label(7);
        const std::string pad_brake = live_gamepad_binding_label(9);
        const std::string pad_a = live_gamepad_binding_label(6);
        const std::string pad_x = live_gamepad_binding_label(8);
        const std::string pad_l = live_gamepad_binding_label(10);
        const std::string pad_r = live_gamepad_binding_label(11);
        // ACTION / PAD / KEY columns, each row fitted to the panel (28 cells
        // on a 256-pixel frame) so long rebound key names cannot spill out.
        const std::size_t text_cells =
            ur::product::modern_overlay_text_cells(panel_w_logical);
        const std::string pad_move =
            pad_left == "LEFT" && pad_right == "RIGHT"
                ? std::string("DPAD")
                : pad_left + "/" + pad_right;
        auto binding_row = [&](const char* action,
                               const std::string& pad,
                               const std::string& keys) {
            char row[160];
            std::snprintf(
                row, sizeof(row), "%-6s %-7s %s",
                action, pad.c_str(), keys.c_str());
            return ur::product::fit_modern_overlay_text(row, text_cells);
        };
        const std::string move_row =
            binding_row("MOVE", pad_move, left + "/" + right);
        const std::string jump_row = binding_row("JUMP", pad_jump, jump);
        const std::string brake_row = binding_row("BRAKE", pad_brake, brake);
        const std::string stunt_row = binding_row(
            "STUNT",
            pad_a + "/" + pad_x + "/" + pad_l + "/" + pad_r,
            a + "/" + x_key + "/" + l + "/" + r);

        if (!g_binding_diagnostics_reported &&
            std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            g_binding_diagnostics_reported = true;
            std::fprintf(
                stderr,
                "UR_ONBOARDING BINDINGS keyboard_left=%s keyboard_right=%s keyboard_jump=%s keyboard_brake=%s keyboard_a=%s keyboard_x=%s keyboard_l=%s keyboard_r=%s pad_left=%s pad_right=%s pad_jump=%s pad_brake=%s pad_a=%s pad_x=%s pad_l=%s pad_r=%s\n",
                left.c_str(), right.c_str(), jump.c_str(), brake.c_str(),
                a.c_str(), x_key.c_str(), l.c_str(), r.c_str(),
                pad_left.c_str(), pad_right.c_str(), pad_jump.c_str(),
                pad_brake.c_str(), pad_a.c_str(), pad_x.c_str(),
                pad_l.c_str(), pad_r.c_str());
            std::fflush(stderr);
        }

        snes_ovl_fill_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xFFF0F0F0u);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 7 * scale,
            "WELCOME TO UNIRACERS", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 27 * scale,
            "       PAD     KEY", 0xFFA0A0A0u, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 42 * scale,
            move_row.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 57 * scale,
            jump_row.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 72 * scale,
            brake_row.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 87 * scale,
            stunt_row.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 107 * scale,
            "STUNTS END WHEEL-DOWN.", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 122 * scale,
            "CLEAN STUNTS ADD SPEED.", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 142 * scale,
            "F5/PAD X  QUICK PRACTICE", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 157 * scale,
            "F2/PAD X  RACERS (PICKER)", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 172 * scale,
            "F7/PAD L PROGRESS F1 HELP", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 187 * scale,
            "F9 CTRL F10/SELECT OPT", 0xFFFFFFFFu, scale);
        return;
    }



    if (g_progress_overview_visible && modern_mode()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w = logical_width < 268 ? logical_width - 16 : 260;
        constexpr int kPanelHeight = 207;
        const auto layout = centered_modern_modal_layout(
            width, height, scale,
            panel_w, kPanelHeight, panel_w, kPanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        snes_ovl_fill_rect(pixels, stride, height, x, y,
            rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(pixels, stride, height, x, y,
            rect.width, rect.height, 0xFFF0F0F0u);
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 8 * scale,
            "TOUR PROGRESS", 0xFFFFFFFFu, scale);
        char row[80];
        std::snprintf(row, sizeof(row), "BRONZE %u  SILVER %u  GOLD %u",
            g_progress_overview.bronze_or_better,
            g_progress_overview.silver_or_better,
            g_progress_overview.gold);
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 30 * scale, row, 0xFFFFFFFFu, scale);
        for (std::uint8_t tour = 0; tour < 8; ++tour) {
            // Catalog index is presentation identity; stock tour option
            // remains the only medal/unlock index. Never name hidden Hunter.
            const auto* course = ur::product::quick_practice_course(
                static_cast<std::uint8_t>(tour * 5));
            if (!course) continue;
            const auto stock_option = ur::product::kQuickPracticeTourOptions[tour];
            const bool visible = ur::title::stock_tour_progress_visible(
                g_progress_overview, stock_option);
            if (visible) {
                std::snprintf(row, sizeof(row), "%u. %.*s  %s",
                    static_cast<unsigned>(tour + 1),
                    static_cast<int>(course->tour_name.size()),
                    course->tour_name.data(),
                    ur::title::stock_tour_progress_medal_name(
                        g_progress_overview, stock_option));
            } else {
                std::snprintf(row, sizeof(row), "%u. LOCKED TOUR",
                    static_cast<unsigned>(tour + 1));
            }
            snes_ovl_draw_text(pixels, stride, height,
                x + 8 * scale,
                y + (51 + static_cast<int>(tour) * 16) * scale,
                row, visible ? 0xFFFFFFFFu : 0xFFA0A0A0u, scale);
        }
        const std::string hint = ur::product::fit_modern_overlay_text(
            "ESC/F7 / PAD " + live_gamepad_binding_label(7) + " BACK",
            ur::product::modern_overlay_text_cells(panel_w));
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 188 * scale,
            hint.c_str(), 0xFFFFFFFFu, scale);
        if (!g_progress_overview_draw_reported &&
            std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            g_progress_overview_draw_reported = true;
            std::fprintf(stderr,
                "UR_TOUR_OVERVIEW PRESENT scale=%d visible=%04X\n",
                scale,
                static_cast<unsigned>(
                    g_progress_overview.visible_tour_options));
            std::fflush(stderr);
        }
        return;
    }

    if (g_practice_picker.visible && modern_mode()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w = logical_width < 284 ? logical_width - 16 : 276;
        constexpr int kPanelHeight = 170;
        const auto layout = centered_modern_modal_layout(
            width, height, scale, panel_w, kPanelHeight, panel_w, kPanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        const auto view = ur::product::quick_practice_selection_view(
            g_practice_picker);
        if (!view.valid) return;
        const auto previous = ur::product::quick_practice_available_course_step(
            g_practice_picker.picker, g_practice_picker_availability, -1);
        const auto next = ur::product::quick_practice_available_course_step(
            g_practice_picker.picker, g_practice_picker_availability, +1);
        const auto* prev_course = ur::product::quick_practice_picker_course(previous);
        const auto* next_course = ur::product::quick_practice_picker_course(next);
        snes_ovl_fill_rect(pixels, stride, height, x, y,
            rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(pixels, stride, height, x, y,
            rect.width, rect.height, 0xFFF0F0F0u);
        char row[96];
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 8 * scale,
            "QUICK PRACTICE", 0xFFFFFFFFu, scale);
        std::snprintf(row, sizeof(row), "TOUR %u/8  %.*s",
            static_cast<unsigned>(view.tour_number),
            static_cast<int>(view.tour_name.size()), view.tour_name.data());
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 28 * scale, row, 0xFFFFFFFFu, scale);
        std::snprintf(row, sizeof(row), "  %.*s",
            prev_course ? static_cast<int>(prev_course->name.size()) : 0,
            prev_course ? prev_course->name.data() : "");
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 50 * scale, row, 0xFFA0A0A0u, scale);
        std::snprintf(row, sizeof(row), "> %.*s",
            static_cast<int>(view.course_name.size()), view.course_name.data());
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 65 * scale, row, 0xFFFFFFFFu, scale);
        std::snprintf(row, sizeof(row), "  %.*s",
            next_course ? static_cast<int>(next_course->name.size()) : 0,
            next_course ? next_course->name.data() : "");
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 80 * scale, row, 0xFFA0A0A0u, scale);
        std::snprintf(row, sizeof(row), "TRACK %u/40  %.*s",
            static_cast<unsigned>(view.course_number),
            static_cast<int>(view.kind_label.size()), view.kind_label.data());
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 101 * scale, row, 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 123 * scale,
            "UP/DOWN TRACK  L/R TOUR", 0xFFFFFFFFu, scale);
        const std::string hint = "ENTER/PAD " +
            live_gamepad_binding_label(6) + " PLAY";
        const std::string back = "ESC/PAD " +
            live_gamepad_binding_label(7) + " BACK";
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 139 * scale, hint.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(pixels, stride, height,
            x + 8 * scale, y + 154 * scale, back.c_str(), 0xFFFFFFFFu, scale);
        if (!g_practice_picker_draw_reported &&
            std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            g_practice_picker_draw_reported = true;
            std::fprintf(stderr, "UR_PRACTICE_PICKER PRESENT scale=%d track=%u\n",
                scale, static_cast<unsigned>(g_practice_picker.picker.track_id));
            std::fflush(stderr);
        }
        return;
    }

    if (modern_mode() &&
        g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE &&
        g_run_ghost_presentation_frame &&
        height % 224 == 0) {
        const int scale = height / 224;
        if (ur::presentation::valid_racer_hd_internal_render_scale(scale)) {
            const auto selected =
                ur::presentation::select_completed_run_ghost_racer_presentation(
                    ur::presentation::GraphicsPack::Remastered,
                    *g_run_ghost_presentation_frame);
            if (selected.uses_replacement() && selected.registration) {
                auto frame = *g_run_ghost_presentation_frame;
                const int logical_width = width / scale;
                if (logical_width > 256) {
                    frame.screen_x += (logical_width - 256) / 2;
                }
                const bool drew =
                    ur::presentation::draw_completed_run_ghost_racer(
                        dst,
                        pitch,
                        logical_width,
                        224,
                        scale,
                        frame,
                        *selected.registration,
                        ur::presentation::CompletedRunGhostRenderStyle{128});
                if (drew && !g_run_ghost_draw_reported &&
                    std::getenv("UR_RUN_GHOST_DRAW_DIAGNOSTICS")) {
                    g_run_ghost_draw_reported = true;
                    std::fprintf(
                        stderr,
                        "UR_RUN_GHOST DRAWN race_frame=%llu semantic=%04X x=%d y=%d scale=%d\n",
                        static_cast<unsigned long long>(frame.race_frame),
                        static_cast<unsigned>(frame.semantic_frame_id),
                        frame.screen_x,
                        frame.screen_y,
                        scale);
                    std::fflush(stderr);
                }
            }
        }
    }

    if (g_local_multiplayer_join_visible && modern_mode()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w_logical = logical_width < 276
            ? logical_width - 16
            : 268;
        constexpr int kLocalMultiplayerPanelHeight = 142;
        const auto layout = centered_modern_modal_layout(
            width, height, scale,
            panel_w_logical, kLocalMultiplayerPanelHeight,
            panel_w_logical, kLocalMultiplayerPanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        snes_ovl_fill_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xFFF0F0F0u);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 7 * scale,
            "LOCAL MULTIPLAYER", 0xFFFFFFFFu, scale);

        // Every line must fit the panel: 8-pixel cells inside an 8-pixel
        // margin on each side.
        const std::size_t row_cells = static_cast<std::size_t>(
            (panel_w_logical - 16) / 8);
        auto participant_row = [&](ur::product::LocalMultiplayerSlot slot,
                                   bool joined) {
            using RowState =
                ur::product::LocalMultiplayerParticipantRowState;
            const auto& selected =
                ur::product::local_multiplayer_participant(
                    g_local_multiplayer_participants, slot);
            const auto* candidate =
                ur::product::local_multiplayer_profile_candidate(
                    g_local_multiplayer_participants,
                    g_profile_catalog,
                    slot);
            const char* label =
                ur::product::local_multiplayer_slot_label(slot);
            if (!joined) {
                return ur::product::local_multiplayer_participant_row_text(
                    label, RowState::NotJoined, {}, {}, row_cells);
            }
            if (selected) {
                return ur::product::local_multiplayer_participant_row_text(
                    label, RowState::Ready, selected->identity.name,
                    selected->profile_id, row_cells);
            }
            if (candidate) {
                return ur::product::local_multiplayer_participant_row_text(
                    label, RowState::Choosing, candidate->identity.name,
                    candidate->profile_id, row_cells);
            }
            return ur::product::local_multiplayer_participant_row_text(
                label, RowState::NoProfiles, {}, {}, row_cells);
        };

        const bool p1_joined =
            g_local_multiplayer_setup.player1.assigned &&
            g_local_multiplayer_setup.player1.source.connected;
        const bool p2_joined =
            g_local_multiplayer_setup.player2.assigned &&
            g_local_multiplayer_setup.player2.source.connected;
        const std::string p1 = participant_row(
            ur::product::LocalMultiplayerSlot::Player1, p1_joined);
        const std::string p2 = participant_row(
            ur::product::LocalMultiplayerSlot::Player2, p2_joined);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 32 * scale,
            p1.c_str(), 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 52 * scale,
            p2.c_str(), 0xFFFFFFFFu, scale);

        auto draw_device_line = [&](ur::product::LocalMultiplayerSlot slot,
                                    int line_y) {
            const std::string line = local_multiplayer_seat_device_line(slot);
            if (line.empty()) return;
            const bool connected =
                ur::product::local_multiplayer_seat_connected(
                    ur::product::local_multiplayer_seat_presentation(
                        g_local_multiplayer_setup, slot));
            snes_ovl_draw_text(
                pixels, stride, height, x + 24 * scale, y + line_y * scale,
                line.c_str(),
                connected ? 0xFFA0F0A0u : 0xFFA0A0A0u,
                scale);
        };
        draw_device_line(
            ur::product::LocalMultiplayerSlot::Player1, 42);
        draw_device_line(
            ur::product::LocalMultiplayerSlot::Player2, 62);

        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 77 * scale,
            "L/R PROFILE  A JOIN/CONFIRM",
            0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 94 * scale,
            "B/BKSP  CLEAR / LEAVE", 0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 111 * scale,
            "ENTER=KEYS P1  ESC=STOCK 2P",
            0xFFFFFFFFu, scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 128 * scale,
            "PICK MATCHING STOCK RIDERS",
            0xFFFFFFFFu, scale);
        return;
    }

    if (g_tour_action_visible && modern_mode() &&
        g_profile_state && g_profile_state->tour_continuation) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w_logical = logical_width < 260
            ? logical_width - 16
            : 252;
        constexpr int kTourActionPanelHeight = 142;
        const auto layout = centered_modern_modal_layout(
            width, height, scale,
            panel_w_logical, kTourActionPanelHeight,
            panel_w_logical, kTourActionPanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        const auto& continuation = *g_profile_state->tour_continuation;
        const auto tier = ur::product::default_modern_challenge_tier(
            continuation.medal_value);
        const auto* course = ur::product::quick_practice_course(
            static_cast<std::uint8_t>(continuation.tour_row * 5u));

        snes_ovl_fill_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xFFF0F0F0u);
        snes_ovl_draw_text(
            pixels, stride, height,
            x + 8 * scale, y + 7 * scale,
            "TOUR", 0xFFFFFFFFu, scale);

        char detail[96];
        std::snprintf(
            detail, sizeof(detail), "%.*s  CHALLENGE %s",
            course ? static_cast<int>(course->tour_name.size()) : 4,
            course ? course->tour_name.data() : "TOUR",
            challenge_tier_name(tier));
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 25 * scale,
            detail, 0xFFFFFFFFu, scale);

        unsigned completed = 0;
        for (const auto flag : continuation.qualified) completed += flag;
        std::snprintf(
            detail, sizeof(detail), "PROGRESS %u/5", completed);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * scale, y + 42 * scale,
            detail, 0xFFFFFFFFu, scale);

        if (g_tour_action_menu.confirming_restart) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8 * scale, y + 67 * scale,
                "RESTART TOUR?", 0xFFFFFFFFu, scale);
            // While the Tour surface is open, pad buttons reach it through
            // the live GamepadMap (SNES A confirms, SNES B cancels), so name
            // the physical buttons that produce those controls.
            const std::string confirm_hint =
                "ENTER / PAD " + live_gamepad_binding_label(6) + " CONFIRM";
            const std::string cancel_hint =
                "ESC / PAD " + live_gamepad_binding_label(7) + " CANCEL";
            snes_ovl_draw_text(
                pixels, stride, height, x + 8 * scale, y + 86 * scale,
                confirm_hint.c_str(), 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8 * scale, y + 105 * scale,
                cancel_hint.c_str(), 0xFFFFFFFFu, scale);
        } else {
            const char* row_labels[] = {
                "RESUME TOUR", "RESTART TOUR", "BACK", "NEXT EVENT"
            };
            const auto next_track = ur::product::unique_next_track_id(
                continuation.tour_row, continuation.qualified);
            const auto* next_course = next_track
                ? ur::product::quick_practice_course(*next_track)
                : nullptr;
            for (std::size_t i = 0; i < g_tour_action_menu.row_count; ++i) {
                char row[64];
                const auto action = g_tour_action_menu.rows[i];
                const auto idx = static_cast<std::size_t>(action);
                if (action == ur::product::ModernTourActionRow::NextEvent &&
                    next_course) {
                    std::snprintf(
                        row, sizeof(row), "%c NEXT EVENT  %.*s",
                        i == g_tour_action_menu.selected ? '>' : ' ',
                        static_cast<int>(next_course->name.size()),
                        next_course->name.data());
                } else {
                    std::snprintf(
                        row, sizeof(row), "%c %s",
                        i == g_tour_action_menu.selected ? '>' : ' ',
                        row_labels[idx]);
                }
                snes_ovl_draw_text(
                    pixels, stride, height, x + 8 * scale,
                    y + (66 + static_cast<int>(i) * 18) * scale,
                    row, 0xFFFFFFFFu, scale);
            }
        }
        return;
    }

    if (g_profile_menu_visible && modern_mode()) {
        ensure_profile_catalog();
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const int scale = modern_overlay_surface_scale(width, height);
        const int logical_width = width / scale;
        const int panel_w_logical = logical_width < 260
            ? logical_width - 16
            : 252;
        constexpr int kProfilePanelHeight = 154;
        const auto layout = centered_modern_modal_layout(
            width,
            height,
            scale,
            panel_w_logical,
            kProfilePanelHeight,
            panel_w_logical,
            kProfilePanelHeight);
        if (!layout.visible) return;
        const auto& rect = layout.presentation_rect;
        const int x = rect.x;
        const int y = rect.y;
        snes_ovl_fill_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xE0202020u);
        snes_ovl_stroke_rect(
            pixels, stride, height,
            x, y, rect.width, rect.height, 0xFFF0F0F0u);
        snes_ovl_draw_text(
            pixels, stride, height,
            x + 8 * scale, y + 7 * scale,
            "RACERS / PROFILES", 0xFFFFFFFFu, scale);

        if (ur::product::modern_profile_reset_confirming(
                g_profile_reset)) {
            const char* racer =
                g_profile_menu_index < g_profile_catalog.size()
                    ? g_profile_catalog[g_profile_menu_index].identity.name.c_str()
                    : "CURRENT RACER";
            char reset_row[96];
            std::snprintf(
                reset_row,
                sizeof(reset_row),
                "RESET %s?",
                racer);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 32 * scale,
                reset_row, 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 57 * scale,
                "MEDALS/RECORDS/TOUR STATE", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 82 * scale,
                "RETURN TO CLEAN STOCK DATA", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 112 * scale,
                "ENTER / PAD A  RESET", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 132 * scale,
                "ESC / PAD B  CANCEL", 0xFFFFFFFFu, scale);
        } else if (g_profile_edit_mode != ProfileEditMode::None) {
            char name_row[64];
            char preset_row[64];
            std::snprintf(name_row, sizeof(name_row), "NAME  %s_", g_profile_edit_name.c_str());
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 32 * scale,
                g_profile_edit_mode == ProfileEditMode::Create
                    ? "CREATE RACER" : "RENAME RACER",
                0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 52 * scale,
                name_row, 0xFFFFFFFFu, scale);
            if (g_profile_edit_mode == ProfileEditMode::Create) {
                const auto& preset =
                    ur::product::legacy_racer_presets()[g_profile_preset_index];
                std::snprintf(preset_row, sizeof(preset_row),
                    "PRESET %s / %s", preset.name.data(), preset.colour_label.data());
                snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 72 * scale,
                    preset_row, 0xFFFFFFFFu, scale);
                snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 92 * scale,
                    "LEFT/RIGHT  PRESET", 0xFFFFFFFFu, scale);
            }
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 112 * scale,
                "ENTER SAVE   ESC CANCEL", 0xFFFFFFFFu, scale);
        } else if (g_profile_catalog.empty()) {
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 37 * scale,
                "NO RACERS YET", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 62 * scale,
                "N / PAD X  CREATE RACER", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 87 * scale,
                "ESC / F2  CLOSE", 0xFFFFFFFFu, scale);
        } else {
            const auto& entry = g_profile_catalog[g_profile_menu_index];
            char name_row[64];
            char preset_row[64];
            const bool active = g_product_state.active_profile_id &&
                *g_product_state.active_profile_id == entry.profile_id;
            std::snprintf(name_row, sizeof(name_row), "%s %s",
                active ? "ACTIVE" : "SELECT", entry.identity.name.c_str());
            const auto& preset =
                ur::product::legacy_racer_presets()[entry.identity.rider_index];
            std::snprintf(preset_row, sizeof(preset_row), "%s / %s",
                preset.name.data(), preset.colour_label.data());
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 32 * scale,
                name_row, 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 52 * scale,
                preset_row, 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 77 * scale,
                "UP/DOWN CHOOSE  ENTER SELECT", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 97 * scale,
                "N/PAD X CREATE  R RENAME", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 117 * scale,
                "D/PAD Y RESET PROGRESS", 0xFFFFFFFFu, scale);
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 137 * scale,
                "ESC / F2  CLOSE", 0xFFFFFFFFu, scale);
        }
        if (g_profile_cool_name_notice) {
            snes_ovl_draw_text(pixels, stride, height, x + 8 * scale, y + 137 * scale,
                "COOL NAME!", 0xFFFFFFFFu, scale);
        }
        return;
    }

    // Modern main-menu continue strip: one row for the Tour surface (Next
    // Event when it is unique) and one for Recent Course, each naming the
    // inputs that actually trigger it. It sits below the stock menu items and
    // fails closed rather than overlapping them.
    if (modern_mode() && !g_practice_active && !paused() &&
        g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7 &&
        !g_options_visible &&
        !g_tour_action_visible && !g_practice_picker.visible &&
        !tour_continue_routing() && !onboarding_surface_active()) {
        ur::product::ModernMainMenuStripInput strip_input;
        if (tour_continue_available()) {
            const auto& continuation = *g_profile_state->tour_continuation;
            const auto* tour_course = ur::product::quick_practice_course(
                static_cast<std::uint8_t>(continuation.tour_row * 5u));
            const auto next_track = ur::product::unique_next_track_id(
                continuation.tour_row, continuation.qualified);
            const auto* next_course = next_track
                ? ur::product::quick_practice_course(*next_track)
                : nullptr;
            std::uint8_t completed = 0;
            for (const auto flag : continuation.qualified) completed += flag;
            strip_input.tour = ur::product::ModernMainMenuTourEntry{
                next_course ? next_course->name : std::string_view{},
                tour_course ? tour_course->tour_name : std::string_view{},
                completed,
            };
        }
        if (recent_course_available_for_active_profile()) {
            if (const auto* recent = ur::product::quick_practice_course(
                    *g_recent_course_track_id)) {
                strip_input.recent_course = recent->name;
            }
        }
        const auto strip =
            ur::product::build_modern_main_menu_strip(strip_input);
        if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
            std::string summary = std::to_string(strip.row_count);
            for (std::size_t i = 0; i < strip.row_count; ++i) {
                summary += " | " + strip.rows[i];
            }
            if (summary != g_main_menu_strip_reported) {
                g_main_menu_strip_reported = summary;
                std::fprintf(
                    stderr, "UR_MAIN_MENU_STRIP rows=%s\n", summary.c_str());
                std::fflush(stderr);
            }
        }
        if (strip.row_count > 0) {
            uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
            const int stride = static_cast<int>(pitch / 4u);
            const int scale = modern_overlay_surface_scale(width, height);
            const int strip_w = static_cast<int>(
                ur::product::kModernMainMenuStripMaxChars) * 8 + 12;
            const int strip_h = 6 + 12 * static_cast<int>(strip.row_count);
            ur::product::HostOverlayCompositionRequest request{};
            request.logical_surface_width = width / scale;
            request.logical_surface_height = height / scale;
            request.presentation_scale = scale;
            request.output_viewport = {0, 0, width, height};
            request.reserved.left = 2;
            request.reserved.right = 2;
            request.reserved.bottom = 2;
            request.anchor = ur::product::HostOverlayAnchor::BottomCenter;
            request.preferred_width = strip_w;
            request.preferred_height = strip_h;
            request.minimum_width = strip_w;
            request.minimum_height = strip_h;
            const auto layout =
                ur::product::resolve_modern_overlay_composition(request);
            if (layout.visible) {
                const auto& rect = layout.presentation_rect;
                snes_ovl_fill_rect(
                    pixels, stride, height,
                    rect.x, rect.y, rect.width, rect.height, 0xC0202020u);
                snes_ovl_stroke_rect(
                    pixels, stride, height,
                    rect.x, rect.y, rect.width, rect.height, 0xFFF0F0F0u);
                for (std::size_t i = 0; i < strip.row_count; ++i) {
                    snes_ovl_draw_text(
                        pixels, stride, height,
                        rect.x + 6 * scale,
                        rect.y + (4 + 12 * static_cast<int>(i)) * scale,
                        strip.rows[i].c_str(), 0xFFFFFFFFu, scale);
                }
            }
        }
    }

    if (modern_mode() && practice_routing()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const char* hint = "PRACTICE  ESC/B/START CANCEL";
        const int scale = modern_overlay_surface_scale(width, height);
        ur::product::HostOverlayCompositionRequest request{};
        request.logical_surface_width = width / scale;
        request.logical_surface_height = height / scale;
        request.presentation_scale = scale;
        request.output_viewport = {0, 0, width, height};
        request.anchor = ur::product::HostOverlayAnchor::TopCenter;
        request.preferred_width = 304;
        request.preferred_height = 22;
        request.minimum_width = 220;
        request.minimum_height = 22;
        request.edge_margin = 8;
        const auto layout =
            ur::product::resolve_modern_overlay_composition(request);
        if (layout.visible) {
            const auto& rect = layout.presentation_rect;
            snes_ovl_fill_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xC0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height,
                rect.x + 8 * scale, rect.y + 7 * scale,
                hint, 0xFFFFFFFFu, scale);
        }
    }

    if (modern_mode() && tour_continue_routing()) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const char* hint = "CONTINUING  ESC/PAD B CANCEL";
        const int scale = modern_overlay_surface_scale(width, height);
        ur::product::HostOverlayCompositionRequest request{};
        request.logical_surface_width = width / scale;
        request.logical_surface_height = height / scale;
        request.presentation_scale = scale;
        request.output_viewport = {0, 0, width, height};
        request.anchor = ur::product::HostOverlayAnchor::TopCenter;
        request.preferred_width = 284;
        request.preferred_height = 22;
        request.minimum_width = 220;
        request.minimum_height = 22;
        request.edge_margin = 8;
        const auto layout =
            ur::product::resolve_modern_overlay_composition(request);
        if (layout.visible) {
            const auto& rect = layout.presentation_rect;
            snes_ovl_fill_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xC0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height,
                rect.x + 8 * scale, rect.y + 7 * scale,
                hint, 0xFFFFFFFFu, scale);
        }
    }

    if (modern_mode() && g_practice_active &&
        g_practice_launch.stage ==
            ur::product::QuickPracticeLaunchStage::Active) {
        uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
        const int stride = static_cast<int>(pitch / 4u);
        const char* hint = "PRACTICE START>EXIT FRONTEND";
        const int scale = modern_overlay_surface_scale(width, height);
        ur::product::HostOverlayCompositionRequest request{};
        request.logical_surface_width = width / scale;
        request.logical_surface_height = height / scale;
        request.presentation_scale = scale;
        request.output_viewport = {0, 0, width, height};
        request.anchor = ur::product::HostOverlayAnchor::TopCenter;
        request.preferred_width = 284;
        request.preferred_height = 22;
        request.minimum_width = 220;
        request.minimum_height = 22;
        request.edge_margin = 8;
        const auto layout =
            ur::product::resolve_modern_overlay_composition(request);
        if (layout.visible) {
            const auto& rect = layout.presentation_rect;
            snes_ovl_fill_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xC0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height,
                rect.x, rect.y, rect.width, rect.height, 0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height,
                rect.x + 8 * scale, rect.y + 7 * scale,
                hint, 0xFFFFFFFFu, scale);
        }
    }

    draw_run_timing_hud(dst, pitch, width, height);

    const int is_paused = paused() ? 1 : 0;
    const int results = g_surface == UR_UNIRACERS_RESTART_RESULTS;
    const int restart = ur_modern_session_restart_available(g_session);
    const bool results_menu_active =
        !is_paused && results && results_navigation_active();
    const bool frontend_options = g_frontend_options_active &&
        (g_options_visible || g_controls_visible) && !is_paused;
    if (!is_paused && !(results && (restart || results_menu_active)) &&
        !frontend_options) return;

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const int modal_scale = modern_overlay_surface_scale(width, height);
    const int logical_width = width / modal_scale;
    const int results_rows = results_menu_active
        ? static_cast<int>(g_results_navigation_menu.row_count)
        : 0;
    const int panel_h_logical =
        is_paused
            ? (restart ? 144 : 129)
            : (results_menu_active
                ? std::max(44, 25 + results_rows * 15)
                : (g_practice_active ? 30 : 44));
    const int panel_w_logical = logical_width < 220 ? logical_width - 16 : 212;
    const auto panel_layout = centered_modern_modal_layout(
        width, height, modal_scale,
        panel_w_logical, panel_h_logical,
        panel_w_logical, panel_h_logical);
    if (!panel_layout.visible) return;
    const int panel_w = panel_layout.presentation_rect.width;
    const int panel_h = panel_layout.presentation_rect.height;
    const int x = panel_layout.presentation_rect.x;
    // The results strip sits above the bottom 14 output pixels, which belong
    // to the one-line F8 / Y RECORDS hint (drawn unscaled at height - 13).
    constexpr int kResultsRecordsHintBand = 14;
    const int y = is_paused
        ? panel_layout.presentation_rect.y
        : height - panel_h - 8 * modal_scale - kResultsRecordsHintBand;

    if (!frontend_options) {
        snes_ovl_fill_rect(
            pixels, stride, height, x, y, panel_w, panel_h, 0xE0202020u);
        snes_ovl_stroke_rect(
            pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);
    }

    const char* controller_notice =
        is_paused
            ? ur::product::controller_hotplug_notice_text(g_controller_hotplug)
            : nullptr;
    if (controller_notice) {
        // Above every pause subview, below the Practice hint strip.
        const int notice_y = (g_practice_active ? 34 : 8) * modal_scale;
        const int notice_w_logical =
            logical_width < 236 ? logical_width - 16 : 220;
        const int notice_w = notice_w_logical * modal_scale;
        const int notice_x = (width - notice_w) / 2;
        snes_ovl_fill_rect(
            pixels, stride, height, notice_x, notice_y,
            notice_w, 22 * modal_scale, 0xE0402020u);
        snes_ovl_stroke_rect(
            pixels, stride, height, notice_x, notice_y,
            notice_w, 22 * modal_scale, 0xFFF0F0F0u);
        snes_ovl_draw_text(
            pixels, stride, height,
            notice_x + 6 * modal_scale, notice_y + 7 * modal_scale,
            controller_notice, 0xFFFFFFFFu, modal_scale);
    }

    if (is_paused || frontend_options) {
        if (g_options_visible) {
            const int options_h_logical = 219;
            const auto options_layout = centered_modern_modal_layout(
                width, height, modal_scale,
                panel_w_logical, options_h_logical,
                panel_w_logical, options_h_logical);
            if (!options_layout.visible) return;
            const int options_h = options_layout.presentation_rect.height;
            const int options_y = options_layout.presentation_rect.y;
            const int options_x = options_layout.presentation_rect.x;
            const UrModernOptionsItem selected =
                ur_modern_options_menu_selected(&g_options_menu);
            const char* focus_text =
                g_product_state.settings.pause_on_focus_loss
                    ? "FOCUS PAUSE  ON" : "FOCUS PAUSE  OFF";
            const char* display_text =
                g_product_state.settings.display_mode ==
                        ur::product::HostDisplayMode::BorderlessFullscreen
                    ? "DISPLAY  BORDERLESS"
                    : (g_product_state.settings.display_mode ==
                               ur::product::HostDisplayMode::Fullscreen
                           ? "DISPLAY  FULLSCREEN"
                           : "DISPLAY  WINDOWED");
            const char* vsync_text =
                g_product_state.settings.vsync_mode ==
                        ur::product::HostVSyncMode::Adaptive
                    ? "VSYNC    ADAPTIVE"
                    : (g_product_state.settings.vsync_mode ==
                               ur::product::HostVSyncMode::Off
                           ? "VSYNC    OFF"
                           : "VSYNC    ON");
            const char* presentation_text =
                g_product_state.settings.presentation_fps_mode ==
                        ur::product::HostPresentationFpsMode::Native
                    ? "PRESENT FPS  NATIVE"
                    : (g_product_state.settings.presentation_fps_mode ==
                               ur::product::HostPresentationFpsMode::Game
                           ? "PRESENT FPS  GAME"
                           : nullptr);
            char presentation_value[32];
            if (!presentation_text) {
                std::snprintf(
                    presentation_value, sizeof(presentation_value),
                    "PRESENT FPS  %s",
                    presentation_fps_mode_name(
                        g_product_state.settings.presentation_fps_mode));
                presentation_text = presentation_value;
            }
            const auto resolution_choices =
                ur::product::build_output_resolution_choices(
                    active_output_modes());
            const auto effective_resolution =
                ur::product::select_supported_output_resolution(
                    g_product_state.settings.output_resolution,
                    resolution_choices);
            const std::string resolution_value =
                output_resolution_name(effective_resolution);
            char focus_row[32];
            char display_row[32];
            char vsync_row[32];
            char presentation_row[32];
            char resolution_row[40];
            char render_scale_row[32];
            char widescreen_row[32];
            char ghost_row[32];
            char vibration_row[32];
            char volume_row[32];
            const auto ghost_target = active_run_ghost_target();
            const std::string ghost_status =
                ur::product::completed_run_ghost_target_status_label(
                    g_run_ghosts, ghost_target);
            std::snprintf(
                focus_row, sizeof(focus_row), "%c %s",
                selected == UR_MODERN_OPTIONS_FOCUS_PAUSE ? '>' : ' ',
                focus_text);
            std::snprintf(
                display_row, sizeof(display_row), "%c %s",
                selected == UR_MODERN_OPTIONS_DISPLAY_MODE ? '>' : ' ',
                display_text);
            std::snprintf(
                vsync_row, sizeof(vsync_row), "%c %s",
                selected == UR_MODERN_OPTIONS_VSYNC ? '>' : ' ',
                vsync_text);
            std::snprintf(
                presentation_row, sizeof(presentation_row), "%c %s",
                selected == UR_MODERN_OPTIONS_PRESENTATION_FPS ? '>' : ' ',
                presentation_text);
            std::snprintf(
                resolution_row, sizeof(resolution_row), "%c OUTPUT  %s",
                selected == UR_MODERN_OPTIONS_OUTPUT_RESOLUTION ? '>' : ' ',
                resolution_value.c_str());
            std::snprintf(
                render_scale_row, sizeof(render_scale_row), "%c HD SCALE %dx",
                selected == UR_MODERN_OPTIONS_RENDER_SCALE ? '>' : ' ',
                ur::product::internal_render_scale_value(
                    g_product_state.settings.internal_render_scale));
            std::snprintf(
                widescreen_row, sizeof(widescreen_row), "%c VIEW     %s",
                selected == UR_MODERN_OPTIONS_WIDESCREEN ? '>' : ' ',
                g_product_state.settings.widescreen_mode ==
                        ur::product::HostWidescreenMode::Authentic16x9
                    ? "16:9" : "ORIGINAL");
            std::snprintf(
                vibration_row, sizeof(vibration_row), "%c VIBRATION %s",
                selected == UR_MODERN_OPTIONS_VIBRATION ? '>' : ' ',
                g_product_state.settings.vibration_enabled ? "ON" : "OFF");
            std::snprintf(
                volume_row, sizeof(volume_row), "%c VOLUME  < %d%% >",
                selected == UR_MODERN_OPTIONS_VOLUME ? '>' : ' ',
                snesrecomp_desktop_get_volume());
            std::snprintf(
                ghost_row, sizeof(ghost_row), "%c GHOST    %s",
                selected == UR_MODERN_OPTIONS_GHOST ? '>' : ' ',
                ghost_status.c_str());
            snes_ovl_fill_rect(
                pixels, stride, height, options_x, options_y, panel_w, options_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, options_x, options_y, panel_w, options_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 7 * modal_scale,
                "OPTIONS", 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 27 * modal_scale,
                focus_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 42 * modal_scale,
                display_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 57 * modal_scale,
                vsync_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 72 * modal_scale,
                presentation_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 87 * modal_scale,
                resolution_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 102 * modal_scale,
                render_scale_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 117 * modal_scale,
                widescreen_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 132 * modal_scale,
                ghost_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 147 * modal_scale,
                vibration_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 162 * modal_scale,
                volume_row, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 182 * modal_scale,
                "A / ENTER  CHANGE", 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, options_x + 8 * modal_scale, options_y + 202 * modal_scale,
                frontend_options ? "PAD X CONTROLS / B BACK"
                                 : "B / ESC    BACK",
                0xFFFFFFFFu, modal_scale);
            if (frontend_options && !g_frontend_options_draw_reported &&
                std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                g_frontend_options_draw_reported = true;
                std::fprintf(stderr, "UR_FRONTEND_OPTIONS PRESENT scale=%d\n",
                    modal_scale);
                std::fflush(stderr);
            }
            return;
        }

        if (g_controls_visible) {
            const int controls_h_logical = 220;
            const auto controls_layout = centered_modern_modal_layout(
                width, height, modal_scale,
                panel_w_logical, controls_h_logical,
                panel_w_logical, controls_h_logical);
            if (!controls_layout.visible) return;
            if (frontend_options && !g_frontend_controls_draw_reported &&
                std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
                g_frontend_controls_draw_reported = true;
                std::fprintf(stderr, "UR_FRONTEND_CONTROLS PRESENT scale=%d\n",
                    modal_scale);
                std::fflush(stderr);
            }
            const int controls_h = controls_layout.presentation_rect.height;
            const int controls_y = controls_layout.presentation_rect.y;
            const int controls_x = controls_layout.presentation_rect.x;
            std::array<std::string, 12> key_label_storage{};
            std::array<std::string_view, 12> key_labels{};
            for (int i = 0; i < ur::product::modern_control_binding_count(); ++i) {
                key_label_storage[static_cast<std::size_t>(i)] =
                    uppercase_keybind_label(keybinds_get_button(1, i));
                key_labels[static_cast<std::size_t>(i)] =
                    key_label_storage[static_cast<std::size_t>(i)];
            }
            const ur::product::ModernControlsPadGlyphs pad_glyphs{
                live_gamepad_binding_label(6),
                live_gamepad_binding_label(7),
                live_gamepad_binding_label(8),
                live_gamepad_binding_label(9),
            };
            const auto presentation = ur::product::present_modern_controls(
                g_controls_rebind, key_labels, pad_glyphs);

            snes_ovl_fill_rect(
                pixels, stride, height, controls_x, controls_y, panel_w, controls_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, controls_x, controls_y, panel_w, controls_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, controls_x + 8 * modal_scale, controls_y + 7 * modal_scale,
                "CONTROLS - KEYBOARD P1", 0xFFFFFFFFu, modal_scale);
            // Every line stays inside the panel (24 cells at 212 pixels).
            const std::size_t text_cells =
                ur::product::modern_overlay_text_cells(panel_w_logical);
            const std::string pad_row = ur::product::fit_modern_overlay_text(
                std::string("PAD P1  ") +
                    (g_controller_hotplug.seats[0].connected
                         ? g_controller_seat_names[0]
                         : std::string("NONE")),
                text_cells);
            snes_ovl_draw_text(
                pixels, stride, height, controls_x + 8 * modal_scale, controls_y + 18 * modal_scale,
                pad_row.c_str(),
                g_controller_hotplug.seats[0].connected
                    ? 0xFFA0F0A0u : 0xFFA0A0A0u,
                modal_scale);

            int row_y = controls_y + 31 * modal_scale;
            for (const auto& row : presentation.rows) {
                char row_text[128];
                std::snprintf(
                    row_text,
                    sizeof(row_text),
                    "%c %-6s  %s",
                    row.selected ? '>' : ' ',
                    row.control_label.c_str(),
                    row.capturing ? "PRESS A KEY" : row.key_label.c_str());
                snes_ovl_draw_text(
                    pixels, stride, height, controls_x + 8 * modal_scale, row_y,
                    ur::product::fit_modern_overlay_text(row_text, text_cells).c_str(),
                    row.capturing ? 0xFFF0F0A0u : 0xFFFFFFFFu, modal_scale);
                row_y += 13 * modal_scale;
            }
            snes_ovl_draw_text(
                pixels, stride, height, controls_x + 8 * modal_scale, controls_y + 188 * modal_scale,
                ur::product::fit_modern_overlay_text(
                    presentation.instruction, text_cells).c_str(),
                0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, controls_x + 8 * modal_scale, controls_y + 205 * modal_scale,
                ur::product::fit_modern_overlay_text(
                    presentation.instruction_detail, text_cells).c_str(),
                0xFFFFFFFFu, modal_scale);
            return;
        }

        if (g_quit_confirm_visible) {
            const int quit_h_logical = 69;
            const auto quit_layout = centered_modern_modal_layout(
                width, height, modal_scale,
                panel_w_logical, quit_h_logical,
                panel_w_logical, quit_h_logical);
            if (!quit_layout.visible) return;
            const int quit_h = quit_layout.presentation_rect.height;
            const int quit_y = quit_layout.presentation_rect.y;
            const int quit_x = quit_layout.presentation_rect.x;
            snes_ovl_fill_rect(
                pixels, stride, height, quit_x, quit_y, panel_w, quit_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, quit_x, quit_y, panel_w, quit_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, quit_x + 8 * modal_scale, quit_y + 7 * modal_scale,
                "QUIT TO DESKTOP?", 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, quit_x + 8 * modal_scale, quit_y + 27 * modal_scale,
                "A / ENTER  CONFIRM", 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, quit_x + 8 * modal_scale, quit_y + 47 * modal_scale,
                "B / ESC    CANCEL", 0xFFFFFFFFu, modal_scale);
            return;
        }

        if (g_run_data_visible) {
            const UrUniracersRunData data = current_run_data();
            const int run_h_logical = 144;
            const auto run_layout = centered_modern_modal_layout(
                width, height, modal_scale,
                panel_w_logical, run_h_logical,
                panel_w_logical, run_h_logical);
            if (!run_layout.visible) return;
            const int run_h = run_layout.presentation_rect.height;
            const int run_y = run_layout.presentation_rect.y;
            const int run_x = run_layout.presentation_rect.x;
            char current_text[40];
            char previous_text[40];
            char pb_text[40];
            char ghost_text[40];
            char delta_text[40];

            const int64_t current_ticks =
                ur_uniracers_run_data_ticks60(data);
            if (current_ticks >= 0) {
                const std::string formatted =
                    ur::product::format_run_ticks60(
                        static_cast<std::uint64_t>(current_ticks));
                std::snprintf(
                    current_text, sizeof(current_text),
                    "CURRENT  %s", formatted.c_str());
            } else {
                std::snprintf(
                    current_text, sizeof(current_text),
                    "CURRENT  --:--.--/60");
            }

            const auto* previous = g_run_ghosts.record(
                ur::product::CompletedRunGhostKind::Previous);
            const auto* personal_best = g_run_ghosts.record(
                ur::product::CompletedRunGhostKind::PersonalBest);
            const auto previous_presented = previous
                ? ur::product::present_run_target(
                    *previous, ur::product::RunDataTargetKind::Previous)
                : std::nullopt;
            const auto pb_presented = personal_best
                ? ur::product::present_run_target(
                    *personal_best,
                    ur::product::RunDataTargetKind::PersonalBest)
                : std::nullopt;
            std::snprintf(
                previous_text, sizeof(previous_text),
                "PREVIOUS %s",
                previous_presented
                    ? previous_presented->time_text.c_str() : "--");
            std::snprintf(
                pb_text, sizeof(pb_text),
                "PB       %s",
                pb_presented ? pb_presented->time_text.c_str() : "--");

            const auto ghost_target = active_run_ghost_target();
            std::snprintf(
                ghost_text, sizeof(ghost_text),
                "GHOST    %s",
                ur::product::completed_run_ghost_target_name(ghost_target));

            std::snprintf(delta_text, sizeof(delta_text), "DELTA    --");
            if (g_surface == UR_UNIRACERS_RESTART_RESULTS &&
                current_ticks >= 0) {
                const auto selection =
                    ur::product::select_completed_run_ghost_target(
                        g_run_ghosts, ghost_target);
                if (selection.active() && selection.record) {
                    const auto delta =
                        ur::product::present_run_finish_delta(
                            *selection.record,
                            static_cast<std::uint64_t>(current_ticks));
                    if (delta) {
                        std::snprintf(
                            delta_text, sizeof(delta_text),
                            "DELTA    %s",
                            delta->delta_text.c_str());
                    }
                }
            }

            const char* surface_text =
                g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE
                    ? "SURFACE  RACE"
                    : (g_surface == UR_UNIRACERS_RESTART_RESULTS
                        ? "SURFACE  RESULTS"
                        : "SURFACE  OTHER");
            const char* retry_text =
                ur_modern_session_restart_available(g_session)
                    ? "RETRY    READY" : "RETRY    UNAVAILABLE";

            snes_ovl_fill_rect(
                pixels, stride, height, run_x, run_y, panel_w, run_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, run_x, run_y, panel_w, run_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 7 * modal_scale,
                "RUN DATA", 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 22 * modal_scale,
                current_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 37 * modal_scale,
                previous_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 52 * modal_scale,
                pb_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 67 * modal_scale,
                ghost_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 82 * modal_scale,
                delta_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 97 * modal_scale,
                surface_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 112 * modal_scale,
                retry_text, 0xFFFFFFFFu, modal_scale);
            snes_ovl_draw_text(
                pixels, stride, height, run_x + 8 * modal_scale, run_y + 127 * modal_scale,
                "BACK     B / ESC", 0xFFFFFFFFu, modal_scale);
            return;
        }

        ur_modern_pause_menu_move(&g_pause_menu, 0, restart);
        const UrModernPauseItem selected =
            ur_modern_pause_menu_selected(&g_pause_menu, restart);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, y + 7 * modal_scale,
            "PAUSED", 0xFFFFFFFFu, modal_scale);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, y + 22 * modal_scale,
            selected == UR_MODERN_PAUSE_RESUME ? "> RESUME" : "  RESUME",
            0xFFFFFFFFu, modal_scale);
        if (restart) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8 * modal_scale, y + 37 * modal_scale,
                selected == UR_MODERN_PAUSE_RESTART
                    ? "> RESTART" : "  RESTART",
                0xFFFFFFFFu, modal_scale);
        }
        const int options_y = restart ? y + 52 * modal_scale : y + 37 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, options_y,
            selected == UR_MODERN_PAUSE_OPTIONS
                ? "> OPTIONS" : "  OPTIONS",
            0xFFFFFFFFu, modal_scale);
        const int controls_y = options_y + 15 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, controls_y,
            selected == UR_MODERN_PAUSE_CONTROLS
                ? "> CONTROLS" : "  CONTROLS",
            0xFFFFFFFFu, modal_scale);
        const int run_data_y = controls_y + 15 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, run_data_y,
            selected == UR_MODERN_PAUSE_RUN_DATA
                ? "> RUN DATA" : "  RUN DATA",
            0xFFFFFFFFu, modal_scale);
        const int records_y = run_data_y + 15 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, records_y,
            selected == UR_MODERN_PAUSE_RECORDS
                ? "> RECORDS" : "  RECORDS",
            0xFFFFFFFFu, modal_scale);
        const int exit_y = records_y + 15 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, exit_y,
            selected == UR_MODERN_PAUSE_EXIT_FRONTEND
                ? "> EXIT FRONTEND" : "  EXIT FRONTEND",
            0xFFFFFFFFu, modal_scale);
        const int quit_y = exit_y + 15 * modal_scale;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8 * modal_scale, quit_y,
            selected == UR_MODERN_PAUSE_QUIT
                ? "> QUIT DESKTOP" : "  QUIT DESKTOP",
            0xFFFFFFFFu, modal_scale);
    } else if (results_menu_active) {
        const auto selected =
            ur::product::selected_modern_results_action(
                g_results_navigation_menu);
        auto action_label = [](ur::product::ModernResultsAction action) {
            switch (action) {
            case ur::product::ModernResultsAction::NextEvent:
                return "NEXT EVENT";
            case ur::product::ModernResultsAction::Retry:
                return "RETRY / REMATCH  R/X";
            case ur::product::ModernResultsAction::TrackSelect:
                return "TRACK SELECT";
            case ur::product::ModernResultsAction::TourSelect:
                return "TOUR SELECT";
            case ur::product::ModernResultsAction::Records:
                return "RECORDS  F8/Y";
            case ur::product::ModernResultsAction::RepeatPractice:
                return "REPEAT PRACTICE  R/X";
            case ur::product::ModernResultsAction::None:
            default:
                return "";
            }
        };

        int row_y = y + 7 * modal_scale;
        for (std::size_t i = 0;
             i < g_results_navigation_menu.row_count;
             ++i) {
            const auto action = g_results_navigation_menu.rows[i];
            char row[64];
            std::snprintf(
                row, sizeof(row), "%c %s",
                action == selected ? '>' : ' ',
                action_label(action));
            const std::string fitted =
                ur::product::fit_modern_overlay_text(
                    row,
                    ur::product::modern_overlay_text_cells(
                        panel_w_logical));
            snes_ovl_draw_text(
                pixels, stride, height,
                x + 8 * modal_scale, row_y,
                fitted.c_str(), 0xFFFFFFFFu, modal_scale);
            row_y += 15 * modal_scale;
        }
        snes_ovl_draw_text(
            pixels, stride, height,
            x + 8 * modal_scale, y + (panel_h_logical - 13) * modal_scale,
            "UP/DN + CONFIRM", 0xFFA0A0A0u, modal_scale);
    } else {
        // Preserve the established result strip on unsupported result families
        // (notably VS), which are outside this navigation slice.
        snes_ovl_draw_text(
            pixels, stride, height,
            x + 8 * modal_scale, y + 11 * modal_scale,
            g_practice_active
                ? "R/PAD X  REPEAT PRACTICE"
                : "R/PAD X  REMATCH",
            0xFFFFFFFFu, modal_scale);
        if (!g_practice_active) {
            snes_ovl_draw_text(
                pixels, stride, height,
                x + 8 * modal_scale, y + 25 * modal_scale,
                "CTRL+R   RETRY", 0xFFFFFFFFu, modal_scale);
        }
    }
}
