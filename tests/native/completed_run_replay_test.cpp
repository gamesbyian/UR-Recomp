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

    // Independent game processes can share a data root. Reservations must
    // never alias, stage different streams without clobbering one another,
    // and clean up only their own lifetime-owned directory.
    const auto user_root = path.parent_path() / "replay-isolation";
    CompletedRunReplayInputStage first_stage;
    CompletedRunReplayInputStage second_stage;
    assert(!first_stage.reserve(""));
    assert(first_stage.input_path().empty());
    assert(first_stage.reserve(user_root.string()));
    assert(second_stage.reserve(user_root.string()));
    const std::string first_path = first_stage.input_path();
    const std::string second_path = second_stage.input_path();
    assert(!first_path.empty() && first_path != second_path);
    assert(std::filesystem::is_directory(
        std::filesystem::path(first_path).parent_path()));
    auto other_run = run;
    other_run.inputs[0].p1_mask = 0x40;
    assert(stage_completed_run_replay_input_file(first_path, run, &detail));
    assert(stage_completed_run_replay_input_file(second_path, other_run, &detail));
    {
        std::ifstream first_input(first_path, std::ios::binary);
        std::ifstream second_input(second_path, std::ios::binary);
        std::ostringstream first_bytes, second_bytes;
        first_bytes << first_input.rdbuf();
        second_bytes << second_input.rdbuf();
        assert(first_bytes.str() == encode_completed_run_input_file(run));
        assert(second_bytes.str() == encode_completed_run_input_file(other_run));
        assert(first_bytes.str() != second_bytes.str());
    }
    first_stage.clear();
    assert(!std::filesystem::exists(first_path));
    assert(std::filesystem::exists(second_path));
    second_stage.clear();
    assert(!std::filesystem::exists(second_path));
    assert(first_stage.input_path().empty());
    assert(second_stage.input_path().empty());

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

    // A browser selection remains a snapshot, never persistent authority.
    // Revalidate the on-disk record before staging it into the next race.
    const auto saved_path = path.string() + ".urrun";
    const RunPlaybackTarget target{
        run.provenance.game_id, run.provenance.rom_sha256,
        run.provenance.build_compat_id, run.provenance.course_id,
        run.provenance.mode,
    };
    assert(save_completed_run_record_file(saved_path, run, &detail));
    const auto reloaded = reload_matching_completed_run_replay_record(
        saved_path, run, target);
    assert(reloaded);
    assert(encode_completed_run_input_file(*reloaded) ==
           encode_completed_run_input_file(run));

    auto modified = run;
    ++modified.elapsed_ticks60;
    assert(save_completed_run_record_file(saved_path, modified, &detail));
    assert(!reload_matching_completed_run_replay_record(
        saved_path, run, target));
    auto wrong_course = target;
    wrong_course.course_id = "course:02";
    assert(!reload_matching_completed_run_replay_record(
        saved_path, modified, wrong_course));
    assert(std::filesystem::remove(saved_path));
    assert(!reload_matching_completed_run_replay_record(
        saved_path, run, target));

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
