#!/usr/bin/env python3
"""DISPOSABLE combined ch5/ch7 HDMA prime, NOT a shipping renderer fix.

The real 2P countdown source failed original RGB5 by 460 pixels with
channel7-only, while all-channel consumption was exact. This isolates the
next original renderer test to channel5 mode1 CGADSUB/COLDATA plus channel7
mode0 INIDISP, retaining pinned non-consuming prime for *other* channels.
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
except ModuleNotFoundError:
    from qa08_patch_hdma_prime_counterfactual import (
        MARK as GLOBAL_MARK, patch_source as validate_global_source,
    )
    from qa08_patch_channel7_only_prime_counterfactual import (
        MARK as CHANNEL7_MARK, SAVE, RESTORE,
    )

MARK = "UR_QA08_CH57_ONLY_PRIME_EXPERIMENT"
SELECTIVE = """    /* UR_QA08_CH57_ONLY_PRIME_EXPERIMENT: diagnostic only, never release.
     * Source-observed direct channel7 mode0 $2100 and direct channel5
     * mode1 $2131/$2132 both consume their first transferred HDMA line.
     * Other channels retain their pinned first-line prime behavior. */
    if ((i == 7 && (ch->mode & 7) == 0 && !ch->indirect &&
         ch->bAdr == 0x00) ||
        (i == 5 && (ch->mode & 7) == 1 && !ch->indirect &&
         ch->bAdr == 0x31)) {
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
    if any(x in source for x in (MARK, GLOBAL_MARK, CHANNEL7_MARK)):
        raise ValueError("disposable HDMA framework already has a prime counterfactual")
    # Reject source drift against the established full prime patch anchors,
    # including the actual A-bus byte and descriptor-loader semantics.
    validate_global_source(source)
    head, tail = source.split("\nvoid dma_doHdma(Dma* dma) {", 1)
    if head.count(SAVE) != 1 or head.count(RESTORE) != 1:
        raise ValueError("expected unique pinned first-line save/restore")
    head = head.replace(RESTORE, SELECTIVE, 1)
    return head + "\nvoid dma_doHdma(Dma* dma) {" + tail


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--apply-experiment", action="store_true")
    args = parser.parse_args()
    path = args.framework / "runner/src/snes/dma.c"
    try:
        initial = path.read_text(encoding="utf-8")
        trial = patch_source(initial)
        if args.apply_experiment:
            path.write_text(trial, encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"QA08_CH57_PRIME_REJECTED {exc}\n")
    print("QA08_CH57_PRIME_COUNTERFACTUAL_STAGED "
          f"applied={args.apply_experiment} path={path} "
          "production_change=false original_pixels_not_yet_checked=true")


if __name__ == "__main__":
    main()
