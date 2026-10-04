#pragma once

#include "completed_run_ghost_projection.hpp"
#include "completed_run_ghost_trace.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

struct CompletedRunGhostPresentationFrame {
    std::uint64_t race_frame = 0;
    std::uint16_t semantic_frame_id = 0;
    std::uint16_t pitch_angle = 0;
    std::uint8_t facing = 0;
    std::uint8_t sprite_attr = 0;
    CompletedRunGhostRacerCompositionSample composition;
    int screen_x = 0;
    int screen_y = 0;
    bool hflip = false;
    bool vflip = false;
    bool oam_x_high = false;
};

/* Resolve one presentation-only ghost frame from retained authoritative
 * evidence and the CURRENT live camera projection context.
 *
 * Missing trace samples and live-camera culling both fail closed. No gameplay
 * state is read or mutated beyond the caller-provided immutable inputs.
 */
std::optional<CompletedRunGhostPresentationFrame>
resolve_completed_run_ghost_presentation_frame(
    const CompletedRunGhostTrace& trace,
    std::uint64_t race_frame,
    const CompletedRunGhostProjectionContext& live);

}  // namespace ur::product
