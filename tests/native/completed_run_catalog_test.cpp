#include "completed_run_catalog.hpp"

#include <cassert>
#include <cstdint>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

CompletedRunRecord run(
    std::uint64_t ticks,
    const std::string& course = "course:01") {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        course,
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.frame_count = 1;
    record.splits = {{"finish", ticks}};
    record.inputs = {{0, 1, 0x100, 0}};
    return record;
}

RunPlaybackTarget target() {
    const auto p = run(1).provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

}  // namespace

int main() {
    const std::vector<StoredRunRecord> records = {
        {"run-1.urrun", run(1800)},
        {"run-bad-course.urrun", run(900, "course:02")},
        {"run-2.urrun", run(1713)},
        {"run-3.urrun", run(1713)},
        {"run-4.urrun", run(1750)},
    };

    const auto catalog = build_run_data_catalog(records, target());
    assert(catalog.entries.size() == 4);

    // Source indices preserve provenance back to the immutable store catalog.
    assert(catalog.entries[0].source_index == 0);
    assert(catalog.entries[1].source_index == 2);
    assert(catalog.entries[2].source_index == 3);
    assert(catalog.entries[3].source_index == 4);

    assert(catalog.entries[0].time_text == "0:30.00/60");
    assert(catalog.entries[1].time_text == "0:28.33/60");

    // Canonical equal-PB policy keeps the most recently supplied equal time.
    assert(catalog.personal_best_entry && *catalog.personal_best_entry == 2);
    assert(catalog.entries[2].is_personal_best);
    assert(!catalog.entries[1].is_personal_best);

    // Previous means the newest compatible record, not merely newest file in
    // an unfiltered mixed-domain directory.
    assert(catalog.previous_entry && *catalog.previous_entry == 3);
    assert(catalog.entries[3].is_previous);

    const auto stats = present_run_data_statistics(catalog);
    assert(stats.completed_runs == 4);
    assert(stats.personal_best_available);
    assert(stats.personal_best_text == "0:28.33/60");
    assert(stats.previous_available);
    assert(stats.previous_text == "0:29.10/60");
    assert(stats.previous_comparison_available);
    assert(stats.previous_vs_pb_text == "+0:00.37/60");

    const std::vector<StoredRunRecord> empty;
    const auto none = build_run_data_catalog(empty, target());
    assert(none.entries.empty());
    assert(!none.previous_entry);
    assert(!none.personal_best_entry);
    const auto empty_stats = present_run_data_statistics(none);
    assert(empty_stats.completed_runs == 0);
    assert(!empty_stats.personal_best_available);
    assert(empty_stats.personal_best_text == "--");
    assert(!empty_stats.previous_available);
    assert(empty_stats.previous_text == "--");
    assert(!empty_stats.previous_comparison_available);
    assert(empty_stats.previous_vs_pb_text == "--");

    return 0;
}
