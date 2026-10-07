#include "completed_run_match_metadata.hpp"

#include <cassert>
#include <cstdio>
#include <string>

using namespace ur::product;
using namespace ur::title;

namespace {

CompletedRunRecord run_record(const char* course = "course:12") {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        std::string(64, 'a'),
        "test-build",
        course,
        "replay-test",
    };
    run.elapsed_ticks60 = 1234;
    run.frame_count = 100;
    return run;
}

BoundOrdinaryTwoPlayerMatchContext match_context() {
    OrdinaryTwoPlayerRaceResult result;
    result.player1_rider = 2;
    result.player2_rider = 7;
    result.player1_hundredths = 1234;
    result.player2_hundredths = 1300;
    result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;

    const HostProfileCatalogEntry p1{
        "ian", HostRacerIdentity{"RIDER | ONE", 2}};
    const HostProfileCatalogEntry p2{
        "guest", HostRacerIdentity{"RIDER % TWO", 7}};
    const auto bound = bind_local_multiplayer_match_context(
        result, p1, p2, UrUniracersCourseIdentity{1, 12});
    assert(bound.bound());
    return *bound.context;
}

}  // namespace

int main() {
    const auto run = run_record();
    const auto context = match_context();

    const auto metadata = make_completed_run_match_metadata(context, run);
    assert(metadata.has_value());
    assert(metadata->run_artifact_checksum ==
           completed_run_record_artifact_checksum(run));
    assert(metadata->course_id == "course:12");
    assert(metadata->player1.identity.name == "RIDER | ONE");
    assert(metadata->player2.identity.name == "RIDER % TWO");
    assert(metadata->outcome == OrdinaryTwoPlayerRaceOutcome::Player1Win);

    const std::string encoded =
        encode_completed_run_match_metadata(*metadata);
    assert(!encoded.empty());
    assert(encoded.find("RIDER %7C ONE") != std::string::npos);
    assert(encoded.find("RIDER %25 TWO") != std::string::npos);

    const auto decoded =
        decode_completed_run_match_metadata(encoded, &run);
    assert(decoded.loaded());
    assert(decoded.metadata->run_artifact_checksum ==
           metadata->run_artifact_checksum);
    assert(decoded.metadata->course_id == metadata->course_id);
    assert(decoded.metadata->player1 == metadata->player1);
    assert(decoded.metadata->player2 == metadata->player2);
    assert(decoded.metadata->player1_hundredths == 1234);
    assert(decoded.metadata->player2_hundredths == 1300);
    assert(decoded.metadata->outcome ==
           OrdinaryTwoPlayerRaceOutcome::Player1Win);

    {
        auto different_run = run;
        different_run.elapsed_ticks60 = 1235;
        const auto mismatch =
            decode_completed_run_match_metadata(encoded, &different_run);
        assert(!mismatch.loaded());
        assert(mismatch.status ==
               CompletedRunMatchMetadataLoadStatus::Incompatible);
    }

    {
        auto wrong_course = run_record("course:13");
        assert(!make_completed_run_match_metadata(context, wrong_course));
    }

    {
        std::string corrupt = encoded;
        const auto pos = corrupt.find("RIDER %7C ONE");
        assert(pos != std::string::npos);
        corrupt[pos] = 'X';
        const auto rejected =
            decode_completed_run_match_metadata(corrupt, &run);
        assert(!rejected.loaded());
        assert(rejected.status ==
               CompletedRunMatchMetadataLoadStatus::Corrupt);
    }

    {
        auto contradictory = *metadata;
        contradictory.outcome =
            OrdinaryTwoPlayerRaceOutcome::Player2Win;
        std::string detail;
        assert(!validate_completed_run_match_metadata(
            contradictory, &run, &detail));
        assert(detail == "invalid authoritative result");
        assert(encode_completed_run_match_metadata(contradictory).empty());
    }

    {
        const std::string path = "completed-run-match-metadata-test.urmatch";
        std::remove(path.c_str());
        std::string detail;
        assert(save_completed_run_match_metadata_file(
            path, *metadata, &detail));
        const auto loaded =
            load_completed_run_match_metadata_file(path, &run);
        assert(loaded.loaded());
        assert(loaded.metadata->player1 == metadata->player1);
        assert(std::remove(path.c_str()) == 0);
    }

    return 0;
}
