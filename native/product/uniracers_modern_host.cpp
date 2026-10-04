#include "uniracers_modern_host.h"

extern "C" {
#include "common_rtl.h"
#include "snes_overlay_draw.h"
}

#include "desktop/config.h"
#include "desktop/host_main.h"
#include "desktop/sdl_compat.h"
#include "completed_run_capture.hpp"
#include "completed_run_ghost.hpp"
#include "completed_run_ghost_frame.hpp"
#include "completed_run_ghost_policy.hpp"
#include "completed_run_ghost_trace.hpp"
#include "completed_run_ghost_world_sample.hpp"
#include "completed_run_record.hpp"
#include "completed_run_store.hpp"
#include "focus_pause_policy.hpp"
#include "host_product_state.hpp"
#include "host_product_store.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_state.hpp"
#include "host_profile_store.hpp"
#include "modern_pause_input.h"
#include "modern_pause_menu.h"
#include "modern_options_menu.h"
#include "modern_session_c_api.h"
#include "output_resolution_runtime_policy.hpp"
#include "uniracers_course_identity.h"
#include "uniracers_restart_policy.h"
#include "uniracers_run_data.h"
#include "uniracers_ws_margins.h"
#include "uniracers_tour_resume.hpp"
#include "widescreen_output_composition.hpp"
#include "../presentation/completed_run_ghost_racer_selector.hpp"
#include "../presentation/completed_run_ghost_raster.hpp"

#include <cstdlib>
#include <fstream>
#include <cstring>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

extern "C" void snesrecomp_desktop_arm_relative_input(uint64_t post_frame_origin);

namespace {

UrModernSession* g_session;
ur::product::HostProductState g_product_state;
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
bool g_controls_visible;
bool g_run_data_visible;
bool g_quit_confirm_visible;
bool g_display_caps_reported;
bool g_profile_sram_reported;
bool g_exit_frontend_waiting_for_main;
bool g_exit_frontend_waiting_for_usable;
bool g_exit_frontend_acceptance_fired;
unsigned g_exit_frontend_acceptance_surface_frames;
ur::product::CompletedRunCapture g_run_capture;
ur::product::CompletedRunGhostState g_run_ghosts;
ur::product::CompletedRunGhostTraceCapture g_run_ghost_trace_capture;
std::optional<ur::product::CompletedRunGhostTrace> g_run_ghost_playback_trace;
std::optional<ur::product::CompletedRunGhostPresentationFrame>
    g_run_ghost_presentation_frame;
bool g_run_capture_previous_active;
bool g_run_ghost_draw_reported;
uint64_t g_run_capture_origin_frame;
uint16_t g_run_capture_checkpoint;
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
void product_diagnostic(const char* message);
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
            resolved.status !=
            ur::product::HostProfileResolveStatus::DefaultedMalformed;
        if (!g_profile_state_writable) {
            product_diagnostic("UR_PROFILE_STATE MALFORMED_READ_ONLY");
        }
    } else {
        g_profile_state.reset();
        g_profile_state_path.clear();
        g_profile_state_writable = false;
        product_diagnostic("UR_PROFILE_STATE LOAD_FAILED");
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
    if (std::getenv("URRECOMP_WS_MARGIN")) return;
    const char* explicit_view = std::getenv("URRECOMP_WS_VIEW");
    if (explicit_view && *explicit_view) return;

    const bool enabled =
        g_product_state.settings.widescreen_mode ==
        ur::product::HostWidescreenMode::Authentic16x9;
#if defined(_WIN32)
    _putenv_s("URRECOMP_WS_VIEW", enabled ? "authentic-16x9" : "");
#else
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
                "UR_HOST_STATE LOADED pause_on_focus_loss=%d display_mode=%s vsync=%s presentation_fps=%s output_resolution=%s widescreen=%s\n",
                g_product_state.settings.pause_on_focus_loss ? 1 : 0,
                display_mode_name(g_product_state.settings.display_mode),
                vsync_mode_name(g_product_state.settings.vsync_mode),
                presentation_fps_mode_name(
                    g_product_state.settings.presentation_fps_mode),
                output_resolution_name(
                    g_product_state.settings.output_resolution).c_str(),
                widescreen_mode_name(
                    g_product_state.settings.widescreen_mode));
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
    case UR_MODERN_OPTIONS_WIDESCREEN:
        return cycle_widescreen_setting();
    case UR_MODERN_OPTIONS_GHOST:
        return cycle_ghost_target_setting();
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

