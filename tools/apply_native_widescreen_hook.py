#!/usr/bin/env python3
"""Apply the accepted +8 Uniracers strip-preparation hook to generated AOT C.

Generated code is ROM-derived and is intentionally not committed. This injector
is the durable source: it fails closed unless the exact accepted preparation
and live preparation boundaries are present.

Runtime contract:
  URRECOMP_WS_MARGIN unset/0 -> untouched stock behavior
  URRECOMP_WS_MARGIN=8       -> one adjacent future horizontal strip
  URRECOMP_WS_MARGIN=16/24   -> no mutation; emit a structural capacity limit
                               when URRECOMP_WS_NATIVE_TRACE is enabled
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MARKER = "UR-Recomp native Widescreen +8 strip hook"
TRACE_RE = re.compile(r"cpu_trace_block\(cpu,\s*0x([0-9A-Fa-f]+)\s*\);")

A59E_CALLEE_RE = re.compile(r"(?P<callee>bank_[0-9A-Fa-f]{2}_A59E_M0X0)\(cpu\)")

PCS = {
    "wrapper_after_first_helper": 0x01A59A,
    "wrapper_after_descriptor_builder": 0x01A59D,
}

SUPPORT = r'''
/* UR-Recomp native Widescreen +8 strip hook.
 *
 * This mirrors the accepted PR #219 diagnostic contract but removes all
 * guest-visible side effects from the extra helper execution. The second
 * stock A59E pass runs against a complete CPU + low-WRAM snapshot. We then
 * restore that snapshot and retain only:
 *   - the future 32-byte strip at $0453;
 *   - the secondary horizontal edge/count pair $0509/$052F until AB88 reads it.
 * $0453 remains live through the intervening NMI and is restored at the next
 * live A59A preparation boundary, before another secondary strip is staged.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int ur_ws_native_margin_cache = -32768;
static int ur_ws_native_trace_cache = -1;
static int ur_ws_native_second_pass = 0;
static int ur_ws_native_payload_live = 0;
static int ur_ws_native_limit_reported = 0;
static CpuState ur_ws_native_cpu_snapshot;
static uint8 ur_ws_native_low_wram_snapshot[0x2000];
static uint8 ur_ws_native_future_payload[32];

static int ur_ws_native_margin(void) {
  if (ur_ws_native_margin_cache == -32768) {
    const char *s = getenv("URRECOMP_WS_MARGIN");
    ur_ws_native_margin_cache = (s && *s) ? atoi(s) : 0;
  }
  return ur_ws_native_margin_cache;
}

static int ur_ws_native_trace(void) {
  if (ur_ws_native_trace_cache < 0) {
    const char *s = getenv("URRECOMP_WS_NATIVE_TRACE");
    ur_ws_native_trace_cache = (s && *s && strcmp(s, "0") != 0) ? 1 : 0;
  }
  return ur_ws_native_trace_cache;
}

static uint16 ur_ws_native_read16(CpuState *cpu, uint16 addr) {
  return (uint16)(cpu->ram[addr] | ((uint16)cpu->ram[(uint16)(addr + 1)] << 8));
}

static void ur_ws_native_write16(CpuState *cpu, uint16 addr, uint16 value) {
  cpu->ram[addr] = (uint8)(value & 0xff);
  cpu->ram[(uint16)(addr + 1)] = (uint8)(value >> 8);
}

static int ur_ws_native_should_prepare(CpuState *cpu) {
  const int margin = ur_ws_native_margin();
  if (margin == 16 || margin == 24) {
    if (!ur_ws_native_limit_reported && ur_ws_native_trace()) {
      fprintf(stderr,
              "URWS_LIMIT margin=%d required_extra_columns=%d "
              "stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
              margin, margin / 8);
      ur_ws_native_limit_reported = 1;
    }
    return 0;
  }
  if (margin != 8 || ur_ws_native_payload_live)
    return 0;
  return ur_ws_native_read16(cpu, 0x0505) != 0xffff &&
         ur_ws_native_read16(cpu, 0x052b) == 16;
}

static void ur_ws_native_begin_second_pass(CpuState *cpu) {
  ur_ws_native_cpu_snapshot = *cpu;
  memcpy(ur_ws_native_low_wram_snapshot, cpu->ram,
         sizeof(ur_ws_native_low_wram_snapshot));
  ur_ws_native_second_pass = 1;
}

static void ur_ws_native_finish_second_pass(CpuState *cpu, RecompReturn result) {
  const uint16 second_edge = ur_ws_native_read16(cpu, 0x0505);
  const uint16 second_count = ur_ws_native_read16(cpu, 0x052b);
  memcpy(ur_ws_native_future_payload, cpu->ram + 0x0453,
         sizeof(ur_ws_native_future_payload));

  ur_ws_native_second_pass = 0;
  *cpu = ur_ws_native_cpu_snapshot;
  memcpy(cpu->ram, ur_ws_native_low_wram_snapshot,
         sizeof(ur_ws_native_low_wram_snapshot));

  if (result != RECOMP_RETURN_NORMAL ||
      second_edge == 0xffff || second_count != 16)
    return;

  ur_ws_native_write16(cpu, 0x0509, second_edge);
  ur_ws_native_write16(cpu, 0x052f, second_count);
  memcpy(cpu->ram + 0x0453, ur_ws_native_future_payload,
         sizeof(ur_ws_native_future_payload));
  ur_ws_native_payload_live = 1;

  if (ur_ws_native_trace())
    fprintf(stderr, "URWS_PREP margin=8 edge=%04X count=%u\n",
            (unsigned)second_edge, (unsigned)second_count);
}

static void ur_ws_native_after_builder(CpuState *cpu) {
  if (!ur_ws_native_payload_live)
    return;
  ur_ws_native_write16(
      cpu, 0x0509,
      (uint16)(ur_ws_native_low_wram_snapshot[0x0509] |
               ((uint16)ur_ws_native_low_wram_snapshot[0x050a] << 8)));
  ur_ws_native_write16(
      cpu, 0x052f,
      (uint16)(ur_ws_native_low_wram_snapshot[0x052f] |
               ((uint16)ur_ws_native_low_wram_snapshot[0x0530] << 8)));
}

static void ur_ws_native_cleanup_previous_payload(CpuState *cpu) {
  if (!ur_ws_native_payload_live)
    return;
  memcpy(cpu->ram + 0x0453,
         ur_ws_native_low_wram_snapshot + 0x0453, 32);
  ur_ws_native_payload_live = 0;
  if (ur_ws_native_trace())
    fprintf(stderr, "URWS_CLEANUP margin=8\n");
}
'''.strip()

SECOND_PASS = r'''
    ur_ws_native_cleanup_previous_payload(cpu);
    if (ur_ws_native_should_prepare(cpu)) {
      ur_ws_native_begin_second_pass(cpu);

      /* Replay the exact stock JSR $A59E host-call ABI emitted at 81:A597. */
      cpu_write8(cpu, 0x00, cpu->S, 0xa5); cpu->S = (uint16)(cpu->S - 1);
      cpu_write8(cpu, 0x00, cpu->S, 0x99); cpu->S = (uint16)(cpu->S - 1);
      cpu->host_return_valid = 2;
      RecompReturn _ur_ws_result = __A59E_CALLEE__(cpu);

      ur_ws_native_finish_second_pass(cpu, _ur_ws_result);
    }
'''.strip("\n")

STAGE_INIT_RE = re.compile(r"(?P<indent>[ \t]*)uint16 (?P<var>_v\d+) = 0x433;\n(?P=indent)cpu_write_y_x\(cpu, \(uint16\)\((?P=var)\)\);")

AFTER_BUILDER = r'''
    ur_ws_native_after_builder(cpu);
'''.strip("\n")



def canon(pc: int) -> int:
    return pc & ~0x800000


def _trace_hits(text: str) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for m in TRACE_RE.finditer(text):
        out.setdefault(canon(int(m.group(1), 16)), []).append(m.start())
    return out


def _insert_before_first_function(text: str, block: str) -> str:
    match = re.search(r"(?m)^RecompReturn\s+[A-Za-z0-9_]+\s*\(", text)
    if not match:
        raise ValueError("generated file has no RecompReturn function definition")
    return text[:match.start()] + block + "\n\n" + text[match.start():]


def _insert_before_postcall_variant_split(text: str, start_pc: int, end_pc: int, snippet: str) -> str:
    hits = _trace_hits(text)
    starts = hits.get(start_pc, [])
    ends = hits.get(end_pc, [])
    if len(starts) != 1 or not ends:
        raise ValueError(
            f"post-call region not exact: start={len(starts)} end={len(ends)}"
        )
    start = starts[0]
    end = min(pos for pos in ends if pos > start)
    region = text[start:end]
    anchor = "switch (((cpu->m_flag & 1) << 1) | (cpu->x_flag & 1)) {"
    positions = []
    off = 0
    while True:
        rel = region.find(anchor, off)
        if rel < 0:
            break
        positions.append(rel)
        off = rel + len(anchor)
    if len(positions) < 2:
        raise ValueError(
            f"expected call dispatch plus post-call variant split, found {len(positions)}"
        )
    pos = start + positions[-1]
    line_start = text.rfind("\n", 0, pos) + 1
    indent = re.match(r"[ \t]*", text[line_start:pos]).group(0)
    rendered = "\n".join(
        indent + line if line else line for line in snippet.splitlines()
    ) + "\n"
    return text[:pos] + rendered + text[pos:]


def _insert_after_deadline_guard(text: str, pc: int, snippet: str) -> str:
    hits = _trace_hits(text).get(pc, [])
    if len(hits) != 1:
        raise ValueError(f"expected exactly one emitted block at {pc:06X}, found {len(hits)}")
    start = hits[0]
    next_trace = TRACE_RE.search(text, start + 1)
    end = next_trace.start() if next_trace else min(len(text), start + 5000)
    region = text[start:end]
    charge = "cpu->coprocessor_master_cycles = cpu->master_cycles;"
    rel = region.find(charge)
    if rel < 0:
        raise ValueError(f"{pc:06X} block lacks expected post-deadline cycle-charge anchor")
    pos = start + rel
    indent = re.match(r"[ \t]*", text[text.rfind("\n", 0, pos) + 1:pos]).group(0)
    rendered = "\n".join(indent + line if line else line for line in snippet.splitlines()) + "\n"
    return text[:pos] + rendered + text[pos:]


def apply(gen_dir: Path) -> dict:
    files = sorted(gen_dir.glob("bank*_v2.c"))
    if not files:
        raise ValueError(f"no generated bank*_v2.c files under {gen_dir}")

    wrapper_pc = PCS["wrapper_after_first_helper"]
    wrapper_candidates = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="strict")
        hits = _trace_hits(text)
        if wrapper_pc in hits:
            wrapper_candidates.append(path)

    if len(wrapper_candidates) != 1:
        raise ValueError(f"expected one wrapper TU, found {len(wrapper_candidates)}")
    wrapper = wrapper_candidates[0]
    wrapper_text = wrapper.read_text(encoding="utf-8")

    if MARKER in wrapper_text:
        return {
            "schema_version": 1,
            "changed": False,
            "wrapper_file": wrapper.name,
            "margin0_control": True,
            "margin8_hook": True,
            "margin16_supported": False,
            "margin24_supported": False,
            "first_constraint": "secondary-lane-capacity",
        }

    required = [
        PCS["wrapper_after_first_helper"],
    ]
    hits = _trace_hits(wrapper_text)
    missing = [f"{pc:06X}" for pc in required if len(hits.get(pc, [])) != 1]
    if missing:
        raise ValueError("wrapper seam not exact: " + ", ".join(missing))
    callee_matches = A59E_CALLEE_RE.findall(wrapper_text)
    callee_names = sorted(set(callee_matches))
    if len(callee_names) != 1:
        raise ValueError(f"expected one generated M0X0 A59E callee, found {callee_names}")
    a59e_callee = callee_names[0]

    stage_matches = list(STAGE_INIT_RE.finditer(wrapper_text))
    if len(stage_matches) != 1:
        raise ValueError(f"expected one A59E staging initializer, found {len(stage_matches)}")

    wrapper_text = _insert_before_first_function(wrapper_text, SUPPORT)
    stage_match = STAGE_INIT_RE.search(wrapper_text)
    if stage_match is None:
        raise ValueError("A59E staging initializer moved after support insertion")
    indent = stage_match.group("indent")
    var = stage_match.group("var")
    stage_replacement = (
        f"{indent}uint16 {var} = ur_ws_native_second_pass ? 0x453 : 0x433;\n"
        f"{indent}cpu_write_y_x(cpu, (uint16)({var}));"
    )
    wrapper_text = wrapper_text[:stage_match.start()] + stage_replacement + wrapper_text[stage_match.end():]
    second_pass = SECOND_PASS.replace("__A59E_CALLEE__", a59e_callee)
    wrapper_text = _insert_after_deadline_guard(
        wrapper_text, PCS["wrapper_after_first_helper"], second_pass)
    wrapper_text = _insert_before_postcall_variant_split(
        wrapper_text,
        PCS["wrapper_after_first_helper"],
        PCS["wrapper_after_descriptor_builder"],
        AFTER_BUILDER,
    )
    wrapper.write_text(wrapper_text, encoding="utf-8")

    return {
        "schema_version": 1,
        "changed": True,
        "wrapper_file": wrapper.name,
        "margin0_control": True,
        "margin8_hook": True,
        "margin16_supported": False,
        "margin24_supported": False,
        "first_constraint": "secondary-lane-capacity",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gen_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = apply(args.gen_dir)
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
