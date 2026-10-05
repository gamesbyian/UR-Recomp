#include "completed_run_browser_host.h"

extern "C" {
#include "common_rtl.h"
#include "snes_overlay_draw.h"
}

#include "desktop/config.h"
#include "desktop/host_main.h"
#include "desktop/sdl_compat.h"
#include "completed_run_browser.hpp"
#include "completed_run_replay.hpp"
#include "host_product_store.hpp"
#include "modern_host_navigation.h"
#include "uniracers_course_identity.h"
#include "uniracers_modern_host.h"
#include "uniracers_restart_policy.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <optional>
#include <string>

namespace {

namespace fs = std::filesystem;

ur::product::CompletedRunBrowser g_browser;
ur::product::CompletedRunReplayFlow g_replay_flow;
UrUniracersRestartPolicyState g_replay_policy;
bool g_browser_visible;
bool g_one_player_context;
std::uint64_t g_last_host_frame;
unsigned g_browser_acceptance_active_frames;
bool g_browser_acceptance_fired;

bool modern_mode() {
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return !(mode && std::strcmp(mode, "authentic") == 0);
}

void diagnostic(const char* message) {
    if (!std::getenv("UR_PRODUCT_DIAGNOSTICS")) return;
    std::fprintf(stderr, "%s\n", message);
    std::fflush(stderr);
}

std::string pref_root() {
    char* pref_path = SDL_GetPrefPath("gamesbyian", "UR-Recomp");
    if (!pref_path) return {};
    std::string root(pref_path);
    SDL_free(pref_path);
    return root;
}

std::string active_profile_id() {
    const std::string root = pref_root();
    if (root.empty()) return "default";

    const char* override_path = std::getenv("UR_HOST_STATE_PATH");
    const std::string state_path =
        override_path && *override_path
            ? std::string(override_path)
            : root + "host-state-v1.txt";
    const auto loaded = ur::product::load_host_product_state_file(
        state_path);
    if (!loaded.loaded() || !loaded.state ||
        !loaded.state->active_profile_id) {
        return "default";
    }
    return *loaded.state->active_profile_id;
}

std::string active_run_directory() {
    if (std::getenv("UR_RUN_BROWSER_ACCEPTANCE")) {
        const char* override_directory =
            std::getenv("UR_RUN_BROWSER_DIRECTORY");
        if (override_directory && *override_directory) {
            return override_directory;
        }
    }

    const std::string root = pref_root();
    if (root.empty()) return {};
    return root + "runs/" + active_profile_id();
}

std::optional<ur::product::RunPlaybackTarget> current_target() {
    if (!modern_mode() || !g_one_player_context) return std::nullopt;

    const UrUniracersCourseIdentity course =
        ur_uniracers_identify_course(g_ram + 0x10000u, 0x10000u);
    if (!course.valid) return std::nullopt;
    const int tour_slot = ((course.course_index - 1) % 5) + 1;
    if (tour_slot != 1 && tour_slot != 4) return std::nullopt;

    char course_id[32];
    std::snprintf(
        course_id, sizeof(course_id), "course:%02d", course.course_index);
    return ur::product::RunPlaybackTarget{
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1",
        course_id,
        "race-1p",
    };
}

bool refresh_browser() {
    const auto target = current_target();
    const std::string directory = active_run_directory();
    if (!target || directory.empty()) {
        g_browser.clear();
        return false;
    }
    return g_browser.refresh(directory, *target);
}

void close_browser() {
    g_browser_visible = false;
    diagnostic("UR_RUN_BROWSER CLOSED");
}

bool normalize_base_pause_surface() {
    if (!snesrecomp_desktop_is_paused()) return false;

    // ESC closes an active Modern subview without resuming. On the base pause
    // surface it resumes instead. If that happens, issue ESC once more before
    // the host loop can run a guest frame; this restores a clean base pause
    // and resets the ordinary pause-menu selection.
    (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    if (!snesrecomp_desktop_is_paused()) {
        (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    }
    return snesrecomp_desktop_is_paused() != 0;
}

bool open_browser() {
    const UrUniracersRestartSurface surface =
        ur_uniracers_classify_restart_surface(
            g_ram[0x0313], g_ram[0x009F]);
    if (!modern_mode() || !snesrecomp_desktop_is_paused() ||
        !g_one_player_context ||
        (surface != UR_UNIRACERS_RESTART_ACTIVE_RACE &&
         surface != UR_UNIRACERS_RESTART_RESULTS)) {
        return false;
    }
    if (!normalize_base_pause_surface() || !refresh_browser()) return false;
    g_browser_visible = true;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RUN_BROWSER OPENED entries=%zu playable=%zu profile=%s\n",
            g_browser.size(),
            g_browser.playable_count(),
            active_profile_id().c_str());
        for (std::size_t index = 0; index < g_browser.entries().size(); ++index) {
            const auto& entry = g_browser.entries()[index];
            std::fprintf(
                stderr,
                "UR_RUN_BROWSER ENTRY index=%zu order=%zu status=%s playable=%d previous=%d pb=%d course=%s date=%s time=%s\n",
                index,
                entry.chronological_order,
                ur::product::completed_run_browser_status_name(entry.status),
                entry.playable() ? 1 : 0,
                entry.is_previous ? 1 : 0,
                entry.is_personal_best ? 1 : 0,
                entry.course_id.c_str(),
                entry.date_text.c_str(),
                entry.time_text.c_str());
        }
        std::fflush(stderr);
    }
    return true;
}

std::string replay_input_path() {
    const std::string root = pref_root();
    if (root.empty()) return {};
    const fs::path directory = fs::path(root) / "replay";
    std::error_code ec;
    fs::create_directories(directory, ec);
    if (ec) return {};
    return (directory / "selected-run.input").string();
}

bool launch_selected_replay() {
    if (!g_browser_visible || !modern_mode() ||
        !snesrecomp_desktop_is_paused()) {
        return false;
    }
    const auto* selected = g_browser.selected();
    if (!selected || !selected->playable() || !selected->record) {
        return false;
    }

    const std::string input_path = replay_input_path();
    std::string detail;
    if (input_path.empty() ||
        !ur::product::stage_completed_run_replay_input_file(
            input_path, *selected->record, &detail)) {
        diagnostic("UR_RUN_BROWSER REPLAY_STAGE_FAILED");
        return false;
    }

    if (!snesrecomp_desktop_load_relative_input_file(input_path.c_str())) {
        diagnostic("UR_RUN_BROWSER REPLAY_LOAD_FAILED");
        return false;
    }

    // Reuse the existing Modern Restart command so the replay always starts
    // from the same lifecycle-owned race-entry anchor as Retry.
    if (!ur_uniracers_modern_system_key_down(SDLK_r, KMOD_CTRL, 0)) {
        (void)snesrecomp_desktop_load_relative_input_file(nullptr);
        diagnostic("UR_RUN_BROWSER REPLAY_RESTART_FAILED");
        return false;
    }

    ur_uniracers_restart_policy_reset(&g_replay_policy);
    if (!g_replay_flow.begin()) {
        (void)snesrecomp_desktop_load_relative_input_file(nullptr);
        return false;
    }

    snesrecomp_desktop_arm_relative_input(g_last_host_frame);
    g_browser_visible = false;

    // Restart deliberately preserves pause state. Resume through the same
    // host-owned pause path after input has been armed.
    if (snesrecomp_desktop_is_paused()) {
        (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    }

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RUN_BROWSER REPLAY_LAUNCHED order=%zu course=%s ticks60=%llu\n",
            selected->chronological_order,
            selected->record->provenance.course_id.c_str(),
            static_cast<unsigned long long>(
                selected->record->elapsed_ticks60));
        std::fflush(stderr);
    }
    return true;
}

