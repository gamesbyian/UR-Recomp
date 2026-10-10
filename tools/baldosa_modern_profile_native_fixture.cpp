/* Native QA ONLY: produce one authentic Modern profile using the same
 * codecs/stores and path scheme as the shipping frontend. No fake serialization,
 * sample user directory, new persistent format, or game-specific test mode.
 *
 * Usage: ur-baldosa-profile-fixture EMPTY_USER_ROOT EXISTING_8192B_SRM
 */
#include "host_product_store.hpp"
#include "host_profile_store.hpp"
#include "host_profile_catalog.hpp"
#include "host_profile_runtime.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    constexpr const char* kProfile = "native-ci-rider";
    if (argc != 3) return 2;

    const fs::path root(argv[1]);
    const fs::path seed(argv[2]);
    std::error_code ec;
    if (!fs::is_directory(root, ec) || ec ||
        !fs::is_regular_file(seed, ec) || ec ||
        fs::file_size(seed, ec) != kStockSramBytes || ec ||
        fs::exists(root / "host-state-v1.txt", ec) || ec) return 3;

    auto profile = make_default_host_profile_state(kProfile);
    auto identity = make_legacy_racer_identity(0);
    if (!profile || !identity) return 4;
    std::array<std::uint8_t, kStockSramBytes> source{};
    {
        std::ifstream in(seed, std::ios::binary);
        if (!in.read(reinterpret_cast<char*>(source.data()), source.size()))
            return 5;
    }
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, *profile,
            source.data(), source.size()) != HostProfileTransferStatus::Applied)
        return 6;
    profile->racer_identity = *identity;

    const auto resolved = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(kProfile));
    if (!resolved.isolated()) return 7;
    const fs::path save_root = root / resolved.save_root;
    if (!fs::create_directories(save_root, ec) || ec) return 8;
    if (save_host_profile_state_file(
            ExecutionMode::Modern, (save_root / "host-profile.txt").string(),
            *profile) != HostProfileSaveStatus::Saved) return 9;
    if (!fs::copy_file(seed, save_root / "save.srm",
                       fs::copy_options::none, ec) || ec) return 10;
    if (!save_host_profile_catalog_file(
            (root / "profiles-v1.txt").string(),
            {{kProfile, *identity}})) return 11;
    HostProductState global{};
    global.active_profile_id = kProfile;
    if (save_host_product_state_file(
            (root / "host-state-v1.txt").string(), global) !=
            HostProductSaveStatus::Saved) return 12;

    const auto reread = load_host_profile_state_file(
        ExecutionMode::Modern, (save_root / "host-profile.txt").string(),
        kProfile);
    const auto roster = load_host_profile_catalog_file(
        (root / "profiles-v1.txt").string());
    if (!reread.loaded() || !roster ||
        !profile_catalog_authorizes_state(*roster, *reread.state)) return 13;

    std::fprintf(stdout,
        "UR_BALDOSA_NATIVE_PROFILE_FIXTURE id=%s state=1 catalog=1 sram=%zu\n",
        kProfile, source.size());
    return 0;
}
