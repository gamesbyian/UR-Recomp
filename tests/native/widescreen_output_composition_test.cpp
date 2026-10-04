#include "widescreen_output_composition.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const HostRational authentic_par{7, 6};
    const HostRational square_par{1, 1};
    const HostRational target_16x9{16, 9};
    const HostRational wide_fit{512, 513};
    const HostRational identity_fit{1, 1};

    const auto original_wide = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::WorldExpand);
    assert(original_wide.logical_view_width == 342);
    assert(original_wide.logical_view_height == 224);
    assert(original_wide.display_pixel_aspect == authentic_par);
    assert(original_wide.target_output_aspect == target_16x9);
    assert(original_wide.horizontal_fit == wide_fit);
    assert(!original_wide.center_logical_view);
    assert(original_wide.expose_added_world);

    const auto original_fixed = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::FixedCenter);
    assert(original_fixed.logical_view_width == 256);
    assert(original_fixed.logical_view_height == 224);
    assert(original_fixed.display_pixel_aspect == authentic_par);
    assert(original_fixed.target_output_aspect == target_16x9);
    assert(original_fixed.horizontal_fit == identity_fit);
    assert(original_fixed.center_logical_view);
    assert(!original_fixed.expose_added_world);

    const auto remastered_wide = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Remastered,
        HostSceneComposition::WorldExpand);
    assert(remastered_wide.logical_view_width == 342);
    assert(remastered_wide.logical_view_height == 224);
    assert(remastered_wide.display_pixel_aspect == square_par);
    assert(remastered_wide.target_output_aspect == target_16x9);
    assert(remastered_wide.horizontal_fit == identity_fit);
    assert(!remastered_wide.center_logical_view);
    assert(remastered_wide.expose_added_world);

    const auto remastered_fixed = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Remastered,
        HostSceneComposition::FixedCenter);
    assert(remastered_fixed.logical_view_width == 256);
    assert(remastered_fixed.logical_view_height == 224);
    assert(remastered_fixed.display_pixel_aspect == square_par);
    assert(remastered_fixed.target_output_aspect == target_16x9);
    assert(remastered_fixed.horizontal_fit == identity_fit);
    assert(remastered_fixed.center_logical_view);
    assert(!remastered_fixed.expose_added_world);

    return 0;
}
