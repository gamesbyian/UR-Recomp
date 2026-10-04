#pragma once

#include <cstdint>

namespace ur::product {

enum class HostGraphicsRepresentation : std::uint8_t {
    Original = 0,
    Remastered = 1,
};

enum class HostSceneComposition : std::uint8_t {
    FixedCenter = 0,
    WorldExpand = 1,
};

struct HostRational {
    int numerator = 1;
    int denominator = 1;

    constexpr bool operator==(const HostRational& other) const noexcept {
        return numerator == other.numerator &&
               denominator == other.denominator;
    }
};

struct HostOutputCompositionPlan {
    int source_width = 256;
    int source_height = 224;
    int canvas_width = 256;
    int canvas_height = 224;
    HostRational source_pixel_aspect{1, 1};
    HostRational horizontal_fit{1, 1};
    bool center_source = false;
    bool expose_added_world = false;

    constexpr bool operator==(const HostOutputCompositionPlan& other) const noexcept {
        return source_width == other.source_width &&
               source_height == other.source_height &&
               canvas_width == other.canvas_width &&
               canvas_height == other.canvas_height &&
               source_pixel_aspect == other.source_pixel_aspect &&
               horizontal_fit == other.horizontal_fit &&
               center_source == other.center_source &&
               expose_added_world == other.expose_added_world;
    }
};

/* Product-side composition contract for the accepted 16:9 view.
 *
 * Original presentation preserves the 7:6 Authentic PAR. Evidence-backed
 * world-expand scenes expose the accepted 342x224 logical viewport, while
 * fixed scenes retain the full 256x224 authored raster centered inside the
 * same 342x224 composition canvas. The 342-wide discrete viewport is 57:32
 * after PAR, so widened Original presentation applies 512/513 horizontal fit
 * at final output.
 *
 * Remastered presentation is square-pixel host composition. It uses the same
 * scene widening decision but does not inherit SNES PAR or its 512/513 fit.
 *
 * This function is deliberately pure: scene recognition belongs to the title
 * host, and authoritative simulation/camera/activation state is out of scope.
 */
HostOutputCompositionPlan resolve_16x9_output_composition(
    HostGraphicsRepresentation representation,
    HostSceneComposition scene) noexcept;

}  // namespace ur::product
