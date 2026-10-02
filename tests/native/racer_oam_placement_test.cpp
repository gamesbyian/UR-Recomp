#include "racer_oam_placement.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::presentation;

namespace {

void set_slot(
    std::array<std::uint8_t, 544>& oam,
    std::uint8_t slot,
    std::uint16_t x,
    std::uint8_t y,
    std::uint8_t tile,
    std::uint8_t attr,
    bool large
) {
    const std::size_t q = static_cast<std::size_t>(slot) * 4;
    oam[q + 0] = static_cast<std::uint8_t>(x & 0xFF);
    oam[q + 1] = y;
    oam[q + 2] = tile;
    oam[q + 3] = attr;
    const std::size_t high = 0x200 + slot / 4;
    const unsigned shift = (slot % 4) * 2;
    const std::uint8_t pair =
        static_cast<std::uint8_t>(((x >> 8) & 1) | (large ? 2 : 0));
    oam[high] = static_cast<std::uint8_t>(
        (oam[high] & ~(0x03u << shift)) | (pair << shift)
    );
}

}  // namespace

int main() {
    std::array<std::uint8_t, 544> oam{};
    set_slot(oam, 98, 104, 40, 0x00, 0x66, true);
    set_slot(oam, 99, 104, 40, 0x88, 0x68, true);

    const auto p1 = decode_racer_oam_placement(oam.data(), oam.size(), 0x83, 1);
    assert(p1.has_value());
    assert(p1->slot == 98);
    assert(p1->x_raw_9bit == 104);
    assert(p1->x_signed == 104);
    assert(p1->y_raw_8bit == 40);
    assert(p1->tile == 0x00);
    assert(p1->attr == 0x66);
    assert(p1->hflip);
    assert(!p1->vflip);
    assert(p1->large);
    assert(p1->width_pixels == 64);
    assert(p1->height_pixels == 64);

    const auto p2 = decode_racer_oam_placement(oam.data(), oam.size(), 0x83, 2);
    assert(p2.has_value());
    assert(p2->slot == 99);
    assert(p2->tile == 0x88);
    assert(p2->attr == 0x68);
    assert(p2->width_pixels == 64);
    assert(p2->height_pixels == 64);

    set_slot(oam, 98, 500, 200, 0x00, 0x00, false);
    const auto wrapped = decode_racer_oam_placement(oam.data(), oam.size(), 0x00, 1);
    assert(wrapped.has_value());
    assert(wrapped->x_raw_9bit == 500);
    assert(wrapped->x_signed == -12);
    assert(!wrapped->large);
    assert(wrapped->width_pixels == 8);
    assert(wrapped->height_pixels == 8);

    assert(!decode_racer_oam_placement(nullptr, 544, 0x83, 1).has_value());
    assert(!decode_racer_oam_placement(oam.data(), 100, 0x83, 1).has_value());
    assert(!decode_racer_oam_placement(oam.data(), oam.size(), 0x83, 3).has_value());
    return 0;
}
