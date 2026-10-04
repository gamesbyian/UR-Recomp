#include "completed_run_ghost.hpp"

#include <cassert>
#include <cstdint>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

CompletedRunRecord make_record(
    std::uint64_t ticks,
    std::uint16_t first_mask,
    const std::string& course = "course:01") {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "rom",
        "build",
        course,
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.frame_count = 4;
    record.splits = {{"finish", ticks}};
    record.inputs = {
        {0, 2, first_mask, 0},
        {2, 2, static_cast<std::uint16_t>(first_mask + 1), 0},
    };
    return record;
}

RunPlaybackTarget target() {
    return {
        "uniracers-usa",
        "rom",
        "build",
        "course:01",
        "race-1p",
    };
}

}  // namespace

int main() {
    const CompletedRunRecord first = make_record(1200, 0x10);
    const CompletedRunRecord fastest = make_record(1100, 0x20);
    const CompletedRunRecord latest = make_record(1150, 0x30);
    const CompletedRunRecord incompatible =
        make_record(900, 0x40, "course:02");

    const std::vector<StoredRunRecord> records = {
        {"run-1.urrun", first},
        {"run-2.urrun", fastest},
        {"run-3.urrun", incompatible},
        {"run-4.urrun", latest},
    };

    CompletedRunGhostState ghosts;
    ghosts.bind(records, target());

    assert(ghosts.compatible_count() == 3);
    assert(ghosts.has(CompletedRunGhostKind::Previous));
    assert(ghosts.has(CompletedRunGhostKind::PersonalBest));
    assert(ghosts.record(CompletedRunGhostKind::Previous)->elapsed_ticks60 == 1150);
    assert(ghosts.record(CompletedRunGhostKind::PersonalBest)->elapsed_ticks60 == 1100);

    assert(
        ghosts.input_at(CompletedRunGhostKind::Previous, 0) ==
        std::make_pair<std::uint16_t, std::uint16_t>(0x30, 0));
    assert(
        ghosts.input_at(CompletedRunGhostKind::Previous, 3) ==
        std::make_pair<std::uint16_t, std::uint16_t>(0x31, 0));
    assert(
        ghosts.input_at(CompletedRunGhostKind::PersonalBest, 1) ==
        std::make_pair<std::uint16_t, std::uint16_t>(0x20, 0));
    assert(
        ghosts.input_at(CompletedRunGhostKind::PersonalBest, 999) ==
        std::make_pair<std::uint16_t, std::uint16_t>(0, 0));

    ghosts.clear();
    assert(ghosts.compatible_count() == 0);
    assert(!ghosts.has(CompletedRunGhostKind::Previous));
    assert(!ghosts.has(CompletedRunGhostKind::PersonalBest));
    assert(ghosts.record(CompletedRunGhostKind::Previous) == nullptr);

    return 0;
}
