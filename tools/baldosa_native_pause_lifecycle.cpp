/* Baldosa native execution lifecycle witness over the existing observer.
 *
 * In ordinary play this adds only the observer forward and a cheap inert
 * SDL event-loop tick. A bounded, explicit environment test exercises the
 * REAL host pause/guest freeze/audio pause path without a synthetic guest
 * step or made-up event completion.
 */
#include <cstddef>
#include <cstdint>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>

#include "modern_session_c_api.h"
#include "baldosa_physical_pause_input.hpp"
#include "modern_pause_input.h"
#include "modern_pause_overlay_presenter.hpp"
#include "baldosa_guest_result_observer.hpp"
#include "host_profile_catalog.hpp"
#include "baldosa_native_run_publish_retry.hpp"
#include "baldosa_native_match_publish_retry.hpp"
#include "baldosa_host_lifecycle_pause.hpp"
#include "baldosa_native_options.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
}

extern "C" {
#include "host_main.h"
#include "common_rtl.h"
extern std::uint8_t g_ram[0x20000];
void ur_baldosa_product_guest_restarted(void);
int ur_baldosa_product_set_paused(int paused);
// Native Options reachable from the paused menu (owned by the Modern root).
int ur_baldosa_modern_root_pause_options_open(void);
int ur_baldosa_modern_root_pause_options_active(void);
void ur_baldosa_modern_root_pause_options_close(void);
int ur_baldosa_modern_root_pause_options_input(int action);
int ur_baldosa_modern_root_pause_options_draw(
    std::uint8_t* pixels, std::size_t pitch, int width, int height);
int snesrecomp_desktop_product_get_volume(void);
int snesrecomp_desktop_product_get_display(int* fullscreen, int* vsync);
// Staged by baldosa_sdl_controller_lifecycle_spike.py: read-only seat view.
long long snesrecomp_desktop_product_seat_source(int seat);
int snesrecomp_desktop_product_input_scripted(void);
int ur_baldosa_product_system_gamepad(int player, int button, int pressed);
int snesrecomp_desktop_product_is_paused(void);
unsigned snesrecomp_desktop_product_pause_presentations(void);
int ur_baldosa_modern_root_key(int key, int pressed);
int ur_baldosa_modern_root_gamepad(int player, int button, int pressed);
void ur_baldosa_modern_root_after_run_frame(unsigned frame);
unsigned ur_baldosa_modern_root_guest_players(void);
int ur_baldosa_modern_root_source_bound_2p_profiles(
    ur::product::HostProfileCatalogEntry* p1,
    ur::product::HostProfileCatalogEntry* p2);
int ur_baldosa_modern_publish_settled_two_player_match(
    const ur::product::BaldosaSettledResult* result,
    const ur::product::HostProfileCatalogEntry* p1,
    const ur::product::HostProfileCatalogEntry* p2);

void ur_baldosa_modern_root_set_run_save_feedback(unsigned);
const char* ur_baldosa_modern_profile_records_directory(void);
int ur_baldosa_modern_publish_settled_one_player_run(
    const ur::product::BaldosaSettledResult* result);
void ur_baldosa_guest_snapshot_after_run_frame(
    const SnesDesktopHostFrameStats* stats);
}

namespace {
bool g_smoke_initialized;
ur::product::BaldosaGuestResultObserver g_native_result_observer;
ur::product::BaldosaPendingOnePlayerRun g_pending_one_player_run;
ur::product::BaldosaPendingTwoPlayerMatch g_pending_two_player_match;
bool g_smoke_enabled;
UrModernSession* g_modern_session;
bool g_native_live_race;
UrModernPauseMenu g_native_pause_menu{};
bool g_pause_navigation_keys[3]{};
bool g_pause_navigation_pad[4]{};
// Independent physical latches for the paused Options panel: up, down,
// confirm, back (Esc / pad B), left, right; the pad adds Start (back).
bool g_pause_options_keys[6]{};
bool g_pause_options_pad[7]{};
int g_pause_options_smoke;  // 0 off, 1 SDL keyboard edges, 2 semantic P1 pad
bool g_pause_options_smoke_verified;
bool g_pause_panel_logged;
unsigned g_pause_panel_paints;
bool g_pause_panel_nav_smoke;
bool g_pause_quit_smoke;
bool g_native_quit_queued;
bool g_pause_quit_key_queued;
std::string g_pause_quit_conflict_gate;
bool g_pause_panel_nav_verified;
ur::product::BaldosaPhysicalPauseInput g_keyboard_pause;
ur::product::BaldosaPhysicalPauseInput g_p1_gamepad_pause;
ur::product::BaldosaPhysicalPauseInput g_keyboard_restart;
bool g_restart_same_frame_checked;
bool g_delayed_restart_enabled;
bool g_native_anchor_captured;
bool g_delayed_restart_verified;
unsigned g_native_anchor_frame;
std::uint8_t g_native_anchor_ram[0x20000];
std::vector<std::uint8_t> g_paused_persistent_bytes;

// Deliberately opt-in while the native Baldosa executable lacks the visible
// established Modern pause/root surfaces. Authentic remains untouched.
bool physical_modern_enabled() {
    static const bool enabled = [] {
        const char* opt = std::getenv("UR_BALDOSA_MODERN_INPUT");
        const char* mode = std::getenv("UR_EXECUTION_MODE");
        return opt && std::strcmp(opt, "1") == 0 &&
               !(mode && std::strcmp(mode, "authentic") == 0);
    }();
    return enabled;
}

bool acknowledged_guest_pause(void*, int paused) {
    return ur_baldosa_product_set_paused(paused) != 0;
}

std::size_t save_native_guest(void* bytes, std::size_t capacity) {
    return RtlRollbackSaveToMemory(bytes, capacity);
}

bool restore_native_guest_preserving_sram(const void* bytes, std::size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &RtlRollbackLoadFromMemory, bytes, size, g_sram,
        g_sram_size > 0 ? static_cast<std::size_t>(g_sram_size) : 0u);
}

