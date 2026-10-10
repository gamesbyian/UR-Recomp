/* Native profile activation must read the existing Modern product codec and
 * fail closed before any guest SRAM is touched. Uses fake RTL save-root APIs,
 * but real product state / profile file codecs, not fake profile records. */
#include "host_product_state.hpp"
#include "host_profile_store.hpp"
#include "host_profile_runtime.hpp"

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <unistd.h>

extern "C" int ur_baldosa_modern_try_activate_profile(void);

/* Real pinned framework provides these. Keep the unit executable's tiny RTL
 * shim link-complete after adding the read-only first-frame SRAM witness. */
extern "C" {
unsigned char* g_sram = nullptr;
int g_sram_size = 0;
}

namespace {
std::string root = "saves";
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
    {
        std::ofstream save("saves/profile-rider-1/save.srm", std::ios::binary);
        std::vector<char> initialized(kStockSramBytes, static_cast<char>(0x31));
        save.write(initialized.data(), initialized.size());
        assert(save.good());
    }

    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves/profile-rider-1");
    assert(fs::file_size("saves/profile-rider-1/save.srm") == kStockSramBytes);
    assert(!fs::exists("saves/save.srm"));

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
