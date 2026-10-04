#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::product {

/* Minimal authoritative presentation sample for a completed-run ghost.
 *
 * Values are read directly from promoted guest state. They describe where the
 * original simulation placed P1 and which semantic racer pose/orientation it
 * selected. The sample carries no mutation API and is not sufficient to drive
 * gameplay.
 */
struct CompletedRunGhostRacerCompositionSample {
    std::uint16_t p1_primary = 0;
    std::uint16_t p2_primary = 0;
    std::uint16_t p1_companion = 0;
    std::uint16_t p2_companion = 0;
    std::uint16_t p1_selector = 0;
    std::uint16_t p2_selector = 0;
    std::uint16_t p1_companion_gate_word = 0;
    std::uint16_t p2_companion_gate_word = 0;
};

struct CompletedRunGhostWorldSample {
    std::uint64_t race_frame = 0;
    std::uint16_t world_x = 0;
    std::uint16_t world_y = 0;
    std::uint16_t pitch_angle = 0;
    std::uint16_t semantic_frame_id = 0;
    std::uint8_t facing = 0;
    std::uint8_t sprite_attr = 0;
    CompletedRunGhostRacerCompositionSample composition;
};

/* Read the promoted USA-retail P1 presentation/world state from WRAM.
 *
 * Required promoted fields:
 *   0411 world X
 *   0415 world Y
 *   04C7 pitch/orientation
 *   0BA1 facing
 *   0FE9 racer semantic presentation ID
 *   150C P1 OAM sprite attribute byte (H/V flip and presentation flags)
 *   0FE9/0FEB primary semantic IDs
 *   0D3F/0D41 companion IDs
 *   0C83/0C85 selectors
 *   0D1B/0D1D companion gate words
 *
 * This is deliberately camera-independent. A later renderer must project the
 * captured world position through the established live-camera presentation
 * path rather than replaying physics or reusing historical screen OAM.
 */
std::optional<CompletedRunGhostWorldSample> read_completed_run_ghost_world_sample(
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint64_t race_frame);

}  // namespace ur::product