void reconcile_after_native_restart() {
    // A source-authenticated Restart begins a NEW attempt. Previous course,
    // official line-write, result and mapped input timeline are revoked.
    // Pause/resume without Restart does not reset this observer.
    g_native_result_observer.reset();
    g_pending_one_player_run.reset();
    g_pending_two_player_match.reset();
    ur_baldosa_modern_root_set_run_save_feedback(0);
    // This is the existing Modern host's post-restore audio reconciliation
    // and the already merged two-seat human input release latch. A paused
    // Restart never gives a held physical Start back to the guest.
    ur_baldosa_product_guest_restarted();
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

// One physical, edge-triggered menu navigation gesture. The guest owns
// every key outside an acknowledged native pause, including its key-up.
bool pause_navigation_edge(int pressed, bool& holding,
                           UrModernPauseAction action,
                           bool* options_hold = nullptr) {
    if (!pressed) {
        if (!holding) return false;
        holding = false;
        return true;
    }
    if (!g_modern_session ||
        !ur_modern_session_is_paused(g_modern_session))
        return false;
    if (holding) return true;
    holding = true;
    if (action == UR_MODERN_PAUSE_ACTIVATE &&
        ur_modern_pause_menu_selected(
            &g_native_pause_menu,
            ur_modern_session_restart_available(g_modern_session)) ==
            UR_MODERN_PAUSE_OPTIONS) {
        // The shared native Options panel, guest frozen. The confirming
        // press stays owned until its release so a held or repeating
        // Enter/A can never change the first row it lands on.
        if (ur_baldosa_modern_root_pause_options_open() && options_hold)
            *options_hold = true;
        return true;
    }
    if (action == UR_MODERN_PAUSE_ACTIVATE &&
        ur_modern_pause_menu_selected(
            &g_native_pause_menu,
            ur_modern_session_restart_available(g_modern_session)) ==
            UR_MODERN_PAUSE_QUIT) {
        // Delegate to Baldosa's already-owned SDL shutdown/event loop. The
        // guest remains frozen until the host processes SDL_QUIT and runs its
        // normal SRAM/profile checkpoint path. No synthetic event result.
        if (g_native_quit_queued) return true;
        SDL_Event quit{};
        quit.type = SDL_QUIT;
        if (SDL_PushEvent(&quit) != 1) {
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_REJECTED=event_queue\n");
            return true;  // keep host focus and the acknowledged pause
        }
        g_native_quit_queued = true;
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0\n");
        std::fflush(stderr);
        return true;
    }
    const auto result = ur_modern_pause_handle_action(
        g_modern_session, &g_native_pause_menu, action);
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_PAUSE_MENU action=%d selected=%d result=%d paused=%d\n",
        static_cast<int>(action),
        g_native_pause_menu.selected, static_cast<int>(result),
        ur_modern_session_is_paused(g_modern_session));
    return true;
}

// One physical edge routed to the paused Options panel. Presses are taken
// only while the panel is open on an acknowledged pause; a release is
// reported only for a press this panel owned. Action codes follow
// ur_baldosa_modern_root_pause_options_input.
bool pause_options_edge(int pressed, bool& holding, int action) {
    if (!pressed) {
        if (!holding) return false;
        holding = false;
        return true;
    }
    if (!ur_baldosa_modern_root_pause_options_active()) return false;
    if (!g_modern_session || !ur_modern_session_is_paused(g_modern_session)) {
        ur_baldosa_modern_root_pause_options_close();
        return false;
    }
    if (holding) return true;
    holding = true;
    return ur_baldosa_modern_root_pause_options_input(action) != 0;
}

void reset_native_pause_menu_on_open() {
    ur_baldosa_modern_root_pause_options_close();
    if (g_modern_session && ur_modern_session_is_paused(g_modern_session)) {
        ur_modern_pause_menu_reset(&g_native_pause_menu);
        g_pause_panel_logged = false;
    }
}

void create_modern_session() {
    if (g_modern_session) return;
    const UrModernNativeSessionHooks hooks{
        nullptr, &acknowledged_guest_pause, nullptr, nullptr, nullptr};
    const auto capacity = RtlRollbackSnapshotBound();
    g_modern_session = capacity
        ? ur_modern_session_create_native_with_snapshot(
              1, &hooks, capacity, &save_native_guest,
              &restore_native_guest_preserving_sram,
              &reconcile_after_native_restart)
        : ur_modern_session_create_native(1, &hooks);
    if (!g_modern_session) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=modern_session_create\n");
        std::abort();
    }
}
bool g_armed;
bool g_resumed;
unsigned g_guest_frame;
unsigned g_frozen_ticks;
unsigned g_pause_at_frame = 120;
bool g_require_race;
bool g_physical_smoke;
std::uint8_t g_frozen_ram[0x20000];

// Use the real Baldosa SDL event pump in this explicit bounded acceptance.
// Queued synthetic keys exercise host dispatch, NOT physical hardware QA.
void queue_key_edge(int key) {
    SDL_Event event{};
    event.type = SDL_KEYDOWN;
#if SNESRECOMP_SDL3
    event.key.key = key;
#else
    event.key.keysym.sym = key;
#endif
    if (SDL_PushEvent(&event) != 1) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=keydown_not_queued\n");
        std::abort();
    }
    event.type = SDL_KEYUP;
    if (SDL_PushEvent(&event) != 1) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=keyup_not_queued\n");
        std::abort();
    }
}

void queue_escape_edge() { queue_key_edge(SDLK_ESCAPE); }
// Smoke mode 1 queues real SDL key edges; mode 2 drives the production P1
// gamepad entry point (semantic edges, not a physical controller).
void options_smoke_edge(int key, int pad_button) {
    if (g_pause_options_smoke == 2) {
        if (!ur_baldosa_product_system_gamepad(0, pad_button, 1) ||
            !ur_baldosa_product_system_gamepad(0, pad_button, 0)) {
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_PAUSE FAIL=options_pad_edge_not_consumed\n");
            std::abort();
        }
    } else {
        queue_key_edge(key);
    }
}
void queue_restart_edge() { queue_key_edge(SDLK_r); }

// Focus-loss and seat-owner-disconnect pauses for a live Modern race. The
// decision is baldosa_host_lifecycle_pause.hpp (reusing the legacy host's
// focus and hotplug policies); this only feeds it and uses the ordinary
// session pause, exactly like a player's own pause.
ur::product::BaldosaHostLifecyclePause g_lifecycle_pause;
unsigned g_lifecycle_pauses_applied;
ur::product::BaldosaLifecyclePauseReason g_lifecycle_last_reason;

bool load_focus_pause_setting() {
    const char* user_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!user_root || !*user_root) return ur::product::HostSettings{}.pause_on_focus_loss;
    const auto loaded = ur::product::load_host_product_state_file(
        ur::product::baldosa_options_path(user_root).string());
    return loaded.loaded()
        ? loaded.state->settings.pause_on_focus_loss
        : ur::product::HostSettings{}.pause_on_focus_loss;
}

int lifecycle_smoke_mode();

