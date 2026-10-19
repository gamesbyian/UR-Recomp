#!/usr/bin/env python3
"""Stage opt-in effective-CGRAM witness in Baldosa's *span* PPU renderer.

The existing QA08 legacy pixel probe does not execute when
kPpuRenderFlags_NewRenderer is selected (including native widescreen).
This separately pinned additive patch reads the actually composed span
renderer zbuffer and final pixel, without a second layer resolver or any
change to PPU/guest state. Actual Windows ON/OFF noninterference is unproved.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess

GAME_REV = "10b864b9d14a7b7416dd909eb7b054c88faef101"
CORE_REV = "075fbe4c8e0d97b0013be541795c39cb644a9709"
RELATIVE = Path("snesrecomp/runner/src/snes/ppu.c")
MARK = "UR_QA08_LATE_EFFECTIVE_SPAN_PPU"
ENV = "UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE"
# Only once, at the end of the optimized span compositor, after its output.
ANCHOR = ("  PpuWriteOverlayRenderLine(ppu, kPpuOverlaySource_Obj, y);\n"
          "}\n\nstatic bool PpuHdWindowCondition")
POINTS = ((70,58),(202,182),(84,77),(175,145),
          (53,41),(187,160),(65,52),(190,161))
POINT_INIT = ", ".join("{%d,%d}" % (x,y) for x,y in POINTS)
TRACE = f"""  /* {MARK}: read existing span winners and final RGB, no re-render. */
  if ((ppu->renderFlags & kPpuRenderFlags_NewRenderer) &&
      snes_frame_counter >= 5176 && snes_frame_counter <= 5186 &&
      getenv("{ENV}")) {{
    static const int points[8][2] = {{{POINT_INIT}}};
    for (unsigned q = 0; q < 8; ++q) {{
      const int x = points[q][0], logical_y = points[q][1];
      if ((int)y != logical_y + 1) continue;
      const size_t i = (size_t)(x + kPpuExtraLeftRight);
      const unsigned layer_main = (ppu->bgBuffers[0].data[i] >> 8) & 15u;
      const unsigned index_main = ppu->bgBuffers[0].data[i] & 255u;
      /* The renderer's exact source colour is PpuPixelColor. This function
       * only reads effective CGRAM or host OBJ overlay colours. */
      const unsigned override_main = ppu->extraObjectCount &&
          (layer_main == 4 || layer_main == 6) &&
          (ppu->objectColors[i] & 0x8000u);
      const unsigned color_main =
          PpuPixelColor(ppu, ppu->bgBuffers[0].data[i], i);
      const unsigned direct_main = PPU_directColor(ppu) && layer_main < 4 &&
          (PPU_mode(ppu) == 3 || PPU_mode(ppu) == 4 ||
           PPU_mode(ppu) == 7);
      /* Keep an explicit marker, not a false CGRAM-index witness, when a
       * host-owned OBJ palette override supplies a winning source colour. */
      if (override_main)
        fprintf(stderr,
          "UR_QA08_LATE_SPAN_OBJECT_OVERRIDE frame=%d x=%d logical_y=%d "
          "layer=%u index=%02x selected_rgb555=%04x\n",
          snes_frame_counter, x, logical_y, layer_main, index_main, color_main);
      else
        fprintf(stderr,
          "UR_QA08_LATE_SPAN_SOURCE frame=%d x=%d logical_y=%d ppu_line=%d "
          "sub=0 layer=%u directcolor=%u index=%02x selected_rgb555=%04x "
          "cgram_index_word=%04x cgram6c=%04x cgram6d=%04x "
          "cgram6e=%04x cgram6f=%04x inidisp=%02x cgadsub=%02x cgwsel=%02x\n",
          snes_frame_counter, x, logical_y, (int)y, layer_main,
          direct_main, index_main, color_main,
          (unsigned)ppu->cgram[index_main], (unsigned)ppu->cgram[0x6c],
          (unsigned)ppu->cgram[0x6d], (unsigned)ppu->cgram[0x6e],
          (unsigned)ppu->cgram[0x6f], (unsigned)ppu->inidisp,
          (unsigned)ppu->cgadsub, (unsigned)ppu->cgwsel);
      if (rendered_subscreen) {{
        const unsigned layer_sub = (ppu->bgBuffers[1].data[i] >> 8) & 15u;
        const unsigned index_sub = ppu->bgBuffers[1].data[i] & 255u;
        const unsigned override_sub = ppu->extraObjectCount &&
            (layer_sub == 4 || layer_sub == 6) &&
            (ppu->objectColors[i] & 0x8000u);
        if (override_sub)
          fprintf(stderr,
            "UR_QA08_LATE_SPAN_OBJECT_OVERRIDE frame=%d x=%d logical_y=%d "
            "layer=%u index=%02x selected_rgb555=%04x\n",
            snes_frame_counter, x, logical_y, layer_sub, index_sub,
            (unsigned)PpuPixelColor(ppu, ppu->bgBuffers[1].data[i], i));
        else
          fprintf(stderr,
            "UR_QA08_LATE_SPAN_SOURCE frame=%d x=%d logical_y=%d ppu_line=%d "
            "sub=1 layer=%u directcolor=%u index=%02x selected_rgb555=%04x "
            "cgram_index_word=%04x cgram6c=%04x cgram6d=%04x "
            "cgram6e=%04x cgram6f=%04x inidisp=%02x cgadsub=%02x cgwsel=%02x\n",
            snes_frame_counter, x, logical_y, (int)y, layer_sub,
            (unsigned)(PPU_directColor(ppu) && layer_sub < 4 &&
            (PPU_mode(ppu) == 3 || PPU_mode(ppu) == 4 || PPU_mode(ppu) == 7)),
            index_sub,
            (unsigned)PpuPixelColor(ppu, ppu->bgBuffers[1].data[i], i),
            (unsigned)ppu->cgram[index_sub], (unsigned)ppu->cgram[0x6c],
            (unsigned)ppu->cgram[0x6d], (unsigned)ppu->cgram[0x6e],
            (unsigned)ppu->cgram[0x6f], (unsigned)ppu->inidisp,
            (unsigned)ppu->cgadsub, (unsigned)ppu->cgwsel);
      }}
      const uint8_t *actual = &ppu->renderBuffer[
          ((size_t)y - 1u) * ppu->renderPitch +
          (size_t)(x + ppu->extraLeftRight) * 4u];
      fprintf(stderr,
        "UR_QA08_LATE_SPAN_FINAL frame=%d x=%d logical_y=%d ppu_line=%d "
        "RGB8=%u,%u,%u inidisp=%02x fixed=%04x tm=%02x ts=%02x\n",
        snes_frame_counter, x, logical_y, (int)y,
        (unsigned)actual[2], (unsigned)actual[1], (unsigned)actual[0],
        (unsigned)ppu->inidisp, (unsigned)ppu->fixedColor,
        (unsigned)ppu->screenEnabled[0], (unsigned)ppu->screenEnabled[1]);
    }}
  }}
