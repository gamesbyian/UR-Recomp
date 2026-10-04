#include "completed_run_ghost_trace.hpp"

#include <cassert>
#include <string>
#include <filesystem>

using namespace ur::product;

namespace {

CompletedRunRecord run_record() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 120;
    record.frame_count = 3;
    record.splits = {{"finish", 120}};
    record.inputs = {{0, 3, 0x100, 0}};
    return record;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path trace_path = argv[1];
    const auto record = run_record();
    const std::string binding =
        completed_run_record_artifact_checksum(record);
    assert(binding.size() == 16);

    CompletedRunGhostTraceCapture capture;
    assert(!capture.observe({0, 1, 1, 1, 1, 1, 0x40}));
    assert(capture.begin_attempt());
    assert(capture.capturing());
    assert(capture.observe({0, 1088, 859, 0x0007, 0x0541, 1, 0x66, {0x0541, 0x0540, 0x0D0D, 0, 0, 0, 1, 0}}));
    assert(capture.observe({1, 1100, 850, 0x0009, 0x0540, 1, 0x66, {0x0540, 0x0541, 0x0D2C, 0, 0, 0, 1, 0}}));
    assert(!capture.observe({1, 9999, 9999, 0, 0, 0, 0}));
    assert(capture.observe({2, 1115, 840, 0x000B, 0x057D, 0, 0x26, {0x057D, 0x0543, 0x0D48, 0, 0, 0, 1, 0}}));
    assert(capture.sample_count() == 3);

    const auto completed_trace = capture.complete(record);
    assert(completed_trace);
    assert(!capture.capturing());
    assert(capture.sample_count() == 0);

    CompletedRunGhostTrace trace = *completed_trace;
    assert(trace.run_artifact_checksum == binding);
    assert(validate_completed_run_ghost_trace(trace, &record));
    const std::string encoded = encode_completed_run_ghost_trace(trace);
    assert(!encoded.empty());

    const auto decoded = decode_completed_run_ghost_trace(encoded, &record);
    assert(decoded.loaded());
    assert(decoded.trace->samples.size() == 3);
    assert(decoded.trace->samples[1].world_x == 1100);
    assert(decoded.trace->samples[2].semantic_frame_id == 0x057D);
    assert(decoded.trace->samples[0].sprite_attr == 0x66);
    assert(decoded.trace->samples[2].sprite_attr == 0x26);
    assert(decoded.trace->samples[0].composition.p1_primary == 0x0541);
    assert(decoded.trace->samples[0].composition.p2_primary == 0x0540);
    assert(decoded.trace->samples[0].composition.p1_companion == 0x0D0D);
    assert(decoded.trace->samples[2].composition.p1_companion == 0x0D48);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 0));
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 1)->world_x == 1100);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 2)->semantic_frame_id == 0x057D);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 3) == nullptr);

    auto other_record = record;
    other_record.elapsed_ticks60 = 121;
    const auto mismatched =
        decode_completed_run_ghost_trace(encoded, &other_record);
    assert(mismatched.status ==
           CompletedRunGhostTraceLoadStatus::Incompatible);

    std::string corrupt = encoded;
    const auto sample_pos = corrupt.find("1100");
    assert(sample_pos != std::string::npos);
    corrupt[sample_pos] = '9';
    const auto damaged = decode_completed_run_ghost_trace(corrupt, &record);
    assert(damaged.status == CompletedRunGhostTraceLoadStatus::Corrupt);

    std::string detail;
    assert(save_completed_run_ghost_trace_file(
        trace_path.string(), trace, &detail));
    const auto reloaded =
        load_completed_run_ghost_trace_file(trace_path.string(), &record);
    assert(reloaded.loaded());
    assert(reloaded.trace->samples.size() == trace.samples.size());

    const auto missing =
        load_completed_run_ghost_trace_file(
            (trace_path.string() + ".missing"), &record);
    assert(missing.status == CompletedRunGhostTraceLoadStatus::IoError);

    CompletedRunGhostState selected_state;
    selected_state.bind(
        {{trace_path.string(), record}},
        RunPlaybackTarget{
            record.provenance.game_id,
            record.provenance.rom_sha256,
            record.provenance.build_compat_id,
            record.provenance.course_id,
            record.provenance.mode,
        });
    const auto selected_trace =
        load_selected_completed_run_ghost_trace(
            selected_state, CompletedRunGhostKind::Previous);
    assert(selected_trace.loaded());
    assert(selected_trace.trace->samples.size() == trace.samples.size());

    CompletedRunGhostState empty_state;
    const auto no_selection =
        load_selected_completed_run_ghost_trace(
            empty_state, CompletedRunGhostKind::Previous);
    assert(no_selection.status == CompletedRunGhostTraceLoadStatus::Incompatible);

    CompletedRunGhostTraceCapture aborted;
    assert(aborted.begin_attempt());
    assert(aborted.observe({0, 1, 2, 3, 4, 1, 0x40}));
    aborted.abort_attempt();
    assert(!aborted.capturing());
    assert(aborted.sample_count() == 0);
    assert(!aborted.complete(record));

    CompletedRunGhostTraceCapture too_long;
    assert(too_long.begin_attempt());
    assert(too_long.observe({record.frame_count, 1, 2, 3, 4, 1, 0x40}));
    assert(!too_long.complete(record));

    auto unordered = trace;
    unordered.samples[2].race_frame = 1;
    assert(!validate_completed_run_ghost_trace(unordered, &record));

    auto out_of_range = trace;
    out_of_range.samples.back().race_frame = record.frame_count;
    assert(!validate_completed_run_ghost_trace(out_of_range, &record));

    return 0;
}
