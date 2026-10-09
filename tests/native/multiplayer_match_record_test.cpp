#include "multiplayer_match_record.hpp"

#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
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

int main(int argc, char** argv) {
    if (argc == 4 && std::string(argv[1]) == "append") {
        auto run = run_record();
        const unsigned serial = static_cast<unsigned>(std::strtoul(argv[3], nullptr, 10));
        if (serial >= 16) return 2;
        run.elapsed_ticks60 += serial;
        const auto match = record(run);
        std::string path, error;
        if (!append_multiplayer_match_pair(argv[2], run, match, &path, &error)) {
            std::cerr << error << "\\n";
            return 3;
        }
        std::cout << path << "\\n";
        return 0;
    }
    if (argc == 3 && std::string(argv[1]) == "inspect") {
        std::set<std::uint64_t> times;
        std::size_t sidecars = 0;
        for (const auto& entry : std::filesystem::directory_iterator(argv[2])) {
            if (entry.path().extension() == ".urmatch") {
                ++sidecars;
                continue;
            }
            if (entry.path().extension() != ".urrun") return 4;
            const auto run = load_completed_run_record_file(entry.path().string());
            if (!run.loaded()) return 5;
            const auto match = load_multiplayer_match_record_for_run(
                entry.path().string(), *run.record);
            if (!match) return 6;
            times.insert(run.record->elapsed_ticks60);
        }
        if (times.size() != 8 || sidecars != 8) return 7;
        for (unsigned i = 0; i != 8; ++i) {
            if (!times.count(1726u + i)) return 8;
        }
        return 0;
    }
    if (argc != 1) return 2;
    const auto run = run_record();
    const auto original = record(run);
    const auto constructed =
        make_multiplayer_match_record(run, original.context);
    assert(constructed.has_value());
    assert(constructed->run_artifact_checksum ==
           original.run_artifact_checksum);
    assert(constructed->context.course_id == "course:01");
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
    assert(!make_multiplayer_match_record(
        wrong_course_run, original.context));

    auto one_player_run = run;
    one_player_run.provenance.mode = "race-1p";
    assert(!multiplayer_match_record_matches_run(original, one_player_run));
    assert(!make_multiplayer_match_record(
        one_player_run, original.context));

    const auto path =
        std::filesystem::temp_directory_path() / "ur-records-match.urmatch";
    std::string detail;
    assert(save_multiplayer_match_record_file(
        path.string(), original, &detail));
    const auto loaded = load_multiplayer_match_record_file(path.string());
    assert(loaded);
    assert(multiplayer_match_record_matches_run(*loaded.record, run));

    {
        const auto run_path =
            std::filesystem::temp_directory_path() / "ur-records-paired.urrun";
        const auto match_path =
            std::filesystem::path(run_path.string() + ".urmatch");
        std::filesystem::remove(run_path);
        std::filesystem::remove(match_path);

        assert(save_completed_run_record_file(
            run_path.string(), run, &detail));
        assert(save_multiplayer_match_record_for_run(
            run_path.string(), run, original, &detail));
        assert(multiplayer_match_record_path_for_run(run_path.string()) ==
               match_path.string());

        const auto fresh_run =
            load_completed_run_record_file(run_path.string());
        assert(fresh_run.loaded());
        const auto fresh_match =
            load_multiplayer_match_record_for_run(
                run_path.string(), *fresh_run.record);
        assert(fresh_match);
        assert(fresh_match.record->context.match.player1.profile_id == "ian");
        assert(fresh_match.record->context.match.player2.profile_id == "friend");

        auto changed_run = *fresh_run.record;
        changed_run.elapsed_ticks60 += 1;
        const auto mismatch =
            load_multiplayer_match_record_for_run(
                run_path.string(), changed_run);
        assert(!mismatch);
        assert(mismatch.error == "match record does not bind completed run");

        auto wrong_record = original;
        wrong_record.context.course_id = "course:02";
        assert(!save_multiplayer_match_record_for_run(
            run_path.string(), run, wrong_record, &detail));

        std::filesystem::remove(match_path);
        std::filesystem::remove(run_path);
    }

    {
        const auto pair_root =
            std::filesystem::temp_directory_path() / "ur-records-match-pair";
        std::filesystem::remove_all(pair_root);
        std::string pair_path;
        detail.clear();
        assert(append_multiplayer_match_pair(
            pair_root.string(), run, original, &pair_path, &detail));
        assert(!pair_path.empty());
        assert(std::filesystem::exists(pair_path));
        assert(std::filesystem::exists(
            multiplayer_match_record_path_for_run(pair_path)));
        assert(std::filesystem::path(pair_path).parent_path() == pair_root);

        std::size_t public_files = 0;
        for (const auto& entry :
             std::filesystem::directory_iterator(pair_root)) {
            assert(entry.is_regular_file());
            ++public_files;
            assert(entry.path().filename().string().find(
                       ".urpair-stage-") == std::string::npos);
        }
        assert(public_files == 2);

        const auto pair_run = load_completed_run_record_file(pair_path);
        assert(pair_run.loaded());
        const auto pair_match = load_multiplayer_match_record_for_run(
            pair_path, *pair_run.record);
        assert(pair_match);

        auto unbound = original;
        unbound.run_artifact_checksum = "0123456789abcdef";
        const auto before = std::distance(
            std::filesystem::directory_iterator(pair_root),
            std::filesystem::directory_iterator{});
        assert(!append_multiplayer_match_pair(
            pair_root.string(), run, unbound, nullptr, &detail));
        const auto after = std::distance(
            std::filesystem::directory_iterator(pair_root),
            std::filesystem::directory_iterator{});
        assert(before == after);
        std::filesystem::remove_all(pair_root);
    }

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
