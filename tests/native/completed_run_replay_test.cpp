#include "completed_run_replay.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord record() {
    CompletedRunRecord out;
    out.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    out.elapsed_ticks60 = 1713;
    out.frame_count = 168;
    out.splits = {{"finish", 1713}};
    out.inputs = {
        {0, 120, 0x80, 0},
        {120, 24, 0x81, 0},
        {144, 24, 0x80, 0},
    };
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path path(argv[1]);

    std::string detail;
    const auto run = record();
    assert(stage_completed_run_replay_input_file(path.string(), run, &detail));

    std::ifstream in(path, std::ios::binary);
    std::ostringstream text;
    text << in.rdbuf();
    assert(text.str() == encode_completed_run_input_file(run));

#if defined(__linux__)
    // A buffered stream may accept write() but fail on flush/close. Never
    // report a staged replay as ready if the disk could not receive it.
    detail.clear();
    assert(!stage_completed_run_replay_input_file("/dev/full", run, &detail));
    assert(detail == "cannot write replay input" ||
           detail == "cannot finish replay input");
#endif

    auto invalid = run;
    invalid.inputs[1].start_frame = 10;
    assert(!stage_completed_run_replay_input_file(
        (path.string() + ".invalid"), invalid, &detail));

    CompletedRunReplayFlow flow;
    assert(flow.begin());
    assert(!flow.begin());
    assert(flow.observe(false, false, false) ==
           CompletedRunReplayTransition::None);
    assert(flow.observe(true, false, false) ==
           CompletedRunReplayTransition::None);
    assert(flow.observe(false, true, false) ==
           CompletedRunReplayTransition::ReturnToBrowser);
    assert(!flow.active());

    assert(flow.begin());
    assert(flow.observe(true, false, false) ==
           CompletedRunReplayTransition::None);
    assert(flow.observe(false, false, true) ==
           CompletedRunReplayTransition::Cancelled);
    assert(!flow.active());


    assert(flow.begin());
    assert(flow.observe(true, false, false) ==
           CompletedRunReplayTransition::None);
    flow.cancel();
    assert(!flow.active());
    assert(flow.observe(false, true, false) ==
           CompletedRunReplayTransition::None);
    assert(flow.begin());
    flow.cancel();
    assert(!flow.active());

    return 0;
}
