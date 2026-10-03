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


    std::array<std::uint16_t, 256> ppu_oam{};
    std::array<std::uint8_t, 32> ppu_high{};
    ppu_oam[98 * 2] = static_cast<std::uint16_t>((40u << 8) | 104u);
    ppu_oam[98 * 2 + 1] = static_cast<std::uint16_t>((0x66u << 8) | 0x00u);
    ppu_high[98 / 4] = static_cast<std::uint8_t>(2u << ((98 % 4) * 2));

    const auto ppu_p1 = decode_racer_ppu_placement(
        ppu_oam.data(), ppu_oam.size(),
        ppu_high.data(), ppu_high.size(),
        0x83, 1
    );
    assert(ppu_p1.has_value());
    assert(ppu_p1->slot == 98);
    assert(ppu_p1->x_signed == 104);
    assert(ppu_p1->y_raw_8bit == 40);
    assert(ppu_p1->hflip);
    assert(!ppu_p1->vflip);
    assert(ppu_p1->width_pixels == 64);
    assert(ppu_p1->height_pixels == 64);


    // Uniracers' two-player raster presents both semantic racers twice:
    // top viewport uses slots 98/99 under high-OAM 0xA5; bottom uses
    // slots 97/96 under 0x5A. Low OAM retains both coordinate sets.
    std::array<std::uint16_t, 256> split_oam{};
    split_oam[98 * 2] = static_cast<std::uint16_t>((40u << 8) | 104u);
    split_oam[98 * 2 + 1] = static_cast<std::uint16_t>((0x66u << 8) | 0x00u);
    split_oam[99 * 2] = static_cast<std::uint16_t>((40u << 8) | 104u);
    split_oam[99 * 2 + 1] = static_cast<std::uint16_t>((0x68u << 8) | 0x88u);
    split_oam[97 * 2] = static_cast<std::uint16_t>((153u << 8) | 104u);
    split_oam[97 * 2 + 1] = static_cast<std::uint16_t>((0x66u << 8) | 0x00u);
    split_oam[96 * 2] = static_cast<std::uint16_t>((153u << 8) | 104u);
    split_oam[96 * 2 + 1] = static_cast<std::uint16_t>((0x68u << 8) | 0x88u);

    const auto p1_top = decode_racer_split_ppu_placement(
        split_oam.data(), split_oam.size(), 0x83, 1, RacerViewport::Top
    );
    const auto p2_top = decode_racer_split_ppu_placement(
        split_oam.data(), split_oam.size(), 0x83, 2, RacerViewport::Top
    );
    const auto p1_bottom = decode_racer_split_ppu_placement(
        split_oam.data(), split_oam.size(), 0x83, 1, RacerViewport::Bottom
    );
    const auto p2_bottom = decode_racer_split_ppu_placement(
        split_oam.data(), split_oam.size(), 0x83, 2, RacerViewport::Bottom
    );
    assert(p1_top && p1_top->slot == 98 && p1_top->large && p1_top->y_raw_8bit == 40);
    assert(p2_top && p2_top->slot == 99 && p2_top->large && p2_top->tile == 0x88);
    assert(p1_bottom && p1_bottom->slot == 97 && p1_bottom->large && p1_bottom->y_raw_8bit == 153);
    assert(p2_bottom && p2_bottom->slot == 96 && p2_bottom->large && p2_bottom->tile == 0x88);
    assert(p1_bottom->x_signed == 104);
    assert(p2_bottom->x_signed == 104);

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
    assert(!decode_racer_ppu_placement(nullptr, 256, ppu_high.data(), ppu_high.size(), 0x83, 1).has_value());
    assert(!decode_racer_ppu_placement(ppu_oam.data(), 100, ppu_high.data(), ppu_high.size(), 0x83, 1).has_value());
    assert(!decode_racer_ppu_placement(ppu_oam.data(), ppu_oam.size(), nullptr, 32, 0x83, 1).has_value());
    assert(!decode_racer_split_ppu_placement(nullptr, 256, 0x83, 1, RacerViewport::Top).has_value());
    assert(!decode_racer_split_ppu_placement(split_oam.data(), 100, 0x83, 1, RacerViewport::Top).has_value());
    assert(!decode_racer_split_ppu_placement(split_oam.data(), split_oam.size(), 0x83, 3, RacerViewport::Top).has_value());
    return 0;
}
