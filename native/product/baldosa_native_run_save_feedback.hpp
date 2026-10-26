#pragma once

// Host-only status strip on the already-settled native 1P stock result.
// It describes the canonical Records append acknowledgement, never guest
// medals or gameplay completion. Draws into an existing copied host raster.
#include "modern_root_overlay_presenter.hpp"

#include <cstdint>

namespace ur::product {

enum class BaldosaNativeRunSaveFeedback : std::uint8_t {
    None = 0,
    Pending = 1,
    Saved = 2,
    NotSaved = 3,
};

inline const char* baldosa_native_run_save_label(
    BaldosaNativeRunSaveFeedback feedback) noexcept {
    switch (feedback) {
    case BaldosaNativeRunSaveFeedback::Pending:
        return "RECORD SAVE PENDING";
    case BaldosaNativeRunSaveFeedback::Saved:
        return "RECORD SAVED";
    case BaldosaNativeRunSaveFeedback::NotSaved:
        return "RECORD NOT SAVED";
    case BaldosaNativeRunSaveFeedback::None:
        return nullptr;
    }
    return nullptr;
}

inline bool render_baldosa_native_run_save_feedback(
    const ModernRootOverlayPainter& paint,
    std::uint32_t* pixels, int stride, int height,
    BaldosaNativeRunSaveFeedback feedback, int source_width = 256) {
    const char* label = baldosa_native_run_save_label(feedback);
    if (!label || !paint.valid() || !pixels ||
        (source_width != 256 && source_width != 342) ||
        stride < source_width || height < 224) return false;
    const auto& pal = kModernStockMenuPalette;
    constexpr int y = 193, width = 192, band_height = 21;
    const int x = (source_width - width) / 2;
    paint.fill_rect(pixels, stride, height, x, y,
                    width, band_height, pal.background);
    paint.stroke_rect(pixels, stride, height, x, y,
                      width, band_height,
                      feedback == BaldosaNativeRunSaveFeedback::NotSaved
                          ? pal.secondary_grey : pal.title_yellow);
    paint.draw_text(pixels, stride, height, x + 13, y + 6, label,
                    feedback == BaldosaNativeRunSaveFeedback::Saved
                        ? pal.title_yellow : 0xFFFFFFFFu, 1);
    return true;
}

} // namespace ur::product
