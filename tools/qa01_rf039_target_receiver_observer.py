#!/usr/bin/env python3
"""RF039: extend actual RF037 SPC F6/F7 receiver probes to Zoo transfer 6091.

Research guest patch only, after RF037. The original observer preserves its
single mmio_read/return, the native hook retains its actual schedule/apply/
read event sites and queue operations. No timing, input, bus or ROM changes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf037_sound_transaction_window as rf037

MARK = "UR_QA01_RF039_TARGET_RECEIVER"
ENV = "UR_QA01_RF039_TARGET_RECEIVER"
ORIGINAL = Path("apu/bapu/smp/core.cpp")
NATIVE = Path("snesrecomp/runner/src/snes/apu.c")

ORIG_NEEDLE = "        ur_qa01_rf030_spc_age <= 103450000ull))) {"
ORIG_SUBSTITUTE = (
    "        ur_qa01_rf030_spc_age <= 103450000ull) ||\n"
    "       /* UR_QA01_RF039_TARGET_RECEIVER: original exact sound upload. */\n"
    '       (getenv("UR_QA01_RF039_TARGET_RECEIVER") &&\n'
    "        ur_qa01_rf030_spc_age >= 103918500ull &&\n"
    "        ur_qa01_rf030_spc_age <= 103920500ull))) {"
)
NATIVE_NEEDLE = (
    '  if (!getenv("UR_QA01_RF037_SOUND_BUS") || port < 2 ||\n'
    '      f < 6055 || f > 6064) return;'
)
NATIVE_SUBSTITUTE = (
    "  /* UR_QA01_RF039_TARGET_RECEIVER: additional genuine host 6091 only. */\n"
    '  if (!getenv("UR_QA01_RF037_SOUND_BUS") || port < 2 ||\n'
    '      ((f < 6055 || f > 6064) &&\n'
    '       !(f == 6091 && getenv("UR_QA01_RF039_TARGET_RECEIVER")))) return;'
)


def replace_verified(src: str, old: str, new: str, label: str) -> str:
    if MARK in src:
        if src.count(new) != 1 or old in src:
            raise ValueError("RF039 partial/tampered " + label)
        return src
    if src.count(old) != 1:
        raise ValueError("RF039 requires exactly one source-pinned RF037 " + label)
    return src.replace(old, new, 1)


def patch_original(src: str) -> str:
    old = rf037.ORIGINAL_SPC_EXTRA
    if old.count(ORIG_NEEDLE) != 1:
        raise ValueError("RF039 upstream original age anchor changed")
    new = old.replace(ORIG_NEEDLE, ORIG_SUBSTITUTE, 1)
    out = replace_verified(src, old, new, "original SPC F6/F7 read")
    if out.count("mmio_read(addr)") != src.count("mmio_read(addr)"):
        raise AssertionError("RF039 altered original SPC read count")
    return out


def patch_native(src: str) -> str:
    old = rf037.NATIVE_APU_HELPER
    if old.count(NATIVE_NEEDLE) != 1:
        raise ValueError("RF039 upstream native host anchor changed")
    new = old.replace(NATIVE_NEEDLE, NATIVE_SUBSTITUTE, 1)
    out = replace_verified(src, old, new, "native queue / SPC read")
    if out.count("apu_writePortNow(") != src.count("apu_writePortNow("):
        raise AssertionError("RF039 altered native port writes")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    path = a.root.resolve() / (ORIGINAL if a.side == "original" else NATIVE)
    if not path.is_file():
        p.error("missing pinned source: " + str(path))
    before = path.read_text(encoding="utf8")
    after = (patch_original if a.side == "original" else patch_native)(before)
    if after != before:
        path.write_text(after, encoding="utf8")
    print("RF039 " + a.side + ": " + ("already staged" if before == after else "target receiver staged"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
