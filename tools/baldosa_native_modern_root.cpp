/* Real pinned Baldosa host's Modern root, using the already shipping shared
 * Modern painter and model. No guest writes or competing window/SDL loop.
 *
 * This is the first visible native root integration: Play yields the actual
 * existing guest title/menu to the player. It does not claim direct event
 * launch, Records callbacks, or route completeness for other destinations.
 */
#include "modern_root_overlay_presenter.hpp"
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
ModernRootMenu g_menu{};
std::string g_racer_name = "CREATE A RACER WITH X";
bool g_visible = false;
bool g_confirm_quit = false;
bool g_render_reported = false;
unsigned g_paint_count = 0;
int g_stock_target = -1;
std::uint16_t g_stock_settle = 0;
std::uint32_t g_stock_budget = 0;
std::uint8_t g_stock_previous_cursor = 0;
bool g_stock_waiting_cursor = false;
bool g_stock_waiting_transition = false;

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
void choose() {
    if (g_stock_target != -1) return;
    if (g_confirm_quit) {
        SDL_Event quit{};
        quit.type = SDL_QUIT;
        if (SDL_PushEvent(&quit) != 1)
            std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT quit_event_rejected\n");
        return;
    }
    const auto selected = ur::product::modern_root_menu_selected(g_menu);
    const auto index = ur::product::modern_root_destination_index(selected);
    if (selected != ModernRootDestination::Play &&
        selected != ModernRootDestination::Multiplayer) {
        // Practice/Records/Options need the original Modern route admission.
        // Do not invent a second UI/Records or alternate save namespace.
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
    if (g_confirm_quit || g_stock_target != -1) return;
    g_menu = ur::product::modern_root_menu_move(g_menu, delta);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT selected=%zu\n",
        ur::product::modern_root_destination_index(
            ur::product::modern_root_menu_selected(g_menu)));
}
void back() {
    if (g_stock_target != -1) {
        stock_route_abort("cancelled");
        return;
    }
    if (g_confirm_quit) g_confirm_quit = false;
    else g_confirm_quit = true;
}
}  // namespace

extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name) {
    g_racer_name = name && *name ? name : "CREATE A RACER WITH X";
}

extern "C" void ur_baldosa_modern_root_after_config(void) {
    if (!configured()) return;
    g_menu = ur::product::modern_root_menu_reset();
    g_confirm_quit = false;
    g_visible = true;
    g_render_reported = false;
    g_paint_count = 0;
    g_stock_target = -1;
    g_stock_budget = 0;
    ur_baldosa_product_set_host_focus(1);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT opened=1\n");
}

extern "C" int ur_baldosa_modern_root_key(int key, int pressed) {
    if (!g_visible) return 0;
    int action = 0;
    switch (key) {
    case SDLK_UP: action = -1; break;
    case SDLK_DOWN: action = 1; break;
    case SDLK_RETURN: action = 2; break;
    case SDLK_ESCAPE: action = 3; break;
    default: return 0;
    }
    if (!pressed) return 1;
    if (action == 2) choose();
    else if (action == 3) back();
    else navigate(action);
    return 1;
}

extern "C" int ur_baldosa_modern_root_gamepad(
    int player, int button, int pressed) {
    if (!g_visible || player != 0) return 0;
    int action = 0;
    switch (button) {
    case kGamepadBtn_DpadUp: action = -1; break;
    case kGamepadBtn_DpadDown: action = 1; break;
    case kGamepadBtn_A:
    case kGamepadBtn_Start: action = 2; break;
    case kGamepadBtn_B: action = 3; break;
    default: return 0;
    }
    if (!pressed) return 1;
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
        false, g_confirm_quit};
    const bool drawn = ur::product::render_modern_root_overlay(
        painter, reinterpret_cast<std::uint32_t*>(dst),
        static_cast<int>(pitch / 4), height, 1, 240,
        HostOverlayRect{8,10,240,204}, view);
    if (drawn) {
        ++g_paint_count;
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
    const char* opt = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE");
    if (!g_visible || !opt || (std::strcmp(opt, "1") != 0 &&
                             std::strcmp(opt, "2") != 0)) return;
    int key = 0;
    // In mode 1 test Records rejection then return to Play.
    // In mode 2 test actual 2P stock entry from the shared root.
    if (std::strcmp(opt, "2") == 0) {
        if (frame == 60 || frame == 62) key = SDLK_DOWN;
        else if (frame == 64) key = SDLK_RETURN;
    } else {
        if (frame >= 60 && frame <= 62) key = SDLK_DOWN;
        else if (frame == 63 || frame == 67) key = SDLK_RETURN;
        else if (frame >= 64 && frame <= 66) key = SDLK_UP;
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
}

extern "C" unsigned ur_baldosa_modern_root_paint_count(void) {
    return g_paint_count;
}
