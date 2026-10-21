#pragma once

// THE shared five-destination Modern root artwork, extracted from the
// existing product host. Both the original shipping executor and Baldosa
// consume this same renderer. It does not own routes, controllers, profiles,
// persistence, SDL, guest frames or any second frontend state machine.

#include "modern_root_menu.hpp"
#include "modern_stock_menu_palette.hpp"
#include "modern_menu_visual_grammar.hpp"
#include "modern_overlay_composition.hpp"
#include "modern_overlay_text_fit.hpp"

#include <array>
#include <cstddef>
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

// One native OPTIONS row as text only. The presenter never learns what a row
// does; the host supplies only controls it genuinely applies.
struct ModernRootOptionRowView {
    std::string_view label{};
    std::string_view value{};
    bool adjustable = false;
};
inline constexpr std::size_t kModernRootOptionRows = 5;

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
    bool second_racer_shortcut_available = false;
    bool second_racer_created = false;
    bool first_racer_is_second = false;
    bool first_racer_open = false;
    bool first_racer_created = false;
    bool first_racer_failed = false;
    std::string_view first_racer_preset_name{};
    // Only the pinned native host exposes the existing named-P1 selector.
    // Other Modern host callers leave these false and retain their layout.
    bool existing_profile_switch_available = false;
    bool existing_profile_switch_saved = false;
    bool first_racer_is_switch = false;
    // Native source-qualified Practice shares the existing root artwork.
    // The old host leaves these false; this cannot advertise unavailable
    // stock tours or change another frontend's established controls.
    bool practice_picker_open = false;
    bool practice_launch_pending = false;
    std::string_view practice_course_name{};
    std::string_view practice_tour_name{};
    std::string_view practice_kind_label{};
    // One short player-facing sentence (a refused route, a stale racer...)
    // shown in place of the racer hint until the next player action.
    std::string_view root_notice{};
    // Courses the original game's own tour menu currently offers this rider.
    // 0 keeps the historical single-course wording for older callers.
    std::uint8_t practice_courses_open = 0;
    // Native OPTIONS (the pinned Baldosa host only). Older callers leave
    // options_open false and keep their exact layout.
    bool options_open = false;
    bool options_controls_help = false;
    std::size_t options_selected = 0;
    std::size_t options_row_count = 0;
    std::array<ModernRootOptionRowView, kModernRootOptionRows> options_rows{};
    std::string_view options_status{};
    std::string_view options_notice{};
};

// The shared native OPTIONS modal (root and in-race pause). Origin and scale
// follow the root panel geometry: a 216x137 logical modal at (12, 43).
inline void render_modern_options_modal(
    const ModernRootOverlayPainter& paint,
    std::uint32_t* pixels, int stride, int surface_height,
    int scale, int panel_w, int x, int y,
    const ModernRootOverlayView& view) {
    const auto& palette = kModernStockMenuPalette;
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        const auto cells = modern_overlay_text_cells(panel_w - 30);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 8 * scale,
                        view.options_controls_help ? "MENU CONTROLS"
                                                   : "OPTIONS",
                        palette.title_yellow, scale);
        if (view.options_controls_help) {
            constexpr const char* kHelp[] = {
                "UP/DOWN  MOVE",
                "A/ENTER  SELECT",
                "B/ESC    BACK",
                "LEFT/RIGHT  CHANGE",
                "X  RACER SETUP",
            };
            for (std::size_t i = 0; i < 5; ++i)
                paint.draw_text(pixels, stride, surface_height,
                                bx + 9 * scale,
                                by + (26 + static_cast<int>(i) * 14) * scale,
                                fit_modern_overlay_text(kHelp[i], cells).c_str(),
                                0xFFFFFFFFu, scale);
            paint.draw_text(pixels, stride, surface_height,
                            bx + 9 * scale, by + 114 * scale,
                            "A/B BACK", palette.cursor_blue, scale);
        } else {
            const std::size_t rows = view.options_row_count <
                kModernRootOptionRows ? view.options_row_count
                                      : kModernRootOptionRows;
            for (std::size_t i = 0; i < rows; ++i) {
                const bool selected = i == view.options_selected;
                const int row_y = by + (24 + static_cast<int>(i) * 14) * scale;
                if (selected)
                    modern_menu_paint_focus_band(
                        paint, pixels, stride, surface_height,
                        bx + 4 * scale, row_y - 3 * scale,
                        bw - 8 * scale, 13 * scale, scale);
                const auto& row = view.options_rows[i];
                std::string value(row.value);
                if (row.adjustable && selected) value = "< " + value + " >";
                std::string label(row.label);
                if (label.size() < 9) label.append(9 - label.size(), ' ');
                paint.draw_text(pixels, stride, surface_height,
                                bx + 9 * scale, row_y,
                                fit_modern_overlay_text(
                                    std::string(selected ? ">" : " ") +
                                    label + value, cells).c_str(),
                                selected ? palette.title_yellow : 0xFFFFFFFFu,
                                scale);
            }
            const bool has_status = !view.options_status.empty();
            const bool has_notice = !view.options_notice.empty();
            if (has_status || has_notice)
                paint.draw_text(pixels, stride, surface_height,
                                bx + 9 * scale, by + 98 * scale,
                                fit_modern_overlay_text(
                                    has_status ? view.options_status
                                               : view.options_notice,
                                    cells).c_str(),
                                has_status ? palette.title_yellow
                                           : palette.secondary_grey, scale);
            paint.draw_text(pixels, stride, surface_height,
                            bx + 9 * scale, by + 114 * scale,
                            fit_modern_overlay_text(
                                "L/R CHANGE  B BACK", cells).c_str(),
                            palette.cursor_blue, scale);
        }
}

