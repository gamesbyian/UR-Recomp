#pragma once

// Host-only, bounded I/O retry for one source-settled ordinary 2P Race.
// Never synthesizes a guest result, opponent, stock rider or extra input.
// Shares the one-player retry's attempt bound and interval, but NOT its
// source-result/participant authority or persistent storage namespace.
#include "baldosa_native_run_publish_retry.hpp"
#include "host_profile_catalog.hpp"

#include <cstdint>
#include <limits>
#include <optional>
#include <utility>

namespace ur::product {

struct BaldosaPendingTwoPlayerMatchAttempt {
    BaldosaSettledResult result;
    HostProfileCatalogEntry player1;
    HostProfileCatalogEntry player2;
};

class BaldosaPendingTwoPlayerMatch {
public:
    static constexpr unsigned kMaxTotalAttempts =
        BaldosaPendingOnePlayerRun::kMaxTotalAttempts;
    static constexpr std::uint64_t kRetryIntervalHostFrames =
        BaldosaPendingOnePlayerRun::kRetryIntervalHostFrames;

    void reset() noexcept {
        pending_.reset();
        failed_attempts_ = 0;
        next_retry_host_frame_ = 0;
    }

    bool pending() const noexcept { return pending_.has_value(); }
    unsigned failed_attempts() const noexcept { return failed_attempts_; }

    bool defer_failed_publication(
        BaldosaSettledResult result, HostProfileCatalogEntry p1,
        HostProfileCatalogEntry p2, std::uint64_t host_frame) {
        if (pending_ ||
            result.kind != BaldosaSettledResultKind::OrdinaryTwoPlayerRace ||
            !result.two_player ||
            result.observed_result_host_frame != host_frame ||
            host_frame > std::numeric_limits<std::uint64_t>::max() -
                             kRetryIntervalHostFrames ||
            p1.profile_id.empty() || p2.profile_id.empty() ||
            p1.profile_id == p2.profile_id ||
            p1.identity.rider_index != result.two_player->player1_rider ||
            p2.identity.rider_index != result.two_player->player2_rider)
            return false;
        pending_.emplace(BaldosaPendingTwoPlayerMatchAttempt{
            std::move(result), std::move(p1), std::move(p2)});
        failed_attempts_ = 1;
        next_retry_host_frame_ = host_frame + kRetryIntervalHostFrames;
        return true;
    }

    // This is evaluated after each real guest frame, not a pause-frame
    // presentation. Require source-resolved result words in unchanged SRAM,
    // the exact previously confirmed profiles, an unrestarted stock 2P
    // handoff and the actual original 0xF9 result surface.
    const BaldosaPendingTwoPlayerMatchAttempt* ready_for_retry(
        unsigned handed_off_players, bool race_active,
        std::uint8_t guest_menu, std::uint64_t host_frame,
        const ur::title::OrdinaryTwoPlayerRaceResult* live,
        const HostProfileCatalogEntry* current_p1,
        const HostProfileCatalogEntry* current_p2) noexcept {
        if (!pending_) return nullptr;
        const auto& saved = *pending_;
        const auto* result = saved.result.two_player
            ? &*saved.result.two_player : nullptr;
        if (handed_off_players != 2u || race_active ||
            guest_menu != ur::title::kOrdinaryTwoPlayerRaceResultMenu ||
            !result || !live || !current_p1 || !current_p2 ||
            !(saved.player1.identity == current_p1->identity) ||
            !(saved.player2.identity == current_p2->identity) ||
            saved.player1.profile_id != current_p1->profile_id ||
            saved.player2.profile_id != current_p2->profile_id ||
            live->player1_rider != result->player1_rider ||
            live->player2_rider != result->player2_rider ||
            live->player1_hundredths != result->player1_hundredths ||
            live->player2_hundredths != result->player2_hundredths ||
            live->outcome != result->outcome) {
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
    std::optional<BaldosaPendingTwoPlayerMatchAttempt> pending_;
    unsigned failed_attempts_ = 0;
    std::uint64_t next_retry_host_frame_ = 0;
};

} // namespace ur::product