void return_to_browser(
    const SnesDesktopHostFrameStats* stats,
    bool completed) {
    (void)snesrecomp_desktop_load_relative_input_file(nullptr);

    // Re-enter the ordinary Modern host exactly once at the terminal surface
    // so its pause/results/frontend policy is synchronized before the browser
    // becomes visible again. Replay frames themselves deliberately bypass the
    // run-capture/ghost path, keeping playback from creating duplicate runs.
    ur_uniracers_modern_after_run_frame(stats);

    if (completed) {
        if (!snesrecomp_desktop_is_paused()) {
            (void)ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
        }
        (void)refresh_browser();
        g_browser_visible = true;
        diagnostic("UR_RUN_BROWSER REPLAY_RETURNED");
        const char* acceptance = std::getenv("UR_RUN_BROWSER_ACCEPTANCE");
        if (acceptance && std::strcmp(acceptance, "quit-after-return") == 0) {
            SDL_Event event{};
            event.type = SDL_QUIT;
            (void)SDL_PushEvent(&event);
        }
    } else {
        diagnostic("UR_RUN_BROWSER REPLAY_CANCELLED");
    }
}

bool browser_navigation(UrModernHostNavigationAction action) {
    if (!g_browser_visible) return false;

    const int delta = ur_modern_host_navigation_vertical_delta(action);
    if (delta != 0) {
        (void)g_browser.move(delta);
        return true;
    }
    if (ur_modern_host_navigation_is_confirm(action)) {
        if (!launch_selected_replay()) {
            diagnostic("UR_RUN_BROWSER REPLAY_REJECTED");
        }
        return true;
    }
    if (ur_modern_host_navigation_is_back(action)) {
        close_browser();
        return true;
    }
    return true;
}