inline bool render_modern_root_overlay(
    const ModernRootOverlayPainter& paint,
    std::uint32_t* pixels, int stride, int surface_height,
    int scale, int panel_w, HostOverlayRect rect,
    const ModernRootOverlayView& view,
    const ModernMenuSourcePixels* source_heading = nullptr) {
    // No partial drawing on an invalid layout or absent host primitives.
    // Reject the entire host draw before a pixel is changed if the logical
    // Modern menu does not fit its assigned framebuffer rectangle. The root
    // uses copy down to y+193 and a 204px stock shell, including the 16:9
    // secondary preview. Previously a narrow/short rectangle could pass the
    // outer bounds test and forward out-of-panel writes to painter callbacks.
    if (!paint.valid() || !pixels || stride <= 0 || surface_height <= 0 ||
        stride > 16384 || surface_height > 16384 ||
        scale < 1 || scale > 4 || panel_w <= 40 || panel_w > 512 ||
        rect.width <= 0 || rect.height <= 0 ||
        rect.x < 0 || rect.y < 0 || rect.x > stride ||
        rect.y > surface_height || rect.width > stride - rect.x ||
        rect.height > surface_height - rect.y ||
        panel_w * scale > rect.width ||
        204 * scale > rect.height)
        return false;

    const int x = rect.x;
    const int y = rect.y;
    const auto& palette = kModernStockMenuPalette;
    const bool wide = panel_w >= 320;
    const int list_w = wide ? 168 : panel_w - 16;
    modern_menu_paint_checker_backdrop(
        paint, pixels, stride, surface_height,
        x, y, rect.width, rect.height, scale);
    paint.fill_rect(pixels, stride, surface_height,
        x, y, rect.width, 27 * scale, palette.header_band);
    paint.stroke_rect(pixels, stride, surface_height,
        x, y, rect.width, rect.height, palette.frame_grey);
    const char* title = view.europe ? "UNIRALLY" : "UNIRACERS";
    // Optional caller-owned, previously verified ORIGINAL BG2 raster.
    // No ROM bytes, PNG decoding, asset I/O or rights decisions live here.
    // The stock image already includes its yellow fill, black outline and
    // source grey shadow, so painting the synthetic host shadow over it would
    // double-ink the heading. The old host fallback remains the default.
    const bool drew_source_heading = source_heading &&
        modern_menu_paint_source_text(
            *source_heading, ModernMenuSourceSheet::Heading,
            pixels, static_cast<std::size_t>(stride) *
                    static_cast<std::size_t>(surface_height),
            stride, surface_height,
            x + 9 * scale, y + 6 * scale, title, scale);
    if (!drew_source_heading)
        modern_menu_paint_shadowed_heading(
            paint, pixels, stride, surface_height,
            x + 9 * scale, y + 6 * scale, title, 2, scale);
    // A stock anonymous rider is a state, not a long player name. Keep
    // that status readable at the real 240-logical-pixel 4:3 fallback.
    const std::string_view racer_name =
        view.racer_name == "STOCK RACER - NO PROFILE"
            ? std::string_view("NO PROFILE") : view.racer_name;
    std::string identity = std::string("RACER: ") + std::string(racer_name);
    const auto identity_cells = modern_overlay_text_cells(panel_w);
    if (identity.size() > identity_cells) {
        // Never silently present a clipped prefix as a complete racer name.
        // Keep the fixed identity label and mark unusually long names.
        if (identity_cells >= 3) {
            identity.resize(identity_cells - 3);
            identity += "...";
        } else {
            identity = fit_modern_overlay_text(identity, identity_cells);
        }
    }
    paint.draw_text(pixels, stride, surface_height,
        x + 8 * scale, y + 36 * scale,
        identity.c_str(), kModernMenuCheckerLegibleGrey, scale);
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
            modern_menu_paint_focus_band(
                paint, pixels, stride, surface_height,
                x + 5 * scale, row_y - 3 * scale,
                list_w * scale, 17 * scale, scale);
        }
        const std::string label = std::string(selected ? "> " : "  ") +
            modern_root_destination_label(destination);
        paint.draw_text(pixels, stride, surface_height,
            x + 9 * scale, row_y,
            label.c_str(),
            !available ? kModernMenuCheckerLegibleGrey :
            selected ? palette.title_yellow : 0xFFFFFFFFu, scale);
        if (!available)
            paint.draw_text(pixels, stride, surface_height,
                x + (list_w - 43) * scale, row_y,
                "SOON", kModernMenuCheckerLegibleGrey, scale);
    }
    constexpr const char* kDetails[] = {
        "TOUR AND CONTINUE",
        "CHOOSE A COURSE",
        "LOCAL TWO PLAYER",
        "RUNS AND BEST TIMES",
        "DISPLAY AND CONTROLS"
    };
    // The right-side preview at a 320px panel offers just 13 ASCII cells.
    // Intentional two-line copy preserves each route's full meaning. This is
    // a layout vocabulary, not a route or guest-state change.
    constexpr const char* kWideDetails[][2] = {
        {"TOUR AND", "CONTINUE"},
        {"CHOOSE A", "COURSE"},
        {"LOCAL", "TWO PLAYER"},
        {"RUNS AND", "BEST TIMES"},
        {"DISPLAY AND", "CONTROLS"}
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
        const bool preview_available =
            (view.available_destinations & (1u << selected_index)) != 0;
        const char* const* preview = preview_available
            ? kWideDetails[selected_index] : nullptr;
        const auto preview_cells = modern_overlay_text_cells(panel_w - 193);
        // These two words/lines are deliberately short, not truncated
        // source status. Never print an incomplete route as if complete.
        for (int line = 0; line < 2; ++line) {
            const char* copy = preview_available
                ? preview[line]
                : (line == 0 ? "NOT YET" : "AVAILABLE");
            paint.draw_text(pixels, stride, surface_height,
                x + 193 * scale, y + (85 + 12 * line) * scale,
                fit_modern_overlay_text(copy, preview_cells).c_str(),
                0xFFFFFFFFu, scale);
        }
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
    const std::string racer_hint = std::string(
        !view.root_notice.empty()
            ? view.root_notice
            : view.existing_profile_switch_saved
            ? "RESTART TO USE NEW P1"
            : view.first_racer_created || view.second_racer_created
            ? "RESTART FOR NEW RACER"
            : view.first_racer_shortcut_available
                ? "X CREATE STOCK RACER"
                : view.second_racer_shortcut_available
                    ? "X ADD SECOND RACER"
                    : view.existing_profile_switch_available
                    ? "X SWITCH ACTIVE P1"
                    : view.racer_shortcuts_available
                    ? "X/F2 RACERS   F1 HELP"
                    : ""); // No nonexistent button or internal engineering status.
    // Empty means this host has no available setup shortcut. The selected
    // racer's identity is already displayed above, and navigation help is
    // already at y+181; do not paint a fabricated/duplicated footer.
    if (!racer_hint.empty())
        paint.draw_text(pixels, stride, surface_height,
            x + 8 * scale, y + 193 * scale,
            fit_modern_overlay_text(racer_hint, modern_overlay_text_cells(panel_w))
                .c_str(),
            !view.root_notice.empty() ? palette.title_yellow
                                      : palette.cursor_blue, scale);
    if (view.practice_picker_open || view.practice_launch_pending) {
        const int bx = x + 12 * scale, by = y + 43 * scale;
        const int bw = (panel_w - 24) * scale, bh = 137 * scale;
        paint.fill_rect(pixels, stride, surface_height,
                        bx, by, bw, bh, palette.background);
        paint.stroke_rect(pixels, stride, surface_height,
                          bx, by, bw, bh, palette.title_yellow);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 10 * scale,
                        "QUICK PRACTICE", palette.title_yellow, scale);
        const auto cells = modern_overlay_text_cells(panel_w - 30);
        const std::string name = fit_modern_overlay_text(
            view.practice_launch_pending ? "ENTERING ORIGINAL COURSE"
                                         : std::string(view.practice_course_name),
            cells);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 37 * scale,
                        name.c_str(), 0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 62 * scale,
                        view.practice_launch_pending
                            ? "WAIT FOR SOURCE GO"
                            : fit_modern_overlay_text(
                                  std::string(view.practice_tour_name) + " - " +
                                      std::string(view.practice_kind_label),
                                  cells).c_str(),
                        palette.secondary_grey, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 89 * scale,
                        view.practice_courses_open >= 40
                            ? (std::to_string(view.practice_courses_open) +
                               " COURSES OPEN").c_str()
                            : view.practice_courses_open > 1
                            // Stock unlocks more tours as medals are earned.
                            ? (std::to_string(view.practice_courses_open) +
                               " OPEN - MORE FROM MEDALS").c_str()
                            : "1 VERIFIED COURSE", palette.cursor_blue, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 115 * scale,
                        view.practice_launch_pending
                            ? "B CANCEL"
                            : view.practice_courses_open > 1
                                ? "A START L/R TOUR B BACK"
                                : "A START  B BACK",
                        0xFFFFFFFFu, scale);
    }
    if (view.options_open)
        render_modern_options_modal(paint, pixels, stride, surface_height,
                                    scale, panel_w, x, y, view);
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
                        view.first_racer_is_switch
                            ? "SWITCH ACTIVE P1"
                            : view.first_racer_is_second
                            ? "SECOND STOCK RACER" : "FIRST STOCK RACER",
                        palette.title_yellow, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 40 * scale,
                        fit_modern_overlay_text(
                            std::string(view.first_racer_is_switch
                                ? "NEXT P1: " : "PRESET: ") +
                            std::string(view.first_racer_preset_name),
                            modern_overlay_text_cells(panel_w - 33)).c_str(),
                        0xFFFFFFFFu, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 67 * scale,
                        view.first_racer_created
                            ? "SAVED FOR NEXT LAUNCH"
                            : view.first_racer_failed
                                ? "NOT SAVED - CHECK DATA"
                                : view.first_racer_is_switch
                                    ? "EXISTING PROFILE ONLY"
                                    : "NEW SEPARATE PROGRESS",
                        palette.secondary_grey, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 94 * scale,
                        view.first_racer_created
                            ? "QUIT AND RESTART GAME"
                            : view.first_racer_is_switch
                                ? "NO LIVE RACER CHANGE"
                                : "UP/DOWN CHOOSE PRESET",
                        palette.cursor_blue, scale);
        paint.draw_text(pixels, stride, surface_height,
                        bx + 9 * scale, by + 116 * scale,
                        view.first_racer_created
                            ? "B BACK / QUIT"
                            : view.first_racer_is_switch
                                ? "A SWITCH  B CANCEL"
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
