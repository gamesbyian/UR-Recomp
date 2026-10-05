#include "host_profile_catalog.hpp"
#include "host_profile_state.hpp"
#include "host_profile_store.hpp"
#include "modern_racer_identity.hpp"
#include "completed_run_store.hpp"
#include "clean_stock_sram.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
CompletedRunRecord fixture_run(std::uint64_t ticks) {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.splits = {{"finish", ticks}};
    return record;
}

RunPlaybackTarget fixture_target() {
    const auto p = fixture_run(1).provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}
}  // namespace

int main(int argc, char** argv) {
    assert(argc == 3);
    const std::filesystem::path root(argv[2]);
    std::filesystem::create_directories(root);
    const auto& presets = legacy_racer_presets();
    static const char* names[16] = {
        "MIKE","ANDREW","MARTIN","MELISSA","AMY","MALCOLM","MICHELLE","COLIN",
        "DAVE","TONY","CAROL","CRAIG","KEN","ROBBIE","ALICE","STEVE"
    };
    static const char* colours[16] = {
        "red","blue","green","yellow","orange","cyan","lime","blue",
        "white","black","pink","teal","purple","red","green","blue"
    };
    for (std::size_t i = 0; i < presets.size(); ++i) {
        assert(presets[i].rider_index == i);
        assert(presets[i].name == names[i]);
        assert(presets[i].colour_label == colours[i]);
        const auto identity = make_legacy_racer_identity(i);
        assert(identity && identity->rider_index == i && identity->name == names[i]);
    }
    assert(stock_forbidden_name_match("SONIC"));
    assert(stock_forbidden_name_match("XSEGAX"));
    assert(stock_forbidden_name_match("BASSIST"));
    assert(!stock_forbidden_name_match("ZED"));
    assert(!valid_racer_name(""));
    assert(!valid_racer_name("                "));
    assert(valid_racer_name("A B"));
    assert(valid_racer_name("1234567890ABCDEF"));
    assert(!valid_racer_name("1234567890ABCDEFG"));

    const auto& clean_sram = clean_stock_sram();
    assert(clean_sram.size() == kStockSramBytes);
    assert(clean_sram[0] == static_cast<std::uint8_t>('A'));
    assert(clean_sram[1] == static_cast<std::uint8_t>('S'));
    assert(clean_sram[2] == static_cast<std::uint8_t>('J'));
    assert(clean_sram[3] == static_cast<std::uint8_t>('I'));
    std::array<std::uint8_t, kStockSramBytes> unrelated_live_sram{};
    unrelated_live_sram.fill(0x77);
    auto fresh_profile = make_default_host_profile_state("fresh");
    assert(fresh_profile);
    assert(capture_stock_sram_for_profile(
               ExecutionMode::Modern,
               *fresh_profile,
               clean_sram.data(),
               clean_sram.size()) == HostProfileTransferStatus::Applied);
    assert(fresh_profile->stock_sram.has_value());
    assert(*fresh_profile->stock_sram != unrelated_live_sram);

    const std::string a_path = (root / "alpha.profile").string();
    const std::string b_path = (root / "beta.profile").string();
    const std::string cat_path = (root / "profiles.catalog").string();
    assert(!load_host_profile_catalog_file(""));
    const auto absent_catalog =
        load_host_profile_catalog_file((root / "absent.catalog").string());
    assert(absent_catalog && absent_catalog->empty());

    if (std::string(argv[1]) == "bootstrap") {
        auto a = make_default_host_profile_state("alpha");
        auto b = make_default_host_profile_state("beta");
        assert(a && b);
        a->racer_identity = HostRacerIdentity{"SONIC", 0};
        b->racer_identity = HostRacerIdentity{"STEVE", 15};
        std::array<std::uint8_t, kStockSramBytes> a_sram{};
        std::array<std::uint8_t, kStockSramBytes> b_sram{};
        a_sram.fill(0x11); b_sram.fill(0x22);
        a->stock_sram = a_sram; b->stock_sram = b_sram;
        a->ghost_target = CompletedRunGhostTarget::Previous;
        b->ghost_target = CompletedRunGhostTarget::PersonalBest;
        assert(save_host_profile_state_file(ExecutionMode::Modern, a_path, *a) == HostProfileSaveStatus::Saved);
        assert(save_host_profile_state_file(ExecutionMode::Modern, b_path, *b) == HostProfileSaveStatus::Saved);
        std::vector<HostProfileCatalogEntry> entries{
            {"alpha", *a->racer_identity}, {"beta", *b->racer_identity}
        };
        assert(save_host_profile_catalog_file(cat_path, entries));

        std::string detail;
        assert(append_completed_run_record(
            (root / "runs" / "alpha").string(),
            fixture_run(1800), nullptr, &detail));
        assert(append_completed_run_record(
            (root / "runs" / "beta").string(),
            fixture_run(1700), nullptr, &detail));
        return 0;
    }

    assert(std::string(argv[1]) == "fresh");
    auto a = load_host_profile_state_file(ExecutionMode::Modern, a_path, "alpha");
    auto b = load_host_profile_state_file(ExecutionMode::Modern, b_path, "beta");
    assert(a.loaded() && b.loaded());
    assert(a.state->racer_identity && a.state->racer_identity->name == "SONIC");
    assert(b.state->racer_identity && b.state->racer_identity->rider_index == 15);
    assert((*a.state->stock_sram)[0] == 0x11 && (*b.state->stock_sram)[0] == 0x22);
    assert(a.state->ghost_target == CompletedRunGhostTarget::Previous);
    assert(b.state->ghost_target == CompletedRunGhostTarget::PersonalBest);

    const auto alpha_runs = load_compatible_run_records(
        (root / "runs" / "alpha").string(), fixture_target());
    const auto beta_runs = load_compatible_run_records(
        (root / "runs" / "beta").string(), fixture_target());
    assert(alpha_runs.size() == 1 && beta_runs.size() == 1);
    assert(alpha_runs[0].record.elapsed_ticks60 == 1800);
    assert(beta_runs[0].record.elapsed_ticks60 == 1700);

    auto cat = load_host_profile_catalog_file(cat_path);
    assert(cat && cat->size() == 2);
    assert((*cat)[0].profile_id == "alpha" && (*cat)[1].profile_id == "beta");
    assert(catalog_entry_matches_profile_state((*cat)[0], *a.state));
    assert(catalog_entry_matches_profile_state((*cat)[1], *b.state));
    assert(profile_catalog_authorizes_state(*cat, *a.state));
    assert(profile_catalog_authorizes_state(*cat, *b.state));
    auto mismatched = (*cat)[0];
    mismatched.identity.rider_index = 1;
    assert(!catalog_entry_matches_profile_state(mismatched, *a.state));
    auto mismatched_catalog = *cat;
    mismatched_catalog[0] = mismatched;
    assert(!profile_catalog_authorizes_state(mismatched_catalog, *a.state));
    auto missing_identity = *a.state;
    missing_identity.racer_identity.reset();
    assert(!catalog_entry_matches_profile_state((*cat)[0], missing_identity));
    assert(!profile_catalog_authorizes_state(*cat, missing_identity));
    auto wrong_profile = *a.state;
    wrong_profile.profile_id = "other";
    assert(!catalog_entry_matches_profile_state((*cat)[0], wrong_profile));
    assert(!profile_catalog_authorizes_state(*cat, wrong_profile));
    auto missing_snapshot = *a.state;
    missing_snapshot.stock_sram.reset();
    assert(!profile_catalog_authorizes_state(*cat, missing_snapshot));

    auto renamed = *a.state;
    renamed.racer_identity->name = "HASSAN";
    assert(stock_forbidden_name_match(renamed.racer_identity->name));
    assert(save_host_profile_state_file(ExecutionMode::Modern, a_path, renamed) == HostProfileSaveStatus::Saved);
    (*cat)[0].identity = *renamed.racer_identity;
    assert(save_host_profile_catalog_file(cat_path, *cat));

    auto reloaded = load_host_profile_state_file(ExecutionMode::Modern, a_path, "alpha");
    assert(reloaded.loaded() && reloaded.state->racer_identity->name == "HASSAN");
    auto cat2 = load_host_profile_catalog_file(cat_path);
    assert(cat2 && (*cat2)[0].identity.name == "HASSAN");
    assert(profile_catalog_authorizes_state(*cat2, *reloaded.state));
    assert((*reloaded.state->stock_sram)[0] == 0x11);
    assert((*b.state->stock_sram)[0] == 0x22);

    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|0|MIKE\n"
        "alpha|1|ANDREW\n"));
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|0|MIKE\n"
        "ALPHA|1|ANDREW\n"));
    assert(encode_host_profile_catalog({
        {"alpha", {"MIKE", 0}},
        {"ALPHA", {"ANDREW", 1}},
    }).empty());

    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "CON|0|MIKE\n"));
    assert(encode_host_profile_catalog({
        {"NUL", {"MIKE", 0}},
    }).empty());
    assert(make_profile_id("CON", {}) == "racer-con");
    assert(make_profile_id("LPT1", {}) == "racer-lpt1");
    const std::vector<HostProfileCatalogEntry> aliased_ids{
        {"alpha", {"MIKE", 0}},
        {"racer-con", {"ANDREW", 1}},
    };
    assert(make_profile_id("ALPHA", aliased_ids) == "alpha-2");
    assert(make_profile_id("CON", aliased_ids) == "racer-con-2");
    const std::vector<HostProfileCatalogEntry> legacy_namespace{
        {"MIKE", {"MIKE", 0}},
    };
    assert(make_profile_id("MIKE", legacy_namespace) == "mike-2");
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "CON.foo|0|MIKE\n"));
    assert(encode_host_profile_catalog({
        {"COM1.profile", {"MIKE", 0}},
    }).empty());
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|0|MIKE\n"
        "alpha.|1|ANDREW\n"));
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|16|INVALID\n"));
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|+1|ANDREW\n"));
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha| 1|ANDREW\n"));
    assert(!decode_host_profile_catalog(
        "UR-PROFILE-CATALOG/1\n"
        "alpha|0|BAD%ZZ\n"));

    const std::string malformed_path = (root / "malformed.catalog").string();
    {
        std::ofstream malformed(malformed_path, std::ios::binary | std::ios::trunc);
        malformed << "UR-PROFILE-CATALOG/1\nalpha|0|BAD%ZZ\n";
    }
    const std::string malformed_before = [] (const std::string& path) {
        std::ifstream in(path, std::ios::binary);
        return std::string(
            std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>());
    }(malformed_path);
    assert(!save_host_profile_catalog_file(
        malformed_path,
        {{"gamma", {"MIKE", 0}}}));
    const std::string malformed_after = [] (const std::string& path) {
        std::ifstream in(path, std::ios::binary);
        return std::string(
            std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>());
    }(malformed_path);
    assert(malformed_after == malformed_before);

    const std::string oversized_path = (root / "oversized.catalog").string();
    {
        std::ofstream oversized(oversized_path, std::ios::binary | std::ios::trunc);
        oversized << "UR-PROFILE-CATALOG/1\n";
        oversized << std::string(1024u * 1024u, 'X');
    }
    assert(!load_host_profile_catalog_file(oversized_path));
    return 0;
}