void maybe_run_browser_acceptance() {
    if (g_browser_acceptance_fired || !modern_mode() ||
        !std::getenv("UR_RUN_BROWSER_ACCEPTANCE")) {
        return;
    }

    const UrUniracersRestartSurface surface =
        ur_uniracers_classify_restart_surface(
            g_ram[0x0313], g_ram[0x009F]);
    if (surface != UR_UNIRACERS_RESTART_ACTIVE_RACE ||
        !g_one_player_context) {
        g_browser_acceptance_active_frames = 0;
        return;
    }

    // Stay behind the settled race-entry checkpoint used by native scripts
    // and behind restart-anchor capture before exercising the player path.
    if (++g_browser_acceptance_active_frames < 90) return;

    g_browser_acceptance_fired = true;
    const int pause_handled =
        ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    const bool opened = pause_handled && open_browser();
    const bool launched = opened && launch_selected_replay();

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RUN_BROWSER ACCEPTANCE_TRIGGER pause=%d opened=%d launched=%d entries=%zu playable=%zu\n",
            pause_handled,
            opened ? 1 : 0,
            launched ? 1 : 0,
            g_browser.size(),
            g_browser.playable_count());
        std::fflush(stderr);
    }
}

void update_context_from_guest() {
    if (g_ram[0x0313] == 0x01) return;
    switch (g_ram[0x009F]) {
    case 0x3C:
        g_one_player_context = true;
        break;
    case 0x3D:
    case 0x3E:
        g_one_player_context = false;
        break;
    default:
        break;
    }
}

void draw_browser(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!g_browser_visible || !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const int panel_w = width < 244 ? width - 12 : 236;
    const int row_count = 6;
    const int panel_h = 39 + row_count * 15 + 31;
    const int x = (width - panel_w) / 2;
    const int y = (height - panel_h) / 2;

    snes_ovl_fill_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xEE202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);

    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + 7,
        "LOCAL RUNS", 0xFFFFFFFFu, 1);

    char summary[48];
    std::snprintf(
        summary, sizeof(summary), "%zu PLAYABLE / %zu STORED",
        g_browser.playable_count(), g_browser.size());
    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + 22,
        summary, 0xFFFFFFFFu, 1);

    std::size_t first = 0;
    if (const auto selected = g_browser.selected_index()) {
        if (*selected >= static_cast<std::size_t>(row_count)) {
            first = *selected - static_cast<std::size_t>(row_count) + 1;
        }
    }

    for (int row = 0; row < row_count; ++row) {
        const std::size_t index = first + static_cast<std::size_t>(row);
        if (index >= g_browser.entries().size()) break;

        const auto& entry = g_browser.entries()[index];
        char line[96];
        if (entry.playable()) {
            std::string tags;
            if (entry.is_personal_best) tags += " PB";
            if (entry.is_previous) tags += " PREV";
            const std::string course =
                entry.course_id.rfind("course:", 0) == 0
                    ? "C" + entry.course_id.substr(7)
                    : entry.course_id;
            std::snprintf(
                line, sizeof(line), "%c #%03zu %s %s %s%s",
                g_browser.selected_index() &&
                        *g_browser.selected_index() == index
                    ? '>' : ' ',
                entry.chronological_order,
                course.c_str(),
                entry.date_text.c_str(),
                entry.time_text.c_str(),
                tags.c_str());
        } else {
            std::snprintf(
                line, sizeof(line), "  #%03zu %s %s %s",
                entry.chronological_order,
                entry.date_text.c_str(),
                entry.course_id.c_str(),
                ur::product::completed_run_browser_status_name(
                    entry.status));
        }
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 42 + row * 15,
            line, 0xFFFFFFFFu, 1);
    }

    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + panel_h - 26,
        "ENTER / A  REPLAY", 0xFFFFFFFFu, 1);
    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + panel_h - 11,
        "ESC / B    BACK", 0xFFFFFFFFu, 1);
}

