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

class BaldosaPendingOnePlayerRun {
public:
    static constexpr unsigned kMaxTotalAttempts = 6;
    static constexpr std::uint64_t kRetryIntervalHostFrames = 30;

    void reset() noexcept {
        pending_.reset();
        failed_attempts_ = 0;
        next_retry_host_frame_ = 0;
    }

    bool pending() const noexcept { return pending_.has_value(); }
    unsigned failed_attempts() const noexcept { return failed_attempts_; }

    // Called exclusively after an actual source-settled result's first
    // synchronous publication failed. Keep at most one bounded input trace.
    bool defer_failed_publication(BaldosaSettledResult result,
                                  std::uint64_t host_frame) {
        if (pending_ ||
            result.kind != BaldosaSettledResultKind::TimedOnePlayerRace ||
            result.observed_result_host_frame != host_frame ||
            host_frame > std::numeric_limits<std::uint64_t>::max() -
                             kRetryIntervalHostFrames)
            return false;
        pending_.emplace(std::move(result));
        failed_attempts_ = 1;
        next_retry_host_frame_ = host_frame + kRetryIntervalHostFrames;
        return true;
    }

    // Any departure, new race, or change in the root's acknowledged seat
    // revokes the pending result. Never replay it into another guest session.
    const BaldosaSettledResult* ready_for_retry(
        unsigned handed_off_players, bool race_active,
        std::uint8_t guest_menu, std::uint64_t host_frame) noexcept {
        if (!pending_) return nullptr;
        if (handed_off_players != 1u || race_active || guest_menu != 0x99u) {
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
    unsigned failed_attempts_ = 0;
    std::uint64_t next_retry_host_frame_ = 0;
};

}  // namespace ur::product
