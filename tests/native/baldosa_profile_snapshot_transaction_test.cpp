/* End-to-end typed Modern store transaction test. No fake serializers.
 * This DOES NOT exercise the full Baldosa guest or guest pause acknowledgement.
 * Those must be supplied before binding this candidate to the native host.
 */
#include "baldosa_profile_snapshot_transaction.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include <unistd.h>

using namespace ur::product;
namespace fs = std::filesystem;

struct Writer {
    fs::path sram;
    fs::path profile_path;
    HostProfileState expected_intermediate;
    const std::uint8_t* bytes = nullptr;
    bool succeed = true;
    bool overwrite_profile = false;
    bool invoked = false;
};

bool native_writer(void* context) {
    auto& writer = *static_cast<Writer*>(context);
    writer.invoked = true;
    if (writer.overwrite_profile) {
        auto concurrent = writer.expected_intermediate;
        concurrent.ghost_target = CompletedRunGhostTarget::Off;
        concurrent.autosave_generation += 10;
        assert(save_host_profile_state_file_if_current(
            ExecutionMode::Modern, writer.profile_path.string(),
            writer.expected_intermediate, concurrent) ==
            HostProfileSaveStatus::Saved);
    }
    if (!writer.succeed) return false;
    std::ofstream out(writer.sram, std::ios::binary | std::ios::trunc);
    out.write(reinterpret_cast<const char*>(writer.bytes), kStockSramBytes);
    return out.good();
}

void assert_profile(const fs::path& file, const HostProfileState& expected) {
    auto actual = load_host_profile_state_file(
        ExecutionMode::Modern, file.string(), expected.profile_id);
    assert(actual.loaded() && *actual.state == expected);
}

int main() {
    constexpr const char* id = "rider-a";
    fs::path dir = fs::temp_directory_path() /
        ("ur-baldosa-snapshot-cas-" + std::to_string(getpid()));
    assert(fs::create_directory(dir));
    auto profile_root = dir / "saves/profile-rider-a";
    assert(fs::create_directories(profile_root));
    auto profile_path = profile_root / "host-profile.txt";
    auto native_sram = profile_root / "save.srm";

    HostProductState global{};
    global.active_profile_id = id;
    auto identity = make_legacy_racer_identity(0);
    assert(identity);
    auto profile = make_default_host_profile_state(id);
    assert(profile);
    profile->racer_identity = *identity;
    std::array<std::uint8_t, kStockSramBytes> old{};
    old.fill(0x41u);
    assert(capture_stock_sram_for_profile(
        ExecutionMode::Modern, *profile, old.data(), old.size()) ==
        HostProfileTransferStatus::Applied);
    assert(save_host_product_state_file(
        (dir / "host-state-v1.txt").string(), global) ==
        HostProductSaveStatus::Saved);
    assert(save_host_profile_catalog_file(
        (dir / "profiles-v1.txt").string(), {{id, *identity}}));
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), *profile) ==
        HostProfileSaveStatus::Saved);
    { std::ofstream out(native_sram, std::ios::binary);
      out.write(reinterpret_cast<const char*>(old.data()), old.size());
      assert(out.good()); }

    std::array<std::uint8_t, kStockSramBytes> changed{};
    changed.fill(0x97u);
    auto candidate = *profile;
    assert(capture_stock_sram_for_profile(
        ExecutionMode::Modern, candidate, changed.data(), changed.size()) ==
        HostProfileTransferStatus::Applied);
    Writer writer{native_sram, profile_path, candidate, changed.data()};
    BaldosaProfileCommitRequest req{
        dir, id, global, *profile, changed.data(), changed.size(), false,
        native_writer, &writer};

    // No guest checkpoint acknowledgement: no native writes or profile CAS.
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::Rejected);
    assert(!writer.invoked);
    assert_profile(profile_path, *profile);

    req.native_checkpoint_acknowledged = true;
    // A missing catalog identity must also reject before the writer.
    assert(save_host_profile_catalog_file(
        (dir / "profiles-v1.txt").string(), {}));
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::Rejected);
    assert(!writer.invoked);
    assert(save_host_profile_catalog_file(
        (dir / "profiles-v1.txt").string(), {{id, *identity}}));

    // The old host-state selector must remain exactly the one observed at
    // native boot. Otherwise do not write any profile or SRAM.
    HostProductState other = global;
    other.active_profile_id = "rider-b";
    assert(save_host_product_state_file(
        (dir / "host-state-v1.txt").string(), other) ==
        HostProductSaveStatus::Saved);
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::SelectorChanged);
    assert(!writer.invoked);
    assert(save_host_product_state_file(
        (dir / "host-state-v1.txt").string(), global) ==
        HostProductSaveStatus::Saved);

    // The stored profile is a complete CAS baseline, never a stale cached
    // record. A competing generation must not be rolled over.
    auto third_party = *profile;
    third_party.autosave_generation += 1;
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), third_party) ==
        HostProfileSaveStatus::Saved);
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::ProfileChanged);
    assert(!writer.invoked);
    assert_profile(profile_path, third_party);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), *profile) ==
        HostProfileSaveStatus::Saved);

    // Native SRAM I/O failure: rollback ONLY the exact intermediate state.
    writer.succeed = false;
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::NativeSramWriteFailed);
    assert(writer.invoked);
    assert_profile(profile_path, *profile);
    writer.invoked = false;

    // A concurrent writer replacing our candidate before failure owns the
    // new state. Never overwrite them with an unguarded rollback.
    writer.overwrite_profile = true;
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::RollbackConflict);
    auto interrupted = load_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), id);
    assert(interrupted.loaded());
    assert(interrupted.state->autosave_generation ==
           candidate.autosave_generation + 10);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), *profile) ==
        HostProfileSaveStatus::Saved);

    writer.overwrite_profile = false;
    writer.succeed = true;
    writer.invoked = false;
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::Saved);
    assert(writer.invoked);
    assert_profile(profile_path, candidate);
    { std::ifstream in(native_sram, std::ios::binary);
      const std::vector<unsigned char> written(
          (std::istreambuf_iterator<char>(in)),
          std::istreambuf_iterator<char>());
      assert(written.size() == changed.size());
      for (std::size_t i = 0; i < changed.size(); ++i)
          assert(written[i] == changed[i]); }
    assert(load_host_product_state_file(
        (dir / "host-state-v1.txt").string()).state->active_profile_id == id);

    // Retrying with the stale guest baseline must fail closed.
    assert(commit_baldosa_profile_snapshot(req) ==
        BaldosaProfileCommitStatus::ProfileChanged);

    // An already-synchronized image must not bump autosave_generation.
    auto fresh = req;
    fresh.expected_profile = candidate;
    fresh.frozen_guest_sram = changed.data();
    writer.invoked = false;
    assert(commit_baldosa_profile_snapshot(fresh) ==
        BaldosaProfileCommitStatus::Unchanged);
    assert(!writer.invoked);
    assert_profile(profile_path, candidate);

    fs::remove_all(dir);
    std::puts("PASS: acknowledged native guest SRAM CAS, stale selector/profile protection, conditional rollback");
    return 0;
}
