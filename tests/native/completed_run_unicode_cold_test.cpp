// ROM-free production Records and replay regression across two OS processes.
// Both executable invocations receive an ASCII fixture root. The real product
// receives UTF-8 strings for a subdirectory outside ordinary Windows ACPs,
// avoiding argv/codepage conversions in the test itself.
#include "baldosa_native_options.hpp"
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


struct OptionsHostState {
    int fullscreen = 0;
    int vsync = 1;
    int volume = 100;
    int display_applies = 0;
};

bool options_get_display(void* context, int* fullscreen, int* vsync) {
    const auto& host = *static_cast<OptionsHostState*>(context);
    *fullscreen = host.fullscreen;
    *vsync = host.vsync;
    return true;
}

bool options_apply_display(void* context, int fullscreen, int vsync) {
    auto& host = *static_cast<OptionsHostState*>(context);
    host.fullscreen = fullscreen;
    host.vsync = vsync;
    ++host.display_applies;
    return true;
}

int options_get_volume(void* context) {
    return static_cast<OptionsHostState*>(context)->volume;
}

int options_set_volume(void* context, int percent) {
    auto& host = *static_cast<OptionsHostState*>(context);
    host.volume = percent;
    return percent;
}

BaldosaOptionsHost options_host(OptionsHostState& host) {
    BaldosaOptionsHost result;
    result.ctx = &host;
    result.get_display = &options_get_display;
    result.apply_display = &options_apply_display;
    result.get_volume = &options_get_volume;
    result.set_volume = &options_set_volume;
    return result;
}

void write_unicode_options(const fs::path& root) {
    const auto options_utf8 = baldosa_options_path(root).u8string();
    OptionsHostState live;
    BaldosaNativeOptions model;
    baldosa_options_boot(model, options_utf8, options_host(live));
    require(model.load == BaldosaOptionsLoad::Missing,
            "Unicode Options fixture unexpectedly preexists");
    baldosa_options_open(model);
    baldosa_options_move(model, 1);  // VSYNC, not a synthetic file write.
    baldosa_options_adjust(model, -1);  // ON -> OFF through product model.
    require(model.status == BaldosaOptionsStatus::Saved &&
                model.vsync == HostVSyncMode::Off && live.vsync == 0,
            "production Options edit did not save or apply");
    require(fs::is_regular_file(host_native_path_from_utf8(options_utf8)),
            "Unicode Options file missing after product save");
}

void cold_read_unicode_options(const fs::path& root) {
    const auto options_utf8 = baldosa_options_path(root).u8string();
    const auto native_path = host_native_path_from_utf8(options_utf8);
    const auto before = read_all(native_path);
    require(!before.empty(), "Unicode Options file absent on cold reopen");
    OptionsHostState fresh_host;  // New OS process begins with VSYNC ON.
    BaldosaNativeOptions model;
    baldosa_options_boot(model, options_utf8, options_host(fresh_host));
    require(model.load == BaldosaOptionsLoad::Loaded &&
                model.vsync == HostVSyncMode::Off &&
                fresh_host.vsync == 0 && fresh_host.display_applies == 1,
            "cold Options boot did not apply saved Unicode settings");
    require(read_all(native_path) == before,
            "cold Options boot modified saved settings");
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
            write_unicode_options(root);
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
            cold_read_unicode_options(root);
        }
#if defined(_WIN32)
        std::cout << " windows_acp=" << GetACP();
#endif
        std::cout << " DATA05_UNICODE_OPTIONS_" <<
            (mode == "write" ? "WRITE" : "COLD_READ") << "=passed\n";
        std::cout << " DATA05_UNICODE_COLD_" <<
            (mode == "write" ? "WRITE" : "READ") << "=passed\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "DATA05_UNICODE_COLD=failed: " << e.what() << '\n';
        return 1;
    }
}
