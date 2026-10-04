#include "completed_run_record.hpp"

#include <iostream>
#include <string>

using namespace ur::product;

namespace {

RunPlaybackTarget target_for(const CompletedRunRecord& record) {
    return {
        record.provenance.game_id,
        record.provenance.rom_sha256,
        record.provenance.build_compat_id,
        record.provenance.course_id,
        record.provenance.mode,
    };
}

bool same_inputs(
    const CompletedRunRecord& a,
    const CompletedRunRecord& b) {
    if (a.inputs.size() != b.inputs.size()) return false;
    for (std::size_t i = 0; i < a.inputs.size(); ++i) {
        const auto& x = a.inputs[i];
        const auto& y = b.inputs[i];
        if (x.start_frame != y.start_frame ||
            x.duration != y.duration ||
            x.p1_mask != y.p1_mask ||
            x.p2_mask != y.p2_mask) return false;
    }
    return true;
}

bool same_splits(
    const CompletedRunRecord& a,
    const CompletedRunRecord& b) {
    if (a.splits.size() != b.splits.size()) return false;
    for (std::size_t i = 0; i < a.splits.size(); ++i) {
        if (a.splits[i].id != b.splits[i].id ||
            a.splits[i].ticks60 != b.splits[i].ticks60) return false;
    }
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 3) return 64;
    const auto original = load_completed_run_record_file(argv[1]);
    const auto replayed = load_completed_run_record_file(argv[2]);
    if (!original.loaded() || !replayed.loaded()) {
        std::cerr << "record load failed\n";
        return 2;
    }

    std::string detail;
    if (!compatible_for_playback(
            *replayed.record, target_for(*original.record), &detail)) {
        std::cerr << detail << "\n";
        return 3;
    }
    if (original.record->elapsed_ticks60 != replayed.record->elapsed_ticks60 ||
        original.record->frame_count != replayed.record->frame_count ||
        !same_splits(*original.record, *replayed.record) ||
        !same_inputs(*original.record, *replayed.record)) {
        std::cerr << "replayed run differs from captured run\n";
        return 4;
    }

    std::cout
        << "UR_RUN_REPLAY_COMPARE PASS course="
        << original.record->provenance.course_id
        << " elapsed_ticks60=" << original.record->elapsed_ticks60
        << " inputs=" << original.record->inputs.size()
        << " splits=" << original.record->splits.size()
        << "\n";
    return 0;
}
