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

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

/* Isolated QA-only selector transition. Never mint a second persistent
 * profile grammar: use the established catalog, profile-state and global
 * CAS writers with existing Modern format validation.
 */
static int add_second_named_profile(const std::filesystem::path& root,
                                    const std::filesystem::path& seed) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    constexpr const char* kFirst = "native-ci-rider";
    constexpr const char* kSecond = "native-ci-second";
    std::error_code ec;
    if (!fs::is_directory(root, ec) || ec ||
        !fs::is_regular_file(seed, ec) || ec ||
        fs::file_size(seed, ec) != kStockSramBytes || ec) return 21;
    const auto global_path = (root / "host-state-v1.txt").string();
    const auto roster_path = (root / "profiles-v1.txt").string();
    const auto original = load_host_product_state_file(global_path);
    auto roster = load_host_profile_catalog_file(roster_path);
    if (!original.loaded() || original.state->active_profile_id != kFirst ||
        !roster || roster->size() != 1 ||
        (*roster)[0].profile_id != kFirst) return 22;
    const auto first_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(kFirst));
    const auto second_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(kSecond));
    if (!first_root.isolated() || !second_root.isolated() ||
        first_root.save_root == second_root.save_root) return 23;
    const auto first_state = load_host_profile_state_file(
        ExecutionMode::Modern,
        (root / first_root.save_root / "host-profile.txt").string(), kFirst);
    if (!first_state.loaded() ||
        !profile_catalog_authorizes_state(*roster, *first_state.state))
        return 24;
    const auto second_dir = root / second_root.save_root;
    if (fs::exists(second_dir, ec) || ec) return 25;

    auto identity = make_legacy_racer_identity(1);
    auto second = make_default_host_profile_state(kSecond);
    if (!identity || !second) return 26;
    std::array<std::uint8_t, kStockSramBytes> bytes{};
    {
        std::ifstream in(seed, std::ios::binary);
        if (!in.read(reinterpret_cast<char*>(bytes.data()), bytes.size()))
            return 27;
    }
    // A harmless, test-owned discriminator in a separate SRAM namespace.
    // The actual native callback observes these bytes before the first
    // guest frame; this does NOT assert a valid completed course result.
    bytes[bytes.size() - 1] ^= 0x5Au;
    second->racer_identity = *identity;
    if (capture_stock_sram_for_profile(ExecutionMode::Modern, *second,
        bytes.data(), bytes.size()) != HostProfileTransferStatus::Applied)
        return 28;
    if (!fs::create_directories(second_dir, ec) || ec) return 29;
    if (save_host_profile_state_file(
            ExecutionMode::Modern, (second_dir / "host-profile.txt").string(),
            *second) != HostProfileSaveStatus::Saved) return 30;
    {
        std::ofstream out(second_dir / "save.srm", std::ios::binary);
        if (!out.write(reinterpret_cast<const char*>(bytes.data()),
                       bytes.size())) return 31;
    }
    const auto before_roster = *roster;
    roster->push_back({kSecond, *identity});
    if (save_host_profile_catalog_file_if_current(
            roster_path, before_roster, *roster) !=
            HostProfileCatalogSaveStatus::Saved) return 32;

    auto next = *original.state;
    next.active_profile_id = kSecond;
    // This pointer is the last publication. If another process raced it,
    // fail closed and leave a legitimate orphan for explicit QA teardown.
    if (save_host_product_state_file_if_current(
            global_path, *original.state, next) !=
            HostProductSaveStatus::Saved) return 33;
    std::fprintf(stdout,
        "UR_BALDOSA_NATIVE_PROFILE_FIXTURE switched=%s sram=%zu distinct=1\n",
        kSecond, bytes.size());
    return 0;
}

/* QA-only read-back through the original product stores. Establish that
 * the complete native save was published to the very same Modern profile
 * state, preserving the single existing persistence namespace.
 */
static int verify_native_checkpoint(const std::filesystem::path& root,
                                    const std::string& id) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    if (!root.is_absolute() || !is_safe_profile_storage_id(id)) return 41;
    const auto decision = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::optional<std::string>(id));
    if (!decision.isolated()) return 42;
    const auto profile = load_host_profile_state_file(
        ExecutionMode::Modern,
        (root / decision.save_root / "host-profile.txt").string(), id);
    const auto catalog = load_host_profile_catalog_file(
        (root / "profiles-v1.txt").string());
    if (!profile.loaded() || !catalog ||
        !profile_catalog_authorizes_state(*catalog, *profile.state) ||
        !profile.state->stock_sram) return 43;
    const auto native = root / decision.save_root / "save.srm";
    std::error_code ec;
    if (!fs::is_regular_file(native, ec) || ec ||
        fs::file_size(native, ec) != kStockSramBytes || ec)
        return 44;
    std::array<std::uint8_t, kStockSramBytes> bytes{};
    std::ifstream file(native, std::ios::binary);
    if (!file.read(reinterpret_cast<char*>(bytes.data()), bytes.size()))
        return 45;
    if (bytes != *profile.state->stock_sram) return 46;
    std::printf(
        "UR_BALDOSA_NATIVE_PROFILE VERIFIED profile=%s sram=%zu generation=%llu\n",
        id.c_str(), bytes.size(),
        static_cast<unsigned long long>(profile.state->autosave_generation));
    return 0;
}

int main(int argc, char** argv) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    constexpr const char* kProfile = "native-ci-rider";
    if (argc == 4 && std::strcmp(argv[3], "--verify-native-save") == 0)
        return verify_native_checkpoint(argv[1], argv[2]);
    if (argc == 4 && std::strcmp(argv[3], "--add-second") == 0)
        return add_second_named_profile(argv[1], argv[2]);
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
