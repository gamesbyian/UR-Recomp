#pragma once

// THE shared five-destination Modern root artwork, extracted from the
// existing product host. Both the original shipping executor and Baldosa
// consume this same renderer. It does not own routes, controllers, profiles,
// persistence, SDL, guest frames or any second frontend state machine.

#include "modern_root_menu.hpp"
#include "modern_stock_menu_palette.hpp"
#include "modern_overlay_composition.hpp"
#include "modern_overlay_text_fit.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace ur::product {

// Narrow host painter ABI. The existing SNES overlay drawing functions are
// the first consumer. A native Baldosa host can bind the same primitives
// without giving this presenter any execution/presentation authority.
struct ModernRootOverlayPainter {
    void (*fill_rect)(std::uint32_t*, int, int, int, int, int, int,
                      std::uint32_t) = nullptr;
    void (*stroke_rect)(std::uint32_t*, int, int, int, int, int, int,
                        std::uint32_t) = nullptr;
    void (*draw_text)(std::uint32_t*, int, int, int, int, const char*,
                      std::uint32_t, int) = nullptr;

    constexpr bool valid() const noexcept {
        return fill_rect && stroke_rect && draw_text;
    }
};

struct ModernRootOverlayView {
    ModernRootMenu menu{};
    bool europe = false;
    std::string_view racer_name = "CREATE A RACER WITH X";
    bool tour_continue_available = false;
    bool quit_confirm = false;
    // Existing Modern host retains all routes by default; a native guest
    // may narrow advertised capabilities without replacing its menu model.
    std::uint8_t available_destinations = 0x1fu;
};

