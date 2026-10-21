#pragma once

// Presentation-only adapter for externally supplied, source-verified menu
// rasters. The image bytes are NOT in UR-Recomp and are never bundled here.
// See tools/extract_menu_visual_language.py: original PPU-local font/cursor
// atlases and BG1 layer, including their SHA-bound manifests.
//
// Every pixel in these sheets is either transparent or fully opaque. This
// nearest-neighbour integer painter uses the host's AARRGGBB framebuffer.
// No PNG loader, I/O, SDL, ROM state, gameplay timing or layout is owned here.

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace ur::product {

enum class ModernMenuSourceSheet : std::uint8_t {
    Heading,   // original yellow 40-slot 16x16 glyph sheet, 640x16
    Detail,    // original grey 45-slot 8x16 glyph sheet, 360x16
    Cursor,    // original arrow+shadow, 16 poses of 39x39, 624x39
    Backdrop,  // source-original BG1 only, 256x224
};

struct ModernMenuSourcePixels {
    const std::uint32_t* pixels = nullptr; // host AARRGGBB, not PNG RGBA bytes
    std::size_t count = 0; // number of allocated uint32_t pixels
    int stride = 0; // elements per row, >= width
    int width = 0;
    int height = 0;
};

constexpr bool modern_menu_source_dimensions(ModernMenuSourceSheet kind,
                                              int width, int height) noexcept {
    switch (kind) {
    case ModernMenuSourceSheet::Heading: return width == 640 && height == 16;
    case ModernMenuSourceSheet::Detail:  return width == 360 && height == 16;
    case ModernMenuSourceSheet::Cursor:  return width == 624 && height == 39;
    case ModernMenuSourceSheet::Backdrop:return width == 256 && height == 224;
    }
    return false;
}

constexpr bool modern_menu_source_buffer(const ModernMenuSourcePixels& atlas,
                                         int width, int height) noexcept {
    return atlas.pixels && atlas.width == width && atlas.height == height &&
           atlas.stride >= atlas.width && atlas.stride <= 4096 &&
           atlas.count >= static_cast<std::size_t>(atlas.stride) *
                          static_cast<std::size_t>(atlas.height);
}

// The original small-letter O is a pixel-exact duplicate of numeral 0.
// The first-party exporter constructs that alias. A correctly dimensioned
// but contradictory caller sheet must not misrepresent that source rule.
inline bool modern_menu_source_detail_zero_alias(
    const ModernMenuSourcePixels& atlas) noexcept {
    if (!modern_menu_source_buffer(atlas, 360, 16)) return false;
    for (int y = 0; y < 16; ++y)
        for (int x = 0; x < 8; ++x) {
            const auto row = static_cast<std::size_t>(y) * atlas.stride;
            if (atlas.pixels[row + x] != atlas.pixels[row + 35 * 8 + x])
                return false;
        }
    return true;
}

// Source PNG decompression yields straight RGBA *bytes*. Do not cast that
// memory to uint32_t*: the framebuffer ABI is AARRGGBB words and host byte
// order differs. This narrow packer works after a separately verified PNG
// decode and source/asset hash check, not as a PNG/manifest parser.
// No writes occur if a buffer is undersized or source alpha is invalid.
inline bool modern_menu_pack_source_rgba(
    ModernMenuSourceSheet sheet,
    const std::uint8_t* rgba, std::size_t rgba_byte_count,
    std::uint32_t* out_argb, std::size_t out_pixel_count,
    int width, int height) noexcept {
    if (!modern_menu_source_dimensions(sheet, width, height) ||
        !rgba || !out_argb || width <= 0 || height <= 0)
        return false;
    const std::size_t count = static_cast<std::size_t>(width) *
                              static_cast<std::size_t>(height);
    if (rgba_byte_count < count * 4 || out_pixel_count < count)
        return false;
    for (std::size_t i = 0; i < count; ++i) {
        const auto a = rgba[i * 4 + 3];
        if (a != 0 && a != 255) return false;
    }
    for (std::size_t i = 0; i < count; ++i) {
        const auto a = rgba[i * 4 + 3];
        out_argb[i] = a == 0 ? 0u :
            (0xFF000000u |
             (static_cast<std::uint32_t>(rgba[i * 4 + 0]) << 16) |
             (static_cast<std::uint32_t>(rgba[i * 4 + 1]) << 8) |
              static_cast<std::uint32_t>(rgba[i * 4 + 2]));
    }
    return true;
}

constexpr int modern_menu_heading_slot(char c) noexcept {
    if (c >= '0' && c <= '9') return c - '0';
    if (c == 'O') return 0; // the original title font draws letter O as zero
    if (c >= 'A' && c <= 'N') return 10 + c - 'A';
    if (c >= 'P' && c <= 'Z') return 24 + c - 'P';
    if (c == ' ') return -2; // transparent 16px word pitch
    return -1;
}

constexpr int modern_menu_detail_slot(char c) noexcept {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'N') return 10 + c - 'A';
    if (c >= 'P' && c <= 'Z') return 24 + c - 'P';
    // Position 35 is O, explicitly duplicated from the numeral zero by
    // the first-party small-atlas exporter. Do not accidentally index
    // punctuation as 'O' or treat these slots as ordinary ASCII offsets.
    if (c == 'O') return 35;
    switch (c) {
    case '%': return 36;
    case '\'': return 37;
    case '(': return 38;
    case '+': return 39;
    case '-': return 40;
    case '.': return 41;
    case ':': return 42;
    case ')': return 43; // original H-flipped '(' image, exporter handles flip
    case ' ': return 44;
    }
    return -1; // source font has no lowercase or other punctuation
}

