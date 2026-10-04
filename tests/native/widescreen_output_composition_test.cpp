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

    assert(resolve_output_viewport(original_wide, 1920, 1080) ==
           HostOutputViewport{0, 0, 1920, 1080});
    assert(resolve_output_viewport(original_fixed, 1920, 1080) ==
           HostOutputViewport{240, 0, 1440, 1080});
    assert(resolve_output_viewport(original_wide, 1280, 1024) ==
           HostOutputViewport{0, 152, 1280, 720});
    assert(resolve_output_viewport(original_fixed, 1280, 1024) ==
           HostOutputViewport{160, 152, 960, 720});
    assert(resolve_output_viewport(original_fixed, 0, 1080) ==
           HostOutputViewport{});

    HostWidescreenSceneState scene{};
    assert(observe_widescreen_scene(&scene, 0x00, 0xD7) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);

    assert(observe_widescreen_scene(&scene, 0x00, 0x3C) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::WorldExpand);
    // Incidental in-race scratch must not replace the latched 1P identity.
    assert(observe_widescreen_scene(&scene, 0x01, 0x3E) ==
           HostSceneComposition::WorldExpand);
    // Results/pre-race remain centered even while the mode latch persists.
    assert(observe_widescreen_scene(&scene, 0x00, 0x99) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::WorldExpand);

    assert(observe_widescreen_scene(&scene, 0x00, 0x3D) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::WorldExpand);

    assert(observe_widescreen_scene(&scene, 0x00, 0x3E) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);

    reset_widescreen_scene_state(&scene);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(nullptr, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);

    return 0;
}
