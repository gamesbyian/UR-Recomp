#include "completed_run_record.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord make_record() {
    CompletedRunRecorder recorder;
    for (std::uint64_t f = 0; f < 120; ++f) recorder.observe_input_frame(f, 0x080);
    for (std::uint64_t f = 120; f < 144; ++f) recorder.observe_input_frame(f, 0x081);
    for (std::uint64_t f = 144; f < 168; ++f) recorder.observe_input_frame(f, 0x080);

    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 1713;
    record.frame_count = 168;
    record.splits = {{"half", 856}, {"finish", 1713}};
    record.inputs = recorder.inputs();
    return record;
}

RunPlaybackTarget target() {
    const auto p = make_record().provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 3 && argc != 4) return 64;
    const std::string mode = argv[1];
    const std::string path = argv[2];
    if (argc == 4 && mode != "write") return 64;

    if (mode == "write") {
        // Optional acceptance-fixture frame count: preserve the same exact
        // controller stream and finish while changing only the capture window.
        auto record = make_record();
        if (argc == 4) record.frame_count = std::stoull(argv[3]);
        std::string detail;
        if (!save_completed_run_record_file(path, record, &detail)) {
            std::cerr << detail << "\n";
            return 2;
        }
        return 0;
    }

    if (mode == "verify") {
        const auto playback_target = target();
        const auto loaded = load_completed_run_record_file(path, &playback_target);
        if (!loaded.loaded()) {
            std::cerr << loaded.detail << "\n";
            return 3;
        }
        if (loaded.record->elapsed_ticks60 != 1713 ||
            loaded.record->frame_count != 168 ||
            loaded.record->splits.size() != 2 ||
            run_record_input_at(*loaded.record, 0).first != 0x080 ||
            run_record_input_at(*loaded.record, 120).first != 0x081 ||
            run_record_input_at(*loaded.record, 144).first != 0x080 ||
            run_record_input_at(*loaded.record, 168).first != 0) {
            return 4;
        }
        std::cout << encode_completed_run_input_file(*loaded.record);
        return 0;
    }

    return 64;
}