void apply_host_lifecycle_pause() {
    ur::product::BaldosaLifecycleObservation in;
    for (int seat = 0; seat < static_cast<int>(ur::product::kControllerSeatCount); ++seat)
        in.seat_sources[static_cast<std::size_t>(seat)] =
            snesrecomp_desktop_product_seat_source(seat);
    in.focused = SDL_GetKeyboardFocus() != nullptr;
    in.mode = physical_modern_enabled() ? ur::product::ExecutionMode::Modern
                                        : ur::product::ExecutionMode::Authentic;
    in.pause_surface = g_modern_session && g_native_live_race;
    in.already_paused = g_modern_session && ur_modern_session_is_paused(g_modern_session);
    // The focus smoke stands in for the player a script otherwise lacks.
    in.focus_pause_eligible =
        !snesrecomp_desktop_product_input_scripted() || lifecycle_smoke_mode() == 2;
    const auto reason = g_lifecycle_pause.step(in, &load_focus_pause_setting);
    if (reason == ur::product::BaldosaLifecyclePauseReason::None) return;
    g_lifecycle_last_reason = reason;
    const auto result = ur_modern_session_pause(g_modern_session);
    if (result == UR_MODERN_SESSION_APPLIED) {
        ++g_lifecycle_pauses_applied;
        reset_native_pause_menu_on_open();
    }
    const char* notice =
        ur::product::controller_hotplug_notice_text(g_lifecycle_pause.hotplug());
    std::fprintf(stderr,
        "UR_BALDOSA_LIFECYCLE_PAUSE reason=%s seat=%d applied=%d notice=%s\n",
        ur::product::baldosa_lifecycle_pause_reason_name(reason),
        g_lifecycle_pause.disconnected_seat() + 1,
        result == UR_MODERN_SESSION_APPLIED ? 1 : 0, notice ? notice : "-");
    std::fflush(stderr);
}

// Alt+Enter / launcher display changes reach only config.ini, but Modern
// boot restores the typed store over it. When the live display changes,
// record it into the EXISTING store (the same one boot restores from, and
// under the same Modern-root gate) so the next launch keeps it. Options'
// own changes already match the store and are a no-op here.
int g_adopt_live_display = -1;
void adopt_live_display_change() {
    int fullscreen = 0;
    int vsync = 1;
    if (!snesrecomp_desktop_product_get_display(&fullscreen, &vsync)) return;
    const int live = fullscreen * 3 + vsync;
    if (g_adopt_live_display < 0 || live == g_adopt_live_display) {
        g_adopt_live_display = live;  // first frame: boot already restored
        return;
    }
    g_adopt_live_display = live;
    const char* root = std::getenv("UR_BALDOSA_MODERN_ROOT");
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    const char* user_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!root || std::strcmp(root, "1") != 0 ||
        (mode && std::strcmp(mode, "authentic") == 0) || !user_root || !*user_root)
        return;
    const auto result = ur::product::baldosa_options_adopt_live_display(
        ur::product::baldosa_options_path(user_root).string(), fullscreen, vsync);
    std::fprintf(stderr, "UR_BALDOSA_OPTIONS adopt_live_display fullscreen=%d vsync=%d result=%d\n",
                 fullscreen, vsync, static_cast<int>(result));
    std::fflush(stderr);
}

// UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE=disconnect|focus (SDL3, test-only, inert
// otherwise). "disconnect" hot-plugs an SDL virtual gamepad during a live
// race and unplugs it once the host has seated it; "focus" minimizes the
// real window. Either must pause through the ordinary session within the
// next completed frame, keep guest WRAM frozen while paused, then resume and
// advance. Virtual devices and a scripted minimize are not hardware QA.
int g_lps_mode = -1;  // 0 off, 1 disconnect, 2 focus
int g_lps_stage;      // 0 wait, 1 armed, 2 triggered, 3 paused, 4 resumed, 5 done
unsigned g_lps_race_frames, g_lps_trigger_frame, g_lps_ticks, g_lps_after_resume;
unsigned g_lps_pauses_before;
std::uint8_t g_lps_frozen[0x20000];
#if SNESRECOMP_SDL3
SDL_JoystickID g_lps_pad_id;
SDL_Joystick* g_lps_pad;
SDL_Window* g_lps_window;
#endif

int lifecycle_smoke_mode() {
    if (g_lps_mode < 0) {
        const char* v = std::getenv("UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE");
        g_lps_mode = !v ? 0 : std::strcmp(v, "disconnect") == 0 ? 1
                   : std::strcmp(v, "focus") == 0 ? 2 : 0;
    }
    return g_lps_mode;
}

void lifecycle_smoke_finish(const char* result, const char* detail) {
    std::fprintf(stderr,
        "UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE mode=%s result=%s detail=%s "
        "race_frames=%u paused_ticks=%u frames_after_resume=%u\n",
        g_lps_mode == 1 ? "disconnect" : "focus", result, detail,
        g_lps_race_frames, g_lps_ticks, g_lps_after_resume);
    std::fflush(stderr);
    g_lps_stage = 5;
#if SNESRECOMP_SDL3
    if (g_lps_pad) SDL_CloseJoystick(g_lps_pad);
    if (g_lps_pad_id) SDL_DetachVirtualJoystick(g_lps_pad_id);
    g_lps_pad = nullptr;
    g_lps_pad_id = 0;
#endif
    SDL_Event quit{};
    quit.type = SDL_QUIT;
    (void)SDL_PushEvent(&quit);
}

// After every completed guest frame, after apply_host_lifecycle_pause().
void lifecycle_pause_smoke_frame() {
#if SNESRECOMP_SDL3
    if (!lifecycle_smoke_mode() || g_lps_stage == 5) return;
    if (g_lps_stage == 4) {
        if (++g_lps_after_resume >= 10)
            lifecycle_smoke_finish("pass", "paused_frozen_resumed");
        return;
    }
    if (!g_native_live_race || !g_modern_session) return;
    ++g_lps_race_frames;
    if (g_lps_stage == 0 && g_lps_race_frames == 5) {
        if (g_lps_mode == 1) {
            SDL_VirtualJoystickDesc desc;
            SDL_INIT_INTERFACE(&desc);
            desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
            desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
            desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
            desc.name = "UR lifecycle pause pad";
            g_lps_pad_id = SDL_AttachVirtualJoystick(&desc);
            g_lps_pad = g_lps_pad_id ? SDL_OpenJoystick(g_lps_pad_id) : nullptr;
            if (!g_lps_pad) return lifecycle_smoke_finish("fail", "virtual_pad_unavailable");
        } else {
            g_lps_window = SDL_GetKeyboardFocus();
            if (!g_lps_window) {
                int count = 0;
                SDL_Window** windows = SDL_GetWindows(&count);
                if (windows && count > 0) {
                    g_lps_window = windows[0];
                    SDL_RaiseWindow(g_lps_window);
                }
                SDL_free(windows);
            }
            if (!g_lps_window) return lifecycle_smoke_finish("fail", "no_window");
        }
        g_lps_stage = 1;
        return;
    }
    if (g_lps_stage == 1 && g_lps_race_frames == 30) {
        g_lps_pauses_before = g_lifecycle_pauses_applied;
        g_lps_trigger_frame = g_lps_race_frames;
        if (g_lps_mode == 1) {
            const long long id = static_cast<long long>(g_lps_pad_id);
            if (snesrecomp_desktop_product_seat_source(0) != id &&
                snesrecomp_desktop_product_seat_source(1) != id)
                return lifecycle_smoke_finish("fail", "pad_not_seated");
            SDL_CloseJoystick(g_lps_pad);
            g_lps_pad = nullptr;
            SDL_DetachVirtualJoystick(g_lps_pad_id);
            g_lps_pad_id = 0;
        } else {
            if (SDL_GetKeyboardFocus() != g_lps_window)
                return lifecycle_smoke_finish("not_exercised", "window_never_focused");
            SDL_MinimizeWindow(g_lps_window);
        }
        g_lps_stage = 2;
        return;
    }
    if (g_lps_stage == 2) {
        const auto want = g_lps_mode == 1
            ? ur::product::BaldosaLifecyclePauseReason::ControllerDisconnect
            : ur::product::BaldosaLifecyclePauseReason::FocusLoss;
        if (g_lifecycle_pauses_applied > g_lps_pauses_before) {
            if (g_lifecycle_last_reason != want ||
                !ur_modern_session_is_paused(g_modern_session))
                return lifecycle_smoke_finish("fail", "wrong_pause");
            std::memcpy(g_lps_frozen, g_ram, sizeof(g_lps_frozen));
            g_lps_stage = 3;
        } else if (g_lps_race_frames > g_lps_trigger_frame + 60) {
            lifecycle_smoke_finish("fail", "no_pause_within_60_frames");
        }
    }
#endif
}

