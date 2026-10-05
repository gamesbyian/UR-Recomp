#include "racer_replacement_selector.hpp"

#include <cassert>
#include <initializer_list>

using namespace ur::presentation;

int main() {
    const auto* registration = find_racer_registration(0x0541);
    assert(registration != nullptr);
    assert(registration->semantic_frame_id == 0x0541);
    assert(registration->player == 1);
    assert(registration->palette_asset_id == 0x06);
    assert(registration->logical_width == 64);
    assert(registration->logical_height == 64);
    assert(registration->occupancy_tile_x == 1);
    assert(registration->occupancy_tile_y == 0);
    assert(registration->remastered_density_scale == 4);
    assert(registration->anchor_fixed_point_scale == 2);
    assert(registration->has_explicit_pivot);
    assert(registration->has_explicit_contact_anchor);
    assert(registration->semantic_pivot.x2 == 63);
    assert(registration->semantic_pivot.y2 == 63);
    assert(registration->contact_anchor.x2 == 61);
    assert(registration->contact_anchor.y2 == 76);

    const auto h_contact = transform_racer_anchor(
        registration->contact_anchor,
        registration->logical_width,
        registration->logical_height,
        true,
        false
    );
    assert(h_contact.x2 == 65);
    assert(h_contact.y2 == 76);
    const auto hv_contact = transform_racer_anchor(
        registration->contact_anchor,
        registration->logical_width,
        registration->logical_height,
        true,
        true
    );
    assert(hv_contact.x2 == 65);
    assert(hv_contact.y2 == 50);

    const RacerCompositionState exact = registration->composition;
    assert(find_racer_registration_for_state(0x0541, exact, 1) == registration);
    auto no_exact_state = exact;
    no_exact_state.p2_primary = 0x0544;
    assert(find_racer_registration_for_state(0x0541, no_exact_state, 1) == nullptr);

    const auto original = select_racer_presentation(
        GraphicsPack::Original, 0x0541, exact, 1
    );
    assert(!original.uses_replacement());
    assert(original.selected_pack == GraphicsPack::Original);
    assert(original.fallback_reason == FallbackReason::OriginalRequested);

    const auto remastered = select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, exact, 1
    );
    assert(remastered.uses_replacement());
    assert(remastered.selected_pack == GraphicsPack::Remastered);
    assert(remastered.fallback_reason == FallbackReason::None);
    assert(remastered.registration == registration);

    auto mismatch = exact;
    mismatch.p1_companion_gate_word = 0;
    const auto mismatch_result = select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, mismatch, 1
    );
    assert(!mismatch_result.uses_replacement());
    assert(mismatch_result.selected_pack == GraphicsPack::Original);
    assert(mismatch_result.fallback_reason == FallbackReason::CompositionMismatch);
    assert(mismatch_result.registration == registration);

    const auto unknown = select_racer_presentation(
        GraphicsPack::Remastered, 0x0999, exact, 1
    );
    assert(!unknown.uses_replacement());
    assert(unknown.selected_pack == GraphicsPack::Original);
    assert(unknown.fallback_reason == FallbackReason::UnregisteredSemanticFrame);
    assert(unknown.registration == nullptr);

    const auto reimagined = select_racer_presentation(
        GraphicsPack::Reimagined, 0x0541, exact, 1
    );
    assert(!reimagined.uses_replacement());
    assert(reimagined.selected_pack == GraphicsPack::Original);
    assert(reimagined.fallback_reason == FallbackReason::PackUnavailable);
    assert(reimagined.registration == registration);

    const auto* p2 = find_racer_registration(0x0540);
    assert(p2 != nullptr);
    assert(p2->semantic_frame_id == 0x0540);
    assert(p2->player == 2);
    assert(p2->palette_asset_id == 0x07);
    assert(composition_equal(p2->composition, exact));
    assert(p2->semantic_pivot.x2 == 63);
    assert(p2->semantic_pivot.y2 == 63);
    assert(p2->contact_anchor.x2 == 63);
    assert(p2->contact_anchor.y2 == 76);

    const auto p2_remastered = select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, exact, 2
    );
    assert(p2_remastered.uses_replacement());
    assert(p2_remastered.registration == p2);

    auto p2_mismatch_state = exact;
    p2_mismatch_state.p2_primary = 0x0544;
    const auto p2_mismatch = select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, p2_mismatch_state, 2
    );
    assert(!p2_mismatch.uses_replacement());
    assert(p2_mismatch.fallback_reason == FallbackReason::CompositionMismatch);

    const auto* p1_adjacent = find_racer_registration(0x057D);
    const auto* p2_adjacent = find_racer_registration(0x0543);
    assert(p1_adjacent != nullptr);
    assert(p2_adjacent != nullptr);
    assert(p1_adjacent->player == 1);
    assert(p2_adjacent->player == 2);
    assert(p1_adjacent->contact_anchor.x2 == 69);
    assert(p1_adjacent->contact_anchor.y2 == 76);
    assert(p2_adjacent->contact_anchor.x2 == 57);
    assert(p2_adjacent->contact_anchor.y2 == 76);
    assert(composition_equal(p1_adjacent->composition, p2_adjacent->composition));

    const auto p1_adjacent_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x057D, p1_adjacent->composition, 1
    );
    const auto p2_adjacent_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x0543, p2_adjacent->composition, 2
    );
    assert(p1_adjacent_selected.uses_replacement());
    assert(p2_adjacent_selected.uses_replacement());

    const auto* p1_second = find_racer_registration(0x057E);
    const auto* p2_second = find_racer_registration(0x0544);
    assert(p1_second != nullptr);
    assert(p2_second != nullptr);
    assert(p1_second->player == 1);
    assert(p2_second->player == 2);
    assert(p1_second->contact_anchor.x2 == 67);
    assert(p1_second->contact_anchor.y2 == 76);
    assert(p2_second->contact_anchor.x2 == 55);
    assert(p2_second->contact_anchor.y2 == 76);
    assert(composition_equal(p1_second->composition, p2_second->composition));

    const auto p1_second_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x057E, p1_second->composition, 1
    );
    const auto p2_second_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x0544, p2_second->composition, 2
    );
    assert(p1_second_selected.uses_replacement());
    assert(p2_second_selected.uses_replacement());

    const RacerCompositionState duplicate_context{
        0x057E,
        0x0543,
        0x0D49,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_duplicate =
        find_racer_registration_for_state(0x057E, duplicate_context, 1);
    const auto* p2_duplicate =
        find_racer_registration_for_state(0x0543, duplicate_context, 2);
    assert(p1_duplicate != nullptr);
    assert(p2_duplicate != nullptr);
    assert(p1_duplicate != p1_second);
    assert(p2_duplicate != p2_adjacent);
    assert(p1_duplicate->contact_anchor.x2 == 67);
    assert(p1_duplicate->contact_anchor.y2 == 76);
    assert(p2_duplicate->contact_anchor.x2 == 57);
    assert(p2_duplicate->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057E, duplicate_context, 1
    ).registration == p1_duplicate);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0543, duplicate_context, 2
    ).registration == p2_duplicate);

    const RacerCompositionState companion_context{
        0x057E,
        0x0544,
        0x0D69,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_companion_context =
        find_racer_registration_for_state(0x057E, companion_context, 1);
    const auto* p2_companion_context =
        find_racer_registration_for_state(0x0544, companion_context, 2);
    assert(p1_companion_context != nullptr);
    assert(p2_companion_context != nullptr);
    assert(p1_companion_context != p1_second);
    assert(p2_companion_context != p2_second);
    assert(p1_companion_context->contact_anchor.x2 == 67);
    assert(p1_companion_context->contact_anchor.y2 == 76);
    assert(p2_companion_context->contact_anchor.x2 == 55);
    assert(p2_companion_context->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057E, companion_context, 1
    ).registration == p1_companion_context);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0544, companion_context, 2
    ).registration == p2_companion_context);

    const RacerCompositionState predecessor_context{
        0x057D,
        0x0542,
        0x0D48,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_predecessor =
        find_racer_registration_for_state(0x057D, predecessor_context, 1);
    const auto* p2_predecessor =
        find_racer_registration_for_state(0x0542, predecessor_context, 2);
    assert(p1_predecessor != nullptr);
    assert(p2_predecessor != nullptr);
    assert(p1_predecessor->contact_anchor.x2 == 69);
    assert(p1_predecessor->contact_anchor.y2 == 76);
    assert(p2_predecessor->contact_anchor.x2 == 59);
    assert(p2_predecessor->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057D, predecessor_context, 1
    ).registration == p1_predecessor);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0542, predecessor_context, 2
    ).registration == p2_predecessor);

    const RacerCompositionState forward_context{
        0x057F,
        0x0543,
        0x0D6A,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_forward =
        find_racer_registration_for_state(0x057F, forward_context, 1);
    const auto* p2_forward =
        find_racer_registration_for_state(0x0543, forward_context, 2);
    assert(p1_forward != nullptr);
    assert(p2_forward != nullptr);
    assert(p1_forward->contact_anchor.x2 == 65);
    assert(p1_forward->contact_anchor.y2 == 76);
    assert(p2_forward->contact_anchor.x2 == 57);
    assert(p2_forward->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057F, forward_context, 1
    ).registration == p1_forward);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0543, forward_context, 2
    ).registration == p2_forward);

    const RacerCompositionState companion_predecessor_context{
        0x0541,
        0x0540,
        0x0D2D,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_companion_predecessor =
        find_racer_registration_for_state(0x0541, companion_predecessor_context, 1);
    const auto* p2_companion_predecessor =
        find_racer_registration_for_state(0x0540, companion_predecessor_context, 2);
    assert(p1_companion_predecessor != nullptr);
    assert(p2_companion_predecessor != nullptr);
    assert(p1_companion_predecessor != registration);
    assert(p2_companion_predecessor != p2);
    assert(p1_companion_predecessor->contact_anchor.x2 == 61);
    assert(p1_companion_predecessor->contact_anchor.y2 == 76);
    assert(p2_companion_predecessor->contact_anchor.x2 == 63);
    assert(p2_companion_predecessor->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, companion_predecessor_context, 1
    ).registration == p1_companion_predecessor);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, companion_predecessor_context, 2
    ).registration == p2_companion_predecessor);

    auto unregistered_companion_context = companion_predecessor_context;
    unregistered_companion_context.p1_companion = 0x0D2C;
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, unregistered_companion_context, 1
    ).fallback_reason == FallbackReason::CompositionMismatch);

    const RacerCompositionState reverse_predecessor_context{
        0x0540,
        0x0541,
        0x0D2C,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_reverse_predecessor =
        find_racer_registration_for_state(0x0540, reverse_predecessor_context, 1);
    const auto* p2_reverse_predecessor =
        find_racer_registration_for_state(0x0541, reverse_predecessor_context, 2);
    assert(p1_reverse_predecessor != nullptr);
    assert(p2_reverse_predecessor != nullptr);
    assert(p1_reverse_predecessor->player == 1);
    assert(p2_reverse_predecessor->player == 2);
    assert(p1_reverse_predecessor->contact_anchor.x2 == 63);
    assert(p1_reverse_predecessor->contact_anchor.y2 == 76);
    assert(p2_reverse_predecessor->contact_anchor.x2 == 61);
    assert(p2_reverse_predecessor->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, reverse_predecessor_context, 1
    ).registration == p1_reverse_predecessor);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, reverse_predecessor_context, 2
    ).registration == p2_reverse_predecessor);

    auto reverse_predecessor_mismatch = reverse_predecessor_context;
    reverse_predecessor_mismatch.p1_companion = 0x0D2B;
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, reverse_predecessor_mismatch, 1
    ).fallback_reason == FallbackReason::CompositionMismatch);

    for (const std::uint16_t companion : {std::uint16_t{0x0D2C}, std::uint16_t{0x0D4C}}) {
        const RacerCompositionState context{
            0x0540,
            0x0542,
            companion,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        };
        const auto* p1_context =
            find_racer_registration_for_state(0x0540, context, 1);
        const auto* p2_context =
            find_racer_registration_for_state(0x0542, context, 2);
        assert(p1_context != nullptr);
        assert(p2_context != nullptr);
        assert(p1_context->player == 1);
        assert(p2_context->player == 2);
        assert(p1_context->contact_anchor.x2 == 63);
        assert(p1_context->contact_anchor.y2 == 76);
        assert(p2_context->contact_anchor.x2 == 59);
        assert(p2_context->contact_anchor.y2 == 76);
        assert(select_racer_presentation(
            GraphicsPack::Remastered, 0x0540, context, 1
        ).registration == p1_context);
        assert(select_racer_presentation(
            GraphicsPack::Remastered, 0x0542, context, 2
        ).registration == p2_context);
    }

    const RacerCompositionState discriminator_a{
        0x0540, 0x0542, 0x0D2C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const RacerCompositionState discriminator_b{
        0x0540, 0x0542, 0x0D4C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    assert(find_racer_registration_for_state(0x0540, discriminator_a, 1) !=
           find_racer_registration_for_state(0x0540, discriminator_b, 1));

    const RacerCompositionState p057f_p0542_context{
        0x057F,
        0x0542,
        0x0D4A,
        0x0000,
        0,
        0,
        0x0001,
        0x0000,
    };
    const auto* p1_057f_0542 =
        find_racer_registration_for_state(0x057F, p057f_p0542_context, 1);
    const auto* p2_057f_0542 =
        find_racer_registration_for_state(0x0542, p057f_p0542_context, 2);
    assert(p1_057f_0542 != nullptr);
    assert(p2_057f_0542 != nullptr);
    assert(p1_057f_0542->player == 1);
    assert(p2_057f_0542->player == 2);
    assert(p1_057f_0542->contact_anchor.x2 == 65);
    assert(p1_057f_0542->contact_anchor.y2 == 76);
    assert(p2_057f_0542->contact_anchor.x2 == 59);
    assert(p2_057f_0542->contact_anchor.y2 == 76);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057F, p057f_p0542_context, 1
    ).registration == p1_057f_0542);
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x0542, p057f_p0542_context, 2
    ).registration == p2_057f_0542);

    auto p057f_p0542_mismatch = p057f_p0542_context;
    p057f_p0542_mismatch.p1_companion = 0x0D49;
    assert(select_racer_presentation(
        GraphicsPack::Remastered, 0x057F, p057f_p0542_mismatch, 1
    ).fallback_reason == FallbackReason::CompositionMismatch);

    return 0;
}
