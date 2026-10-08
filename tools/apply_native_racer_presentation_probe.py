#!/usr/bin/env python3
"""Inject a diagnostic-only native racer-presentation acceptance probe."""

from __future__ import annotations

import argparse
from pathlib import Path

INCLUDE_ANCHOR = '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
FIELD_ANCHOR = '    .game_info           = &kGameInfo,\n'

PROBE_DECL = r'''
#ifdef __cplusplus
extern "C"
#endif
void UrRacerPresentationProbeAfterRunFrame(const SnesDesktopHostFrameStats *stats);
int UrRacerHdProbeWideRequested(void);
void UrRacerHdPrepareFrame(int drawable_w, int drawable_h, int *frame_w, int *frame_h);
void UrRacerHdBeginSimFrame(unsigned number);
int UrRacerHdPresentationScale(void);
int UrRacerHdDrawFrame(
    uint8_t *dst, size_t pitch, const uint8_t *field,
    int frame_w, int frame_h, double alpha
);
'''

PROBE_CPP = r'''#include "host_main.h"
#include "snes/ppu.h"
#include "racer_guest_snapshot.hpp"
#include "racer_hd_presenter.hpp"
#include "racer_oam_placement.hpp"

#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>

extern "C" {
extern std::uint8_t g_ram[0x20000];
extern Ppu* g_ppu;
}

extern "C" int UrRacerHdProbeWideRequested(void) {
    return std::getenv("UR_RACER_HD_PROBE_WIDE") != nullptr ? 1 : 0;
}

extern "C" void UrRacerHdPrepareFrame(
    int drawable_w, int drawable_h, int *frame_w, int *frame_h
) {
    ur::presentation::racer_hd_prepare_frame(
        drawable_w, drawable_h, frame_w, frame_h
    );
    if (std::getenv("UR_RACER_HD_P1_NATIVE_TEST")) {
        // Only the diagnostic mixed-OBJ path uses 1x to permit a strict
        // same-frame PPU input vs final-output pixel comparison.
        (void)ur::presentation::racer_hd_set_internal_render_scale(1);
    }
    if (std::getenv("UR_RACER_HD_PROBE_WIDE") && frame_w && frame_h) {
        // Diagnostic-only WorldExpand-sized logical field. The generated
        // native acceptance game has native_widescreen enabled explicitly.
        *frame_w = 342;
        *frame_h = 224;
    }
}

extern "C" void UrRacerHdBeginSimFrame(unsigned number) {
    ur::presentation::racer_hd_begin_sim_frame(number);
    if (std::getenv("UR_RACER_HD_P1_NATIVE_TEST") && g_ppu) {
        static unsigned partial_captures = 0;
        const auto& policy = g_ppu->overlayCaptures[kPpuOverlaySource_Obj];
        if ((policy.flags & kPpuOverlayFlag_RemoveFromGame) != 0 &&
            policy.oamFirst == 97 && policy.oamCount == 2) {
            ++partial_captures;
        }
        if (number == 3820) {
            std::fprintf(stderr,
                "UR_RACER_HD_P1_NATIVE_SUMMARY frame=3820 partial_captures=%u\n",
                partial_captures);
        }
    }
    if (!std::getenv("UR_RACER_HD_PROBE_WIDE")) return;
    const int width = snesrecomp_desktop_frame_width();
    const int height = snesrecomp_desktop_frame_height();
    const bool removal_armed = g_ppu &&
        ((g_ppu->overlayCaptures[kPpuOverlaySource_Obj].flags &
          kPpuOverlayFlag_RemoveFromGame) != 0);
    if (width != 342 || height != 224 || removal_armed) {
        std::fprintf(
            stderr,
            "UR_RACER_HD_WIDE_CAPTURE FAIL frame=%u width=%d height=%d removal=%d\n",
            number, width, height, removal_armed ? 1 : 0
        );
        std::abort();
    }
    if (number == 1220u) {
        std::fprintf(
            stderr,
            "UR_RACER_HD_WIDE_CAPTURE PASS frame=1220 width=342 height=224 removal=0\n"
        );
    }
}

extern "C" int UrRacerHdPresentationScale(void) {
    return ur::presentation::racer_hd_presentation_scale();
}

extern "C" int UrRacerHdDrawFrame(
    std::uint8_t *dst,
    std::size_t pitch,
    const std::uint8_t *field,
    int frame_w,
    int frame_h,
    double alpha
) {
    const int drawn = ur::presentation::racer_hd_draw_frame(
        dst, pitch, field, frame_w, frame_h, alpha
    );
    if (!std::getenv("UR_RACER_HD_P1_NATIVE_TEST") || !g_ppu) return drawn;

    const auto& capture = g_ppu->overlayCaptures[kPpuOverlaySource_Obj];
    const bool partial = (capture.flags & kPpuOverlayFlag_RemoveFromGame) &&
        capture.oamFirst == 97 && capture.oamCount == 2;
    if (!partial) return drawn;
    if (!drawn || frame_w != 256 || frame_h != 224 || pitch < 256u * 4u) {
        std::fprintf(stderr, "UR_RACER_HD_P1_NATIVE FAIL invalid partial draw geometry\n");
        std::abort();
    }

    const auto p2 = ur::presentation::decode_racer_split_ppu_placement(
        g_ppu->oam, 256, g_ppu->obsel, 2,
        ur::presentation::RacerViewport::Bottom
    );
    if (!p2 || !p2->large || p2->width_pixels != 64 ||
        p2->height_pixels != 64) {
        std::fprintf(stderr, "UR_RACER_HD_P1_NATIVE FAIL invalid stock P2 OAM\n");
        std::abort();
    }

    // The HD compositor copied *this exact PPU frame* before placing only
    // P1's two authored instances. P2 remains in the flattened stock field,
    // and the approved non-overlap gate must leave every pixel inside P2's
    // lower-viewport OAM rectangle untouched. This avoids any cross-process
    // guest-frame skew or speculative crop/hash tolerance.
    int p2_roi_pixels = 0;
    int hd_changed_pixels = 0;
    for (int y = 0; y < 224; ++y) {
        for (int x = 0; x < 256; ++x) {
            const auto* src = field + static_cast<std::size_t>(y) * 256u * 4u
                                   + static_cast<std::size_t>(x) * 4u;
            const auto* out = dst + static_cast<std::size_t>(y) * pitch
                                 + static_cast<std::size_t>(x) * 4u;
            const bool differs = std::memcmp(src, out, 4) != 0;
            if (differs) ++hd_changed_pixels;
            if (y < 112 || ((y - p2->y_raw_8bit) & 0xFF) >= 64 ||
                x < p2->x_signed || x >= p2->x_signed + 64) continue;
            ++p2_roi_pixels;
            if (differs) {
                std::fprintf(stderr,
                    "UR_RACER_HD_P1_NATIVE FAIL stock P2 overwritten x=%d y=%d\n",
                    x, y);
                std::abort();
            }
        }
    }
    if (p2_roi_pixels > 0 && hd_changed_pixels > 0) {
        static unsigned logged = 0;
        if (logged < 24) {
            std::fprintf(stderr,
                "UR_RACER_HD_P1_NATIVE PASS p2_stock_roi_exact=1 pixels=%d "
                "p1_hd_changed_pixels=%d\n", p2_roi_pixels, hd_changed_pixels);
            ++logged;
        }
    }
    return drawn;
}

extern "C" void UrRacerPresentationProbeAfterRunFrame(
    const SnesDesktopHostFrameStats *stats
) {
    static bool passed = false;

    const auto selection =
        ur::presentation::select_racer_presentation_from_wram(
            ur::presentation::GraphicsPack::Remastered,
            g_ram,
            0x20000,
            1
        );
    const auto snapshot =
        ur::presentation::read_racer_guest_snapshot(g_ram, 0x20000);
    if (!snapshot.has_value()) return;

    const unsigned frame = stats ? stats->frame : 0u;
    if (frame >= 1180u && frame <= 1620u) {
        std::fprintf(
            stderr,
            "UR_RACER_PRESENTATION_TRACE frame=%u "
            "p1_primary=%04X p2_primary=%04X "
            "p1_companion=%04X p2_companion=%04X "
            "p1_selector=%04X p2_selector=%04X "
            "p1_gate=%04X p2_gate=%04X\n",
            frame,
            snapshot->composition.p1_primary,
            snapshot->composition.p2_primary,
            snapshot->composition.p1_companion,
            snapshot->composition.p2_companion,
            snapshot->composition.p1_selector,
            snapshot->composition.p2_selector,
            snapshot->composition.p1_companion_gate_word,
            snapshot->composition.p2_companion_gate_word
        );
    }

    const bool primary_match =
        snapshot->composition.p1_primary == 0x0541 &&
        snapshot->composition.p2_primary == 0x0540;
    const bool checkpoint_window = frame >= 1216u && frame <= 1224u;
    if (checkpoint_window || primary_match) {
        std::fprintf(
            stderr,
            "UR_RACER_PRESENTATION_OBS frame=%u "
            "p1_primary=%04X p2_primary=%04X "
            "p1_companion=%04X p2_companion=%04X "
            "p1_selector=%04X p2_selector=%04X "
            "p1_gate=%04X p2_gate=%04X uses_replacement=%d reason=%u\n",
            frame,
            snapshot->composition.p1_primary,
            snapshot->composition.p2_primary,
            snapshot->composition.p1_companion,
            snapshot->composition.p2_companion,
            snapshot->composition.p1_selector,
            snapshot->composition.p2_selector,
            snapshot->composition.p1_companion_gate_word,
            snapshot->composition.p2_companion_gate_word,
            selection.uses_replacement() ? 1 : 0,
            static_cast<unsigned>(selection.fallback_reason)
        );
    }

    if (passed || !selection.uses_replacement()) return;

    std::fprintf(
        stderr,
        "UR_RACER_PRESENTATION_PROBE PASS frame=%u "
        "p1_primary=%04X p2_primary=%04X "
        "p1_companion=%04X p2_companion=%04X "
        "p1_selector=%04X p2_selector=%04X "
        "p1_gate=%04X p2_gate=%04X selected=remastered\n",
        frame,
        snapshot->composition.p1_primary,
        snapshot->composition.p2_primary,
        snapshot->composition.p1_companion,
        snapshot->composition.p2_companion,
        snapshot->composition.p1_selector,
        snapshot->composition.p2_selector,
        snapshot->composition.p1_companion_gate_word,
        snapshot->composition.p2_companion_gate_word
    );
    passed = true;
}
'''

