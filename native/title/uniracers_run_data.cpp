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

extern "C" int64_t ur_uniracers_run_data_ticks60(UrUniracersRunData data) {
    if (!data.valid ||
        data.minutes < 0 || data.minutes > 9 ||
        data.tens_seconds < 0 || data.tens_seconds > 5 ||
        data.seconds < 0 || data.seconds > 9 ||
        data.tenths < 0 || data.tenths > 9 ||
        data.sub_tick < 0 || data.sub_tick > 5) {
        return -1;
    }
    const int64_t whole_seconds =
        static_cast<int64_t>(data.minutes) * 60 +
        static_cast<int64_t>(data.tens_seconds) * 10 +
        static_cast<int64_t>(data.seconds);
    return whole_seconds * 60 +
           static_cast<int64_t>(data.tenths) * 6 +
           static_cast<int64_t>(data.sub_tick);
}

extern "C" UrUniracersLineSnapshot ur_uniracers_read_line_snapshot(
    const unsigned char* wram,
    size_t wram_size,
    int player) {
    UrUniracersLineSnapshot out{};
    if (!wram || player < 0 || player > 1 || wram_size <= 0x0E48u) {
        return out;
    }
    const size_t slot = static_cast<size_t>(player) * 2u;
    out.hundredths = read_le16(wram, 0x0E35 + slot);
    out.minutes = read_le16(wram, 0x0E39 + slot);
    out.tens_seconds = read_le16(wram, 0x0E3D + slot);
    out.seconds = read_le16(wram, 0x0E41 + slot);
    out.tenths = read_le16(wram, 0x0E45 + slot);
    if (out.minutes < 0 || out.minutes > 9 ||
        out.tens_seconds < 0 || out.tens_seconds > 5 ||
        out.seconds < 0 || out.seconds > 9 ||
        out.tenths < 0 || out.tenths > 9 ||
        out.hundredths < 0 || out.hundredths > 9) {
        return UrUniracersLineSnapshot{};
    }
    out.valid = 1;
    return out;
}

extern "C" int ur_uniracers_read_laps_remaining(
    const unsigned char* wram,
    size_t wram_size,
    int player) {
    if (!wram || player < 0 || player > 1 || wram_size <= 0x0EF4u) return -1;
    return read_le16(wram, 0x0EF1 + static_cast<size_t>(player) * 2u);
}

extern "C" int ur_uniracers_line_snapshot_equal(
    UrUniracersLineSnapshot a,
    UrUniracersLineSnapshot b) {
    return a.valid == b.valid && a.minutes == b.minutes &&
           a.tens_seconds == b.tens_seconds && a.seconds == b.seconds &&
           a.tenths == b.tenths && a.hundredths == b.hundredths;
}

extern "C" int64_t ur_uniracers_line_snapshot_ticks60(
    UrUniracersRunData shared_at_write,
    UrUniracersLineSnapshot snapshot) {
    const int64_t shared = ur_uniracers_run_data_ticks60(shared_at_write);
    if (shared < 0 || !snapshot.valid) return -1;
    UrUniracersRunData base{};
    base.valid = 1;
    base.minutes = snapshot.minutes;
    base.tens_seconds = snapshot.tens_seconds;
    base.seconds = snapshot.seconds;
    base.tenths = snapshot.tenths;
    base.sub_tick = 0;
    const int64_t tenth_start = ur_uniracers_run_data_ticks60(base);
    if (tenth_start < 0) return -1;
    if (shared >= tenth_start && shared <= tenth_start + 5) return shared;
    if (shared == tenth_start + 6) return tenth_start + 5;
    return -1;
}
