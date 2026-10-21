// Native source-atlas framebuffer tests: no ROMs, copied assets or SDL.
// Source texture sizes and glyph encodings come from the canonical PPU
// extractor, not a replacement art pack.
#include "native/product/modern_menu_source_atlas.hpp"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>

using namespace ur::product;

static_assert(modern_menu_source_dimensions(ModernMenuSourceSheet::Heading,640,16));
static_assert(modern_menu_source_dimensions(ModernMenuSourceSheet::Detail,360,16));
static_assert(modern_menu_source_dimensions(ModernMenuSourceSheet::Cursor,624,39));
static_assert(modern_menu_source_dimensions(ModernMenuSourceSheet::Backdrop,256,224));
static_assert(!modern_menu_source_dimensions(ModernMenuSourceSheet::Cursor,640,39));
static_assert(modern_menu_heading_slot('O') == modern_menu_heading_slot('0'));
static_assert(modern_menu_heading_slot('A') == 10);
static_assert(modern_menu_heading_slot('N') == 23);
static_assert(modern_menu_heading_slot('P') == 24);
static_assert(modern_menu_heading_slot('Z') == 34);
static_assert(modern_menu_heading_slot(' ') == -2);
static_assert(modern_menu_heading_slot('_') == -1);
static_assert(modern_menu_detail_slot('O') == 35);
static_assert(modern_menu_detail_slot('0') == 0);
static_assert(modern_menu_detail_slot('%') == 36);
static_assert(modern_menu_detail_slot(static_cast<char>(39)) == 37);
static_assert(modern_menu_detail_slot('(') == 38);
static_assert(modern_menu_detail_slot('+') == 39);
static_assert(modern_menu_detail_slot('-') == 40);
static_assert(modern_menu_detail_slot('.') == 41);
static_assert(modern_menu_detail_slot(':') == 42);
static_assert(modern_menu_detail_slot(')') == 43);
static_assert(modern_menu_detail_slot(' ') == 44);
static_assert(modern_menu_detail_slot('/') == -1);

