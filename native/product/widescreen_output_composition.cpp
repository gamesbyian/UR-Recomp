#include "widescreen_output_composition.hpp"

namespace ur::product {

HostOutputCompositionPlan resolve_16x9_output_composition(
    HostGraphicsRepresentation representation,
    HostSceneComposition scene) noexcept {
    const bool widened = scene == HostSceneComposition::WorldExpand;

    HostOutputCompositionPlan plan{};
    plan.logical_view_width = widened ? 342 : 256;
    plan.logical_view_height = 224;
    plan.target_output_aspect = {16, 9};
    plan.center_logical_view = !widened;
    plan.expose_added_world = widened;

    if (representation == HostGraphicsRepresentation::Original) {
        plan.display_pixel_aspect = {7, 6};
        plan.horizontal_fit = widened
            ? HostRational{512, 513}
            : HostRational{1, 1};
    } else {
        plan.display_pixel_aspect = {1, 1};
        plan.horizontal_fit = {1, 1};
    }

    return plan;
}

HostOutputViewport resolve_output_viewport(
    const HostOutputCompositionPlan& plan,
    int drawable_width,
    int drawable_height) noexcept {
    if (drawable_width <= 0 || drawable_height <= 0 ||
        plan.logical_view_width <= 0 || plan.logical_view_height <= 0 ||
        plan.display_pixel_aspect.numerator <= 0 ||
        plan.display_pixel_aspect.denominator <= 0 ||
        plan.target_output_aspect.numerator <= 0 ||
        plan.target_output_aspect.denominator <= 0 ||
        plan.horizontal_fit.numerator <= 0 ||
        plan.horizontal_fit.denominator <= 0) {
        return {};
    }

    const std::int64_t target_num = plan.target_output_aspect.numerator;
    const std::int64_t target_den = plan.target_output_aspect.denominator;

    int canvas_width = drawable_width;
    int canvas_height = static_cast<int>(
        (static_cast<std::int64_t>(canvas_width) * target_den +
         target_num / 2) / target_num);
    if (canvas_height > drawable_height) {
        canvas_height = drawable_height;
        canvas_width = static_cast<int>(
            (static_cast<std::int64_t>(canvas_height) * target_num +
             target_den / 2) / target_den);
    }
    if (canvas_width < 1 || canvas_height < 1) {
        return {};
    }

    const std::int64_t source_num =
        static_cast<std::int64_t>(plan.logical_view_width) *
        plan.display_pixel_aspect.numerator *
        plan.horizontal_fit.numerator;
    const std::int64_t source_den =
        static_cast<std::int64_t>(plan.logical_view_height) *
        plan.display_pixel_aspect.denominator *
        plan.horizontal_fit.denominator;

    int width = canvas_width;
    int height = static_cast<int>(
        (static_cast<std::int64_t>(width) * source_den +
         source_num / 2) / source_num);
    if (height > canvas_height) {
        height = canvas_height;
        width = static_cast<int>(
            (static_cast<std::int64_t>(height) * source_num +
             source_den / 2) / source_den);
    }

    if (width < 1) width = 1;
    if (height < 1) height = 1;

    const int canvas_x = (drawable_width - canvas_width) / 2;
    const int canvas_y = (drawable_height - canvas_height) / 2;
    return {
        canvas_x + (canvas_width - width) / 2,
        canvas_y + (canvas_height - height) / 2,
        width,
        height,
    };
}

void reset_widescreen_scene_state(HostWidescreenSceneState* state) noexcept {
    if (state) {
        state->race_mode = HostRacePresentationMode::Unknown;
    }
}

HostSceneComposition observe_widescreen_scene(
    HostWidescreenSceneState* state,
    std::uint8_t race_active_state,
    std::uint8_t frontend_state) noexcept {
    if (state && race_active_state != 0x01) {
        switch (frontend_state) {
        case 0x3C:
            state->race_mode = HostRacePresentationMode::OnePlayer;
            break;
        case 0x3D:
            state->race_mode = HostRacePresentationMode::TwoPlayer;
            break;
        case 0x3E:
            state->race_mode = HostRacePresentationMode::Vs;
            break;
        default:
            break;
        }
    }

    if (race_active_state != 0x01 || !state) {
        return HostSceneComposition::FixedCenter;
    }

    return state->race_mode == HostRacePresentationMode::OnePlayer ||
           state->race_mode == HostRacePresentationMode::TwoPlayer ||
           state->race_mode == HostRacePresentationMode::Vs
        ? HostSceneComposition::WorldExpand
        : HostSceneComposition::FixedCenter;
}

}  // namespace ur::product
