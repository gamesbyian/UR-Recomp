#include "completed_run_ghost_policy.hpp"

#include <cassert>
#include <cstdint>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

constexpr const char* kRom =
    "0123456789abcdef0123456789abcdef"
    "0123456789abcdef0123456789abcdef";

CompletedRunRecord make_record(
    std::uint64_t ticks,
    std::uint16_t mask,
    const std::string& course = "course:01") {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        kRom,
        "build",
        course,
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.frame_count = 2;
    record.splits = {{"finish", ticks}};
    record.inputs = {{0, 2, mask, 0}};
    return record;
}

RunPlaybackTarget target() {
    return {
        "uniracers-usa",
        kRom,
        "build",
        "course:01",
        "race-1p",
    };
}

}  // namespace

int main() {
    const std::vector<StoredRunRecord> records = {
        {"run-1.urrun", make_record(1200, 0x10)},
        {"run-2.urrun", make_record(1100, 0x20)},
        {"run-3.urrun", make_record(1150, 0x30)},
    };

    CompletedRunGhostState state;
    state.bind(records, target());

    {
        const auto selected = select_completed_run_ghost_target(
            state, CompletedRunGhostTarget::Off);
        assert(!selected.active());
        assert(selected.target == CompletedRunGhostTarget::Off);
        assert(!selected.kind);
        assert(selected.record == nullptr);
    }
    {
        const auto selected = select_completed_run_ghost_target(
            state, CompletedRunGhostTarget::Previous);
        assert(selected.active());
        assert(selected.kind == CompletedRunGhostKind::Previous);
        assert(selected.record->elapsed_ticks60 == 1150);
    }
    {
        const auto selected = select_completed_run_ghost_target(
            state, CompletedRunGhostTarget::PersonalBest);
        assert(selected.active());
        assert(selected.kind == CompletedRunGhostKind::PersonalBest);
        assert(selected.record->elapsed_ticks60 == 1100);
    }

    CompletedRunGhostState empty;
    const auto missing_previous = select_completed_run_ghost_target(
        empty, CompletedRunGhostTarget::Previous);
    const auto missing_pb = select_completed_run_ghost_target(
        empty, CompletedRunGhostTarget::PersonalBest);
    assert(!missing_previous.active());
    assert(!missing_previous.kind);
    assert(!missing_pb.active());
    assert(!missing_pb.kind);

    assert(std::string(completed_run_ghost_target_name(
        CompletedRunGhostTarget::Off)) == "off");
    assert(std::string(completed_run_ghost_target_name(
        CompletedRunGhostTarget::Previous)) == "previous");
    assert(std::string(completed_run_ghost_target_name(
        CompletedRunGhostTarget::PersonalBest)) == "personal-best");

    assert(parse_completed_run_ghost_target("off") ==
           CompletedRunGhostTarget::Off);
    assert(parse_completed_run_ghost_target("previous") ==
           CompletedRunGhostTarget::Previous);
    assert(parse_completed_run_ghost_target("personal-best") ==
           CompletedRunGhostTarget::PersonalBest);
    assert(!parse_completed_run_ghost_target("pb"));
    assert(!parse_completed_run_ghost_target("fastest"));
    assert(!parse_completed_run_ghost_target(""));

    return 0;
}
