#include "completed_run_replay.hpp"

#include <cstdio>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s SAVED.urrun REPLAY.input\n", argv[0]);
        return 2;
    }

    // This is the exact production artifact decoder and replay-input staging
    // path, run in a process that did not witness the original attempt.
    const auto stored = ur::product::load_completed_run_record_file(argv[1]);
    if (!stored.loaded()) {
        std::fprintf(stderr, "UR_RUN_REPLAY_REHYDRATE FAIL record=%s\n",
                     stored.detail.c_str());
        return 1;
    }

    std::string detail;
    if (!ur::product::stage_completed_run_replay_input_file(
            argv[2], *stored.record, &detail)) {
        std::fprintf(stderr, "UR_RUN_REPLAY_REHYDRATE FAIL input=%s\n",
                     detail.c_str());
        return 1;
    }
    std::printf(
        "UR_RUN_REPLAY_REHYDRATE PASS course=%s inputs=%zu\n",
        stored.record->provenance.course_id.c_str(),
        stored.record->inputs.size());
    return 0;
}
