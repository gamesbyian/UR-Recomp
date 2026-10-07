#include "multiplayer_match_record.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

using namespace ur::product;
using namespace ur::title;

namespace {

HostProfileCatalogEntry profile(
    const char* id,
    const char* name,
    std::uint8_t rider) {
    return {id, HostRacerIdentity{name, rider}};
}

CompletedRunRecord run_record() {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-2p",
    };
    run.elapsed_ticks60 = 1726;
    run.frame_count = 2;
    run.inputs = {{0, 2, 0x080, 0x001}};
    return run;
}

MultiplayerMatchRecord record(const CompletedRunRecord& run) {
    OrdinaryTwoPlayerRaceResult result;
    result.player1_rider = 0;
    result.player2_rider = 1;
    result.player1_hundredths = 2876;
    result.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;

    const auto context = bind_local_multiplayer_match_context(
        result,
        profile("ian", "MIKE", 0),
        profile("friend", "ANDREW", 1),
        UrUniracersCourseIdentity{1, 1});
    assert(context.bound());

    MultiplayerMatchRecord value;
    value.run_artifact_checksum = completed_run_record_artifact_checksum(run);
    value.context = *context.context;
    return value;
}

}  // namespace

int main() {
    const auto run = run_record();
    const auto original = record(run);
    assert(validate_multiplayer_match_record(original));
    assert(multiplayer_match_record_matches_run(original, run));

    const std::string encoded = encode_multiplayer_match_record(original);
    assert(!encoded.empty());
    const auto decoded = decode_multiplayer_match_record(encoded);
    assert(decoded);
    assert(decoded.record->context.course_id == "course:01");
    assert(decoded.record->context.match.player1.profile_id == "ian");
    assert(decoded.record->context.match.player2.profile_id == "friend");
    assert(decoded.record->context.match.result.outcome ==
           OrdinaryTwoPlayerRaceOutcome::Player1Win);
    assert(multiplayer_match_record_matches_run(*decoded.record, run));

    auto corrupted = encoded;
    const auto pos = corrupted.find("2876");
    assert(pos != std::string::npos);
    corrupted[pos] = '3';
    assert(!decode_multiplayer_match_record(corrupted));

    {
        auto unsafe = original;
        unsafe.context.match.player2.profile_id = "CON";
        assert(!validate_multiplayer_match_record(unsafe));
        assert(encode_multiplayer_match_record(unsafe).empty());
    }

    {
        auto alias = original;
        alias.context.match.player2.profile_id = "IAN";
        assert(!validate_multiplayer_match_record(alias));
        assert(encode_multiplayer_match_record(alias).empty());
    }

    auto wrong_outcome = original;
    wrong_outcome.context.match.result.outcome =
        OrdinaryTwoPlayerRaceOutcome::Player2Win;
    assert(!validate_multiplayer_match_record(wrong_outcome));

    auto wrong_course_run = run;
    wrong_course_run.provenance.course_id = "course:02";
    assert(!multiplayer_match_record_matches_run(original, wrong_course_run));

    const auto path =
        std::filesystem::temp_directory_path() / "ur-records-match.urmatch";
    std::string detail;
    assert(save_multiplayer_match_record_file(
        path.string(), original, &detail));
    const auto loaded = load_multiplayer_match_record_file(path.string());
    assert(loaded);
    assert(multiplayer_match_record_matches_run(*loaded.record, run));

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
