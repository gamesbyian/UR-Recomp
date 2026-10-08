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

#include <cstdio>
#include <cstdint>
#include <cstdlib>

extern "C" {
extern std::uint8_t g_ram[0x20000];
extern Ppu* g_ppu;
}

extern "C" void UrRacerHdPrepareFrame(
    int drawable_w, int drawable_h, int *frame_w, int *frame_h
) {
    ur::presentation::racer_hd_prepare_frame(
        drawable_w, drawable_h, frame_w, frame_h
    );
    if (std::getenv("UR_RACER_HD_PROBE_WIDE") && frame_w && frame_h) {
        // Diagnostic-only WorldExpand-sized logical field. The generated
        // native acceptance game has native_widescreen enabled explicitly.
        *frame_w = 342;
        *frame_h = 224;
    }
}

extern "C" void UrRacerHdBeginSimFrame(unsigned number) {
    ur::presentation::racer_hd_begin_sim_frame(number);
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
    return ur::presentation::racer_hd_draw_frame(
        dst, pitch, field, frame_w, frame_h, alpha
    );
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
    if INCLUDE_ANCHOR not in source or FIELD_ANCHOR not in source:
        raise ValueError("generated host anchors not found")
    source = source.replace(INCLUDE_ANCHOR, INCLUDE_ANCHOR + PROBE_DECL + "\n", 1)
    return source.replace(
        FIELD_ANCHOR,
        FIELD_ANCHOR
        + "    .native_widescreen   = 1,\n"
        + "    .after_run_frame     = &UrRacerPresentationProbeAfterRunFrame,\n"
        + "    .prepare_frame       = &UrRacerHdPrepareFrame,\n"
        + "    .begin_sim_frame     = &UrRacerHdBeginSimFrame,\n"
        + "    .draw_frame          = &UrRacerHdDrawFrame,\n"
        + "    .presentation_scale  = &UrRacerHdPresentationScale,\n",
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
