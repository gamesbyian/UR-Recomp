#pragma once

// A bounded, process-local retry of a source-settled native one-player
// result whose first canonical Records append failed. No alternate store,
// guest result authority or replay/PB claim. A retry is allowed only while
// the SAME source-confirmed 1P result surface retains host ownership.
#include "baldosa_guest_result_observer.hpp"

#include <cstdint>
#include <limits>
#include <optional>
#include <utility>

namespace ur::product {

enum class BaldosaRunRetryOutcome : std::uint8_t {
    Saved,
    Pending,
    Exhausted,
};

// A source-authenticated P1 finish snapshot is stable across normal 1P
// results frames. The shared timer is not: it continues advancing.
inline bool baldosa_same_one_player_finish_line(
    const UrUniracersLineSnapshot& saved,
    const UrUniracersLineSnapshot& live) noexcept {
    return saved.valid && live.valid &&
           saved.minutes == live.minutes &&
           saved.tens_seconds == live.tens_seconds &&
           saved.seconds == live.seconds &&
           saved.tenths == live.tenths &&
           saved.hundredths == live.hundredths;
}

class BaldosaPendingOnePlayerRun {
public:
    static constexpr unsigned kMaxTotalAttempts = 6;
    static constexpr std::uint64_t kRetryIntervalHostFrames = 30;

    void reset() noexcept {
        pending_.reset();
        failed_attempts_ = 0;
        next_retry_host_frame_ = 0;
        finish_line_ = {};
    }

    bool pending() const noexcept { return pending_.has_value(); }
    unsigned failed_attempts() const noexcept { return failed_attempts_; }

    // Called exclusively after an actual source-settled result's first
    // synchronous publication failed. Keep at most one bounded input trace.
    bool defer_failed_publication(
        BaldosaSettledResult result, std::uint64_t host_frame,
        const UrUniracersLineSnapshot& observed_finish_line,
        int laps_remaining) {
        if (pending_ ||
            result.kind != BaldosaSettledResultKind::TimedOnePlayerRace ||
            result.observed_result_host_frame != host_frame ||
            !observed_finish_line.valid || laps_remaining != 0 ||
            host_frame > std::numeric_limits<std::uint64_t>::max() -
                             kRetryIntervalHostFrames)
            return false;
        finish_line_ = observed_finish_line;
        pending_.emplace(std::move(result));
        failed_attempts_ = 1;
        next_retry_host_frame_ = host_frame + kRetryIntervalHostFrames;
        return true;
    }

    // Result menu visibility alone cannot prove that its source result
    // survived unchanged. Check the original stock P1 line and lap count.
    const BaldosaSettledResult* ready_for_retry(
        unsigned handed_off_players, bool race_active,
        std::uint8_t guest_menu, std::uint64_t host_frame,
        const UrUniracersLineSnapshot* live_finish_line,
        int laps_remaining) noexcept {
        if (!pending_) return nullptr;
        if (handed_off_players != 1u || race_active || guest_menu != 0x99u ||
            !live_finish_line || laps_remaining != 0 ||
            !baldosa_same_one_player_finish_line(
                finish_line_, *live_finish_line)) {
            reset();
            return nullptr;
        }
        return host_frame >= next_retry_host_frame_ ? &*pending_ : nullptr;
    }

    BaldosaRunRetryOutcome after_retry(bool published,
                                       std::uint64_t host_frame) noexcept {
        if (published) {
            reset();
            return BaldosaRunRetryOutcome::Saved;
        }
        if (!pending_ || ++failed_attempts_ >= kMaxTotalAttempts ||
            host_frame > std::numeric_limits<std::uint64_t>::max() -
                             kRetryIntervalHostFrames) {
            reset();
            return BaldosaRunRetryOutcome::Exhausted;
        }
        next_retry_host_frame_ = host_frame + kRetryIntervalHostFrames;
        return BaldosaRunRetryOutcome::Pending;
    }

private:
    std::optional<BaldosaSettledResult> pending_;
    UrUniracersLineSnapshot finish_line_{};
    unsigned failed_attempts_ = 0;
    std::uint64_t next_retry_host_frame_ = 0;
};

}  // namespace ur::product