int main() {
    std::vector<std::uint32_t> big(640 * 16, 0u);
    std::vector<std::uint32_t> small(360 * 16, 0u);
    std::vector<std::uint32_t> cursor(624 * 39, 0u);
    std::vector<std::uint32_t> backdrop(256 * 224, 0u);
    std::vector<std::uint32_t> screen(342 * 224, 0xFF101010u);
    const ModernMenuSourcePixels big_view{big.data(),big.size(),640,640,16};
    const ModernMenuSourcePixels small_view{small.data(),small.size(),360,360,16};
    const ModernMenuSourcePixels cursor_view{cursor.data(),cursor.size(),624,624,39};
    const ModernMenuSourcePixels backdrop_view{
        backdrop.data(),backdrop.size(),256,256,224};
    // RGBA bytes from PNG storage must be unpacked to host AARRGGBB
    // words. Test fully transparent, colored and invalid-alpha pixels.
    std::vector<std::uint8_t> source_rgba(640 * 16 * 4, 0u);
    std::vector<std::uint32_t> converted(640 * 16, 0xAABBCCDDu);
    source_rgba[0] = 17; source_rgba[1] = 34;
    source_rgba[2] = 51; source_rgba[3] = 255;
    source_rgba[4] = 255; source_rgba[5] = 99;
    source_rgba[6] = 77; source_rgba[7] = 0;
    assert(modern_menu_pack_source_rgba(
        ModernMenuSourceSheet::Heading,source_rgba.data(),source_rgba.size(),
        converted.data(),converted.size(),640,16));
    assert(converted[0] == 0xFF112233u);
    assert(converted[1] == 0u);
    assert(converted[2] == 0u);
    converted.assign(converted.size(),0xAABBCCDDu);
    source_rgba[11] = 128; // invalid alpha at later pixel
    assert(!modern_menu_pack_source_rgba(
        ModernMenuSourceSheet::Heading,source_rgba.data(),source_rgba.size(),
        converted.data(),converted.size(),640,16));
    assert(converted.front() == 0xAABBCCDDu);
    assert(converted.back() == 0xAABBCCDDu);
    source_rgba[11] = 0;
    assert(!modern_menu_pack_source_rgba(
        ModernMenuSourceSheet::Heading,source_rgba.data(),source_rgba.size()-1,
        converted.data(),converted.size(),640,16));
    assert(!modern_menu_pack_source_rgba(
        ModernMenuSourceSheet::Heading,source_rgba.data(),source_rgba.size(),
        converted.data(),converted.size()-1,640,16));
    assert(!modern_menu_pack_source_rgba(
        ModernMenuSourceSheet::Cursor,source_rgba.data(),source_rgba.size(),
        converted.data(),converted.size(),640,16));
    assert(converted.front() == 0xAABBCCDDu);

    assert(modern_menu_source_buffer(big_view,640,16));
    assert(!modern_menu_source_buffer(big_view,640,32));
    assert(!modern_menu_source_buffer(
        ModernMenuSourcePixels{big.data(),big.size()-1,640,640,16},640,16));

    // First rendered original big-font "O" must use the ZERO cell (slot 0).
    big[0] = 0xFFF8F800u;
    big[16 * 24] = 0xFFC8C800u; // P
    assert(modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,2,2,"O P",1));
    assert(screen[2*342+2] == 0xFFF8F800u);
    assert(screen[2*342+2+16] == 0xFF101010u); // blank space
    assert(screen[2*342+2+32] == 0xFFC8C800u);
    // Authentic source rider heading "PICK YOUR UNI" uses 8px
    // intra-word blanks, unlike the main/options 16px word pitch.
    assert(modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,8,70,"O P",1,8));
    assert(screen[70*342+8] == 0xFFF8F800u);
    assert(screen[70*342+8+24] == 0xFFC8C800u);
    assert(screen[70*342+8+32] == 0xFF101010u);
    const auto before_invalid_gap = screen;
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,8,90,"O P",1,12));
    assert(screen == before_invalid_gap);

    // Real detail/Records original font includes source closing-paren image.
    small[35*8] = 0xFF989898u; // O's duplicate cell
    small[43*8] = 0xFF686868u; // ) cell from extractor's H-flipped (
    assert(modern_menu_paint_source_text(
        small_view,ModernMenuSourceSheet::Detail,
        screen.data(),screen.size(),342,224,2,24,"O)",1));
    assert(screen[24*342+2] == 0xFF989898u);
    assert(screen[24*342+10] == 0xFF686868u);
    // The original detail-font slot 44 is a deliberately blank space.
    // A caller cannot transform that into a phantom source glyph. Check
    // both individual-cell and full-word paths, with atomic framebuffer
    // rejection even if an earlier letter in the word was valid.
    const auto before_detail_space = screen;
    assert(modern_menu_paint_source_text(
        small_view,ModernMenuSourceSheet::Detail,
        screen.data(),screen.size(),342,224,2,52,"O ",1));
    assert(screen[52*342+2] == 0xFF989898u);
    assert(screen[52*342+10] == 0xFF101010u);
    small[44*8] = 0xFF989898u; // forged ink in actual space slot
    const auto before_corrupt_detail = screen;
    assert(!modern_menu_paint_source_cell(
        small_view,ModernMenuSourceSheet::Detail,
        screen.data(),screen.size(),342,224,2,65,44,1));
    assert(!modern_menu_paint_source_text(
        small_view,ModernMenuSourceSheet::Detail,
        screen.data(),screen.size(),342,224,2,70,"O ",1));
    assert(screen == before_corrupt_detail);
    small[44*8] = 0u;
    (void)before_detail_space; // preserved non-space pixels intentionally

    // At 4x scale an opaque pixel becomes an exact 4x4 block.
    cursor[15*39] = 0xFFA0D0F8u;
    assert(modern_menu_paint_source_cell(
        cursor_view,ModernMenuSourceSheet::Cursor,
        screen.data(),screen.size(),342,224,48,40,15,4));
    for (int y=40;y<44;++y)
        for(int x=48;x<52;++x)
            assert(screen[y*342+x] == 0xFFA0D0F8u);
    assert(screen[40*342+52] == 0xFF101010u);

    // Source BG1 is a separate 256x224 layer with transparent pixels.
    std::vector<std::uint32_t> full_frame(256 * 224,0xFF123456u);
    backdrop[0] = 0xFFF8F800u;
    assert(modern_menu_paint_source_cell(
        backdrop_view,ModernMenuSourceSheet::Backdrop,
        full_frame.data(),full_frame.size(),256,224,0,0,0,1));
    assert(full_frame[0] == 0xFFF8F800u);
    assert(full_frame[1] == 0xFF123456u);

    // Strong no-partial-output guarantees for invalid glyph, clipping and
    // alpha. These are actually tested on the image buffer, not call counts.
    const auto before = screen;
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,0,0,"UNIRACERS!",1));
    assert(screen == before);
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,340,0,"P",1));
    assert(screen == before);
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,0,0,"",1));
    assert(screen == before);
    // A blank art sheet is never silently accepted as an invisible cursor,
    // and a blank *later* glyph cannot partially paint the earlier O.
    big[16*24] = 0u;
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,0,100,"O P",1));
    assert(screen == before);
    big[16*24] = 0xFFC8C800u;
    assert(!modern_menu_paint_source_cell(
        cursor_view,ModernMenuSourceSheet::Cursor,
        screen.data(),screen.size(),342,224,0,0,14,1));
    assert(screen == before);
    // The original 8px small-font SPACE sheet is intentionally empty.
    assert(modern_menu_paint_source_text(
        small_view,ModernMenuSourceSheet::Detail,
        screen.data(),screen.size(),342,224,0,100," ",1));
    assert(screen == before);
    big[0] = 0x80808080u;
    assert(!modern_menu_paint_source_text(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,0,0,"0",1));
    assert(!modern_menu_paint_source_cell(
        big_view,ModernMenuSourceSheet::Heading,
        screen.data(),screen.size(),342,224,0,0,0,1));
    assert(screen == before);
    big[0] = 0xFFF8F800u;
    assert(!modern_menu_paint_source_cell(
        cursor_view,ModernMenuSourceSheet::Cursor,
        screen.data(),screen.size(),342,224,0,0,16,1)); // frame 16 OOB
    assert(!modern_menu_paint_source_cell(
        cursor_view,ModernMenuSourceSheet::Cursor,
        screen.data(),screen.size()-1,342,224,0,0,0,1));
    assert(screen == before);
    std::puts("PASS: original menu source raster cells, glyph encoding and exact native pixels");
    return 0;
}
