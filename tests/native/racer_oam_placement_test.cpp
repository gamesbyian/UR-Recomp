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
    // Exhaust all possible hardware Y values and the full 64-row large OBJ:
    // each source row must land on exactly the corresponding modulo-256
    // scanline or be culled by the 224-row visible field.
    for (int scale = 1; scale <= 4; ++scale) {
        for (int raw_y = 0; raw_y < 256; ++raw_y) {
            for (int source_row = 0; source_row < 64; ++source_row) {
                const int logical = (raw_y + source_row) & 0xFF;
                const int actual = racer_obj_wrapped_output_row(
                    static_cast<std::uint8_t>(raw_y), source_row * scale, scale
                );
                assert(actual == (logical < 224 ? logical * scale : -1));
            }
        }
    }

    // A sprite's 8-bit Y is modulo 256, not modulo the 224 visible rows.
    // Row 250 itself is below the visible image, but source row 6 wraps to 0.
    // Row 224 remains offscreen even though the hardware sprite exists there.
    for (int scale = 1; scale <= 4; ++scale) {
        const auto project = [scale](std::uint8_t y, int source_row) {
            return racer_obj_wrapped_output_row(y, source_row, scale);
        };
        assert(project(0, 0) == 0);
        assert(project(200, 23 * scale) == 223 * scale);
        assert(project(200, 24 * scale) == -1);
        assert(project(250, 0) == -1);
        assert(project(250, 6 * scale - 1) == -1);
        assert(project(250, 6 * scale) == 0);
        assert(project(250, 63 * scale) == 57 * scale);
        assert(project(255, 0) == -1);
        assert(project(255, scale) == 0);
        assert(racer_split_viewport_contains_row(
            RacerViewport::Top, project(250, 6 * scale), scale
        ));
        assert(!racer_split_viewport_contains_row(
            RacerViewport::Bottom, project(250, 6 * scale), scale
        ));
        assert(project(0, -1) == -1);
        assert(project(0, 64 * scale) == -1);
    }
    assert(racer_obj_wrapped_output_row(250, 6, 0) == -1);
    assert(racer_obj_wrapped_output_row(250, 6, 5) == -1);

    // The top pair is 98/99: 98 is in front, so 99 paints first.
    // The bottom pair is 97/96: 96 is in front, so 97 paints first.
    assert(racer_obj_paints_behind(99, 98));
    assert(!racer_obj_paints_behind(98, 99));
    assert(racer_obj_paints_behind(97, 96));
    assert(!racer_obj_paints_behind(96, 97));
    assert(!racer_obj_paints_behind(98, 98));

    // The HD replacement must obey the original HDMA $A5/$5A handoff
    // after logical scanline 111 even with 1x-4x presentation density.
    for (int scale = 1; scale <= 4; ++scale) {
        const auto visible = [scale](RacerViewport viewport, int y) {
            return racer_split_viewport_contains_row(viewport, y, scale);
        };
        assert(!visible(RacerViewport::Top, -1));
        assert(!visible(RacerViewport::Bottom, -1));
        assert(visible(RacerViewport::Top, 0));
        assert(visible(RacerViewport::Top, 112 * scale - 1));
        assert(!visible(RacerViewport::Top, 112 * scale));
        assert(!visible(RacerViewport::Bottom, 112 * scale - 1));
        assert(visible(RacerViewport::Bottom, 112 * scale));
        assert(visible(RacerViewport::Bottom, 224 * scale - 1));
        assert(!visible(RacerViewport::Bottom, 224 * scale));
        assert(!visible(RacerViewport::Top, 224 * scale));
    }
    assert(!racer_split_viewport_contains_row(RacerViewport::Top, 0, 0));
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
    // Native host dimensions are resolved *before* begin_sim_frame. Any
    // output geometry unsupported by the HD presenter must retain stock
    // OBJ pixels rather than capturing/removing sprites that cannot be
    // recomposited after the raster scan.
    static_assert(racer_hd_can_capture_frame_geometry(256, 224));
    static_assert(!racer_hd_can_capture_frame_geometry(342, 224));
    static_assert(!racer_hd_can_capture_frame_geometry(256, 240));
    assert(racer_hd_can_capture_frame_geometry(256, 224));
    for (int width : {0, 1, 255, 257, 320, 342, 512}) {
        assert(!racer_hd_can_capture_frame_geometry(width, 224));
    }
    for (int height : {0, 1, 112, 223, 225, 239, 240}) {
        assert(!racer_hd_can_capture_frame_geometry(256, height));
    }

    // A selective P1-only high-resolution compositor may remove contiguous
    // slots 97/98, preserving stock P2 in 96/99. Fail closed whenever the
    // lower viewport's P2-front OAM raster might overlap P1 HD pixels.
    RacerOamPlacement p1_top{};
    RacerOamPlacement p1_bottom{};
    RacerOamPlacement p2_top{};
    RacerOamPlacement p2_bottom{};
    p1_top.slot = 98;
    p1_bottom.slot = 97;
    p2_top.slot = 99;
    p2_bottom.slot = 96;
    for (auto* placement : {&p1_top, &p1_bottom, &p2_top, &p2_bottom}) {
        placement->large = true;
        placement->width_pixels = 64;
        placement->height_pixels = 64;
        placement->x_signed = 100;
        placement->y_raw_8bit = 150;
        placement->attr = 0x60;  // same OBJ priority level
    }
    // Authentic top P1 large object at Y=40 has no inactive small copy
    // in the bottom 112..223 scanlines.
    p1_top.y_raw_8bit = 40;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_bottom.x_signed = 164;
    assert(racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_bottom.x_signed = 163;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_bottom.x_signed = 100;
    p2_bottom.y_raw_8bit = 230;
    assert(racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_bottom.y_raw_8bit = 120;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p1_bottom.y_raw_8bit = 250;
    // At $83 size mode the normally inactive 16px bottom slot wraps
    // visibly into the top viewport: extraction would erase it.
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p1_bottom.y_raw_8bit = 150;
    p1_top.y_raw_8bit = 120;  // inactive top slot visible at bottom
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p1_top.y_raw_8bit = 150; // top slot small copy is still in lower viewport
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p1_top.y_raw_8bit = 40;
    p2_top.attr = 0x50;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_top.attr = 0x60;
    p1_bottom.slot = 98;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p1_bottom.slot = 97;
    p2_bottom.height_pixels = 0;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    p2_bottom.height_pixels = 64;
    p2_bottom.x_signed = -200;
    assert(racer_p1_only_no_stock_p2_occlusion(
        p1_top, p1_bottom, p2_top, p2_bottom
    ));
    return 0;
}
