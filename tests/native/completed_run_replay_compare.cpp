#include "completed_run_record.hpp"

#include <algorithm>
#include <cctype>
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

bool report_provenance(
    const CompletedRunRecord& a,
    const CompletedRunRecord& b) {
    bool same = true;
    const auto report = [&](const char* field, const std::string& x, const std::string& y) {
        if (x == y) return;
        same = false;
        std::cerr << "DIFF provenance." << field
                  << " original=" << x
                  << " replayed=" << y << "\n";
    };
    report("game_id", a.provenance.game_id, b.provenance.game_id);
    report("rom_sha256", a.provenance.rom_sha256, b.provenance.rom_sha256);
    report("build_compat_id", a.provenance.build_compat_id, b.provenance.build_compat_id);
    report("course_id", a.provenance.course_id, b.provenance.course_id);
    report("mode", a.provenance.mode, b.provenance.mode);
    return same;
}

bool report_terminal_digest(
    const CompletedRunRecord& original,
    const CompletedRunRecord& replayed) {
    const auto& left = original.terminal_simulation_digest;
    const auto& right = replayed.terminal_simulation_digest;
    // Digests encode bytes as hex. The canonical v1 parser admits uppercase
    // and lowercase A-F, so compare the semantic digest, not letter casing.
    if (left.size() == right.size() &&
        std::equal(left.begin(), left.end(), right.begin(),
            [](unsigned char a, unsigned char b) {
                return std::tolower(a) == std::tolower(b);
            })) {
        return true;
    }
    // An absent digest in both historical artifacts is acceptable. Once
    // either side claims terminal-state evidence, the other side must agree.
    std::cerr << "DIFF terminal_simulation_digest original="
              << (left.empty() ? "(absent)" : left)
              << " replayed=" << (right.empty() ? "(absent)" : right)
              << "\n";
    return false;
}

bool report_inputs(
    const CompletedRunRecord& a,
    const CompletedRunRecord& b) {
    bool same = true;
    if (a.inputs.size() != b.inputs.size()) {
        same = false;
        std::cerr << "DIFF inputs.size original=" << a.inputs.size()
                  << " replayed=" << b.inputs.size() << "\n";
    }
    const std::size_t count = a.inputs.size() < b.inputs.size()
        ? a.inputs.size() : b.inputs.size();
    for (std::size_t i = 0; i < count; ++i) {
        const auto& x = a.inputs[i];
        const auto& y = b.inputs[i];
        if (x.start_frame == y.start_frame &&
            x.duration == y.duration &&
            x.p1_mask == y.p1_mask &&
            x.p2_mask == y.p2_mask) {
            continue;
        }
        same = false;
        std::cerr << "DIFF input[" << i << "]"
                  << " original={start=" << x.start_frame
                  << ",duration=" << x.duration
                  << ",p1=" << x.p1_mask
                  << ",p2=" << x.p2_mask
                  << "} replayed={start=" << y.start_frame
                  << ",duration=" << y.duration
                  << ",p1=" << y.p1_mask
                  << ",p2=" << y.p2_mask
                  << "}\n";
    }
    return same;
}

bool report_splits(
    const CompletedRunRecord& a,
    const CompletedRunRecord& b) {
    bool same = true;
    if (a.splits.size() != b.splits.size()) {
        same = false;
        std::cerr << "DIFF splits.size original=" << a.splits.size()
                  << " replayed=" << b.splits.size() << "\n";
    }
    const std::size_t count = a.splits.size() < b.splits.size()
        ? a.splits.size() : b.splits.size();
    for (std::size_t i = 0; i < count; ++i) {
        const auto& x = a.splits[i];
        const auto& y = b.splits[i];
        if (x.id == y.id && x.ticks60 == y.ticks60) continue;
        same = false;
        std::cerr << "DIFF split[" << i << "]"
                  << " original={id=" << x.id << ",ticks60=" << x.ticks60
                  << "} replayed={id=" << y.id << ",ticks60=" << y.ticks60
                  << "}\n";
    }
    return same;
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
        std::cerr << "playback compatibility failed: " << detail << "\n";
        (void)report_provenance(*original.record, *replayed.record);
        return 3;
    }

    bool same = true;
    same = report_provenance(*original.record, *replayed.record) && same;
    same = report_terminal_digest(*original.record, *replayed.record) && same;
    if (original.record->elapsed_ticks60 != replayed.record->elapsed_ticks60) {
        same = false;
        std::cerr << "DIFF elapsed_ticks60 original="
                  << original.record->elapsed_ticks60
                  << " replayed=" << replayed.record->elapsed_ticks60 << "\n";
    }
    if (original.record->frame_count != replayed.record->frame_count) {
        std::cerr << "INFO frame_count differs across lifecycle observation "
                  << "boundaries original=" << original.record->frame_count
                  << " replayed=" << replayed.record->frame_count << "\n";
    }
    same = report_splits(*original.record, *replayed.record) && same;
    same = report_inputs(*original.record, *replayed.record) && same;

    if (!same) {
        std::cerr << "replayed run differs from captured run\n";
        return 4;
    }

    std::cout
        << "UR_RUN_REPLAY_COMPARE PASS course="
        << original.record->provenance.course_id
        << " elapsed_ticks60=" << original.record->elapsed_ticks60
        << " frame_count=" << original.record->frame_count
        << " inputs=" << original.record->inputs.size()
        << " splits=" << original.record->splits.size()
        << "\n";
    return 0;
}
