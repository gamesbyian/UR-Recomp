/* QA-08 only: actual fixed Original PPU framebuffer sampled by the native
 * Baldosa host's existing end_sim_frame hook. No guest writes, painter,
 * 2D compositor, Modern state, alternate renderer or screen crop.
 * 
 * This is opt-in and never enabled for an ordinary player. The read-only
 * slot is called AFTER draw_ppu_frame, with full logical 256x224 ARGB pixels,
 * independently of title draw_frame and host SDL scaling.
 */
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {
constexpr unsigned kFrame[] = {1856, 2192, 2208, 2224};
constexpr int kWidth = 256;
constexpr int kHeight = 224;
unsigned g_seen = 0;

bool wanted(unsigned frame) noexcept {
    for (unsigned select : kFrame)
        if (frame == select) return true;
    return false;
}

bool save_source(const char* dir, const std::uint8_t* field,
                 unsigned frame) noexcept {
    char file[1024];
    const int written = std::snprintf(file, sizeof(file),
        "%s/ur-baldosa-original-source-%06u.pam", dir, frame);
    if (written <= 0 || static_cast<std::size_t>(written) >= sizeof(file))
        return false;
    std::FILE* handle = std::fopen(file, "wb");
    if (!handle) return false;
    bool ok = std::fprintf(handle,
        "P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n") > 0;
    for (int y = 0; ok && y < kHeight; ++y)
        for (int x = 0; ok && x < kWidth; ++x) {
            std::uint32_t argb = 0;
            std::memcpy(&argb, field + (y * kWidth + x) * 4u, 4);
            const std::uint8_t rgba[4] = {
                static_cast<std::uint8_t>((argb >> 16) & 255),
                static_cast<std::uint8_t>((argb >> 8) & 255),
                static_cast<std::uint8_t>(argb & 255),
                static_cast<std::uint8_t>((argb >> 24) & 255)
            };
            ok = std::fwrite(rgba, 1, sizeof(rgba), handle) == sizeof(rgba);
        }
    if (std::fclose(handle) != 0) ok = false;
    if (!ok) std::remove(file);
    return ok;
}
}

extern "C" void ur_qa08_windows_capture_original_source(
    const std::uint8_t* field, unsigned guest_frame) {
    // Independent source producer: no synthetic frame for a missing callback.
    // Reject repeat presentation rather than overwriting a source witness.
    if (!wanted(guest_frame)) return;
    const char* dir = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR");
    if (!dir || !dir[0]) return;
    if (guest_frame == 0 || !field || (g_seen & (1u << (guest_frame == 1856 ? 0 :
        guest_frame == 2192 ? 1 : guest_frame == 2208 ? 2 : 3)))) {
        std::fprintf(stderr, "UR_QA08_WINDOWS_SOURCE_REJECT frame=%u reason=repeat-or-null\n",
                     guest_frame);
        return;
    }
    const unsigned bit = guest_frame == 1856 ? 0 : guest_frame == 2192 ? 1 :
                         guest_frame == 2208 ? 2 : 3;
    const bool saved = save_source(dir, field, guest_frame);
    if (saved) g_seen |= (1u << bit);
    std::fprintf(stderr,
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=%u logical=256x224 "
        "saved=%u source=post-original-ppu-before-present\n",
        guest_frame, saved ? 1u : 0u);
}
