#pragma once

#include "../product/completed_run_ghost_frame.hpp"
#include "racer_replacement_selector.hpp"

namespace ur::presentation {

/* Select the exact existing Racer-HD registration for a retained ghost frame.
 *
 * The ghost trace carries the same synchronized composition tuple used by the
 * live selector. This adapter performs no fuzzy semantic-ID fallback and does
 * not mutate guest state.
 */
SelectionResult select_completed_run_ghost_racer_presentation(
    GraphicsPack requested_pack,
    const ur::product::CompletedRunGhostPresentationFrame& frame
) noexcept;

}  // namespace ur::presentation