// Every host loop iteration, including while paused.
void lifecycle_pause_smoke_tick() {
#if SNESRECOMP_SDL3
    if (!lifecycle_smoke_mode() || g_lps_stage != 3) return;
    if (std::memcmp(g_ram, g_lps_frozen, sizeof(g_lps_frozen)) != 0)
        return lifecycle_smoke_finish("fail", "guest_advanced_while_paused");
    ++g_lps_ticks;
    if (g_lps_mode == 2 && g_lps_ticks == 20) {
        SDL_RestoreWindow(g_lps_window);
        SDL_RaiseWindow(g_lps_window);
    }
    if (g_lps_ticks == 40) {
        if (ur_modern_session_resume(g_modern_session) != UR_MODERN_SESSION_APPLIED)
            return lifecycle_smoke_finish("fail", "resume_refused");
        g_lps_stage = 4;
    }
#endif
}

bool smoke_enabled() {
    if (!g_smoke_initialized) {
        const char* env = std::getenv("UR_BALDOSA_PAUSE_SMOKE");
        g_smoke_enabled = env && std::strcmp(env, "1") == 0;
        if (g_smoke_enabled) {
            const char* frame = std::getenv("UR_BALDOSA_PAUSE_SMOKE_AT_FRAME");
            if (frame && frame[0]) {
                errno = 0;
                char* end = nullptr;
                const unsigned long n = std::strtoul(frame, &end, 10);
                if (errno != 0 || !end || end == frame || *end != '\0' ||
                    n == 0 || n > UINT_MAX) {
                    std::fprintf(stderr,
                        "UR_BALDOSA_NATIVE_PAUSE FAIL=invalid_test_frame\n");
                    std::abort();
                }
                g_pause_at_frame = static_cast<unsigned>(n);
            }
            const char* require = std::getenv("UR_BALDOSA_PAUSE_REQUIRE_RACE");
            g_require_race = require && std::strcmp(require, "1") == 0;
            const char* physical = std::getenv("UR_BALDOSA_PHYSICAL_PAUSE_SMOKE");
            g_physical_smoke = physical && std::strcmp(physical, "1") == 0;
            const char* nav = std::getenv("UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE");
            g_pause_panel_nav_smoke = nav && std::strcmp(nav, "1") == 0;
            const char* options_env =
                std::getenv("UR_BALDOSA_PAUSE_OPTIONS_SMOKE");
            g_pause_options_smoke =
                options_env && std::strcmp(options_env, "1") == 0 ? 1 :
                options_env && std::strcmp(options_env, "2") == 0 ? 2 : 0;
            if (g_pause_options_smoke &&
                (!g_physical_smoke || g_pause_panel_nav_smoke)) {
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_PAUSE FAIL=options_smoke_requires_exclusive_physical_route\n");
                std::abort();
            }
            const char* quit = std::getenv("UR_BALDOSA_PAUSE_QUIT_SMOKE");
            g_pause_quit_smoke = quit && std::strcmp(quit, "1") == 0;
            const char* gate = std::getenv(
                "UR_BALDOSA_PAUSE_QUIT_CONFLICT_GATE");
            g_pause_quit_conflict_gate = gate && *gate ? gate : "";
            if (!g_pause_quit_conflict_gate.empty() && !g_pause_quit_smoke) {
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_PAUSE FAIL=quit_gate_without_quit_smoke\n");
                std::abort();
            }
            const char* delayed = std::getenv("UR_BALDOSA_DELAYED_RESTART_SMOKE");
            g_delayed_restart_enabled =
                delayed && std::strcmp(delayed, "1") == 0;
            if (g_pause_quit_smoke &&
                (!g_physical_smoke || g_pause_panel_nav_smoke ||
                 g_delayed_restart_enabled)) {
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_PAUSE FAIL=quit_smoke_requires_exclusive_physical_route\n");
                std::abort();
            }
        }
        g_smoke_initialized = true;
    }
    return g_smoke_enabled;
}
void require(bool ok, const char* why) {
    if (!ok) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=%s\n", why);
        std::fflush(stderr);
        std::abort();
    }
}
} // namespace

