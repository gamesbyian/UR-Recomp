#include "racer_hd_presenter.hpp"

#include "racer_guest_snapshot.hpp"
#include "racer_oam_placement.hpp"
#include "racer_replacement_selector.hpp"

extern "C" {
#include "snes/ppu.h"
#include "desktop/host_main.h"
}

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" {
extern std::uint8_t g_ram[0x20000];
extern Ppu* g_ppu;
}

namespace ur::presentation {
namespace {

constexpr int kBaseWidth = 256;
constexpr int kBaseHeight = 224;
constexpr std::size_t kOverlayBytes =
    static_cast<std::size_t>(kBaseWidth) * kBaseHeight * 4;
constexpr int kWideProbeWidth = 342;
constexpr int kWideProbeHalfMargin = (kWideProbeWidth - kBaseWidth) / 2;
constexpr std::size_t kWideProbeBytes =
    static_cast<std::size_t>(kWideProbeWidth) * kBaseHeight * 4;

std::array<std::uint8_t, kOverlayBytes> g_obj_overlay{};
std::array<std::uint8_t, kWideProbeBytes> g_wide_obj_overlay{};
bool g_wide_probe_armed = false;
bool g_wide_probe_dumped = false;
int g_wide_probe_slot = -1;
bool g_frame_active = false;
int g_internal_render_scale = kRacerHdDensityScale;
unsigned g_logged_state_transitions = 0;
const RacerRegistration* g_last_logged_p1_registration = nullptr;
const RacerRegistration* g_last_logged_p2_registration = nullptr;
struct RacerDrawInstance {
    std::uint16_t semantic_frame_id;
    const RacerRegistration* registration;
    RacerViewport viewport;
    RacerOamPlacement placement;
};

std::array<RacerDrawInstance, 4> g_instances{};
std::size_t g_instance_count = 0;
unsigned g_sim_frame = 0;

bool env_enabled() noexcept {
    static const bool enabled = [] {
        const char* v = std::getenv("UR_RACER_HD");
        return v != nullptr && v[0] != '\0' && !(v[0] == '0' && v[1] == '\0');
    }();
    return enabled;
}

// Opt-in per-guest-frame and per-present diagnostics. A selector registration
// is not evidence that an authored HD racer survived placement and raster
// capture, nor that a capture was actually presented. Keep these phases
// separate and do not add any guest-state write surface for measurement.
bool hd_census_enabled() noexcept {
    static const bool enabled = [] {
        const char* value = std::getenv("UR_RACER_HD_CENSUS");
        return value != nullptr && value[0] == '1' && value[1] == '\0';
    }();
    return enabled;
}

// Preserve the historical authored-art fixture as an explicitly unsafe,
// scripted forensic comparison. Shipping execution must never gain permission
// to remove overlapping racer OBJ merely because both OAM placements exist.
// Require both a diagnostic census and a host-controlled input fixture to
// avoid treating this environment knob as a player graphics option.
bool unsafe_legacy_overlap_fixture_enabled() noexcept {
    static const bool enabled = [] {
        const char* opt = std::getenv("UR_RACER_HD_UNSAFE_OVERLAP_FIXTURE");
        const char* input = std::getenv("SNESRECOMP_INPUT_FILE");
        return hd_census_enabled() && input != nullptr && *input != '\0' &&
               opt != nullptr && opt[0] == '1' && opt[1] == '\0';
    }();
    return enabled;
}

void hd_census_gate(const char* status, const char* reason) noexcept {
    if (!hd_census_enabled()) return;
    std::fprintf(
        stderr,
        "UR_RACER_HD_CENSUS frame=%u phase=gate status=%s reason=%s\n",
        g_sim_frame, status, reason
    );
}

void hd_census_present(const char* status, const char* reason) noexcept {
    if (!hd_census_enabled()) return;
    std::fprintf(
        stderr,
        "UR_RACER_HD_CENSUS frame=%u phase=present status=%s reason=%s\n",
        g_sim_frame, status, reason
    );
}

// Read-only, single-OAM-slot native visibility probe for *widened* 2P
// raster, using the pinned PPU's own isolated OBJ export with removal OFF.
// Every slot 96..99 is tested in a separate deterministic process. Never
// authorize HD painting from this diagnostic alone: isolated OBJ emission is
// still earlier than final BG/window priority composition.
int wide_source_probe_slot() noexcept {
    const char* value = std::getenv("UR_RACER_HD_WIDE_SOURCE_SLOT");
    const char* directory = std::getenv("UR_RACER_HD_WIDE_SOURCE_DIR");
    if (!value || !*value || !directory || !*directory) return -1;
    char* end = nullptr;
    const long slot = std::strtol(value, &end, 10);
    if (end == value || *end != '\0' || slot < 96 || slot > 99) return -1;
    return static_cast<int>(slot);
}

void dump_wide_obj_source() noexcept {
    if (!g_wide_probe_armed || g_wide_probe_dumped) return;
    const char* requested = std::getenv("UR_RACER_HD_WIDE_SOURCE_FRAME");
    const char* directory = std::getenv("UR_RACER_HD_WIDE_SOURCE_DIR");
    if (!requested || !*requested || !directory || !*directory) return;
    char* end = nullptr;
    const unsigned long target = std::strtoul(requested, &end, 10);
    if (end == requested || *end != '\0' || target != g_sim_frame) return;
    g_wide_probe_dumped = true;  // one exact source-frame capture per process

    char path[1024];
    const int n = std::snprintf(path, sizeof(path),
        "%s/ur-baldosa-ws342-obj-slot%d-frame%06u.pam",
        directory, g_wide_probe_slot, g_sim_frame);
    if (n <= 0 || static_cast<std::size_t>(n) >= sizeof(path)) return;
    std::FILE* out = std::fopen(path, "wb");
    if (!out) return;
    const char* header =
        "P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n";
    bool ok = std::fwrite(header, 1, std::strlen(header), out) ==
              std::strlen(header);
    std::size_t alpha_top = 0, alpha_bottom = 0;
    int min_x = kWideProbeWidth, min_y = kBaseHeight, max_x = -1, max_y = -1;
    for (int y = 0; ok && y < kBaseHeight; ++y) {
        for (int x = 0; x < kWideProbeWidth; ++x) {
            std::uint32_t argb = 0;
            std::memcpy(&argb, g_wide_obj_overlay.data() +
                (static_cast<std::size_t>(y) * kWideProbeWidth + x) * 4, 4);
            const std::uint8_t rgba[4] = {
                static_cast<std::uint8_t>((argb >> 16) & 255),
                static_cast<std::uint8_t>((argb >> 8) & 255),
                static_cast<std::uint8_t>(argb & 255),
                static_cast<std::uint8_t>((argb >> 24) & 255),
            };
            if (rgba[3]) {
                (y < 112 ? alpha_top : alpha_bottom)++;
                min_x = std::min(min_x, x);
                min_y = std::min(min_y, y);
                max_x = std::max(max_x, x);
                max_y = std::max(max_y, y);
            }
            if (std::fwrite(rgba, 1, 4, out) != 4) {
                ok = false;
                break;
            }
        }
    }
    if (std::fclose(out) != 0) ok = false;
    if (!ok) std::remove(path);
    std::fprintf(stderr,
        "UR_RACER_HD_WIDE_SOURCE frame=%u slot=%d status=%s "
        "top_alpha=%zu bottom_alpha=%zu bbox=%d,%d,%d,%d path=%s\n",
        g_sim_frame, g_wide_probe_slot,
        !ok ? "io-error" : (alpha_top + alpha_bottom ? "source" : "empty"),
        alpha_top, alpha_bottom, min_x, min_y, max_x, max_y, path);
}

// Experimental opt-in until native stock-P2 occlusion acceptance is complete.
// The pinned PPU only supports one contiguous OBJ extraction range: P1's
// bottom/top slots 97/98 are adjacent, unlike P2's 96/99.
bool p1_only_capture_enabled() noexcept {
    const char* value = std::getenv("UR_RACER_HD_P1_ONLY");
    return value != nullptr && value[0] == '1' && value[1] == '\0';
}

std::uint64_t fnv1a(const void* data, std::size_t size, std::uint64_t seed) noexcept {
    const auto* p = static_cast<const std::uint8_t*>(data);
    std::uint64_t h = seed;
    for (std::size_t i = 0; i < size; ++i) {
        h ^= p[i];
        h *= 1099511628211ull;
    }
    return h;
}

std::uint64_t guest_state_digest() noexcept {
    std::uint64_t h = 1469598103934665603ull;
    h = fnv1a(g_ram, 0x20000, h);
    if (g_ppu == nullptr) return h;
    h = fnv1a(g_ppu->cgram, sizeof(g_ppu->cgram), h);
    h = fnv1a(g_ppu->oam, sizeof(g_ppu->oam), h);
    h = fnv1a(g_ppu->highOam, sizeof(g_ppu->highOam), h);
    h = fnv1a(g_ppu->vram, sizeof(g_ppu->vram), h);
    return h;
}

void copy_field_scaled(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int scale
) noexcept {
    for (int y = 0; y < kBaseHeight; ++y) {
        const auto* src = reinterpret_cast<const std::uint32_t*>(
            field + static_cast<std::size_t>(y) * kBaseWidth * 4
        );
        for (int sy = 0; sy < scale; ++sy) {
            auto* row = reinterpret_cast<std::uint32_t*>(
                dst + static_cast<std::size_t>(y * scale + sy) * pitch
            );
            for (int x = 0; x < kBaseWidth; ++x) {
                for (int sx = 0; sx < scale; ++sx) {
                    row[x * scale + sx] = src[x];
                }
            }
        }
    }
}

// Diagnostic only: retain the *isolated Original OBJ layer* already exported
// by the pinned PPU. Its alpha/colour can be compared against the independent
// Original screenshot to find likely foreground-occluded racer pixels before
// anyone changes the actual host compositing policy. It never reads/writes a
// guest byte and never runs without an explicit output path and frame number.
void dump_obj_layer_for_occlusion_review() noexcept {
    const char* output = std::getenv("UR_RACER_HD_OBJ_LAYER_PAM");
    const char* requested_frame = std::getenv("UR_RACER_HD_OBJ_LAYER_FRAME");
    if (output == nullptr || output[0] == '\0' ||
        requested_frame == nullptr || requested_frame[0] == '\0') return;
    char* end = nullptr;
    const unsigned long target = std::strtoul(requested_frame, &end, 10);
    if (end == requested_frame || *end != '\0' ||
        target != g_sim_frame || !g_frame_active) return;

    // The PPU's ARGB32 colour is 0xAARRGGBB, independent of host byte order.
    // PAM P7 carries transparent RGBA exactly, avoiding false black-pixel
    // assumptions or a dependency on image libraries in the native runner.
    std::FILE* file = std::fopen(output, "wb");
    if (file == nullptr) return;
    const char* header =
        "P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n";
    bool ok = std::fwrite(header, 1, std::strlen(header), file) == std::strlen(header);
    std::size_t opaque_pixels = 0;
    for (int y = 0; ok && y < kBaseHeight; ++y) {
        for (int x = 0; x < kBaseWidth; ++x) {
            const std::size_t byte_offset =
                (static_cast<std::size_t>(y) * kBaseWidth + x) * 4;
            // The PPU exposes byte storage; avoid assuming a uint32_t
            // alignment or introducing an aliasing violation on other hosts.
            std::uint32_t pixel = 0;
            std::memcpy(
                &pixel, g_obj_overlay.data() + byte_offset, sizeof(pixel)
            );
            const std::uint8_t rgba[4] = {
                static_cast<std::uint8_t>((pixel >> 16) & 0xFF),
                static_cast<std::uint8_t>((pixel >> 8) & 0xFF),
                static_cast<std::uint8_t>(pixel & 0xFF),
                static_cast<std::uint8_t>((pixel >> 24) & 0xFF)
            };
            if (rgba[3] != 0) ++opaque_pixels;
            if (std::fwrite(rgba, 1, sizeof(rgba), file) != sizeof(rgba)) {
                ok = false;
                break;
            }
        }
    }
    if (std::fclose(file) != 0) ok = false;
    std::fprintf(
        stderr,
        "UR_RACER_HD_OBJ_LAYER frame=%u status=%s opaque_pixels=%zu path=%s\n",
        g_sim_frame,
        !ok ? "io-error" : opaque_pixels ? "captured" : "empty",
        opaque_pixels, output
    );
}

void draw_asset(
    std::uint8_t* dst,
    std::size_t pitch,
    const RacerRegistration& registration,
    const RacerOamPlacement& placement,
    RacerViewport viewport,
    int scale
) noexcept {
    const int origin_x = static_cast<int>(placement.x_signed) * scale;
    const int out_w = kBaseWidth * scale;
    const int out_h = kBaseHeight * scale;

    if (!valid_racer_hd_internal_render_scale(scale)) return;

    const int scaled_asset_size = kRacerHdLogicalSize * scale;
    for (int oy = 0; oy < scaled_asset_size; ++oy) {
        const int dy = racer_obj_wrapped_output_row(
            placement.y_raw_8bit, oy, scale
        );
        if (dy < 0 || dy >= out_h ||
            !racer_split_viewport_contains_row(viewport, dy, scale)) continue;
        auto* row = reinterpret_cast<std::uint32_t*>(
            dst + static_cast<std::size_t>(dy) * pitch
        );
        for (int ox = 0; ox < scaled_asset_size; ++ox) {
            const int dx = origin_x + ox;
            if (dx < 0 || dx >= out_w) continue;
            const std::uint32_t px = sample_racer_hd_scaled_asset(
                registration,
                ox,
                oy,
                scale,
                placement.hflip,
                placement.vflip
            );
            if ((px >> 24) != 0) row[dx] = px;
        }
    }
}

}  // namespace

void racer_hd_prepare_frame(
    int,
    int,
    int* frame_w,
    int* frame_h
) noexcept {
    // Logical guest geometry remains authentic. High-density output is owned
    // separately by racer_hd_presentation_scale(), so Widescreen/output-size
    // policy and guest PPU geometry are not conflated with asset density.
    (void)frame_w;
    (void)frame_h;
}

bool racer_hd_set_internal_render_scale(int scale) noexcept {
    if (!valid_racer_hd_internal_render_scale(scale)) return false;
    g_internal_render_scale = scale;
    return true;
}

int racer_hd_internal_render_scale() noexcept {
    return g_internal_render_scale;
}

int racer_hd_presentation_scale() noexcept {
    return env_enabled() && g_frame_active ? g_internal_render_scale : 1;
}

void racer_hd_begin_sim_frame(unsigned number) noexcept {
    g_frame_active = false;
    g_instance_count = 0;
    g_wide_probe_armed = false;
    g_wide_probe_dumped = false;
    g_wide_probe_slot = -1;
    g_sim_frame = number;

    if (!env_enabled() || g_ppu == nullptr) {
        hd_census_gate("original", !env_enabled() ? "disabled" : "no-ppu");
        return;
    }

    PpuClearOverlayCaptures(g_ppu);

    // PreparePpuFrame() has already resolved the host's real logical field
    // geometry before calling begin_sim_frame(). A widened scene cannot be
    // composed by racer_hd_draw_frame(), which currently accepts 256x224
    // only. Do not remove OBJ slots 96..99 from the PPU's stock output when
    // the later HD draw would necessarily refuse that field. Checking in
    // draw_frame would be too late to recover those missing stock pixels.
    if (!racer_hd_can_capture_frame_geometry(
            snesrecomp_desktop_frame_width(),
            snesrecomp_desktop_frame_height())) {
        if (snesrecomp_desktop_frame_width() == kWideProbeWidth &&
            snesrecomp_desktop_frame_height() == kBaseHeight) {
            const int slot = wide_source_probe_slot();
            if (slot >= 0) {
                const std::uint64_t before = guest_state_digest();
                std::memset(g_wide_obj_overlay.data(), 0,
                            g_wide_obj_overlay.size());
                // PPU widescreen logical X spans [-43, 299); the isolated
                // 342-column raster stores them at [0, 342). Selecting one
                // exact OAM slot avoids cross-rider source attribution.
                const bool bound = PpuBindOverlaySurface(
                    g_ppu, kPpuOverlaySource_Obj, g_wide_obj_overlay.data(),
                    kWideProbeWidth * 4);
                const bool captured = bound && PpuSetOverlayCapture(
                    g_ppu, kPpuOverlaySource_Obj, -kWideProbeHalfMargin,
                    0, kWideProbeWidth, kBaseHeight, 0 /* no removal */);
                const bool ranged = captured && PpuSetOverlayOamRange(
                    g_ppu, static_cast<std::uint8_t>(slot), 1);
                const bool unchanged = before == guest_state_digest();
                if (ranged && unchanged) {
                    g_wide_probe_armed = true;
                    g_wide_probe_slot = slot;
                } else {
                    PpuClearOverlayCaptures(g_ppu);
                    std::fprintf(stderr,
                        "UR_RACER_HD_WIDE_SOURCE_FAIL frame=%u slot=%d "
                        "reason=%s\n", number, slot,
                        !unchanged ? "guest-state-mutated" : "overlay-unavailable");
                }
            }
        }
        // Read-only overlay never authorizes RemoveFromGame, new art or a
        // change to the actual stock PPU output in widened scenes.
        hd_census_gate("original", "unsupported-geometry");
        return;
    }

    const SelectionResult p1 = select_racer_presentation_from_wram(
        GraphicsPack::Remastered,
        g_ram,
        0x20000,
        1
    );
    const SelectionResult p2 = select_racer_presentation_from_wram(
        GraphicsPack::Remastered,
        g_ram,
        0x20000,
        2
    );
    if (!p1.uses_replacement() || p1.registration == nullptr ||
        !racer_hd_asset_available(p1.registration->semantic_frame_id)) {
        hd_census_gate("original", "p1-selection-or-art");
        return;
    }

    const bool p2_ready = p2.uses_replacement() &&
        p2.registration != nullptr &&
        racer_hd_asset_available(p2.registration->semantic_frame_id);
    const bool p1_only = !p2_ready && p1_only_capture_enabled();
    if (!p2_ready && !p1_only) {
        hd_census_gate("original", "p2-pair-gate");
        return;
    }

    const auto p1_top = decode_racer_split_ppu_placement(
        g_ppu->oam, 256, g_ppu->obsel, 1, RacerViewport::Top
    );
    const auto p2_top = decode_racer_split_ppu_placement(
        g_ppu->oam, 256, g_ppu->obsel, 2, RacerViewport::Top
    );
    const auto p1_bottom = decode_racer_split_ppu_placement(
        g_ppu->oam, 256, g_ppu->obsel, 1, RacerViewport::Bottom
    );
    const auto p2_bottom = decode_racer_split_ppu_placement(
        g_ppu->oam, 256, g_ppu->obsel, 2, RacerViewport::Bottom
    );
    if (!p1_top || !p2_top || !p1_bottom || !p2_bottom) {
        hd_census_gate("original", "missing-oam-placement");
        return;
    }

    const std::array<const RacerRegistration*, 4> registrations = {
        p1.registration, p2_ready ? p2.registration : nullptr,
        p1.registration, p2_ready ? p2.registration : nullptr
    };
    const std::array<RacerOamPlacement, 4> placements = {
        *p1_top, *p2_top, *p1_bottom, *p2_bottom
    };
    for (std::size_t i = 0; i < placements.size(); ++i) {
        if (registrations[i] == nullptr) continue;
        if (!placements[i].large ||
            placements[i].width_pixels != registrations[i]->logical_width ||
            placements[i].height_pixels != registrations[i]->logical_height) {
            hd_census_gate("original", "oam-size-mismatch");
            return;
        }
    }
    // Full-pair removal also captures the inactive 16px split aliases.
    // A copy peeking in from the left or across Y-wrap would otherwise be
    // erased from the stock PPU raster and never redrawn. Refuse the capture
    // before PpuSetOverlayCapture(RemoveFromGame), preserving all stock OBJ.
    if (p2_ready && !racer_hd_full_pair_preserves_split_objs(
            *p1_top, *p2_top, *p1_bottom, *p2_bottom,
            g_ppu->obsel, g_ppu->oamaddh)) {
        hd_census_gate("original", "full-pair-split-obj");
        return;
    }
    // Per-rider footprint alpha cannot prove which slot actually emitted
    // pixels when active 64px riders overlap. An emitted front rider could
    // otherwise authorize a source-absent rear HD phantom. The pinned PPU's
    // separate slot planes also show rear OBJ samples obscured by front OBJ
    // or BG/window pixels at source frame 1856. Fail before arming any
    // destructive capture; Original owns the complete ambiguous frame.
    const bool source_overlap = p2_ready &&
        (racer_active_source_footprints_overlap(
             *p1_top, *p2_top, RacerViewport::Top) ||
         racer_active_source_footprints_overlap(
             *p1_bottom, *p2_bottom, RacerViewport::Bottom));
    if (source_overlap && !unsafe_legacy_overlap_fixture_enabled()) {
        hd_census_gate("original", "overlapping-source-obj");
        return;
    }
    if (source_overlap) {
        static bool warned = false;
        if (!warned) {
            std::fprintf(stderr,
                "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE enabled=1 "
                "warning=overlap-guard-bypassed-for-art-reference-only\\n");
            warned = true;
        }
    }
    // Stock bottom P2 slot 96 paints in front of P1 97. The flattened
    // framebuffer has no reusable P2 depth plane, so an isolated host P1
    // cannot be painted where its lower sprite rectangle intersects P2.
    // Reject even a *possible* overlap; retain the original entire frame.
    // A rotated OAM first-sprite index can reverse the usual ordering.
    // Preserve stock in that unsupported priority mode.
    // Only the proven 16/64px split-OBJ mode has a validated alias rule.
    if (p1_only && g_ppu->obsel != 0x83) {
        hd_census_gate("original", "p1-only-obsel");
        return;
    }
    if (p1_only && (g_ppu->oamaddh & 0x80) != 0) {
        hd_census_gate("original", "p1-only-priority-rotation");
        return;
    }
    if (p1_only && !racer_p1_only_no_stock_p2_occlusion(
            *p1_top, *p1_bottom, *p2_top, *p2_bottom)) {
        hd_census_gate("original", "p1-only-occlusion");
        return;
    }

    const std::uint64_t before = guest_state_digest();
    std::memset(g_obj_overlay.data(), 0, g_obj_overlay.size());

    const bool bound = PpuBindOverlaySurface(
        g_ppu,
        kPpuOverlaySource_Obj,
        g_obj_overlay.data(),
        kBaseWidth * 4
    );
    const bool captured = bound && PpuSetOverlayCapture(
        g_ppu,
        kPpuOverlaySource_Obj,
        0,
        0,
        kBaseWidth,
        kBaseHeight,
        kPpuOverlayFlag_RemoveFromGame
    );
    const bool ranged = captured && PpuSetOverlayOamRange(
        g_ppu, p1_only ? 97 : 96, p1_only ? 2 : 4
    );
    const std::uint64_t after = guest_state_digest();

    if (!ranged || before != after) {
        hd_census_gate("original", before != after ? "guest-state-mutated" : "ppu-capture-failed");
        PpuClearOverlayCaptures(g_ppu);
        if (before != after) {
            std::fprintf(
                stderr,
                "UR_RACER_HD_FAIL frame=%u reason=guest-state-mutated\n",
                number
            );
        }
        return;
    }

    g_instances = {{
        {p1.registration->semantic_frame_id, p1.registration, RacerViewport::Top, *p1_top},
        {p2_ready ? p2.registration->semantic_frame_id : p1.registration->semantic_frame_id,
         p2_ready ? p2.registration : p1.registration,
         p2_ready ? RacerViewport::Top : RacerViewport::Bottom,
         p2_ready ? *p2_top : *p1_bottom},
        {p1.registration->semantic_frame_id, p1.registration, RacerViewport::Bottom, *p1_bottom},
        {p2_ready ? p2.registration->semantic_frame_id : std::uint16_t{0},
         p2_ready ? p2.registration : nullptr,
         RacerViewport::Bottom, *p2_bottom},
    }};
    g_instance_count = p1_only ? 2 : g_instances.size();
    g_frame_active = true;
    hd_census_gate("armed", p1_only ? "p1-only" : "full-pair");
}

int racer_hd_draw_frame(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int frame_w,
    int frame_h,
    double
) noexcept {
    if (frame_w == kWideProbeWidth && frame_h == kBaseHeight)
        dump_wide_obj_source();
    if (!env_enabled() || !g_frame_active || dst == nullptr || field == nullptr) {
        hd_census_present("original", !g_frame_active ? "not-armed" : "unavailable-output");
        return 0;
    }
    const int scale = racer_hd_presentation_scale();
    if (frame_w != kBaseWidth ||
        frame_h != kBaseHeight ||
        !valid_racer_hd_internal_render_scale(scale) ||
        pitch < static_cast<std::size_t>(frame_w * scale) * 4) {
        hd_census_present("original", "unsupported-output");
        return 0;
    }

    dump_obj_layer_for_occlusion_review();
    copy_field_scaled(dst, pitch, field, scale);
    // QA-08 opt-in destructive-capture witness: render exactly the captured
    // PPU stock framebuffer, without authored racers, so a native screenshot
    // can prove that RemoveFromGame really erased the original OBJ. Unset in
    // all ordinary builds and never alters guest state or admission policy.
    const char* capture_only = std::getenv("UR_RACER_HD_CAPTURE_ONLY");
    if (capture_only != nullptr && capture_only[0] == '1' &&
        capture_only[1] == '\0') {
        std::fprintf(
            stderr, "UR_RACER_HD_CAPTURE_ONLY frame=%u instances=%zu\n",
            g_sim_frame, g_instance_count
        );
        return 1;
    }
    // SNES OBJ priority among overlapping sprites follows the ascending OAM
    // index, regardless of the sprite's background-priority attribute bits.
    // Draw in descending slot order: the lowest-numbered OAM slot paints last
    // and remains visible where the two racers intersect. The original split
    // viewport restriction is applied independently inside draw_asset().
    std::array<std::size_t, 4> draw_order{{0, 1, 2, 3}};
    std::sort(
        draw_order.begin(),
        draw_order.begin() + g_instance_count,
        [](std::size_t a, std::size_t b) noexcept {
            return racer_obj_paints_behind(
                g_instances[a].placement.slot,
                g_instances[b].placement.slot
            );
        }
    );
    // Source OBJ isolation is read-only. A populated WRAM frame and OAM
    // placement can exist even when the authentic PPU emitted no sprite
    // pixels in one half of the screen. Painting that half fabricates a
    // rider (demonstrated on the frame-1220 bottom player).
    std::array<std::size_t, 2> source_opaque{{0, 0}};
    std::array<std::size_t, 4> footprint_opaque{{0, 0, 0, 0}};
    for (std::size_t i = 0; i < g_instance_count; ++i) {
        const auto& instance = g_instances[i];
        const unsigned index =
            instance.viewport == RacerViewport::Top ? 0u : 1u;
        footprint_opaque[i] = racer_stock_obj_pixels_in_footprint(
            g_obj_overlay.data(), g_obj_overlay.size(),
            instance.placement, instance.viewport
        );
        source_opaque[index] += footprint_opaque[i];
    }
    if (hd_census_enabled()) {
        std::fprintf(
            stderr,
            "UR_RACER_HD_SOURCE_OBJ frame=%u top_opaque=%zu bottom_opaque=%zu "
            "top_painted=%u bottom_painted=%u\n",
            g_sim_frame, source_opaque[0], source_opaque[1],
            source_opaque[0] != 0 ? 1u : 0u,
            source_opaque[1] != 0 ? 1u : 0u
        );
    }
    if (hd_census_enabled()) {
        // These are *footprint* hits in the composite OBJ source plane, not
        // independently attributed pixels from the individual OAM slots.
        std::fprintf(
            stderr,
            "UR_RACER_HD_SOURCE_FOOTPRINTS frame=%u count=%zu "
            "alpha0=%zu alpha1=%zu alpha2=%zu alpha3=%zu\n",
            g_sim_frame, g_instance_count,
            footprint_opaque[0], footprint_opaque[1],
            footprint_opaque[2], footprint_opaque[3]
        );
    }
    for (std::size_t rank = 0; rank < g_instance_count; ++rank) {
        const auto instance_index = draw_order[rank];
        const auto& instance = g_instances[instance_index];
        // One player's OBJ emission in this viewport cannot authorize a
        // disjoint, source-empty second racer. Overlapping OBJ footprints
        // remain ambiguous until the PPU exports per-slot visibility.
        if (footprint_opaque[instance_index] == 0) continue;
        draw_asset(
            dst,
            pitch,
            *instance.registration,
            instance.placement,
            instance.viewport,
            scale
        );
    }

    const RacerRegistration* p1_registration =
        g_instance_count >= 1 ? g_instances[0].registration : nullptr;
    const RacerRegistration* p2_registration =
        g_instance_count == 4 ? g_instances[1].registration : nullptr;
    const bool registration_pair_changed =
        p1_registration != g_last_logged_p1_registration ||
        p2_registration != g_last_logged_p2_registration;
    if (registration_pair_changed && g_logged_state_transitions < 32) {
        if (g_instance_count == 2) {
            std::fprintf(
                stderr,
                "UR_RACER_HD_P1_ONLY frame=%u slots=97-98 p2_stock=1 bottom_nonoverlap=1\\n",
                g_sim_frame
            );
        }
        for (std::size_t i = 0; i < g_instance_count; ++i) {
            const auto& instance = g_instances[i];
            std::fprintf(
                stderr,
                "UR_RACER_HD_DRAW PASS frame=%u semantic=%04X viewport=%s slot=%u "
                "x=%d y=%u hflip=%d vflip=%d density=4 output_scale=%d guest_state_unchanged=1\n",
                g_sim_frame,
                static_cast<unsigned>(instance.semantic_frame_id),
                instance.viewport == RacerViewport::Top ? "top" : "bottom",
                static_cast<unsigned>(instance.placement.slot),
                static_cast<int>(instance.placement.x_signed),
                static_cast<unsigned>(instance.placement.y_raw_8bit),
                instance.placement.hflip ? 1 : 0,
                instance.placement.vflip ? 1 : 0,
                scale
            );
        }
        g_last_logged_p1_registration = p1_registration;
        g_last_logged_p2_registration = p2_registration;
        ++g_logged_state_transitions;
    }
    hd_census_present("hd", g_instance_count == 2 ? "p1-only" : "full-pair");
    return 1;
}

}  // namespace ur::presentation
