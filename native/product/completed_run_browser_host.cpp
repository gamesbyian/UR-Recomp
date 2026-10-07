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
#include "quick_practice_catalog.hpp"
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
ur::product::CompletedRunRecordsBrowser g_records_browser;
ur::product::CompletedRunReplayFlow g_replay_flow;
UrUniracersRestartPolicyState g_replay_policy;
bool g_browser_visible;
bool g_records_browser_visible;
bool g_one_player_context;
std::uint64_t g_last_host_frame;
unsigned g_browser_acceptance_active_frames;
bool g_browser_acceptance_fired;
unsigned g_records_browser_acceptance_active_frames;
bool g_records_browser_acceptance_fired;

std::string records_course_label(const std::string& course_id) {
    if (course_id.size() == 9 &&
        course_id.compare(0, 7, "course:") == 0 &&
        course_id[7] >= '0' && course_id[7] <= '9' &&
        course_id[8] >= '0' && course_id[8] <= '9') {
        const int course_index =
            (course_id[7] - '0') * 10 + (course_id[8] - '0');
        if (course_index >= 1 && course_index <= 45) {
            const auto* course = ur::product::quick_practice_course(
                static_cast<std::uint8_t>(course_index - 1));
            if (course) return std::string(course->name);
        }
    }
    return course_id;
}

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
    if (std::getenv("UR_RUN_BROWSER_ACCEPTANCE") ||
        std::getenv("UR_RECORDS_BROWSER_ACCEPTANCE")) {
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

ur::product::RunRecordsScope records_scope() {
    return {
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1",
        "race-1p",
    };
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

bool records_selected_matches_current_course() {
    const auto* selected = g_records_browser.selected_course();
    const auto target = current_target();
    return selected && target &&
           selected->course_id == target->course_id;
}

bool refresh_records_browser() {
    const std::string directory = active_run_directory();
    if (directory.empty()) {
        g_records_browser.clear();
        return false;
    }
    return g_records_browser.refresh(directory, records_scope());
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

void close_records_browser() {
    g_records_browser_visible = false;
    diagnostic("UR_RECORDS_BROWSER CLOSED");
}

bool records_results_surface() {
    return ur_uniracers_classify_restart_surface(
               g_ram[0x0313], g_ram[0x009F]) ==
           UR_UNIRACERS_RESTART_RESULTS;
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

bool open_records_from_results() {
    if (!modern_mode() || snesrecomp_desktop_is_paused() ||
        !records_results_surface()) {
        return false;
    }

    // Enter the same host-owned pause authority used everywhere else before
    // opening Records. The browser remains a paused product surface and no
    // guest result state is mutated.
    if (!ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0) ||
        !snesrecomp_desktop_is_paused()) {
        return false;
    }
    const bool opened = open_records_browser();
    if (opened) diagnostic("UR_RECORDS_BROWSER OPENED_FROM_RESULTS");
    return opened;
}

bool open_records_browser() {
    if (!modern_mode() || !snesrecomp_desktop_is_paused()) {
        return false;
    }
    if (!normalize_base_pause_surface() || !refresh_records_browser()) {
        return false;
    }

    g_browser_visible = false;
    g_records_browser_visible = true;
    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RECORDS_BROWSER OPENED courses=%zu runs=%zu unavailable=%zu profile=%s\n",
            g_records_browser.index().courses.size(),
            g_records_browser.index().total_completed_runs,
            g_records_browser.unavailable_artifact_count(),
            active_profile_id().c_str());
        for (const auto& course : g_records_browser.index().courses) {
            std::fprintf(
                stderr,
                "UR_RECORDS_BROWSER COURSE course=%s runs=%zu pb=%s previous=%s delta=%s\n",
                course.course_id.c_str(),
                course.statistics.completed_runs,
                course.statistics.personal_best_text.c_str(),
                course.statistics.previous_text.c_str(),
                course.statistics.previous_vs_pb_text.c_str());
        }
        std::fflush(stderr);
    }
    return true;
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
    g_records_browser_visible = false;
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
        g_records_browser_visible = false;
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

bool records_browser_navigation(UrModernHostNavigationAction action) {
    if (!g_records_browser_visible) return false;

    const int delta = ur_modern_host_navigation_vertical_delta(action);
    if (delta != 0) {
        (void)g_records_browser.move(delta);
        return true;
    }
    if (ur_modern_host_navigation_is_confirm(action)) {
        if (g_records_browser.view() ==
            ur::product::CompletedRunRecordsView::Courses) {
            (void)g_records_browser.open_selected_course();
        } else if (g_records_browser.view() ==
                   ur::product::CompletedRunRecordsView::Runs) {
            (void)g_records_browser.open_selected_run_detail();
        }
        return true;
    }
    if (ur_modern_host_navigation_is_back(action)) {
        if (g_records_browser.view() ==
            ur::product::CompletedRunRecordsView::Detail) {
            (void)g_records_browser.back_to_runs();
        } else if (g_records_browser.view() ==
                   ur::product::CompletedRunRecordsView::Runs) {
            (void)g_records_browser.back_to_courses();
        } else {
            close_records_browser();
        }
        return true;
    }
    return true;
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

void maybe_run_records_browser_acceptance() {
    if (g_records_browser_acceptance_fired || !modern_mode() ||
        !std::getenv("UR_RECORDS_BROWSER_ACCEPTANCE")) {
        return;
    }

    const UrUniracersRestartSurface surface =
        ur_uniracers_classify_restart_surface(
            g_ram[0x0313], g_ram[0x009F]);
    if (surface != UR_UNIRACERS_RESTART_ACTIVE_RACE ||
        !g_one_player_context) {
        g_records_browser_acceptance_active_frames = 0;
        return;
    }

    if (++g_records_browser_acceptance_active_frames < 90) return;

    g_records_browser_acceptance_fired = true;
    const int pause_handled =
        ur_uniracers_modern_system_key_down(SDLK_ESCAPE, 0, 0);
    const bool opened = pause_handled && open_records_browser();
    const bool drilled =
        opened &&
        records_browser_navigation(UR_MODERN_HOST_NAV_CONFIRM);
    const bool detail =
        drilled &&
        records_browser_navigation(UR_MODERN_HOST_NAV_CONFIRM) &&
        g_records_browser.view() ==
            ur::product::CompletedRunRecordsView::Detail;
    const bool current_course =
        detail && records_selected_matches_current_course();
    const auto summary = g_records_browser.selected_run_summary();
    const auto previous_delta =
        g_records_browser.selected_run_previous_delta();

    if (std::getenv("UR_PRODUCT_DIAGNOSTICS")) {
        std::fprintf(
            stderr,
            "UR_RECORDS_BROWSER ACCEPTANCE_TRIGGER pause=%d opened=%d drilled=%d detail=%d current_course=%d courses=%zu runs=%zu finish=%s delta=%s previous=%s previous_delta=%s\n",
            pause_handled,
            opened ? 1 : 0,
            drilled ? 1 : 0,
            detail ? 1 : 0,
            current_course ? 1 : 0,
            g_records_browser.index().courses.size(),
            g_records_browser.index().total_completed_runs,
            summary ? summary->finish.clock_text.c_str() : "--",
            summary ? summary->finish.comparison_text.c_str() : "--",
            previous_delta ? previous_delta->target_text.c_str() : "--",
            previous_delta ? previous_delta->delta_text.c_str() : "--");
        std::fflush(stderr);
    }

    const char* acceptance =
        std::getenv("UR_RECORDS_BROWSER_ACCEPTANCE");
    if (acceptance &&
        std::strcmp(acceptance, "quit-after-open") == 0) {
        SDL_Event event{};
        event.type = SDL_QUIT;
        (void)SDL_PushEvent(&event);
    }
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

void draw_records_browser(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!g_records_browser_visible || !dst || pitch < 4 ||
        width <= 0 || height <= 0) {
        return;
    }

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const int panel_w = width < 244 ? width - 12 : 236;
    const int row_count = 7;
    const int panel_h = 39 + row_count * 15 + 60;
    const int x = (width - panel_w) / 2;
    const int y = (height - panel_h) / 2;

    snes_ovl_fill_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xEE202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);

    if (g_records_browser.view() ==
        ur::product::CompletedRunRecordsView::Courses) {
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 7,
            "RECORDS / TRACKS", 0xFFFFFFFFu, 1);

        char summary[80];
        const std::size_t unavailable =
            g_records_browser.unavailable_artifact_count();
        if (unavailable) {
            std::snprintf(
                summary, sizeof(summary), "%zu TRACKS / %zu RUNS  %zu UNAVAILABLE",
                g_records_browser.index().courses.size(),
                g_records_browser.index().total_completed_runs,
                unavailable);
        } else {
            std::snprintf(
                summary, sizeof(summary), "%zu TRACKS / %zu RUNS",
                g_records_browser.index().courses.size(),
                g_records_browser.index().total_completed_runs);
        }
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 22,
            summary, 0xFFFFFFFFu, 1);

        std::size_t first = 0;
        if (const auto selected = g_records_browser.selected_course_index()) {
            if (*selected >= static_cast<std::size_t>(row_count)) {
                first = *selected - static_cast<std::size_t>(row_count) + 1;
            }
        }

        if (g_records_browser.index().courses.empty()) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + 42,
                "NO RUNS RECORDED YET", 0xFFFFFFFFu, 1);
        }

        for (int row = 0; row < row_count; ++row) {
            const std::size_t index = first + static_cast<std::size_t>(row);
            if (index >= g_records_browser.index().courses.size()) break;
            const auto& course = g_records_browser.index().courses[index];
            const std::string course_label =
                records_course_label(course.course_id);
            char line[96];
            std::snprintf(
                line, sizeof(line), "%c %-13s %2zu PB %s",
                g_records_browser.selected_course_index() &&
                        *g_records_browser.selected_course_index() == index
                    ? '>' : ' ',
                course_label.c_str(),
                course.statistics.completed_runs,
                course.statistics.personal_best_text.c_str());
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + 42 + row * 15,
                line, 0xFFFFFFFFu, 1);
        }

        const auto* selected = g_records_browser.selected_course();
        char previous[80];
        std::snprintf(
            previous, sizeof(previous), "PREV %s  VS PB %s",
            selected ? selected->statistics.previous_text.c_str() : "--",
            selected ? selected->statistics.previous_vs_pb_text.c_str() : "--");
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + panel_h - 41,
            previous, 0xFFFFFFFFu, 1);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + panel_h - 26,
            "ENTER / A  RUNS", 0xFFFFFFFFu, 1);
    } else if (g_records_browser.view() ==
               ur::product::CompletedRunRecordsView::Runs) {
        const auto* course = g_records_browser.selected_course();
        const std::string course_label =
            course ? records_course_label(course->course_id) : "--";
        char title[64];
        std::snprintf(
            title, sizeof(title), "RECORDS / %s", course_label.c_str());
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 7,
            title, 0xFFFFFFFFu, 1);

        char summary[64];
        std::snprintf(
            summary, sizeof(summary), "%zu RUNS  PB %s",
            course ? course->statistics.completed_runs : 0u,
            course ? course->statistics.personal_best_text.c_str() : "--");
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 22,
            summary, 0xFFFFFFFFu, 1);

        if (course) {
            std::size_t first = 0;
            if (const auto selected = g_records_browser.selected_run_index()) {
                if (*selected >= static_cast<std::size_t>(row_count)) {
                    first = *selected - static_cast<std::size_t>(row_count) + 1;
                }
            }
            for (int row = 0; row < row_count; ++row) {
                const std::size_t index = first + static_cast<std::size_t>(row);
                if (index >= course->catalog.entries.size()) break;
                const auto& entry = course->catalog.entries[index];
                std::string tags;
                if (entry.is_personal_best) tags += " PB";
                if (entry.is_previous) tags += " PREV";
                const std::string date =
                    ur::product::completed_run_browser_date_text(entry.path);
                const std::string short_date =
                    date.size() == 10 ? date.substr(5) : date;
                char line[112];
                std::snprintf(
                    line, sizeof(line), "%c #%03zu %s %s%s",
                    g_records_browser.selected_run_index() &&
                            *g_records_browser.selected_run_index() == index
                        ? '>' : ' ',
                    entry.source_index + 1,
                    short_date.c_str(),
                    entry.time_text.c_str(),
                    tags.c_str());
                snes_ovl_draw_text(
                    pixels, stride, height, x + 8, y + 42 + row * 15,
                    line, 0xFFFFFFFFu, 1);
            }
        }

        const auto* selected = g_records_browser.selected_run();
        char comparison[80];
        std::snprintf(
            comparison, sizeof(comparison), "VS PB %s",
            selected ? selected->personal_best_delta_text.c_str() : "--");
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + panel_h - 56,
            comparison, 0xFFFFFFFFu, 1);
        if (records_selected_matches_current_course()) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + panel_h - 41,
                "CTRL+B / X  LOCAL RUNS", 0xFFFFFFFFu, 1);
        }
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + panel_h - 26,
            "ESC / B    COURSES", 0xFFFFFFFFu, 1);
    } else {
        const auto* course = g_records_browser.selected_course();
        const auto* selected = g_records_browser.selected_run();
        const auto summary = g_records_browser.selected_run_summary();
        const auto previous_delta =
            g_records_browser.selected_run_previous_delta();
        const std::string course_label =
            course ? records_course_label(course->course_id) : "--";

        char title[80];
        std::snprintf(
            title, sizeof(title), "RECORDS / %s / RUN", course_label.c_str());
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 7,
            title, 0xFFFFFFFFu, 1);

        const std::string run_date = selected
            ? ur::product::completed_run_browser_date_text(selected->path)
            : "--";
        char run_label[96];
        std::snprintf(
            run_label, sizeof(run_label), "RUN #%03zu  %s%s%s",
            selected ? selected->source_index + 1 : 0u,
            run_date.c_str(),
            selected && selected->is_personal_best ? "  PB" : "",
            selected && selected->is_previous ? "  PREV" : "");
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 22,
            run_label, 0xFFFFFFFFu, 1);

        char finish[80];
        char pb[96];
        char previous[96];
        std::snprintf(
            finish, sizeof(finish), "FINISH  %s",
            summary ? summary->finish.clock_text.c_str() : "--");
        std::snprintf(
            pb, sizeof(pb), "PB      %s  %s",
            summary ? summary->finish.target_text.c_str() : "--",
            summary ? summary->finish.comparison_text.c_str() : "--");
        std::snprintf(
            previous, sizeof(previous), "PREV    %s  %s",
            previous_delta ? previous_delta->target_text.c_str() : "--",
            previous_delta ? previous_delta->delta_text.c_str() : "--");
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 47,
            finish, 0xFFFFFFFFu, 1);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 62,
            pb, 0xFFFFFFFFu, 1);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 77,
            previous, 0xFFFFFFFFu, 1);

        if (summary) {
            int split_y = y + 97;
            int shown = 0;
            for (const auto& split : summary->splits) {
                if (split.id == "finish" || shown >= 4) continue;
                std::string label = split.id;
                if (label.rfind("checkpoint-", 0) == 0) {
                    label = "CP " + label.substr(11);
                }
                char split_line[96];
                std::snprintf(
                    split_line, sizeof(split_line), "%s  %s  %s",
                    label.c_str(),
                    split.current_text.c_str(),
                    split.delta_text.c_str());
                snes_ovl_draw_text(
                    pixels, stride, height, x + 8, split_y,
                    split_line, 0xFFFFFFFFu, 1);
                split_y += 15;
                ++shown;
            }
        }

        if (records_selected_matches_current_course()) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + panel_h - 41,
                "CTRL+B / X  LOCAL RUNS", 0xFFFFFFFFu, 1);
        }
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + panel_h - 26,
            "ESC / B    RUNS", 0xFFFFFFFFu, 1);
    }

    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + panel_h - 11,
        "F8 / Y      CLOSE", 0xFFFFFFFFu, 1);
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
    const int panel_h = 39 + row_count * 15 + 76;
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
            const std::string date =
                entry.date_text.size() == 10
                    ? entry.date_text.substr(5)
                    : entry.date_text;
            std::snprintf(
                line, sizeof(line), "%c #%03zu %s %s %s%s",
                g_browser.selected_index() &&
                        *g_browser.selected_index() == index
                    ? '>' : ' ',
                entry.chronological_order,
                course.c_str(),
                date.c_str(),
                entry.time_text.c_str(),
                tags.c_str());
        } else {
            const std::string course =
                entry.course_id.rfind("course:", 0) == 0
                    ? "C" + entry.course_id.substr(7)
                    : entry.course_id;
            const std::string date =
                entry.date_text.size() == 10
                    ? entry.date_text.substr(5)
                    : entry.date_text;
            std::snprintf(
                line, sizeof(line), "  #%03zu %s %s %s",
                entry.chronological_order,
                date.c_str(),
                course.c_str(),
                ur::product::completed_run_browser_status_name(
                    entry.status));
        }
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 42 + row * 15,
            line, 0xFFFFFFFFu, 1);
    }

    char comparison[64];
    const auto* selected = g_browser.selected();
    std::snprintf(
        comparison, sizeof(comparison), "VS PB     %s",
        selected ? selected->personal_best_delta_text.c_str() : "--");
    snes_ovl_draw_text(
        pixels, stride, height, x + 8, y + panel_h - 71,
        comparison, 0xFFFFFFFFu, 1);

    if (selected && !selected->personal_best_splits.empty()) {
        int split_row_y = y + panel_h - 56;
        int shown = 0;
        for (auto it = selected->personal_best_splits.rbegin();
             it != selected->personal_best_splits.rend() && shown < 2;
             ++it) {
            if (it->id == "finish") continue;
            std::string label = it->id;
            if (label.rfind("checkpoint-", 0) == 0) {
                label = "CP " + label.substr(11);
            }
            char split_line[72];
            std::snprintf(
                split_line, sizeof(split_line),
                "%s  %s  %s",
                label.c_str(),
                it->current_text.c_str(),
                it->delta_text.c_str());
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, split_row_y,
                split_line, 0xFFFFFFFFu, 1);
            split_row_y += 15;
            ++shown;
        }
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
    if (!modern_mode() || g_browser_visible || g_records_browser_visible ||
        g_replay_flow.active() ||
        !g_one_player_context || !snesrecomp_desktop_is_paused() ||
        !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }
    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    snes_ovl_draw_text(
        pixels, stride, height, 8, height - 28,
        "F8 / Y      RECORDS", 0xFFFFFFFFu, 1);
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
        maybe_run_records_browser_acceptance();
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

    if (g_records_browser_visible) {
        if (repeat) return 1;
        if (key == SDLK_UP) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (key == SDLK_DOWN) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (key == SDLK_RETURN || key == SDLK_KP_ENTER) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        if (key == SDLK_ESCAPE) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        }
        if (key == SDLK_b && (mod & KMOD_CTRL) &&
            g_records_browser.view() !=
                ur::product::CompletedRunRecordsView::Courses &&
            records_selected_matches_current_course()) {
            g_records_browser_visible = false;
            (void)open_browser();
            return 1;
        }
        if (key == SDLK_F8) {
            close_records_browser();
            return 1;
        }
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

    if (key == SDLK_F8) {
        if (snesrecomp_desktop_is_paused()) {
            (void)open_records_browser();
            return 1;
        }
        if (records_results_surface()) {
            (void)open_records_from_results();
            return 1;
        }
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

    if (g_records_browser_visible) {
        if (!pressed) return 1;
        if (button == kGamepadBtn_DpadUp) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_UP) ? 1 : 0;
        }
        if (button == kGamepadBtn_DpadDown) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_DOWN) ? 1 : 0;
        }
        if (button == kGamepadBtn_A) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_CONFIRM) ? 1 : 0;
        }
        if (button == kGamepadBtn_B) {
            return records_browser_navigation(UR_MODERN_HOST_NAV_BACK) ? 1 : 0;
        }
        if (button == kGamepadBtn_X &&
            g_records_browser.view() !=
                ur::product::CompletedRunRecordsView::Courses &&
            records_selected_matches_current_course()) {
            g_records_browser_visible = false;
            (void)open_browser();
            return 1;
        }
        if (button == kGamepadBtn_Y) {
            close_records_browser();
            return 1;
        }
        return 1;
    }

    // Modern Controls owns raw controller events only long enough to let
    // SNESRecomp resolve the configured GamepadMap and call the semantic
    // control hook. Do this before the paused X/Y Records/Run Data shortcuts.
    if (ur_uniracers_modern_controls_active()) {
        return ur_uniracers_modern_system_gamepad_button(button, pressed);
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

    if (pressed && button == kGamepadBtn_Y) {
        if (snesrecomp_desktop_is_paused()) {
            (void)open_records_browser();
            return 1;
        }
        if (records_results_surface()) {
            (void)open_records_from_results();
            return 1;
        }
    }

    if (pressed && button == kGamepadBtn_X &&
        snesrecomp_desktop_is_paused()) {
        (void)open_browser();
        return 1;
    }

    return ur_uniracers_modern_system_gamepad_button(button, pressed);
}

extern "C" int ur_uniracers_product_system_gamepad_control(
    int control,
    int pressed) {
    // Run/Records surfaces retain their existing raw-button ownership above
    // the framework mapping. When they are not active, forward mapped SNES
    // controls to the Modern host so Controls can honor GamepadMap rebinding.
    if (g_replay_flow.active() ||
        g_records_browser_visible ||
        g_browser_visible) {
        return 1;
    }
    return ur_uniracers_modern_system_gamepad_control(control, pressed);
}

extern "C" void ur_uniracers_product_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!g_replay_flow.active()) {
        ur_uniracers_modern_system_overlay(dst, pitch, width, height);
    }
    draw_records_browser(dst, pitch, width, height);
    draw_browser(dst, pitch, width, height);
    draw_browser_hint(dst, pitch, width, height);
}
