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
    bool racer_shortcuts_available = true;
    bool read_only_records_open = false;
    std::string_view records_status{};
    std::string_view records_recent{};
    // Native source-only Records may switch to existing paired 2P history.
    // All older root callers default to the historical 1P RUNS view.
    bool read_only_records_two_player = false;
    bool read_only_records_pages_available = false;
    // Optional product-owned, controller-confirmed 2P profile selection;
    // hosts without this feature retain the exact same default root UI.
    bool two_seat_join_open = false;
    std::string_view join_p1_name{};
    std::string_view join_p2_name{};
    std::string_view join_p1_stock{};
    std::string_view join_p2_stock{};
    bool join_p1_confirmed = false;
    bool join_p2_confirmed = false;
    // Extra optional read-only detail, supplied by native Records only.
    // Older Modern presenters retain their exact two-line layout by default.
    std::string_view records_detail{};
    bool unbound_two_player_warning_open = false;
    // Optional native first-time preset, committed for NEXT guest process.
    bool first_racer_shortcut_available = false;
    bool first_racer_open = false;
    bool first_racer_created = false;
    bool first_racer_failed = false;
    std::string_view first_racer_preset_name{};
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
        view.first_racer_created
            ? "RESTART FOR NEW RACER"
            : view.first_racer_shortcut_available
                ? "X CREATE STOCK RACER"
                : view.racer_shortcuts_available
                    ? "X/F2 RACERS   F1 HELP"
                    : "RACER SETUP NOT YET LINKED",
        palette.cursor_blue, scale);
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
    if (view.read_only_records_open) {
        // One existing Modern root painter, with the archive as a modal
        // read-only child. The established host's non-native UI is unchanged.
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 9 * scale,
                        view.read_only_records_two_player
                            ? "TWO PLAYER RECORDS" : "STORED RUNS",
                        palette.title_yellow, scale);
        // The 216-logical-pixel modal has a 9-pixel text inset on each
        // side. At 8 logical pixels/glyph, 24 cells fit safely. A previous
        // 22-cell limit silently truncated the last run's hundredths digit.
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 38 * scale,
                        fit_modern_overlay_text(
                            view.records_status, modern_overlay_text_cells(
                                panel_w - 30)).c_str(),
                        0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 60 * scale,
                        fit_modern_overlay_text(
                            view.records_recent, modern_overlay_text_cells(
                                panel_w - 30)).c_str(),
                        palette.secondary_grey, scale);
        if (!view.records_detail.empty() &&
            view.read_only_records_two_player) {
            paint.draw_text(pixels, stride, surface_height,
                            bx + 9 * scale, by + 82 * scale,
                            fit_modern_overlay_text(
                                view.records_detail,
                                modern_overlay_text_cells(panel_w - 30)).c_str(),
                            0xFFFFFFFFu, scale);
        }
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale,
                        by + (view.read_only_records_two_player &&
                              !view.records_detail.empty() ? 99 : 85) * scale,
                        "READ ONLY - NO REPLAY", palette.cursor_blue, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 114 * scale,
                        !view.read_only_records_pages_available
                            ? "A/ENTER  B/ESC BACK"
                            : view.read_only_records_two_player
                                ? "UP/DOWN 1P  B BACK"
                                : "UP/DOWN 2P  B BACK",
                        0xFFFFFFFFu, scale);
    }
    if (view.two_seat_join_open) {
        // The same shared Modern root painter owns the 2P child modal.
        // Baldosa only supplies catalog-backed names and pad acknowledgments.
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 9 * scale,
                        "TWO PLAYER PROFILES", palette.title_yellow, scale);
        const auto cells = modern_overlay_text_cells(panel_w - 34);
        const std::string p1 = fit_modern_overlay_text(
            std::string("P1 ") + std::string(view.join_p1_name) +
            (view.join_p1_confirmed ? " READY" : " ACTIVE"), cells);
        const std::string p2 = fit_modern_overlay_text(
            std::string("P2 ") + std::string(view.join_p2_name) +
            (view.join_p2_confirmed ? " READY" : " CHOOSE"), cells);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 37 * scale, p1.c_str(),
                        view.join_p1_confirmed
                            ? palette.title_yellow : 0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 63 * scale, p2.c_str(),
                        view.join_p2_confirmed
                            ? palette.title_yellow : 0xFFFFFFFFu, scale);
        const std::string stock = fit_modern_overlay_text(
            std::string("STOCK: ") + std::string(view.join_p1_stock) +
            " / " + std::string(view.join_p2_stock), cells);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 83 * scale,
                        stock.c_str(), palette.cursor_blue, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 98 * scale,
                        "P1 A READY / B BACK", palette.secondary_grey, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 113 * scale,
                        "P2 DPAD+A / B CLEAR", palette.secondary_grey, scale);
    }
    if (view.first_racer_open) {
        // Shared Modern painter; Baldosa supplies the existing stock preset,
        // never a speculative rider name or in-process SRAM hot-swap.
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 10 * scale,
                        "FIRST STOCK RACER", palette.title_yellow, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 40 * scale,
                        fit_modern_overlay_text(
                            std::string("PRESET: ") +
                            std::string(view.first_racer_preset_name),
                            modern_overlay_text_cells(panel_w - 33)).c_str(),
                        0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 67 * scale,
                        view.first_racer_created
                            ? "SAVED FOR NEXT LAUNCH"
                            : view.first_racer_failed
                                ? "NOT SAVED - CHECK DATA"
                                : "NEW SEPARATE PROGRESS",
                        palette.secondary_grey, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 94 * scale,
                        view.first_racer_created
                            ? "QUIT AND RESTART GAME"
                            : "UP/DOWN CHOOSE PRESET",
                        palette.cursor_blue, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 116 * scale,
                        view.first_racer_created
                            ? "B BACK / QUIT"
                            : "A CREATE  B CANCEL",
                        0xFFFFFFFFu, scale);
    }
    if (view.unbound_two_player_warning_open) {
        // An unbound stock session is playable, but not attributable.
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 12 * scale,
                        "UNRECORDED TWO PLAYER", palette.title_yellow, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 43 * scale,
                        "NEED TWO NAMED RACERS", 0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 63 * scale,
                        "NO MATCH HISTORY SAVED", palette.secondary_grey, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 92 * scale,
                        "PLAY STOCK 2P ANYWAY?", 0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 115 * scale,
                        "P1 A YES  B BACK", palette.cursor_blue, scale);
    }
    return true;
}

}  // namespace ur::product
