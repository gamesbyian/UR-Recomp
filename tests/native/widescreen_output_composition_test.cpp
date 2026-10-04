#include "widescreen_output_composition.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto original_wide = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::WorldExpand);
    assert(original_wide.source_width == 342);
    assert(original_wide.source_height == 224);
    assert(original_wide.canvas_width == 342);
    assert(original_wide.canvas_height == 224);
    assert(original_wide.source_pixel_aspect == HostRational{7, 6});
    assert(original_wide.horizontal_fit == HostRational{512, 513});
    assert(!original_wide.center_source);
    assert(original_wide.expose_added_world);

    const auto original_fixed = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::FixedCenter);
    assert(original_fixed.source_width == 256);
    assert(original_fixed.canvas_width == 342);
    assert(original_fixed.source_pixel_aspect == HostRational{7, 6});
    assert(original_fixed.horizontal_fit == HostRational{1, 1});
    assert(original_fixed.center_source);
    assert(!original_fixed.expose_added_world);

    const auto remastered_wide = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Remastered,
        HostSceneComposition::WorldExpand);
    assert(remastered_wide.source_width == 342);
    assert(remastered_wide.canvas_width == 342);
    assert(remastered_wide.source_pixel_aspect == HostRational{1, 1});
    assert(remastered_wide.horizontal_fit == HostRational{1, 1});
    assert(!remastered_wide.center_source);
    assert(remastered_wide.expose_added_world);

    const auto remastered_fixed = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Remastered,
        HostSceneComposition::FixedCenter);
    assert(remastered_fixed.source_width == 256);
    assert(remastered_fixed.canvas_width == 342);
    assert(remastered_fixed.source_pixel_aspect == HostRational{1, 1});
    assert(remastered_fixed.horizontal_fit == HostRational{1, 1});
    assert(remastered_fixed.center_source);
    assert(!remastered_fixed.expose_added_world);

    return 0;
}