void draw_browser_hint(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!modern_mode() || g_browser_visible || g_replay_flow.active() ||
        !g_one_player_context || !snesrecomp_desktop_is_paused() ||
        !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }
    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    snes_ovl_draw_text(
        pixels, stride, height, 8, height - 13,
        "CTRL+B / X  LOCAL RUNS", 0xFFFFFFFFu, 1);
}

}  // namespace

extern "C" void ur_uniracers_product_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    if (stats) g_last_host_frame = stats->frame;

    if (!g_replay_flow.active()) {
        ur_uniracers_modern_after_run_frame(stats);
        update_context_from_guest();
        maybe_run_browser_acceptance();
        return;
    }

    const UrUniracersRestartDecision decision =
        ur_uniracers_restart_policy_observe(
            &g_replay_policy,
            g_ram[0x0313],
            g_ram[0x009F]);
    const auto transition = g_replay_flow.observe(
        decision.surface == UR_UNIRACERS_RESTART_ACTIVE_RACE,
        decision.surface == UR_UNIRACERS_RESTART_RESULTS,
        decision.retire_attempt != 0);

    if (transition == ur::product::CompletedRunReplayTransition::ReturnToBrowser) {
        return_to_browser(stats, true);
    } else if (transition == ur::product::CompletedRunReplayTransition::Cancelled) {
        return_to_browser(stats, false);
    }
}

extern "C" int ur_uniracers_product_system_key_down(
    int key,
    int mod,
    int repeat) {
    if (!modern_mode()) {
        return ur_uniracers_modern_system_key_down(key, mod, repeat);
    }

    if (g_replay_flow.active()) {
        return 1;
    }

    if (g_browser_visible) {
        if (repeat) return 1;
        if (key == SDLK_UP) {
            return browser_navigation(UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (key == SDLK_DOWN) {
            return browser_navigation(UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            return browser_navigation(UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        if (key == SDLK_ESCAPE) {
            return browser_navigation(UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        }
        return 1;
    }

    if (key == SDLK_b && (mod & KMOD_CTRL) &&
        snesrecomp_desktop_is_paused()) {
        (void)open_browser();
        return 1;
    }

    if (repeat) return 0;
    return ur_uniracers_modern_system_key_down(key, mod, repeat);
}

extern "C" int ur_uniracers_product_system_gamepad_button(
    int button,
    int pressed) {
    if (!modern_mode()) {
        return ur_uniracers_modern_system_gamepad_button(button, pressed);
    }

    if (g_replay_flow.active()) {
        return 1;
    }

    if (g_browser_visible) {
        if (!pressed) return 1;
        if (button == kGamepadBtn_DpadUp) {
            return browser_navigation(UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (button == kGamepadBtn_DpadDown) {
            return browser_navigation(UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (button == kGamepadBtn_A) {
            return browser_navigation(UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        if (button == kGamepadBtn_B) {
            return browser_navigation(UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        }
        return 1;
    }

    if (pressed && button == kGamepadBtn_X &&
        snesrecomp_desktop_is_paused()) {
        (void)open_browser();
        return 1;
    }

    return ur_uniracers_modern_system_gamepad_button(button, pressed);
}

extern "C" void ur_uniracers_product_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!g_replay_flow.active()) {
        ur_uniracers_modern_system_overlay(dst, pitch, width, height);
    }
    draw_browser(dst, pitch, width, height);
    draw_browser_hint(dst, pitch, width, height);
}
