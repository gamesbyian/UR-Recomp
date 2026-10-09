/* Baldosa-native moving presentation experiment.
 * Exactly UR-Recomp's source-derived racer renderer and OAM admission gate.
 * This is intentionally host-only: no ROM, guest code, input, SRAM or Records
 * mutation. The original renderer owns pixels whenever UR's gate refuses.
 */
#include "racer_hd_presenter.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {
unsigned g_frame = 0;
unsigned g_captured = 0;
unsigned g_last_captured_frame = 0;

bool enabled() noexcept {
    const char* value = std::getenv("UR_BALDOSA_HD");
    return value != nullptr && std::strcmp(value, "1") == 0;
}

bool save_presented_pam(const std::uint8_t* argb, std::size_t pitch,
                        int width, int height, unsigned frame) noexcept {
    const char* dir = std::getenv("UR_BALDOSA_HD_CAPTURE_DIR");
    if (dir == nullptr || dir[0] == '\0') return false;
    char path[1024];
    const int length = std::snprintf(path, sizeof(path),
        "%s/ur-baldosa-frame-%06u.pam", dir, frame);
    if (length <= 0 || static_cast<std::size_t>(length) >= sizeof(path))
        return false;
    std::FILE* out = std::fopen(path, "wb");
    if (out == nullptr) return false;
    const int header_len = std::fprintf(out,
        "P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n", width, height);
    bool ok = header_len > 0;
    // Renderer supplies 0xAARRGGBB logical pixels. PAM is actual RGBA bytes.
    for (int y = 0; ok && y < height; ++y) {
        const std::uint8_t* row = argb + static_cast<std::size_t>(y) * pitch;
        for (int x = 0; x < width; ++x) {
            std::uint32_t pixel = 0;
            std::memcpy(&pixel, row + static_cast<std::size_t>(x) * 4, 4);
            const std::uint8_t rgba[] = {
                static_cast<std::uint8_t>((pixel >> 16) & 255),
                static_cast<std::uint8_t>((pixel >> 8) & 255),
                static_cast<std::uint8_t>(pixel & 255),
                static_cast<std::uint8_t>((pixel >> 24) & 255)
            };
            if (std::fwrite(rgba, 1, sizeof(rgba), out) != sizeof(rgba)) {
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

extern "C" void ur_baldosa_hd_begin_sim_frame(unsigned number) {
    if (!enabled()) return;
    g_frame = number;
    // The pinned Baldosa host accepts logical 256x224 pixels in draw_frame;
    // 4x internal output belongs to the subsequent adapter, not this gate.
    ur::presentation::racer_hd_set_internal_render_scale(1);
    ur::presentation::racer_hd_begin_sim_frame(number);
}

extern "C" int ur_baldosa_hd_draw_frame(std::uint8_t* dst, std::size_t pitch,
    const std::uint8_t* field, int frame_w, int frame_h, double alpha) {
    if (!enabled()) return 0;
    const int handled = ur::presentation::racer_hd_draw_frame(
        dst, pitch, field, frame_w, frame_h, alpha);
    if (!handled) return 0;
    // Turbo presentation is asynchronous to guest frame cadence: accepted
    // HD frames occurred at 1808, 1856 and 1952 in the first native run.
    // Sample actual successful draw callbacks, not arbitrary frame moduli.
    if (g_frame >= 1800 && g_frame <= 2450
        && g_last_captured_frame != g_frame && g_captured < 9) {
        const bool saved = save_presented_pam(dst, pitch, frame_w, frame_h, g_frame);
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_COMPOSE frame=%u racer_present=1 "
            "logical=%dx%d source_art=ur hd_capture=%u\n",
            g_frame, frame_w, frame_h, saved ? 1u : 0u);
        g_last_captured_frame = g_frame;
        if (saved) ++g_captured;
    }
    return handled;
}