inline bool modern_menu_paint_source_cell(
    const ModernMenuSourcePixels& atlas, ModernMenuSourceSheet sheet,
    std::uint32_t* destination, std::size_t destination_count,
    int stride, int height, int left, int top, int cell, int scale) noexcept {
    if (!modern_menu_source_dimensions(sheet, atlas.width, atlas.height) ||
        !modern_menu_source_buffer(atlas, atlas.width, atlas.height) ||
        !destination || stride <= 0 || height <= 0 || scale < 1 || scale > 4 ||
        stride > 16384 || height > 16384 ||
        destination_count < static_cast<std::size_t>(stride) *
                            static_cast<std::size_t>(height) ||
        left < 0 || top < 0 ||
        (sheet == ModernMenuSourceSheet::Detail &&
         !modern_menu_source_detail_zero_alias(atlas))) return false;

    const int cw = sheet == ModernMenuSourceSheet::Heading ? 16 :
                   sheet == ModernMenuSourceSheet::Detail ? 8 :
                   sheet == ModernMenuSourceSheet::Cursor ? 39 : 256;
    const int ch = sheet == ModernMenuSourceSheet::Backdrop ? 224 :
                   sheet == ModernMenuSourceSheet::Cursor ? 39 : 16;
    const int slots = atlas.width / cw;
    if (cell < 0 || cell >= slots ||
        static_cast<std::int64_t>(left) + cw * scale > stride ||
        static_cast<std::int64_t>(top) + ch * scale > height)
        return false; // no partial glyph/raster writes
    // First pass makes malformed or blank source pixels an atomic refusal,
    // never an apparently accepted sprite that paints no selected state.
    bool has_ink = false;
    for (int y = 0; y < ch; ++y)
        for (int x = 0; x < cw; ++x) {
            const auto alpha = atlas.pixels[
                static_cast<std::size_t>(y) * atlas.stride +
                static_cast<std::size_t>(cell * cw + x)] >> 24;
            if (alpha != 0 && alpha != 255) return false;
            if (alpha == 255) has_ink = true;
        }
    // Slot 44 in the original detail sheet is a transparent *space*,
    // never a drawable glyph. Do not accept invented pixels merely because
    // the caller supplied an otherwise correctly sized bitmap.
    if (sheet == ModernMenuSourceSheet::Detail && cell == 44)
        { if (has_ink) return false; }
    else if (!has_ink) return false;
    for (int y = 0; y < ch; ++y) {
        for (int x = 0; x < cw; ++x) {
            const std::uint32_t pixel =
                atlas.pixels[static_cast<std::size_t>(y) * atlas.stride +
                             static_cast<std::size_t>(cell * cw + x)];
            if ((pixel >> 24) == 0) continue;
            for (int yy = 0; yy < scale; ++yy)
                for (int xx = 0; xx < scale; ++xx)
                    destination[static_cast<std::size_t>(top + y * scale + yy)
                                    * stride + left + x * scale + xx] = pixel;
        }
    }
    return true;
}

