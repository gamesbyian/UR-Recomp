#include "completed_run_record.hpp"

#include <iostream>
#include <string>

using namespace ur::product;

int main(int argc, char** argv) {
    if (argc != 3) return 64;
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 120;
    record.frame_count = 10;
    record.splits = {{"finish", 120}};
    record.inputs = {{0, 10, 0x100, 0}};
    const std::string digest = argv[2];
    if (digest != "-") record.terminal_simulation_digest = digest;
    std::string detail;
    if (!save_completed_run_record_file(argv[1], record, &detail)) {
        std::cerr << detail << "\n";
        return 1;
    }
    return 0;
}
