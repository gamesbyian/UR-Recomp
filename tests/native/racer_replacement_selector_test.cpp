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

    return 0;
}
