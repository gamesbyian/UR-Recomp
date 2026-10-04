#include "uniracers_modern_host.h"

extern "C" {
#include "common_rtl.h"
#include "snes_overlay_draw.h"
}

#include "desktop/config.h"
#include "desktop/host_main.h"
#include "desktop/sdl_compat.h"
#include "focus_pause_policy.hpp"
#include "host_product_state.hpp"
#include "host_product_store.hpp"
#include "modern_pause_input.h"
#include "modern_pause_menu.h"
#include "modern_options_menu.h"
#include "modern_session_c_api.h"
#include "output_resolution_runtime_policy.hpp"
#include "uniracers_restart_policy.h"
#include "uniracers_run_data.h"
#include "widescreen_output_composition.hpp"

#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <string>
#include <vector>

namespace {

UrModernSession* g_session;
ur::product::HostProductState g_product_state;
ur::product::HostPresentationFpsMode g_live_presentation_fps_mode =
    ur::product::HostPresentationFpsMode::Game;
bool g_product_state_initialized;
std::string g_product_state_path;
UrModernPauseMenu g_pause_menu;
UrModernOptionsMenu g_options_menu;
bool g_options_visible;
bool g_controls_visible;
bool g_run_data_visible;
bool g_quit_confirm_visible;
bool g_display_caps_reported;
bool g_exit_frontend_waiting_for_main;
bool g_exit_frontend_waiting_for_usable;
bool g_exit_frontend_acceptance_fired;
unsigned g_exit_frontend_acceptance_surface_frames;
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

bool authentic_16x9_view_enabled() {
    if (!modern_mode()) return false;
    const char* view = std::getenv("URRECOMP_WS_VIEW");
    return view &&
           (std::strcmp(view, "authentic-16x9") == 0 ||
            std::strcmp(view, "authentic-16x9-candidate") == 0);
}

void product_diagnostic(const char* message) {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS")) return;
    std::fprintf(stderr, "%s\n", message);
    std::fflush(stderr);
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

    char* pref_path = SDL_GetPrefPath("gamesbyian", "UR-Recomp");
    if (!pref_path) {
        return {};
    }
    std::string path(pref_path);
    SDL_free(pref_path);
    path += "host-state-v1.txt";
    return path;
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
                "UR_HOST_STATE LOADED pause_on_focus_loss=%d display_mode=%s vsync=%s presentation_fps=%s output_resolution=%s\n",
                g_product_state.settings.pause_on_focus_loss ? 1 : 0,
                display_mode_name(g_product_state.settings.display_mode),
                vsync_mode_name(g_product_state.settings.vsync_mode),
                presentation_fps_mode_name(
                    g_product_state.settings.presentation_fps_mode),
                output_resolution_name(
                    g_product_state.settings.output_resolution).c_str());
            std::fflush(stderr);
        }
    } else if (loaded.status == ur::product::HostProductLoadStatus::Missing) {
        product_diagnostic("UR_HOST_STATE MISSING_DEFAULTS");
    } else if (loaded.status == ur::product::HostProductLoadStatus::Rejected) {
        product_diagnostic("UR_HOST_STATE REJECTED_DEFAULTS");
    } else {
        product_diagnostic("UR_HOST_STATE IO_ERROR_DEFAULTS");
    }

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
    }
    return g_session != nullptr;
}

bool restart_surface() {
    return g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ||
           g_surface == UR_UNIRACERS_RESTART_RESULTS;
}

bool exit_to_frontend() {
    if (!modern_mode() || !restart_surface()) {
        product_diagnostic("UR_EXIT_FRONTEND REJECTED_UNSAFE_SURFACE");
        return false;
    }

    const int source_surface = static_cast<int>(g_surface);
    const uint32_t before_sram = current_sram_digest();

    // Queue a full host-owned session rebuild. The request durably publishes
    // current cartridge SRAM before it can succeed; the host consumes it only
    // after the SDL callback returns, then rebuilds the guest through the same
    // snes_free + SnesInit + RtlReadSram lifecycle used for framework session
    // replacement. No guest PC, WRAM menu byte or progression state is forged.
    if (!snesrecomp_desktop_request_session_reboot()) {
        product_diagnostic("UR_EXIT_FRONTEND RESET_REQUEST_FAILED");
        return false;
    }

    g_options_visible = false;
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
            "UR_EXIT_FRONTEND REQUESTED source=%d sram=%08X\n",
            source_surface,
            static_cast<unsigned>(before_sram));
        std::fflush(stderr);
    }
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

