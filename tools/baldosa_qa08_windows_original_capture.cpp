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
constexpr unsigned kOnePlayerFirst = 1280;
constexpr unsigned kOnePlayerLast = 5440;
constexpr unsigned kOnePlayerStep = 16;
constexpr unsigned kOnePlayerSlots =
    (kOnePlayerLast - kOnePlayerFirst) / kOnePlayerStep + 1;
constexpr unsigned kTwoPlayerLast = 5472;
/* Exact genuine 2014 original 1P callback2176..2240 maps to native f+1. */
constexpr unsigned kRealOriginal1PFirst = 2177;
constexpr unsigned kRealOriginal1PLast = 2241;
constexpr unsigned kRealOriginal1PSlots = 65;
constexpr unsigned kTwoPlayerSlots =
    (kTwoPlayerLast - kOnePlayerFirst) / kOnePlayerStep + 1;
constexpr int kWidth = 256;
constexpr int kHeight = 224;
bool g_seen_default[4] = {};
bool g_seen_oneplayer[kOnePlayerSlots] = {};
bool g_seen_twoplayer[kTwoPlayerSlots] = {};
bool g_seen_real_original1p[kRealOriginal1PSlots] = {};

// One explicitly bounded diagnostic case. The default post-PPU observer
// remains exactly its previously accepted 2P four-frame experiment.
// No arbitrary frame lists, guest mutation or global presentation controls.
bool oneplayer_coverage_mode() noexcept {
    const char* mode = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE");
    return mode && std::strcmp(mode, "oneplayer-coverage") == 0;
}

bool real_original1p_65_mode() noexcept {
    const char* mode = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE");
    return mode && std::strcmp(mode, "oneplayer-original65") == 0;
}

bool twoplayer_coverage_mode() noexcept {
    const char* mode = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE");
    return mode && std::strcmp(mode, "twoplayer-fullroute") == 0;
}

int wanted_index(unsigned frame, bool oneplayer, bool twoplayer) noexcept {
    if (oneplayer || twoplayer) {
        const unsigned last = twoplayer ? kTwoPlayerLast : kOnePlayerLast;
        if (frame < kOnePlayerFirst || frame > last ||
            (frame - kOnePlayerFirst) % kOnePlayerStep != 0)
            return -1;
        return static_cast<int>((frame - kOnePlayerFirst) / kOnePlayerStep);
    }
    for (unsigned i = 0; i < sizeof(kFrame) / sizeof(kFrame[0]); ++i)
        if (frame == kFrame[i]) return static_cast<int>(i);
    return -1;
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
    const char* dir = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR");
    if (!dir || !dir[0]) return;
    const char* mode = std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE");
    if (mode && mode[0] && !oneplayer_coverage_mode() &&
        !twoplayer_coverage_mode() && !real_original1p_65_mode()) {
        // Bad diagnostic selectors fail closed. Not even a diagnostic file
        // is produced, and ordinary game output remains unmodified.
        return;
    }
    const bool real1p = real_original1p_65_mode();
    const bool oneplayer = oneplayer_coverage_mode();
    const bool twoplayer = twoplayer_coverage_mode();
    const int index = real1p ?
        (guest_frame >= kRealOriginal1PFirst && guest_frame <= kRealOriginal1PLast ?
         static_cast<int>(guest_frame - kRealOriginal1PFirst) : -1) :
        wanted_index(guest_frame, oneplayer, twoplayer);
    if (index < 0) return;
    bool& seen = real1p ? g_seen_real_original1p[index] :
        twoplayer ? g_seen_twoplayer[index] :
        (oneplayer ? g_seen_oneplayer[index] : g_seen_default[index]);
    if (guest_frame == 0 || !field || seen) {
        std::fprintf(stderr, "UR_QA08_WINDOWS_SOURCE_REJECT frame=%u reason=repeat-or-null\n",
                     guest_frame);
        return;
    }
    const bool saved = save_source(dir, field, guest_frame);
    if (saved) seen = true;
    std::fprintf(stderr,
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=%u logical=256x224 "
        "saved=%u source=post-original-ppu-before-present\n",
        guest_frame, saved ? 1u : 0u);
}
