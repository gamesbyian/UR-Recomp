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
           state->race_mode == HostRacePresentationMode::TwoPlayer
        ? HostSceneComposition::WorldExpand
        : HostSceneComposition::FixedCenter;
}

}  // namespace ur::product
