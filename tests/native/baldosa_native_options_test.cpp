#include "baldosa_native_options.hpp"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

namespace {

struct FakeHost {
    int fullscreen = 0;
    int vsync = 1;
    int volume = 100;
    int display_applies = 0;
    int volume_applies = 0;
    bool refuse_display = false;
    bool refuse_volume = false;
};

bool fake_get_display(void* ctx, int* fullscreen, int* vsync) {
    auto* host = static_cast<FakeHost*>(ctx);
    *fullscreen = host->fullscreen;
    *vsync = host->vsync;
    return true;
}
bool fake_apply_display(void* ctx, int fullscreen, int vsync) {
    auto* host = static_cast<FakeHost*>(ctx);
    if (host->refuse_display) return false;
    ++host->display_applies;
    host->fullscreen = fullscreen;
    host->vsync = vsync;
    return true;
}
int fake_get_volume(void* ctx) { return static_cast<FakeHost*>(ctx)->volume; }
int fake_set_volume(void* ctx, int percent) {
    auto* host = static_cast<FakeHost*>(ctx);
    if (host->refuse_volume || percent < 0 || percent > 100) return -1;
    ++host->volume_applies;
    host->volume = percent;
    return percent;
}

BaldosaOptionsHost make_host(FakeHost& fake) {
    BaldosaOptionsHost host;
    host.ctx = &fake;
    host.get_display = &fake_get_display;
    host.apply_display = &fake_apply_display;
    host.get_volume = &fake_get_volume;
    host.set_volume = &fake_set_volume;
    return host;
}

std::string slurp(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(in), {}};
}

}  // namespace

