#pragma once

// Baldosa's native Modern destination surfaces.  This is a *view* of the
// already-authoritative ModernRootOverlayView, never a menu controller, save
// store or guest renderer.  Keep it separate from the shared root/title skin:
// those are independently owned visual lanes.
//
// Colours and 16/8-pixel text hierarchy come from the observed stock BG2
// menu family (analysis/generated/menu-visual-language.json).  The present
// host glyph painter is still provisional pending source-font art approval.
#include "modern_root_overlay_presenter.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace ur::product {

struct ModernNativeDestinationCanvas {
    int x = 0;
    int y = 0;
    int w = 0;
    int h = 0;
    int scale = 0;
    bool wide = false;
};

// Position the same destination body within either a narrow 240-logical-pixel
// root or a 320+-logical-pixel widescreen root. The containing root rectangle
// and pixel bounds remain authoritative; never draw beyond them.
inline ModernNativeDestinationCanvas modern_native_destination_canvas(
    int stride, int surface_height, int scale, int panel_w,
    HostOverlayRect root) noexcept {
    if (scale <= 0 || scale > 4 || panel_w < 176 || panel_w > 342 ||
        stride <= 0 ||
        surface_height <= 0 || root.x < 0 || root.y < 0 ||
        root.width <= 0 || root.height <= 0 ||
        root.x > stride || root.width > stride - root.x ||
        root.y > surface_height ||
        root.height > surface_height - root.y ||
        panel_w * scale > root.width ||
        root.height < 204 * scale) return {};
    const int inset = 2 * scale;
    const int width = panel_w * scale - 2 * inset;
    const int height = 154 * scale;
    const int x = root.x + inset;
    const int y = root.y + 50 * scale;
    if (x < root.x || y < root.y ||
        width > root.x + root.width - x ||
        height > root.y + root.height - y) return {};
    return {x, y, width, height, scale, panel_w >= 320};
}

inline bool modern_native_destination_is_open(
    const ModernRootOverlayView& v) noexcept {
    return v.practice_picker_open || v.practice_launch_pending ||
           v.options_open || v.read_only_records_open ||
           v.two_seat_join_open || v.first_racer_open ||
           v.unbound_two_player_warning_open;
}

// Run summaries may have a long course label followed by the *actual*
// recorded time. Preserve the complete trailing time token in compact 4:3
// instead of silently losing its hundredths when the course name grows.
// Other too-long text is explicitly marked truncated with a final dot.
// A stable, source-model-derived screen identifier for integration/capture
// receipts. This exposes ONLY already-visible Modern view states. It never
// reads guest RAM, launches a route, polls controllers or invents a result.
inline const char* modern_native_destination_stage(
    const ModernRootOverlayView& v) noexcept {
    if (v.options_open)
        return v.options_controls_help ? "options-help" : "options";
    if (v.practice_launch_pending) return "practice-entering-stock";
    if (v.practice_picker_open) return "practice-picker";
    if (v.read_only_records_open)
        return v.read_only_records_two_player ? "records-2p" : "records-1p";
    if (v.two_seat_join_open)
        return v.join_p1_confirmed && v.join_p2_confirmed
            ? "multiplayer-both-ready"
            : v.join_p1_confirmed ? "multiplayer-p1-ready"
            : v.join_p2_confirmed ? "multiplayer-p2-ready"
            : "multiplayer-join";
    if (v.first_racer_open) {
        if (v.first_racer_is_switch)
            return v.first_racer_created ? "profile-switch-saved"
                 : v.first_racer_failed ? "profile-switch-refused"
                 : "profile-switch";
        if (v.first_racer_is_second)
            return v.first_racer_created ? "profile-second-saved"
                 : v.first_racer_failed ? "profile-second-refused"
                 : "profile-second";
        return v.first_racer_created ? "profile-first-saved"
             : v.first_racer_failed ? "profile-first-refused"
             : "profile-first";
    }
    if (v.unbound_two_player_warning_open)
        return "multiplayer-unrecorded-warning";
    if (v.quit_confirm) return "quit-confirm";
    if (!v.root_notice.empty()) return "root-notice";
    return "root";
}

