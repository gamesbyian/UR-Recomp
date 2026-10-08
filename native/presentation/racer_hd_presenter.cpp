#include "racer_hd_presenter.hpp"

#include "racer_guest_snapshot.hpp"
#include "racer_oam_placement.hpp"
#include "racer_replacement_selector.hpp"

extern "C" {
#include "snes/ppu.h"
}

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

std::array<std::uint8_t, kOverlayBytes> g_obj_overlay{};
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

void draw_asset(
    std::uint8_t* dst,
    std::size_t pitch,
    const RacerRegistration& registration,
    const RacerOamPlacement& placement,
    RacerViewport viewport,
    int scale
) noexcept {
    const int origin_x = static_cast<int>(placement.x_signed) * scale;
    const int origin_y = static_cast<int>(placement.y_raw_8bit) * scale;
    const int out_w = kBaseWidth * scale;
    const int out_h = kBaseHeight * scale;

    if (!valid_racer_hd_internal_render_scale(scale)) return;

    const int scaled_asset_size = kRacerHdLogicalSize * scale;
    for (int oy = 0; oy < scaled_asset_size; ++oy) {
        const int dy = origin_y + oy;
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
    g_sim_frame = number;

    if (!env_enabled() || g_ppu == nullptr) return;

    PpuClearOverlayCaptures(g_ppu);

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
    if (!p1.uses_replacement() || !p2.uses_replacement() ||
        p1.registration == nullptr || p2.registration == nullptr) {
        return;
    }
    if (!racer_hd_asset_available(p1.registration->semantic_frame_id) ||
        !racer_hd_asset_available(p2.registration->semantic_frame_id)) {
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
    if (!p1_top || !p2_top || !p1_bottom || !p2_bottom) return;

    const std::array<const RacerRegistration*, 4> registrations = {
        p1.registration, p2.registration, p1.registration, p2.registration
    };
    const std::array<RacerOamPlacement, 4> placements = {
        *p1_top, *p2_top, *p1_bottom, *p2_bottom
    };
    for (std::size_t i = 0; i < placements.size(); ++i) {
        if (!placements[i].large ||
            placements[i].width_pixels != registrations[i]->logical_width ||
            placements[i].height_pixels != registrations[i]->logical_height) {
            return;
        }
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
    const bool ranged = captured && PpuSetOverlayOamRange(g_ppu, 96, 4);
    const std::uint64_t after = guest_state_digest();

    if (!ranged || before != after) {
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
        {p2.registration->semantic_frame_id, p2.registration, RacerViewport::Top, *p2_top},
        {p1.registration->semantic_frame_id, p1.registration, RacerViewport::Bottom, *p1_bottom},
        {p2.registration->semantic_frame_id, p2.registration, RacerViewport::Bottom, *p2_bottom},
    }};
    g_instance_count = g_instances.size();
    g_frame_active = true;
}

int racer_hd_draw_frame(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int frame_w,
    int frame_h,
    double
) noexcept {
    if (!env_enabled() || !g_frame_active || dst == nullptr || field == nullptr) {
        return 0;
    }
    const int scale = racer_hd_presentation_scale();
    if (frame_w != kBaseWidth ||
        frame_h != kBaseHeight ||
        !valid_racer_hd_internal_render_scale(scale) ||
        pitch < static_cast<std::size_t>(frame_w * scale) * 4) {
        return 0;
    }

    copy_field_scaled(dst, pitch, field, scale);
    for (std::size_t i = 0; i < g_instance_count; ++i) {
        draw_asset(
            dst,
            pitch,
            *g_instances[i].registration,
            g_instances[i].placement,
            g_instances[i].viewport,
            scale
        );
    }

    const RacerRegistration* p1_registration =
        g_instance_count >= 1 ? g_instances[0].registration : nullptr;
    const RacerRegistration* p2_registration =
        g_instance_count >= 2 ? g_instances[1].registration : nullptr;
    const bool registration_pair_changed =
        p1_registration != g_last_logged_p1_registration ||
        p2_registration != g_last_logged_p2_registration;
    if (registration_pair_changed && g_logged_state_transitions < 32) {
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
    return 1;
}

}  // namespace ur::presentation
