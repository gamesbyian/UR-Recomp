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

int main() {
    const auto stamp = std::chrono::steady_clock::now()
                           .time_since_epoch().count();
    const fs::path workspace = fs::temp_directory_path() /
        ("ur-native-first-racer-" + std::to_string(stamp));
    assert(fs::create_directory(workspace));
    const auto empty = workspace / "empty";
    assert(fs::create_directory(empty));
    const auto bad = create_baldosa_first_preset_for_next_boot(empty, 999u);
    assert(bad.status == BaldosaFirstRacerStatus::Invalid);
    assert(!fs::exists(empty / "host-state-v1.txt"));
    assert(!fs::exists(empty / "profiles-v1.txt"));
    assert(create_baldosa_first_preset_for_next_boot(
        fs::path("relative-folder"), 0).status ==
        BaldosaFirstRacerStatus::Invalid);

    // The same established catalog, typed state and exact 8KiB clean stock
    // image are now durable BEFORE the new native process reads its SRAM.
    const auto made = create_baldosa_first_preset_for_next_boot(empty, 0);
    assert(made.created() && made.profile_id == "mike");
    const auto selector =
        load_host_product_state_file((empty / "host-state-v1.txt").string());
    const auto catalog =
        load_host_profile_catalog_file((empty / "profiles-v1.txt").string());
    assert(selector.loaded() && selector.state->active_profile_id == "mike");
    assert(catalog && catalog->size() == 1);
    const auto identity = make_legacy_racer_identity(0);
    assert(identity && (*catalog)[0].identity == *identity);
    const auto save_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string("mike"));
    assert(save_root.isolated());
    assert(baldosa_native_selected_profile_paths_are_real(
        empty, save_root.save_root));
    const auto state = load_host_profile_state_file(
        ExecutionMode::Modern,
        (empty / save_root.save_root / "host-profile.txt").string(), "mike");
    assert(state.loaded() && state.state->stock_sram &&
           state.state->racer_identity == identity);
    // The shared stock image is a BASELINE, not necessarily a profile
    // already projected to the first named racer. Compare to an independent
    // expected copy with ONLY the source-backed rider byte rewritten.
    const auto& canonical = clean_stock_sram();
    auto expected_mike = canonical;
    expected_mike[0x0748] = identity->rider_index;
    assert(*state.state->stock_sram == expected_mike);
    const fs::path raw = empty / save_root.save_root / "save.srm";
    assert(fs::file_size(raw) == kStockSramBytes);
    assert(baldosa_sram_file_matches_exact(
        raw, expected_mike.data(), expected_mike.size()));
    const auto before = fs::last_write_time(raw);
    assert(create_baldosa_first_preset_for_next_boot(empty, 1).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
    assert(fs::last_write_time(raw) == before);

    // A different first-time preset must seed the actual cartridge rider
    // byte in BOTH typed and raw 8 KiB states without changing the shared
    // stock image or the first player's new profile.
    const auto second = workspace / "second-preset";
    assert(fs::create_directory(second));
    const auto andrew = create_baldosa_first_preset_for_next_boot(second, 1);
    assert(andrew.created() && andrew.profile_id == "andrew");
    const auto typed2 = load_host_profile_state_file(
        ExecutionMode::Modern, (second / "saves/profile-andrew/host-profile.txt").string(),
        "andrew");
    assert(typed2.loaded() && typed2.state->racer_identity &&
           typed2.state->racer_identity->rider_index == 1);
    assert(typed2.state->stock_sram &&
           (*typed2.state->stock_sram)[0x0748] == 1u);
    const auto raw2 = second / "saves/profile-andrew/save.srm";
    assert(baldosa_sram_file_matches_exact(
        raw2, typed2.state->stock_sram->data(), kStockSramBytes));
    // Creating ANDREW didn't change the already committed Mike snapshot.
    assert(baldosa_sram_file_matches_exact(
        raw, expected_mike.data(), expected_mike.size()));

    // Simulate the exact durable shape left by a process death after
    // catalog/typed/raw publication but before the selector's last CAS.
    // A WRONG preset may never choose another person's interrupted identity.
    const auto interrupted = workspace / "interrupted-catalog-publication";
    assert(fs::create_directory(interrupted));
    const auto initially_complete =
        create_baldosa_first_preset_for_next_boot(interrupted, 1);
    assert(initially_complete.created() &&
           initially_complete.profile_id == "andrew");
    const auto missing_selector = interrupted / "host-state-v1.txt";
    assert(fs::remove(missing_selector)); // test-only crash fixture
    const auto interrupted_typed =
        interrupted / "saves/profile-andrew/host-profile.txt";
    const auto interrupted_raw =
        interrupted / "saves/profile-andrew/save.srm";
    const auto interrupted_catalog = interrupted / "profiles-v1.txt";
    const auto exact_contents = [](const fs::path& p) {
        std::ifstream stream(p, std::ios::binary);
        return std::string(std::istreambuf_iterator<char>(stream),
                           std::istreambuf_iterator<char>());
    };
    const auto typed_bytes = exact_contents(interrupted_typed);
    const auto raw_bytes = exact_contents(interrupted_raw);
    const auto catalog_bytes = exact_contents(interrupted_catalog);
    assert(!typed_bytes.empty() && raw_bytes.size() == kStockSramBytes &&
           !catalog_bytes.empty());
    assert(recover_baldosa_first_preset_for_next_boot(interrupted, 0).status ==
           BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(missing_selector));
    const auto resumed =
        recover_baldosa_first_preset_for_next_boot(interrupted, 1);
    assert(resumed.status == BaldosaFirstRacerStatus::Recovered &&
           resumed.created() && resumed.profile_id == "andrew");
    const auto reselected =
        load_host_product_state_file(missing_selector.string());
    assert(reselected.loaded() &&
           reselected.state->active_profile_id == "andrew");
    assert(exact_contents(interrupted_typed) == typed_bytes);
    assert(exact_contents(interrupted_raw) == raw_bytes);
    assert(exact_contents(interrupted_catalog) == catalog_bytes);
    assert(recover_baldosa_first_preset_for_next_boot(interrupted, 1).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);

    // P1-owned additional racer creation is NOT an active-profile switch.
    // The single trusted Mike catalog entry authorizes exactly one new
    // independently initialized stock rider, and source P1 SRAM may never
    // be truncated or rekeyed by P2 setup.
    const auto duo = workspace / "named-p1-and-new-p2";
    assert(fs::create_directory(duo));
    assert(create_baldosa_first_preset_for_next_boot(duo, 0).created());
    const auto duo_global = duo / "host-state-v1.txt";
    const auto duo_catalog = duo / "profiles-v1.txt";
    const auto duo_mike_typed = duo / "saves/profile-mike/host-profile.txt";
    const auto duo_mike_raw = duo / "saves/profile-mike/save.srm";
    const auto p1_global_before = exact_contents(duo_global);
    const auto p1_typed_before = exact_contents(duo_mike_typed);
    const auto p1_raw_before = exact_contents(duo_mike_raw);
    assert(!p1_global_before.empty() && !p1_typed_before.empty() &&
           p1_raw_before.size() == kStockSramBytes);
    assert(create_baldosa_second_preset_for_next_boot(
               duo, "andrew", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(create_baldosa_second_preset_for_next_boot(
               duo, "mike", 0).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(create_baldosa_second_preset_for_next_boot(
               duo, "mike", 999u).status ==
           BaldosaSecondRacerStatus::Invalid);
    assert(load_host_profile_catalog_file(duo_catalog.string())->size() == 1u);
    const auto second_member =
        create_baldosa_second_preset_for_next_boot(duo, "mike", 1);
    assert(second_member.created() && second_member.profile_id == "andrew");
    const auto second_roster =
        load_host_profile_catalog_file(duo_catalog.string());
    assert(second_roster && second_roster->size() == 2u &&
           (*second_roster)[0].profile_id == "mike" &&
           (*second_roster)[1].profile_id == "andrew");
    const auto duo_andrew_typed =
        duo / "saves/profile-andrew/host-profile.txt";
    const auto duo_andrew_raw = duo / "saves/profile-andrew/save.srm";
    const auto second_state = load_host_profile_state_file(
        ExecutionMode::Modern, duo_andrew_typed.string(), "andrew");
    const auto second_identity = make_legacy_racer_identity(1);
    assert(second_state.loaded() && second_identity &&
           second_state.state->racer_identity == second_identity);
    assert(second_state.state->stock_sram &&
           (*second_state.state->stock_sram)[0x0748] == 1u);
    assert(catalog_entry_matches_profile_state(
        (*second_roster)[1], *second_state.state));
    assert(baldosa_sram_file_matches_exact(
        duo_andrew_raw, second_state.state->stock_sram->data(),
        kStockSramBytes));
    assert(exact_contents(duo_global) == p1_global_before);
    assert(exact_contents(duo_mike_typed) == p1_typed_before);
    assert(exact_contents(duo_mike_raw) == p1_raw_before);
    const auto duo_catalog_two = exact_contents(duo_catalog);
    assert(create_baldosa_second_preset_for_next_boot(
               duo, "mike", 2).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(duo_catalog) == duo_catalog_two);
    assert(exact_contents(duo_global) == p1_global_before);

    // Corrupt current P1 raw SRAM never authorizes an additional catalog
    // entry. Do not promote an extra rider from roster-only metadata.
    const auto corrupt_parent = workspace / "p1-corrupt-p2-rejected";
    assert(fs::create_directory(corrupt_parent));
    assert(create_baldosa_first_preset_for_next_boot(corrupt_parent, 0)
               .created());
    const auto corrupt_raw =
        corrupt_parent / "saves/profile-mike/save.srm";
    {
        std::fstream f(corrupt_raw,
                       std::ios::binary | std::ios::in | std::ios::out);
        f.seekp(0x0748);
        f.put(static_cast<char>(0x7f));
        f.flush();
    }
    assert(create_baldosa_second_preset_for_next_boot(
               corrupt_parent, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(!fs::exists(corrupt_parent / "saves/profile-andrew"));
    assert(load_host_profile_catalog_file(
               (corrupt_parent / "profiles-v1.txt").string())->size() == 1u);

    // An orphan P2 directory from a crashed attempt is never adopted,
    // repaired, truncated or promoted by retrying profile creation.
    const auto incomplete_p2 = workspace / "orphan-new-p2";
    assert(fs::create_directory(incomplete_p2));
    assert(create_baldosa_first_preset_for_next_boot(incomplete_p2, 0)
               .created());
    assert(fs::create_directory(
        incomplete_p2 / "saves/profile-andrew"));
    assert(create_baldosa_second_preset_for_next_boot(
               incomplete_p2, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(load_host_profile_catalog_file(
               (incomplete_p2 / "profiles-v1.txt").string())->size() == 1u);
    // Reproduce the exact completed-P2-files / missing-final-catalog window
    // from an interrupted creation. This fixture deliberately rewinds ONLY
    // the test catalog after an otherwise legitimate full P2 publication.
    // No synthetic guest-result or profile creation production path exists.
    const auto stage_interrupted_second = [&](const char* name) {
        const fs::path dir = workspace / name;
        assert(fs::create_directory(dir));
        assert(create_baldosa_first_preset_for_next_boot(dir, 0).created());
        const fs::path entries = dir / "profiles-v1.txt";
        const auto initial = load_host_profile_catalog_file(entries.string());
        assert(initial && initial->size() == 1u);
        assert(create_baldosa_second_preset_for_next_boot(dir, "mike", 1).created());
        assert(save_host_profile_catalog_file(entries.string(), *initial));
        assert(load_host_profile_catalog_file(entries.string())->size() == 1u);
        return dir;
    };
    const auto staged_p2 = stage_interrupted_second("staged-second-before-catalog");
    const auto staged_selector = staged_p2 / "host-state-v1.txt";
    const auto staged_catalog = staged_p2 / "profiles-v1.txt";
    const auto staged_mike = staged_p2 / "saves/profile-mike/save.srm";
    const auto staged_mike_typed =
        staged_p2 / "saves/profile-mike/host-profile.txt";
    const auto staged_andrew = staged_p2 / "saves/profile-andrew/save.srm";
    const auto staged_andrew_typed =
        staged_p2 / "saves/profile-andrew/host-profile.txt";
    const auto selector_before = exact_contents(staged_selector);
    const auto catalog_before = exact_contents(staged_catalog);
    const auto mike_before = exact_contents(staged_mike);
    const auto mike_typed_before = exact_contents(staged_mike_typed);
    const auto andrew_before = exact_contents(staged_andrew);
    const auto andrew_typed_before = exact_contents(staged_andrew_typed);
    const auto staged_mutex = staged_p2 /
        "saves/profile-andrew/host-profile.txt.urmutex";
    assert(fs::is_regular_file(staged_mutex) &&
           fs::file_size(staged_mutex) == 0u);

    // A normal retry correctly refuses an orphan directory. Recovery may
    // publish only on the user's exact matching next-boot preset selection.
    assert(create_baldosa_second_preset_for_next_boot(
               staged_p2, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(recover_baldosa_second_preset_for_next_boot(
               staged_p2, "mike", 2).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(recover_baldosa_second_preset_for_next_boot(
               staged_p2, "andrew", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(staged_catalog) == catalog_before);
    const auto resumed_p2 = recover_baldosa_second_preset_for_next_boot(
        staged_p2, "mike", 1);
    assert(resumed_p2.created() &&
           resumed_p2.status == BaldosaSecondRacerStatus::Recovered &&
           resumed_p2.profile_id == "andrew");
    const auto restored_roster =
        load_host_profile_catalog_file(staged_catalog.string());
    assert(restored_roster && restored_roster->size() == 2u &&
           restored_roster->at(0).profile_id == "mike" &&
           restored_roster->at(1).profile_id == "andrew");
    assert(exact_contents(staged_selector) == selector_before);
    assert(exact_contents(staged_mike) == mike_before);
    assert(exact_contents(staged_mike_typed) == mike_typed_before);
    assert(exact_contents(staged_andrew) == andrew_before);
    assert(exact_contents(staged_andrew_typed) == andrew_typed_before);
    assert(recover_baldosa_second_preset_for_next_boot(
               staged_p2, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);

    // A partial, tampered or foreign P2 can never acquire a catalog row.
    const auto partial = stage_interrupted_second("partial-second-sram");
    const fs::path partial_sram = partial / "saves/profile-andrew/save.srm";
    {
        std::ofstream short_save(partial_sram,
                                 std::ios::binary | std::ios::trunc);
        short_save << "short";
    }
    const auto partial_catalog_before =
        exact_contents(partial / "profiles-v1.txt");
    assert(recover_baldosa_second_preset_for_next_boot(
               partial, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(partial / "profiles-v1.txt") == partial_catalog_before);

    const auto tampered = stage_interrupted_second("modified-second-typed");
    const auto tampered_typed =
        tampered / "saves/profile-andrew/host-profile.txt";
    {
        std::ofstream bad(tampered_typed, std::ios::binary | std::ios::trunc);
        bad << "foreign typed profile\n";
    }
    const auto tampered_catalog_before =
        exact_contents(tampered / "profiles-v1.txt");
    assert(recover_baldosa_second_preset_for_next_boot(
               tampered, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(tampered / "profiles-v1.txt") ==
           tampered_catalog_before);

    const auto unexpected = stage_interrupted_second("foreign-extra-p2-file");
    const auto extra_file =
        unexpected / "saves/profile-andrew/foreign-note.txt";
    { std::ofstream note(extra_file); note << "unreviewed user data"; }
    const auto unexpected_before =
        exact_contents(unexpected / "profiles-v1.txt");
    assert(recover_baldosa_second_preset_for_next_boot(
               unexpected, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(unexpected / "profiles-v1.txt") == unexpected_before);

    // A missing or redirected OS path lock is not a canonical completed
    // typed-store publication, even if the 8-KiB stock bytes still match.
    const auto mutex_lost = stage_interrupted_second("missing-p2-mutex");
    const fs::path missing_mutex =
        mutex_lost / "saves/profile-andrew/host-profile.txt.urmutex";
    assert(fs::remove(missing_mutex));
    assert(recover_baldosa_second_preset_for_next_boot(
               mutex_lost, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(!fs::exists(missing_mutex));
#ifndef _WIN32
    const auto mutex_redirect = stage_interrupted_second("redirected-p2-mutex");
    const fs::path redirected_mutex =
        mutex_redirect / "saves/profile-andrew/host-profile.txt.urmutex";
    assert(fs::remove(redirected_mutex));
    fs::create_symlink(workspace / "unknown-target", redirected_mutex);
    assert(recover_baldosa_second_preset_for_next_boot(
               mutex_redirect, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
#endif

    const auto stale = stage_interrupted_second("stale-p1-selector");
    const auto stale_global = stale / "host-state-v1.txt";
    auto changed = *load_host_product_state_file(stale_global.string()).state;
    changed.active_profile_id = "andrew";
    assert(save_host_product_state_file(stale_global.string(), changed) ==
           HostProductSaveStatus::Saved);
    const auto stale_before = exact_contents(stale / "profiles-v1.txt");
    assert(recover_baldosa_second_preset_for_next_boot(
               stale, "mike", 1).status ==
           BaldosaSecondRacerStatus::ExistingData);
    assert(exact_contents(stale / "profiles-v1.txt") == stale_before);
    std::puts("PASS: interrupted P2 publication resumes only exact initial "
              "typed/raw stock files with authenticated P1 unchanged");

    std::puts("PASS: second named stock racer uses canonical isolated "
              "typed/raw P2 state with P1 selector/save byte-exact unchanged");

    // Correct profile name is not enough: a power-loss/corruption during raw
    // write must remain nonrecoverable by a generic one-button adoption.
    const auto interrupted_bad = workspace / "interrupted-bad-sram";
    assert(fs::create_directory(interrupted_bad));
    assert(create_baldosa_first_preset_for_next_boot(interrupted_bad, 0)
               .created());
    assert(fs::remove(interrupted_bad / "host-state-v1.txt"));
    const auto corrupted = interrupted_bad / "saves/profile-mike/save.srm";
    {
        std::fstream output(corrupted,
                            std::ios::binary | std::ios::in | std::ios::out);
        output.seekp(0x0748);
        output.put(static_cast<char>(0x7F));
        output.flush();
    }
    assert(recover_baldosa_first_preset_for_next_boot(interrupted_bad, 0)
               .status == BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(interrupted_bad / "host-state-v1.txt"));

    // A foreign/broken catalog, a dangling redirected save path, and
    // corrupted global state may not be silently overwritten.
    const auto foreign = workspace / "foreign";
    assert(fs::create_directory(foreign));
    { std::ofstream out(foreign / "profiles-v1.txt"); out << "junk\n"; }
    assert(create_baldosa_first_preset_for_next_boot(foreign, 0).status ==
           BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(foreign / "host-state-v1.txt"));
    { std::ofstream out(foreign / "host-state-v1.txt"); out << "corrupt\n"; }
    assert(create_baldosa_first_preset_for_next_boot(foreign, 0).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
#ifndef _WIN32
    const auto dangling = workspace / "dangling-selector";
    assert(fs::create_directory(dangling));
    fs::create_symlink("nonexistent-global-target",
                       dangling / "host-state-v1.txt");
    assert(create_baldosa_first_preset_for_next_boot(dangling, 0).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
    assert(!fs::exists(dangling / "profiles-v1.txt"));
#endif

    const auto redirect = workspace / "redirect";
    assert(fs::create_directory(redirect));
    fs::create_directory(redirect / "saves");
    fs::create_directory(redirect / "saves/profile-mike");
    assert(create_baldosa_first_preset_for_next_boot(redirect, 0).status ==
           BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(redirect / "host-state-v1.txt"));
    fs::remove_all(workspace);
    std::puts("PASS: first Modern preset creation uses canonical clean SRAM "
              "and exact next-process catalog identity; refuses overwrite");
}
