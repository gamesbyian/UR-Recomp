#include "host_profile_state.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <string>

using namespace ur::product;

int main() {
    const auto default_state = make_default_host_profile_state("profile.alpha");
    assert(default_state);
    assert(default_state->profile_id == "profile.alpha");
    assert(default_state->autosave_generation == 0);
    assert(!default_state->stock_sram);
    assert(!make_default_host_profile_state("bad/profile"));

    HostProfileState state = *default_state;

    std::array<std::uint8_t, kStockSramBytes> source{};
    for (std::size_t i = 0; i < source.size(); ++i) {
        source[i] = static_cast<std::uint8_t>((i * 37u + 11u) & 0xffu);
    }

    assert(capture_stock_sram_for_profile(
               ExecutionMode::Modern,
               state,
               source.data(),
               source.size()) == HostProfileTransferStatus::Applied);
    assert(state.autosave_generation == 1);
    assert(state.stock_sram.has_value());

    const std::string encoded = encode_host_profile_state(state);
    assert(!encoded.empty());
    const auto decoded = decode_host_profile_state(encoded);
    assert(decoded);
    assert(*decoded.state == state);

    std::array<std::uint8_t, kStockSramBytes> restored{};
    assert(restore_stock_sram_from_profile(
               ExecutionMode::Modern,
               *decoded.state,
               restored.data(),
               restored.size()) == HostProfileTransferStatus::Applied);
    assert(restored == source);

    const auto malformed = decode_host_profile_state(
        "UR-HOST-PROFILE/1\nprofile=profile.alpha\ngeneration=1\nstock_sram=xyz\n");
    assert(!malformed);

    HostProfileState authentic;
    authentic.profile_id = "profile.authentic";
    assert(capture_stock_sram_for_profile(
               ExecutionMode::Authentic,
               authentic,
               source.data(),
               source.size()) == HostProfileTransferStatus::RejectedByPolicy);
    assert(!authentic.stock_sram);
    assert(authentic.autosave_generation == 0);

    std::array<std::uint8_t, kStockSramBytes> authentic_target{};
    authentic_target.fill(0x5a);
    const auto authentic_before = authentic_target;
    assert(restore_stock_sram_from_profile(
               ExecutionMode::Authentic,
               state,
               authentic_target.data(),
               authentic_target.size()) == HostProfileTransferStatus::RejectedByPolicy);
    assert(authentic_target == authentic_before);

    HostProfileState empty;
    empty.profile_id = "profile.empty";
    assert(restore_stock_sram_from_profile(
               ExecutionMode::Modern,
               empty,
               restored.data(),
               restored.size()) == HostProfileTransferStatus::MissingSnapshot);

    return 0;
}