inline bool render_modern_root_overlay(
    const ModernRootOverlayPainter& paint,
    std::uint32_t* pixels, int stride, int surface_height,
    int scale, int panel_w, HostOverlayRect rect,
    const ModernRootOverlayView& view) {
    // No partial drawing on an invalid layout or absent host primitives.
    if (!paint.valid() || !pixels || stride <= 0 || surface_height <= 0 ||
        scale <= 0 || panel_w <= 40 || rect.width <= 0 || rect.height <= 0 ||
        rect.x < 0 || rect.y < 0 || rect.x > stride ||
        rect.y > surface_height || rect.width > stride - rect.x ||
        rect.height > surface_height - rect.y)
        return false;

    const int x = rect.x;
    const int y = rect.y;
    const auto& palette = kModernStockMenuPalette;
    const bool wide = panel_w >= 320;
    const int list_w = wide ? 168 : panel_w - 16;
    paint.fill_rect(pixels, stride, surface_height,
        x, y, rect.width, rect.height, palette.background);
    paint.fill_rect(pixels, stride, surface_height,
        x, y, rect.width, 27 * scale, palette.header_band);
    paint.stroke_rect(pixels, stride, surface_height,
        x, y, rect.width, rect.height, palette.frame_grey);
    const char* title = view.europe ? "UNIRALLY" : "UNIRACERS";
    paint.draw_text(pixels, stride, surface_height,
        x + 10 * scale, y + 7 * scale, title,
        palette.shadow_black, 2 * scale);
    paint.draw_text(pixels, stride, surface_height,
        x + 9 * scale, y + 6 * scale, title,
        palette.title_yellow, 2 * scale);
    const std::string identity = fit_modern_overlay_text(
        std::string("RACER: ") + std::string(view.racer_name),
        modern_overlay_text_cells(panel_w));
    paint.draw_text(pixels, stride, surface_height,
        x + 8 * scale, y + 36 * scale,
        identity.c_str(), palette.secondary_grey, scale);
    constexpr int kRootFirstRow = 57;
    constexpr int kRootRowStride = 21;
    for (std::size_t i = 0; i < kModernRootDestinationCount; ++i) {
        const auto destination = modern_root_destination_from_index(i);
        const bool selected =
            destination == modern_root_menu_selected(view.menu);
        const bool available = (view.available_destinations & (1u << i)) != 0;
        const int row_y = y + (kRootFirstRow +
            static_cast<int>(i) * kRootRowStride) * scale;
        if (selected) {
            paint.fill_rect(pixels, stride, surface_height,
                x + 5 * scale, row_y - 3 * scale,
                list_w * scale, 17 * scale, palette.cursor_blue);
            paint.stroke_rect(pixels, stride, surface_height,
                x + 5 * scale, row_y - 3 * scale,
                list_w * scale, 17 * scale, palette.frame_grey);
        }
        const std::string label = std::string(selected ? "> " : "  ") +
            modern_root_destination_label(destination);
        paint.draw_text(pixels, stride, surface_height,
            x + 9 * scale, row_y,
            label.c_str(),
            !available ? palette.secondary_grey :
            selected ? palette.shadow_black : 0xFFFFFFFFu, scale);
        if (!available)
            paint.draw_text(pixels, stride, surface_height,
                x + (list_w - 43) * scale, row_y,
                "SOON", palette.secondary_grey, scale);
    }
    constexpr const char* kDetails[] = {
        "TOUR AND CONTINUE",
        "CHOOSE A COURSE",
        "LOCAL TWO PLAYER",
        "RUNS AND BEST TIMES",
        "DISPLAY AND CONTROLS"
    };
    const auto selected_index = modern_root_destination_index(
        modern_root_menu_selected(view.menu));
    if (wide) {
        paint.fill_rect(pixels, stride, surface_height,
            x + 184 * scale, y + 52 * scale,
            (panel_w - 191) * scale, 109 * scale, palette.header_band);
        paint.draw_text(pixels, stride, surface_height,
            x + 193 * scale, y + 64 * scale,
            "SELECTED", palette.title_yellow, scale);
        paint.draw_text(pixels, stride, surface_height,
            x + 193 * scale, y + 85 * scale,
            fit_modern_overlay_text(
                (view.available_destinations & (1u << selected_index))
                    ? kDetails[selected_index] : "NOT YET AVAILABLE",
                modern_overlay_text_cells(panel_w - 193)
            ).c_str(), 0xFFFFFFFFu, scale);
        if (selected_index == 0 && view.tour_continue_available) {
            paint.draw_text(pixels, stride, surface_height,
                x + 193 * scale, y + 111 * scale,
                "CONTINUE READY", palette.cursor_blue, scale);
        }
    } else {
        paint.draw_text(pixels, stride, surface_height,
            x + 8 * scale, y + 165 * scale,
            fit_modern_overlay_text(
                (view.available_destinations & (1u << selected_index))
                    ? kDetails[selected_index] : "NOT YET AVAILABLE",
                modern_overlay_text_cells(panel_w)).c_str(),
            palette.title_yellow, scale);
    }
    paint.draw_text(pixels, stride, surface_height,
        x + 8 * scale, y + 181 * scale,
        fit_modern_overlay_text(
            "A/ENTER SELECT   B/ESC QUIT",
            modern_overlay_text_cells(panel_w)).c_str(),
        0xFFFFFFFFu, scale);
    paint.draw_text(pixels, stride, surface_height,
        x + 8 * scale, y + 193 * scale,
        "X/F2 RACERS   F1 HELP", palette.cursor_blue, scale);
    if (view.quit_confirm) {
        const int qx = x + 12 * scale, qy = y + 65 * scale;
        const int qw = (panel_w - 24) * scale;
        paint.fill_rect(pixels, stride, surface_height,
            qx, qy, qw, 67 * scale, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
            qx, qy, qw, 67 * scale, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
            qx + 8 * scale, qy + 10 * scale,
            "QUIT TO DESKTOP?", palette.title_yellow, scale);
        paint.draw_text(pixels, stride, surface_height,
            qx + 8 * scale, qy + 37 * scale,
            "A/ENTER YES   B/ESC NO", 0xFFFFFFFFu, scale);
    }
    return true;
}

}  // namespace ur::product
