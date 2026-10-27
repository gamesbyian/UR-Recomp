#!/usr/bin/env python3
"""RF086: observe the proven non-FastRom Zoo sound writers AFTER their real write.

Stage only in the disposable, regenerated pinned Baldosa bank82, after RF084.
No new guest bus calls, changes to writes, or CPU-clock charges. Original v/h
and native master cycles are distinct, unregistered clock domains.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

FILE = Path("src/gen/bank82_part00_v2.c")
STAMP = "UR_QA01_RF086_NONFAST_BOUNDARY_POSTCOMMIT"
HEADER = '#include "funcs.h"\n'
SITES = (
    ("Snd_IncDataPtr_M0X0", 2, 0x63),
    ("Snd_IncDataPtr_M1X0", 2, 0x63),
    ("Snd_UploadBlock_8097_M0X0", 1, 0x69),
)
HOOK = r'''/* UR_QA01_RF086_NONFAST_BOUNDARY_POSTCOMMIT
 * Direct raw-RAM before/after observation, never another SNES bus operation.
 */
extern int snes_frame_counter;
static unsigned ur_rf086_rows;
static void ur_rf086_after(CpuState *cpu, const char *scope, unsigned width,
                           uint16 addr, unsigned before, unsigned supplied) {
    const char *flag = getenv("UR_QA01_RF084_NATIVE_SOUND_DP");
    if (!flag || flag[0] != '1' || flag[1] != '\0' ||
        snes_frame_counter < 6056 || snes_frame_counter > 6060) return;
    if (++ur_rf086_rows > 8192u) {
        if (ur_rf086_rows == 8193u)
            fprintf(stderr, "QA01RF086NATIVE_TRUNCATED\n");
        return;
    }
    unsigned after = (unsigned)cpu->ram[addr];
    if (width == 2u)
        after |= (unsigned)cpu->ram[(uint16)(addr + 1u)] << 8;
    fprintf(stderr,
        "QA01RF086NATIVE seq=%u scope=%s f=%d width=%u D=%04X"
        " addr=%04X old=%04X supplied=%04X rawAfter=%04X"
        " native_master=%llu\n",
        ur_rf086_rows, scope, snes_frame_counter, width,
        (unsigned)cpu->D, (unsigned)addr, before, supplied, after,
        (unsigned long long)cpu->master_cycles);
}
'''


def instrument(text: str, name: str, width: int, offset: int) -> str:
    marker = f"RecompReturn {name}(CpuState *cpu) {{"
    if text.count(marker) != 1:
        raise ValueError("RF086 missing/ambiguous non-FastRom function " + name)
    start = text.index(marker)
    end = text.find("\nRecompReturn ", start + len(marker))
    if end < 0:
        raise ValueError("RF086 unbounded generated function " + name)
    body = text[start:end]
    pattern = re.compile(
        rf"(?m)^(?P<indent>[ \t]*)cpu_write{width * 8}_paced\(cpu,\s*"
        rf"0x00,\s*\(uint16\)\(cpu->D\s*\+\s*0x{offset:04X}\),\s*_im\);[ \t]*$"
    )
    hits = list(pattern.finditer(body))
    if len(hits) != 1:
        raise ValueError(f"RF086 missing/ambiguous real paced write {name}: {len(hits)}")
    hit = hits[0]
    indent = hit.group("indent")
    addr = f"ur_rf086_addr_{offset:04x}"
    before = f"ur_rf086_before_{offset:04x}"
    replacement = (
        f"{indent}uint16 {addr} = (uint16)(cpu->D + 0x{offset:04X});\n"
        f"{indent}unsigned {before} = (unsigned)cpu->ram[{addr}];\n"
    )
    if width == 2:
        replacement += (
            f"{indent}{before} |= (unsigned)cpu->ram[(uint16)({addr} + 1u)] << 8;\n"
        )
    replacement += (
        hit.group(0) + "\n" +
        f'{indent}ur_rf086_after(cpu, "{name}", {width}u, {addr}, {before}, (unsigned)_im);'
    )
    return text[:start] + body[:hit.start()] + replacement + body[hit.end():] + text[end:]


def patch(text: str) -> str:
    if STAMP in text or "ur_rf086_after" in text:
        raise ValueError("RF086 generated source already or partly patched")
    if text.count(HEADER) != 1:
        raise ValueError("RF086 pinned generated header drift")
    if "UR_QA01_RF084_NATIVE_SOUND_DP_COMMIT" not in text:
        raise ValueError("RF086 must follow RF084 staging in disposable source")
    calls = ("cpu_read8_paced(", "cpu_read16_paced(",
             "cpu_write8_paced(", "cpu_write16_paced(")
    old = tuple(text.count(x) for x in calls)
    text = text.replace(HEADER, HEADER + HOOK, 1)
    for name, width, offset in SITES:
        text = instrument(text, name, width, offset)
    if tuple(text.count(x) for x in calls) != old:
        raise AssertionError("RF086 changed guest bus helper population")
    if text.count(STAMP) != 1 or text.count('ur_rf086_after(cpu, "') != 3:
        raise AssertionError("RF086 hook count changed")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    target = args.root / FILE
    if not target.is_file() or target.is_symlink():
        parser.error("actual disposable generated bank82 C source missing")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    print("RF086 native non-FastRom post-commit witness staged; no guest bus changes")


if __name__ == "__main__":
    main()
