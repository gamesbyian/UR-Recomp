/* Baldosa +24 / 342-column Original-world presentation bridge.
 * No guest writes. Native 342x224 is still NOT 4K output.
 * The historical bounded 1800..2450 experiment remains the default.
 * Explicit UR_BALDOSA_WS342_LIVE=1 uses the established Modern race
 * scene classifier to enable calibrated 1P/2P/VS world expansion.
 * Source of margin tiles: native/title/uniracers_ws_margins.c (live $7F
 * course table => calibrated ws_shadow). This does not widen gameplay.
 */
#include "uniracers_ws_margins.h"
#include "widescreen_output_composition.hpp"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" {
extern std::uint8_t g_ram[0x20000];
void ur_baldosa_hd_begin_sim_frame(unsigned);
int ur_baldosa_hd_presentation_scale(void);
int ur_baldosa_hd_draw_frame(std::uint8_t*, std::size_t,
    const std::uint8_t*, int, int, double);
}

namespace {
unsigned frame_number = 0;
unsigned last_capture = 0;
unsigned capture_count = 0;
// The guest owns the scene state; the host only observes it.
ur::product::HostWidescreenSceneState live_scene{};
// Calibration and geometry are frozen for the prepared presentation.
bool prepared_wide = false;
bool full_view_enabled() noexcept {
    const char* v = std::getenv("UR_BALDOSA_WS342");
    return v && std::strcmp(v, "1") == 0;
}
bool probe_enabled() noexcept {
    const char* e = std::getenv("UR_BALDOSA_WS24");
    return full_view_enabled() || (e && std::strcmp(e, "1") == 0);
}
int visible_margin() noexcept { return full_view_enabled() ? 43 : 24; }
int backing_margin() noexcept { return full_view_enabled() ? 48 : 24; }
int wide_width() noexcept { return 256 + 2 * visible_margin(); }
bool live_scene_enabled() noexcept {
    const char* v = std::getenv("UR_BALDOSA_WS342_LIVE");
    return full_view_enabled() && v && std::strcmp(v, "1") == 0;
}
// The pre-race mode must be observed at GUEST cadence, not only on sparse
// desktop prepares. Turbo routes can skip every host draw during selection.
// Sampling again at prepare uses the most recent authoritative guest state;
// neither sampler writes to SNES memory or changes the calibrated world.
ur::product::HostSceneComposition sample_live_scene() noexcept {
    if (g_ram[0x0313] != 0x01 && g_ram[0x009F] == 0xD7)
        ur::product::reset_widescreen_scene_state(&live_scene);
    const auto previous = live_scene.race_mode;
    const auto scene = ur::product::observe_widescreen_scene(
        &live_scene, g_ram[0x0313], g_ram[0x009F]);
    if (previous != live_scene.race_mode) {
        std::fprintf(stderr,
            "UR_BALDOSA_WS342_LIVE_MODE frame=%u mode=%u guest_race=%02X frontend=%02X\n",
            frame_number, static_cast<unsigned>(live_scene.race_mode),
            static_cast<unsigned>(g_ram[0x0313]),
            static_cast<unsigned>(g_ram[0x009F]));
    }
    return scene;
}
bool racing_window() noexcept {
    if (!probe_enabled()) return false;
    if (live_scene_enabled()) {
        return sample_live_scene() ==
            ur::product::HostSceneComposition::WorldExpand;
    }
    // Retain the reproducible historical 2P comparison unchanged.
    return frame_number >= 1800 && frame_number <= 2450;
}
bool dump_pam(const std::uint8_t* data, std::size_t pitch,
              int w, int h, unsigned frame) noexcept {
    const bool full = full_view_enabled();
    const char* dir = std::getenv(full
        ? "UR_BALDOSA_WS342_CAPTURE_DIR" : "UR_BALDOSA_WS24_CAPTURE_DIR");
    if (!dir || !*dir) return false;
    char path[1024];
    const int n = std::snprintf(path, sizeof(path),
        full ? "%s/ur-baldosa-ws342-%06u.pam"
             : "%s/ur-baldosa-ws24-%06u.pam", dir, frame);
    if (n <= 0 || static_cast<std::size_t>(n) >= sizeof(path)) return false;
    std::FILE* out = std::fopen(path, "wb");
    if (!out) return false;
    bool ok = std::fprintf(out,
        "P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n", w, h) > 0;
    for (int y = 0; ok && y < h; ++y) {
        const auto* row = data + static_cast<std::size_t>(y) * pitch;
        for (int x = 0; x < w; ++x) {
            std::uint32_t pixel = 0;
            std::memcpy(&pixel, row + static_cast<std::size_t>(x) * 4, 4);
            const std::uint8_t rgba[4] = {
                static_cast<std::uint8_t>((pixel >> 16) & 255),
                static_cast<std::uint8_t>((pixel >> 8) & 255),
                static_cast<std::uint8_t>(pixel & 255),
                static_cast<std::uint8_t>((pixel >> 24) & 255),
            };
            if (std::fwrite(rgba, 1, 4, out) != 4) {
                ok = false;
                break;
            }
        }
    }
    if (std::fclose(out) != 0) ok = false;
    if (!ok) std::remove(path);
    return ok;
}
} // namespace

