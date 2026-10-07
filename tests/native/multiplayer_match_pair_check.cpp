#include "completed_run_record.hpp"
#include "multiplayer_match_record.hpp"

#include <fstream>
#include <iostream>
#include <string>

using namespace ur::product;
using namespace ur::title;

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: check <run.urrun> <out.input>\n";
        return 2;
    }

    const std::string run_path = argv[1];
    const auto run = load_completed_run_record_file(run_path);
    if (!run.loaded()) {
        std::cerr << "run load failed: " << run.detail << "\n";
        return 1;
    }
    if (run.record->provenance.mode != "race-2p") {
        std::cerr << "unexpected mode\n";
        return 1;
    }
    if (run.record->elapsed_ticks60 != 1726 || !run.record->splits.empty()) {
        std::cerr << "unexpected 2P carrier timing\n";
        return 1;
    }

    const auto match =
        load_multiplayer_match_record_for_run(run_path, *run.record);
    if (!match) {
        std::cerr << "match load failed: " << match.error << "\n";
        return 1;
    }
    if (match.record->context.match.result.outcome !=
        OrdinaryTwoPlayerRaceOutcome::Player1Win) {
        std::cerr << "unexpected outcome\n";
        return 1;
    }
    if (match.record->context.match.player1.profile_id != "accept-p1" ||
        match.record->context.match.player2.profile_id != "accept-p2") {
        std::cerr << "unexpected participants\n";
        return 1;
    }

    const std::string input =
        encode_completed_run_input_file(*run.record);
    std::ofstream out(argv[2], std::ios::binary | std::ios::trunc);
    out.write(input.data(), static_cast<std::streamsize>(input.size()));
    out.close();
    if (!out) {
        std::cerr << "input export failed\n";
        return 1;
    }

    std::cout
        << "UR_MULTIPLAYER_MATCH_PAIR_CHECK PASS"
        << " course=" << match.record->context.course_id
        << " p1=" << match.record->context.match.player1.profile_id
        << " p2=" << match.record->context.match.player2.profile_id
        << " p1_hundredths="
        << match.record->context.match.result.player1_hundredths
        << " p2_hundredths="
        << match.record->context.match.result.player2_hundredths
        << " frames=" << run.record->frame_count
        << " inputs=" << run.record->inputs.size()
        << "\n";
    return 0;
}
