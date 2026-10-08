#pragma once

#include <cstdint>

namespace ur::test {

// Capture and fresh-process re-drive can observe the terminal lifecycle one
// guest frame apart. A larger discrepancy is not simulation equivalence,
// even when all recorded controller spans and timer splits happen to match.
inline bool replay_frame_windows_compatible(
    std::uint64_t original_frames, std::uint64_t replayed_frames) noexcept {
    return original_frames >= replayed_frames
        ? original_frames - replayed_frames <= 1u
        : replayed_frames - original_frames <= 1u;
}

}  // namespace ur::test
