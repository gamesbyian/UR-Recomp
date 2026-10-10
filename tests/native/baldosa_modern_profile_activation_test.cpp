/* Native profile activation must read the existing Modern product codec and
 * fail closed before any guest SRAM is touched. Uses fake RTL save-root APIs,
 * but real product state / profile file codecs, not fake profile records. */
#include "host_product_state.hpp"
#include "host_profile_store.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_catalog.hpp"
#include "baldosa_native_profile_sram_checkpoint.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <unistd.h>

extern "C" int ur_baldosa_modern_try_activate_profile(void);
extern "C" int ur_baldosa_modern_profile_before_native_save(void);
extern "C" int ur_baldosa_modern_profile_finish_native_save(int);

/* Real pinned framework provides these. Keep the unit executable's tiny RTL
 * shim link-complete after adding the read-only first-frame SRAM witness. */
extern "C" {
unsigned char* g_sram = nullptr;
int g_sram_size = 0;
}

namespace {
std::string root = "saves";
std::string selected_racer;
}

extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name) {
    selected_racer = name ? name : "";
}

extern "C" void RtlSetSaveRoot(const char* value) {
    root = value && *value ? value : "saves";
}
extern "C" const char* RtlSaveRoot(void) { return root.c_str(); }
extern "C" void RtlEnsureSaveDir(void) {
    std::filesystem::create_directories(root);
}

int main() {
    namespace fs = std::filesystem;
    using namespace ur::product;

    const auto dir = fs::temp_directory_path() /
        ("ur-baldosa-real-modern-profile-" + std::to_string(getpid()));
    fs::create_directories(dir);
    assert(chdir(dir.c_str()) == 0);
    assert(setenv("SNESRECOMP_USER_DATA_DIR", dir.c_str(), 1) == 0);
    assert(setenv("UR_BALDOSA_MODERN_PROFILE_SELECT", "1", 1) == 0);
    assert(unsetenv("UR_HOST_STATE_PATH") == 0);
    assert(unsetenv("UR_EXECUTION_MODE") == 0);

    // A missing state is a new Modern installation, not an unnamed profile.
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves");

    HostProductState state{};
    state.active_profile_id = "rider-1";
    {
        std::ofstream output("host-state-v1.txt", std::ios::binary);
        assert(output << encode_host_product_state(state));
    }

    // A registered active name with no actual profile state must NOT silently
    // create (or initialize from) another player's generic save.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");

    fs::create_directories("saves/profile-rider-1");
    auto profile = make_default_host_profile_state("rider-1");
    assert(profile.has_value());
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);

    // Initializing guest SRAM is the existing frontend's job, not this
    // read-only selector. We must not create a blank 8 KiB save here.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");
    std::array<std::uint8_t, kStockSramBytes> initialized{};
    initialized.fill(0x31u);
    {
        std::ofstream save("saves/profile-rider-1/save.srm", std::ios::binary);
        save.write(reinterpret_cast<const char*>(initialized.data()),
                   initialized.size());
        assert(save.good());
    }

    // An identity-less named file is not an authorized Modern player, even
    // when a valid 8 KiB native SRAM happens to exist beside it.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");

    const auto identity = make_legacy_racer_identity(0);
    assert(identity.has_value());
    profile->racer_identity = *identity;
    assert(capture_stock_sram_for_profile(
        ExecutionMode::Modern, *profile, initialized.data(),
        initialized.size()) == HostProfileTransferStatus::Applied);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);

    // Even complete metadata remains untrusted until registered in the
    // original Modern catalog. Do not infer roster membership from filename.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");
    assert(save_host_profile_catalog_file(
        "profiles-v1.txt", {{"rider-1", *identity}}));
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves/profile-rider-1");
    assert(selected_racer == identity->name);
    assert(fs::file_size("saves/profile-rider-1/save.srm") == kStockSramBytes);
    assert(!fs::exists("saves/save.srm"));

    // The original framework write MUST be preceded by a compatible typed
    // selection check under the canonical OS lock, retained until CAS.
    g_sram = initialized.data();
    g_sram_size = static_cast<int>(initialized.size());
    const std::string global_path = (dir / "host-state-v1.txt").string();
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    {
        TournamentLaunchPathLock competing(global_path, true);
        assert(!competing.acquired());
    }
    assert(ur_baldosa_modern_profile_finish_native_save(1) == 1);
    {
        TournamentLaunchPathLock released(global_path, true);
        assert(released.acquired());
    }

    // An external Modern instance can change selector/profile while this
    // native process runs; shutdown must refuse BEFORE writing raw SRAM.
    const fs::path selected_raw = "saves/profile-rider-1/save.srm";
    const auto original_raw_size = fs::file_size(selected_raw);
    const auto assert_raw_unchanged = [&] {
        std::array<std::uint8_t, kStockSramBytes> raw{};
        std::ifstream in(selected_raw, std::ios::binary);
        assert(in);
        in.read(reinterpret_cast<char*>(raw.data()), raw.size());
        assert(in.gcount() == static_cast<std::streamsize>(raw.size()));
        assert(raw == initialized);
    };
    HostProductState different_selector = state;
    different_selector.active_profile_id.reset();
    assert(save_host_product_state_file(global_path, different_selector) ==
           HostProductSaveStatus::Saved);
    assert(ur_baldosa_modern_profile_before_native_save() == 0);
    assert(fs::file_size("saves/profile-rider-1/save.srm") ==
           original_raw_size);
    assert_raw_unchanged();
    assert(save_host_product_state_file(global_path, state) ==
           HostProductSaveStatus::Saved);

    auto newer_profile = *profile;
    newer_profile.recent_track = 7;
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        newer_profile) == HostProfileSaveStatus::Saved);
    assert(ur_baldosa_modern_profile_before_native_save() == 0);
    assert(fs::file_size("saves/profile-rider-1/save.srm") ==
           original_raw_size);
    assert_raw_unchanged();
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);

    // Failed upstream SRAM I/O must also release the selector lease.
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    assert(ur_baldosa_modern_profile_finish_native_save(0) == 0);
    {
        TournamentLaunchPathLock released(global_path, true);
        assert(released.acquired());
    }

    // The successful path still delegates the actual guest bytes to the
    // framework save, then publishes only the validated typed Modern CAS.
    std::array<std::uint8_t, kStockSramBytes> advanced = initialized;
    advanced[0x0748] ^= 0xC3u;
    g_sram = advanced.data();
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    {
        std::ofstream raw(selected_raw, std::ios::binary | std::ios::trunc);
        assert(raw);
        raw.write(reinterpret_cast<const char*>(advanced.data()),
                  advanced.size());
        assert(raw.good());
    }
    assert(ur_baldosa_modern_profile_finish_native_save(1) == 1);
    const auto after_real_save = load_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        "rider-1");
    assert(after_real_save.loaded());
    assert(after_real_save.state->stock_sram &&
           *after_real_save.state->stock_sram == advanced);
    assert(fs::file_size(selected_raw) == original_raw_size);

    // An invalid loaded selector must NEVER downgrade to default saves.
    state.active_profile_id = "../other-player";
    {
        std::ofstream output("host-state-v1.txt", std::ios::binary | std::ios::trunc);
        output << "not-a-valid-modern-host-state\n";
    }
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves/profile-rider-1");

    // The existing Authentic mode has no Modern profile authority.
    assert(setenv("UR_EXECUTION_MODE", "authentic", 1) == 0);
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves/profile-rider-1");

    assert(chdir("/") == 0);
    fs::remove_all(dir);
    std::puts("PASS: native Modern pre-SRAM profile root respects exact stored state and fails closed");
}
