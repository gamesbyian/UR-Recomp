#include "racer_replacement_selector.hpp"

#include <cassert>

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
    assert(find_racer_registration_for_state(0x0541, exact) == registration);
    auto no_exact_state = exact;
    no_exact_state.p2_primary = 0x0544;
    assert(find_racer_registration_for_state(0x0541, no_exact_state) == nullptr);

    const auto original = select_racer_presentation(
        GraphicsPack::Original, 0x0541, exact
    );
    assert(!original.uses_replacement());
    assert(original.selected_pack == GraphicsPack::Original);
    assert(original.fallback_reason == FallbackReason::OriginalRequested);

    const auto remastered = select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, exact
    );
    assert(remastered.uses_replacement());
    assert(remastered.selected_pack == GraphicsPack::Remastered);
    assert(remastered.fallback_reason == FallbackReason::None);
    assert(remastered.registration == registration);

    auto mismatch = exact;
    mismatch.p1_companion_gate_word = 0;
    const auto mismatch_result = select_racer_presentation(
        GraphicsPack::Remastered, 0x0541, mismatch
    );
    assert(!mismatch_result.uses_replacement());
    assert(mismatch_result.selected_pack == GraphicsPack::Original);
    assert(mismatch_result.fallback_reason == FallbackReason::CompositionMismatch);
    assert(mismatch_result.registration == registration);

    const auto unknown = select_racer_presentation(
        GraphicsPack::Remastered, 0x0999, exact
    );
    assert(!unknown.uses_replacement());
    assert(unknown.selected_pack == GraphicsPack::Original);
    assert(unknown.fallback_reason == FallbackReason::UnregisteredSemanticFrame);
    assert(unknown.registration == nullptr);

    const auto reimagined = select_racer_presentation(
        GraphicsPack::Reimagined, 0x0541, exact
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
        GraphicsPack::Remastered, 0x0540, exact
    );
    assert(p2_remastered.uses_replacement());
    assert(p2_remastered.registration == p2);

    auto p2_mismatch_state = exact;
    p2_mismatch_state.p2_primary = 0x0544;
    const auto p2_mismatch = select_racer_presentation(
        GraphicsPack::Remastered, 0x0540, p2_mismatch_state
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
        GraphicsPack::Remastered, 0x057D, p1_adjacent->composition
    );
    const auto p2_adjacent_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x0543, p2_adjacent->composition
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
        GraphicsPack::Remastered, 0x057E, p1_second->composition
    );
    const auto p2_second_selected = select_racer_presentation(
        GraphicsPack::Remastered, 0x0544, p2_second->composition
    );
    assert(p1_second_selected.uses_replacement());
    assert(p2_second_selected.uses_replacement());

    return 0;
}
