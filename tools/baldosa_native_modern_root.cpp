/* Real pinned Baldosa host's Modern root, using the already shipping shared
 * Modern painter and model. No guest writes or competing window/SDL loop.
 *
 * This is the first visible native root integration: Play yields the actual
 * existing guest title/menu to the player. It does not claim direct event
 * launch, Records callbacks, or route completeness for other destinations.
 */
#include "modern_root_overlay_presenter.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
void ur_baldosa_product_set_host_focus(int);
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

bool configured() {
    const char* opt = std::getenv("UR_BALDOSA_MODERN_ROOT");
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return opt && std::strcmp(opt, "1") == 0 &&
        !(mode && std::strcmp(mode, "authentic") == 0);
}
void choose() {
    if (g_confirm_quit) {
        SDL_Event quit{};
        quit.type = SDL_QUIT;
        if (SDL_PushEvent(&quit) != 1)
            std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT quit_event_rejected\n");
        return;
    }
    const auto selected = ur::product::modern_root_menu_selected(g_menu);
    const auto index = ur::product::modern_root_destination_index(selected);
    if (selected != ModernRootDestination::Play) {
        // The original Modern route's profile/Records/Options authorities are
        // not yet available in this native process. Do not invent facades.
        std::fprintf(stderr,
            "UR_BALDOSA_MODERN_ROOT route=%zu unavailable=1\n", index);
        return;
    }
    g_visible = false;
    ur_baldosa_product_set_host_focus(0);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT play_guest_title=1\n");
}
void navigate(int delta) {
    if (g_confirm_quit) return;
    g_menu = ur::product::modern_root_menu_move(g_menu, delta);
    std::fprintf(stderr, "UR_BALDOSA_MODERN_ROOT selected=%zu\n",
        ur::product::modern_root_destination_index(
            ur::product::modern_root_menu_selected(g_menu)));
}
void back() {
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
extern "C" void ur_baldosa_modern_root_after_run_frame(unsigned frame) {
    const char* opt = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE");
    if (!g_visible || !opt || std::strcmp(opt, "1") != 0) return;
    int key = 0;
    if (frame >= 60 && frame <= 62) key = SDLK_DOWN;
    else if (frame == 63 || frame == 67) key = SDLK_RETURN;
    else if (frame >= 64 && frame <= 66) key = SDLK_UP;
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