int main() {
    const auto stamp = std::chrono::steady_clock::now()
                           .time_since_epoch().count();
    const fs::path root = fs::temp_directory_path() /
        ("ur-native-options-" + std::to_string(stamp));
    assert(fs::create_directory(root));
    const std::string path = baldosa_options_path(root).string();

    // No file: the framework's own configuration stays authoritative and the
    // host is never forced to defaults. Nothing is written by merely booting
    // or opening the panel.
    {
        FakeHost fake;
        fake.fullscreen = 1;  // e.g. config.ini Fullscreen = 1
        fake.vsync = 2;
        fake.volume = 40;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        assert(model.load == BaldosaOptionsLoad::Missing);
        assert(fake.display_applies == 0 && fake.volume_applies == 0);
        assert(model.display == HostDisplayMode::BorderlessFullscreen);
        assert(model.vsync == HostVSyncMode::Adaptive);
        assert(model.volume == 40);
        baldosa_options_open(model);
        assert(model.open && model.selected == BaldosaOptionsRow::Display);
        baldosa_options_close(model);
        assert(!model.open && !fs::exists(path));
    }

    // Changing DISPLAY applies live, persists through the typed store and is
    // restored by a new process BEFORE any window exists.
    {
        FakeHost fake;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        baldosa_options_open(model);
        baldosa_options_adjust(model, 1);
        assert(model.status == BaldosaOptionsStatus::Saved);
        assert(fake.fullscreen == 1 && fake.display_applies == 1);
        assert(model.display == HostDisplayMode::BorderlessFullscreen);
        assert(fs::exists(path));
        // LEFT from windowed wraps to exclusive fullscreen.
        baldosa_options_adjust(model, -1);
        assert(model.display == HostDisplayMode::Windowed);
        baldosa_options_adjust(model, -1);
        assert(model.display == HostDisplayMode::Fullscreen);
        assert(fake.fullscreen == 2);
        baldosa_options_adjust(model, 1);  // wraps back to windowed
        assert(model.display == HostDisplayMode::Windowed);
        // Move to VSYNC and cycle it.
        baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::VSync);
        baldosa_options_activate(model);  // A cycles forward
        assert(model.vsync == HostVSyncMode::Adaptive && fake.vsync == 2);
        baldosa_options_adjust(model, 1);
        assert(model.vsync == HostVSyncMode::Off && fake.vsync == 0);
    }
    {
        FakeHost next_process;  // a fresh process begins with parsed defaults
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(next_process));
        assert(model.load == BaldosaOptionsLoad::Loaded);
        assert(next_process.display_applies == 1);
        assert(next_process.fullscreen == 0 && next_process.vsync == 0);
        assert(model.display == HostDisplayMode::Windowed);
        assert(model.vsync == HostVSyncMode::Off);
        // The persisted file is the existing typed state, with no racer
        // selector inside it.
        const auto loaded = load_host_product_state_file(path);
        assert(loaded.loaded() && !loaded.state->active_profile_id);
        assert(loaded.state->settings.vsync_mode == HostVSyncMode::Off);
    }

    // Volume steps by ten, clamps with LEFT/RIGHT and A wraps full -> silent.
    {
        FakeHost fake;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        baldosa_options_open(model);
        baldosa_options_move(model, 1);
        baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::Volume);
        baldosa_options_adjust(model, 1);
        assert(model.volume == 100 && fake.volume == 100);  // clamp
        baldosa_options_adjust(model, -1);
        assert(model.volume == 90 && fake.volume == 90);
        baldosa_options_activate(model);
        assert(model.volume == 100);
        baldosa_options_activate(model);
        assert(model.volume == 0 && fake.volume == 0);
        baldosa_options_adjust(model, -1);
        assert(model.volume == 0);  // clamp, never negative
        fake.refuse_volume = true;
        baldosa_options_adjust(model, 1);
        assert(model.status == BaldosaOptionsStatus::ApplyFailed);
        assert(model.volume == 0);
    }

    // CONTROLS opens a read-only help page that B closes before the panel,
    // and navigation is inert while it is shown.
    {
        FakeHost fake;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        baldosa_options_open(model);
        baldosa_options_move(model, 1);
        baldosa_options_move(model, 1);
        baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::Controls);
        baldosa_options_adjust(model, 1);  // nothing to adjust
        assert(!model.controls_help);
        baldosa_options_activate(model);
        assert(model.controls_help);
        baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::Controls);
        baldosa_options_close(model);
        assert(!model.controls_help && model.open);
        baldosa_options_close(model);
        assert(!model.open);
    }

    // DEFAULTS restores the three real settings in one action.
    {
        FakeHost fake;
        fake.fullscreen = 1;
        fake.vsync = 0;
        fake.volume = 30;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        baldosa_options_open(model);
        for (int i = 0; i < 4; ++i) baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::Reset);
        baldosa_options_activate(model);
        assert(model.status == BaldosaOptionsStatus::DefaultsRestored);
        assert(fake.fullscreen == 0 && fake.vsync == 1 && fake.volume == 100);
        assert(model.display == HostDisplayMode::Windowed &&
               model.vsync == HostVSyncMode::On && model.volume == 100);
        // Wrapping upward from DEFAULTS returns to DISPLAY.
        baldosa_options_move(model, 1);
        assert(model.selected == BaldosaOptionsRow::Display);
        baldosa_options_move(model, -1);
        assert(model.selected == BaldosaOptionsRow::Reset);
    }

    // A host that refuses the change leaves everything untouched; a store
    // that cannot persist rolls the live change back and says so.
    {
        FakeHost fake;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        const auto before = slurp(path);
        baldosa_options_open(model);
        fake.refuse_display = true;
        baldosa_options_adjust(model, 1);
        assert(model.status == BaldosaOptionsStatus::ApplyFailed);
        assert(model.display == HostDisplayMode::Windowed);
        assert(slurp(path) == before);
        fake.refuse_display = false;

        // Unwritable destination: the data folder itself has vanished.
        const fs::path blocked_root = root / "vanished";
        FakeHost other;
        BaldosaNativeOptions blocked;
        baldosa_options_boot(
            blocked, baldosa_options_path(blocked_root).string(),
            make_host(other));
        baldosa_options_open(blocked);
        baldosa_options_adjust(blocked, 1);
        assert(blocked.status == BaldosaOptionsStatus::SaveFailed);
        assert(other.fullscreen == 0);  // rolled back
        assert(blocked.display == HostDisplayMode::Windowed);
    }

    // Another process rewrote the file between open and change: the stale
    // writer is refused, rolled back, re-reads, and the retry succeeds.
    {
        FakeHost fake;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        baldosa_options_open(model);
        HostProductState external = *model.persisted;
        external.settings.vsync_mode = HostVSyncMode::Adaptive;
        assert(save_host_product_state_file_if_current(
                   path, model.persisted, external) ==
               HostProductSaveStatus::Saved);
        baldosa_options_adjust(model, 1);  // DISPLAY
        assert(model.status == BaldosaOptionsStatus::ChangedElsewhere);
        assert(fake.fullscreen == 0);
        baldosa_options_adjust(model, 1);
        assert(model.status == BaldosaOptionsStatus::Saved);
        assert(fake.fullscreen == 1);
        const auto loaded = load_host_product_state_file(path);
        assert(loaded.loaded() &&
               loaded.state->settings.vsync_mode == HostVSyncMode::Adaptive &&
               loaded.state->settings.display_mode ==
                   HostDisplayMode::BorderlessFullscreen);
    }

    // Damaged file: reported, never forced onto the host, preserved aside
    // as .damaged on the player's first explicit change, then rewritten.
    {
        {
            std::ofstream out(path, std::ios::binary | std::ios::trunc);
            out << "THIS IS NOT A HOST STATE FILE\n";
        }
        const std::string damaged_bytes = slurp(path);
        FakeHost fake;
        fake.fullscreen = 1;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, path, make_host(fake));
        assert(model.load == BaldosaOptionsLoad::Damaged);
        assert(fake.display_applies == 0 && fake.fullscreen == 1);
        assert(std::string(baldosa_options_standing_notice(model)) ==
               "SAVED OPTIONS DAMAGED");
        baldosa_options_open(model);
        assert(slurp(path) == damaged_bytes);  // opening changes nothing
        baldosa_options_adjust(model, 1);
        assert(model.status == BaldosaOptionsStatus::DamagedQuarantined);
        assert(slurp(path + ".damaged") == damaged_bytes);
        assert(load_host_product_state_file(path).loaded());
        assert(model.load == BaldosaOptionsLoad::Loaded);
        assert(std::string(baldosa_options_standing_notice(model)).empty());
    }

    // Row text is truthful and bounded for the shared 8-pixel painter.
    {
        FakeHost fake;
        fake.fullscreen = 2;
        fake.vsync = 2;
        fake.volume = 70;
        BaldosaNativeOptions model;
        baldosa_options_boot(model, root.string() + "/missing.txt",
                             make_host(fake));
        const auto rows = baldosa_options_row_texts(model);
        assert(rows[0].value == "FULLSCREEN" && rows[0].adjustable);
        assert(rows[1].value == "ADAPTIVE");
        assert(rows[2].value == "70%");
        assert(!rows[3].adjustable && !rows[4].adjustable);
        for (const auto& row : rows)
            assert(row.label.size() + row.value.size() <= 20);
    }

    fs::remove_all(root);
    std::puts("PASS: native Options apply, persist, roll back and recover");
    return 0;
}
