#pragma once

// Native Windows Modern OPTIONS for the pinned Baldosa host.
//
// A pure, host-injected model: it owns no SDL, painter, guest memory or
// controller edge. Every row is a control the shipping host genuinely
// applies (window mode, swap interval, mixer level) -- there are no
// functional-looking toggles that do nothing. Anything the pinned host does
// not honour (pause on focus loss, rumble, ghost, widescreen, render scale,
// output resolution) is deliberately absent rather than disabled.
//
// Persistence reuses the existing Modern HostSettings model and the existing
// typed HostProductState codec/CAS store, but in its OWN file
// (options-v1.txt) so a settings write can never interfere with the
// create-only active-racer selector in host-state-v1.txt, and a damaged
// settings file can never stop the game or a first-racer creation.
//
// Volume stays the framework's own [Sound] Volume in config.ini, exactly as
// the legacy Modern host treats it; the host seam rewrites it immediately.

#include "host_product_state.hpp"
#include "host_product_store.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <optional>
#include <string>
#include <system_error>

namespace ur::product {

enum class BaldosaOptionsRow : std::uint8_t {
    Display = 0,
    VSync = 1,
    Volume = 2,
    Controls = 3,
    Reset = 4,
};
inline constexpr std::size_t kBaldosaOptionsRowCount = 5;
inline constexpr int kBaldosaOptionsVolumeStep = 10;
inline constexpr int kBaldosaOptionsDefaultVolume = 100;

enum class BaldosaOptionsStatus : std::uint8_t {
    None = 0,
    Saved,
    DefaultsRestored,
    ApplyFailed,        // live host refused; nothing changed
    SaveFailed,         // could not persist; live change was rolled back
    ChangedElsewhere,   // another process rewrote the file; rolled back
    DamagedQuarantined, // damaged file preserved aside, fresh file written
};

// The live host seam. Plain function pointers keep the model unit-testable
// without SDL or the pinned framework.
struct BaldosaOptionsHost {
    void* ctx = nullptr;
    // 0 windowed / 1 borderless / 2 exclusive ; 0 off / 1 on / 2 adaptive.
    bool (*get_display)(void*, int* fullscreen, int* vsync) = nullptr;
    bool (*apply_display)(void*, int fullscreen, int vsync) = nullptr;
    int (*get_volume)(void*) = nullptr;
    // Returns the applied percent, or -1 when rejected.
    int (*set_volume)(void*, int percent) = nullptr;

