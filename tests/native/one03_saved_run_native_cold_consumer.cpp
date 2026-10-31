// Consume the actual source-earned ONE-03 record in a fresh native process.
// This exercises production decode, playback compatibility, immutable reload
// and replay-input staging after the separate game cold-boot process exits.
#include "completed_run_replay.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: one03_saved_run_native_cold_consumer SAVED.urrun STAGED.input\n";
        return 64;
    }
    const std::string record_path = argv[1];
    const std::string staged_path = argv[2];
    const ur::product::RunPlaybackTarget target = {
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "snesrecomp-cd5875cbdaf19f5e324272b1f8051d671fce9215-ur-sim-v1",
        "course:00", "race-1p"
    };
    const auto loaded = ur::product::load_completed_run_record_file(record_path, &target);
    if (!loaded.loaded()) {
        std::cerr << "ONE03_NATIVE_COLD_CONSUMER FAIL load=" << loaded.detail << '\n';
        return 2;
    }
    const auto reloaded = ur::product::reload_matching_completed_run_replay_record(
        record_path, *loaded.record, target);
    if (!reloaded) {
        std::cerr << "ONE03_NATIVE_COLD_CONSUMER FAIL immutable_replay_reload\n";
        return 3;
    }
    std::string detail;
    if (!ur::product::stage_completed_run_replay_input_file(
            staged_path, *reloaded, &detail)) {
        std::cerr << "ONE03_NATIVE_COLD_CONSUMER FAIL stage=" << detail << '\n';
        return 4;
    }
    std::ifstream staged(staged_path, std::ios::binary);
    if (!staged) {
        std::cerr << "ONE03_NATIVE_COLD_CONSUMER FAIL staged_file_missing\n";
        return 5;
    }
    const std::string actual{std::istreambuf_iterator<char>(staged),
                             std::istreambuf_iterator<char>()};
    if (staged.bad() || actual.empty() ||
            actual != ur::product::encode_completed_run_input_file(*reloaded)) {
        std::cerr << "ONE03_NATIVE_COLD_CONSUMER FAIL staged_input_mismatch\n";
        return 6;
    }
    std::cout << "ONE03_NATIVE_COLD_CONSUMER PASS course="
              << reloaded->provenance.course_id
              << " inputs=" << reloaded->inputs.size()
              << " replay_bytes=" << actual.size() << '\n';
    return 0;
}
