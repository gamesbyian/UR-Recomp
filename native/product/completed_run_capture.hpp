#pragma once

#include "completed_run_record.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

/* Lifecycle-only coordinator for a single race attempt.
 *
 * The caller owns title semantics. Call begin_attempt() after the authoritative
 * race-entry frame has completed, then observe_guest_frame() once for each
 * subsequent frame actually submitted to the guest. This mirrors the existing
 * Restart Race boundary: transition input is not part of the replay stream.
 */
class CompletedRunCapture {
public:
    bool begin_attempt(const RunRecordProvenance& provenance);
    bool observe_guest_frame(std::uint32_t controller_word);
    bool observe_split(const std::string& id, std::uint64_t ticks60);

    std::optional<CompletedRunRecord> complete(
        std::uint64_t elapsed_ticks60,
        const std::string& terminal_simulation_digest = {});

    void abort_attempt();
    bool capturing() const { return capturing_; }
    std::uint64_t captured_frames() const { return captured_frames_; }

private:
    bool capturing_ = false;
    std::uint64_t captured_frames_ = 0;
    RunRecordProvenance provenance_;
    CompletedRunRecorder recorder_;
    std::vector<RunRecordSplit> splits_;
};

/* Presentation/selection seam for a future PB ghost. Returns the fastest
 * compatible timed run and never grants the selected record gameplay
 * authority. Equal times keep the most recently supplied record. */
std::optional<std::size_t> select_fastest_compatible_run(
    const std::vector<CompletedRunRecord>& records,
    const RunPlaybackTarget& target);

}  // namespace ur::product
