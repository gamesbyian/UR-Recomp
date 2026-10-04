#include "completed_run_ghost_racer_selector.hpp"

namespace ur::presentation {

SelectionResult select_completed_run_ghost_racer_presentation(
    GraphicsPack requested_pack,
    const ur::product::CompletedRunGhostPresentationFrame& frame
) noexcept {
    const auto& c = frame.composition;
    const RacerCompositionState composition = {
        c.p1_primary,
        c.p2_primary,
        c.p1_companion,
        c.p2_companion,
        c.p1_selector,
        c.p2_selector,
        c.p1_companion_gate_word,
        c.p2_companion_gate_word,
    };
    return select_racer_presentation(
        requested_pack,
        frame.semantic_frame_id,
        composition);
}

}  // namespace ur::presentation