CMAKE_BLOCK = r'''
if(NOT DEFINED UR_RECOMP_SOURCE_ROOT)
    message(FATAL_ERROR "UR_RECOMP_SOURCE_ROOT is required for the racer presentation acceptance probe")
endif()
target_sources(UniracersSNESRecomp PRIVATE
    "${UR_RECOMP_SOURCE_ROOT}/native/presentation/racer_replacement_selector.cpp"
    "${UR_RECOMP_SOURCE_ROOT}/native/presentation/racer_guest_snapshot.cpp"
    "${UR_RECOMP_SOURCE_ROOT}/native/presentation/racer_oam_placement.cpp"
    "${UR_RECOMP_SOURCE_ROOT}/native/presentation/racer_hd_presenter.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ur_racer_presentation_probe.cpp"
)
target_include_directories(UniracersSNESRecomp PRIVATE
    "${UR_RECOMP_SOURCE_ROOT}/native/presentation"
)
'''


def patch_main(source: str) -> str:
    if "UrRacerPresentationProbeAfterRunFrame" in source:
        return source
    generated_decl = "static const SnesDesktopHostGame kGameHost = {"
    host_entry = "    return snesrecomp_desktop_main(&kGameHost, argc, argv);"
    if (
        INCLUDE_ANCHOR not in source or FIELD_ANCHOR not in source
        or generated_decl not in source or host_entry not in source
    ):
        raise ValueError("generated host anchors not found")
    source = source.replace(INCLUDE_ANCHOR, INCLUDE_ANCHOR + PROBE_DECL + "\n", 1)
    source = source.replace(
        FIELD_ANCHOR,
        FIELD_ANCHOR
        + "    .after_run_frame     = &UrRacerPresentationProbeAfterRunFrame,\n"
        + "    .prepare_frame       = &UrRacerHdPrepareFrame,\n"
        + "    .begin_sim_frame     = &UrRacerHdBeginSimFrame,\n"
        + "    .draw_frame          = &UrRacerHdDrawFrame,\n"
        + "    .presentation_scale  = &UrRacerHdPresentationScale,\n",
        1,
    )
    # Only diagnostic native-wide runs switch the generated host's native
    # renderer. Keep all existing 256x224 baseline routes on their original
    # renderer path, so this extra acceptance cannot redefine the oracle.
    source = source.replace(
        generated_decl, "static SnesDesktopHostGame kGameHost = {", 1
    )
    return source.replace(
        host_entry,
        "    kGameHost.native_widescreen = UrRacerHdProbeWideRequested() != 0;\n"
        + host_entry,
        1,
    )


def patch_cmake(source: str) -> str:
    if "UR_RECOMP_SOURCE_ROOT" in source:
        return source
    anchor = "snesrecomp_target_desktop_host(UniracersSNESRecomp)"
    if anchor not in source:
        raise ValueError("generated CMake desktop-host anchor not found")
    return source.replace(anchor, anchor + "\n" + CMAKE_BLOCK, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root", type=Path)
    args = ap.parse_args()

    main_c = args.project_root / "src" / "main.c"
    cmake = args.project_root / "CMakeLists.txt"
    probe = args.project_root / "src" / "ur_racer_presentation_probe.cpp"

    main_c.write_text(patch_main(main_c.read_text(encoding="utf-8")), encoding="utf-8")
    cmake.write_text(patch_cmake(cmake.read_text(encoding="utf-8")), encoding="utf-8")
    probe.write_text(PROBE_CPP, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
