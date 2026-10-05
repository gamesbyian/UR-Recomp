#include "uniracers_challenge_completion_runtime.hpp"

#include "uniracers_challenge_generation_bridge.h"

namespace ur::title {
namespace {

struct ArmedCompletionOverrides {
    ChallengeQualificationRequest qualification{};
    ChallengeAwardRequest award{};
    const std::uint8_t* wram = nullptr;
    std::size_t wram_size = 0;
    const std::uint8_t* sram = nullptr;
    std::size_t sram_size = 0;
    bool active = false;
    bool has_award_override = false;
    ChallengeQualificationStatus last_qualification =
        ChallengeQualificationStatus::NoOverride;
    ChallengeAwardStatus last_award =
        ChallengeAwardStatus::NoOverride;
};

ArmedCompletionOverrides g_completion;

void clear_internal() noexcept {
    g_completion.active = false;
    g_completion.has_award_override = false;
    g_completion.wram = nullptr;
    g_completion.wram_size = 0;
    g_completion.sram = nullptr;
    g_completion.sram_size = 0;
    ur_uniracers_set_challenge_qualification_generation_filter(nullptr);
    ur_uniracers_set_challenge_award_previous_medal_filter(nullptr);
}

extern "C" std::uint8_t resolve_qualification_override(
    std::uint8_t stock_generation) {
    if (!g_completion.active) return stock_generation;

    const auto decision = resolve_stunt_qualification_generation(
        &g_completion.qualification,
        stock_generation,
        g_completion.wram,
        g_completion.wram_size,
        g_completion.sram,
        g_completion.sram_size);
    g_completion.last_qualification = decision.status;

    // A stale selected-tour context is terminal. Do not let it survive to a
    // later stunt or award transaction.
    if (!decision.applied()) {
        clear_internal();
    }
    return decision.generation;
}

extern "C" std::uint8_t resolve_award_override(
    std::uint8_t stock_previous_medal) {
    if (!g_completion.active) return stock_previous_medal;

    std::uint8_t out = stock_previous_medal;
    if (g_completion.has_award_override) {
        const auto decision = resolve_challenge_award_previous_medal(
            &g_completion.award,
            stock_previous_medal,
            g_completion.wram,
            g_completion.wram_size,
            g_completion.sram,
            g_completion.sram_size);
        g_completion.last_award = decision.status;
        out = decision.previous_medal;
    } else {
        g_completion.last_award = ChallengeAwardStatus::NoOverride;
    }

    // Reaching the stock award boundary ends this selected-tour lifecycle
    // whether the replay changes persistent completion or not.
    clear_internal();
    return out;
}

bool matching_requests(
    const ChallengeQualificationRequest& qualification,
    const ChallengeAwardRequest& award) noexcept {
    return qualification.rider_index == award.rider_index &&
           qualification.tour_row == award.tour_row &&
           qualification.expected_persisted_medal ==
               award.expected_persisted_medal;
}

}  // namespace

ChallengeCompletionArmStatus arm_challenge_completion_overrides(
    const ChallengeQualificationRequest& qualification,
    const ChallengeAwardRequest* award,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (g_completion.active) {
        return ChallengeCompletionArmStatus::AlreadyArmed;
    }
    if (!valid_challenge_qualification_request(qualification)) {
        return ChallengeCompletionArmStatus::InvalidQualificationRequest;
    }
    if (award &&
        (!valid_challenge_award_request(*award) ||
         !matching_requests(qualification, *award))) {
        return ChallengeCompletionArmStatus::InvalidAwardRequest;
    }
    if (!wram || !sram || wram_size == 0 || sram_size == 0) {
        return ChallengeCompletionArmStatus::InvalidBuffers;
    }

    g_completion.qualification = qualification;
    if (award) g_completion.award = *award;
    g_completion.wram = wram;
    g_completion.wram_size = wram_size;
    g_completion.sram = sram;
    g_completion.sram_size = sram_size;
    g_completion.active = true;
    g_completion.has_award_override = award != nullptr;
    g_completion.last_qualification =
        ChallengeQualificationStatus::NoOverride;
    g_completion.last_award = ChallengeAwardStatus::NoOverride;

    ur_uniracers_set_challenge_qualification_generation_filter(
        &resolve_qualification_override);
    // Install even when no override is required so the stock award boundary
    // automatically retires lower/equal-tier replay context.
    ur_uniracers_set_challenge_award_previous_medal_filter(
        &resolve_award_override);
    return ChallengeCompletionArmStatus::Armed;
}

void clear_challenge_completion_overrides() noexcept {
    clear_internal();
}

bool challenge_completion_overrides_active() noexcept {
    return g_completion.active;
}

ChallengeQualificationStatus
challenge_completion_last_qualification_status() noexcept {
    return g_completion.last_qualification;
}

ChallengeAwardStatus
challenge_completion_last_award_status() noexcept {
    return g_completion.last_award;
}

}  // namespace ur::title