// The original menu atlas uses uppercase text. Render source course/tour
// labels in that documented display grammar without changing catalog bytes
// or locale-sensitive process state (ASCII-only cartridge course names).
inline std::string modern_native_display_caps(std::string_view name) {
    std::string shown(name);
    for (char& ch : shown)
        if (ch >= 'a' && ch <= 'z')
            ch = static_cast<char>(ch - ('a' - 'A'));
    return shown;
}

inline std::string modern_native_destination_fit(
    std::string_view value, std::size_t cells,
    bool keep_last_token = false) {
    if (cells == 0) return {};
    if (value.size() <= cells) return std::string(value);
    if (keep_last_token && cells > 4) {
        const auto split = value.find_last_of(' ');
        if (split != std::string_view::npos) {
            const auto last = value.substr(split + 1);
            // Reserve 2 cells for the visible continuation marker.
            if (last.size() + 3 <= cells) {
                const auto first = value.substr(0, cells - last.size() - 2);
                return std::string(first) + ".." + std::string(last);
            }
        }
    }
    if (cells == 1) return ".";
    return std::string(value.substr(0, cells - 1)) + ".";
}

inline void modern_native_destination_line(
    const ModernRootOverlayPainter& p, std::uint32_t* pixels,
    int stride, int surface_height,
    const ModernNativeDestinationCanvas& c,
    int y, std::string_view value, std::uint32_t colour,
    int x = 9, int text_scale = 1, bool keep_last_token = false,
    int right_edge = -1) {
    // This helper is also public to native screen composers. A malformed
    // canvas or text scale must never reach division or an unclipped painter.
    // Validate the complete destination rectangle before drawing any glyph.
    if (!p.draw_text || !pixels || stride <= 0 || surface_height <= 0 ||
        c.scale < 1 || c.scale > 4 ||
        text_scale < 1 || text_scale > 2 ||
        c.x < 0 || c.y < 0 || c.w <= 0 || c.h <= 0 ||
        c.x > stride || c.w > stride - c.x ||
        c.y > surface_height || c.h > surface_height - c.y ||
        x < 0 || y < 0) return;
    // All text is contained within the panel. Never silently crop the right
    // edge of a stock name, saved time, controls legend or options value.
    // A second column may start before the canvas edge. Bound this text
    // to its own cell budget; the shared host painter has no scissor.
    const int canvas_end = c.w / c.scale - 5;
    const int content_end = right_edge >= 0 && right_edge < canvas_end
        ? right_edge : canvas_end;
    const int available = content_end - x;
    if (available < 8 * text_scale || y + 8 * text_scale > c.h / c.scale)
        return;
    const auto fit = modern_native_destination_fit(
        value, static_cast<std::size_t>(
            available / (kModernOverlayCellPixels * text_scale)),
        keep_last_token);
    p.draw_text(pixels, stride, surface_height,
                c.x + x * c.scale, c.y + y * c.scale, fit.c_str(),
                colour, text_scale * c.scale);
}

inline void modern_native_destination_row(
    const ModernRootOverlayPainter& p, std::uint32_t* pixels,
    int stride, int surface_height,
    const ModernNativeDestinationCanvas& c, int y, bool selected,
    std::string_view text, int right_edge = -1) {
    const auto& color = kModernStockMenuPalette;
    if (selected) {
        // Share the root's source-measured blue arrow and dark focus field,
        // rather than a contradictory cyan slab/black selected label.
        // Only presentation changes; the product view still owns selection.
        // Shared source-colour focus is now on main. Keep one canonical
        // painter for the Modern root and all destination selections.
        modern_menu_paint_focus_band(
            p, pixels, stride, surface_height,
            c.x + 5 * c.scale, c.y + (y - 3) * c.scale,
            c.w - 10 * c.scale, 13 * c.scale, c.scale);
    }
    modern_native_destination_line(
        p, pixels, stride, surface_height, c, y,
        std::string(selected ? "> " : "  ") + std::string(text),
        selected ? color.title_yellow : 0xFFFFFFFFu,
        9, 1, false, right_edge);
}