// Called from the ORIGINAL Baldosa SDL keyboard/gamepad processing after the
// host's physical mapping, not from a script/debug controller word. Only P1
// Escape/Start while actually racing belongs to this narrow Modern pause
// bridge; all ordinary profile/stock/menu controls retain guest authority.
extern "C" int ur_baldosa_product_system_key(int key, int pressed) {
    if (ur_baldosa_modern_root_key(key, pressed)) return 1;
    if (!physical_modern_enabled() ||
        (smoke_enabled() && !g_physical_smoke)) return 0;
    int nav = -1;
    int opt = -1;  // paused-Options action: up down confirm back left right
    switch (key) {
    case SDLK_UP: nav = 0; opt = 0; break;
    case SDLK_DOWN: nav = 1; opt = 1; break;
    case SDLK_RETURN: nav = 2; opt = 2; break;
    case SDLK_ESCAPE: opt = 3; break;
    case SDLK_LEFT: opt = 4; break;
    case SDLK_RIGHT: opt = 5; break;
    default: break;
    }
    // Paused Options owns its presses first; releases always reach both
    // owners so neither latch can stick.
    bool options_release = false;
    if (opt >= 0) {
        const bool owned =
            pause_options_edge(pressed, g_pause_options_keys[opt], opt);
        if (owned && pressed) return 1;
        options_release = owned && !pressed;
    }
    if (nav >= 0 && pause_navigation_edge(
            pressed, g_pause_navigation_keys[nav],
            nav == 0 ? UR_MODERN_PAUSE_PREVIOUS :
            nav == 1 ? UR_MODERN_PAUSE_NEXT :
                       UR_MODERN_PAUSE_ACTIVATE,
            nav == 2 ? &g_pause_options_keys[2] : nullptr))
        return 1;
    if (options_release && key != SDLK_ESCAPE) return 1;
    if (ur_baldosa_modern_root_pause_options_active() &&
        (key == SDLK_r || key == SDLK_LEFT || key == SDLK_RIGHT))
        return 1;  // no Restart while the Options panel is open
    if (key == SDLK_r) {
        // R is a Modern Restart command only inside an acknowledged host
        // pause. Normal stock racing and menu navigation retain the key.
        if (!g_modern_session ||
            (!ur_modern_session_is_paused(g_modern_session) &&
             !g_keyboard_restart.holding())) return 0;
        const bool used = g_keyboard_restart.on_button(
            pressed, false, g_modern_session, UR_MODERN_SESSION_KEY_RESTART);
        if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS"))
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_INPUT key=restart status=%d paused=%d\n",
                static_cast<int>(g_keyboard_restart.last_result()),
                ur_modern_session_is_paused(g_modern_session));
        return used ? 1 : 0;
    }
    if (key != SDLK_ESCAPE) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_keyboard_pause.on_button(
        pressed, g_native_live_race, g_modern_session) || options_release;
    if (used && pressed &&
        g_keyboard_pause.last_result() == UR_MODERN_SESSION_APPLIED)
        reset_native_pause_menu_on_open();
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT key=escape action=%d paused=%d\n",
                     static_cast<int>(g_keyboard_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

extern "C" int ur_baldosa_product_system_gamepad(
    int player, int button, int pressed) {
    if (ur_baldosa_modern_root_gamepad(player, button, pressed)) return 1;
    if (!physical_modern_enabled() ||
        (smoke_enabled() && !g_physical_smoke) || player != 0) return 0;
    int nav = -1;
    int opt = -1;       // paused-Options action codes
    int opt_slot = -1;  // its physical latch
    switch (button) {
    case kGamepadBtn_DpadUp: nav = 0; opt = 0; opt_slot = 0; break;
    case kGamepadBtn_DpadDown: nav = 1; opt = 1; opt_slot = 1; break;
    case kGamepadBtn_A: nav = 2; opt = 2; opt_slot = 2; break;
    case kGamepadBtn_B: nav = 3; opt = 3; opt_slot = 3; break;
    case kGamepadBtn_Start: opt = 3; opt_slot = 4; break;
    case kGamepadBtn_DpadLeft: opt = 4; opt_slot = 5; break;
    case kGamepadBtn_DpadRight: opt = 5; opt_slot = 6; break;
    default: break;
    }
    bool options_release = false;
    if (opt >= 0) {
        const bool owned = pause_options_edge(
            pressed, g_pause_options_pad[opt_slot], opt);
        if (owned && pressed) return 1;
        options_release = owned && !pressed;
    }
    if (nav >= 0 && pause_navigation_edge(
            pressed, g_pause_navigation_pad[nav],
            nav == 0 ? UR_MODERN_PAUSE_PREVIOUS :
            nav == 1 ? UR_MODERN_PAUSE_NEXT :
            nav == 2 ? UR_MODERN_PAUSE_ACTIVATE :
                       UR_MODERN_PAUSE_CANCEL,
            nav == 2 ? &g_pause_options_pad[2] : nullptr)) return 1;
    if (options_release && button != kGamepadBtn_Start) return 1;
    if (ur_baldosa_modern_root_pause_options_active() &&
        (button == kGamepadBtn_DpadLeft || button == kGamepadBtn_DpadRight))
        return 1;
    if (button != kGamepadBtn_Start) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_p1_gamepad_pause.on_button(
        pressed, g_native_live_race, g_modern_session) || options_release;
    if (used && pressed &&
        g_p1_gamepad_pause.last_result() == UR_MODERN_SESSION_APPLIED)
        reset_native_pause_menu_on_open();
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT pad=p1_start action=%d paused=%d\n",
                     static_cast<int>(g_p1_gamepad_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

// Called solely by Baldosa's ORIGINAL frozen-frame renderer after it copies
// the last raster. This operates on host pixels; no guest draw/step or SRAM.
extern "C" int ur_baldosa_product_pause_draw(
    std::uint8_t* pixels, std::size_t pitch, int width, int height) {
    if (!physical_modern_enabled() || !g_modern_session ||
        !ur_modern_session_is_paused(g_modern_session) ||
        !pixels || width <= 0 || height <= 0 ||
        pitch < static_cast<std::size_t>(width) * 4 ||
        pitch % 4 != 0)
        return 0;
    if (ur_baldosa_modern_root_pause_options_active())
        return ur_baldosa_modern_root_pause_options_draw(
            pixels, pitch, width, height);
    const ur::product::ModernRootOverlayPainter paint{
        &snes_ovl_fill_rect, &snes_ovl_stroke_rect, &snes_ovl_draw_text};
    if (!ur::product::render_native_modern_pause_overlay(
            paint, reinterpret_cast<std::uint32_t*>(pixels),
            static_cast<int>(pitch / 4), width, height, g_native_pause_menu,
            ur_modern_session_restart_available(g_modern_session) != 0,
            ur::product::controller_hotplug_notice_text(g_lifecycle_pause.hotplug())))
        return 0;
    ++g_pause_panel_paints;
    if (!g_pause_panel_logged) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE PANEL_RENDERED=1 pixels=%dx%d "
            "renderer=shared guest_steps=0\n", width, height);
        g_pause_panel_logged = true;
    }
    return 1;
}

extern "C" void ur_baldosa_product_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    // Existing verified two-seat guest observer remains intact.
    ur_baldosa_guest_snapshot_after_run_frame(stats);
    if (stats) {
        ur_baldosa_modern_root_after_run_frame(stats->frame);
        // Only the native root's source-confirmed stock handoff can arm
        // outcomes. This observes the already executed guest frame and
        // exact cartridge SRAM: no alternate timer, game-rule write or
        // durability claim. The owning Modern record publisher must still
        // provide provenance/inputs and a committed settlement separately.
        const unsigned rooted_players =
            ur_baldosa_modern_root_guest_players();
        const auto terminal = g_native_result_observer.observe(
            rooted_players, g_ram, sizeof(g_ram), g_sram,
            g_sram_size > 0 ? static_cast<std::size_t>(g_sram_size) : 0u,
            stats->frame, stats->resolved_controller_word);
        // A temporary Records lease/write failure must not silently lose
        // a legitimate native result. Retry only while the very same
        // observed 1P stock result remains visible and player-owned.
        // No pause-only presentation advances the retry clock.
        const bool had_pending = g_pending_one_player_run.pending();
        // Preserve the original P1 finish digits as retry source evidence.
        // The live shared timer is free-running and cannot be compared.
        const auto p1_line = ur_uniracers_read_line_snapshot(
            g_ram, sizeof(g_ram), 0);
        const int p1_laps = ur_uniracers_read_laps_remaining(
            g_ram, sizeof(g_ram), 0);
        const auto* retry = g_pending_one_player_run.ready_for_retry(
            rooted_players, g_ram[0x0313u] == 0x01u,
            g_ram[0x009fu], stats->frame, &p1_line, p1_laps);
        if (had_pending && !g_pending_one_player_run.pending()) {
            ur_baldosa_modern_root_set_run_save_feedback(0);
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RUN SAVE_ABANDONED=1 "
                "reason=left_result_surface\n");
        }
        if (retry) {
            const int saved =
                ur_baldosa_modern_publish_settled_one_player_run(retry);
            const auto outcome = g_pending_one_player_run.after_retry(
                saved == 1, stats->frame);
            ur_baldosa_modern_root_set_run_save_feedback(
                outcome == ur::product::BaldosaRunRetryOutcome::Saved ? 2u :
                outcome == ur::product::BaldosaRunRetryOutcome::Pending ? 1u : 3u);
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RUN SAVE_RETRY status=%s "
                "host_frame=%u\n",
                outcome == ur::product::BaldosaRunRetryOutcome::Saved
                    ? "saved" :
                outcome == ur::product::BaldosaRunRetryOutcome::Pending
                    ? "pending" : "exhausted",
                stats->frame);
        }
        // A transient two-file match receipt failure may be retried only
        // while exactly the SAME original title 0xF9 result is visible.
        // A source result is never reconstructed from the stored payload:
        // the original SRAM/result observer must still acknowledge it, and
        // the root must still expose both independently confirmed profiles.
        if (g_pending_two_player_match.pending()) {
            ur::product::HostProfileCatalogEntry current_p1{}, current_p2{};
            const bool profiles_still_bound =
                ur_baldosa_modern_root_source_bound_2p_profiles(
                    &current_p1, &current_p2) != 0;
            const auto current_result =
                profiles_still_bound && rooted_players == 2u &&
                g_ram[0x0313u] != 0x01u &&
                g_ram[0x009fu] ==
                    ur::title::kOrdinaryTwoPlayerRaceResultMenu
                    ? ur::title::observe_ordinary_two_player_race_result(
                        true, g_ram, sizeof(g_ram), g_sram,
                        g_sram_size > 0
                            ? static_cast<std::size_t>(g_sram_size) : 0u)
                    : std::nullopt;
            const auto* retry = g_pending_two_player_match.ready_for_retry(
                rooted_players, g_ram[0x0313u] == 0x01u,
                g_ram[0x009fu], stats->frame,
                current_result ? &*current_result : nullptr,
                profiles_still_bound ? &current_p1 : nullptr,
                profiles_still_bound ? &current_p2 : nullptr);
            if (!g_pending_two_player_match.pending()) {
                ur_baldosa_modern_root_set_run_save_feedback(0);
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_MATCH SAVE_ABANDONED=1 "
                    "reason=changed_source_or_profiles\n");
            } else if (retry) {
                const int saved =
                    ur_baldosa_modern_publish_settled_two_player_match(
                        &retry->result, &retry->player1, &retry->player2);
                const auto outcome = g_pending_two_player_match.after_retry(
                    saved == 1, stats->frame);
                ur_baldosa_modern_root_set_run_save_feedback(
                    outcome == ur::product::BaldosaRunRetryOutcome::Saved ? 2u :
                    outcome == ur::product::BaldosaRunRetryOutcome::Pending ? 1u : 3u);
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_MATCH SAVE_RETRY status=%s "
                    "host_frame=%llu\n",
                    outcome == ur::product::BaldosaRunRetryOutcome::Saved
                        ? "saved" :
                    outcome == ur::product::BaldosaRunRetryOutcome::Pending
                        ? "pending" : "exhausted",
                    static_cast<unsigned long long>(stats->frame));
            }
        }
        if (terminal) {
            if (terminal->kind ==
                ur::product::BaldosaSettledResultKind::TimedOnePlayerRace) {
                const int published =
                    ur_baldosa_modern_publish_settled_one_player_run(
                        &*terminal);
                if (published == 1) {
                    // Only a completed canonical append means Records saved.
                    ur_baldosa_modern_root_set_run_save_feedback(2);
                } else if (ur_baldosa_modern_profile_records_directory() &&
                           g_pending_one_player_run.defer_failed_publication(
                               *terminal, stats->frame, p1_line, p1_laps)) {
                    ur_baldosa_modern_root_set_run_save_feedback(1);
                    std::fprintf(stderr,
                        "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1 "
                        "retry_while_result_visible=1\n");
                } else {
                    // Anonymous/invalid selections cannot publish to an
                    // authorized named Records archive. No false 'pending'
                    // promise, and no write into a default shared save.
                    ur_baldosa_modern_root_set_run_save_feedback(3);
                    std::fprintf(stderr,
                        "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1 "
                        "reason=no_retry_authority\n");
                }
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
                    "race_host=%llu result_host=%llu finish_ticks60=%llu "
                    "input_frames=%llu input_runs=%zu published=%d\n",
                    static_cast<unsigned long long>(
                        terminal->first_race_host_frame),
                    static_cast<unsigned long long>(
                        terminal->observed_result_host_frame),
                    static_cast<unsigned long long>(
                        terminal->p1_finish_ticks60),
                    static_cast<unsigned long long>(
                        terminal->captured_input_frames),
                    terminal->mapped_inputs.size(), published);
            } else if (terminal->two_player) {
                const auto& result = *terminal->two_player;
                ur::product::HostProfileCatalogEntry p1{}, p2{};
                int published = 0;
                if (ur_baldosa_modern_root_source_bound_2p_profiles(
                        &p1, &p2)) {
                    // The established native writer rechecks the selector,
                    // both profile states, roster, original rider result and
                    // real guest input trace under its canonical OS leases.
                    published = ur_baldosa_modern_publish_settled_two_player_match(
                        &*terminal, &p1, &p2);
                    if (published != 1 &&
                        g_pending_two_player_match.defer_failed_publication(
                            *terminal, p1, p2, stats->frame)) {
                        std::fprintf(stderr,
                            "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1 "
                            "retry_while_original_result_visible=1\n");
                    }
                }
                // A badge is truthful only after the exact atomic
                // .urrun + .urmatch publisher reports committed success.
                // An unbound or exhausted result shows NOT SAVED, not PB.
                ur_baldosa_modern_root_set_run_save_feedback(
                    published == 1 ? 2u :
                    g_pending_two_player_match.pending() ? 1u : 3u);
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
                    "race_host=%llu result_host=%llu riders=%u,%u "
                    "hundredths=%u,%u winner=%u input_frames=%llu input_runs=%zu published=%d\n",
                    static_cast<unsigned long long>(
                        terminal->first_race_host_frame),
                    static_cast<unsigned long long>(
                        terminal->observed_result_host_frame),
                    static_cast<unsigned>(result.player1_rider),
                    static_cast<unsigned>(result.player2_rider),
                    static_cast<unsigned>(result.player1_hundredths),
                    static_cast<unsigned>(result.player2_hundredths),
                    static_cast<unsigned>(result.outcome),
                    static_cast<unsigned long long>(
                        terminal->captured_input_frames),
                    terminal->mapped_inputs.size(), published);
            }
            std::fflush(stderr);
        }
    }
    // A rollback can rewind the guest's own snes_frame_counter, which the
    // stock framedump uses as its filename. A deterministic replay can
    // overwrite earlier frame_NNN.json files with their identical CRCs.
    // Record a separate APPEND-ONLY host-frame witness, measured after each
    // genuine RtlRunFrame, to distinguish a real rewind from frame filenames.
    const char* host_trace = std::getenv("UR_BALDOSA_RESTART_FRAME_TRACE");
    if (stats && host_trace && std::strcmp(host_trace, "1") == 0 &&
        stats->frame >= 1948 && stats->frame <= 1970) {
        std::uint32_t hash = 2166136261u; // full 128 KiB WRAM, FNV-1a
        for (const std::uint8_t byte : g_ram) {
            hash ^= byte;
            hash *= 16777619u;
        }
        std::fprintf(stderr,
            "UR_BALDOSA_HOST_FRAME_CRC host=%u guest=%d hash=%08x\n",
            stats->frame, snes_frame_counter, static_cast<unsigned>(hash));
        std::fflush(stderr);
    }
    if (stats) {
        g_native_live_race = g_ram[0x0313] == 0x01;
        // Create at the FIRST observed authentic racing frame, not at the
        // first human pause. That gives Restart a real immutable race anchor.
        if (physical_modern_enabled() && g_native_live_race &&
            !g_modern_session) create_modern_session();
        if (g_modern_session)
            ur_modern_session_observe_race_active(
                g_modern_session, g_native_live_race ? 1 : 0);
        apply_host_lifecycle_pause();
        adopt_live_display_change();
        lifecycle_pause_smoke_frame();

        if (smoke_enabled() && g_delayed_restart_enabled &&
            g_native_live_race && !g_native_anchor_captured) {
            require(g_modern_session &&
                        ur_modern_session_restart_available(g_modern_session),
                    "delayed_restart_anchor_unavailable");
            g_native_anchor_captured = true;
            g_native_anchor_frame = stats->frame;
            std::memcpy(g_native_anchor_ram, g_ram, sizeof(g_native_anchor_ram));
        }

        // Explicit test-only, real same-boundary native rollback round trip.
        // It must leave guest WRAM, persistent SRAM and all future 2P frame
        // CRCs unchanged; the user-facing, multi-frame Retry still needs QA.
        if (!g_restart_same_frame_checked && g_native_live_race &&
            std::getenv("UR_BALDOSA_RESTART_SAME_FRAME_SMOKE") &&
            std::strcmp(std::getenv("UR_BALDOSA_RESTART_SAME_FRAME_SMOKE"), "1") == 0) {
            g_restart_same_frame_checked = true;
            require(g_modern_session &&
                    ur_modern_session_restart_available(g_modern_session),
                    "native_restart_anchor_missing");
            std::uint8_t before_ram[0x20000];
            std::memcpy(before_ram, g_ram, sizeof(before_ram));
            require(g_sram != nullptr && g_sram_size > 0,
                    "native_restart_sram_unavailable");
            const std::vector<std::uint8_t> preserved(
                g_sram, g_sram + static_cast<std::size_t>(g_sram_size));
            require(ur_modern_session_restart_race(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "native_rollback_restore_rejected");
            require(std::memcmp(g_ram, before_ram, sizeof(before_ram)) == 0,
                    "native_rollback_wram_changed");
            require(std::memcmp(g_sram, preserved.data(), preserved.size()) == 0,
                    "native_rollback_sram_changed");
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RESTART SAME_FRAME guest=%u sram_equal=1 wram_equal=1\n",
                stats->frame);
            std::fflush(stderr);
        }
    }
    if (!smoke_enabled()) return;
    require(stats != nullptr, "missing_frame_statistics");

    if (g_resumed && stats->frame == g_guest_frame + 1) {
        require(g_frozen_ticks >= 24, "insufficient_frozen_event_pumps");
        require(snesrecomp_desktop_product_is_paused() == 0,
                "guest_not_resumed_after_event");
        if (g_delayed_restart_enabled)
            require(g_delayed_restart_verified,
                    "delayed_restart_missing_acknowledgement");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=%u "
            "new_guest=%u frozen_pumps=%u\n",
            g_guest_frame, stats->frame, g_frozen_ticks);
        std::fflush(stderr);
        // Only one synthetic acceptance pause per process; no player data
        // or host controls are modified once the observation is complete.
        g_resumed = false;
        // Keep the real Modern session and immutable race anchor alive for
        // Retry after the smoke; only guest completion/front-end owns retirement.
    }

    // Explicit test frame only. Require the actual source guest's in-race
    // byte, shared with Modern's existing title-state observer, when enabled.
    // A script advancing frames without entering a race cannot pass the gate.
    if (!g_armed && stats->frame == g_pause_at_frame) {
        const bool live_race = g_ram[0x0313] == 0x01;
        if (g_require_race)
            require(live_race, "expected_live_race_state");
        if (g_delayed_restart_enabled) {
            require(g_physical_smoke, "delayed_restart_needs_sdl_input");
            require(g_native_anchor_captured &&
                        g_native_anchor_frame + 12 < stats->frame,
                    "delayed_restart_insufficient_real_guest_frames");
            require(std::memcmp(
                        g_native_anchor_ram, g_ram, sizeof(g_native_anchor_ram)) != 0,
                    "delayed_restart_guest_has_not_advanced");
            require(g_sram && g_sram_size > 0, "delayed_restart_missing_sram");
            g_paused_persistent_bytes.assign(
                g_sram, g_sram + static_cast<std::size_t>(g_sram_size));
        }
        g_armed = true;
        g_guest_frame = stats->frame;
        std::memcpy(g_frozen_ram, g_ram, sizeof(g_frozen_ram));
        if (g_physical_smoke) {
            require(physical_modern_enabled(), "physical_modern_mode_disabled");
            queue_escape_edge();  // next normal SDL event pump opens pause
        } else {
            create_modern_session();
            require(ur_modern_session_pause(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "modern_pause_was_not_acknowledged");
            require(snesrecomp_desktop_product_is_paused() != 0,
                    "host_not_actually_paused");
        }
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=%u live_race=%u modern_session=1 physical_sdl=%u\n",
            g_guest_frame, live_race ? 1U : 0U, g_physical_smoke ? 1U : 0U);
        std::fflush(stderr);
    }
}

