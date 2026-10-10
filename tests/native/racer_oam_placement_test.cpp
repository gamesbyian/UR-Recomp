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
    // An accepted OAM placement is not evidence the Original PPU emitted
    // that rider. Regression: guest frame 1220 has top OBJ pixels but no
    // bottom OBJ pixels; host art must not invent the absent lower racer.
    {
        std::array<std::uint8_t, 256u * 224u * 4u> isolated{};
        RacerOamPlacement top{
            98, 104, 104, 40, 0, 0, false, false, true, 64, 64
        };
        RacerOamPlacement bottom{
            97, 104, 104, 153, 0, 0, false, false, true, 64, 64
        };
        const auto mark = [&](int x, int y) {
            const std::uint32_t argb = 0xFF102030u;
            std::memcpy(
                isolated.data() + (static_cast<std::size_t>(y) * 256u + x) * 4u,
                &argb, sizeof(argb)
            );
        };
        const auto source_count = [&](const RacerOamPlacement& p, RacerViewport view) {
            return racer_stock_obj_pixels_in_footprint(
                isolated.data(), isolated.size(), p, view
            );
        };
        assert(source_count(top, RacerViewport::Top) == 0);
        assert(source_count(bottom, RacerViewport::Bottom) == 0);
        mark(104, 40);
        mark(167, 103);
        mark(104, 111);  // Outside top OAM's 64-row tile.
        mark(10, 10);
        // The isolated OBJ plane includes both racers. An unrelated source
        // pixel elsewhere in the same viewport must not authorize HD pixels
        // inside a second, disjoint 64x64 OAM footprint.
        RacerOamPlacement other_top{
            99, 10, 10, 10, 0x88, 0, false, false, true, 64, 64
        };
        assert(source_count(top, RacerViewport::Top) == 2);
        assert(source_count(other_top, RacerViewport::Top) == 1);
        assert(source_count(bottom, RacerViewport::Bottom) == 0);
        // Clear the second rider while leaving the first one's top OBJ
        // source intact. A viewport-level any-OBJ test would falsely pass.
        std::array<std::uint8_t, 256u * 224u * 4u> single_source{};
        const std::uint32_t stock = 0xFF102030u;
        std::memcpy(
            single_source.data() + (40u * 256u + 104u) * 4u,
            &stock, sizeof(stock)
        );
        const auto count_single = [&](const RacerOamPlacement& p) {
            return racer_stock_obj_pixels_in_footprint(
                single_source.data(), single_source.size(), p,
                RacerViewport::Top
            );
        };
        assert(count_single(top) == 1);
        assert(count_single(other_top) == 0);
        other_top.x_signed = -12;
        other_top.x_raw_9bit = 500;
        assert(count_single(other_top) == 0);
        other_top.x_signed = 10;
        other_top.x_raw_9bit = 10;
        mark(130, 180);
        assert(source_count(bottom, RacerViewport::Bottom) == 1);
        top.y_raw_8bit = 110;
        assert(source_count(top, RacerViewport::Top) == 1);
        assert(source_count(top, RacerViewport::Bottom) == 0);
        top.y_raw_8bit = 250;
        mark(104, 0);
        // Both logical rows 0 and 40 are reachable after 256-line wrap.
        assert(source_count(top, RacerViewport::Top) == 2);
        assert(source_count(top, RacerViewport::Bottom) == 0);
        top.large = false;
        assert(source_count(top, RacerViewport::Top) == 0);
        top.large = true;
        assert(racer_stock_obj_pixels_in_footprint(
            nullptr, isolated.size(), top, RacerViewport::Top
        ) == 0);
        assert(racer_stock_obj_pixels_in_footprint(
            isolated.data(), 5, top, RacerViewport::Top
        ) == 0);
    }

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
    RacerOamPlacement partial_p1_top{};
    RacerOamPlacement partial_p1_bottom{};
    RacerOamPlacement partial_p2_top{};
    RacerOamPlacement partial_p2_bottom{};
    partial_p1_top.slot = 98;
    partial_p1_bottom.slot = 97;
    partial_p2_top.slot = 99;
    partial_p2_bottom.slot = 96;
    for (auto* placement : {&partial_p1_top, &partial_p1_bottom, &partial_p2_top, &partial_p2_bottom}) {
        placement->large = true;
        placement->width_pixels = 64;
        placement->height_pixels = 64;
        placement->x_signed = 100;
        placement->y_raw_8bit = 150;
        placement->attr = 0x60;  // same OBJ priority level
    }
    // Authentic top P1 large object at Y=40 has no inactive small copy
    // in the bottom 112..223 scanlines.
    partial_p1_top.y_raw_8bit = 40;
    partial_p1_top.tile = 0x00;
    partial_p1_bottom.tile = 0x08;
    partial_p2_top.tile = 0x80;
    partial_p2_bottom.tile = 0x88;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.x_signed = 164;
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.x_signed = 163;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.x_signed = 100;
    partial_p2_bottom.y_raw_8bit = 230;
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.y_raw_8bit = 120;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.y_raw_8bit = 250;
    // At top split high OAM $A5, inactive bottom slot97 has X-high=1.
    // LOW_X=100 -> small alias X=-156: its wrapped Y is visible,
    // but its full 16px width is offscreen, so no stock pixel is erased.
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.x_signed = 240;  // small alias X=-16, right edge 0
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.x_signed = 241;  // small alias X=-15, one visible pixel
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.x_signed = -16;  // malformed active 64px X high bit
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.x_signed = 100;
    partial_p1_bottom.y_raw_8bit = 150;

    // The inverse split high OAM $5A sets top slot98 X-high=1 below
    // scanline112. A Y-visible inactive top copy is safe if its X is
    // offscreen; only LOW_X >=241 can expose an actual source pixel.
    partial_p2_bottom.x_signed = 164;  // keep lower P1/P2 separate
    partial_p1_top.y_raw_8bit = 120;
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_top.x_signed = 241;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_top.x_signed = 240;
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_top.x_signed = 100;
    partial_p1_top.y_raw_8bit = 40;
    partial_p2_top.attr = 0x50;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_top.attr = 0x60;
    partial_p1_bottom.slot = 98;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p1_bottom.slot = 97;
    partial_p2_bottom.height_pixels = 0;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.height_pixels = 64;
    partial_p2_bottom.tile = 0x00;  // unknown P2 graphics family
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_bottom.tile = 0x88;
    partial_p2_top.large = false;
    assert(!racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    partial_p2_top.large = true;
    partial_p2_bottom.x_signed = -200;
    assert(racer_p1_only_no_stock_p2_occlusion(
        partial_p1_top, partial_p1_bottom, partial_p2_top, partial_p2_bottom
    ));
    // Full-pair capture must not erase the inactive small split copies.
    // The real 2P slots are top 98/99 and bottom 97/96. At low X=240,
    // the 16px inactive alias occupies [-16,0) and is invisible; at X=241
    // it exposes one column if its 8-bit Y reaches the opposite viewport.
    RacerOamPlacement full_p1_top = *p1_top;
    RacerOamPlacement full_p2_top = *p2_top;
    RacerOamPlacement full_p1_bottom = *p1_bottom;
    RacerOamPlacement full_p2_bottom = *p2_bottom;
    const auto pair_safe = [&]() {
        return racer_hd_full_pair_preserves_split_objs(
            full_p1_top, full_p2_top, full_p1_bottom, full_p2_bottom,
            0x83, 0x00
        );
    };
    assert(pair_safe());
    full_p1_bottom.x_signed = 240;
    full_p1_bottom.y_raw_8bit = 250;
    assert(pair_safe());
    full_p1_bottom.x_signed = 241;
    assert(!pair_safe());  // Y=250 wraps to top scanlines 0..9.
    full_p1_bottom.x_signed = 240;
    full_p2_bottom.x_signed = 241;
    assert(pair_safe());   // Y=153 never reaches the top half.
    full_p2_bottom.y_raw_8bit = 255;
    assert(!pair_safe());
    full_p2_bottom.x_signed = 104;
    full_p2_bottom.y_raw_8bit = 153;
    full_p1_top.x_signed = 241;
    full_p1_top.y_raw_8bit = 110;
    assert(!pair_safe());  // Inactive top slot98 crosses scanline 112.
    full_p1_top.y_raw_8bit = 40;
    assert(pair_safe());
    full_p2_top.x_signed = 241;
    full_p2_top.y_raw_8bit = 112;
    assert(!pair_safe());
    full_p2_top.x_signed = 104;
    full_p2_top.y_raw_8bit = 40;
    assert(pair_safe());
    full_p2_bottom.attr ^= 0x10;
    assert(!pair_safe());  // Cross-racer OBJ priority not reconstructed.
    full_p2_bottom.attr ^= 0x10;
    assert(!racer_hd_full_pair_preserves_split_objs(
        full_p1_top, full_p2_top, full_p1_bottom, full_p2_bottom,
        0x83, 0x80));  // Priority rotation changes the slot ordering.
    assert(!racer_hd_full_pair_preserves_split_objs(
        full_p1_top, full_p2_top, full_p1_bottom, full_p2_bottom,
        0x00, 0x00));  // Other OBJ size/alias modes unproven.
    // Correct shape and priority do not authorize destructive OBJ removal
    // when a slot's tile bank no longer belongs to its racer. Keep the
    // inactive small OAM aliases and original graphical object unchanged.
    full_p1_top.tile = 0x09;
    assert(!pair_safe());
    full_p1_top.tile = 0x08;
    assert(pair_safe());
    full_p1_bottom.tile = 0x80;
    assert(!pair_safe());
    full_p1_bottom.tile = 0x00;
    assert(pair_safe());
    full_p2_top.tile = 0x00;
    assert(!pair_safe());
    full_p2_top.tile = 0x80;
    assert(pair_safe());
    full_p2_bottom.tile = 0x89;
    assert(!pair_safe());
    full_p2_bottom.tile = 0x88;
    assert(pair_safe());
    full_p1_top.tile = 0x00;
    full_p2_top.tile = 0x88;
    assert(pair_safe());

    full_p1_top.x_signed = -1;
    assert(!pair_safe());  // Malformed active-large split placement.

    // The independent Baldosa 342-wide four-slot PPU source-plane witness
    // demonstrates that an opaque shared rectangle does not prove each
    // rider actually contributed final pixels. Suppress full-pair authored
    // HD before any destructive OBJ capture while two active rectangles
    // can overlap on visible scanlines in the *same* split viewport.
    RacerOamPlacement a = *p1_top;
    RacerOamPlacement b = *p2_top;
    a.x_signed = 104;
    b.x_signed = 105;
    a.y_raw_8bit = 40;
    b.y_raw_8bit = 44;
    assert(racer_active_source_footprints_overlap(
        a, b, RacerViewport::Top));
    assert(!racer_active_source_footprints_overlap(
        a, b, RacerViewport::Bottom));
    b.x_signed = 168;  // Touching pixel-edge is not overlap.
    assert(!racer_active_source_footprints_overlap(
        a, b, RacerViewport::Top));
    b.x_signed = 167;  // One shared screen column.
    assert(racer_active_source_footprints_overlap(
        a, b, RacerViewport::Top));
    b.x_signed = 105;
    a.y_raw_8bit = 250;  // Hardware modulo-256 wraps 250..255 to 0..57.
    b.y_raw_8bit = 1;
    assert(racer_active_source_footprints_overlap(
        a, b, RacerViewport::Top));
    b.y_raw_8bit = 100;
    assert(!racer_active_source_footprints_overlap(
        a, b, RacerViewport::Top));
    a.y_raw_8bit = 112;
    b.y_raw_8bit = 175;
    assert(racer_active_source_footprints_overlap(
        a, b, RacerViewport::Bottom));  // Exact one-row intersection.
    b.y_raw_8bit = 176;
    assert(!racer_active_source_footprints_overlap(
        a, b, RacerViewport::Bottom));
    a.large = false;
    assert(racer_active_source_footprints_overlap(
        a, b, RacerViewport::Bottom));  // Unsupported shape fails closed.
    return 0;
}
