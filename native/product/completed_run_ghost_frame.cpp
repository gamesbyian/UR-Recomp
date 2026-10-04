#include "completed_run_ghost_frame.hpp"

namespace ur::product {

std::optional<CompletedRunGhostPresentationFrame>
resolve_completed_run_ghost_presentation_frame(
    const CompletedRunGhostTrace& trace,
    std::uint64_t race_frame,
    const CompletedRunGhostProjectionContext& live) {
    const CompletedRunGhostWorldSample* sample =
        completed_run_ghost_trace_sample_at(trace, race_frame);
    if (!sample) return std::nullopt;

    const auto projected =
        project_completed_run_ghost_sample(*sample, live);
    if (!projected) return std::nullopt;

    return CompletedRunGhostPresentationFrame{
        sample->race_frame,
        sample->semantic_frame_id,
        sample->pitch_angle,
        sample->facing,
        sample->sprite_attr,
        sample->composition,
        projected->screen_x,
        projected->screen_y,
        (sample->sprite_attr & 0x40u) != 0,
        (sample->sprite_attr & 0x80u) != 0,
        projected->oam_x_high,
    };
}

}  // namespace ur::product
