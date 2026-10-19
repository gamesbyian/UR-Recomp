#!/usr/bin/env python3
"""Stage read-only native PPU effective palette witnesses at eight real QA08 pixels.

Only a disposable exact-pinned Baldosa game/core checkout. This reads existing
PPU resolver outputs and composed pixels without deliberate state writes.
Host logging noninterference, guest CRC parity, and visual parity remain
unproven until paired real Windows execution. No release acceptance.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess

GAME_REV = "10b864b9d14a7b7416dd909eb7b054c88faef101"
CORE_REV = "075fbe4c8e0d97b0013be541795c39cb644a9709"
RELATIVE = Path("snesrecomp/runner/src/snes/ppu_legacy.c")
ENV = "UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE"
MARK_RESOLVER = "UR_QA08_LATE_EFFECTIVE_PIXEL_RESOLVER"
MARK_FINAL = "UR_QA08_LATE_EFFECTIVE_PIXEL_FINAL"
HEADER = "#include <stdbool.h>\n"
RESOLVER = ("  if (layer == 4 && pixel < 0xc0) layer = 6; // sprites with palette color < 0xc0\n"
            "  return layer;\n")
FINAL = "  pixelBuffer[3] = 0;\n"
# Renderer y is source logical y+1. These center pixels are source-verified
# across 13 112-field captures and six surrounding 16-field controls.
POINTS = ((70,58),(202,182),(84,77),(175,145),
          (53,41),(187,160),(65,52),(190,161))
TARGET = " || ".join(f"(x == {x} && y == {y+1})" for x,y in POINTS)
PREDICATE = ("snes_frame_counter >= 5176 && snes_frame_counter <= 5186 &&\n"
             f"      ({TARGET}) &&\n"
             f'      getenv("{ENV}")')
RESOLVER_TRACE = f'''  /* {MARK_RESOLVER}: selected source pixel; no second resolver. */
  if ({PREDICATE}) {{
    const unsigned qa08_index = (unsigned)(pixel & 255);
    const unsigned qa08_selected_rgb555 =
      (unsigned)(*r | (*g << 5) | (*b << 10));
    fprintf(stderr,
      "UR_QA08_LATE_PPU_SOURCE frame=%d x=%d logical_y=%d ppu_line=%d "
      "sub=%u layer=%d index=%02x selected_rgb555=%04x "
      "cgram_index_word=%04x cgram6c=%04x cgram6d=%04x "
      "cgram6e=%04x cgram6f=%04x inidisp=%02x "
      "cgadsub=%02x cgwsel=%02x\\n",
      snes_frame_counter, x, y-1, y, (unsigned)sub, layer,
      qa08_index, qa08_selected_rgb555,
      (unsigned)ppu->cgram[qa08_index],
      (unsigned)ppu->cgram[0x6c], (unsigned)ppu->cgram[0x6d],
      (unsigned)ppu->cgram[0x6e], (unsigned)ppu->cgram[0x6f],
      (unsigned)ppu->inidisp, (unsigned)ppu->cgadsub,
      (unsigned)ppu->cgwsel);
  }}
'''
FINAL_TRACE = f'''  /* {MARK_FINAL}: actual post-composition source pixel, no alteration. */
  if ({PREDICATE}) {{
    fprintf(stderr,
      "UR_QA08_LATE_PPU_FINAL frame=%d x=%d logical_y=%d ppu_line=%d "
      "RGB8=%u,%u,%u inidisp=%02x fixed=%04x tm=%02x ts=%02x\\n",
      snes_frame_counter, x, y-1, y,
      (unsigned)pixelBuffer[2], (unsigned)pixelBuffer[1],
      (unsigned)pixelBuffer[0], (unsigned)ppu->inidisp,
      (unsigned)ppu->fixedColor, (unsigned)ppu->screenEnabled[0],
      (unsigned)ppu->screenEnabled[1]);
  }}
'''
HEADERS = "#include <stdio.h>\n#include <stdlib.h>\n"


def patch_source(src: str) -> str:
    """Guard source anchors, allow byte-exact idempotence, refuse partial edits."""
    if MARK_RESOLVER in src or MARK_FINAL in src:
        if (src.count(RESOLVER_TRACE) != 1 or
            src.count(FINAL_TRACE) != 1 or src.count(HEADERS) != 1):
            raise ValueError("partial or modified effective PPU witness")
        original = src.replace(RESOLVER_TRACE, "").replace(FINAL_TRACE, "")
        original = original.replace(HEADERS, "")
        if patch_source(original) != src:
            raise ValueError("altered effective PPU source witness")
        return src
    if (src.count(HEADER) != 1 or src.count(RESOLVER) != 1 or
        src.count(FINAL) != 1 or "#include <stdio.h>" in src or
        "#include <stdlib.h>" in src or
        "UR_QA08_NATIVE_EFFECTIVE_PIXEL_OWNER" in src):
        raise ValueError("pinned original native PPU renderer or observer differs")
    src = src.replace(HEADER, HEADER + HEADERS, 1)
    src = src.replace(RESOLVER, RESOLVER.replace("  return layer;\n",
                        RESOLVER_TRACE + "  return layer;\n"), 1)
    src = src.replace(FINAL, FINAL + FINAL_TRACE, 1)
    return src


def pinned_revision(path: Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True,
                          timeout=20).stdout.strip()


def apply_game(game: Path, *, write: bool = False) -> Path:
    game = game.resolve()
    if pinned_revision(game) != GAME_REV or pinned_revision(game / "snesrecomp") != CORE_REV:
        raise ValueError("Baldosa guest or SNESRecomp core revision differs")
    if not (game / "src/gen/dispatch_v2.c").is_file():
        raise ValueError("exact generated Uniracers guest was not found")
    path = game / RELATIVE
    before = path.read_text(encoding="utf-8")
    after = patch_source(before)
    if write and after != before:
        path.write_text(after, encoding="utf-8")
    return path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--apply-candidate", action="store_true")
    args = p.parse_args()
    try:
        path = apply_game(args.game, write=args.apply_candidate)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        p.exit(2, f"QA08_LATE_EFFECTIVE_PROBE_REFUSED: {exc}\n")
    print(f"QA08_LATE_EFFECTIVE_PROBE path={path} staged={int(args.apply_candidate)} "
          "real_windows_execution=0 output_pixel_noninterference_unverified=1 release_credit=0")


if __name__ == "__main__":
    main()
