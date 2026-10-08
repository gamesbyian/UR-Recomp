#include "ghost_trace_equivalence.hpp"

#include <cstdio>
#include <string>

using ur::product::load_completed_run_ghost_trace_file;
using ur::product::load_completed_run_record_file;

int main(int argc, char** argv) {
    if (argc != 5) {
        std::fprintf(
            stderr,
            "usage: %s ORIGINAL.urrun ORIGINAL.urrun.urghost "
            "REPLAYED.urrun REPLAYED.urrun.urghost\n",
            argv[0]);
        return 2;
    }

    const auto original = load_completed_run_record_file(argv[1]);
    const auto replayed = load_completed_run_record_file(argv[3]);
    if (!original.loaded() || !replayed.loaded()) {
        std::fprintf(
            stderr, "UR_RUN_GHOST_TRACE_COMPARE FAIL record original=%s replayed=%s\n",
            original.detail.c_str(), replayed.detail.c_str());
        return 1;
    }

    const auto original_trace =
        load_completed_run_ghost_trace_file(argv[2], &*original.record);
    const auto replayed_trace =
        load_completed_run_ghost_trace_file(argv[4], &*replayed.record);
    if (!original_trace.loaded() || !replayed_trace.loaded()) {
        std::fprintf(
            stderr, "UR_RUN_GHOST_TRACE_COMPARE FAIL trace original=%s replayed=%s\n",
            original_trace.detail.c_str(), replayed_trace.detail.c_str());
        return 1;
    }

    if (!ur::test::ghost_trace_covers_completed_run(
            *original_trace.trace, *original.record) ||
        !ur::test::ghost_trace_covers_completed_run(
            *replayed_trace.trace, *replayed.record)) {
        std::fprintf(stderr,
            "UR_RUN_GHOST_TRACE_COMPARE FAIL incomplete run-frame coverage "
            "original=%zu/%llu replayed=%zu/%llu\\n",
            original_trace.trace->samples.size(),
            static_cast<unsigned long long>(original.record->frame_count),
            replayed_trace.trace->samples.size(),
            static_cast<unsigned long long>(replayed.record->frame_count));
        return 1;
    }

    std::string detail;
    std::size_t compared = 0;
    ur::test::GhostTraceReplayComparison comparison;
    if (!ur::test::equivalent_ghost_world_samples(
            *original_trace.trace, *replayed_trace.trace,
            &detail, &compared, &comparison)) {
        std::fprintf(stderr, "UR_RUN_GHOST_TRACE_COMPARE FAIL %s\n",
                     detail.c_str());
        return 1;
    }

    std::printf(
        "UR_RUN_GHOST_TRACE_COMPARE PASS course=%s frames=%zu original=%zu "
        "replayed=%zu terminal_delta=%zu pose_drift=%zu "
        "p2_context_drift=%zu terminal_observation_drift=%zu "
        "first_pose_drift=%llu first_context_drift=%llu\n",
        original.record->provenance.course_id.c_str(),
        compared, original_trace.trace->samples.size(),
        replayed_trace.trace->samples.size(),
        original_trace.trace->samples.size() > replayed_trace.trace->samples.size()
            ? original_trace.trace->samples.size() - replayed_trace.trace->samples.size()
            : replayed_trace.trace->samples.size() - original_trace.trace->samples.size(),
        comparison.p1_pose_drift_frames,
        comparison.p2_context_drift_frames,
        comparison.terminal_observation_drift_frames,
        static_cast<unsigned long long>(comparison.first_p1_pose_drift_frame),
        static_cast<unsigned long long>(comparison.first_p2_context_drift_frame));
    return 0;
}
