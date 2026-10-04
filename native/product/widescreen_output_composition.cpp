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

}  // namespace ur::product
