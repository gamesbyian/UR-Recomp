#include "widescreen_output_composition.hpp"

namespace ur::product {

HostOutputCompositionPlan resolve_16x9_output_composition(
    HostGraphicsRepresentation representation,
    HostSceneComposition scene) noexcept {
    const bool widened = scene == HostSceneComposition::WorldExpand;

    HostOutputCompositionPlan plan{};
    plan.source_width = widened ? 342 : 256;
    plan.source_height = 224;
    plan.canvas_width = 342;
    plan.canvas_height = 224;
    plan.center_source = !widened;
    plan.expose_added_world = widened;

    if (representation == HostGraphicsRepresentation::Original) {
        plan.source_pixel_aspect = {7, 6};
        plan.horizontal_fit = widened
            ? HostRational{512, 513}
            : HostRational{1, 1};
    } else {
        plan.source_pixel_aspect = {1, 1};
        plan.horizontal_fit = {1, 1};
    }

    return plan;
}

}  // namespace ur::product
