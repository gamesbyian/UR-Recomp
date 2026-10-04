#pragma once

#include "completed_run_ghost_world_sample.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::product {

struct CompletedRunGhostProjectionContext {
    std::uint16_t camera_x = 0;
    std::uint16_t camera_y = 0;
    std::uint16_t horizontal_scale_shifts = 0;
    std::uint16_t horizontal_lower_bound = 0;
    std::uint16_t horizontal_upper_bound = 0;
    std::uint16_t horizontal_wrap_mask = 0;
};

struct CompletedRunGhostScreenProjection {
    int screen_x = 0;
    int screen_y = 0;
    bool oam_x_high = false;
};

/* Read the live ordinary-1P stock racer projection context.
 *
 * This deliberately fails closed when $0DDB selects the alternate projection
 * path. The first ghost slice only targets the already-eligible ordinary 1P
 * timed-Race domain.
 */
std::optional<CompletedRunGhostProjectionContext>
read_completed_run_ghost_projection_context(
    const std::uint8_t* wram,
    std::size_t wram_size);

/* Reproduce the ordinary P1 coordinate/culling portion of
 * Race_BuildRacerOAMState ($82:ACF5..AD62) using a historical world sample
 * and the CURRENT live camera context.
 *
 * Returns nullopt when the historical racer would be culled by the live
 * viewport. It does not read or write guest presentation state.
 */
std::optional<CompletedRunGhostScreenProjection>
project_completed_run_ghost_sample(
    const CompletedRunGhostWorldSample& sample,
    const CompletedRunGhostProjectionContext& live);

}  // namespace ur::product
