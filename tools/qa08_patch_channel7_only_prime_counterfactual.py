#!/usr/bin/env python3
"""DISPOSABLE hypothesis: consume channel7/direct-mode0/$2100 first HDMA line.

This is a narrower causal discriminator than the *global* consumed-prime
counterfactual. Other HDMA channels still use the pinned non-consuming
prime behavior, originally retained for Gundam Wing compatibility.
Do not promote as source-faithful shipping behavior absent final pixels
and independent original hardware channel timing.
"""
from __future__ import annotations
import argparse
from pathlib import Path

try:
    from tools.qa08_patch_hdma_prime_counterfactual import (
        MARK as GLOBAL_MARK, patch_source as validate_global_source,
    )
except ModuleNotFoundError:
    from qa08_patch_hdma_prime_counterfactual import (
        MARK as GLOBAL_MARK, patch_source as validate_global_source,
    )

MARK = "UR_QA08_CH7_ONLY_PRIME_EXPERIMENT"
SAVE = "    DmaChannel save = *ch;\n"
RESTORE = "    *ch = save;\n  }\n}"
SELECTIVE = """    /* UR_QA08_CH7_ONLY_PRIME_EXPERIMENT: diagnostic, never release code.
     * Channel 7 direct mode0 to INIDISP ($2100) is the independently
     * source-observed Uniracers 2P brightness seam. Consume its first
     * descriptor exactly once while leaving all other channels' pinned
     * original counter/table semantics unchanged. */
    if (i == 7 && (ch->mode & 7) == 0 && !ch->indirect &&
        ch->bAdr == 0x00) {
      ch->repCount--;
      ch->doTransfer = (ch->repCount & 0x80) != 0;
      if ((ch->repCount & 0x7f) == 0)
        dma_hdmaLoadDescriptor(dma, ch);
    } else {
      *ch = save;
    }
  }
}"""


def patch_source(text: str) -> str:
    if MARK in text or GLOBAL_MARK in text:
        raise ValueError("first-line HDMA framework already has a counterfactual")
    # Delegate all pinned-source byte transfer, call order, snapshot restore,
    # and descriptor loader validation to the existing accepted narrow tool.
    validate_global_source(text)
    head, tail = text.split("\nvoid dma_doHdma(Dma* dma) {", 1)
    if head.count(SAVE) != 1 or head.count(RESTORE) != 1:
        raise ValueError("pinned original first-line DMA save/restore changed")
    head = head.replace(RESTORE, SELECTIVE, 1)
    return head + "\nvoid dma_doHdma(Dma* dma) {" + tail


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", required=True, type=Path)
    parser.add_argument("--apply-experiment", action="store_true")
    args = parser.parse_args()
    file = args.framework / "runner/src/snes/dma.c"
    try:
        original = file.read_text(encoding="utf-8")
        changed = patch_source(original)
        if args.apply_experiment:
            file.write_text(changed, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"QA08_CH7_ONLY_PRIME_REJECTED {exc}\n")
    print("QA08_CH7_ONLY_PRIME_COUNTERFACTUAL_STAGED "
          f"applied={args.apply_experiment} path={file} "
          "real_original_raster=not_checked")


if __name__ == "__main__":
    main()
