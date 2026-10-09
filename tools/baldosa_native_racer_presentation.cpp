/* Baldosa-native moving presentation experiment.
 * Exactly UR-Recomp's source-derived racer renderer and OAM admission gate.
 * This is intentionally host-only: no ROM, guest code, input, SRAM or Records
 * mutation. The original renderer owns pixels whenever UR's gate refuses.
 */
#include "racer_hd_presenter.hpp"
#include "presentation_density_compositor.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {
unsigned g_frame = 0;
unsigned g_captured = 0;
unsigned g_last_captured_frame = 0;
unsigned g_fallback_captured = 0;
unsigned g_last_fallback_frame = 0;

bool enabled() noexcept {
    const char* value = std::getenv("UR_BALDOSA_HD");
    return value != nullptr && std::strcmp(value, "1") == 0;
}

int density() noexcept {
    if (!enabled()) return 1;
    const char* value = std::getenv("UR_BALDOSA_HD_DENSITY");
    return value != nullptr && std::strcmp(value, "4") == 0 ? 4 : 1;
}

bool save_presented_pam(const std::uint8_t* argb, std::size_t pitch,
                        int width, int height, unsigned frame,
                        const char* stem = "ur-baldosa-frame") noexcept {
    const char* dir = std::getenv("UR_BALDOSA_HD_CAPTURE_DIR");
    if (dir == nullptr || dir[0] == '\0') return false;
    char path[1024];
    const int length = std::snprintf(path, sizeof(path),
        "%s/%s-%06u.pam", dir, stem, frame);
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
// Compare the actual composited raster to the nearest-scaled logical stock
// field *after* the title's source-derived draw callback. Both split views
// must contain genuine authored pixels, rather than merely changing stock
// scenery or positive source-OBJ admission logs. Diagnostic/capture frames
// only; no guest, PPU, or product-state mutation.
std::size_t authored_difference_count(
    const std::uint8_t* dst, std::size_t pitch, const std::uint8_t* field,
    int width, int height, int scale, bool bottom) noexcept {
    if (dst == nullptr || field == nullptr || width != 256 ||
        height != 224 || (scale != 1 && scale != 4) ||
        pitch < static_cast<std::size_t>(width * scale) * 4)
        return 0;
    const int split = height * scale / 2;
    const int row_start = bottom ? split : 0;
    const int row_end = bottom ? height * scale : split;
    std::size_t changed = 0;
    for (int y = row_start; y < row_end; ++y) {
        const auto* source_row = field +
            static_cast<std::size_t>(y / scale) * width * 4;
        const auto* composed_row = dst + static_cast<std::size_t>(y) * pitch;
        for (int x = 0; x < width * scale; ++x)
            if (std::memcmp(composed_row + static_cast<std::size_t>(x) * 4,
                            source_row + static_cast<std::size_t>(x / scale) * 4,
                            4) != 0)
                ++changed;
    }
    return changed;
}
} // namespace

extern "C" int ur_baldosa_hd_presentation_scale(void) {
    // Stable density for every accepted fixed logical scene: real HD art when
    // available, first-party nearest Original fallback otherwise. Neither
    // may let Baldosa's 1x raster write into a scaled buffer.
    return density();
}

extern "C" void ur_baldosa_hd_begin_sim_frame(unsigned number) {
    if (!enabled()) return;
    g_frame = number;
    // A single imported UR host patch allocates scaled host-presentation
    // pixels; the PPU, WRAM, and original logical field stay 256x224.
    ur::presentation::racer_hd_set_internal_render_scale(density());
    ur::presentation::racer_hd_begin_sim_frame(number);
}

extern "C" int ur_baldosa_hd_draw_frame(std::uint8_t* dst, std::size_t pitch,
    const std::uint8_t* field, int frame_w, int frame_h, double alpha) {
    if (!enabled()) return 0;
    const int handled = ur::presentation::racer_hd_draw_frame(
        dst, pitch, field, frame_w, frame_h, alpha);
    if (!handled) {
        const int scale = density();
        if (scale == 1) return 0; // stock host owns 1x Original
        const bool safe = ur::product::compose_nearest_density_frame(
            dst, pitch, field, frame_w, frame_h, scale);
        if (!safe) {
            std::fprintf(stderr,
                "UR_BALDOSA_FATAL invalid density fallback geometry width=%d "
                "height=%d pitch=%zu scale=%d\n",
                frame_w, frame_h, pitch, scale);
            std::abort(); // fail closed before partial/mis-sized texture writes
        }
        const std::size_t changed_top = authored_difference_count(
            dst, pitch, field, frame_w, frame_h, scale, false);
        const std::size_t changed_bottom = authored_difference_count(
            dst, pitch, field, frame_w, frame_h, scale, true);
        if (changed_top != 0 || changed_bottom != 0) {
            std::fprintf(stderr,
                "UR_BALDOSA_FATAL original density fallback changed pixels\n");
            std::abort();
        }
        if (g_frame >= 400 && g_frame <= 1700 &&
            g_fallback_captured < 3 && g_last_fallback_frame != g_frame) {
            const bool saved = save_presented_pam(
                dst, pitch, frame_w * scale, frame_h * scale, g_frame,
                "ur-baldosa-fallback");
            std::fprintf(stderr,
                "UR_BALDOSA_ORIGINAL_FALLBACK frame=%u logical=%dx%d "
                "raster=%dx%d pitch=%zu top_changed=%zu bottom_changed=%zu saved=%d\n",
                g_frame, frame_w, frame_h, frame_w * scale,
                frame_h * scale, pitch, changed_top, changed_bottom, saved ? 1 : 0);
            g_last_fallback_frame = g_frame;
            if (saved) ++g_fallback_captured;
        }
        return 1;
    }
    // Turbo presentation is asynchronous to guest frame cadence: accepted
    // HD frames occurred at 1808, 1856 and 1952 in the first native run.
    // Sample actual successful draw callbacks, not arbitrary frame moduli.
    if (g_frame >= 1800 && g_frame <= 2450
        && g_last_captured_frame != g_frame && g_captured < 9) {
        const int scale = ur::presentation::racer_hd_presentation_scale();
        const std::size_t top_changed = authored_difference_count(
            dst, pitch, field, frame_w, frame_h, scale, false);
        const std::size_t bottom_changed = authored_difference_count(
            dst, pitch, field, frame_w, frame_h, scale, true);
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAINT frame=%u raster=%dx%d pitch=%zu "
            "top_changed=%zu bottom_changed=%zu\n",
            g_frame, frame_w * scale, frame_h * scale, pitch,
            top_changed, bottom_changed);
        const bool saved = save_presented_pam(
            dst, pitch, frame_w * scale, frame_h * scale, g_frame);
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_COMPOSE frame=%u racer_present=1 "
            "logical=%dx%d source_art=ur hd_capture=%u raster=%dx%d density=%d\n",
            g_frame, frame_w, frame_h, saved ? 1u : 0u,
            frame_w * scale, frame_h * scale, scale);
        g_last_captured_frame = g_frame;
        if (saved) ++g_captured;
    }
    return handled;
}
