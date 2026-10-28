// ROM-free production Records and replay regression across two OS processes.
// Both executable invocations receive an ASCII fixture root. The real product
// receives UTF-8 strings for a subdirectory outside ordinary Windows ACPs,
// avoiding argv/codepage conversions in the test itself.
#include "completed_run_replay.hpp"
#include "completed_run_store.hpp"
#include "local_tournament_utf8_path.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace fs = std::filesystem;
using namespace ur::product;

namespace {

void require(bool passed, const char* reason) {
    if (!passed) throw std::runtime_error(reason);
}

CompletedRunRecord synthetic_run() {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1", "course:01", "race-1p"
    };
    run.elapsed_ticks60 = 1713;
    run.frame_count = 168;
    run.splits = {{"finish", 1713}};
    run.inputs = {{0, 120, 0x80, 0}, {120, 24, 0x81, 0},
                  {144, 24, 0x80, 0}};
    return run;
}

RunPlaybackTarget target_for(const CompletedRunRecord& run) {
    const auto& p = run.provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id,
            p.course_id, p.mode};
}

std::string read_all(const fs::path& file) {
    std::ifstream in(file, std::ios::binary);
    require(in.is_open(), "cannot reopen native Unicode replay input");
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}

} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 3, "usage: test ASCII_ROOT write|cold-read");
        const std::string mode = argv[2];
        require(mode == "write" || mode == "cold-read", "unknown test mode");
        // The Unicode part is built from a wide/native filesystem path. On
        // Windows, argv[1] alone is ordinary ASCII; no ACP-decorated argument
        // is used to supply or validate the production UTF-8 pathname.
        const fs::path root = fs::path(argv[1]) /
            fs::u8path(u8"player-漢字-資料-🚲");
        const fs::path archive = root / "runs" / "mike";
        const std::string archive_utf8 = archive.u8string();
        const auto expected = synthetic_run();
        const auto encoded = encode_completed_run_record(expected);
        require(!encoded.empty(), "invalid synthetic fixture");
        const auto target = target_for(expected);

        if (mode == "write") {
            std::string published, detail;
            require(append_completed_run_record(
                        archive_utf8, expected, &published, &detail),
                    "production append of Unicode .urrun failed");
            require(fs::is_regular_file(host_native_path_from_utf8(published)),
                    "published Unicode record path missing");
            require(read_all(host_native_path_from_utf8(published)) == encoded,
                    "published Unicode record bytes wrong");
            bool scanned = false;
            const auto inspected =
                inspect_completed_run_record_artifacts(archive_utf8, &scanned);
            require(scanned && inspected.size() == 1 &&
                        inspected[0].loaded(),
                    "Unicode archive not scanned after publication");
        } else {
            // Entirely new process: no retained in-memory run or replay path.
            const auto records = load_compatible_run_records(
                archive_utf8, target);
            require(records.size() == 1,
                    "cold process failed to enumerate Unicode .urrun");
            require(encode_completed_run_record(records[0].record) == encoded,
                    "cold process loaded different record content");
            const auto reloaded = reload_matching_completed_run_replay_record(
                records[0].path, expected, target);
            require(reloaded &&
                        encode_completed_run_record(*reloaded) == encoded,
                    "cold replay identity/content verification failed");
            CompletedRunReplayInputStage stage;
            require(stage.reserve(root.u8string()),
                    "cannot reserve UTF-8 replay namespace in cold process");
            const std::string staged_utf8 = stage.input_path();
            require(!staged_utf8.empty(),
                    "no selected replay input path");
            std::string detail;
            require(stage_completed_run_replay_input_file(
                        staged_utf8, *reloaded, &detail),
                    "cannot write exact Unicode replay input");
            const fs::path staged_native =
                host_native_path_from_utf8(staged_utf8);
            require(read_all(staged_native) ==
                        encode_completed_run_input_file(expected),
                    "cold replay input bytes differ from selected record");
            stage.clear();
            require(!fs::exists(staged_native),
                    "cold replay temporary input was not retired");
            require(read_all(host_native_path_from_utf8(records[0].path)) ==
                        encoded,
                    "replay cleanup modified the immutable earned record");
        }
#if defined(_WIN32)
        std::cout << " windows_acp=" << GetACP();
#endif
        std::cout << " DATA05_UNICODE_COLD_" <<
            (mode == "write" ? "WRITE" : "READ") << "=passed\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "DATA05_UNICODE_COLD=failed: " << e.what() << '\n';
        return 1;
    }
}
