#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::product {

/* Exact host-owned nearest-neighbour composition for a logical RGBA frame.
 *
 * This exists so presentation density remains stable even when a higher-density
 * replacement presenter has no asset for the current frame. It never changes
 * guest geometry: frame_width/frame_height are logical dimensions and scale
 * only sizes the destination presentation surface.
 *
 * Both pointers are byte buffers: the source need not be uint32-aligned and
 * the destination pitch may include any number of padding bytes. The caller
 * supplies non-overlapping, sufficiently allocated input/output spans; this
 * routine checks stride arithmetic and never writes destination padding.
 */
bool compose_nearest_density_frame(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int frame_width,
    int frame_height,
    int scale) noexcept;

}  // namespace ur::product
