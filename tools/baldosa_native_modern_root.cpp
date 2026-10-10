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
}

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

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
std::string g_racer_name = "STOCK RACER - NO PROFILE";
bool g_visible = false;
bool g_confirm_quit = false;
bool g_records_open = false;
std::string g_records_status;
std::string g_records_recent;
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
    g_stock_handed_off = false;
    g_handed_off_players = 0;
    g_handed_off_saw_race = false;
    g_reentry_needs_paint = true;
    ur_baldosa_product_set_host_focus(1);
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0\n");
    return true;
}
void open_records_archive() {
    g_records_open = true;
    const char* directory = ur_baldosa_modern_profile_records_directory();
    if (!directory || !*directory) {
        g_records_status = "NO ACTIVE NAMED RACER";
        g_records_recent = "CREATE OR SELECT A RACER";
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=none validated=0 unavailable=0\n");
        return;
    }
    const auto result =
        ur::product::inspect_baldosa_native_records_archive(directory);
    if (!result.directory_available) {
        g_records_status = "RECORDS DIRECTORY INVALID";
        g_records_recent = "NOTHING WAS LOADED";
    } else {
        g_records_status =
            "VALID " + std::to_string(result.validated_archives) +
            "  UNAVAILABLE " + std::to_string(result.unavailable_artifacts);
        if (result.validated_archives == 0) {
            g_records_recent = "NO STORED RUNS YET";
        } else {
            const auto hundredths =
                (result.recent_ticks60 * 100u + 30u) / 60u;
            char timing[24]{};
            std::snprintf(timing, sizeof(timing), "%02llu:%02llu.%02llu",
                static_cast<unsigned long long>(hundredths / 6000u),
                static_cast<unsigned long long>((hundredths / 100u) % 60u),
                static_cast<unsigned long long>(hundredths % 100u));
            g_records_recent =
                "LAST: " + result.recent_course + " " + timing;
        }
    }
    std::fprintf(stderr,
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=%zu unavailable=%zu\n",
        result.validated_archives, result.unavailable_artifacts);
}

void choose() {
    if (g_stock_target != -1) return;
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
    g_stock_target = selected == ModernRootDestination::Play ? 0 : 1;
    g_stock_settle = 0;
    g_stock_budget = ur::product::kQuickPracticeLaunchMaxObservations;
    g_stock_waiting_cursor = false;
    g_stock_waiting_transition = false;
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT stock_requested players=%d\n",
        g_stock_target + 1);
}
void navigate(int delta) {
    if (g_confirm_quit || g_records_open || g_stock_target != -1) return;
    g_menu = ur::product::modern_root_menu_move(g_menu, delta);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT selected=%zu\n",
        ur::product::modern_root_destination_index(
            ur::product::modern_root_menu_selected(g_menu)));
}
void back() {
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

extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name) {
    g_racer_name = name && *name ? name : "STOCK RACER - NO PROFILE";
}

extern "C" void ur_baldosa_modern_root_after_config(void) {
    if (!configured()) return;
    g_menu = ur::product::modern_root_menu_reset();
    g_navigation_edges.reset();
    g_confirm_quit = false;
    g_records_open = false;
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
    else navigate(action);
    return 1;
}

extern "C" int ur_baldosa_modern_root_gamepad(
    int player, int button, int pressed) {
    if (player != 0) return 0;
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
    else navigate(action);
    return 1;
}

extern "C" int ur_baldosa_modern_root_draw_frame(
    std::uint8_t* dst, std::size_t pitch, const std::uint8_t* field,
    int width, int height, double) {
    if (!g_visible) return 0;
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
    const ModernRootOverlayView view{
        g_menu, false, g_racer_name,
        false, g_confirm_quit, kNativeRootAvailable, false,
        g_records_open, g_records_status, g_records_recent};
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
    if (g_stock_budget-- == 0) {
        stock_route_abort("timeout");
        return;
    }
    const std::uint8_t menu = g_ram[0x009f];
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
                             std::strcmp(opt, "2") != 0)) return;
    int key = 0;
    // In mode 1 open and close the actual read-only Records archive,
    // then enter 1P. Mode 2 proves the actual stock 2P handoff.
    if (std::strcmp(opt, "2") == 0) {
        if (frame == 60 || frame == 62) key = SDLK_DOWN;
        else if (frame == 64) key = SDLK_RETURN;
    } else {
        if (frame >= 60 && frame <= 62) key = SDLK_DOWN;
        else if (frame == 63 || frame == 68) key = SDLK_RETURN;
        else if (frame == 64) key = SDLK_ESCAPE;
        else if (frame >= 65 && frame <= 67) key = SDLK_UP;
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
