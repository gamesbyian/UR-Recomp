#include "uniracers_challenge_generation_runtime.hpp"

#include "uniracers_challenge_generation_bridge.h"

namespace ur::title {
namespace {

struct ArmedGenerationOverride {
    ChallengeGenerationRequest request{};
    const std::uint8_t* wram = nullptr;
    std::size_t wram_size = 0;
    const std::uint8_t* sram = nullptr;
    std::size_t sram_size = 0;
    bool active = false;
    ChallengeGenerationStatus last_status =
        ChallengeGenerationStatus::NoOverride;
};

ArmedGenerationOverride g_override;

extern "C" std::uint8_t consume_generation_override(
    std::uint8_t stock_generation) {
    if (!g_override.active) return stock_generation;

    const auto decision = resolve_challenge_generation_snapshot(
        &g_override.request,
        stock_generation,
        g_override.wram,
        g_override.wram_size,
        g_override.sram,
        g_override.sram_size);

    // The request belongs to exactly one stock tour-confirm snapshot writer.
    // Consume it on success or failure so stale policy can never leak forward.
    g_override.last_status = decision.status;
    g_override.active = false;
    ur_uniracers_set_challenge_generation_filter(nullptr);
    return decision.generation;
}

}  // namespace

ChallengeGenerationArmStatus arm_challenge_generation_override(
    const ChallengeGenerationRequest& request,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (g_override.active) {
        return ChallengeGenerationArmStatus::AlreadyArmed;
    }
    if (!valid_challenge_generation_request(request)) {
        return ChallengeGenerationArmStatus::InvalidRequest;
    }
    if (!wram || !sram || wram_size == 0 || sram_size == 0) {
        return ChallengeGenerationArmStatus::InvalidBuffers;
    }

    g_override.request = request;
    g_override.wram = wram;
    g_override.wram_size = wram_size;
    g_override.sram = sram;
    g_override.sram_size = sram_size;
    g_override.last_status = ChallengeGenerationStatus::NoOverride;
    g_override.active = true;
    ur_uniracers_set_challenge_generation_filter(
        &consume_generation_override);
    return ChallengeGenerationArmStatus::Armed;
}

void clear_challenge_generation_override() noexcept {
    g_override.active = false;
    g_override.wram = nullptr;
    g_override.wram_size = 0;
    g_override.sram = nullptr;
    g_override.sram_size = 0;
    ur_uniracers_set_challenge_generation_filter(nullptr);
}

bool challenge_generation_override_active() noexcept {
    return g_override.active;
}

ChallengeGenerationStatus
challenge_generation_override_last_status() noexcept {
    return g_override.last_status;
}

}  // namespace ur::title
