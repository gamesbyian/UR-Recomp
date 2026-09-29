#!/usr/bin/env python3
"""Functional smoke for UR-Recomp's pinned snes2asm adaptation."""

from __future__ import annotations

import snes2asm
from snes2asm.configurator import Configurator


def main() -> int:
    captured = []
    original = snes2asm.exec_asm
    try:
        snes2asm.exec_asm = lambda options: captured.append(options)
        snes2asm.main(["snes2asm", "dummy.sfc", "--empty-fill", "0x7f"])
    finally:
        snes2asm.exec_asm = original

    assert len(captured) == 1
    assert captured[0].empty_fill == 0x7F
    assert isinstance(captured[0].empty_fill, int)

    cfg = object.__new__(Configurator)
    cfg.decoders_enabled = {}
    cfg.label_lookup = {}

    try:
        cfg.build_decoder(None, {})
    except ValueError as exc:
        assert "missing type" in str(exc).lower()
    else:
        raise AssertionError("missing decoder type did not produce ValueError")

    try:
        cfg.build_decoder(None, {"type": "not-a-real-decoder"})
    except ValueError as exc:
        assert "unknown decoder type" in str(exc).lower()
    else:
        raise AssertionError("unknown decoder type did not produce ValueError")

    print("PASS: patched snes2asm option parsing and decoder diagnostics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
