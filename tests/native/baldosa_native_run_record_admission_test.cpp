#include "baldosa_native_run_record_admission.hpp"
#include "run_record_capture_policy.hpp"
#include "completed_run_store.hpp"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <unistd.h>
#include <string>

using namespace ur::product;

int main() {
    BaldosaSettledResult settled{};
    settled.kind = BaldosaSettledResultKind::TimedOnePlayerRace;
    settled.first_race_host_frame = 100;
    settled.observed_result_host_frame = 104;
    settled.p1_finish_ticks60 = 740;
    settled.course_index = 1;
    settled.captured_input_frames = 4;
    settled.mapped_inputs = {{0, 2, 0x11, 0}, {3, 1, 0x20, 0}};
    BaldosaRunRecordAuthority signed_p1{true, false};

    // A guessed guest result, anonymous player or wrong course cannot
    // create a canonical record, even though the raw codec can encode one.
    assert(!assemble_baldosa_native_run_record(settled, {}));
    const auto one = assemble_baldosa_native_run_record(settled, signed_p1);
    assert(one);
    assert(one->provenance.mode == "race-1p");
    assert(one->provenance.course_id == "course:01");
    assert(one->provenance.build_compat_id == kBaldosaNativeRunCompatId);
    assert(one->frame_count == 4);
    // RunRecordInputRun has no equality operator; compare exact source fields.
    assert(one->inputs.size() == 2);
    assert(one->inputs[0].p1_mask == 0x11u);
    assert(one->inputs[1].start_frame == 3);
    assert(one->elapsed_ticks60 == 740);
    assert(one->splits.size() == 1);
    assert(one->splits[0].id == "finish");
    const auto encoded = encode_completed_run_record(*one);
    assert(!encoded.empty());
    const auto readback = decode_completed_run_record(encoded);
    assert(readback.loaded());
    assert(readback.record->frame_count == 4);
    const RunPlaybackTarget correct{
        one->provenance.game_id, one->provenance.rom_sha256,
        one->provenance.build_compat_id, one->provenance.course_id,
        one->provenance.mode};
    assert(compatible_for_playback(*one, correct));
    const RunPlaybackTarget legacy{
        correct.game_id, correct.rom_sha256, "snesrecomp-legacy",
        correct.course_id, correct.mode};
    assert(!compatible_for_playback(*one, legacy));
    // Exercise the *same* immutable publication/inspection codecs as the
    // Modern Records browser. This is a synthetic fixture, NOT an actual
    // gameplay-event acceptance or permission to publish in shipping code.
    namespace fs = std::filesystem;
    const fs::path root = fs::temp_directory_path() /
        ("ur-baldosa-admission-unit-" + std::to_string(getpid()) + "-" +
         std::to_string(
             std::chrono::steady_clock::now().time_since_epoch().count()));
    const fs::path directory = root / "runs" / "fixture-rider";
    std::string stored, detail;
    assert(append_completed_run_record(
        directory.string(), *one, &stored, &detail));
    const auto archives = inspect_completed_run_record_artifacts(
        directory.string());
    assert(archives.size() == 1);
    assert(archives.front().loaded());
    const auto loaded = load_completed_run_record_file(stored, &correct);
    assert(loaded.loaded());
    assert(loaded.record->elapsed_ticks60 == 740);
    assert(loaded.record->inputs.size() == 2);
    assert(load_completed_run_record_file(stored, &legacy).status ==
           RunRecordLoadStatus::Incompatible);
    fs::remove_all(root);


    auto invalid = settled;
    invalid.course_index = 2; // circuit, not Race
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.course_index = 0; // no source decoded course
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.course_index = 46;
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.first_race_host_frame = 0; // host frames are one-based
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.observed_result_host_frame = 103; // missing real guest sample
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.p1_finish_ticks60 = 0;
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.p1_finish_ticks60 = 36000u; // original race timer max 9:59
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.mapped_inputs[1].start_frame = 1; // overlapping RLE
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.mapped_inputs[1].p2_mask = 0xf000u; // outside 12-bit mask
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));
    invalid = settled;
    invalid.two_player = ur::title::OrdinaryTwoPlayerRaceResult{};
    assert(!assemble_baldosa_native_run_record(invalid, signed_p1));

    BaldosaSettledResult two = settled;
    two.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    two.p1_finish_ticks60 = 0;
    two.two_player = ur::title::OrdinaryTwoPlayerRaceResult{};
    two.two_player->player1_rider = 0;
    two.two_player->player2_rider = 1;
    two.two_player->player1_hundredths = 874;
    two.two_player->player2_hundredths = 913;
    two.two_player->outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    two.mapped_inputs = {{0, 2, 0x5, 0x4}, {2, 2, 0, 0x4}};
    assert(!assemble_baldosa_native_run_record(two, signed_p1));
    const BaldosaRunRecordAuthority signed_two{true, true};
    const auto match = assemble_baldosa_native_run_record(two, signed_two);
    assert(match);
    assert(match->provenance.mode == "race-2p");
    assert(match->elapsed_ticks60 ==
        ordinary_two_player_carrier_elapsed_ticks60(*two.two_player));
    assert(match->splits.empty());
    assert(match->inputs.size() == 2);
    assert(!encode_completed_run_record(*match).empty());
    two.two_player->player1_rider = 16; // invalid source rider
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player1_rider = 0;
    two.two_player->player2_rider = 16;
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player2_rider = 1;
    two.two_player->outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw; // inconsistent win
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    two.two_player->player1_hundredths = 60001; // invalid guest time
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player1_hundredths = 874;
    two.two_player->player2_hundredths = 873; // P2 actually won
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player2_hundredths = 913;
    assert(assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player1_hundredths = 0; // impossible 0.00 finish
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player1_hundredths = 874;
    two.two_player->player2_hundredths = 0;
    assert(!assemble_baldosa_native_run_record(two, signed_two));
    two.two_player->player2_hundredths = 913;
    two.two_player->player1_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    two.two_player->player2_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    assert(!assemble_baldosa_native_run_record(two, signed_two));

    std::puts("PASS: source-settled Baldosa results admit only canonical authorized in-memory .urrun");
}