"""
# Since TRACE is a raw C insertion, escaped newlines in C format strings must
# be preserved as backslash-n rather than literal source-line breaks.
TRACE = TRACE.replace("rgb555=%04x\n\"", "rgb555=%04x\\n\"").replace(
    "cgwsel=%02x\n\"", "cgwsel=%02x\\n\"").replace(
    "ts=%02x\n\"", "ts=%02x\\n\"")


def patch_source(src: str) -> str:
    if MARK in src:
        if src.count(TRACE) != 1 or src.count(MARK) != 1:
            raise ValueError("partial or changed span PPU diagnostic")
        old = src.replace(TRACE, "", 1)
        if patch_source(old) != src:
            raise ValueError("span PPU diagnostic differs from exact transform")
        return src
    if src.count(ANCHOR) != 1 or src.count("static NOINLINE void PpuDrawWholeLine(Ppu *ppu, uint y) {") != 1:
        raise ValueError("exact pinned span renderer compositor anchor differs")
    if "UR_QA08_LATE_PPU_SOURCE" in src or "UR_QA08_LATE_SPAN_" in src:
        raise ValueError("competing span PPU observer")
    return src.replace(ANCHOR, TRACE + ANCHOR, 1)


def pinned_revision(path: Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True,
                          timeout=20).stdout.strip()


def apply_game(game: Path, *, write: bool=False) -> Path:
    game = game.resolve()
    if pinned_revision(game) != GAME_REV or pinned_revision(game / "snesrecomp") != CORE_REV:
        raise ValueError("Baldosa game/core revision changed")
    if not (game / "src/gen/dispatch_v2.c").is_file():
        raise ValueError("generated Uniracers USA guest missing")
    target = game / RELATIVE
    old = target.read_text(encoding="utf-8")
    new = patch_source(old)
    if write and new != old:
        target.write_text(new, encoding="utf-8")
    return target


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", required=True, type=Path)
    p.add_argument("--apply-candidate", action="store_true")
    args = p.parse_args()
    try:
        target = apply_game(args.game, write=args.apply_candidate)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        p.exit(2, f"QA08_SPAN_EFFECTIVE_PPU_REFUSED: {exc}\n")
    print(f"QA08_SPAN_EFFECTIVE_PPU {target} applied={int(args.apply_candidate)} "
          "same_PE_and_P7_noninterference_unproven=1 release_credit=0")


if __name__ == "__main__":
    main()