// All text is preflighted before changing a pixel. Unsupported glyphs,
// clipping and bad sizes fail as an atomic transaction, without truncating
// player-visible records or inventing unavailable source characters.
inline bool modern_menu_paint_source_text(
    const ModernMenuSourcePixels& atlas, ModernMenuSourceSheet sheet,
    std::uint32_t* destination, std::size_t destination_count,
    int stride, int height, int left, int top,
    std::string_view value, int scale, int heading_word_gap_px = 16) noexcept {
    if (sheet != ModernMenuSourceSheet::Heading &&
        sheet != ModernMenuSourceSheet::Detail) return false;
    const int cw = sheet == ModernMenuSourceSheet::Heading ? 16 : 8;
    if (!modern_menu_source_dimensions(sheet, atlas.width, atlas.height) ||
        !modern_menu_source_buffer(atlas, atlas.width, atlas.height) ||
        !destination || stride <= 0 || height <= 0 ||
        stride > 16384 || height > 16384 ||
        destination_count < static_cast<std::size_t>(stride) *
                            static_cast<std::size_t>(height) ||
        left < 0 || top < 0 || scale < 1 || scale > 4 ||
        value.empty() || value.size() > 256 ||
        (sheet == ModernMenuSourceSheet::Heading &&
         heading_word_gap_px != 8 && heading_word_gap_px != 16) ||
        static_cast<std::int64_t>(top) + 16 * scale > height ||
        (sheet == ModernMenuSourceSheet::Detail &&
         !modern_menu_source_detail_zero_alias(atlas)))
        return false;
    // Stock BG2 has both 8px (rider title) and 16px (main/options)
    // word gaps despite the fixed 16px heading glyph width. Preflight the
    // entire string against the selected source-measured pitch.
    std::int64_t text_width = 0;
    for (char c : value) {
        const int index = sheet == ModernMenuSourceSheet::Heading
            ? modern_menu_heading_slot(c) : modern_menu_detail_slot(c);
        if (index == -1) return false;
        text_width += sheet == ModernMenuSourceSheet::Heading && c == ' '
            ? heading_word_gap_px : cw;
    }
    if (static_cast<std::int64_t>(left) + text_width * scale > stride)
        return false;
    // Validate all referenced alpha up front to avoid partial rendering in
    // case a non-source atlas with unsupported translucent pixels sneaks in.
    for (char c : value) {
        const int index = sheet == ModernMenuSourceSheet::Heading
            ? modern_menu_heading_slot(c) : modern_menu_detail_slot(c);
        if (index == -2) continue;
        bool has_ink = false;
        for (int yy = 0; yy < 16; ++yy)
            for (int xx = 0; xx < cw; ++xx) {
                const auto pixel = atlas.pixels[
                    static_cast<std::size_t>(yy) * atlas.stride +
                    static_cast<std::size_t>(index * cw + xx)];
                const auto alpha = pixel >> 24;
                if (alpha != 0 && alpha != 255) return false;
                if (alpha == 255) has_ink = true;
            }
        if (sheet == ModernMenuSourceSheet::Detail && c == ' ')
            { if (has_ink) return false; }
        else if (!has_ink) return false;
    }
    int pen_x = left;
    for (char c : value) {
        const int index = sheet == ModernMenuSourceSheet::Heading
            ? modern_menu_heading_slot(c) : modern_menu_detail_slot(c);
        if (index != -2 &&
            !modern_menu_paint_source_cell(
                atlas, sheet, destination, destination_count,
                stride, height, pen_x, top, index, scale)) return false;
        pen_x += (sheet == ModernMenuSourceSheet::Heading && c == ' '
            ? heading_word_gap_px : cw) * scale;
    }
    return true;
}

} // namespace ur::product
