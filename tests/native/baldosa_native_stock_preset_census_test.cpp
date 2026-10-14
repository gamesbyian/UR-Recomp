#include "baldosa_native_first_profile.hpp"
#include "baldosa_native_second_profile.hpp"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

static std::string read_exact(const fs::path& file) {
    std::ifstream in(file, std::ios::binary);
    assert(in.is_open());
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}

static void require_stock_racer(const fs::path& root,
                                const HostProfileCatalogEntry& entry,
                                std::size_t preset) {
    const auto identity = make_legacy_racer_identity(preset);
    assert(identity && *identity == entry.identity);
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, entry.profile_id);
    assert(location.isolated());
    assert(baldosa_native_selected_profile_paths_are_real(
        root, location.save_root));
    const auto typed = load_host_profile_state_file(
        ExecutionMode::Modern,
        (root / location.save_root / "host-profile.txt").string(),
        entry.profile_id);
    assert(typed.loaded() && typed.state->racer_identity == identity &&
           typed.state->stock_sram);
    auto source = clean_stock_sram();
    source[0x0748] = identity->rider_index;
    assert(*typed.state->stock_sram == source);
    assert(stock_sram_format_signature_present(
        typed.state->stock_sram->data(), typed.state->stock_sram->size()));
    assert(baldosa_sram_file_matches_exact(
        root / location.save_root / "save.srm", source.data(), source.size()));
    assert(read_exact(root / location.save_root / "save.srm").size() ==
           kStockSramBytes);
}

int main() {
    const fs::path root = fs::temp_directory_path() /
        ("baldosa-preset-census-" + std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    assert(fs::create_directory(root));
    const auto& presets = legacy_racer_presets();
    assert(presets.size() == 16);
    unsigned count_first = 0, count_second = 0;

    // This is a product-store census, not a real native SDL/guest 16-racer
    // UI survey. Every cold-install preset must publish its OWN rider byte,
    // exact typed/raw full SRAM, one catalog entry and one active selector.
    for (std::size_t n = 0; n < presets.size(); ++n) {
        const fs::path home = root / ("first-" + std::to_string(n));
        assert(fs::create_directory(home));
        const auto identity = make_legacy_racer_identity(n);
        assert(identity && identity->rider_index == n);
        const auto created = create_baldosa_first_preset_for_next_boot(home, n);
        const auto canonical_id = make_profile_id(identity->name, {});
        assert(created.created() && created.profile_id == canonical_id);
        const auto selected = load_host_product_state_file(
            (home / "host-state-v1.txt").string());
        const auto roster = load_host_profile_catalog_file(
            (home / "profiles-v1.txt").string());
        assert(selected.loaded() &&
               selected.state->active_profile_id == canonical_id);
        assert(roster && roster->size() == 1u &&
               roster->front().profile_id == canonical_id);
        require_stock_racer(home, roster->front(), n);
        const auto typed_path = home / "saves" /
            ("profile-" + canonical_id) / "host-profile.txt";
        const std::string typed_prior = read_exact(typed_path);
        const std::string raw_prior = read_exact(
            home / "saves" / ("profile-" + canonical_id) / "save.srm");
        assert(create_baldosa_first_preset_for_next_boot(
                   home, n).status == BaldosaFirstRacerStatus::AlreadyConfigured);
        assert(read_exact(typed_path) == typed_prior);
        assert(read_exact(home / "saves" /
               ("profile-" + canonical_id) / "save.srm") == raw_prior);
        ++count_first;
    }

    // Every alternative stock preset can be the *new P2*, not an overwrite
    // of a current Mike P1. The global selector and original P1 SRAM/typed
    // snapshots must survive byte-identically, including its catalog row.
    for (std::size_t n = 1; n < presets.size(); ++n) {
        const fs::path home = root / ("second-" + std::to_string(n));
        assert(fs::create_directory(home));
        const auto p1 = create_baldosa_first_preset_for_next_boot(home, 0);
        assert(p1.created() && p1.profile_id == "mike");
        const fs::path selected_path = home / "host-state-v1.txt";
        const fs::path catalog_path = home / "profiles-v1.txt";
        const fs::path mike_typed =
            home / "saves/profile-mike/host-profile.txt";
        const fs::path mike_raw = home / "saves/profile-mike/save.srm";
        const std::string selector_before = read_exact(selected_path);
        const std::string mike_typed_before = read_exact(mike_typed);
        const std::string mike_raw_before = read_exact(mike_raw);
        const auto requested = make_legacy_racer_identity(n);
        assert(requested);
        const std::string candidate = make_profile_id(
            requested->name, {{p1.profile_id, *make_legacy_racer_identity(0)}});
        const auto created = create_baldosa_second_preset_for_next_boot(
            home, "mike", n);
        assert(created.created() && created.profile_id == candidate &&
               candidate != p1.profile_id);
        const auto roster =
            load_host_profile_catalog_file(catalog_path.string());
        assert(roster && roster->size() == 2u &&
               (*roster)[0].profile_id == p1.profile_id &&
               (*roster)[1].profile_id == created.profile_id);
        require_stock_racer(home, (*roster)[0], 0);
        require_stock_racer(home, (*roster)[1], n);
        assert(read_exact(selected_path) == selector_before);
        assert(read_exact(mike_typed) == mike_typed_before);
        assert(read_exact(mike_raw) == mike_raw_before);
        const auto catalog_after = read_exact(catalog_path);
        assert(create_baldosa_second_preset_for_next_boot(
                   home, "mike", n).status ==
               BaldosaSecondRacerStatus::ExistingData);
        assert(read_exact(catalog_path) == catalog_after);
        assert(read_exact(selected_path) == selector_before);
        assert(read_exact(mike_raw) == mike_raw_before);
        ++count_second;
    }

    // Out-of-range stock names must not introduce a new directory or row.
    assert(!make_legacy_racer_identity(16).has_value());
    assert(!make_legacy_racer_identity(999).has_value());
    const auto ignored = root / "out-of-range";
    assert(fs::create_directory(ignored));
    assert(create_baldosa_first_preset_for_next_boot(
               ignored, 16).status == BaldosaFirstRacerStatus::Invalid);
    assert(!fs::exists(ignored / "host-state-v1.txt"));
    assert(!fs::exists(ignored / "profiles-v1.txt"));
    assert(count_first == 16 && count_second == 15);
    fs::remove_all(root);
    std::printf("PASS: %u first-racer and %u independent second-racer "
                "stock presets, exact isolated 8192-byte typed/raw SRAM, "
                "catalog identity and P1 selector preservation\n",
                count_first, count_second);
}