// Compact seat labels must not let a long catalog name push the important
// READY/ACTIVE/CHOOSE status offscreen. The native model retains the *full*
// identity; only this one painter string is shortened, visibly with a dot.
inline std::string modern_native_join_label(
    const ModernNativeDestinationCanvas& c,
    std::string_view seat, std::string_view name,
    std::string_view status) {
    constexpr std::size_t cursor_cells = 2;
    const std::size_t text_cells = c.scale > 0
        ? static_cast<std::size_t>(
            (c.w / c.scale - 9 - 5) / kModernOverlayCellPixels)
        : 0u;
    const std::size_t fixed = cursor_cells + seat.size() +
        2u + 2u + status.size();
    const std::size_t available = text_cells > fixed ? text_cells - fixed : 0u;
    std::string shown(name.substr(0, available));
    if (shown.size() < name.size() && !shown.empty())
        shown.back() = '.';
    return std::string(seat) + "  " + shown + "  " +
        std::string(status);
}

inline bool render_modern_native_destination(
    const ModernRootOverlayPainter& p,
    std::uint32_t* pixels, int stride, int surface_height,
    int scale, int panel_w, HostOverlayRect root,
    const ModernRootOverlayView& v) {
    if (!p.valid() || !pixels || !modern_native_destination_is_open(v))
        return false;
    const auto c = modern_native_destination_canvas(
        stride, surface_height, scale, panel_w, root);
    if (c.scale == 0) return false;

    const auto& col = kModernStockMenuPalette;
    // Modal focus owns the entire body and its controls footer. Mask the
    // underlying root's selection bar, two-column preview, and "B/ESC QUIT"
    // footer before drawing the real child. Merely hiding the old child model
    // leaves blue focus slivers and mutually contradictory shortcuts showing
    // outside a centred dialog on the actual SDL drawable.
    // Keep the shell's outer border and profile/identity glyphs (y+36..43) untouched;
    // this operation is entirely host-owned Modern UI presentation.
    p.fill_rect(pixels, stride, surface_height,
                root.x + scale, root.y + 46 * scale,
                root.width - 2 * scale,
                root.height - 47 * scale, col.background);
    p.fill_rect(pixels, stride, surface_height,
                c.x, c.y, c.w, c.h, col.background);
    p.fill_rect(pixels, stride, surface_height,
                c.x, c.y, c.w, 29 * c.scale, col.header_band);
    p.fill_rect(pixels, stride, surface_height,
                c.x, c.y, c.w, 3 * c.scale, col.title_yellow);
    p.stroke_rect(pixels, stride, surface_height,
                  c.x, c.y, c.w, c.h, col.frame_grey);
    // A double-rendered stock-style title retains the bold yellow/shadow
    // hierarchy of the original without inventing a replacement logo.
    const char* title = v.options_open ? "OPTIONS" :
        (v.practice_picker_open || v.practice_launch_pending) ? "PRACTICE" :
        v.read_only_records_open ? "RECORDS" :
        v.first_racer_open ? "RACERS" :
        v.two_seat_join_open ? "TWO PLAYER" : "MULTIPLAYER";
    modern_native_destination_line(
        p, pixels, stride, surface_height, c, 7,
        title, col.shadow_black, 11, 2);
    modern_native_destination_line(
        p, pixels, stride, surface_height, c, 6,
        title, col.title_yellow, 10, 2);

    // The extra native-wide header width is a quiet, source-colour identity
    // rail. It tells the player which *existing* product surface is active,
    // without placing new actions in the panel or truncating full racer names
    // and saved Records times in the content below. The 4:3 title stays exact.
    if (c.wide) {
        const std::string_view tag = v.options_open
            ? (v.options_controls_help ? "HELP" : "SETTINGS")
            : (v.practice_picker_open || v.practice_launch_pending) ? "COURSES"
            : v.read_only_records_open ? "ARCHIVE"
            : v.first_racer_open ? "PROFILE"
            : v.two_seat_join_open ? "P1 + P2" : "LOCAL 2P";
        const int tag_x = c.w / c.scale - 10 -
            static_cast<int>(tag.size()) * kModernOverlayCellPixels;
        p.fill_rect(pixels, stride, surface_height,
                    c.x + (tag_x - 7) * c.scale, c.y + 9 * c.scale,
                    c.scale, 11 * c.scale, col.frame_grey);
        // The 8px tag sits on a #484848 header band. Stock #989898
        // provides only 3.17:1 there; shared stock-grammar's legible
        // neutral #C8C8C8 provides 5.47:1 without recolouring guest art.
        p.draw_text(pixels, stride, surface_height,
                    c.x + tag_x * c.scale, c.y + 12 * c.scale,
                    tag.data(), 0xFFC8C8C8u, c.scale);
    }

    // Player-facing language deliberately omits implementation terms such
    // as host, guest, route and stock. The underlying source-authoritative
    // course count, save policy and next-boot racer activation are unchanged.
    if (v.options_open) {
        if (v.options_controls_help) {
            static constexpr const char* lines[] = {
                "UP/DOWN  MOVE", "A/ENTER  SELECT", "B/ESC  BACK",
                "LEFT/RIGHT  CHANGE", "B  CLOSE HELP"};
            for (std::size_t i = 0; i < 5; ++i)
                modern_native_destination_line(
                    p, pixels, stride, surface_height, c,
                    36 + static_cast<int>(i) * 16, lines[i],
                    i == 0 ? col.cursor_blue : 0xFFFFFFFFu);
            modern_native_destination_line(
                p, pixels, stride, surface_height, c,
                124, "A/B  BACK", col.cursor_blue);
        } else {
            const std::size_t count =
                v.options_row_count < kModernRootOptionRows
                ? v.options_row_count : kModernRootOptionRows;
            for (std::size_t i = 0; i < count; ++i) {
                const auto& row = v.options_rows[i];
                const bool selected = i == v.options_selected;
                const int row_y = 36 + static_cast<int>(i) * 15;
                if (c.wide) {
                    // Native-wide Options has real fixed columns, not a
                    // padded engineering string. The stock focus still
                    // follows only the selected real product option.
                    modern_native_destination_row(
                        p, pixels, stride, surface_height, c,
                        row_y, selected, row.label, 175);
                    std::string value(row.value);
                    if (selected && row.adjustable)
                        value = "< " + value + " >";
                    modern_native_destination_line(
                        p, pixels, stride, surface_height, c,
                        row_y, value,
                        selected ? col.title_yellow : 0xFFFFFFFFu, 183);
                } else {
                    // Compact 4:3 retains its source-safe single-line
                    // interaction pattern and existing value clipping.
                    std::string label(row.label);
                    if (label.size() < 9) label.append(9 - label.size(), ' ');
                    label += std::string(row.adjustable && selected
                        ? "< " : "");
                    label += row.value;
                    if (row.adjustable && selected) label += " >";
                    modern_native_destination_row(
                        p, pixels, stride, surface_height, c,
                        row_y, selected, label);
                }
            }
            const bool status = !v.options_status.empty();
            const bool notice = !v.options_notice.empty();
            // A successful setting action does not invalidate an earlier
            // settings-load warning. Give each message its own row, including
            // the fifth option's focus band, without hiding the Back legend.
            // Retain existing single-message geometry for other callers.
            if (notice)
                modern_native_destination_line(
                    p, pixels, stride, surface_height, c,
                    status ? 109 : 112, v.options_notice,
                    kModernMenuCheckerLegibleGrey);
            if (status)
                modern_native_destination_line(
                    p, pixels, stride, surface_height, c,
                    notice ? 120 : 112, v.options_status,
                    col.title_yellow);
            const bool has_selection = v.options_selected < count;
            const bool adjustable = has_selection &&
                v.options_rows[v.options_selected].adjustable;
            modern_native_destination_line(
                p, pixels, stride, surface_height, c,
                status && notice ? 138 : 125, !has_selection
                    ? "B BACK" : adjustable
                        ? "L/R CHANGE   B BACK" : "A SELECT   B BACK"
                col.cursor_blue);
        }
    } else if (v.practice_picker_open || v.practice_launch_pending) {
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 38,
            v.practice_launch_pending ? "STARTING PRACTICE"
                                      : modern_native_display_caps(
                                            v.practice_course_name),
            col.title_yellow);
        std::string context =
            modern_native_display_caps(v.practice_tour_name);
        if (!v.practice_kind_label.empty()) {
            if (!context.empty()) context += "  /  ";
            context += modern_native_display_caps(v.practice_kind_label);
        }
        if (c.wide && !v.practice_launch_pending &&
            !v.practice_kind_label.empty()) {
            // The two source-owned course dimensions get independent
            // columns. Keep the stock tour string fully visible when it
            // fits; visually mark only overlong labels as truncated.
            const std::string tour = modern_native_destination_fit(
                "TOUR  " + modern_native_display_caps(v.practice_tour_name),
                20);
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 63,
                tour, 0xFFFFFFFFu);
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 63,
                modern_native_display_caps(v.practice_kind_label),
                0xFFFFFFFFu, 183);
        } else {
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 63,
                v.practice_launch_pending ? "WAIT FOR GO" : context,
                0xFFFFFFFFu);
        }
        const std::string unlocked =
            v.practice_courses_open > 1
            ? std::to_string(v.practice_courses_open) +
                " COURSES UNLOCKED"
            : "1 COURSE UNLOCKED";
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 91,
            v.practice_launch_pending ? "RACE STARTING" : unlocked,
            kModernMenuCheckerLegibleGrey);
        if (!v.practice_launch_pending && v.practice_courses_open > 1)
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 110,
                "UP/DN COURSE   L/R TOUR", kModernMenuCheckerLegibleGrey);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 125,
            v.practice_launch_pending ? "B CANCEL" : "A START   B BACK",
            col.cursor_blue);
    } else if (v.read_only_records_open) {
        modern_native_destination_row(
            p, pixels, stride, surface_height, c, 37,
            !v.read_only_records_two_player, "1P RUNS");
        // A highlighted second row is an actual page of the same existing
        // archive, not a fabricated replay/save action.
        modern_native_destination_row(
            p, pixels, stride, surface_height, c, 51,
            v.read_only_records_two_player, "2P MATCHES");
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 72,
            v.records_status, col.title_yellow);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 88,
            v.records_recent, 0xFFFFFFFFu, 9, 1, true);
        if (v.read_only_records_two_player && !v.records_detail.empty())
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 101,
                v.records_detail, kModernMenuCheckerLegibleGrey, 9, 1, true);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 114,
            "REPLAY UNAVAILABLE", kModernMenuCheckerLegibleGrey);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 125,
            v.read_only_records_pages_available
                ? "UP/DOWN PAGE  B BACK"
                : "B BACK  /  READ ONLY", col.cursor_blue);
    } else if (v.two_seat_join_open) {
        // P1 is fixed to the active loaded profile and may confirm readiness,
        // while P2 alone moves the candidate cursor. Never paint two identical
        // blue focus bands suggesting P1 can browse P2's choices.
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 39,
            "  " + modern_native_join_label(
                c, "P1", v.join_p1_name,
                v.join_p1_confirmed ? "READY" : "ACTIVE"),
            v.join_p1_confirmed ? col.title_yellow : 0xFFFFFFFFu);
        const auto p2 = modern_native_join_label(
            c, "P2", v.join_p2_name,
            v.join_p2_confirmed ? "READY" : "CHOOSE");
        if (v.join_p2_confirmed)
            modern_native_destination_line(
                p, pixels, stride, surface_height, c, 59,
                "  " + p2, col.title_yellow);
        else
            modern_native_destination_row(
                p, pixels, stride, surface_height, c, 59, true, p2);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 84,
            std::string("RACE AS: ") + std::string(v.join_p1_stock) +
            " / " + std::string(v.join_p2_stock), kModernMenuCheckerLegibleGrey);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 108,
            "P1 A READY   B BACK", 0xFFFFFFFFu);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 124,
            "P2 DPAD+A   B CLEAR", col.cursor_blue);
    } else if (v.first_racer_open) {
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 39,
            v.first_racer_is_switch ? "P1 CHANGES ON RESTART" :
            v.first_racer_is_second ? "SECOND RACER" :
                                       "FIRST RACER", kModernMenuCheckerLegibleGrey);
        modern_native_destination_row(
            p, pixels, stride, surface_height, c, 59, true,
            std::string(v.first_racer_is_switch ? "NEXT P1: " : "PRESET: ") +
            std::string(v.first_racer_preset_name));
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 83,
            v.first_racer_created ? "SAVED FOR NEXT LAUNCH" :
            v.first_racer_failed ? "NOT SAVED - CHECK DATA" :
            v.first_racer_is_switch ? "RESTART TO SWITCH RACER" :
                                      "SEPARATE SAVED PROGRESS",
            v.first_racer_failed ? col.title_yellow : 0xFFFFFFFFu);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 105,
            v.first_racer_created ? "QUIT AND RESTART GAME" :
            v.first_racer_is_switch ? "EXISTING PROFILE ONLY" :
                                      "UP/DOWN CHOOSE PRESET", kModernMenuCheckerLegibleGrey);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 124,
            v.first_racer_created ? "B BACK  THEN QUIT" :
            v.first_racer_is_switch ? "A SWITCH   B CANCEL" :
                                      "A CREATE   B CANCEL", col.cursor_blue);
    } else if (v.unbound_two_player_warning_open) {
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 41,
            "TWO NAMED RACERS NEEDED", col.title_yellow);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 63,
            "LOCAL 2P STILL PLAYABLE", 0xFFFFFFFFu);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 85,
            "2P RESULTS NOT SAVED", kModernMenuCheckerLegibleGrey);
        modern_native_destination_line(
            p, pixels, stride, surface_height, c, 124,
            "P1 A ANYWAY   B BACK", col.cursor_blue);
    }
    return true;
}


