#include "completed_run_ghost_racer_selector.hpp"

#include <cassert>

using namespace ur::presentation;

namespace {

ur::product::CompletedRunGhostPresentationFrame frame_for(
    std::uint16_t semantic,
    ur::product::CompletedRunGhostRacerCompositionSample composition) {
    ur::product::CompletedRunGhostPresentationFrame frame;
    frame.semantic_frame_id = semantic;
    frame.composition = composition;
    return frame;
}

}  // namespace

int main() {
    const auto baseline = frame_for(
        0x0541,
        {0x0541, 0x0540, 0x0D0D, 0x0000, 0, 0, 0x0001, 0x0000});
    const auto selected =
        select_completed_run_ghost_racer_presentation(
            GraphicsPack::Remastered, baseline);
    assert(selected.uses_replacement());
    assert(selected.fallback_reason == FallbackReason::None);
    assert(selected.registration);
    assert(selected.registration->semantic_frame_id == 0x0541);
    assert(selected.registration->player == 1);

    auto mismatched = baseline;
    mismatched.composition.p1_companion = 0x7777;
    const auto rejected =
        select_completed_run_ghost_racer_presentation(
            GraphicsPack::Remastered, mismatched);
    assert(!rejected.uses_replacement());
    assert(rejected.fallback_reason == FallbackReason::CompositionMismatch);

    const auto original =
        select_completed_run_ghost_racer_presentation(
            GraphicsPack::Original, baseline);
    assert(!original.uses_replacement());
    assert(original.fallback_reason == FallbackReason::OriginalRequested);

    auto unknown = baseline;
    unknown.semantic_frame_id = 0xFFFF;
    const auto unregistered =
        select_completed_run_ghost_racer_presentation(
            GraphicsPack::Remastered, unknown);
    assert(!unregistered.uses_replacement());
    assert(unregistered.fallback_reason ==
           FallbackReason::UnregisteredSemanticFrame);

    return 0;
}
