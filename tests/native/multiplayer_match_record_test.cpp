#include "multiplayer_match_record.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

using namespace ur::product;
using namespace ur::title;

namespace {

MultiplayerMatchRecord record() {
    MultiplayerMatchRecord value;
    value.run_artifact_checksum = "0123456789abcdef";
    value.match.course_id = "course:01";
    value.match.result.player1_rider = 0;
    value.match.result.player2_rider = 1;
    value.match.result.player1_hundredths = 2876;
    value.match.result.player2_hundredths =
        kOrdinaryTwoPlayerNoTimeHundredths;
    value.match.result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    value.match.player1 = {
        std::string("ian"),
        HostRacerIdentity{"IAN", 0},
    };
    value.match.player2 = {
        std::nullopt,
        HostRacerIdentity{"ANDREW", 1},
    };
    return value;
}

}  // namespace

int main() {
    const auto original = record();
    const std::string encoded = encode_multiplayer_match_record(original);
    assert(!encoded.empty());
    assert(encoded.find("UR-MULTIPLAYER-MATCH/1\n") == 0);
    assert(encoded.find("run_checksum 0123456789abcdef\n") !=
           std::string::npos);

    const auto decoded = decode_multiplayer_match_record(encoded);
    assert(decoded);
    assert(decoded.record->run_artifact_checksum ==
           original.run_artifact_checksum);
    assert(decoded.record->match.course_id == "course:01");
    assert(decoded.record->match.result.outcome ==
           OrdinaryTwoPlayerRaceOutcome::Player1Win);
    assert(decoded.record->match.player1.profile_id);
    assert(*decoded.record->match.player1.profile_id == "ian");
    assert(!decoded.record->match.player2.profile_id);
    assert(decoded.record->match.player2.racer.name == "ANDREW");

    auto corrupted = encoded;
    const auto pos = corrupted.find("2876");
    assert(pos != std::string::npos);
    corrupted[pos] = '3';
    assert(!decode_multiplayer_match_record(corrupted));

    auto mismatch = original;
    mismatch.match.result.outcome = OrdinaryTwoPlayerRaceOutcome::Player2Win;
    assert(!validate_multiplayer_match_record(mismatch));
    assert(encode_multiplayer_match_record(mismatch).empty());

    auto duplicate = original;
    duplicate.match.player2.profile_id = std::string("ian");
    assert(!validate_multiplayer_match_record(duplicate));

    auto wrong_rider = original;
    wrong_rider.match.player2.racer.rider_index = 2;
    assert(!validate_multiplayer_match_record(wrong_rider));

    auto bad_checksum = original;
    bad_checksum.run_artifact_checksum = "short";
    assert(!validate_multiplayer_match_record(bad_checksum));

    const auto path =
        std::filesystem::temp_directory_path() / "ur-match-record-test.urmatch";
    std::string detail;
    assert(save_multiplayer_match_record_file(
        path.string(), original, &detail));
    const auto loaded = load_multiplayer_match_record_file(path.string());
    assert(loaded);
    assert(loaded.record->run_artifact_checksum ==
           original.run_artifact_checksum);

    {
        std::ofstream oversized(path, std::ios::binary | std::ios::trunc);
        oversized << std::string(4097, 'x');
    }
    const auto rejected = load_multiplayer_match_record_file(path.string());
    assert(!rejected);
    assert(rejected.error == "match record too large");
    std::filesystem::remove(path);

    return 0;
}
