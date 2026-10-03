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
unsigned g_logged_state_transitions = 0;
std::uint16_t g_last_logged_p1_semantic = 0xFFFF;
std::uint16_t g_last_logged_p2_semantic = 0xFFFF;
struct RacerDrawInstance {
    std::uint16_t semantic_frame_id;
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

void copy_field(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field
) noexcept {
    for (int y = 0; y < kBaseHeight; ++y) {
        std::memcpy(
            dst + static_cast<std::size_t>(y) * pitch,
            field + static_cast<std::size_t>(y) * kBaseWidth * 4,
            kBaseWidth * 4
        );
    }
}

void draw_asset(
    std::uint8_t* dst,
    std::size_t pitch,
    const RacerOamPlacement& placement
) noexcept {
    const int origin_x = static_cast<int>(placement.x_signed);
    const int origin_y = static_cast<int>(placement.y_raw_8bit);
    const int out_w = kBaseWidth;
    const int out_h = kBaseHeight;

    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        const int dy = origin_y + ly;
        if (dy < 0 || dy >= out_h) continue;
        auto* row = reinterpret_cast<std::uint32_t*>(
            dst + static_cast<std::size_t>(dy) * pitch
        );
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int dx = origin_x + lx;
            if (dx < 0 || dx >= out_w) continue;
            const std::uint32_t px =
                sample_racer_hd_presented_pixel(placement, dx, dy);
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
    // Keep the guest's authentic logical 4:3 surface. The registered asset is
    // four times denser; this first draw-frame seam samples it into the stock
    // 64x64 presentation footprint. A later high-density presenter can consume
    // the same semantic asset without changing guest state or registration.
    (void)frame_w;
    (void)frame_h;
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
        {p1.registration->semantic_frame_id, RacerViewport::Top, *p1_top},
        {p2.registration->semantic_frame_id, RacerViewport::Top, *p2_top},
        {p1.registration->semantic_frame_id, RacerViewport::Bottom, *p1_bottom},
        {p2.registration->semantic_frame_id, RacerViewport::Bottom, *p2_bottom},
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
    if (frame_w != kBaseWidth ||
        frame_h != kBaseHeight ||
        pitch < static_cast<std::size_t>(frame_w) * 4) {
        return 0;
    }

    copy_field(dst, pitch, field);
    for (std::size_t i = 0; i < g_instance_count; ++i) {
        draw_asset(dst, pitch, g_instances[i].placement);
    }

    const std::uint16_t p1_semantic =
        g_instance_count >= 1 ? g_instances[0].semantic_frame_id : 0xFFFF;
    const std::uint16_t p2_semantic =
        g_instance_count >= 2 ? g_instances[1].semantic_frame_id : 0xFFFF;
    const bool semantic_pair_changed =
        p1_semantic != g_last_logged_p1_semantic ||
        p2_semantic != g_last_logged_p2_semantic;
    if (semantic_pair_changed && g_logged_state_transitions < 32) {
        for (std::size_t i = 0; i < g_instance_count; ++i) {
            const auto& instance = g_instances[i];
            std::fprintf(
                stderr,
                "UR_RACER_HD_DRAW PASS frame=%u semantic=%04X viewport=%s slot=%u "
                "x=%d y=%u hflip=%d vflip=%d density=4 guest_state_unchanged=1\n",
                g_sim_frame,
                static_cast<unsigned>(instance.semantic_frame_id),
                instance.viewport == RacerViewport::Top ? "top" : "bottom",
                static_cast<unsigned>(instance.placement.slot),
                static_cast<int>(instance.placement.x_signed),
                static_cast<unsigned>(instance.placement.y_raw_8bit),
                instance.placement.hflip ? 1 : 0,
                instance.placement.vflip ? 1 : 0
            );
        }
        g_last_logged_p1_semantic = p1_semantic;
        g_last_logged_p2_semantic = p2_semantic;
        ++g_logged_state_transitions;
    }
    return 1;
}

}  // namespace ur::presentation
