#include "completed_run_ghost_trace.hpp"

#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord make_run() {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    run.frame_count = 2;
    run.elapsed_ticks60 = 120;
    run.splits = {{"finish", 120}};
    run.inputs = {{0, 2, 0x080, 0}};
    return run;
}

std::string read_bytes(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(input),
            std::istreambuf_iterator<char>()};
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path base(argv[1]);
    const auto valid_path = std::filesystem::path(base.string() + ".urghost");
    const auto huge_path = std::filesystem::path(base.string() + ".huge.urghost");
    const auto run = make_run();
    assert(validate_completed_run_record(run));

    CompletedRunGhostTraceCapture capture;
    assert(capture.begin_attempt());
    assert(capture.observe({0, 1040, 800, 1, 0x0540, 1, 0x40, {}}));
    assert(capture.observe({1, 1060, 799, 2, 0x0541, 1, 0x40, {}}));
    const auto trace = capture.complete(run);
    assert(trace);

    std::string detail;
    assert(save_completed_run_ghost_trace_file(
        valid_path.string(), *trace, &detail));
    const auto original_bytes = read_bytes(valid_path);
    assert(!original_bytes.empty());
    const auto admitted =
        load_completed_run_ghost_trace_file(valid_path.string(), &run);
    assert(admitted.loaded());
    assert(admitted.trace->samples.size() == 2);

    // No disk payload larger than the retained ceiling may be materialized.
    // resize_file yields a sparse file on Linux: CI does not need 64 MiB
    // of artifact disk traffic just to exercise rejection.
    {
        std::ofstream out(huge_path, std::ios::binary);
        assert(out);
        out.put('x');
    }
    std::filesystem::resize_file(
        huge_path, kCompletedRunGhostTraceMaxBytes + 1);
    const auto oversized =
        load_completed_run_ghost_trace_file(huge_path.string(), &run);
    assert(oversized.status == CompletedRunGhostTraceLoadStatus::Malformed);
    assert(oversized.detail == "ghost trace byte limit exceeded");
    assert(!oversized.trace);

    // Optional trace collection is bounded even before serialization.
    CompletedRunGhostTraceCapture long_attempt;
    assert(long_attempt.begin_attempt());
    CompletedRunGhostWorldSample sample{};
    for (std::size_t i = 0; i < kCompletedRunGhostTraceMaxSamples; ++i) {
        sample.race_frame = i;
        assert(long_attempt.observe(sample));
    }
    sample.race_frame = kCompletedRunGhostTraceMaxSamples;
    assert(!long_attempt.observe(sample));
    assert(long_attempt.sample_count() == kCompletedRunGhostTraceMaxSamples);
    long_attempt.abort_attempt();
    assert(!long_attempt.capturing());

    // Refusing an excessive sidecar must not truncate the already saved
    // original, and the independently valid run record remains intact.
    CompletedRunGhostTrace excessive = *trace;
    excessive.samples.resize(kCompletedRunGhostTraceMaxSamples + 1);
    assert(!validate_completed_run_ghost_trace(excessive, &run, &detail));
    assert(detail == "ghost trace sample limit exceeded");
    assert(!save_completed_run_ghost_trace_file(
        valid_path.string(), excessive, &detail));
    assert(read_bytes(valid_path) == original_bytes);
    assert(load_completed_run_ghost_trace_file(
        valid_path.string(), &run).loaded());

    return 0;
}
