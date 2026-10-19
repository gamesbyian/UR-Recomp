#!/usr/bin/env python3
"""RF047 companion: stamp ACTUALLY emitted/executed 65816 opcode PCs.

Research-only Baldosa source transform. Install RF047 first, then this patch,
BEFORE regeneration. Generated markers are placed inside every matching
decoded instruction in *every emitted M/X variant*. A static marker in an ELF,
a cached interpreter PC and a function-name hint are never execution proof.
The recorder's own native ordinals are not shared with RF045 or RF044.
"""
from __future__ import annotations

import argparse
from pathlib import Path

BEAM = Path("snesrecomp/runner/src/beam_frame_driver.c")
EMITTER = Path("snesrecomp/recompiler/v2/emit_function.py")
BRIDGE = Path("snesrecomp/runner/src/snes/interp_bridge.c")
STAMP = "UR_QA01_RF047_EXECUTED_GUEST_OPCODE_PC"
# Source-original branch/wait tail and late ROM-to-SPC sound upload.
# This intentionally cannot label every possible native stack helper read.
TARGET_PCS = (0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5,
              0x8282F0, 0x8282F2, 0x8282F6)
BEAM_ANCHOR = "static void ur_rf047_nmi_snapshot(const char *stage, uint32_t vector) {\n"
EMITTER_DECLARE = "    src.append(f'  extern const char *g_last_recomp_func;')\n"
EMITTER_SITE = '            # Axis-2 step C dynamics: charge runtime-only modifiers (D.l != 0,\n'
INTERP_SITE = "        const uint8_t  op = bridge_bus_read(cpu, pc_before);\n"
BEAM_HOOK = r"""/* UR_QA01_RF047_EXECUTED_GUEST_OPCODE_PC
 * Executed (not statically decoded) instruction-site markers. The native
 * original RF047 seq shares the early NMI recorder when its window is active.
 * Late sound-PC observations have their OWN ordinal and clock origin.
 * Neither PC stream constitutes proof that a later helper read used the
 * opcode: only an in-sequence, actually observed bus operation can do that.
 */
void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {
  extern int snes_frame_counter;
  static unsigned long long late_seq;
  static unsigned late_count;
  const char *enabled = getenv("UR_QA01_RF047_EXEC_PC");
  if (!enabled || !*enabled) return;
  if (pc != 0x82D4EEu && pc != 0x82D4F0u &&
      pc != 0x82D4F2u && pc != 0x82D4F4u && pc != 0x82D4F5u &&
      pc != 0x8282F0u && pc != 0x8282F2u && pc != 0x8282F6u) return;
  /* Early stream shares RF047 NMI/read event ordinals, not stderr order. */
  if (ur_rf047_allowed()) {
    if (!ur_rf047_allow_row()) return;
    ur_rf047_emit(
        "QA01RF047NATIVE seq=%llu stage=opcode f=%d guestPC=%06X"
        " tier=%s master=%llu\n",
        ++ur_rf047_seq, snes_frame_counter, (unsigned)pc,
        tier == 1u ? "aot" : "interp",
        (unsigned long long)g_cpu.master_cycles);
    return;
  }
  /* RF047's NMI coverage stays restricted to host 1017..1025. A distinct
   * opt-in late host window avoids accidentally polluting its nine-frame
   * contiguous sequence or claiming identical cross-emulator clocks. */
  const char *start = getenv("UR_QA01_RF047_EXEC_PC_LATE_START");
  const char *end = getenv("UR_QA01_RF047_EXEC_PC_LATE_END");
  if (!start || !end || !*start || !*end) return;
  char *s_end = NULL, *e_end = NULL;
  long lo = strtol(start, &s_end, 10);
  long hi = strtol(end, &e_end, 10);
  if (!s_end || *s_end || !e_end || *e_end ||
      lo < 0 || hi < lo || hi-lo > 16 ||
      snes_frame_counter < lo || snes_frame_counter > hi) return;
  if (late_count++ >= 8192u) {
    if (late_count == 8193u)
      ur_rf047_emit("QA01RF047NATIVEPC_TRUNCATED\n");
    return;
  }
  ur_rf047_emit(
      "QA01RF047NATIVEPC seq=%llu f=%d guestPC=%06X tier=%s"
      " master=%llu\n",
      ++late_seq, snes_frame_counter, (unsigned)pc,
      tier == 1u ? "aot" : "interp",
      (unsigned long long)g_cpu.master_cycles);
}
"""

def once(src: str, old: str, new: str, label: str) -> str:
    if src.count(old) != 1:
        raise ValueError("RF047 executed-PC source drift: " + label)
    return src.replace(old, new, 1)


def patch(beam: str, emitter: str, bridge: str) -> tuple[str, str, str]:
    if any(STAMP in s for s in (beam, emitter, bridge)):
        raise ValueError("RF047 executed-PC already/partially staged")
    if "UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN" not in beam or \
       "ur_rf047_allow_row" not in beam:
        raise ValueError("RF047 base native recorder must be staged first")
    beam = once(beam, BEAM_ANCHOR, BEAM_HOOK + BEAM_ANCHOR, "native event recorder")
    emitter = once(emitter, EMITTER_DECLARE,
                   EMITTER_DECLARE +
                   '    src.append("  extern void ur_rf047_mark_executed_pc(uint32_t, unsigned);")\n',
                   "emitted C declaration")
    # The marker is inside the decoded insn loop, *after* skipped synthesis
    # instructions and *before* dynamic charging / the real instruction IR.
    # di_insn.addr supplies actual decoded 24-bit guest opcode site. All M/X
    # variants are visited, including Snd_UploadBlockList_82EF_M1X0.
    call = ('            if (di_insn.addr & 0xFFFFFF) in ' +
            repr(TARGET_PCS) + ':\n' +
            '                lines.append(f"  ur_rf047_mark_executed_pc(0x{di_insn.addr & 0xFFFFFF:06X}u, 1u);")\n')
    emitter = once(emitter, EMITTER_SITE, call + EMITTER_SITE,
                   "compiled actual decoded instruction site")
    # Interpreter guest PC comes from the real fetch point, NOT a cached
    # g_interp816_cur_pc that becomes stale when AOT owns execution.
    bridge = once(bridge, INTERP_SITE,
                  INTERP_SITE + "        ur_rf047_mark_executed_pc(pc_before, 0u);\n",
                  "interpreted opcode fetch")
    bridge = once(bridge, "extern Snes *g_snes;\n",
                  "extern Snes *g_snes;\n"
                  "extern void ur_rf047_mark_executed_pc(uint32_t, unsigned);\n",
                  "interpreter declaration")
    if emitter.count("ur_rf047_mark_executed_pc") != 2 or \
       bridge.count("ur_rf047_mark_executed_pc") != 2:
        raise AssertionError("RF047 executed opcode hook count changed")
    return beam, emitter, bridge


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    paths = [root / p for p in (BEAM, EMITTER, BRIDGE)]
    if not all(p.is_file() for p in paths):
        ap.error("missing pinned Baldosa runtime/v2 emitter sources")
    previous = [p.read_text(encoding="utf8") for p in paths]
    updated = patch(*previous)
    for path, data in zip(paths, updated):
        path.write_text(data, encoding="utf8")
    print("RF047 actual executed guest-PC witness staged (no CPU/gameplay retime)")


if __name__ == "__main__":
    main()
