#include "completed_run_ghost_trace.hpp"
#include "completed_run_record.hpp"

#include <cstdio>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s RUN.urrun RUN.urrun.urghost\n", argv[0]);
        return 2;
    }

    const auto run = ur::product::load_completed_run_record_file(argv[1]);
    if (!run.loaded()) {
        std::fprintf(
            stderr, "UR_RUN_GHOST_TRACE_CHECK FAIL run=%s detail=%s\n",
            argv[1], run.detail.c_str());
        return 1;
    }

    const auto trace =
        ur::product::load_completed_run_ghost_trace_file(
            argv[2], &*run.record);
    if (!trace.loaded()) {
        std::fprintf(
            stderr, "UR_RUN_GHOST_TRACE_CHECK FAIL trace=%s detail=%s\n",
            argv[2], trace.detail.c_str());
        return 1;
    }

    std::printf(
        "UR_RUN_GHOST_TRACE_CHECK PASS course=%s samples=%zu run_checksum=%s\n",
        run.record->provenance.course_id.c_str(),
        trace.trace->samples.size(),
        trace.trace->run_artifact_checksum.c_str());
    return 0;
}
