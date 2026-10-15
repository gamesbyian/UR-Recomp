#!/usr/bin/env python3
"""DISPOSABLE consumed-prime on SOURCE-OBSERVED HDMA channels 6+7 only.

Native real 2P countdown channel6 is direct mode4 bank15 to
$2126..$2129 window boundaries, with 900 stock vs 896 globally
consumed PPU register writes. Channel7 is direct mode0 to $2100
brightness. No production renderer/hardware correction is implied.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.qa08_patch_hdma_prime_counterfactual import (
        MARK as GLOBAL_MARK, patch_source as validate_global_source,
    )
    from tools.qa08_patch_channel7_only_prime_counterfactual import (
        MARK as CHANNEL7_MARK, SAVE, RESTORE,
    )
    from tools.qa08_patch_channel57_prime_counterfactual import (
        MARK as CHANNEL57_MARK,
    )
except ModuleNotFoundError:
    from qa08_patch_hdma_prime_counterfactual import (
        MARK as GLOBAL_MARK, patch_source as validate_global_source,
    )
    from qa08_patch_channel7_only_prime_counterfactual import (
        MARK as CHANNEL7_MARK, SAVE, RESTORE,
    )
    from qa08_patch_channel57_prime_counterfactual import (
        MARK as CHANNEL57_MARK,
    )

MARK = "UR_QA08_CH67_ONLY_PRIME_EXPERIMENT"
SELECTIVE = """    /* UR_QA08_CH67_ONLY_PRIME_EXPERIMENT: disposable source test ONLY.
     * Genuine Uniracers countdown channel6: mode4/direct ROM bank15
     * WRAM-independent per-scanline window coordinates to $2126-$2129.
     * Genuine channel7: direct mode0 INIDISP brightness to $2100.
     * Preserve all OTHER channels' pinned prime and game semantics. */
    if ((i == 7 && (ch->mode & 7) == 0 && !ch->indirect &&
         ch->bAdr == 0x00) ||
        (i == 6 && (ch->mode & 7) == 4 && !ch->indirect &&
         ch->bAdr == 0x26 && ch->aBank == 0x15)) {
      ch->repCount--;
      ch->doTransfer = (ch->repCount & 0x80) != 0;
      if ((ch->repCount & 0x7f) == 0)
        dma_hdmaLoadDescriptor(dma, ch);
    } else {
      *ch = save;
    }
  }
}"""


def patch_source(source: str) -> str:
    if any(mark in source for mark in (MARK, GLOBAL_MARK, CHANNEL7_MARK, CHANNEL57_MARK)):
        raise ValueError("first-line HDMA source already has a counterfactual")
    validate_global_source(source)
    head, tail = source.split("\nvoid dma_doHdma(Dma* dma) {", 1)
    if head.count(SAVE) != 1 or head.count(RESTORE) != 1:
        raise ValueError("pinned first-line HDMA save/restore source differs")
    return head.replace(RESTORE, SELECTIVE, 1) + "\nvoid dma_doHdma(Dma* dma) {" + tail


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--framework", type=Path, required=True)
    p.add_argument("--apply-experiment", action="store_true")
    args = p.parse_args()
    path = args.framework / "runner/src/snes/dma.c"
    try:
        old = path.read_text(encoding="utf-8")
        changed = patch_source(old)
        if args.apply_experiment:
            path.write_text(changed, encoding="utf-8")
    except (OSError, ValueError) as exc:
        p.exit(2, f"QA08_CH67_PRIME_REJECTED {exc}\n")
    print("QA08_CH67_PRIME_COUNTERFACTUAL_STAGED "
          f"applied={args.apply_experiment} path={path} "
          "genuine_native_original_pixels_not_yet_checked=true shipping=false")


if __name__ == "__main__":
    main()
