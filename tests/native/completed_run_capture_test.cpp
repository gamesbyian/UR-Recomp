#include "completed_run_capture.hpp"

#include <cassert>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

RunRecordProvenance dragster() {
    return {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
}

RunPlaybackTarget target_for(const RunRecordProvenance& p) {
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

}  // namespace

int main() {
    CompletedRunCapture capture;
    assert(!capture.observe_guest_frame(0x100));
    assert(capture.begin_attempt(dragster()));
    assert(capture.capturing());
    assert(capture.captured_frames() == 0);

    // These are exact resolved guest words, not raw SDL events.
    assert(capture.observe_guest_frame(0x000100));
    assert(capture.observe_guest_frame(0x000100));
    assert(capture.observe_guest_frame(0x000101));
    assert(capture.observe_guest_frame(0x008101));  // P2 bit in upper word too.
    assert(capture.captured_frames() == 4);

    assert(capture.observe_split("mid", 840));
    assert(!capture.observe_split("regressed", 839));
    assert(capture.observe_split("finish", 1713));

    const auto completed = capture.complete(
        1713,
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789");
    assert(completed);
    assert(!capture.capturing());
    assert(completed->inputs.size() == 3);
    assert(completed->inputs[0].start_frame == 0);
    assert(completed->inputs[0].duration == 2);
    assert(completed->inputs[0].p1_mask == 0x100);
    assert(completed->inputs[1].p1_mask == 0x101);
    assert(completed->inputs[2].p2_mask == 0x008);

    // A failed/aborted attempt cannot leak its previous input into the next.
    assert(capture.begin_attempt(dragster()));
    assert(capture.observe_guest_frame(0x080));
    capture.abort_attempt();
    assert(capture.begin_attempt(dragster()));
    assert(capture.observe_guest_frame(0x100));
    const auto replacement = capture.complete(1800);
    assert(replacement && replacement->inputs.size() == 1);
    assert(replacement->inputs[0].p1_mask == 0x100);

    std::vector<CompletedRunRecord> records;
    auto slower = *replacement;
    slower.elapsed_ticks60 = 1800;
    records.push_back(slower);
    records.push_back(*completed);
    auto equal_newer = *completed;
    records.push_back(equal_newer);

    const auto best = select_fastest_compatible_run(records, target_for(dragster()));
    assert(best && *best == 2);  // equal PB chooses most recently supplied.

    auto wrong_course = target_for(dragster());
    wrong_course.course_id = "course:02";
    assert(!select_fastest_compatible_run(records, wrong_course));

    return 0;
}
