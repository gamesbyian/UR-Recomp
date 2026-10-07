#include "completed_run_profile_sources.hpp"

#include "completed_run_record.hpp"
#include "completed_run_store.hpp"
#include "host_profile_catalog.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

CompletedRunRecord run() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 1713;
    record.frame_count = 1;
    record.splits = {{"finish", 1713}};
    record.inputs = {{0, 1, 0x100, 0}};
    return record;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path root(argv[1]);
    std::filesystem::create_directories(root);

    const std::vector<HostProfileCatalogEntry> profiles = {
        {"alpha", {"ALPHA", 3}},
        {"beta", {"BETA", 4}},
    };
    assert(save_host_profile_catalog_file(
        (root / "profiles-v1.txt").string(), profiles));

    const auto alpha_runs = root / "runs" / "alpha";
    std::filesystem::create_directories(alpha_runs);
    std::string detail;
    assert(append_completed_run_record(
        alpha_runs.string(), run(), nullptr, &detail));
    {
        std::ofstream bad(alpha_runs / "run-bad.urrun");
        bad << "not a completed run\n";
    }

    const auto loaded = load_run_records_profile_sources(root.string());
    assert(loaded);
    assert(loaded->size() == 2);
    assert((*loaded)[0].profile_id == "alpha");
    assert((*loaded)[0].racer_identity.name == "ALPHA");
    assert((*loaded)[0].records.size() == 1);
    assert((*loaded)[0].total_artifacts == 2);
    assert((*loaded)[1].profile_id == "beta");
    assert((*loaded)[1].racer_identity.name == "BETA");
    assert((*loaded)[1].records.empty());
    assert((*loaded)[1].total_artifacts == 0);

    const auto missing_root = root / "missing";
    std::filesystem::create_directories(missing_root);
    const auto missing =
        load_run_records_profile_sources(missing_root.string());
    assert(missing);
    assert(missing->empty());

    const auto malformed_root = root / "malformed";
    std::filesystem::create_directories(malformed_root);
    {
        std::ofstream out(malformed_root / "profiles-v1.txt");
        out << "not a profile catalog\n";
    }
    assert(!load_run_records_profile_sources(malformed_root.string()));
    assert(!load_run_records_profile_sources(""));

    return 0;
}