UrUniracersRunData current_run_data() {
    return ur_uniracers_read_run_data(g_ram, 0x20000u);
}

void close_host_subview() {
    if (g_options_visible) {
        g_options_visible = false;
        product_diagnostic("UR_PAUSE_OPTIONS CLOSED");
    }
    if (g_controls_visible) {
        g_controls_visible = false;
        product_diagnostic("UR_PAUSE_CONTROLS CLOSED");
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
        ur_modern_options_menu_reset(&g_options_menu);
        product_diagnostic("UR_PAUSE_OPTIONS OPENED");
        return true;
    }
    if (selected == UR_MODERN_PAUSE_CONTROLS) {
        g_options_visible = false;
        g_run_data_visible = false;
        g_controls_visible = true;
        product_diagnostic("UR_PAUSE_CONTROLS OPENED");
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
    if (selected == UR_MODERN_PAUSE_QUIT) {
        g_options_visible = false;
        g_controls_visible = false;
        g_run_data_visible = false;
        g_quit_confirm_visible = true;
        product_diagnostic("UR_PAUSE_QUIT CONFIRM_OPENED");
        return true;
    }
    return dispatch(UR_MODERN_PAUSE_ACTIVATE);
}

}  // namespace

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
    if (!frame_width || !frame_height || !authentic_16x9_view_enabled()) {
        return;
    }

    const auto plan = ur::product::resolve_16x9_output_composition(
        ur::product::HostGraphicsRepresentation::Original,
        g_widescreen_scene);
    *frame_width = plan.logical_view_width;
    *frame_height = plan.logical_view_height;
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
        ur::product::HostGraphicsRepresentation::Original,
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

extern "C" void ur_uniracers_modern_after_run_frame(
    const SnesDesktopHostFrameStats*) {
    report_display_capabilities_once();
    if (!ensure_session()) return;

    const UrUniracersRestartDecision decision =
        ur_uniracers_restart_policy_observe(
            &g_title_policy,
            g_ram[0x0313],
            g_ram[0x009F]);
    g_surface = decision.surface;
    g_widescreen_scene = ur::product::observe_widescreen_scene(
        &g_widescreen_scene_state,
        g_ram[0x0313],
        g_ram[0x009F]);

    if (g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
        ur_modern_session_observe_race_active(g_session, 1);
    } else {
        ur_modern_session_observe_race_active(g_session, 0);
        if (decision.retire_attempt) {
            ur_modern_session_retire_race_attempt(g_session);
        }
    }

    maybe_run_exit_frontend_acceptance();

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

    apply_focus_pause_policy();
}

extern "C" int ur_uniracers_modern_system_key_down(
    int key,
    int mod,
    int repeat) {
    if (repeat || !ensure_session()) return 0;

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
    if (key == SDLK_r && (mod & KMOD_CTRL) &&
        restart_surface() &&
        ur_modern_session_restart_available(g_session)) {
        return dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY) ? 1 : 0;
    }
    return 0;
}

