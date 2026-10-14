#!/usr/bin/env python3
"""Opt-in EXPERIMENT ONLY: consume the already transferred first HDMA line.

Applies to a disposable copy of pinned Baldosa SNESRecomp dma.c, never to
canonical generated game code or the release build. Do not apply until a
same-input 256x224 original/native RGB comparison and all-channel regression
can adjudicate the predicted difference.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_HDMA_PRIME_COUNTERFACTUAL"
FUNCTION = "void dma_primeHdmaFirstLine(Dma* dma) {"
NEXT = "\nvoid dma_doHdma(Dma* dma) {"
OLD_SAVE = "    DmaChannel save = *ch;\n    int len = transferLength[ch->mode & 7];"
OLD_RESTORE = "    *ch = save;\n  }\n}"
NEW_ADVANCE = """    /* UR_QA08_HDMA_PRIME_COUNTERFACTUAL: hypothesis, not accepted production.
     * First-line HDMA transfer has consumed A-bus bytes. Carry forward
     * channel table address and repetition state to avoid retransmitting
     * the same descriptor on the next visible line. */
    ch->repCount--;
    ch->doTransfer = (ch->repCount & 0x80) != 0;
    if ((ch->repCount & 0x7f) == 0)
      dma_hdmaLoadDescriptor(dma, ch);
  }
}"""


def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("HDMA prime counterfactual already applied")
    if (source.count(FUNCTION) != 1 or source.count(NEXT) != 1
        or "static void dma_hdmaLoadDescriptor(Dma* dma, DmaChannel* ch)" not in source
        or "void dma_initHdma(Dma* dma)" not in source):
        raise ValueError("not the pinned HDMA renderer source")
    head, rest = source.split(FUNCTION, 1)
    body, tail = rest.split(NEXT, 1)
    if (body.count(OLD_SAVE) != 1 or body.count(OLD_RESTORE) != 1
        or "dma_transferByte(dma, ch->tableAdr++, ch->aBank" not in body
        or "dma_transferByte(dma, ch->size++, ch->indBank" not in body
        or "hdma_pin_oam_address(dma, ch);" not in body):
        raise ValueError("pinned first-line HDMA implementation changed")
    body = body.replace(OLD_SAVE, "    int len = transferLength[ch->mode & 7];", 1)
    body = body.replace(OLD_RESTORE, NEW_ADVANCE, 1)
    return head + FUNCTION + body + NEXT + tail


def apply(framework: Path, *, experimental_write: bool) -> Path:
    file = framework / "runner/src/snes/dma.c"
    current = file.read_text(encoding="utf-8")
    updated = patch_source(current)
    if experimental_write:
        file.write_text(updated, encoding="utf-8")
    return file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", required=True, type=Path)
    parser.add_argument("--apply-experiment", action="store_true",
                        help="mutate disposable pinned framework; NEVER a shipping promotion")
    args = parser.parse_args()
    try:
        file = apply(args.framework, experimental_write=args.apply_experiment)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"QA08_HDMA_PRIME_COUNTERFACTUAL_REJECTED {exc}\n")
    print(f"QA08_HDMA_PRIME_COUNTERFACTUAL_STAGED applied={args.apply_experiment} "
          f"path={file}")


if __name__ == "__main__":
    main()
