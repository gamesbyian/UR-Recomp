#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace ur::product {

/*
 * Presentation-only previous-frame blend for Reduced Flashing.
 *
 * The reference is always the previous UNBLENDED guest frame. Re-presenting
 * one guest frame at a higher host refresh may blend against the same reference
 * without advancing it. Geometry changes reset automatically.
 *
 * This object owns presentation bytes only. It has no guest-memory, timing,
 * input, replay, records, or simulation authority.
 */
class ReducedFlashingFrameBlend {
public:
    void reset() noexcept;

    /*
     * Blend the supplied frame in place against the retained unblended guest
     * frame.
     *
     * - width/height are presentation pixels.
     * - pitch_bytes may exceed width * 4.
     * - advance_reference=true means this present carries a new guest frame:
     *   capture its unblended bytes as the next reference.
     * - advance_reference=false means a repeated/intermediate host present:
     *   blend against the existing reference without replacing it.
     *
     * Returns true only when the supplied frame was actually modified.
     * Invalid geometry, insufficient pitch, allocation failure, first frame
     * after reset/resize, and holding with no retained frame are inert.
     */
    bool apply(
        std::uint8_t* frame,
        int width,
        int height,
        std::size_t pitch_bytes,
        bool advance_reference) noexcept;

    bool has_reference() const noexcept { return valid_; }
    int width() const noexcept { return width_; }
    int height() const noexcept { return height_; }

private:
    bool ensure_geometry(int width, int height) noexcept;

    std::vector<std::uint8_t> previous_;
    int width_ = 0;
    int height_ = 0;
    bool valid_ = false;
};

}  // namespace ur::product
