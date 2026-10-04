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

enum class HostRacePresentationMode : std::uint8_t {
    Unknown = 0,
    OnePlayer = 1,
    TwoPlayer = 2,
    Vs = 3,
};

struct HostWidescreenSceneState {
    HostRacePresentationMode race_mode = HostRacePresentationMode::Unknown;
};

struct HostRational {
    int numerator = 1;
    int denominator = 1;

    constexpr bool operator==(const HostRational& other) const noexcept {
        return numerator == other.numerator &&
               denominator == other.denominator;
    }
};

struct HostOutputViewport {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;

    constexpr bool operator==(const HostOutputViewport& other) const noexcept {
        return x == other.x && y == other.y &&
               width == other.width && height == other.height;
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

/* Resolve the title-owned source rectangle inside the largest target-aspect
 * canvas that fits the drawable. The renderer is expected to clear outside
 * this viewport, so fixed-center scenes naturally gain side mattes while a
 * world-expand plan whose display aspect equals 16:9 fills the canvas.
 * Invalid drawable dimensions fail closed to an empty viewport. */
HostOutputViewport resolve_output_viewport(
    const HostOutputCompositionPlan& plan,
    int drawable_width,
    int drawable_height) noexcept;

/* Evidence-backed runtime scene binding.
 *
 * The title's verified rider-selection states identify the durable race mode:
 * 0x3C = 1P, 0x3D = ordinary 2P, 0x3E = VS. They are latched only outside
 * active racing so incidental in-race frontend scratch values cannot change
 * composition. 1P, ordinary-2P and VS races widen: their margins are
 * presented host-side per viewport (native/title/uniracers_ws_margins.c).
 * Unknown races fail closed to fixed-center. Non-race scenes always remain
 * fixed-center.
 */
void reset_widescreen_scene_state(HostWidescreenSceneState* state) noexcept;
HostSceneComposition observe_widescreen_scene(
    HostWidescreenSceneState* state,
    std::uint8_t race_active_state,
    std::uint8_t frontend_state) noexcept;

}  // namespace ur::product
