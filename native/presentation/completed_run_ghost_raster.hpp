#pragma once

#include "completed_run_ghost_racer_selector.hpp"
#include "racer_hd_presenter.hpp"

#include <cstddef>
#include <cstdint>

namespace ur::presentation {

/* Blend one already-resolved ghost racer into a host-owned RGBA8888 surface.
 *
 * The frame coordinates are logical 256x224 presentation coordinates and are
 * scaled by `scale`. This helper only writes `dst`; it never touches guest
 * RAM, PPU/OAM state or controller input.
 */
bool draw_completed_run_ghost_racer(
    std::uint8_t* dst,
    std::size_t pitch,
    int frame_w,
    int frame_h,
    int scale,
    const ur::product::CompletedRunGhostPresentationFrame& frame,
    const RacerRegistration& registration,
    std::uint8_t opacity
) noexcept;

}  // namespace ur::presentation
