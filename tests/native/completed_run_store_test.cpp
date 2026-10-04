#include "completed_run_store.hpp"

#include <cassert>
#include <filesystem>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

CompletedRunRecord run(std::uint64_t ticks) {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.splits = {{"finish", ticks}};
    return record;
}

RunPlaybackTarget target() {
    const auto p = run(1).provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path dir = argv[1];

    std::string path1, path2, detail;
    assert(append_completed_run_record(dir.string(), run(1800), &path1, &detail));
    assert(append_completed_run_record(dir.string(), run(1713), &path2, &detail));
    assert(path1 != path2);

    const auto records = load_compatible_run_records(dir.string(), target());
    assert(records.size() == 2);
    const auto previous = select_previous_run(records);
    assert(previous && *previous == 1);

    std::vector<CompletedRunRecord> plain;
    for (const auto& stored : records) plain.push_back(stored.record);
    const auto best = select_fastest_compatible_run(plain, target());
    assert(best && plain[*best].elapsed_ticks60 == 1713);

    auto wrong = target();
    wrong.course_id = "course:02";
    assert(load_compatible_run_records(dir.string(), wrong).empty());

    return 0;
}
