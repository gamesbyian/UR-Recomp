#include "uniracers_run_data.h"

#include <stdint.h>

namespace {

uint16_t read_le16(const unsigned char* wram, size_t offset) {
    return static_cast<uint16_t>(
        static_cast<uint16_t>(wram[offset]) |
        (static_cast<uint16_t>(wram[offset + 1]) << 8));
}

}  // namespace

extern "C" UrUniracersRunData ur_uniracers_read_run_data(
    const unsigned char* wram,
    size_t wram_size) {
    UrUniracersRunData out{};
    if (!wram || wram_size <= 0x0E20u) {
        return out;
    }

    out.minutes = read_le16(wram, 0x0E0F);
    out.tens_seconds = read_le16(wram, 0x0E13);
    out.seconds = read_le16(wram, 0x0E17);
    out.tenths = read_le16(wram, 0x0E1B);
    out.sub_tick = read_le16(wram, 0x0E1F);

    if (out.minutes < 0 || out.minutes > 9 ||
        out.tens_seconds < 0 || out.tens_seconds > 5 ||
        out.seconds < 0 || out.seconds > 9 ||
        out.tenths < 0 || out.tenths > 9 ||
        out.sub_tick < 0 || out.sub_tick > 5) {
        return UrUniracersRunData{};
    }

    out.valid = 1;
    return out;
}