    bool valid() const noexcept {
        return get_display && apply_display && get_volume && set_volume;
    }
};

enum class BaldosaOptionsLoad : std::uint8_t {
    Missing,   // no file: the framework's own config is authoritative
    Loaded,
    Damaged,   // present but rejected; defaults are NOT forced onto the host
    IoError,
};

struct BaldosaNativeOptions {
    bool open = false;
    bool controls_help = false;
    BaldosaOptionsRow selected = BaldosaOptionsRow::Display;
    BaldosaOptionsStatus status = BaldosaOptionsStatus::None;
    HostDisplayMode display = HostDisplayMode::Windowed;
    HostVSyncMode vsync = HostVSyncMode::On;
    int volume = kBaldosaOptionsDefaultVolume;
    BaldosaOptionsLoad load = BaldosaOptionsLoad::Missing;
    // Exact complete state last read from / written to disk: the CAS token.
    std::optional<HostProductState> persisted;
    std::string path;
    BaldosaOptionsHost host;
};

inline std::filesystem::path baldosa_options_path(
    const std::filesystem::path& user_root) {
    return user_root / "options-v1.txt";
}

constexpr int baldosa_options_display_value(HostDisplayMode mode) noexcept {
    return static_cast<int>(mode);
}
constexpr int baldosa_options_vsync_value(HostVSyncMode mode) noexcept {
    return static_cast<int>(mode);
}

constexpr const char* baldosa_options_display_label(
    HostDisplayMode mode) noexcept {
    switch (mode) {
    case HostDisplayMode::Windowed: return "WINDOWED";
    case HostDisplayMode::BorderlessFullscreen: return "BORDERLESS";
    case HostDisplayMode::Fullscreen: return "FULLSCREEN";
    }
    return "WINDOWED";
}
constexpr const char* baldosa_options_vsync_label(
    HostVSyncMode mode) noexcept {
    switch (mode) {
    case HostVSyncMode::Off: return "OFF";
    case HostVSyncMode::On: return "ON";
    case HostVSyncMode::Adaptive: return "ADAPTIVE";
    }
    return "ON";
}
constexpr const char* baldosa_options_row_label(
    BaldosaOptionsRow row) noexcept {
    switch (row) {
    case BaldosaOptionsRow::Display: return "DISPLAY";
    case BaldosaOptionsRow::VSync: return "VSYNC";
    case BaldosaOptionsRow::Volume: return "VOLUME";
    case BaldosaOptionsRow::Controls: return "CONTROLS";
    case BaldosaOptionsRow::Reset: return "DEFAULTS";
    }
    return "";
}
constexpr const char* baldosa_options_status_text(
    BaldosaOptionsStatus status) noexcept {
    switch (status) {
    case BaldosaOptionsStatus::None: return "";
    case BaldosaOptionsStatus::Saved: return "SAVED";
    case BaldosaOptionsStatus::DefaultsRestored: return "DEFAULTS RESTORED";
    case BaldosaOptionsStatus::ApplyFailed: return "NOT APPLIED";
    case BaldosaOptionsStatus::SaveFailed: return "NOT SAVED - CHECK DATA";
    case BaldosaOptionsStatus::ChangedElsewhere:
        return "CHANGED ELSEWHERE - RETRY";
    case BaldosaOptionsStatus::DamagedQuarantined:
        return "OLD FILE KEPT .damaged";
    }
    return "";
}

constexpr HostDisplayMode baldosa_options_cycle_display(
    HostDisplayMode mode, int delta) noexcept {
    int value = static_cast<int>(mode) + (delta >= 0 ? 1 : -1);
    if (value < 0) value = 2;
    if (value > 2) value = 0;
    return static_cast<HostDisplayMode>(value);
}
constexpr HostVSyncMode baldosa_options_cycle_vsync(
    HostVSyncMode mode, int delta) noexcept {
    int value = static_cast<int>(mode) + (delta >= 0 ? 1 : -1);
    if (value < 0) value = 2;
    if (value > 2) value = 0;
    return static_cast<HostVSyncMode>(value);
}

namespace baldosa_options_detail {

inline bool display_in_range(int value) noexcept {
    return value >= 0 && value <= 2;
}

// Loads the persisted file; never throws, never modifies anything.
inline BaldosaOptionsLoad read_state(
    const std::string& path, std::optional<HostProductState>& out) {
    out.reset();
    if (path.empty()) return BaldosaOptionsLoad::IoError;
    const auto loaded = load_host_product_state_file(path);
    switch (loaded.status) {
    case HostProductLoadStatus::Loaded:
        out = loaded.state;
        return BaldosaOptionsLoad::Loaded;
    case HostProductLoadStatus::Missing:
        return BaldosaOptionsLoad::Missing;
    case HostProductLoadStatus::Rejected:
        return BaldosaOptionsLoad::Damaged;
    case HostProductLoadStatus::IoError:
        break;
    }
    return BaldosaOptionsLoad::IoError;
}

inline void pull_live(BaldosaNativeOptions& model) {
    int fullscreen = 0;
    int vsync = 1;
    if (model.host.valid() &&
        model.host.get_display(model.host.ctx, &fullscreen, &vsync) &&
        display_in_range(fullscreen) && display_in_range(vsync)) {
        model.display = static_cast<HostDisplayMode>(fullscreen);
        model.vsync = static_cast<HostVSyncMode>(vsync);
    }
    if (model.host.valid()) {
        const int volume = model.host.get_volume(model.host.ctx);
        if (volume >= 0 && volume <= 100) model.volume = volume;
    }
}

// Rename a rejected file aside (keeping the player's bytes) so a fresh,
// create-only write can succeed. The previous .damaged file, if any, is
// replaced: only the most recent damaged copy is retained.
inline bool quarantine_damaged(const std::string& path) {
    std::error_code ec;
    const std::filesystem::path source(path);
    std::filesystem::path aside = source;
    aside += ".damaged";
    std::filesystem::remove(aside, ec);
    ec.clear();
    std::filesystem::rename(source, aside, ec);
    return !ec;
}

// Persist display/vsync through the existing typed store. `expected` is the
// exact state last observed; nullopt means create-only.
inline BaldosaOptionsStatus persist(
    BaldosaNativeOptions& model, HostDisplayMode display, HostVSyncMode vsync,
    bool quarantine_first) {
    HostProductState next = model.persisted.value_or(HostProductState{});
    next.settings.display_mode = display;
    next.settings.vsync_mode = vsync;
    std::optional<HostProductState> expected = model.persisted;
    BaldosaOptionsStatus damaged_note = BaldosaOptionsStatus::None;
    if (quarantine_first) {
        if (!quarantine_damaged(model.path))
            return BaldosaOptionsStatus::SaveFailed;
        expected.reset();
        damaged_note = BaldosaOptionsStatus::DamagedQuarantined;
    }
    switch (save_host_product_state_file_if_current(
        model.path, expected, next)) {
    case HostProductSaveStatus::Saved:
        model.persisted = next;
        model.load = BaldosaOptionsLoad::Loaded;
        return damaged_note != BaldosaOptionsStatus::None
            ? damaged_note : BaldosaOptionsStatus::Saved;
    case HostProductSaveStatus::Conflict: {
        // Learn what is on disk now so the next attempt is a clean CAS.
        std::optional<HostProductState> current;
        const auto load = read_state(model.path, current);
        model.persisted = current;
        model.load = load;
        return BaldosaOptionsStatus::ChangedElsewhere;
    }
    case HostProductSaveStatus::Rejected:
    case HostProductSaveStatus::IoError:
        break;
    }
    return BaldosaOptionsStatus::SaveFailed;
}

}  // namespace baldosa_options_detail

// Boot: restore the persisted display/vsync BEFORE the window exists. A
// missing file leaves the framework's own config.ini authoritative; a
// damaged one is reported through the model and defaults are not forced.
inline void baldosa_options_boot(
    BaldosaNativeOptions& model, const std::string& path,
    const BaldosaOptionsHost& host) {
    model = BaldosaNativeOptions{};
    model.path = path;
    model.host = host;
    model.load = baldosa_options_detail::read_state(path, model.persisted);
    if (model.load == BaldosaOptionsLoad::Loaded && host.valid()) {
        const auto& settings = model.persisted->settings;
        (void)host.apply_display(
            host.ctx, baldosa_options_display_value(settings.display_mode),
            baldosa_options_vsync_value(settings.vsync_mode));
    }
    baldosa_options_detail::pull_live(model);
}

inline void baldosa_options_open(BaldosaNativeOptions& model) {
    // Re-read both the live host and the file so the panel is truthful about
    // window-key changes and edits made by another process.
    baldosa_options_detail::pull_live(model);
    model.load = baldosa_options_detail::read_state(
        model.path, model.persisted);
    model.open = true;
    model.controls_help = false;
    model.selected = BaldosaOptionsRow::Display;
    model.status = BaldosaOptionsStatus::None;
}

inline void baldosa_options_close(BaldosaNativeOptions& model) {
    if (model.controls_help) {
        model.controls_help = false;
        return;
    }
    model.open = false;
    model.status = BaldosaOptionsStatus::None;
}

inline void baldosa_options_move(BaldosaNativeOptions& model, int delta) {
    if (model.controls_help || delta == 0) return;
    const int count = static_cast<int>(kBaldosaOptionsRowCount);
    int index = static_cast<int>(model.selected);
    index = (index + (delta > 0 ? 1 : -1) + count) % count;
    model.selected = static_cast<BaldosaOptionsRow>(index);
    model.status = BaldosaOptionsStatus::None;
}

namespace baldosa_options_detail {

// Apply -> persist, rolling the live host back if persistence fails so what
// the player sees can never silently diverge from what will be restored.
inline void change_display_vsync(
    BaldosaNativeOptions& model, HostDisplayMode display,
    HostVSyncMode vsync, BaldosaOptionsStatus success_status) {
    const HostDisplayMode old_display = model.display;
    const HostVSyncMode old_vsync = model.vsync;
    if (!model.host.valid() ||
        !model.host.apply_display(
            model.host.ctx, baldosa_options_display_value(display),
            baldosa_options_vsync_value(vsync))) {
        model.status = BaldosaOptionsStatus::ApplyFailed;
        return;
    }
    const bool quarantine = model.load == BaldosaOptionsLoad::Damaged;
    auto status = persist(model, display, vsync, quarantine);
    if (status == BaldosaOptionsStatus::Saved ||
        status == BaldosaOptionsStatus::DamagedQuarantined) {
        model.display = display;
        model.vsync = vsync;
        model.status = status == BaldosaOptionsStatus::Saved
            ? success_status : status;
        return;
    }
    HostDisplayMode restore_display = old_display;
    HostVSyncMode restore_vsync = old_vsync;
    if (status == BaldosaOptionsStatus::ChangedElsewhere &&
        model.load == BaldosaOptionsLoad::Loaded && model.persisted) {
        // The file is the newer authority: adopt what it now says so the
        // retry builds on it rather than silently overwriting it.
        restore_display = model.persisted->settings.display_mode;
        restore_vsync = model.persisted->settings.vsync_mode;
    }
    if (model.host.apply_display(
            model.host.ctx, baldosa_options_display_value(restore_display),
            baldosa_options_vsync_value(restore_vsync))) {
        model.display = restore_display;
        model.vsync = restore_vsync;
    }
    model.status = status;
}

inline void change_volume(BaldosaNativeOptions& model, int percent) {
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    if (!model.host.valid()) {
        model.status = BaldosaOptionsStatus::ApplyFailed;
        return;
    }
    const int applied = model.host.set_volume(model.host.ctx, percent);
    if (applied < 0 || applied > 100) {
        model.status = BaldosaOptionsStatus::ApplyFailed;
        return;
    }
    model.volume = applied;
    model.status = BaldosaOptionsStatus::Saved;
}

}  // namespace baldosa_options_detail

// LEFT / RIGHT on the selected row. Enumerations cycle; volume steps and
// clamps (no surprising jump from silent back to full).
inline void baldosa_options_adjust(BaldosaNativeOptions& model, int delta) {
    if (model.controls_help || delta == 0) return;
    using namespace baldosa_options_detail;
    switch (model.selected) {
    case BaldosaOptionsRow::Display:
        change_display_vsync(
            model, baldosa_options_cycle_display(model.display, delta),
            model.vsync, BaldosaOptionsStatus::Saved);
        break;
    case BaldosaOptionsRow::VSync:
        change_display_vsync(
            model, model.display,
            baldosa_options_cycle_vsync(model.vsync, delta),
            BaldosaOptionsStatus::Saved);
        break;
    case BaldosaOptionsRow::Volume:
        change_volume(model,
            model.volume + (delta > 0 ? kBaldosaOptionsVolumeStep
                                      : -kBaldosaOptionsVolumeStep));
        break;
    case BaldosaOptionsRow::Controls:
    case BaldosaOptionsRow::Reset:
        break;
    }
}

// A / ENTER. Cycles enumerations forward (volume steps up and wraps from
// full to silent, so one button reaches every level), opens the controls
// help, or restores the three defaults. LEFT/RIGHT never wrap volume.
inline void baldosa_options_activate(BaldosaNativeOptions& model) {
    using namespace baldosa_options_detail;
    if (model.controls_help) {
        model.controls_help = false;
        return;
    }
    switch (model.selected) {
    case BaldosaOptionsRow::Display:
    case BaldosaOptionsRow::VSync:
        baldosa_options_adjust(model, 1);
        break;
    case BaldosaOptionsRow::Volume:
        change_volume(model, model.volume >= 100
            ? 0 : model.volume + kBaldosaOptionsVolumeStep);
        break;
    case BaldosaOptionsRow::Controls:
        model.controls_help = true;
        model.status = BaldosaOptionsStatus::None;
        break;
    case BaldosaOptionsRow::Reset: {
        // All-or-nothing: the (reversible) volume change goes first; if the
        // display/vsync change then fails, the previous volume is restored,
        // so DEFAULTS never reports or leaves a half-restored state.
        const HostSettings defaults{};
        const int previous_volume = model.volume;
        if (previous_volume != kBaldosaOptionsDefaultVolume) {
            change_volume(model, kBaldosaOptionsDefaultVolume);
            if (model.status != BaldosaOptionsStatus::Saved) break;
        }
        change_display_vsync(
            model, defaults.display_mode, defaults.vsync_mode,
            BaldosaOptionsStatus::DefaultsRestored);
        if (model.status != BaldosaOptionsStatus::DefaultsRestored &&
            model.status != BaldosaOptionsStatus::DamagedQuarantined) {
            const auto failure = model.status;
            if (previous_volume != kBaldosaOptionsDefaultVolume) {
                const int back = model.host.set_volume(
                    model.host.ctx, previous_volume);
                if (back >= 0 && back <= 100) model.volume = back;
            }
            model.status = failure;
        }
        break;
    }
    }
}

// Display strings for the shared presenter (fixed width cells, ASCII only).
struct BaldosaOptionsRowText {
    std::string label;
    std::string value;
    bool adjustable = false;
};

inline std::string baldosa_options_volume_text(int percent) {
    char buffer[16];
    std::snprintf(buffer, sizeof(buffer), "%d%%", percent);
    return buffer;
}

inline std::array<BaldosaOptionsRowText, kBaldosaOptionsRowCount>
baldosa_options_row_texts(const BaldosaNativeOptions& model) {
    std::array<BaldosaOptionsRowText, kBaldosaOptionsRowCount> rows{};
    rows[0] = {baldosa_options_row_label(BaldosaOptionsRow::Display),
               baldosa_options_display_label(model.display), true};
    rows[1] = {baldosa_options_row_label(BaldosaOptionsRow::VSync),
               baldosa_options_vsync_label(model.vsync), true};
    rows[2] = {baldosa_options_row_label(BaldosaOptionsRow::Volume),
               baldosa_options_volume_text(model.volume), true};
    rows[3] = {baldosa_options_row_label(BaldosaOptionsRow::Controls),
               "SHOW", false};
    rows[4] = {baldosa_options_row_label(BaldosaOptionsRow::Reset),
               "RESTORE", false};
    return rows;
}

// A damaged file is surfaced even before any change is attempted, so the
// player is told why their saved choices are not in effect.
inline const char* baldosa_options_standing_notice(
    const BaldosaNativeOptions& model) noexcept {
    switch (model.load) {
    case BaldosaOptionsLoad::Damaged:
        return "SAVED OPTIONS DAMAGED";
    case BaldosaOptionsLoad::IoError:
        return "OPTIONS FILE UNREADABLE";
    case BaldosaOptionsLoad::Missing:
    case BaldosaOptionsLoad::Loaded:
        break;
    }
    return "";
}

}  // namespace ur::product
