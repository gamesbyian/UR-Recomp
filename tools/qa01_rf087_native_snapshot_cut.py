#!/usr/bin/env python3
"""RF087: bracket actual native scripted WRAM snapshot in disposable host_main.c.

RF086's per-write master accounting is not a timestamp for the scene dump.
This opt-in hook preserves the original dump call and does not add guest bus
operations or clock charges. All observations are investigative only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

FILE = Path("snesrecomp/runner/src/desktop/host_main.c")
STAMP = "UR_QA01_RF087_NATIVE_SNAPSHOT_CUT"
ANCHOR = '''  int rc = snes_state_dump(dir ? dir : "", tag, g_my_pixels, pitch, g_ws_extra,
                           g_snes_height, frame);
  fprintf(stderr, "script f=%u dump %s %s\n", frame, tag, rc ? "partial" : "ok");'''
REPLACEMENT = r'''  /* UR_QA01_RF087_NATIVE_SNAPSHOT_CUT: bracket actual scripted WRAM dump.
   * Native master is accounting, not independently registered original v/h. */
  const char *rf087_flag = getenv("UR_QA01_RF084_NATIVE_SOUND_DP");
  const bool rf087_cut = rf087_flag && rf087_flag[0] == '1' &&
      rf087_flag[1] == '\0' && frame >= 6056u && frame <= 6060u;
  uint64_t rf087_master_before = 0;
  unsigned rf087_ptr_before = 0, rf087_counter_before = 0;
  if (rf087_cut) {
    rf087_master_before = g_cpu.master_cycles;
    rf087_ptr_before = (unsigned)g_ram[0x0063] |
        ((unsigned)g_ram[0x0064] << 8);
    rf087_counter_before = (unsigned)g_ram[0x0069];
  }
  int rc = snes_state_dump(dir ? dir : "", tag, g_my_pixels, pitch, g_ws_extra,
                           g_snes_height, frame);
  if (rf087_cut) {
    const unsigned rf087_ptr_after = (unsigned)g_ram[0x0063] |
        ((unsigned)g_ram[0x0064] << 8);
    const unsigned rf087_counter_after = (unsigned)g_ram[0x0069];
    fprintf(stderr,
        "QA01RF087NATIVECUT f=%u rc=%d master_before=%llu master_after=%llu"
        " ptr_before=%04X ptr_after=%04X"
        " counter_before=%02X counter_after=%02X\n",
        frame, rc, (unsigned long long)rf087_master_before,
        (unsigned long long)g_cpu.master_cycles,
        rf087_ptr_before, rf087_ptr_after,
        rf087_counter_before, rf087_counter_after);
  }
  fprintf(stderr, "script f=%u dump %s %s\n", frame, tag, rc ? "partial" : "ok");'''


def patch(source: str) -> str:
    if STAMP in source or "rf087_cut" in source:
        raise ValueError("RF087 snapshot observer already or partly patched")
    if source.count(ANCHOR) != 1:
        raise ValueError("RF087 pinned scripted-dump anchor missing/ambiguous")
    after = source.replace(ANCHOR, REPLACEMENT, 1)
    if (after.count(STAMP) != 1 or
            after.count("snes_state_dump(") != source.count("snes_state_dump(")):
        raise AssertionError("RF087 changed snapshot call population")
    for helper in ("cpu_write8(", "cpu_write16(", "cpu_read8(", "cpu_read16("):
        if after.count(helper) != source.count(helper):
            raise AssertionError("RF087 changed guest bus call population")
    return after


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    target = args.root / FILE
    if not target.is_file() or target.is_symlink():
        parser.error("disposable pinned Baldosa desktop host missing")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    print("RF087 actual native scripted snapshot cut marker staged")


if __name__ == "__main__":
    main()
