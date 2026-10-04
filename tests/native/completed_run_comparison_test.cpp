#include "completed_run_comparison.hpp"

#include <cassert>
#include <cstdint>
#include <limits>

using namespace ur::product;

namespace {

CompletedRunRecord run(std::uint64_t finish, std::uint64_t split) {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = finish;
    record.splits = {{"checkpoint-1", split}};
    return record;
}

}  // namespace

int main() {
    const auto pb = run(1713, 850);
    const auto ahead = run(1707, 844);
    const auto behind = run(1725, 861);

    const auto ahead_cmp = compare_completed_run_timing(ahead, pb);
    assert(ahead_cmp);
    assert(ahead_cmp->finish_delta_ticks60 == -6);
    assert(ahead_cmp->splits.size() == 1);
    assert(ahead_cmp->splits[0].delta_ticks60 == -6);

    const auto behind_cmp = compare_completed_run_timing(behind, pb);
    assert(behind_cmp);
    assert(behind_cmp->finish_delta_ticks60 == 12);
    assert(behind_cmp->splits[0].delta_ticks60 == 11);

    auto wrong_course = ahead;
    wrong_course.provenance.course_id = "course:02";
    assert(!compare_completed_run_timing(wrong_course, pb));

    auto wrong_split = ahead;
    wrong_split.splits[0].id = "other";
    assert(!compare_completed_run_timing(wrong_split, pb));

    auto huge = ahead;
    huge.elapsed_ticks60 = std::numeric_limits<std::uint64_t>::max();
    assert(!compare_completed_run_timing(huge, pb));

    return 0;
}
