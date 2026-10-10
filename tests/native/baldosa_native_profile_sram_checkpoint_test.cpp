// Actual shipping Modern typed stores, with a small deterministic simulated
// guest SRAM *after* a native RtlWriteSram checkpoint. No synthetic file
// formats or fake CAS; only the native host/guest execution is replaced here.
#include "baldosa_native_profile_sram_checkpoint.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>

using namespace ur::product;

namespace {
void write_raw(const std::filesystem::path& path,
               const std::array<std::uint8_t, kStockSramBytes>& bytes) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    assert(out);
    out.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    assert(out.good());
}

struct Fixture {
    std::filesystem::path root;
    HostProductState global;
    HostProfileState profile;
    std::array<std::uint8_t, kStockSramBytes> initial{};
    std::array<std::uint8_t, kStockSramBytes> live{};
    std::filesystem::path profile_path;
    std::filesystem::path native_path;

    explicit Fixture(const std::filesystem::path& dir) : root(dir) {
        constexpr const char* id = "checkpoint-rider";
        std::filesystem::create_directories(root / "saves/profile-checkpoint-rider");
        profile_path = root / "saves/profile-checkpoint-rider/host-profile.txt";
        native_path = root / "saves/profile-checkpoint-rider/save.srm";
        initial.fill(0x35);
        live = initial;
        profile = *make_default_host_profile_state(id);
        profile.racer_identity = *make_legacy_racer_identity(0);
        assert(capture_stock_sram_for_profile(
            ExecutionMode::Modern, profile, initial.data(), initial.size())
                == HostProfileTransferStatus::Applied);
        global.active_profile_id = id;
        assert(save_host_product_state_file(
            (root / "host-state-v1.txt").string(), global) ==
            HostProductSaveStatus::Saved);
        assert(save_host_profile_catalog_file(
            (root / "profiles-v1.txt").string(), {{id, *profile.racer_identity}}));
        assert(save_host_profile_state_file(
            ExecutionMode::Modern, profile_path.string(), profile) ==
            HostProfileSaveStatus::Saved);
        write_raw(native_path, initial);
    }

    BaldosaSramCheckpoint request() {
        return {root, global, profile, live.data(), live.size()};
    }

    HostProfileState read() const {
        const auto current = load_host_profile_state_file(
            ExecutionMode::Modern, profile_path.string(), profile.profile_id);
        assert(current.loaded());
        return *current.state;
    }
};
}  // namespace

int main() {
    namespace fs = std::filesystem;
    const auto root = fs::temp_directory_path() /
        ("ur-baldosa-typed-sram-checkpoint-test-" +
            std::to_string(
                static_cast<std::uint64_t>(
                    fs::file_time_type::clock::now().time_since_epoch().count())));
    fs::create_directories(root);

    {
        Fixture f(root / "unchanged");
        const auto baseline = f.read();
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::Unchanged);
        assert(f.read() == baseline);
    }
    {
        Fixture f(root / "real-post-save");
        const auto baseline = f.read();
        f.live[0x0748] = 7;
        f.live[0x0300] = 0xCC;
        // Caller MUST observe the native framework's completed SRAM write;
        // unsaved guest bytes are not permission to update the typed profile.
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::NativeSaveUnverified);
        assert(f.read() == baseline);
        write_raw(f.native_path, f.live);

        const auto actual = checkpoint_baldosa_native_profile_sram(f.request());
        assert(actual == BaldosaSramCheckpointStatus::Committed);
        const auto committed = f.read();
        assert(committed.autosave_generation ==
               baseline.autosave_generation + 1);
        assert(committed.stock_sram &&
               *committed.stock_sram == f.live);
        assert(committed.racer_identity == baseline.racer_identity);
        assert(committed.tour_continuation == baseline.tour_continuation);
        assert(committed.ghost_target == baseline.ghost_target);
        // A stale callback must not replay its own 8 KiB or generation over
        // another process's concurrently committed profile-state version.
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::ProfileConflict);
        assert(f.read() == committed);
        assert(fs::file_size(f.native_path) == kStockSramBytes);
    }
    {
        Fixture f(root / "selector-changed");
        f.live[22] = 9;
        write_raw(f.native_path, f.live);
        HostProductState newer = f.global;
        newer.active_profile_id.reset();
        assert(save_host_product_state_file(
            (f.root / "host-state-v1.txt").string(), newer) ==
            HostProductSaveStatus::Saved);
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::SelectionConflict);
        assert(f.read() == f.profile);
    }
    {
        Fixture f(root / "profile-concurrent");
        f.live[22] = 9;
        write_raw(f.native_path, f.live);
        auto newer = f.profile;
        newer.recent_track = 7;
        assert(save_host_profile_state_file(
            ExecutionMode::Modern, f.profile_path.string(), newer) ==
            HostProfileSaveStatus::Saved);
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::ProfileConflict);
        assert(f.read() == newer);
    }
    {
        Fixture f(root / "not-authorized");
        f.live[22] = 9;
        write_raw(f.native_path, f.live);
        assert(save_host_profile_catalog_file(
            (f.root / "profiles-v1.txt").string(), {}) );
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::UnauthorizedProfile);
        assert(f.read() == f.profile);
    }
    {
        Fixture f(root / "corrupt-native-save");
        f.live[22] = 9;
        write_raw(f.native_path, f.live);
        {
            std::ofstream out(f.native_path, std::ios::binary | std::ios::trunc);
            out << "SHORT";
        }
        assert(checkpoint_baldosa_native_profile_sram(f.request()) ==
               BaldosaSramCheckpointStatus::NativeSaveUnverified);
        assert(f.read() == f.profile);
    }
    {
        Fixture f(root / "invalid-size");
        auto bad = f.request();
        bad.guest_sram_size = 64;
        assert(checkpoint_baldosa_native_profile_sram(bad) ==
               BaldosaSramCheckpointStatus::InvalidContext);
        bad = f.request();
        bad.expected_global.active_profile_id = "another-rider";
        assert(checkpoint_baldosa_native_profile_sram(bad) ==
               BaldosaSramCheckpointStatus::InvalidContext);
        assert(f.read() == f.profile);
    }
    fs::remove_all(root);
    std::puts("PASS: exact native SRAM post-write typed Modern profile CAS; unchanged, selector change, races and invalid saves fail closed");
}
