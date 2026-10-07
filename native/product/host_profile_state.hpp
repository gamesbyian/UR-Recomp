#pragma once

#include "host_product_state.hpp"
#include "completed_run_ghost_target.hpp"
#include "modern_racer_identity.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

constexpr std::size_t kStockSramBytes = 8192;
constexpr std::size_t kTourTrackCount = 5;

struct HostTourContinuation {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t medal_value = 0;
    std::array<std::uint8_t, kTourTrackCount> qualified{};

    bool operator==(const HostTourContinuation& other) const noexcept {
        return rider_index == other.rider_index &&
               tour_row == other.tour_row &&
               medal_value == other.medal_value &&
               qualified == other.qualified;
    }

    bool operator!=(const HostTourContinuation& other) const noexcept {
        return !(*this == other);
    }
};

bool valid_tour_continuation(const HostTourContinuation& value) noexcept;

// Stock course catalog size. A profile's Recent Course is a canonical
// zero-based course id observed authoritatively while that profile raced; it
// is navigation metadata only and never progression.
constexpr std::uint8_t kHostProfileCourseCount = 45;

constexpr bool valid_recent_track(std::uint8_t track_id) noexcept {
    return track_id < kHostProfileCourseCount;
}

struct HostProfileState {
    static constexpr std::uint32_t schema_version = 5;

    std::string profile_id;
    std::uint64_t autosave_generation = 0;
    std::optional<std::array<std::uint8_t, kStockSramBytes>> stock_sram;
    std::optional<HostTourContinuation> tour_continuation;
    CompletedRunGhostTarget ghost_target = CompletedRunGhostTarget::Off;
    std::optional<HostRacerIdentity> racer_identity;
    std::optional<std::uint8_t> recent_track;

    bool operator==(const HostProfileState& other) const noexcept {
        return profile_id == other.profile_id &&
               autosave_generation == other.autosave_generation &&
               stock_sram == other.stock_sram &&
               tour_continuation == other.tour_continuation &&
               ghost_target == other.ghost_target &&
               racer_identity == other.racer_identity &&
               recent_track == other.recent_track;
    }
};

struct HostProfileDecodeResult {
    std::optional<HostProfileState> state;
    bool migrated = false;
    std::string error;

    explicit operator bool() const noexcept { return state.has_value(); }
};

enum class HostProfileTransferStatus : std::uint8_t {
    Applied = 0,
    RejectedByPolicy = 1,
    InvalidBuffer = 2,
    MissingSnapshot = 3,
};

std::optional<HostProfileState> make_default_host_profile_state(
    std::string_view profile_id);
std::string encode_host_profile_state(const HostProfileState& state);
HostProfileDecodeResult decode_host_profile_state(std::string_view encoded);

HostProfileTransferStatus capture_stock_sram_for_profile(
    ExecutionMode mode,
    HostProfileState& state,
    const std::uint8_t* data,
    std::size_t size) noexcept;

HostProfileTransferStatus restore_stock_sram_from_profile(
    ExecutionMode mode,
    const HostProfileState& state,
    std::uint8_t* data,
    std::size_t size) noexcept;

}  // namespace ur::product
