#include "widescreen_output_composition.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    assert(resolve_output_geometry_representation(false) ==
           HostGraphicsRepresentation::Original);
    assert(resolve_output_geometry_representation(true) ==
           HostGraphicsRepresentation::Remastered);

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

    const HostOutputViewport wide_1080{0, 0, 1920, 1080};
    const HostOutputViewport fixed_1080{240, 0, 1440, 1080};
    const HostOutputViewport wide_1280x1024{0, 152, 1280, 720};
    const HostOutputViewport fixed_1280x1024{160, 152, 960, 720};
    const HostOutputViewport empty_viewport{};

    assert(resolve_output_viewport(original_wide, 1920, 1080) == wide_1080);
    assert(resolve_output_viewport(original_fixed, 1920, 1080) == fixed_1080);

    // QA-10: actual UHD drawable geometry. 342x224 source with 7:6 PAR
    // and 512:513 fit fills 16:9 without cropping the final eight lines.
    // Original 256x224 keeps its authentic 4:3 visible content centered;
    // neither layout silently promotes a 216-high legacy crop.
    const HostOutputViewport wide_4k{0, 0, 3840, 2160};
    const HostOutputViewport fixed_4k{480, 0, 2880, 2160};
    assert(resolve_output_viewport(original_wide, 3840, 2160) == wide_4k);
    assert(resolve_output_viewport(original_fixed, 3840, 2160) == fixed_4k);
    // QA-10: a *square-pixel* 342x224 Remastered scene does not have the
    // Original-mode 7:6 display PAR. Retaining 342 logical columns cannot
    // populate a physical 16:9 UHD drawable with square source texels.
    // Explicitly preserve true output geometry, without quietly stretching
    // the source/authoring grid to pass a future HD-asset acceptance gate.
    const HostOutputViewport remastered_wide_4k{271, 0, 3298, 2160};
    const HostOutputViewport remastered_fixed_4k{685, 0, 2469, 2160};
    assert(resolve_output_viewport(remastered_wide, 3840, 2160) ==
           remastered_wide_4k);
    assert(resolve_output_viewport(remastered_fixed, 3840, 2160) ==
           remastered_fixed_4k);
    assert(remastered_wide_4k.width < wide_4k.width);
    assert(remastered_wide_4k.x > 0);
    assert(remastered_wide.display_pixel_aspect == square_par);
    assert(original_wide.display_pixel_aspect == authentic_par);
    // The wide Remastered source remains narrower than the 16:9 drawable
    // until independently authored square-pixel border/world content exists.
    const HostOutputViewport remastered_wide_1080{135, 0, 1649, 1080};
    assert(resolve_output_viewport(remastered_wide, 1920, 1080) ==
           remastered_wide_1080);

    const HostOutputViewport portrait_4k_drawable{0, 1312, 2160, 1215};
    assert(resolve_output_viewport(original_wide, 2160, 3840) ==
           portrait_4k_drawable);

    assert(resolve_output_viewport(original_wide, 1280, 1024) == wide_1280x1024);
    assert(resolve_output_viewport(original_fixed, 1280, 1024) == fixed_1280x1024);
    assert(resolve_output_viewport(original_fixed, 0, 1080) == empty_viewport);

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
           HostSceneComposition::WorldExpand);
    // VS results remain centered.
    assert(observe_widescreen_scene(&scene, 0x00, 0xF9) ==
           HostSceneComposition::FixedCenter);

    reset_widescreen_scene_state(&scene);
    assert(observe_widescreen_scene(&scene, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);
    assert(observe_widescreen_scene(nullptr, 0x01, 0x00) ==
           HostSceneComposition::FixedCenter);

    return 0;
}