extern "C" void ur_baldosa_product_host_tick(void) {
    lifecycle_pause_smoke_tick();
    if (!smoke_enabled() || !g_armed || g_resumed ||
        (g_frozen_ticks >= 24 && !g_pause_quit_smoke)) return;
    require(snesrecomp_desktop_product_is_paused() != 0,
            "host_exited_pause_without_permission");
    if (g_physical_smoke) {
        require(g_modern_session &&
                    ur_modern_session_is_paused(g_modern_session),
                "physical_sdl_did_not_reach_modern_session");
    }
    if (g_delayed_restart_enabled && g_frozen_ticks >= 8) {
        // At the eighth frozen pump the host queued an actual SDL 'R'
        // press/release; this is checked on the ninth pump after the SDL
        // dispatcher has handled it. No guest frames run during Restart.
        require(g_keyboard_restart.last_result() == UR_MODERN_SESSION_APPLIED &&
                    !g_keyboard_restart.holding() &&
                    ur_modern_session_is_paused(g_modern_session),
                "delayed_restart_did_not_reach_modern_native_session");
        require(std::memcmp(
                    g_ram, g_native_anchor_ram, sizeof(g_native_anchor_ram)) == 0,
                "delayed_restart_wram_did_not_rewind_to_race_anchor");
        require(g_sram &&
                    static_cast<std::size_t>(g_sram_size) ==
                        g_paused_persistent_bytes.size() &&
                    std::memcmp(g_sram, g_paused_persistent_bytes.data(),
                                g_paused_persistent_bytes.size()) == 0,
                "delayed_restart_did_not_preserve_persistent_sram");
        if (!g_delayed_restart_verified) {
            g_delayed_restart_verified = true;
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=%u "
                "request_guest=%u paused=1 sram_equal=1 wram_rewound=1\n",
                g_native_anchor_frame, g_guest_frame);
            std::fflush(stderr);
        }
    } else {
        require(std::memcmp(g_ram, g_frozen_ram, sizeof(g_frozen_ram)) == 0,
                "guest_wram_advanced_during_pause");
    }
    ++g_frozen_ticks;
    if (g_physical_smoke && g_pause_quit_smoke) {
        // Native CI requests the actual paused menu destination with SDL
        // keyboard edges: Up wraps Resume -> Quit, Enter commits. The
        // event loop, not this probe, decides when to close the process.
        if (g_frozen_ticks == 2) queue_key_edge(SDLK_UP);
        if (g_frozen_ticks >= 4 && !g_pause_quit_key_queued &&
            (g_pause_quit_conflict_gate.empty() ||
             std::filesystem::is_regular_file(g_pause_quit_conflict_gate))) {
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_QUIT,
                    "native_quit_not_selected_by_physical_edge");
            g_pause_quit_key_queued = true;
            queue_key_edge(SDLK_RETURN);
        }
        // The Windows driver owns a wall-clock timeout; this generous
        // tick bound guards accidentally unbounded frozen loops without
        // racing a legitimate independent process under turbo playback.
        if (g_frozen_ticks > 500000u && !g_pause_quit_key_queued)
            require(false, "native_quit_conflict_gate_timeout");
    }
    if (g_physical_smoke && g_pause_panel_nav_smoke) {
        // Test-only queued physical SDL key edges: Down then Up must
        // navigate the existing Modern model while the original guest stays
        // frozen. Never feed them into the guest controller word.
        if (g_frozen_ticks == 2) queue_key_edge(SDLK_DOWN);
        if (g_frozen_ticks == 4) {
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_RESTART,
                    "physical_down_did_not_select_restart");
            queue_key_edge(SDLK_UP);
        }
        if (g_frozen_ticks >= 6 && !g_pause_panel_nav_verified) {
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_RESUME &&
                    g_pause_panel_paints >= 4,
                    "native_paused_panel_navigation_or_paint_failed");
            g_pause_panel_nav_verified = true;
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_PAUSE_MENU NAV=1 down_up=1 "
                "selected=0 guest_steps=0\n");
            std::fflush(stderr);
        }
    }
    if (g_physical_smoke && g_pause_options_smoke) {
        // Real SDL key edges through the paused menu into the shared native
        // Options panel: Down, Down (Resume -> Restart -> Options), Enter,
        // Down, Down (Display -> VSync -> Volume), Left (volume 100 -> 90),
        // Escape closes the panel (not the pause). The original guest stays
        // frozen throughout (checked every tick above); the standard release
        // at tick 24 then resumes through the ordinary Escape path.
        switch (g_frozen_ticks) {
        case 2: case 4: options_smoke_edge(SDLK_DOWN, kGamepadBtn_DpadDown); break;
        case 6:
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_OPTIONS,
                    "pause_options_row_not_selected");
            options_smoke_edge(SDLK_RETURN, kGamepadBtn_A);
            break;
        case 8:
            require(ur_baldosa_modern_root_pause_options_active() != 0,
                    "pause_options_did_not_open");
            options_smoke_edge(SDLK_DOWN, kGamepadBtn_DpadDown);
            break;
        case 10: options_smoke_edge(SDLK_DOWN, kGamepadBtn_DpadDown); break;
        case 12: options_smoke_edge(SDLK_LEFT, kGamepadBtn_DpadLeft); break;
        case 14:
            require(snesrecomp_desktop_product_get_volume() == 90,
                    "pause_options_volume_not_applied");
            options_smoke_edge(SDLK_ESCAPE, kGamepadBtn_B);
            break;
        case 16:
            require(ur_baldosa_modern_root_pause_options_active() == 0 &&
                        ur_modern_session_is_paused(g_modern_session) &&
                        snesrecomp_desktop_product_is_paused() != 0,
                    "pause_options_escape_resumed_or_stayed_open");
            if (!g_pause_options_smoke_verified) {
                g_pause_options_smoke_verified = true;
                std::fprintf(stderr,
                    "UR_BALDOSA_NATIVE_PAUSE_MENU OPTIONS=%d volume=90 "
                    "closed_by_back=1 still_paused=1 guest_steps=0\n",
                    g_pause_options_smoke);
                std::fflush(stderr);
            }
            break;
        default: break;
        }
    }
    if (g_delayed_restart_enabled && g_frozen_ticks == 8)
        queue_restart_edge(); // SDL processes this BEFORE the next host tick
    if (g_frozen_ticks == 24 && !g_pause_quit_smoke) {
        // The host's real frozen compositor must keep the window visibly
        // alive during the entire native-pause interval. Presentations run
        // without a guest frame and without executing draw_ppu_frame().
        const unsigned frozen_presentations =
            snesrecomp_desktop_product_pause_presentations();
        require(frozen_presentations >= 23u,
                "native_pause_did_not_present_frozen_raster");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE FROZEN_PRESENT guest=%u present_count=%u "
            "no_guest_steps=1\n", g_guest_frame, frozen_presentations);
        std::fflush(stderr);
        if (g_physical_smoke) {
            // A second physical SDL edge, not a direct lifecycle call, resumes.
            // If the host fails to dispatch it, the guest remains frozen and
            // the existing bounded native route fails closed.
            queue_escape_edge();
        } else {
            require(ur_modern_session_resume(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "modern_resume_was_not_acknowledged");
            require(snesrecomp_desktop_product_is_paused() == 0,
                    "host_still_paused_after_resume");
            ur_modern_session_destroy(g_modern_session);
            g_modern_session = nullptr;
        }
        g_resumed = true;
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=%u frozen_pumps=%u physical_sdl=%u\n",
            g_guest_frame, g_frozen_ticks, g_physical_smoke ? 1U : 0U);
        std::fflush(stderr);
    }
}