bool save_active_profile_state(
    const std::optional<ur::product::HostTourContinuation>& continuation,
    const char* diagnostic) {
    if (!modern_mode() || !g_profile_state || !g_profile_state_writable ||
        g_profile_state_path.empty() || !g_sram ||
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

    // Stock TRACK_SELECT is the first stable point after rider/tour
    // confirmation. Rider select has already performed its historical wipe.
    if (g_ram[0x009F] == 0xF6 && g_profile_state->tour_continuation) {
        const auto saved =
            title_continuation(*g_profile_state->tour_continuation);

        if (current->rider_index == saved.rider_index &&
            current->tour_row == saved.tour_row &&
            current->medal_value != saved.medal_value) {
            (void)save_active_profile_state(
                std::nullopt,
                "UR_TOUR_RESUME CLEARED_STALE_MEDAL");
            return;
        }

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
    return modern_mode() &&
           g_widescreen_scene_state.race_mode ==
               ur::product::HostRacePresentationMode::OnePlayer;
}

std::string default_run_record_directory() {
    if (!run_record_capture_enabled()) return {};
    ensure_product_state();

    char* pref_path = SDL_GetPrefPath("gamesbyian", "UR-Recomp");
    if (!pref_path) return {};
    std::string path(pref_path);
    SDL_free(pref_path);
    path += "runs/";
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

void observe_run_record_split() {
    if (!g_run_capture.capturing()) return;
    const uint16_t checkpoint = read_run_word(0x1199u);
    if (checkpoint == g_run_capture_checkpoint) return;

    const int64_t ticks60 = ur_uniracers_run_data_ticks60(current_run_data());
    if (ticks60 >= 0) {
        const std::string id = "checkpoint-" + std::to_string(checkpoint);
        (void)g_run_capture.observe_split(
            id, static_cast<uint64_t>(ticks60));
    }
    g_run_capture_checkpoint = checkpoint;
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
    g_run_ghost_trace_capture.abort_attempt();
    g_run_ghosts.clear();
    g_run_ghost_playback_trace.reset();
    g_run_ghost_presentation_frame.reset();
    g_run_capture_previous_active = false;
    product_diagnostic("UR_RUN_RECORD RETRY_REARMED");
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
    if (selected == UR_MODERN_PAUSE_RESTART) {
        const bool handled = dispatch(UR_MODERN_PAUSE_ACTIVATE);
        if (handled) rearm_run_capture_after_retry();
        return handled;
    }
    return dispatch(UR_MODERN_PAUSE_ACTIVATE);
}

}  // namespace

extern "C" void ur_uniracers_modern_after_config(void) {
    apply_profile_save_root();
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
    if (!frame_width || !frame_height || !authentic_16x9_view_enabled()) {
        return;
    }

    const auto plan = ur::product::resolve_16x9_output_composition(
        ur::product::HostGraphicsRepresentation::Original,
        g_widescreen_scene);
    *frame_width = plan.logical_view_width;
    *frame_height = plan.logical_view_height;

    // Every widened race presents its margins host-side; split-screen
    // viewports each get their own band origin in the shared store.
    ur_ws_margins_prepare_frame(
        plan.expose_added_world ? 1 : 0,
        (plan.logical_view_width - 256) / 2);
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
    g_widescreen_scene = ur::product::observe_widescreen_scene(
        &g_widescreen_scene_state,
        g_ram[0x0313],
        g_ram[0x009F]);

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
    if (stats && !g_run_capture_previous_active && run_active) {
        (void)begin_run_record_capture(stats->frame);
    }
    if (run_active && g_run_capture.capturing()) {
        observe_run_record_split();
    }
    if (g_surface == UR_UNIRACERS_RESTART_RESULTS &&
        g_run_capture.capturing()) {
        complete_run_record_capture();
    }
    if (decision.retire_attempt && g_run_capture.capturing()) {
        g_run_capture.abort_attempt();
        g_run_ghost_trace_capture.abort_attempt();
        g_run_ghost_playback_trace.reset();
        g_run_ghost_presentation_frame.reset();
    }
    g_run_capture_previous_active = run_active;

    reconcile_tour_resume();

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
        const bool handled = dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY);
        if (handled) rearm_run_capture_after_retry();
        return handled ? 1 : 0;
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
                        128);
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
            const int options_h = 174;
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
            char widescreen_row[32];
            char ghost_row[32];
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
                widescreen_row, sizeof(widescreen_row), "%c VIEW     %s",
                selected == UR_MODERN_OPTIONS_WIDESCREEN ? '>' : ' ',
                g_product_state.settings.widescreen_mode ==
                        ur::product::HostWidescreenMode::Authentic16x9
                    ? "16:9" : "ORIGINAL");
            std::snprintf(
                ghost_row, sizeof(ghost_row), "%c GHOST    %s",
                selected == UR_MODERN_OPTIONS_GHOST ? '>' : ' ',
                ur::product::completed_run_ghost_target_name(
                    active_run_ghost_target()));
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
                pixels, stride, height, x + 8, options_y + 102,
                widescreen_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 117,
                ghost_row, 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 137,
                "A / ENTER  CHANGE", 0xFFFFFFFFu, 1);
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, options_y + 157,
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
