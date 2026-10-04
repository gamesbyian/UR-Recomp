#pragma once

#include "host_product_state.hpp"

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
};

bool valid_tour_continuation(const HostTourContinuation& value) noexcept;

struct HostProfileState {
    static constexpr std::uint32_t schema_version = 2;

    std::string profile_id;
    std::uint64_t autosave_generation = 0;
    std::optional<std::array<std::uint8_t, kStockSramBytes>> stock_sram;
    std::optional<HostTourContinuation> tour_continuation;

    bool operator==(const HostProfileState& other) const noexcept {
        return profile_id == other.profile_id &&
               autosave_generation == other.autosave_generation &&
               stock_sram == other.stock_sram &&
               tour_continuation == other.tour_continuation;
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