// The in-race pause Options entry has the same authoritative host settings,
// but its root is centred over the FROZEN guest image rather than the title.
// Compose its frame and identical destination child without drawing the old
// translucent Options modal first. No second options state or input handler.
inline bool render_modern_native_pause_destination(
    const ModernRootOverlayPainter& p,
    std::uint32_t* pixels, int stride,
    int width, int height,
    const ModernRootOverlayView& view) {
    if (!p.valid() || !pixels || !view.options_open ||
        width < 256 || stride < width || height < 224) return false;
    const int scale = width >= 1024 && height >= 896 ? 4 :
        width >= 512 && height >= 448 ? 2 : 1;
    // Paused Options has the same 342-wide Modern composition as the root
    // whenever its actual prepared native framebuffer has room for it. The
    // original 256-wide guest / 4:3 frame stays 240-wide at every scale.
    // This changes presentation geometry only, never the frozen guest image,
    // option store, input owner or resume state.
    // Output-sized buffers (such as 1280x720) are not evidence that the
    // game actually prepared a 342x224 logical native frame. Only the exact
    // source-size family may use the 320px destination composition.
    const int logical_w = width == 342 * scale && height == 224 * scale
        ? 320 : 240;
    constexpr int logical_h = 204;
    const HostOverlayRect root{
        (width - logical_w * scale) / 2,
        (height - logical_h * scale) / 2,
        logical_w * scale, logical_h * scale};
    if (root.x < 0 || root.y < 0 ||
        root.width > width - root.x ||
        root.height > height - root.y) return false;
    const auto& pal = kModernStockMenuPalette;
    p.fill_rect(pixels, stride, height, root.x, root.y,
                root.width, root.height, pal.background);
    p.fill_rect(pixels, stride, height, root.x, root.y,
                root.width, 27 * scale, pal.header_band);
    p.stroke_rect(pixels, stride, height, root.x, root.y,
                  root.width, root.height, pal.frame_grey);
    p.draw_text(pixels, stride, height,
                root.x + 9 * scale, root.y + 6 * scale,
                view.europe ? "UNIRALLY" : "UNIRACERS",
                pal.title_yellow, 2 * scale);
    p.draw_text(pixels, stride, height,
                root.x + 8 * scale, root.y + 36 * scale,
                "GAME PAUSED", kModernMenuCheckerLegibleGrey, scale);
    return render_modern_native_destination(
        p, pixels, stride, height, scale, logical_w, root, view);
}

}  // namespace ur::product
