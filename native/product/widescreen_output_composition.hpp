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
    int logical_view_width = 256;
    int logical_view_height = 224;
    HostRational display_pixel_aspect{1, 1};
    HostRational target_output_aspect{16, 9};
    HostRational horizontal_fit{1, 1};
    bool center_logical_view = false;
    bool expose_added_world = false;

    constexpr bool operator==(const HostOutputCompositionPlan& other) const noexcept {
        return logical_view_width == other.logical_view_width &&
               logical_view_height == other.logical_view_height &&
               display_pixel_aspect == other.display_pixel_aspect &&
               target_output_aspect == other.target_output_aspect &&
               horizontal_fit == other.horizontal_fit &&
               center_logical_view == other.center_logical_view &&
               expose_added_world == other.expose_added_world;
    }
};

/* Product-side composition contract for the accepted 16:9 view.
 *
 * The logical view remains title space, not the final output framebuffer.
 * Evidence-backed world-expand scenes expose 342x224; fixed scenes retain the
 * complete 256x224 authored image and are centered by the host inside a 16:9
 * output surface.
 *
 * Original presentation preserves Authentic 7:6 PAR. The discrete 342-wide
 * view is 57:32 after PAR, so widened Original presentation applies 512/513
 * horizontal fit at final output. Remastered presentation is square-pixel
 * host composition and therefore does not inherit either SNES PAR or that
 * quantization correction.
 *
 * This function is deliberately pure: scene recognition belongs to the title
 * host, output resolution belongs to the presenter, and authoritative
 * simulation/camera/activation state is out of scope.
 */
HostOutputCompositionPlan resolve_16x9_output_composition(
    HostGraphicsRepresentation representation,
    HostSceneComposition scene) noexcept;

}  // namespace ur::product
