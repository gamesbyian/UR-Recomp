/* Disposable Baldosa +24 / 342-column 16:9 world presentation probes.
 * No guest writes. Native 342x224 is still NOT 4K output.
 * Source of margin tiles: native/title/uniracers_ws_margins.c (live $7F
 * course table => calibrated ws_shadow). This does not widen gameplay.
 */
#include "uniracers_ws_margins.h"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" {
void ur_baldosa_hd_begin_sim_frame(unsigned);
int ur_baldosa_hd_draw_frame(std::uint8_t*, std::size_t,
    const std::uint8_t*, int, int, double);
}

namespace {
unsigned frame_number = 0;
unsigned last_capture = 0;
unsigned capture_count = 0;
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
bool racing_window() noexcept {
    // Bounded two-player proof only. This is deliberately NOT a gameplay
    // state classifier and must never be enabled as a shipping scene policy.
    return probe_enabled() && frame_number >= 1800 && frame_number <= 2450;
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
    if (!width || !height) return;
    const bool try_margin = racing_window();
    // Calibrate exclusively against existing guest WRAM+PPU VRAM. All
    // newly exposed BG cells are provided by the verified live course model.
    ur_ws_margins_prepare_frame(
        try_margin ? 1 : 0, try_margin ? backing_margin() : 0);
    const bool admit = try_margin && ur_ws_margins_calibrated();
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
extern "C" void ur_baldosa_ws24_begin_sim_frame(unsigned frame) {
    frame_number = frame;
    ur_baldosa_hd_begin_sim_frame(frame);
}
extern "C" int ur_baldosa_ws24_draw_frame(std::uint8_t* dst,
    std::size_t pitch, const std::uint8_t* field,
    int width, int height, double alpha) {
    if (!racing_window() || !ur_ws_margins_calibrated() ||
        width != wide_width() || height != 224 || !dst || !field ||
        pitch < static_cast<std::size_t>(width) * 4)
        return ur_baldosa_hd_draw_frame(dst, pitch, field, width, height, alpha);
    // The PPU produced actual 304- or 342-column course-derived pixels.
    // The 342-column view uses 43 visible logical pixels per side while
    // supplying 48 pixels' worth of host-owned course tiles for its
    // fractional tile-phase guard. No authored sprite inventing.
    for (int y = 0; y < height; ++y)
        std::memcpy(dst + static_cast<std::size_t>(y) * pitch,
                    field + static_cast<std::size_t>(y) * width * 4,
                    static_cast<std::size_t>(width) * 4);
    if (capture_count < 6 && frame_number != last_capture) {
        const bool saved = dump_pam(dst, pitch, width, height, frame_number);
        std::fprintf(stderr,
            full_view_enabled()
                ? "UR_BALDOSA_WS342_PRESENT frame=%u width=%d height=%d "
                  "pitch=%zu calibrated=1 saved=%d\n"
                : "UR_BALDOSA_WS24_PRESENT frame=%u width=%d height=%d "
                  "pitch=%zu calibrated=1 saved=%d\n",
            frame_number, width, height, pitch, saved ? 1 : 0);
        last_capture = frame_number;
        if (saved) ++capture_count;
    }
    return 1;
}