extern "C" int ur_uniracers_modern_system_gamepad_button(
    int button,
    int pressed) {
    if (!ensure_session()) return 0;

    if (!pressed) {
        return paused() ? 1 : 0;
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

extern "C" void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!ensure_session() || !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }

    const int is_paused = paused() ? 1 : 0;
    const int results = g_surface == UR_UNIRACERS_RESTART_RESULTS;
    const int restart = ur_modern_session_restart_available(g_session);
    if (!is_paused && !(results && restart)) return;

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const int panel_w = width < 220 ? width - 16 : 212;
    const int panel_h = is_paused ? (restart ? 129 : 114) : 30;
    const int x = (width - panel_w) / 2;
    const int y = is_paused ? (height - panel_h) / 2 : height - panel_h - 8;

    snes_ovl_fill_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xE0202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);

    if (is_paused) {
        if (g_options_visible) {
            const int options_h = 144;
            const int options_y = (height - options_h) / 2;
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
            snes_ovl_fill_rect(
                pixels, stride, height, x, options_y, panel_w, options_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, x, options_y, panel_w, options_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 7,
                "OPTIONS", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 27,
                focus_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 42,
                display_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 57,
                vsync_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 72,
                presentation_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 87,
                resolution_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 107,
                "A / ENTER  CHANGE", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 127,
                "B / ESC    BACK", 0xFFFFFFFFu, 1);
            return;
        }

        if (g_controls_visible) {
            const int controls_h = 99;
            const int controls_y = (height - controls_h) / 2;
            snes_ovl_fill_rect(
                pixels, stride, height, x, controls_y, panel_w, controls_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, x, controls_y, panel_w, controls_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 7,
                "CONTROLS", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 22,
                "MOVE   DPAD / ARROWS", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 37,
                "ACTION A / ENTER", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 52,
                "PAUSE  START / ESC", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 67,
                "BACK   B / ESC", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, controls_y + 82,
                "CTRL+R RETRY", 0xFFFFFFFFu, 1);
            return;
        }

        if (g_quit_confirm_visible) {
            const int quit_h = 69;
            const int quit_y = (height - quit_h) / 2;
            snes_ovl_fill_rect(
                pixels, stride, height, x, quit_y, panel_w, quit_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, x, quit_y, panel_w, quit_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, quit_y + 7,
                "QUIT TO DESKTOP?", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, quit_y + 27,
                "A / ENTER  CONFIRM", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, quit_y + 47,
                "B / ESC    CANCEL", 0xFFFFFFFFu, 1);
            return;
        }

        if (g_run_data_visible) {
            const UrUniracersRunData data = current_run_data();
            const int run_h = 84;
            const int run_y = (height - run_h) / 2;
            char time_text[32];
            if (data.valid) {
                std::snprintf(
                    time_text,
                    sizeof(time_text),
                    "TIME   %d:%d%d.%d",
                    data.minutes,
                    data.tens_seconds,
                    data.seconds,
                    data.tenths);
            } else {
                std::snprintf(time_text, sizeof(time_text), "TIME   --:--.-");
            }
            const char* surface_text =
                g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE
                    ? "SURFACE RACE"
                    : (g_surface == UR_UNIRACERS_RESTART_RESULTS
                        ? "SURFACE RESULTS"
                        : "SURFACE OTHER");
            const char* retry_text =
                ur_modern_session_restart_available(g_session)
                    ? "RETRY  READY" : "RETRY  UNAVAILABLE";

            snes_ovl_fill_rect(
                pixels, stride, height, x, run_y, panel_w, run_h,
                0xE0202020u);
            snes_ovl_stroke_rect(
                pixels, stride, height, x, run_y, panel_w, run_h,
                0xFFF0F0F0u);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, run_y + 7,
                "RUN DATA", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, run_y + 22,
                time_text, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, run_y + 37,
                surface_text, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, run_y + 52,
                retry_text, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, run_y + 67,
                "BACK   B / ESC", 0xFFFFFFFFu, 1);
            return;
        }

        ur_modern_pause_menu_move(&g_pause_menu, 0, restart);
        const UrModernPauseItem selected =
            ur_modern_pause_menu_selected(&g_pause_menu, restart);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 7,
            "PAUSED", 0xFFFFFFFFu, 1);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 22,
            selected == UR_MODERN_PAUSE_RESUME ? "> RESUME" : "  RESUME",
            0xFFFFFFFFu, 1);
        if (restart) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + 37,
                selected == UR_MODERN_PAUSE_RESTART
                    ? "> RESTART" : "  RESTART",
                0xFFFFFFFFu, 1);
        }
        const int options_y = restart ? y + 52 : y + 37;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, options_y,
            selected == UR_MODERN_PAUSE_OPTIONS
                ? "> OPTIONS" : "  OPTIONS",
            0xFFFFFFFFu, 1);
        const int controls_y = options_y + 15;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, controls_y,
            selected == UR_MODERN_PAUSE_CONTROLS
                ? "> CONTROLS" : "  CONTROLS",
            0xFFFFFFFFu, 1);
        const int run_data_y = controls_y + 15;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, run_data_y,
            selected == UR_MODERN_PAUSE_RUN_DATA
                ? "> RUN DATA" : "  RUN DATA",
            0xFFFFFFFFu, 1);
        const int exit_y = run_data_y + 15;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, exit_y,
            selected == UR_MODERN_PAUSE_EXIT_FRONTEND
                ? "> EXIT FRONTEND" : "  EXIT FRONTEND",
            0xFFFFFFFFu, 1);
        const int quit_y = exit_y + 15;
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, quit_y,
            selected == UR_MODERN_PAUSE_QUIT
                ? "> QUIT DESKTOP" : "  QUIT DESKTOP",
            0xFFFFFFFFu, 1);
    } else {
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 11,
            "START / CTRL+R  RETRY", 0xFFFFFFFFu, 1);
    }
}
