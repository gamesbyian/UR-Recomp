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
    assert(default_state->ghost_target == CompletedRunGhostTarget::Off);
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

    HostTourContinuation continuation;
    continuation.rider_index = 3;
    continuation.tour_row = 4;
    continuation.medal_value = 1;
    continuation.qualified = {1, 0, 1, 0, 0};
    assert(valid_tour_continuation(continuation));
    state.tour_continuation = continuation;
    state.ghost_target = CompletedRunGhostTarget::PersonalBest;
    state.racer_identity = HostRacerIdentity{"SONIC", 7};

    const std::string encoded = encode_host_profile_state(state);
    assert(!encoded.empty());
    const auto decoded = decode_host_profile_state(encoded);
    assert(decoded);
    assert(*decoded.state == state);
    assert(!decoded.migrated);
    assert(decoded.state->ghost_target == CompletedRunGhostTarget::PersonalBest);
    assert(decoded.state->racer_identity);
    assert(decoded.state->racer_identity->name == "SONIC");
    assert(decoded.state->racer_identity->rider_index == 7);
    assert(encoded.rfind("UR-HOST-PROFILE/5\n", 0) == 0);
    assert(encoded.find("recent_track=\n") != std::string::npos);
    assert(!decoded.state->recent_track);
    assert(encoded.find("ghost_target=personal-best\n") != std::string::npos);
    assert(encoded.find("racer_name=SONIC\n") != std::string::npos);
    assert(encoded.find("racer_index=7\n") != std::string::npos);

    const auto legacy = decode_host_profile_state(
        "UR-HOST-PROFILE/1\n"
        "profile=profile.alpha\n"
        "generation=7\n"
        "stock_sram=\n");
    assert(legacy);
    assert(legacy.migrated);
    assert(legacy.state->autosave_generation == 7);
    assert(!legacy.state->tour_continuation);
    assert(legacy.state->ghost_target == CompletedRunGhostTarget::Off);
    assert(encode_host_profile_state(*legacy.state).rfind(
               "UR-HOST-PROFILE/5\n", 0) == 0);

    const auto legacy_v2 = decode_host_profile_state(
        "UR-HOST-PROFILE/2\n"
        "profile=profile.alpha\n"
        "generation=8\n"
        "stock_sram=\n"
        "tour_resume=3:4:1:10100\n");
    assert(legacy_v2);
    assert(legacy_v2.migrated);
    assert(legacy_v2.state->autosave_generation == 8);
    assert(legacy_v2.state->tour_continuation);
    assert(legacy_v2.state->ghost_target == CompletedRunGhostTarget::Off);
    assert(!legacy_v2.state->racer_identity);

    const auto legacy_v3 = decode_host_profile_state(
        "UR-HOST-PROFILE/3\n"
        "profile=profile.alpha\n"
        "generation=9\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=previous\n");
    assert(legacy_v3);
    assert(legacy_v3.migrated);
    assert(legacy_v3.state->ghost_target == CompletedRunGhostTarget::Previous);
    assert(!legacy_v3.state->racer_identity);

    const auto incomplete_identity = decode_host_profile_state(
        "UR-HOST-PROFILE/4\n"
        "profile=profile.alpha\n"
        "generation=1\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=off\n"
        "racer_name=MIKE\n"
        "racer_index=\n");
    assert(!incomplete_identity);

    // v4 files remain readable and gain no Recent Course.
    const auto legacy_v4 = decode_host_profile_state(
        "UR-HOST-PROFILE/4\n"
        "profile=profile.alpha\n"
        "generation=3\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=off\n"
        "racer_name=MIKE\n"
        "racer_index=0\n");
    assert(legacy_v4);
    assert(legacy_v4.migrated);
    assert(legacy_v4.state->racer_identity);
    assert(!legacy_v4.state->recent_track);
    // A v4 header must not smuggle in the v5-only field.
    assert(!decode_host_profile_state(
        "UR-HOST-PROFILE/4\n"
        "profile=profile.alpha\n"
        "generation=3\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=off\n"
        "racer_name=\n"
        "racer_index=\n"
        "recent_track=4\n"));

    // Recent Course round-trips byte-stably at both catalog bounds.
    for (const std::uint8_t track : {std::uint8_t{0}, std::uint8_t{44}}) {
        HostProfileState recent = state;
        recent.recent_track = track;
        const std::string recent_encoded = encode_host_profile_state(recent);
        assert(!recent_encoded.empty());
        const auto recent_decoded = decode_host_profile_state(recent_encoded);
        assert(recent_decoded);
        assert(!recent_decoded.migrated);
        assert(*recent_decoded.state == recent);
        assert(encode_host_profile_state(*recent_decoded.state) ==
               recent_encoded);
    }

    // Out-of-catalog values are never written and fail closed on read.
    HostProfileState out_of_range = state;
    out_of_range.recent_track = 45;
    assert(encode_host_profile_state(out_of_range).empty());
    const char* const kBadRecent[] = {"45", "255", "256", "-1", "x", "4 ", "04x"};
    for (const char* bad : kBadRecent) {
        const std::string text =
            std::string("UR-HOST-PROFILE/5\n"
                        "profile=profile.alpha\n"
                        "generation=3\n"
                        "stock_sram=\n"
                        "tour_resume=\n"
                        "ghost_target=off\n"
                        "racer_name=\n"
                        "racer_index=\n"
                        "recent_track=") + bad + "\n";
        assert(!decode_host_profile_state(text));
    }
    // v5 requires the field to be present (empty means none).
    assert(!decode_host_profile_state(
        "UR-HOST-PROFILE/5\n"
        "profile=profile.alpha\n"
        "generation=3\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=off\n"
        "racer_name=\n"
        "racer_index=\n"));

    HostTourContinuation no_progress = continuation;
    no_progress.qualified = {0, 0, 0, 0, 0};
    assert(!valid_tour_continuation(no_progress));
    HostTourContinuation completed = continuation;
    completed.qualified = {1, 1, 1, 1, 1};
    assert(!valid_tour_continuation(completed));
    HostTourContinuation bad_rider = continuation;
    bad_rider.rider_index = 16;
    assert(!valid_tour_continuation(bad_rider));

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

    const auto invalid_ghost = decode_host_profile_state(
        "UR-HOST-PROFILE/3\n"
        "profile=profile.alpha\n"
        "generation=1\n"
        "stock_sram=\n"
        "tour_resume=\n"
        "ghost_target=fastest\n");
    assert(!invalid_ghost);

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