extern "C" void ur_baldosa_ws24_prepare_frame(
    int, int, int* width, int* height) {
    // Failed/incomplete frame preparation must never leave last frame's
    // wide admission active for a later host callback.
    prepared_wide = false;
    if (!width || !height) return;
    const bool try_margin = racing_window();
    // Calibrate exclusively against existing guest WRAM+PPU VRAM. All
    // newly exposed BG cells are provided by the verified live course model.
    ur_ws_margins_prepare_frame(
        try_margin ? 1 : 0, try_margin ? backing_margin() : 0);
    prepared_wide = try_margin && ur_ws_margins_calibrated();
    const bool admit = prepared_wide;
    *width = admit ? wide_width() : 256;
    *height = 224;
    if (try_margin && frame_number % 60 == 0) {
        if (full_view_enabled())
            std::fprintf(stderr,
                "UR_BALDOSA_WS342_PREP frame=%u calibrated=%d "
                "logical=%dx%d backing=48 visible=43\n",
                frame_number, admit ? 1 : 0, *width, *height);
        else
            std::fprintf(stderr,
                "UR_BALDOSA_WS24_PREP frame=%u calibrated=%d "
                "logical=%dx%d margin=24\n",
                frame_number, admit ? 1 : 0, *width, *height);
    }
}
// A native desktop viewport hook, not an assertion of physical 4K output.
// Accept both logical and exact density-scaled callback dimensions.
extern "C" int ur_baldosa_ws24_original_viewport(
    int input_width, int input_height, int drawable_width, int drawable_height,
    int* out_x, int* out_y, int* out_width, int* out_height) {
    if (!full_view_enabled() || !out_x || !out_y || !out_width || !out_height)
        return 0;
    const int logical_width = prepared_wide ? 342 : 256;
    const int scale = ur_baldosa_hd_presentation_scale();
    if (scale < 1 || scale > 4 ||
        !((input_width == logical_width && input_height == 224) ||
          (input_width == logical_width * scale &&
           input_height == 224 * scale)))
        return 0;
    const auto plan = ur::product::resolve_16x9_output_composition(
        ur::product::HostGraphicsRepresentation::Original,
        prepared_wide ? ur::product::HostSceneComposition::WorldExpand
                      : ur::product::HostSceneComposition::FixedCenter);
    const auto viewport = ur::product::resolve_output_viewport(
        plan, drawable_width, drawable_height);
    if (viewport.width <= 0 || viewport.height <= 0) return 0;
    *out_x = viewport.x;
    *out_y = viewport.y;
    *out_width = viewport.width;
    *out_height = viewport.height;
    return 1;
}

extern "C" void ur_baldosa_ws24_begin_sim_frame(unsigned frame) {
    frame_number = frame;
    // Observe even if this guest frame never reaches the desktop presenter.
    // Otherwise a skipped pre-race host callback loses 1P/2P/VS identity.
    if (live_scene_enabled()) (void)sample_live_scene();
    ur_baldosa_hd_begin_sim_frame(frame);
}
extern "C" int ur_baldosa_ws24_draw_frame(std::uint8_t* dst,
    std::size_t pitch, const std::uint8_t* field,
    int width, int height, double alpha) {
    if (!prepared_wide || !ur_ws_margins_calibrated() ||
        width != wide_width() || height != 224)
        return ur_baldosa_hd_draw_frame(dst, pitch, field, width, height, alpha);

    // One existing source/HD/fallback compositor owns every host frame.
    // The wide PPU supplies genuine course-derived logical world pixels;
    // density changes only the destination. The former path copied 1x
    // pixels into a 4x output, leaving most of the buffer unwritten.
    // Racer HD conservatively refuses to remove stock OBJ at 342 columns;
    // its existing generic nearest fallback composes the complete wide field
    // until source-visible wide OBJ replacement is independently validated.
    const int scale = ur_baldosa_hd_presentation_scale();
    if (!dst || !field || scale < 1 || scale > 4 ||
        pitch < static_cast<std::size_t>(width) *
                    static_cast<std::size_t>(scale) * 4u) {
        std::fprintf(stderr,
            "UR_BALDOSA_FATAL unsafe wide density geometry width=%d height=%d "
            "pitch=%zu density=%d\n", width, height, pitch, scale);
        std::abort();
    }
    const int handled = ur_baldosa_hd_draw_frame(
        dst, pitch, field, width, height, alpha);
    if (!handled) {
        // An unhandled high-density draw would expose unwritten pixels.
        // Original's existing 1x stock contract remains valid.
        if (scale != 1) {
            std::fprintf(stderr,
                "UR_BALDOSA_FATAL wide density compositor declined scale=%d\n",
                scale);
            std::abort();
        }
        for (int y = 0; y < height; ++y)
            std::memcpy(dst + static_cast<std::size_t>(y) * pitch,
                        field + static_cast<std::size_t>(y) * width * 4u,
                        static_cast<std::size_t>(width) * 4u);
    }
    if (capture_count < 6 && frame_number != last_capture) {
        const bool saved = dump_pam(dst, pitch, width * scale, height * scale, frame_number);
        std::fprintf(stderr,
            full_view_enabled()
                ? "UR_BALDOSA_WS342_PRESENT frame=%u width=%d height=%d "
                  "pitch=%zu calibrated=1 saved=%d density=%d raster=%dx%d\n"
                : "UR_BALDOSA_WS24_PRESENT frame=%u width=%d height=%d "
                  "pitch=%zu calibrated=1 saved=%d density=%d raster=%dx%d\n",
            frame_number, width, height, pitch, saved ? 1 : 0,
            scale, width * scale, height * scale);
        last_capture = frame_number;
        if (saved) ++capture_count;
    }
    return 1;
}
